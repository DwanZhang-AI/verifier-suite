#!/usr/bin/env python3
"""Install and verify locked native backends on Linux x86_64; never run a model.

The public VerifierBench dataset comes from HF. Its runtime is the supplied,
aligned runtime. Native package locks, tau2's exact official source commit,
SWE's pinned HF dataset, and immutable image digests remain distinct sources.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile

TAU_REPO = 'https://github.com/sierra-research/tau2-bench.git'
TAU_COMMIT = 'fc0055dc4e0a316c3f83133267fbd6faaa770992'
SWE_REPO = 'princeton-nlp/SWE-bench_Verified'
SWE_REVISION = 'c104f840cc67f8b6eec6f759ebc8b2693d585d4a'
SWE_PARQUET = 'data/test-00000-of-00001.parquet'
SWE_PARQUET_SHA256 = 'a45b1fe4e2f0c8390b2b2938ac83e92ed5979000856808f3679c07812e9e6dcd'
GIB = 1024 ** 3


class SetupError(RuntimeError):
    pass


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', prefix='.' + path.name, dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    try:
        tmp.replace(path)
    finally:
        if tmp.exists(): tmp.unlink()


def parse_requirements(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'): continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s;]+)', line)
        if not match: raise SetupError('Every native dependency must be an exact version pin: ' + line)
        name, version = match.groups()
        key = re.sub(r'[-_.]+', '-', name).lower()
        if key in result: raise SetupError('Duplicate native dependency: ' + name)
        result[key] = version
    if not result: raise SetupError('Empty native package lock')
    return result


def check_versions(installed, expected):
    actual = {re.sub(r'[-_.]+', '-', k).lower(): v for k, v in installed.items()}
    return {name: {'expected': version, 'actual': actual.get(name)}
            for name, version in expected.items() if actual.get(name) != version}


def validate_swe_rows(rows, expected):
    """Match all frozen 47 public source IDs, base commits and problem statements."""
    by_id = {}
    for row in rows:
        key = row['instance_id']
        if key in by_id: raise SetupError('Duplicate SWE dataset source ID: ' + key)
        by_id[key] = row
    if len(by_id) != 500: raise SetupError('Expected the official 500-task SWE Verified dataset')
    if len(expected) != 47 or len({r['source_task_id'] for r in expected}) != 47:
        raise SetupError('Expected exactly 47 distinct frozen SWE tasks')
    verified = []
    for task in expected:
        key = task['source_task_id']; row = by_id.get(key)
        if row is None: raise SetupError('Missing frozen SWE source ID: ' + key)
        for field in ('base_commit', 'problem_statement'):
            if not task.get(field) or row.get(field) != task[field]:
                raise SetupError('SWE frozen public field differs: ' + key + '/' + field)
        verified.append({'source_task_id': key, 'base_commit': row['base_commit'],
                         'problem_statement_sha256': hashlib.sha256(row['problem_statement'].encode()).hexdigest()})
    return verified


def validate_image_inspect(record, observed):
    refs = record.get('repo_digests') or []
    if not refs or not re.fullmatch(r'[^\s@]+@sha256:[0-9a-f]{64}', refs[0]):
        raise SetupError('An immutable SWE image RepoDigest is required')
    if len(observed) != 1 or refs[0] not in (observed[0].get('RepoDigests') or []):
        raise SetupError('Docker image does not match the required immutable RepoDigest')
    actual = observed[0]
    if actual.get('Os') != 'linux' or actual.get('Architecture') != 'amd64':
        raise SetupError('SWE image must be Linux amd64')
    # The supplied image_id fields contain manifest digests on some hosts,
    # not Docker config IDs. RepoDigest is the portable binding; record both.
    return {'repo_digest': refs[0], 'actual_config_id': actual['Id'],
            'recorded_image_id': record.get('image_id'), 'os': actual['Os'],
            'architecture': actual['Architecture'], 'verified': True}


def _default_run(argv, *, env=None, cwd=None):
    return subprocess.run(argv, env=env, cwd=cwd, capture_output=True, text=True, timeout=7200)


class NativeSetup:
    def __init__(self, workspace, python312, runtime_root, run_command=None):
        self.work = Path(workspace).resolve(); self.python = str(Path(python312).resolve())
        self.runtime = Path(runtime_root).resolve(); self.sources = self.work/'sources'
        self.out = self.work/'native-setup'; self.runner = run_command or _default_run
        self.environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', VGB_SRC_ROOT=str(self.sources),
                                APPWORLD_ROOT=str(self.sources/'aw_root'),
                                TAU2_DATA_DIR=str(self.sources/'tau2-bench/data'),
                                V4V_TAU2_RETRIEVAL='bm25', VGB_AD_SUITE_VERSION='v1.2',
                                HF_HOME=str(self.work/'hf-cache'),
                                HF_DATASETS_CACHE=str(self.work/'hf-cache/datasets'))
        # Setup's online downloads must not inherit runtime's offline flags.
        self.environment.pop('HF_HUB_OFFLINE', None)
        self.environment.pop('HF_DATASETS_OFFLINE', None)
        self.steps = {}

    def command(self, argv, *, env=None, cwd=None, allow_failure=False):
        result = self.runner([str(x) for x in argv], env=env or self.environment, cwd=str(cwd) if cwd else None)
        if result.returncode and not allow_failure:
            # Error messages contain command names and bounded output, never the environment.
            raise SetupError('Native setup command failed: ' + str(argv[0]) + ' rc=' + str(result.returncode) + '\n' + (result.stderr or result.stdout or '')[-4000:])
        return result

    def python_json(self, python, code, *, env=None):
        r = self.command([python, '-c', code], env=env)
        try: return json.loads(r.stdout)
        except json.JSONDecodeError as error: raise SetupError('Native probe did not return JSON') from error

    def receipt(self, phase, value):
        value = dict(value, sampled_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
        # Keep previous receipts immutable and publish the latest pointer separately.
        stamp = value['sampled_at'].replace(':', '').replace('.', '').replace('+00', 'Z')
        atomic_json(self.out/'history'/(phase+'-'+stamp+'.json'), value)
        atomic_json(self.out/(phase+'.json'), value)
        self.steps[phase] = value
        return value

    def preflight(self):
        if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'AMD64'):
            raise SetupError('Native VerifierBench setup requires Linux x86_64')
        self.sources.mkdir(parents=True, exist_ok=True); self.out.mkdir(parents=True, exist_ok=True)
        info = self.python_json(self.python, "import json,sys;print(json.dumps({'version':list(sys.version_info[:3]),'executable':sys.executable}))")
        if info['version'] != [3, 12, 14]: raise SetupError('The aligned suite requires Python 3.12.14')
        for name in ('aw', 'ad', 'tau2', 'swe'):
            parse_requirements(self.runtime/'environment'/('_venv_'+name+'.requirements.txt'))
        self.command(['git', '--version']); self.command(['docker', 'version', '--format', '{{.Server.Version}}'])
        self.command(['bwrap', '--version'])
        return self.receipt('preflight', {'python': info, 'platform': platform.platform(), 'verified': True})

    def tau_source(self):
        path = self.sources/'tau2-bench'
        if not path.exists():
            stage = Path(tempfile.mkdtemp(prefix='.tau2-source-', dir=self.sources))
            try:
                self.command(['git', 'init', str(stage)])
                self.command(['git', '-C', stage, 'remote', 'add', 'origin', TAU_REPO])
                self.command(['git', '-C', stage, 'fetch', '--depth', '1', 'origin', TAU_COMMIT])
                self.command(['git', '-C', stage, 'checkout', '--detach', 'FETCH_HEAD'])
                stage.rename(path)
            finally:
                if stage.exists(): shutil.rmtree(stage)
        head = self.command(['git', '-C', path, 'rev-parse', 'HEAD']).stdout.strip()
        dirty = self.command(['git', '-C', path, 'status', '--porcelain', '--untracked-files=no']).stdout.strip()
        origin = self.command(['git', '-C', path, 'remote', 'get-url', 'origin']).stdout.strip()
        if head != TAU_COMMIT or dirty or origin != TAU_REPO:
            raise SetupError('Existing tau2 source is not the pinned clean official checkout; refusing to reset it')
        for domain in ('retail', 'banking_knowledge'):
            if not (path/'data/tau2/domains'/domain/'tasks.json').is_file():
                raise SetupError('Pinned tau2 source missing required domain: ' + domain)
        untracked = self.command(['git', '-C', path, 'ls-files', '--others', '-z', '--', 'src', 'data']).stdout.split('\0')
        unsafe = []
        for name in filter(None, untracked):
            parts = Path(name).parts
            cache = '__pycache__' in parts and Path(name).suffix == '.pyc'
            metadata = any(part.endswith('.egg-info') for part in parts)
            if not (cache or metadata): unsafe.append(name)
        if unsafe:
            raise SetupError('Untracked tau2 source/data could alter pinned behavior: ' + ', '.join(unsafe[:10]))
        files = self.command(['git', '-C', path, 'ls-files', '-z']).stdout.split('\0')
        hashes = {name: digest(path/name) for name in files if name and (path/name).is_file()}
        binding = hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        return self.receipt('tau2-source', {'repository': origin, 'commit': head, 'tracked_files': len(hashes),
                                           'source_sha256': binding, 'verified': True})

    def versions(self, python):
        return self.python_json(python, "import importlib.metadata as m,json,sys;print(json.dumps({'python':list(sys.version_info[:3]),'packages':{d.metadata['Name']:d.version for d in m.distributions()},'tau2_direct_url':next((d.read_text('direct_url.json') for d in m.distributions() if d.metadata['Name'].lower()=='tau2'),None)}))")

    def packages(self, name):
        lock = self.runtime/'environment'/('_venv_'+name+'.requirements.txt'); expected = parse_requirements(lock)
        venv = self.sources/('_venv_'+name); python = venv/'bin/python'
        previous_path = self.out/('packages-'+name+'.json')
        previous = json.loads(previous_path.read_text()) if previous_path.exists() else None
        if previous and (previous.get('lock_sha256') != digest(lock) or not python.exists()):
            raise SetupError('Previously verified native environment binding changed; refusing to rebuild it: ' + name)
        if not python.exists():
            if venv.exists(): raise SetupError('Incomplete unrecognized venv; choose a clean workspace: ' + str(venv))
            self.command([self.python, '-m', 'venv', str(venv)])
        before = self.versions(python)
        if before['python'] != [3, 12, 14]: raise SetupError('Existing native environment has the wrong Python version')
        need = bool(check_versions(before['packages'], expected))
        if name == 'tau2':
            direct = json.loads(before['tau2_direct_url']) if before.get('tau2_direct_url') else {}
            need = need or direct.get('url') != (self.sources/'tau2-bench').as_uri()
        before_inventory = hashlib.sha256(json.dumps(before['packages'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if previous and (need or previous.get('installed_package_inventory_sha256') != before_inventory):
            raise SetupError('Previously verified native packages changed; refusing to hot-modify them: ' + name)
        if need:
            lines = [k+'=='+v for k, v in expected.items() if not (name == 'tau2' and k == 'tau2')]
            effective = self.out/(name+'-effective.requirements.txt')
            effective.write_text('\n'.join(lines)+'\n')
            self.command([python, '-m', 'pip', 'install', '--index-url', 'https://pypi.org/simple', '--no-deps', '-r', effective])
            if name == 'tau2':
                self.command([python, '-m', 'pip', 'install', '--index-url', 'https://pypi.org/simple', '--no-deps', self.sources/'tau2-bench'])
        after = self.versions(python)
        if name == 'tau2':
            direct = json.loads(after['tau2_direct_url']) if after.get('tau2_direct_url') else {}
            if direct.get('url') != (self.sources/'tau2-bench').as_uri():
                raise SetupError('Installed tau2 does not originate from the pinned local source')
        mismatch = check_versions(after['packages'], expected)
        if mismatch: raise SetupError('Native package pins did not match: '+json.dumps(mismatch))
        normalized = {re.sub(r'[-_.]+', '-', k).lower(): v for k,v in after['packages'].items()}
        extras = {k:v for k,v in normalized.items() if k not in expected}
        check = self.command([python, '-m', 'pip', 'check'])
        return self.receipt('packages-'+name, {'lock_sha256': digest(lock), 'python': after['python'],
                                             'pins': expected, 'pinned_count': len(expected), 'extra_installed_packages': extras,
                                             'package_set_equals_lock': not bool(extras),
                                             'installed_package_inventory_sha256': hashlib.sha256(json.dumps(after['packages'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                                             'installed_this_run': need, 'pip_check': check.stdout.strip(), 'verified': True})

    def frozen_scope(self):
        python = self.sources/'_venv_swe/bin/python'
        code = """import json,hashlib
