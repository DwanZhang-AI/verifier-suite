#!/usr/bin/env python3
"""Build an isolated generation image from the exact scoring Python environment.

Only invoked by explicit suite setup on Linux. This module never starts a model,
controller or benchmark. It consumes a standalone Python tree and a scoring venv;
no old experiment paths, images, candidate data or results are used.
"""
from __future__ import annotations
import argparse,datetime,fcntl,hashlib,json,os,platform,re,shutil,stat,subprocess,tempfile
from pathlib import Path

PYTHON_VERSION=[3,12,14]
NODE_IMAGE='node:22.23.3-bookworm-slim'
NODE_VERSION='v22.23.3'
OPENCODE_VERSION='1.18.3'
TOOLS_SHA={
 'node':'fde6a4bf8d0562f7751d1a2d6cb9b417c4cfe107bbcb0aa3e9a24e125e348f48',
 'opencode':'fdf58364c969a144fff0ae3a30f2fb6e705ada06864842613de1f9ecc70feb20',
}
FORBIDDEN_NAMES={'.ssh','.aws','.env','.netrc','.pypirc','credentials.json','credentials','id_rsa','id_ed25519'}

PYTHON_PROBE="\nimport hashlib,importlib.util,json,os,pathlib,sys,sysconfig\nroot=pathlib.Path(sys.base_prefix).resolve()\ndef sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()\nstdlib=pathlib.Path(sysconfig.get_path('stdlib')).resolve()\nrows=[]\nfor p in sorted(stdlib.rglob('*')):\n if not p.is_file() or any(x in ('site-packages','__pycache__') for x in p.relative_to(stdlib).parts) or p.suffix=='.pyc':continue\n target=p.resolve()\n if not target.is_relative_to(root):raise RuntimeError('stdlib link escapes interpreter tree')\n rows.append((str(p.relative_to(stdlib)),sha(target)))\nlibs={}\nfor p in sorted((root/'lib').glob('*')):\n if p.is_file() and ('.so' in p.name or p.name.endswith('.a')):\n  if not p.resolve().is_relative_to(root):raise RuntimeError('library escapes interpreter tree')\n  libs[p.name]=sha(p)\nfor mod in ('ssl','sqlite3','ctypes','multiprocessing','asyncio','decimal','lzma','bz2','zlib','venv','hashlib','json','pathlib','argparse','subprocess','resource'):__import__(mod)\nimport ssl,sqlite3\nspec=importlib.util.spec_from_file_location('vgb_env_alignment_probe',sys.argv[1]);client=importlib.util.module_from_spec(spec);spec.loader.exec_module(client)\nexe=pathlib.Path('/proc/self/exe').resolve()\nprint(json.dumps({'version':sys.version,'version_info':list(sys.version_info[:3]),'executable_sha256':sha(exe),\n 'stdlib_files':len(rows),'stdlib_sha256':hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(),\n 'library_sha256':libs,'openssl_version':ssl.OPENSSL_VERSION,'sqlite_version':sqlite3.sqlite_version,\n 'client_sha256':sha(sys.argv[1]),'client_import_ok':all(callable(getattr(client,k,None)) for k in ('inspect','run_public','reset','run_appworld_solution')),\n 'client_unconnected':not client.available(),'stdlib_imports_passed':True},sort_keys=True))\n"

TOOLS_PROBE="\nimport hashlib,json,pathlib,shutil,subprocess\nout={}\nfor name in ('node','opencode'):\n p=shutil.which(name)\n if not p:out[name]=None;continue\n real=pathlib.Path(p).resolve()\n r=subprocess.run([p,'--version'],capture_output=True,text=True,timeout=20)\n out[name]={'path':p,'resolved':str(real),'sha256':hashlib.sha256(real.read_bytes()).hexdigest(),'version':r.stdout.strip(),'returncode':r.returncode}\nprint(json.dumps(out,sort_keys=True))\n"

