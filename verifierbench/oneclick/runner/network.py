"""Create only this run's Docker networks. No host firewall rule is added or required.

The private network is internal and the host has no IPv4 address on its bridge
(com.docker.network.bridge.inhibit_ipv4), so generation containers can reach
neither the host nor the internet. The model proxy runs as a container that is
attached to the private network under PROXY_ALIAS and to a separate egress network.
"""
import ipaddress,json,os,secrets,subprocess
from config import load,paths,save_json

INHIBIT='com.docker.network.bridge.inhibit_ipv4'
PROXY_ALIAS='vgb-proxy'


def command(args):return subprocess.run(args,check=True,capture_output=True,text=True).stdout

def egress_name(cfg):return cfg['private_network']+'-egress'

def proxy_name(cfg):return 'vgb-proxy-'+cfg['run_id']


def inspect(name):
    found=subprocess.run(['docker','network','inspect',name],capture_output=True,text=True)
    return json.loads(found.stdout)[0] if found.returncode==0 else None


def check_private(cfg,n):
    """Raise unless n is this run's internal network and the host has no address on it."""
    if n.get('Driver')!='bridge' or not n['Internal'] or n['EnableIPv6'] or n.get('Labels',{}).get('verifierbench.workspace')!=cfg['run_id']:
        raise RuntimeError('Network identity/isolation mismatch')
    if (n.get('Options') or {}).get(INHIBIT)!='true':
        raise RuntimeError('Private network gives the host an address; '+INHIBIT+'=true is required')
    subnet=n['IPAM']['Config'][0]['Subnet'];gateway=n['IPAM']['Config'][0]['Gateway']
    if ipaddress.ip_network(subnet).version!=4 or ipaddress.ip_address(gateway).version!=4:raise RuntimeError('Only isolated IPv4 supported')
    return subnet,gateway


def check_egress(cfg,n):
    if n.get('Driver')!='bridge' or n['Internal'] or n.get('Labels',{}).get('verifierbench.workspace')!=cfg['run_id'] or n.get('Labels',{}).get('verifierbench.role')!='egress':
        raise RuntimeError('Egress network identity mismatch')


def container(name):
    found=subprocess.run(['docker','container','inspect',name],capture_output=True,text=True)
    return json.loads(found.stdout)[0] if found.returncode==0 else None


def check_proxy(cfg,c):
    """Raise unless c (docker container inspect) is this run's proxy on both networks."""
    labels=c['Config'].get('Labels') or {}
    if labels.get('verifierbench.workspace')!=cfg['run_id'] or labels.get('verifierbench.role')!='proxy' or c['Image']!=cfg['generation_image_id']:
        raise RuntimeError('Proxy container identity mismatch')
    nets=c['NetworkSettings']['Networks'];private=nets.get(cfg['private_network']) or {}
    if PROXY_ALIAS not in (private.get('Aliases') or [])+(private.get('DNSNames') or []) or egress_name(cfg) not in nets:
        raise RuntimeError('Proxy container networks changed')
    return {'container_id':c['Id'],'started_at':c['State']['StartedAt'],'running':bool(c['State']['Running'])}


def setup(cfg):
    w,_,_,_=paths(cfg);w.mkdir(parents=True,exist_ok=True)
    name=cfg['private_network'];egress=egress_name(cfg);marker='verifierbench.workspace='+cfg['run_id']
    if inspect(name) is None:
        command(['docker','network','create','--driver','bridge','--internal','-o',INHIBIT+'=true','--label',marker,name])
    subnet,gateway=check_private(cfg,inspect(name))
    if inspect(egress) is None:
        command(['docker','network','create','--driver','bridge','--label',marker,'--label','verifierbench.role=egress',egress])
    check_egress(cfg,inspect(egress))
    token=w/'.proxy-token'
    try:
        fd=os.open(token,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        if token.is_symlink() or token.stat().st_mode&0o077:raise RuntimeError('Unsafe proxy token file')
    else:
        with os.fdopen(fd,'w') as f:f.write(secrets.token_urlsafe(32))
    result={'name':name,'internal':True,'host_address':False,'subnet':subnet,'gateway':gateway,
            'egress_network':egress,'proxy_container':proxy_name(cfg),'proxy_alias':PROXY_ALIAS,
            'proxy_port':cfg['proxy_port'],'run_id':cfg['run_id']}
    save_json(w/'private-network.json',result)
    return result

if __name__=='__main__':print(json.dumps(setup(load())))