from pathlib import Path
import pyarrow.parquet as pq
r=Path(RUNTIME)
rows=pq.read_table(r/'dataset/data/tasks.parquet').to_pylist()
freeze=json.loads((r/'paper/freeze.json').read_text())['tasks']
assert len(rows)==222 and len({x['task_id'] for x in rows})==222 and {x['task_id'] for x in rows}==set(freeze)
def unique_field(obj,key):
 values=[]
 def visit(x):
  if isinstance(x,dict):
   if key in x:values.append(x[key])
   for value in x.values():visit(value)
  elif isinstance(x,list):
   for value in x:visit(value)
 visit(obj)
 values=list(dict.fromkeys(x for x in values if isinstance(x,str) and x))
 assert len(values)==1,(key,len(values))
 return values[0]
out=[]
for x in rows:
 rec={k:x[k] for k in ['task_id','benchmark','source_task_id']}
 if x['benchmark']=='SWE-bench Verified':
  spec=json.loads(x['task_spec_json'])
  rec.update({k:unique_field(spec,k) for k in ['base_commit','problem_statement']})
 out.append(rec)
print(json.dumps(out))
""".replace('RUNTIME', repr(str(self.runtime)))
        return self.python_json(python, code)

    def appworld_data(self, scope):
        python = self.sources/'_venv_aw/bin/python'; root = self.sources/'aw_root'; root.mkdir(exist_ok=True)
        install = self.out/'appworld-install.json'
        if not install.exists():
            self.command([python, '-m', 'appworld.cli', 'install'], cwd=root)
            atomic_json(install, {'version': '0.1.3.post1', 'completed': True})
        if not (root/'data').exists():
            self.command([python, '-m', 'appworld.cli', 'download', 'data', '--root', root], cwd=root)
        # Reconstruct and hash-check every frozen AppWorld task and candidate, without
        # executing a checker, candidate, or official hidden evaluation.
        code = """import sys,json,hashlib
