"""Idempotent launcher. Adopts existing identity-bound processes; never retries tasks."""
import fcntl,json,os,socket,subprocess,time
from pathlib import Path
from urllib.parse import urlsplit
from config import load,paths,save_json
from dispatch import identity,same_identity,read_json
from network import PROXY_ALIAS,check_proxy,container,egress_name,proxy_name,setup
from prepare import prepare

PROBE='''import json,socket,sys,urllib.request
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
with opener.open(sys.argv[1],timeout=5) as response:
 data=response.read(4097)
 if len(data)>4096:raise ValueError('Oversized health response')
def reachable(host,port):
 try:socket.create_connection((host,port),timeout=3).close();return True
 except OSError:return False
print(json.dumps({'health':json.loads(data),
 'host_reachable':reachable(sys.argv[2],int(sys.argv[3])) or reachable(sys.argv[2],22),
 'internet_reachable':any(reachable(ip,443) for ip in sys.argv[4:])}))
'''


def upstream_addresses(cfg):
    host=urlsplit(cfg['api_base_url']).hostname
    found=sorted({a[4][0] for a in socket.getaddrinfo(host,443,socket.AF_INET,socket.SOCK_STREAM)})
    if not found:raise RuntimeError('Cannot resolve the model endpoint on the host')
    return found[:3]


def proxy_health(cfg,net,proxy):
    """Probe from the isolated workspace network, without model credentials.

    The same probe proves isolation: from the private network neither the host
    (the network gateway address) nor the model endpoint may be reachable.
    """
    name='vgb-health-'+cfg['run_id']+'-'+str(os.getpid());addresses=upstream_addresses(cfg)
    command=['docker','run','--rm','--pull=never','--read-only','--cap-drop','ALL',
             '--security-opt','no-new-privileges','--memory','128m','--cpus','0.25',
             '--pids-limit','32','--name',name,
             '--label','verifierbench.workspace='+cfg['run_id'],
             '--label','verifierbench.role=health',
             '--network',cfg['private_network'],
             '--entrypoint','/opt/vgb-python/bin/python3',cfg['generation_image_id'],
             '-I','-B','-c',PROBE,
             'http://'+PROXY_ALIAS+':'+str(cfg['proxy_port'])+'/healthz',net['gateway'],str(cfg['proxy_port']),*addresses]
    result=subprocess.run(command,check=True,capture_output=True,text=True,timeout=60)
    probe=json.loads(result.stdout);health=probe['health']
    if health.get('ok') is not True or health.get('run_id')!=cfg['run_id']:raise RuntimeError('Proxy health identity mismatch')
    if probe.get('host_reachable') is not False or probe.get('internet_reachable') is not False:
        raise RuntimeError('Private network is not isolated: '+json.dumps({k:probe.get(k) for k in ('host_reachable','internet_reachable')}))
    current=container(proxy_name(cfg))
    if current is None or check_proxy(cfg,current)!=proxy:raise RuntimeError('Proxy container identity changed during health check')
    return dict(health,isolation={'host_reachable':False,'internet_reachable':False,'probed_internet_addresses':addresses})


def proxy_command(cfg,w,s):
    """The proxy holds the key and is the private network's only route to the model endpoint."""
    return ['docker','create','--pull=never','--read-only','--cap-drop','ALL',
            '--security-opt','no-new-privileges','--memory','1g','--cpus','1','--pids-limit','256',
            '--user',str(os.getuid())+':'+str(os.getgid()),'--name',proxy_name(cfg),
            '--label','verifierbench.workspace='+cfg['run_id'],'--label','verifierbench.role=proxy',
            '--network',cfg['private_network'],'--network-alias',PROXY_ALIAS,
            '--env',cfg['api_key_env'],'--env','VGB_RUN_CONFIG='+cfg['config_path'],
            '--mount','type=bind,src='+str(w)+',dst='+str(w),
            '--mount','type=bind,src='+str(s)+',dst='+str(s)+',readonly',
            '--workdir',str(w),'--entrypoint','/opt/vgb-python/bin/python3',cfg['generation_image_id'],
            '-B','-E','-s',str(s/'proxy.py')]


def ensure_proxy(cfg,w,s):
    """Adopt this run's running proxy container, or start one on both networks."""
    found=container(proxy_name(cfg))
    if found is not None:
        current=check_proxy(cfg,found)
        if current['running']:return dict(current,running=True)
        # A stopped proxy holds no state outside the workspace; replace it.
        subprocess.run(['docker','rm',proxy_name(cfg)],check=True,capture_output=True,text=True)
    started=time.time()
    cid=subprocess.run(proxy_command(cfg,w,s),check=True,capture_output=True,text=True).stdout.strip()
    subprocess.run(['docker','network','connect',egress_name(cfg),cid],check=True,capture_output=True,text=True)
    subprocess.run(['docker','start',cid],check=True,capture_output=True,text=True)
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        found=container(proxy_name(cfg));launch=read_json(w/'proxy-launch.json',{})
        if found is None or found['Id']!=cid:raise RuntimeError('Proxy container replaced during startup')
        if not found['State']['Running']:raise RuntimeError('Proxy container exited; inspect docker logs '+proxy_name(cfg))
        hostname=launch.get('container_hostname')
        if launch.get('run_id')==cfg['run_id'] and hostname and cid.startswith(hostname) and launch.get('started',0)>=started-1:
            return dict(check_proxy(cfg,found),running=True)
        time.sleep(.1)
    raise RuntimeError('Proxy startup not verified')


def launch(cfg):
    if not os.environ.get(cfg['api_key_env']):raise ValueError('Set '+cfg['api_key_env']+' in the environment')
    w,a,_,_=paths(cfg);s=Path(__file__).resolve().parent;w.mkdir(parents=True,exist_ok=True)
    with (w/'launch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        preparation=prepare(cfg)
        if (a/'ended.json').exists():return {'status':'terminal','new_tasks_manually_started':0,'note':'All terminal tasks are retained; no new generation'}
        net=setup(cfg)
        proxy=ensure_proxy(cfg,w,s)
        proxy_health(cfg,net,proxy)
        state=read_json(a/'dispatch-state.json',{})
        if same_identity(identity(state.get('pid',0)),state.get('controller_identity')):
            return {'status':'already_running','controller':state['controller_identity'],'new_tasks_manually_started':0}
        # Refuse competing controller instead of relying only on its last status PID.
        for path in (w/'dispatch.lock',a/'controller.lock'):
            with path.open('a') as fd:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with (a/'controller.log').open('ab') as log:
            child=subprocess.Popen([cfg['generation_python'],str(s/'dispatch.py')],stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,cwd=w)
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            state=read_json(a/'dispatch-state.json',{})
            if state.get('pid')==child.pid and same_identity(identity(child.pid),state.get('controller_identity')):
                result={'status':'started','controller':state['controller_identity'],'proxy':proxy,'preparation':preparation,'at':time.time()};save_json(a/'launch.json',result);return result
            if child.poll() is not None:
                if (a/'ended.json').exists():return {'status':'terminal','new_tasks_manually_started':0}
                raise RuntimeError('Controller exited; existing workers and outputs retained; inspect controller.log')
            time.sleep(.1)
        raise RuntimeError('Controller startup not verified; inspect processes before rerunning start')

if __name__=='__main__':print(json.dumps(launch(load()),ensure_ascii=False))
