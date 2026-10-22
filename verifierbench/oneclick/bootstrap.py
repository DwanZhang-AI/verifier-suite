#!/usr/bin/env python3
"""One command: pinned HF inputs, native environments, Gavel generation, official scoring.

Bootstrap uses Python >=3.9 stdlib. Benchmark work uses managed CPython 3.12.14.
No previous experiment, result directory or secret file is imported.
"""
from __future__ import annotations
import argparse,fcntl,hashlib,json,os,platform,re,shutil,stat,subprocess,sys,tempfile,time,urllib.parse,urllib.request,zipfile
from contextlib import contextmanager
from pathlib import Path,PurePosixPath

SUITE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
MARKER='.verifierbench-workspace.json'
GIB=1024**3


def require(ok,message):
    if not ok:raise RuntimeError(message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()

def read(path):return json.loads(Path(path).read_text())

def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def write_exact(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        require(not path.is_symlink() and path.is_file() and path.read_bytes()==data,'Existing bytes differ: '+str(path));return
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.link(name,path)
    finally:os.unlink(name)

def source_files(root):
    root=Path(root);out={}
    for p in sorted(root.rglob('*')):
        if '__pycache__' in p.parts or p.suffix=='.pyc':continue
        require(not p.is_symlink(),'Source archive contains unsupported symlink: '+str(p))
        if p.is_file():out[p.relative_to(root).as_posix()]=sha(p)
    return out

def suite_identity():
    if (SUITE/'SUITE_MANIFEST.json').exists():return sha(SUITE/'SUITE_MANIFEST.json')
    files={}
    for folder in ('runner','runtime','vendor'):
        files.update({folder+'/'+n:v for n,v in source_files(SUITE/folder).items()})
    for name in ('bootstrap.py','hf_assets.py','native_setup.py','environment_image.py','dataset-lock.json','toolchain-lock.json','requirements-generation.txt'):
        files[name]=sha(SUITE/name)
    return hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()

@contextmanager
def workspace_lock(workspace,*,create=True,identity=None):
    path=Path(workspace).expanduser().absolute()
    require(not path.is_symlink(),'Workspace cannot be a symlink')
    if not path.exists():
        require(create,'Workspace does not exist');path.mkdir(parents=True)
    require(path.is_dir(),'Workspace must be a directory')
    marker=path/MARKER
    if not marker.exists():
        require(create and not any(path.iterdir()),'Refusing nonempty unknown workspace')
        value={'schema':'verifierbench-oneclick-workspace-v1','workspace':str(path.resolve()),'suite_identity':identity,'created_at':time.time()}
        write_exact(marker,json.dumps(value,sort_keys=True,indent=2).encode())
    data=read(marker)
    require(data.get('schema')=='verifierbench-oneclick-workspace-v1' and data.get('workspace')==str(path.resolve()),'Workspace marker identity mismatch')
    if identity is not None:require(data.get('suite_identity')==identity,'Suite source changed after workspace creation; refusing an implicit experiment revision')
    with (path/'bootstrap.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield path.resolve()


def verify_package(root):
    root=Path(root).resolve();manifest=root/'SUITE_MANIFEST.json'
    require(manifest.is_file(),'Missing SUITE_MANIFEST.json; use the sealed release package')
    content=read(manifest);pins=content['files'];seen=set()
    for pin in pins:
        rel=pin['path'];parts=PurePosixPath(rel)
        require(not parts.is_absolute() and '..' not in parts.parts and rel not in seen,'Unsafe/duplicate package manifest path')
        seen.add(rel);p=root/rel
        require(not p.is_symlink() and p.is_file() and p.resolve().is_relative_to(root),'Missing/unsafe package file: '+rel)
        size=pin.get('size',pin.get('bytes'))
        require(p.stat().st_size==size and sha(p)==pin['sha256'],'Package file hash/size mismatch: '+rel)
    return {'files_verified':len(seen),'manifest_sha256':sha(manifest)}


def check_platform():
    require(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),'Execution requires Linux x86_64; local macOS does not run benchmark Docker')
    for tool in ('docker','bwrap','git'):
        require(shutil.which(tool) is not None,'Missing required host tool: '+tool)
    subprocess.run(['docker','info','--format','{{.ServerVersion}}'],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['bwrap','--version'],check=True,stdout=subprocess.DEVNULL)


def safe_api(base,key_env):
    u=urllib.parse.urlsplit(base)
    require(u.scheme=='https' and u.hostname and not u.username and not u.password and not u.query and not u.fragment,'API base must be HTTPS without credentials/query/fragment')
    require(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',key_env) is not None,'Invalid key environment name')
    return base.rstrip('/')


def command(args,*,env=None,cwd=None,output=False):
    args=[str(a) for a in args]
    child_env=dict(os.environ if env is None else env,PYTHONDONTWRITEBYTECODE='1')
    result=subprocess.run(args,env=child_env,cwd=cwd,check=False,text=True,capture_output=True)
    if result.returncode:
        raise RuntimeError(Path(args[0]).name+' failed with exit '+str(result.returncode)+'\n'+(result.stderr or result.stdout)[-3000:])
    return result.stdout.strip() if output else None


def verify_uv_version(value,expected):
    # Official wheels append a platform or build identifier in parentheses.
    # Wheel/executable SHA binds those bytes; compare the complete semantic
    # version token rather than permitting a prefix such as 0.13.40.
    match=re.fullmatch(r'uv ([0-9]+\.[0-9]+\.[0-9]+)(?: \([^\r\n()]+\))?',value)
    require(match is not None and match[1]==expected,'Downloaded uv version mismatch')


def uv_binary(work,lock):
    tools=work/'tools';tools.mkdir(exist_ok=True);binary=tools/'uv';receipt=tools/'uv.json'
    if binary.exists():
        require(receipt.is_file() and read(receipt).get('binary_sha256')==sha(binary),'Unbound uv executable')
        verify_uv_version(command([binary,'--version'],output=True),lock['version']);return binary
    wheel=tools/lock['filename']
    if not wheel.exists():
        tmp=wheel.with_suffix('.download')
        require(not tmp.exists(),'Interrupted uv download retained; inspect before resuming')
        req=urllib.request.Request(lock['url'],headers={'User-Agent':'verifierbench-oneclick/1'})
        with urllib.request.urlopen(req,timeout=120) as response,tmp.open('xb') as f:
            size=0
            while True:
                part=response.read(1024**2)
                if not part:break
                size+=len(part);require(size<=128*GIB//1024,'uv wheel exceeds 128 MiB');f.write(part)
        require(sha(tmp)==lock['sha256'],'uv wheel hash mismatch');tmp.rename(wheel)
    require(sha(wheel)==lock['sha256'],'uv wheel hash mismatch')
    with zipfile.ZipFile(wheel) as z:
        candidates=[]
        for info in z.infolist():
            p=PurePosixPath(info.filename)
            require(not p.is_absolute() and '..' not in p.parts,'Unsafe wheel member')
            if p.name=='uv' and 'scripts' in p.parts:candidates.append(info)
        require(len(candidates)==1,'uv wheel lacks a unique executable')
        info=candidates[0];require(info.file_size<=128*1024**2,'uv executable size bound')
        write_exact(binary,z.read(info));binary.chmod(0o755)
    verify_uv_version(command([binary,'--version'],output=True),lock['version'])
    atomic_json(receipt,{'wheel_sha256':lock['sha256'],'binary_sha256':sha(binary),'version':lock['version']});return binary


def python_environment(work,uv,toolchain):
    env=dict(os.environ,UV_PYTHON_INSTALL_DIR=str(work/'python'),UV_CACHE_DIR=str(work/'cache/uv'),UV_NO_CONFIG='1',PYTHONDONTWRITEBYTECODE='1')
    receipt=work/'setup/python.json'
    if receipt.exists():
        saved=read(receipt);python=Path(saved['python'])
        require(python.exists() and python.resolve().is_relative_to((work/'python').resolve()) and sha(python.resolve())==saved['executable_sha256'],'Existing managed interpreter differs from receipt')
    else:
        command([uv,'python','install',toolchain['python'],'--install-dir',work/'python','--no-bin'],env=env)
        python=Path(command([uv,'python','find','--managed-python',toolchain['python']],env=env,output=True))
        require(python.resolve().is_relative_to((work/'python').resolve()),'Managed interpreter escaped workspace')
    got=json.loads(command([python,'-I','-c','import json,sys;print(json.dumps({"version":list(sys.version_info[:3]),"base":sys.base_prefix}))'],output=True))
    require(got['version']==[3,12,14],'Managed Python must be exactly 3.12.14')
    atomic_json(receipt,{'python':str(python),'base':got['base'],'version':got['version'],'executable_sha256':sha(python.resolve())})
    return python,env


def installed(python):
    return json.loads(command([python,'-I','-c','import json,importlib.metadata as m;print(json.dumps({d.metadata["Name"].lower().replace("_","-"):d.version for d in m.distributions()}))'],output=True))


def requirements(path):
    result={}
    for line in Path(path).read_text().splitlines():
        line=line.strip()
        if not line or line.startswith('#'):continue
        match=re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s]+)',line);require(match is not None,'Dependency lock must use exact versions')
        name=match[1].lower().replace('_','-');require(name not in result,'Duplicate dependency lock');result[name]=match[2]
    return result


def venv_install(work,uv,python,env,name,wanted,install_args):
    dest=work/name;py=dest/'bin/python';receipt=work/'setup'/(name+'.json')
    if receipt.exists():
        require(py.exists() and installed(py)==wanted,'Existing '+name+' packages differ from lock; refusing mutation');return py
    if not dest.exists():command([uv,'venv','--python',python,dest],env=env)
    require(py.exists(),'Interrupted venv creation; inspect '+str(dest))
    # An interrupted install is completed only before a successful immutable receipt.
    command([uv,'pip','install','--python',py,'--no-deps','--no-sources','--index-url','https://pypi.org/simple',*install_args],env=env)
    require(installed(py)==wanted,'Installed '+name+' dependency inventory differs from exact lock')
    atomic_json(receipt,{'packages':wanted,'python':str(py),'verified':True});return py


def copy_runtime(work):
    src=SUITE/'runtime';dest=work/'runtime';pins=source_files(src);pins.pop('MANIFEST.json',None)
    if not dest.exists():dest.mkdir()
    for rel,digest in pins.items():
        target=dest/rel;source=src/rel
        if target.exists():require(not target.is_symlink() and sha(target)==digest,'Runtime file changed: '+rel)
        else:
            write_exact(target,source.read_bytes());target.chmod(stat.S_IMODE(source.stat().st_mode))
    actual={p.relative_to(dest).as_posix() for p in dest.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.relative_to(dest).parts[0]!='dataset' and p.name!='MANIFEST.json'}
    require(actual==set(pins),'Unrecognized runtime source files')
    return dest


def download_data(runtime,work):
    from hf_assets import download_snapshot
    lock=read(SUITE/'dataset-lock.json')
    receipt=download_snapshot(lock['repo_id'],lock['revision'],runtime/'dataset',lock['files'],lock.get('repo_type','dataset'))
    atomic_json(work/'setup/hf-dataset.json',receipt)
    return receipt


def seal_runtime(runtime,dataset):
    pins=[{'path':name,'sha256':digest} for name,digest in source_files(runtime).items() if name!='MANIFEST.json']
    manifest={'schema':'verifierbench-oneclick-derived-runtime-v1','files':pins,'upstream_runtime_manifest_sha256':sha(SUITE/'runtime/MANIFEST.json'),'dataset':{'repo_id':dataset['repo_id'],'revision':dataset['revision']},'provenance':'Bundled corrected public runtime plus exact HF dataset; derived identity, not upstream manifest'}
    write_exact(runtime/'MANIFEST.json',json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2).encode());return sha(runtime/'MANIFEST.json')


def materialize_inputs(work,python,runtime,native_env):
    env=dict(os.environ,**native_env);env['PYTHONDONTWRITEBYTECODE']='1'
    # Only official HF materialization functions are used. Existing bytes are rehashed.
    code=r'''import hashlib,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1])/'dataset/scripts'))
import materialize as M
w=Path(sys.argv[2]);rows=M.rows('paper','tasks');assert len(rows)==222
metadata=json.dumps(rows,ensure_ascii=False,indent=2).encode();path=w/'tasks.json'
if path.exists():assert path.read_bytes()==metadata,'Task metadata changed'
else:path.write_bytes(metadata)
if (w/'generation-inputs').exists():
 for row in rows:
  p=w/'generation-inputs'/row['task_id']/'task_spec.public.json';assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==row['effective_spec_sha256'],row['task_id']
 assert len(list((w/'generation-inputs').rglob('task_spec.public.json')))==222
else:M.materialize('paper','generation',w/'generation-inputs',w/'sources/aw_root')
print(json.dumps({'tasks':222,'generation_specs_verified':222}))
'''
    generation=json.loads(command([python,'-c',code,runtime,work],env=env,output=True))
    views=work/'evaluator-views'
    if not views.exists():command([python,runtime/'scripts/prepare_views.py','--output',views,'--appworld-root',work/'sources/aw_root'],env=env)
    verify=r'''import json,sys
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'scripts'))
from replay import validate_views
freeze=json.loads((root/'paper/freeze.json').read_text());bindings=validate_views(Path(sys.argv[2]),freeze)
assert bindings['tasks']==222 and bindings['candidates']==4993
print(json.dumps({'tasks':222,'candidates':4993,'bound_files':len(bindings['sha256'])}))'''
    result=json.loads(command([python,'-c',verify,runtime,views],env=env,output=True));result['generation']=generation
    atomic_json(work/'setup/inputs.json',result);return result


def configure_run(work,args,image,genpy,scorepy,native_env):
    cfg={'workspace':str(work),'harness_root':str(SUITE/'vendor/harness'),'generation_python':str(genpy),'scoring_python':str(scorepy),'model':args.model,'generation_image':image['image'],'generation_image_id':image['image_id'],'generation_site_packages_sha256':image['generation_site_packages_sha256'],'api_base_url':safe_api(args.api_base_url,args.api_key_env),'api_key_env':args.api_key_env,'api_protocol':args.api_protocol,'max_workers':args.max_workers,'native_environment':native_env}
    path=work/'run-config.json';write_exact(path,json.dumps(cfg,ensure_ascii=False,sort_keys=True,indent=2).encode());return path


def prepare(work,args):
    require(shutil.disk_usage(work).free>=100*GIB,'Setup requires at least 100 GiB free disk; this is not a peak guarantee')
    (work/'setup').mkdir(exist_ok=True)
    tools=read(SUITE/'toolchain-lock.json');uv=uv_binary(work,tools['uv']);py,env=python_environment(work,uv,tools)
    runtime=copy_runtime(work);data=download_data(runtime,work);seal_runtime(runtime,data)
    genwanted=requirements(SUITE/'requirements-generation.txt');genwanted['harbor']=tools['harbor_version']
    genpy=venv_install(work,uv,py,env,'generation-venv',genwanted,['-r',SUITE/'requirements-generation.txt',SUITE/'vendor/harbor'])
    scorewanted={k.lower().replace('_','-'):v for k,v in tools['scoring_packages'].items()}
    scorepy=venv_install(work,uv,py,env,'venv',scorewanted,[n+'=='+v for n,v in tools['scoring_packages'].items()])
    # Native setup performs metadata-only task probes, not benchmark candidates.
    command([py,SUITE/'native_setup.py','--workspace',work,'--python',py,'--runtime',runtime],env=env)
    native=read(work/'native-setup/complete.json');native_env=native['environment']
    materialize_inputs(work,scorepy,runtime,native_env)
    ready=read(work/'native-setup/swe-images.json')['images'];(work/'swe-images').mkdir(exist_ok=True)
    for source,item in ready.items():
        binding={k:v for k,v in item.items() if k not in ('pulled_this_run','sampled_at')}
        write_exact(work/'swe-images'/(source+'.json'),json.dumps(dict(binding,ok=True),sort_keys=True,indent=2).encode())
    command([py,SUITE/'environment_image.py','--workspace',work,'--python',py,'--scoring-python',scorepy,'--runtime',runtime],env=env)
    image=read(work/'environment-build/image-receipt.json');config=configure_run(work,args,image,genpy,scorepy,native_env)
    runner_env=dict(os.environ,**native_env)
    runner_env.update(VGB_RUN_CONFIG=str(config),PYTHONDONTWRITEBYTECODE='1')
    package=json.loads(command([genpy,SUITE/'runner/prepare.py'],env=runner_env,output=True))
    receipt={'status':'prepared','workspace':str(work),'tasks':222,'candidates':4993,'generation_packages':package,'model_calls':0,'run_config':str(config),'runtime_manifest_sha256':sha(runtime/'MANIFEST.json'),'generation_image_id':image['image_id']}
    atomic_json(work/'setup/complete.json',receipt);return receipt,runner_env


def status(work):
    cfg=read(work/'run-config.json');env=dict(os.environ,**cfg.get('native_environment',{}),VGB_RUN_CONFIG=str(work/'run-config.json'))
    result={'runtime':json.loads(command([cfg['generation_python'],SUITE/'runner/runtime.py'],env=env,output=True))}
    result['metrics']=json.loads(command([cfg['scoring_python'],SUITE/'runner/metrics.py'],env=env,output=True))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('prepare','run','status'))
    parser.add_argument('--work-dir',required=True,type=Path);parser.add_argument('--model',default='gpt-6-astra');parser.add_argument('--api-base-url');parser.add_argument('--api-key-env',default='OPENAI_API_KEY');parser.add_argument('--api-protocol',choices=('responses','chat_completions'),default='responses');parser.add_argument('--max-workers',type=int,default=6)
    args=parser.parse_args()
    verify_package(SUITE)
    if args.command=='status':
        with workspace_lock(args.work_dir,create=False):result=status(args.work_dir.resolve())
    else:
        require(args.api_base_url is not None,'--api-base-url is required for prepare/run');safe_api(args.api_base_url,args.api_key_env);require(1<=args.max_workers<=6,'max-workers must be 1..6');check_platform()
        if args.command=='run':require(os.environ.get(args.api_key_env),'Missing model API key environment variable: '+args.api_key_env)
        with workspace_lock(args.work_dir,identity=suite_identity()) as work:
            receipt,env=prepare(work,args)
            if args.command=='run':
                cfg=read(work/'run-config.json');result=json.loads(command([cfg['generation_python'],SUITE/'runner/start.py'],env=env,output=True))
            else:result=receipt
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    try:main()
    except Exception as exc:print(type(exc).__name__+': '+str(exc),file=sys.stderr);raise SystemExit(1)