from pathlib import Path
sys.path.insert(0, SCRIPTS)
import materialize as m
root=Path(AWROOT)
rows=[r for r in m.rows('paper','tasks') if r['benchmark']=='AppWorld']
manifest={r['task_id']:r for r in json.loads((m.PACKAGE/'metadata/appworld_reconstruction.json').read_text())}
for r in rows:m.reconstruct_task(r,manifest,root)
cache={};candidates=[r for r in m.rows('paper','evaluation') if r['benchmark']=='AppWorld']
for r in candidates:
 raw=m.reconstruct_candidate(r,root,cache)
 assert hashlib.sha256(raw).hexdigest()==r['candidate_view_sha256']
assert len(rows)==28
print(json.dumps({'tasks':len(rows),'candidates':len(candidates),'frozen_hashes_verified':True}))
""".replace('SCRIPTS', repr(str(self.runtime/'dataset/scripts'))).replace('AWROOT', repr(str(root)))
        result = self.python_json(self.sources/'_venv_swe/bin/python', code)
        # Import AppWorld's unpacked native implementations, not only package metadata.
        self.command([python, '-c', 'import appworld; from appworld import AppWorld; from appworld.task import Task'])
        return self.receipt('appworld-data', dict(result, version='0.1.3.post1', source='official appworld CLI', verified=True))

    def agentdojo_layout(self, scope):
        python = self.sources/'_venv_ad/bin/python'
        package = Path(self.python_json(python, "import agentdojo,json;from pathlib import Path;print(json.dumps(str(Path(agentdojo.__file__).resolve().parent)))"))
        src = self.sources/'_new/agentdojo/src'; src.mkdir(parents=True, exist_ok=True)
        link = src/'agentdojo'
        if link.exists() or link.is_symlink():
            if not link.is_symlink() or link.resolve() != package:
                raise SetupError('Existing AgentDojo source import path differs from installed pinned package')
        else: link.symlink_to(package, target_is_directory=True)
        selected = [x for x in scope if x['benchmark'].startswith('AgentDojo')]
        code = """import json
