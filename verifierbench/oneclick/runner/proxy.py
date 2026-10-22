"""Fixed configured model upstream; task/status/SHA audit only, no payload logging."""
from __future__ import annotations
import base64,fcntl,hashlib,hmac,http.client,http.server,json,os,re,socket,tempfile,threading,time
from pathlib import Path
from urllib.parse import urlsplit
from config import load,paths,save_json

def transform(data,model,full_history):
    if data.get('model')!=model:raise ValueError('Unexpected model')
    if not full_history:return data,{}
    if data.get('previous_response_id') or data.get('conversation'):raise ValueError('Full visible history required')
    clean=[];removed=0;ids=0
    for item in data.get('input',[]):
        if item.get('type')=='reasoning':removed+=1;continue
        if item.get('type')=='item_reference':raise ValueError('Opaque item reference is not replayable')
        if 'id' in item:item=dict(item);item.pop('id');ids+=1
        clean.append(item)
    result=dict(data,input=clean,store=False)
    result['include']=[x for x in data.get('include',[]) if x!='reasoning.encrypted_content']
    return result,{'omitted_opaque_reasoning_items':removed,'stripped_resource_item_ids':ids,'visible_input_items':len(clean)}

class RefusalBarrier:
    """Persist the first upstream 403 before another request for that task runs.

    Only a refused response body is retained (mode 0600, at most 1 MiB). Normal
    prompts and responses are never logged. A partial refusal also blocks retry;
    its missing body is explicitly reported, never reconstructed or invented.
    """
    max_body=1024**2
    def __init__(self,workspace,run_id):
        self.w=Path(workspace);self.run_id=run_id;self.root=self.w/'upstream-refusals'
        self.root.mkdir(mode=0o700,exist_ok=True);self._locks={};self._guard=threading.Lock()
    def lock(self,task):
        if not re.fullmatch(r'vgb-t-[0-9a-f]+',task):raise ValueError('Invalid task identity')
        with self._guard:return self._locks.setdefault(task,threading.Lock())
    def _write(self,path,value):
        path.parent.mkdir(mode=0o700,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
        try:
            with os.fdopen(fd,'w') as f:json.dump(value,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
            os.link(name,path)
        finally:os.unlink(name)
    def lookup(self,task,path):
        header=self.root/task/'header.json'
        if not header.exists():
            registry=self.w/'content-denial-tasks.json';data=json.loads(registry.read_text()) if registry.exists() else {'tasks':[]}
            if task in data.get('tasks',[]) or task in data.get('transport_barriers',{}):raise RuntimeError('Previously refused task has no original transport header')
            return None
        first=json.loads(header.read_text())
        if (first.get('task'),first.get('path'),first.get('run_id'),first.get('status'))!=(task,path,self.run_id,403):raise RuntimeError('Refusal identity mismatch')
        self._register(task,first,header)
        response=header.with_name('response.json')
        if response.exists():
            result=json.loads(response.read_text());body=base64.b64decode(result['body_base64'],validate=True)
            if len(body)>self.max_body or hashlib.sha256(body).hexdigest()!=result['body_sha256']:raise RuntimeError('Refusal response hash mismatch')
            return dict(first,body=body,headers=result['headers'],body_sha256=result['body_sha256'],receipt=str(header),original_body_complete=True)
        body=json.dumps({'error':{'type':'upstream_refusal_preserved','message':'This task previously received upstream HTTP 403; the response body was not fully captured. No further upstream request is permitted.'}}).encode()
        return dict(first,body=body,headers=[['Content-Type','application/json']],body_sha256=hashlib.sha256(body).hexdigest(),receipt=str(header),original_body_complete=False)
    def begin(self,task,path,record):
        header=self.root/task/'header.json'
        first={'task':task,'path':path,'run_id':self.run_id,'status':403,'at':time.time(),
               'original_request_sha256':record['original_sha256'],'sent_request_sha256':record['sent_sha256'],'no_upstream_retry':True}
        self._write(header,first)
        self._register(task,first,header)
        return header
    def _register(self,task,first,header):
        # Register only this task, so the dispatcher does not turn a known 403
        # into a global hold. It remains a refusal/needs_review, never success.
        with (self.w/'content-denial.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            target=self.w/'content-denial-tasks.json';data=json.loads(target.read_text()) if target.exists() else {'tasks':[],'receipts':{}}
            binding=dict(first,header_receipt=str(header),header_sha256=hashlib.sha256(header.read_bytes()).hexdigest())
            previous=data.get('transport_barriers',{}).get(task)
            if previous is not None and previous!=binding:raise RuntimeError('Existing first-refusal binding changed')
            if task not in data['tasks']:data['tasks'].append(task)
            data.setdefault('transport_barriers',{})[task]=binding
            save_json(target,data)
    def finish(self,header,body,headers):
        if len(body)>self.max_body:raise RuntimeError('Upstream refusal body exceeds capture bound; task remains blocked')
        kept=[[k,v] for k,v in headers if k.lower() in ('content-type','x-request-id','request-id','retry-after')]
        self._write(header.with_name('response.json'),{'body_base64':base64.b64encode(body).decode(),'body_sha256':hashlib.sha256(body).hexdigest(),'headers':kept,'status':403})

def make_handler(cfg,w,key,token,refusals,audit_lock):
    up=urlsplit(cfg['api_base_url']);prefix='/t/vgb-'+cfg['run_id']+'-'
    suffix='/responses' if cfg['api_protocol']=='responses' else '/chat/completions'
    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def log_message(self,*args):pass
        def do_GET(self):
            if self.path!='/healthz':self.send_error(404);return
            body=json.dumps({'ok':True,'upstream':up.netloc,'run_id':cfg['run_id']}).encode();self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def do_POST(self):
            auth=self.headers.get('Authorization','')
            if not hmac.compare_digest(auth,'Bearer '+token):self.send_error(403);return
            match=re.fullmatch(re.escape(prefix)+r'(vgb-t-[0-9a-f]+)'+re.escape(up.path.rstrip('/')+suffix),self.path)
            if not match:self.send_error(403);return
            record={'at':time.time(),'task':match[1],'path':self.path,'upstream_contacted':False};conn=None;sent=False
            try:
                n=int(self.headers.get('Content-Length','0'))
                if not 0<n<=32*1024**2:raise ValueError('Request length')
                raw=self.rfile.read(n);body=json.loads(raw)
                body,meta=transform(body,cfg['model'],cfg['responses_full_history'] and cfg['api_protocol']=='responses');encoded=json.dumps(body).encode()
                record.update(meta,original_sha256=hashlib.sha256(raw).hexdigest(),sent_sha256=hashlib.sha256(encoded).hexdigest())
                with refusals.lock(match[1]):
                    prior=refusals.lookup(match[1],self.path)
                    if prior:
                        record.update(status=403,blocked_by_prior_403=True,original_refusal_receipt=prior['receipt'],response_body_sha256=prior['body_sha256'],original_body_complete=prior['original_body_complete'])
                        self.send_response(403)
                        for k,v in prior['headers']:self.send_header(k,v)
                        self.send_header('Connection','close');self.end_headers();sent=True;self.close_connection=True
                        self.wfile.write(prior['body']);self.wfile.flush()
                    else:
                        conn=http.client.HTTPSConnection(up.hostname,up.port or 443,timeout=900)
                        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','Content-Length':str(len(encoded)),'Connection':'close'}
                        record['upstream_contacted']=True
                        conn.request('POST',up.path.rstrip('/')+suffix,encoded,headers);reply=conn.getresponse();record['status']=reply.status
                        if reply.status==403:
                            marker=refusals.begin(match[1],self.path,record);record['original_refusal_receipt']=str(marker)
                            denied_body=reply.read(refusals.max_body+1)
                            refusals.finish(marker,denied_body,reply.getheaders())
                            record.update(response_body_sha256=hashlib.sha256(denied_body).hexdigest(),original_body_complete=True)
                        self.send_response(reply.status)
                        for k,v in reply.getheaders():
                            if k.lower() not in ('connection','transfer-encoding','content-length','set-cookie'):self.send_header(k,v)
                        self.send_header('Connection','close');self.end_headers();sent=True;self.close_connection=True
                        if reply.status==403:self.wfile.write(denied_body);self.wfile.flush()
                        else:
                            while chunk:=reply.read1(65536):self.wfile.write(chunk);self.wfile.flush()
            except Exception as exc:
                record['error_type']=type(exc).__name__
                if not sent:record['downstream_status']=502;self.send_error(502,'Model transport failed')
            finally:
                if conn:conn.close()
                record['ended']=time.time()
                with audit_lock:
                    with (w/'responses-transport-audit.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
    return Handler

def serve(cfg):
    """Runs inside the proxy container; the private network reaches it only by its alias."""
    w,_,_,_=paths(cfg);key=os.environ.get(cfg['api_key_env'])
    if not key:raise ValueError('Missing '+cfg['api_key_env'])
    token=(w/'.proxy-token').read_text().strip();up=urlsplit(cfg['api_base_url'])
    lock=(w/'proxy.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    Handler=make_handler(cfg,w,key,token,RefusalBarrier(w,cfg['run_id']),threading.Lock())
    server=http.server.ThreadingHTTPServer(('0.0.0.0',cfg['proxy_port']),Handler,bind_and_activate=False)
    # Concurrent tasks connect in bursts; the default listen backlog of 5 is too small.
    server.request_queue_size=128;server.server_bind();server.server_activate()
    save_json(w/'proxy-launch.json',{'container_hostname':socket.gethostname(),'pid':os.getpid(),'started':time.time(),'run_id':cfg['run_id'],'upstream':up.netloc})
    server.serve_forever()

if __name__=='__main__':serve(load())
