"""One versioned corrected attempt, using the same frozen inputs and native scorer."""
import os,sys,json,dataclasses,time,argparse,fcntl,hashlib,shutil,subprocess,traceback,stat,tempfile
from pathlib import Path

def publish_initial_status(path, data):
 """Publish complete JSON atomically while retaining exclusive-create semantics."""
 path=Path(path)
 fd,temporary=tempfile.mkstemp(prefix='.'+path.name+'.initial-',dir=path.parent)
 temporary=Path(temporary)
 try:
  with os.fdopen(fd,'w') as f:
   json.dump(data,f);f.write('\n');f.flush();os.fsync(f.fileno())
  # Same-filesystem hard-link creation is atomic and never overwrites a prior
  # attempt. Readers cannot see the empty/partial bytes of an open('x') writer.
  os.link(temporary,path)
 finally:temporary.unlink(missing_ok=True)

def delivery_gate(result):
 probe=result.get('probe') or {}
 gate={'outcome':probe.get('outcome'),'reward':result.get('reward'),
       'artifact_collected':result.get('ok') is True,'scope':'synthetic_CLI_schema_no_correctness_label'}
 gate['passed']=bool(gate['artifact_collected'] and gate['outcome']=='ok' and gate['reward']==1.0)
 return gate

def collect_delivery(artifact_root, destination, max_bytes=100*2**20, max_files=10000):
 """Copy only Harbor's declared /app/checker.py and /app/verifier_helpers.

 Python helper modules may themselves be named checker.py. Only the fixed root
 entrypoint is executable as the verifier; all copied files are manifest-bound.
 """
 artifact_root=Path(artifact_root);destination=Path(destination)
 app=artifact_root/'app';checker=app/'checker.py';helpers=app/'verifier_helpers'
 for p in (artifact_root,app):
  if p.is_symlink() or not p.is_dir():raise RuntimeError('Unsafe or missing Harbor artifact directory')
 files=[];directories=[];total=0;entries=0
 def add_file(p,rel):
  nonlocal total
  st=p.lstat()
  if not stat.S_ISREG(st.st_mode):raise RuntimeError('Delivered artifact is not a regular file: '+str(rel))
  total+=st.st_size
  if total>max_bytes or len(files)>=max_files:raise RuntimeError('Delivered artifact exceeds file/size limit')
  files.append((p,rel,st))
 if not checker.exists() or checker.is_symlink():raise RuntimeError('Missing or unsafe declared /app/checker.py')
 add_file(checker,Path('checker.py'))
 if helpers.exists() or helpers.is_symlink():
  if helpers.is_symlink() or not helpers.is_dir():raise RuntimeError('verifier_helpers must be a real directory')
  directories.append(Path('verifier_helpers'))
  for current,dirs,names in os.walk(helpers,followlinks=False):
   dirs.sort();names.sort()
   for name in dirs+names:
    p=Path(current)/name;rel=Path('verifier_helpers')/p.relative_to(helpers);st=p.lstat();entries+=1
    if entries>max_files*2:raise RuntimeError('Delivered helper tree exceeds entry limit')
    if stat.S_ISLNK(st.st_mode):raise RuntimeError('Symlink in delivered helpers: '+str(rel))
    if stat.S_ISDIR(st.st_mode):directories.append(rel)
    else:add_file(p,rel)
 destination.mkdir(parents=True,exist_ok=False)
 for rel in directories:(destination/rel).mkdir(parents=True,exist_ok=True)
 pins=[]
 for source,rel,before in files:
  # Traverse every component relative to an opened directory, with no symlink
  # following, so helpers cannot escape if a parent changes during collection.
  directory_fd=os.open(artifact_root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
  try:
   for component in ('app',)+rel.parts[:-1]:
    next_fd=os.open(component,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=directory_fd)
    os.close(directory_fd);directory_fd=next_fd
   fd=os.open(rel.name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=directory_fd)
  finally:os.close(directory_fd)
  with os.fdopen(fd,'rb') as f:
   opened=os.fstat(f.fileno())
   if not stat.S_ISREG(opened.st_mode) or (opened.st_dev,opened.st_ino,opened.st_size,opened.st_mtime_ns,opened.st_ctime_ns)!=(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns):raise RuntimeError('Delivered file changed before copy')
   blob=f.read(max_bytes+1);after=os.fstat(f.fileno())
  if len(blob)!=before.st_size or (after.st_size,after.st_mtime_ns,after.st_ctime_ns)!=(before.st_size,before.st_mtime_ns,before.st_ctime_ns):raise RuntimeError('Delivered file changed during copy')
  out=destination/rel;out.parent.mkdir(parents=True,exist_ok=True)
  with out.open('xb') as f:f.write(blob)
  out.chmod(stat.S_IMODE(before.st_mode)&0o777)
  digest=hashlib.sha256(blob).hexdigest()
  if hashlib.sha256(out.read_bytes()).hexdigest()!=digest:raise RuntimeError('Delivered bytes changed after copy')
  pins.append({'path':rel.as_posix(),'sha256':'sha256:'+digest})
 return {'checker_source':str(checker),'files':pins,'file_count':len(pins),'bytes':total}


def main():
 from config import load,paths
 cfg=load();W,A,R,H=paths(cfg);S=Path(__file__).resolve().parent
 os.environ['VGB_GENERATION_IMAGE']=cfg['generation_image']
 p=argparse.ArgumentParser();p.add_argument('--task',required=True);args=p.parse_args();tid=args.task
 sys.path[:0]=[str(S),str(H),str(H/'rig'),str(H/'harbor_integration')]
 from adapter_contract import RUNTIME_CONTRACT,AST_BENCHMARKS,GENERATION_IMAGE
 lock=(W/'locks'/tid).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 statepath=A/'task-status'/f'{tid}.json';statepath.parent.mkdir(exist_ok=True)
 # A completed/failed attempt is never silently retried or replaced.
 publish_initial_status(statepath,{'task':tid,'phase':'preparing','pid':os.getpid(),'started':time.time()})
 row=next(t for t in json.loads((W/'tasks.json').read_text()) if t['task_id']==tid)
 run=next(t for t in json.loads((A/'task-runs.json').read_text()) if t['task_id']==tid)
 manifest_sha=hashlib.sha256((R/'MANIFEST.json').read_bytes()).hexdigest()
 status={'task':tid,'benchmark':row['benchmark'],'pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'start_ticks':Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],'started':time.time(),'phase':'preparing','integration_revision':'integration-alignment-20261021-v4','suite_runtime':str(R),'suite_manifest_sha256':manifest_sha,'generation_contract':RUNTIME_CONTRACT}
 def save(**kw):
  status.update(kw);tmp=statepath.with_suffix('.tmp');tmp.write_text(json.dumps(status,indent=2));tmp.replace(statepath)
 broker=None
 try:
  denied=json.loads((W/'content-denial-tasks.json').read_text())['tasks']
  if tid in denied:raise RuntimeError('Upstream refusal preserved; no retry permitted')
  release=json.loads((A/'release.json').read_text());assert release['runtime_manifest_sha256']==manifest_sha
  assert hashlib.sha256(Path(cfg['config_path']).read_bytes()).hexdigest()==release['config_sha256'],'Run configuration changed'
  image_name=release['generation_image'];assert image_name==GENERATION_IMAGE
  image_id=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',image_name],text=True).strip();assert image_id==release['generation_image_id']
  assert release['generation_python']=='3.12.14'
  dependency_sha=release['generation_site_packages_sha256'];assert isinstance(dependency_sha,str) and len(dependency_sha)==64 and all(c in '0123456789abcdef' for c in dependency_sha),'Missing generation dependency SHA'
  save(generation_python=release['generation_python'],generation_image_id=image_id,generation_site_packages_sha256=dependency_sha)
  for pin in release['files']:
   assert hashlib.sha256((S/pin['path']).read_bytes()).hexdigest()==pin['sha256'],pin['path']
  for pin in json.loads((R/'MANIFEST.json').read_text())['files']:
   assert hashlib.sha256((R/pin['path']).read_bytes()).hexdigest()==pin['sha256'],pin['path']
  os.environ.update(LOOP_RUNTIME=str(A/'veritas-runtime'),VERITAS_ENV_LOCAL='1',VERITAS_HARNESS='opencode',VERITAS_API_PROTOCOL=cfg['api_protocol'],VERITAS_RUNTIME='1',VERITAS_LOCAL_STAGE=str(A/'local-stage'),VERITAS_RUNTIME_SPOOL=str(A/'runtime-spool'),VERITAS_PROMPTS_DIR=str(Path(run['package_dir'])/'adapter-source/prompts'),VGB_SRC_ROOT=str(W/'sources'),APPWORLD_ROOT=str(W/'sources/aw_root'),TAU2_DATA_DIR=str(W/'sources/tau2-bench/data'),HF_HOME=str(W/'hf-cache'),HF_DATASETS_CACHE=str(W/'hf-cache/datasets'),VGB_PUBLIC_OBSERVATION_V2='1',V4V_TAU2_RETRIEVAL='bm25',VGB_AD_SUITE_VERSION='v1.2',HF_HUB_OFFLINE='1',HF_DATASETS_OFFLINE='1')
  from judge.core import session,probe_core
  from local_docker_provider import LocalDockerEnvironment
  session._env_import_path=lambda:'provider:VGBEnvironment'
  original_spec=session._agent_spec
  def agent_spec(cfg,env):
   spec=original_spec(cfg,env);spec['kwargs']['opencode_config']['permission']['external_directory']='allow';return spec
  session._agent_spec=agent_spec
  sys.path[:0]=[str(R/'pipeline'),str(R/'pipeline/capabilities')]
  if row['benchmark'] not in AST_BENCHMARKS:
   from broker import Broker
   cap=A/'cap-rpc'/tid;cap.mkdir(parents=True,exist_ok=True)
   broker=Broker(row['benchmark'],row['source_task_id'],str(cap),budget=20)
  tag='vgb-'+cfg['run_id']+'-'+tid
  network=json.loads((W/'private-network.json').read_text())
  from urllib.parse import urlsplit
  base=urlsplit(cfg['api_base_url']);key='VGB_PROXY_TOKEN';os.environ[key]=(W/'.proxy-token').read_text().strip()
  protocol=cfg['api_protocol']
  # Provider id 'ark' is the one the reported run used. OpenCode writes
  # '<provider id>/<model>' into the agent's system prompt, so it stays unchanged.
  provider={'ark':{'npm':'@ai-sdk/openai' if protocol=='responses' else '@ai-sdk/openai-compatible','name':'VerifierBench fixed upstream proxy','options':{'baseURL':'http://'+network['proxy_alias']+':'+str(cfg['proxy_port'])+'/t/'+tag+base.path.rstrip('/'),'apiKey':'{env:'+key+'}'},'models':{cfg['model']:{'limit':{'context':200000,'output':32768},'options':{'store':False,'reasoningEffort':cfg['reasoning_effort'],'reasoningSummary':'auto'}}}}}
  session_cfg=session.SessionConfig(model='ark/'+cfg['model'],boxes=[tid],jobs_dir=str(A/'jobs'),timeout_sec=cfg['generation_timeout'],api_key_env=key,opencode_provider=provider,retry=False,exclude_agent_logs=[])
  save(phase='generating',capability_ready=bool(broker),protocol=protocol,meter_tag=tag)
  tr=session.TaskRun(task_id=tid,package_dir=run['package_dir'],contract_feedback_file=run['contract_feedback_file'])
  result=session.generate_roll([tr],session_cfg,probe_core.ProbeSpec(crash_patterns=['VGB_DELIVERY_CRASH'],ok_patterns=['VGB_DELIVERY_OK']),tag)[tid]
  resultpath=A/'generation-results'/f'{tid}.json';resultpath.parent.mkdir(exist_ok=True)
  with resultpath.open('x') as f:json.dump(dataclasses.asdict(result),f,indent=2,default=str)
  if broker:save(generation_capability_stats=dict(broker.stats));broker.close();broker=None
  result=json.loads(resultpath.read_text())
  from denial_receipt import record
  refusals=record(tid,result)
  if refusals:save(upstream_content_refusals=refusals,no_task_retry=True);raise RuntimeError('Upstream content refusal; no retry')
  artifactroot=Path(result['artifact_dir']) if result.get('artifact_dir') else None
  if not artifactroot:raise RuntimeError('Missing delivered artifact directory')
  artifact=A/'artifacts'/tid;delivery=collect_delivery(artifactroot,artifact)
  specbytes=(W/'generation-inputs'/tid/'task_spec.public.json').read_bytes()
  assert hashlib.sha256(specbytes).hexdigest()==row['effective_spec_sha256'],'Effective public task changed'
  spec=json.loads(specbytes)
  gi={'task_spec_sha256':row['task_spec_sha256'],'effective_spec_sha256':row['effective_spec_sha256'],'spec_renderer_version':'public-input-contract-20260917-v2','suite_manifest_sha256':manifest_sha,'integration_revision':'integration-alignment-20261021-v4','generation_python':release['generation_python'],'generation_image_id':image_id,'generation_site_packages_sha256':dependency_sha,'adapter_instruction_sha256':hashlib.sha256((Path(run['package_dir'])/'instruction.md').read_bytes()).hexdigest()}
  manifest={'schema_version':'1.0','artifact_api_version':'1.0','verifier_form':spec['verifier_form'],'entrypoint':{'protocol':'vgb-json-file-v1','argv':['python3','checker.py']},'files':delivery['files'],'requires_network':False,'harness':{'model':cfg['model'],'name':'Gavel','scaffold_axis':'Gavel'},'generation_inputs':gi,'source_result':str(resultpath),'source_checker':delivery['checker_source']}
  if row['benchmark'] not in AST_BENCHMARKS:
   manifest['environment_capabilities']={'mode':'interactive_resettable'};gi['generation_environment_contract']=RUNTIME_CONTRACT
  (artifact/'manifest.json').write_text(json.dumps(manifest,indent=2))
  # Gavel deliberately ships artifacts even when its probe fails. Preserve that
  # delivery, but do not mistake artifact presence for this adapter's CLI gate.
  gate=delivery_gate(result)
  save(artifact=str(artifact),delivery_gate=gate,delivered_files=delivery['file_count'],delivered_bytes=delivery['bytes'])
  if not gate['passed']:raise RuntimeError('Synthetic CLI/schema delivery probe did not pass; original artifact preserved, no replay or retry')
  save(phase='scoring',artifact=str(artifact))
  rounds=[1] if row['benchmark'] in AST_BENCHMARKS else [1,2,3]
  for rd in rounds:
   out=A/'verdicts'/tid/f'r{rd}.jsonl';out.parent.mkdir(parents=True,exist_ok=True)
   assert not out.exists() and not out.with_suffix('.jsonl.receipt.json').exists()
   save(round=rd,round_started=time.time())
   with (out.parent/f'r{rd}-driver.log').open('x') as log:
    rc=subprocess.run([cfg['scoring_python'],str(R/'scripts/replay.py'),'--bundle',str(artifact),'--views',str(W/'evaluator-views'),'--task',tid,'--source-root',str(W/'sources'),'--out',str(out)],stdout=log,stderr=subprocess.STDOUT).returncode
   if rc:raise RuntimeError('Replay failed r'+str(rd)+'; result retained for review')
  save(phase='complete',ended=time.time(),rounds=rounds)
 except Exception as exc:
  save(phase='needs_review',error=str(exc),traceback=traceback.format_exc(),ended=time.time());raise
 finally:
  if broker:broker.close()

if __name__=="__main__":main()