from agentdojo.task_suite.load_suites import get_suites
suites=get_suites('v1.2');rows=TASKS
for row in rows:
 name,tid=row['source_task_id'].split('/',1)
 suite=suites[name]
 tasks=suite.injection_tasks if row['benchmark'].endswith('injection') else suite.user_tasks
 assert tid in tasks,row['source_task_id']
assert len(rows)==20
print(json.dumps({'tasks':len(rows),'suite_version':'v1.2','domains':sorted({r['source_task_id'].split('/')[0] for r in rows})}))
""".replace('TASKS', repr(selected))
        result = self.python_json(python, code)
        return self.receipt('agentdojo-source', dict(result, installed_package=str(package), import_path=str(src), verified=True))

    def tau_tasks(self, scope):
        selected = [x for x in scope if x['benchmark']=='τ²-bench']
        code = """import sys,json
sys.path.insert(0, HELPERS)
import tau2_all
from tau2.registry import registry
rows=TASKS;domains={}
for row in rows:
 domain,tid=row['source_task_id'].split('/',1)
 if domain not in domains:domains[domain]={t.id for t in registry.get_tasks_loader(domain)()}
 assert tid in domains[domain],row['source_task_id']
assert len(rows)==32 and set(domains)=={'retail','banking_knowledge'}
assert tau2_all.BANKING_VARIANT=='bm25'
print(json.dumps({'tasks':len(rows),'domains':{d:sum(r['source_task_id'].startswith(d+'/') for r in rows) for d in domains},'retrieval_variant':tau2_all.BANKING_VARIANT}))
""".replace('HELPERS', repr(str(self.runtime/'pipeline/data/tau2_full'))).replace('TASKS', repr(selected))
        return self.receipt('tau2-tasks', dict(self.python_json(self.sources/'_venv_tau2/bin/python', code), verified=True))

    def swe_cache(self, scope):
        python = self.sources/'_venv_swe/bin/python'; expected = [x for x in scope if x['benchmark']=='SWE-bench Verified']
        receipt = self.out/'swe-cache.json'
        if not receipt.exists():
            code = ("from datasets import load_dataset; from huggingface_hub import hf_hub_download; "
                    + "hf_hub_download(repo_id="+repr(SWE_REPO)+",revision="+repr(SWE_REVISION)
                    + ",repo_type='dataset',filename="+repr(SWE_PARQUET)+"); "
                    + "d=load_dataset("+repr(SWE_REPO)+", revision="+repr(SWE_REVISION)+", split='test'); assert len(d)==500")
            self.command([python, '-c', code])
        offline = dict(self.environment, HF_HUB_OFFLINE='1', HF_DATASETS_OFFLINE='1')
        # Exact same no-revision API call as original cap_swe, in a separate offline
        # process. Compare every cached row against the pinned, SHA-checked parquet.
        code = ("from datasets import load_dataset; from huggingface_hub import hf_hub_download; "
                + "import pyarrow.parquet as pq; import json,hashlib; "
                + "p=hf_hub_download(repo_id="+repr(SWE_REPO)+",revision="+repr(SWE_REVISION)
                + ",repo_type='dataset',filename="+repr(SWE_PARQUET)+",local_files_only=True); "
                + "assert hashlib.sha256(open(p,'rb').read()).hexdigest()=="+repr(SWE_PARQUET_SHA256)+"; "
                + "d=list(load_dataset("+repr(SWE_REPO)+",split='test')); "
                + "assert d==pq.read_table(p).to_pylist(); "
                + "print(json.dumps([{'instance_id':r['instance_id'],'base_commit':r['base_commit'],'problem_statement':r['problem_statement']} for r in d]))")
        rows = self.python_json(python, code, env=offline)
        verified = validate_swe_rows(rows, expected)
        return self.receipt('swe-cache', {'repo_id': SWE_REPO, 'revision': SWE_REVISION, 'official_dataset_tasks':500,
                                        'parquet_sha256': SWE_PARQUET_SHA256, 'frozen_tasks_verified': len(verified), 'public_bindings': verified,
                                        'offline_original_api_verified': True, 'verified': True})

    def swe_images(self, scope):
        records = json.loads((self.runtime/'environment/observed_execution_host.json').read_text())['swe_images']
        expected = {x['source_task_id'] for x in scope if x['benchmark']=='SWE-bench Verified'}
        if len(expected) != 47 or set(records) != expected:
            raise SetupError('SWE image manifest must match all 47 frozen tasks exactly')
        output = {}
        for name, record in records.items():
            refs=record.get('repo_digests') or []
            if not refs or not re.fullmatch(r'[^\s@]+@sha256:[0-9a-f]{64}',refs[0]):
                raise SetupError('Missing immutable image RepoDigest for ' + name)
            query = self.command(['docker','image','inspect',refs[0]],allow_failure=True)
            pulled = False
            if query.returncode:
                root_result = self.command(['docker','info','--format','{{json .DockerRootDir}}'])
                docker_root = json.loads(root_result.stdout)
                if not isinstance(docker_root, str) or not docker_root or not Path(docker_root).is_absolute():
                    raise SetupError('Cannot identify Docker storage filesystem before pull')
                try:
                    work_free = shutil.disk_usage(self.work).free
                    docker_free = shutil.disk_usage(docker_root).free
                except OSError as error:
                    raise SetupError('Cannot inspect Docker storage free space: ' + str(error)) from error
                guard = {'workspace':str(self.work),'workspace_free_bytes':work_free,
                         'docker_root':docker_root,'docker_free_bytes':docker_free,'minimum_bytes':100*GIB}
                self.receipt('image-storage-guard-'+name, guard)
                if min(work_free,docker_free) < 100 * GIB:
                    raise SetupError('Less than 100 GiB available on workspace or Docker storage before a new SWE image pull')
                self.command(['docker','pull',refs[0]])
                query=self.command(['docker','image','inspect',refs[0]]);pulled=True
            output[name] = dict(validate_image_inspect(record,json.loads(query.stdout)),pulled_this_run=pulled)
            self.receipt('image-'+name, output[name])
        return self.receipt('swe-images', {'count':len(output),'images':output,'verified':True})

    def run(self):
        self.preflight();self.tau_source()
        for name in ('aw','ad','tau2','swe'): self.packages(name)
        scope=self.frozen_scope()
        self.appworld_data(scope);self.agentdojo_layout(scope);self.tau_tasks(scope)
        self.swe_cache(scope);self.swe_images(scope)
        exports={k:self.environment[k] for k in ('PYTHONDONTWRITEBYTECODE','VGB_SRC_ROOT','APPWORLD_ROOT','TAU2_DATA_DIR','V4V_TAU2_RETRIEVAL','VGB_AD_SUITE_VERSION','HF_HOME','HF_DATASETS_CACHE')}
        exports.update(HF_HUB_OFFLINE='1',HF_DATASETS_OFFLINE='1')
        result={'workspace':str(self.work),'runtime':str(self.runtime),'environment':exports,
                'phases':self.steps,'verified':True,'models_called':0,'benchmark_candidates_executed':0}
        atomic_json(self.out/'complete.json',result)
        return result


def setup_native(workspace, python312, runtime_root, run_command=None):
    return NativeSetup(workspace, python312, runtime_root, run_command).run()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',required=True,type=Path)
    parser.add_argument('--python',required=True,type=Path)
    parser.add_argument('--runtime',required=True,type=Path)
    args=parser.parse_args()
    result=setup_native(args.workspace,args.python,args.runtime)
    print(json.dumps({'verified':result['verified'],'environment':result['environment'],
                      'receipt':str(args.workspace/'native-setup/complete.json')},indent=2))


if __name__=='__main__':main()