PACKAGE_PROBE="\nimport hashlib,importlib,importlib.metadata,importlib.util,json,os,pathlib,stat,sys,sysconfig\nroot=pathlib.Path(sysconfig.get_path('purelib')).resolve()\nrows=[];regular=symlinks=directories=total=0\nfor current,dirs,files in os.walk(root,followlinks=False):\n dirs[:]=[n for n in dirs if n!='__pycache__'];files=[n for n in files if not n.endswith('.pyc')]\n for name in sorted(dirs+files):\n  p=pathlib.Path(current)/name;rel=str(p.relative_to(root));st=p.lstat()\n  if stat.S_ISLNK(st.st_mode):\n   target=p.resolve(strict=True)\n   if not target.is_relative_to(root):raise RuntimeError('Package symlink escapes fixed site-packages')\n   rows.append({'path':rel,'kind':'symlink','target':str(target.relative_to(root))});symlinks+=1\n  elif stat.S_ISDIR(st.st_mode):rows.append({'path':rel,'kind':'directory'});directories+=1\n  elif stat.S_ISREG(st.st_mode):\n   rows.append({'path':rel,'kind':'file','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':st.st_size,'mode':stat.S_IMODE(st.st_mode)});regular+=1;total+=st.st_size\n  else:raise RuntimeError('Special file in package tree')\nrows.sort(key=lambda x:x['path'])\ndists=[]\nfor d in importlib.metadata.distributions(path=[str(root)]):\n name=d.metadata.get('Name');version=d.version\n if not name or version is None:raise RuntimeError('Distribution lacks identity')\n dists.append({'name':name,'version':version})\ndists.sort(key=lambda x:(x['name'].lower(),x['version']))\nimports={}\nfor name in ('numpy','pydantic','requests','yaml','regex','jsonschema','packaging','dateutil','pandas','pyarrow'):\n spec=importlib.util.find_spec(name)\n if spec is None:continue\n mod=importlib.import_module(name);origin=getattr(mod,'__file__',None)\n if not origin or not pathlib.Path(origin).resolve().is_relative_to(root):raise RuntimeError('Dependency resolves outside copied package tree: '+name)\n imports[name]={'ok':True,'origin':str(pathlib.Path(origin).resolve().relative_to(root))}\nprint(json.dumps({'inventory':{'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'regular':regular,'symlinks':symlinks,'directories':directories,'bytes':total},'distribution_count':len(dists),'distributions':dists,'bounded_imports':imports},sort_keys=True))\n"


def require(ok,message):
 if not ok:raise RuntimeError(message)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(args,timeout=90):
 """No shell and no inherited output; subprocess failures remain failures."""
 r=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=timeout)
 if r.returncode:raise RuntimeError(f'{Path(str(args[0])).name} failed with exit {r.returncode}: '+r.stderr[-2000:])
 return r.stdout.strip()

