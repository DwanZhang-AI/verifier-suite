"""One run configuration. Secrets are environment variables, never config fields."""
from __future__ import annotations
import hashlib, json, os, re
from pathlib import Path
from urllib.parse import urlsplit

REVISION='integration-alignment-20261021-v4'


def load(path=None):
    path=Path(path or os.environ['VGB_RUN_CONFIG']).expanduser().resolve()
    data=json.loads(path.read_text())
    required={'workspace','harness_root','generation_python','scoring_python','model','generation_image','generation_image_id','generation_site_packages_sha256','api_base_url','api_key_env'}
    missing=required-set(data)
    if missing:raise ValueError('Missing configuration fields: '+', '.join(sorted(missing)))
    if any(k in data for k in ('api_key','token','authorization','password')):raise ValueError('Credentials belong only in environment variables')
    data['config_path']=str(path)
    for key in ('workspace','harness_root','generation_python','scoring_python'):
        value=Path(data[key]).expanduser()
        if not value.is_absolute():raise ValueError(key+' must be absolute')
        data[key]=str(value.absolute() if key in ('generation_python','scoring_python') else value.resolve())
    u=urlsplit(data['api_base_url'])
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment:raise ValueError('api_base_url must be HTTPS without credentials/query/fragment')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',data['api_key_env']):raise ValueError('Invalid API key environment name')
    if not re.fullmatch(r'[A-Za-z0-9_.:-]+',data['model']):raise ValueError('Invalid model name')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',data['generation_image_id']):raise ValueError('Generation image must be digest-bound')
    if not re.fullmatch(r'[0-9a-f]{64}',data['generation_site_packages_sha256']):raise ValueError('Scorer dependencies must be SHA-bound')
    suffix=hashlib.sha256(data['workspace'].encode()).hexdigest()[:12]
    data.setdefault('private_network','vgb-'+suffix)
    if data['private_network']!='vgb-'+suffix:raise ValueError('Network namespace must be derived from the workspace')
    data.setdefault('proxy_port',18887)
    data.setdefault('max_workers',6)
    if not 1<=int(data['max_workers'])<=6:raise ValueError('max_workers must be 1..6')
    if not 1024<=int(data['proxy_port'])<=65535:raise ValueError('proxy_port must be 1024..65535')
    data.setdefault('api_protocol','responses')
    if data['api_protocol'] not in ('responses','chat_completions'):raise ValueError('Unsupported protocol')
    data.setdefault('responses_full_history',True)
    data.setdefault('generation_timeout',5400)
    data.setdefault('reasoning_effort','medium')
    data['run_id']=suffix
    return data


def paths(config):
    w=Path(config['workspace']);return w,w/'run',w/'runtime',Path(config['harness_root'])


def save_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name('.'+path.name+'.'+str(os.getpid())+'.tmp')
    with tmp.open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
