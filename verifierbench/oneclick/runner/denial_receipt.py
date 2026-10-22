"""Record exact task-scoped upstream content refusals; never retry or change requests."""
import fcntl,hashlib,json,re,time
from pathlib import Path
from urllib.parse import urlsplit
from config import load,paths

def transport_refusal(work,task,run_id,expected_path,root_name='upstream-refusals'):
 """A bound first HTTP 403 takes precedence over a later overwritten agent log."""
 if not re.fullmatch(r'vgb-t-[0-9a-f]+',task):raise ValueError('Invalid refusal task')
 W=Path(work);header=W/root_name/task/'header.json'
 registry=W/'content-denial-tasks.json'
 data=json.loads(registry.read_text()) if registry.exists() else {'tasks':[]}
 binding=data.get('transport_barriers',{}).get(task)
 if not header.exists() and not binding:return []
 if not binding or not header.is_file() or header.is_symlink():raise RuntimeError('Incomplete transport refusal binding')
 raw=header.read_bytes();digest=hashlib.sha256(raw).hexdigest();first=json.loads(raw)
 if (binding.get('header_receipt'),binding.get('header_sha256'))!=(str(header),digest):raise RuntimeError('Transport refusal SHA/path mismatch')
 if task not in data['tasks'] or any(binding.get(k)!=v for k,v in first.items()):raise RuntimeError('Transport refusal registration mismatch')
 if (first.get('task'),first.get('run_id'),first.get('path'),first.get('status'),first.get('no_upstream_retry'))!=(task,run_id,expected_path,403,True):raise RuntimeError('Transport refusal identity mismatch')
 for field in ('original_request_sha256','sent_request_sha256'):
  if not re.fullmatch(r'[0-9a-f]{64}',str(first.get(field,''))):raise RuntimeError('Transport refusal request fingerprint missing')
 return [{'task':task,'status':403,'code':None,'classification':'upstream_http_403','header_receipt':str(header),'header_sha256':digest,'no_task_retry':True}]

def record(task,result):
 cfg=load();W,_,_,_=paths(cfg)
 suffix='/responses' if cfg['api_protocol']=='responses' else '/chat/completions'
 expected='/t/vgb-'+cfg['run_id']+'-'+task+urlsplit(cfg['api_base_url']).path.rstrip('/')+suffix
 bound=transport_refusal(W,task,cfg['run_id'],expected)
 if bound:return bound
 p=Path(result['trial_dir'])/'agent/opencode.txt'
 if not p.exists():return []
 found=[]
 def visit(x):
  if isinstance(x,dict):
   if x.get('statusCode')==403 and x.get('responseBody'):
    try:b=json.loads(x['responseBody'])
    except (ValueError,TypeError):b={}
    if str(b.get('code'))=='4003' and str(b.get('result','')).startswith('unauthorized_access_rejected') and b.get('rejected_fields'):
     found.append({'code':'4003','result':'unauthorized_access_rejected','rejected_fields':b['rejected_fields'],'request_id':b.get('request_id')})
   for v in x.values():visit(v)
  elif isinstance(x,list):
   for v in x:visit(v)
 for l in p.read_text().splitlines():
  try:x=json.loads(l)
  except ValueError:continue
  if x.get('type')=='error':visit(x)
 if found:
  with (W/'content-denial.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   out=W/'content-denial-tasks.json';data=json.loads(out.read_text()) if out.exists() else {'tasks':[]}
   if task not in data['tasks']:data['tasks'].append(task)
   data.setdefault('receipts',{})[task]={'at':time.time(),'original_log':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'refusals':found,'no_task_retry':True}
   tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2));tmp.replace(out)
 return found