def identity(root):
 """Relative inventory; reject special files and links escaping the copied root."""
 root=Path(root).resolve(strict=True);require(root.is_dir(),'Inventory requires a directory')
 rows=[];total=0;regular=symlinks=directories=0
 for current,dirs,files in os.walk(root,followlinks=False):
  dirs[:]=[n for n in dirs if n!='__pycache__']
  for name in sorted(dirs+[n for n in files if not n.endswith('.pyc')]):
   p=Path(current)/name;rel=p.relative_to(root).as_posix();s=p.lstat()
   require(not FORBIDDEN_NAMES.intersection(p.relative_to(root).parts),'Credential-like path in interpreter/package tree')
   require(len(rows)<60000,'Interpreter/package tree exceeds 60000 entries')
   if stat.S_ISLNK(s.st_mode):
    target=p.resolve(strict=True);require(target.is_relative_to(root),'Symlink escapes interpreter/package tree')
    rows.append({'path':rel,'kind':'symlink','target':target.relative_to(root).as_posix()});symlinks+=1
   elif stat.S_ISDIR(s.st_mode):rows.append({'path':rel,'kind':'directory'});directories+=1
   elif stat.S_ISREG(s.st_mode):
    require(s.st_size<512*2**20 and total+s.st_size<=2*2**30,'Interpreter/package tree exceeds size bound')
    rows.append({'path':rel,'kind':'file','sha256':sha(p),'bytes':s.st_size,'mode':stat.S_IMODE(s.st_mode)});regular+=1;total+=s.st_size
   else:raise RuntimeError('Special file in interpreter/package tree')
 rows.sort(key=lambda x:x['path'])
 summary={'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'regular':regular,'symlinks':symlinks,'directories':directories,'bytes':total}
 return rows,summary

def copy_tree(root,destination,rows):
 root=Path(root).resolve();destination=Path(destination)
 require(identity(root)[0]==rows,'Source tree changed after inventory')
 destination.mkdir()
 for row in rows:
  src=root/row['path'];out=destination/row['path'];out.parent.mkdir(parents=True,exist_ok=True)
  if row['kind']=='directory':out.mkdir(exist_ok=True)
  elif row['kind']=='file':shutil.copy2(src,out)
  else:out.symlink_to(os.path.relpath(destination/row['target'],out.parent),target_is_directory=src.resolve().is_dir())
 require(identity(root)[0]==rows and identity(destination)[0]==rows,'Copied tree differs from captured source inventory')

def validate_pth(root):
 root=Path(root).resolve();out=[]
 for p in sorted(root.glob('*.pth')):
  for line in p.read_text().splitlines():
   line=line.strip()
   if not line or line.startswith('#') or line.startswith(('import ','import\t')):continue
   require((root/line).resolve().is_relative_to(root),'External path in .pth dependency')
  out.append({'path':p.name,'sha256':sha(p)})
 return out

def resources(workspace):
 available=next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))/1048576
 docker_root=Path(run(['docker','info','--format','{{.DockerRootDir}}']))
 require(docker_root.is_absolute() and docker_root.is_dir(),'DockerRootDir is not a local accessible directory; cannot verify image disk capacity')
 work_free=shutil.disk_usage(workspace).free/2**30
 docker_free=shutil.disk_usage(docker_root).free/2**30
 return {'mem_available_gib':available,'disk_free_gib':min(work_free,docker_free),
         'workspace_disk_free_gib':work_free,'docker_disk_free_gib':docker_free,
         'docker_root_dir':str(docker_root),'load':list(os.getloadavg())}

def inspect_image(image):
 p=subprocess.run(['docker','image','inspect',image,'--format','{{json .}}'],capture_output=True,text=True)
 if p.returncode:return None
 return json.loads(p.stdout)

def image_probe(image,code,client=None):
 args=['docker','run','--rm','--network','none','--memory','2g','--cpus','1']
 if client:args+=['--mount','type=bind,src='+str(client)+',dst=/probe/vgb_env.py,readonly']
 args+=['--entrypoint','python3',image,'-I','-B','-c',code]
 if client:args+=['/probe/vgb_env.py']
 return json.loads(run(args,180))

def validate_tools(tools):
 for name,version in [('node',NODE_VERSION),('opencode',OPENCODE_VERSION)]:
  got=tools.get(name) or {}
  require(got.get('returncode')==0 and got.get('version')==version,'Wrong '+name+' version')
  require(got.get('sha256')==TOOLS_SHA[name],'Pinned '+name+' executable bytes differ')

def dockerfile(base_repo_digest):
 # A registry RepoDigest is portable across both classic Docker and BuildKit;
 # an image config ID is recorded separately and is not a registry reference.
 require(re.fullmatch(r'(?:node|docker.io/library/node)@sha256:[0-9a-f]{64}',base_repo_digest),'Base image must be an immutable official Node RepoDigest')
 return f'''FROM {base_repo_digest}
RUN apt-get update && apt-get install -y --no-install-recommends bash git curl ripgrep time ca-certificates procps && rm -rf /var/lib/apt/lists/*
RUN npm install --global --no-audit --no-fund opencode-ai@{OPENCODE_VERSION} && npm cache clean --force
COPY python/ /opt/vgb-python/
RUN rm -rf /opt/vgb-python/lib/python3.12/site-packages && mkdir -p /opt/vgb-python/lib/python3.12/site-packages
COPY site-packages/ /opt/vgb-python/lib/python3.12/site-packages/
ENV PATH="/opt/vgb-python/bin:${{PATH}}" PYTHONDONTWRITEBYTECODE=1 OPENCODE_DISABLE_AUTOUPDATE=1 OPENCODE_DISABLE_LSP_DOWNLOAD=1
RUN ln -sfn /opt/vgb-python/bin/python3 /usr/local/bin/python3 && ln -sfn /opt/vgb-python/bin/python3 /usr/local/bin/python
WORKDIR /app
ENTRYPOINT []
CMD ["sleep", "infinity"]
'''

def resolve_python(python):
 p=Path(python).expanduser().resolve(strict=True)
 if p.is_dir():p=p/'bin/python3'
 require(p.is_file(),'Missing standalone Python executable')
 root=Path(run([p,'-I','-B','-c','import sys;print(sys.base_prefix)'])).resolve(strict=True)
 require(root.is_dir() and root!=Path('/usr'),'Use a standalone Python tree, not the host system interpreter')
 return p,root

def build(workspace,python,scoring_python,runtime):
 require(platform.system()=='Linux' and platform.machine() in ('x86_64','amd64'),'Image construction requires Linux x86_64')
 workspace=Path(workspace).expanduser().resolve(strict=True);runtime=Path(runtime).expanduser().resolve(strict=True)
 scoring=Path(scoring_python).expanduser().absolute();require(scoring.is_file(),'Missing scoring interpreter')
 client=runtime/'pipeline/capabilities/vgb_env_client.py';require(client.is_file(),'Missing pinned runtime client')
 rootpython,source=resolve_python(python)
 meta=workspace/'environment-build';meta.mkdir(exist_ok=True)
 with (meta/'image.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  return _build_locked(workspace,meta,rootpython,source,scoring,client)

def _build_locked(workspace,meta,rootpython,source,scoring,client):
 expected=json.loads(run([scoring,'-I','-B','-c',PYTHON_PROBE,str(client)],180))
 require(expected['version_info']==PYTHON_VERSION,'Scoring Python must be exactly 3.12.14')
 require(expected['client_import_ok'] and expected['client_unconnected'],'Runtime client import/channel probe failed')
 require(json.loads(run([rootpython,'-I','-B','-c',PYTHON_PROBE,str(client)],180))==expected,'Standalone Python differs from scorer executable/stdlib/libraries')
 site=Path(run([scoring,'-I','-B','-c','import sysconfig;print(sysconfig.get_path("purelib"))'])).resolve(strict=True)
 require(site!=source and site.is_dir(),'Missing scoring site-packages')
 source_rows,source_inventory=identity(source);package_rows,package_inventory=identity(site);pth=validate_pth(site)
 packages=json.loads(run([scoring,'-I','-B','-c',PACKAGE_PROBE],180));require(packages['inventory']==package_inventory,'Scoring site-packages inventory mismatch')
 tag='verifierbench-suiteenv:'+hashlib.sha256(str(workspace).encode()).hexdigest()[:12]
 receipt_path=meta/'image-receipt.json'
 binding={'schema':'verifierbench-suiteenv-image-v1','workspace':str(workspace),'python_inventory':source_inventory,'package_inventory':package_inventory,'client_sha256':sha(client),'node_image':NODE_IMAGE,'node_version':NODE_VERSION,'opencode_version':OPENCODE_VERSION,'tool_sha256':TOOLS_SHA,'builder_sha256':sha(Path(__file__))}
 if receipt_path.exists():
  receipt=json.loads(receipt_path.read_text());require(receipt['binding']==binding,'Image receipt disagrees with current inputs; refusing overwrite')
  image=inspect_image(tag);require(image and image['Id']==receipt['image_id'],'Existing image tag/ID differs from receipt')
  return {**receipt,'reused':True}
 require(inspect_image(tag) is None,'Unreceipted target image exists; refusing overwrite')
 before=resources(workspace);require(before['mem_available_gib']>=6 and before['disk_free_gib']>=100,'Image build requires MemAvailable>=6GiB and both workspace/Docker disk>=100GiB')
 # Acquisition is setup only. Actual verifier executions use network=none and
 # benchmark generation uses the configured private proxy network.
 run(['docker','pull','--platform','linux/amd64',NODE_IMAGE],900)
 base=inspect_image(NODE_IMAGE);require(base and base.get('Architecture')=='amd64' and base.get('Os')=='linux','Base image must be linux/amd64')
 base_id=base['Id']
 base_refs=[ref for ref in base.get('RepoDigests',[]) if re.fullmatch(r'(?:node|docker.io/library/node)@sha256:[0-9a-f]{64}',ref)]
 require(len(base_refs)==1,'Pulled official Node image lacks one immutable RepoDigest')
 base_ref=base_refs[0]
 prebuild=resources(workspace);require(prebuild['mem_available_gib']>=6 and prebuild['disk_free_gib']>=100,'Image build capacity changed after base pull')
 with tempfile.TemporaryDirectory(prefix='image-',dir=meta) as td:
  context=Path(td);copy_tree(source,context/'python',source_rows);copy_tree(site,context/'site-packages',package_rows)
  (context/'Dockerfile').write_text(dockerfile(base_ref));recipe_sha=sha(context/'Dockerfile')
  # Record build logs locally without model credentials. No environment values
  # are copied into build args, image layers or the receipt.
  command=['docker','build','--platform','linux/amd64','--pull=false','-t',tag,str(context)]
  with (meta/'docker-build.log').open('x') as log:
   p=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
  require(p.returncode==0,'Image build failed; inspect environment-build/docker-build.log')
 image=inspect_image(tag);require(image,'Built image was not found');image_id=image['Id']
 got_python=image_probe(image_id,PYTHON_PROBE,client);require(got_python==expected,'Image/scorer executable/stdlib/libraries/client differ')
 got_packages=image_probe(image_id,PACKAGE_PROBE);require(got_packages==packages,'Image/scorer installed dependency files or imports differ')
 tools=image_probe(image_id,TOOLS_PROBE);validate_tools(tools)
 shell_python={}
 for shell in ('/bin/sh','/bin/bash'):
  result=run(['docker','run','--rm','--network','none','--entrypoint',shell,image_id,'-lc','python3 -I -B -c "import sys;print(sys.version.split()[0])"'],60)
  require(result.splitlines()[-1]=='3.12.14','Login shell resolves wrong Python');shell_python[shell]='3.12.14'
 require(identity(source)[1]==source_inventory and identity(site)[1]==package_inventory,'Scoring Python or packages changed during build')
 receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'verified','binding':binding,'image':tag,'image_id':image_id,'base_image':NODE_IMAGE,'base_image_id':base_id,'base_repo_digest':base_ref,'base_repo_digests':base.get('RepoDigests',[]),'dockerfile_sha256':recipe_sha,'generation_python':'3.12.14','generation_site_packages_sha256':package_inventory['sha256'],'evaluation_python':expected,'image_python':got_python,'evaluation_packages':packages,'image_packages':got_packages,'image_tools':tools,'pth_checks':pth,'shell_python':shell_python,'resources_before':before,'resources_before_build':prebuild,'resources_after':resources(workspace),'reused':False,'model_calls':0,'candidate_reads':0,'starts_experiment':False}
 tmp=receipt_path.with_suffix('.tmp')
 with tmp.open('x') as f:json.dump(receipt,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
 os.link(tmp,receipt_path);tmp.unlink()
 return receipt

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--workspace',required=True,type=Path);p.add_argument('--python',required=True,type=Path)
 p.add_argument('--scoring-python',required=True,type=Path);p.add_argument('--runtime',required=True,type=Path)
 a=p.parse_args();print(json.dumps(build(a.workspace,a.python,a.scoring_python,a.runtime),ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
