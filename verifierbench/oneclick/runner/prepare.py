"""Seal all 222 public packages with the original Gavel composer; no model calls."""
from __future__ import annotations
import collections,hashlib,json,os,shutil,sys,time
from pathlib import Path
from urllib.parse import urlsplit
from config import load,paths,save_json,REVISION

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def write_atomic(path,obj):
    tmp=path.with_name('.'+path.name+'.'+str(os.getpid())+'.tmp')
    with tmp.open('w') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def prepared_packages(rows,packages,inputs_for,build,validate):
    """Build one package per row, reusing packages an interrupted run already sealed.

    `<task>.prepared.json` next to a package is written only after the package is
    sealed and verified, together with the inputs it was built from. A package
    directory without it was interrupted before sealing finished and is rebuilt;
    building calls no model. A receipt whose inputs differ, or a sealed package
    that no longer verifies, stops preparation.
    """
    packages.mkdir(parents=True,exist_ok=True);runs=[]
    for row in rows:
        tid=row['task_id'];pkg=packages/tid;done=packages/(tid+'.prepared.json');inputs=inputs_for(row)
        if done.exists():
            receipt=json.loads(done.read_text())
            if receipt.get('inputs')!=inputs:raise RuntimeError('Package '+tid+' was prepared from different inputs; inspect before retry')
            if not pkg.is_dir() or validate(pkg)!='verified':raise RuntimeError('Prepared package integrity failed: '+tid)
            runs.append(receipt['run']);continue
        if pkg.exists():shutil.rmtree(pkg)
        run=build(row,pkg)
        write_atomic(done,{'inputs':inputs,'run':run})
        runs.append(run)
    return runs

def prepare(cfg):
    w,a,r,h=paths(cfg);s=Path(__file__).resolve().parent
    os.environ['VGB_GENERATION_IMAGE']=cfg['generation_image']
    from adapter_contract import prepare_package,AST_BENCHMARKS,RUNTIME_CONTRACT
    for name in ('locks','generation-inputs'): (w/name).mkdir(parents=True,exist_ok=True)
    a.mkdir(parents=True,exist_ok=True)
    config_sha=sha(Path(cfg['config_path']))
    manifest=json.loads((r/'MANIFEST.json').read_text())
    for pin in manifest['files']:
        p=r/pin['path']
        if not p.resolve().is_relative_to(r.resolve()) or sha(p)!=pin['sha256']:raise ValueError('Runtime integrity failed: '+pin['path'])
    runtime_sha=sha(r/'MANIFEST.json');rows=json.loads((w/'tasks.json').read_text())
    freeze=json.loads((r/'paper/freeze.json').read_text())
    if len(rows)!=222 or {t['task_id'] for t in rows}!=set(freeze['tasks']):raise ValueError('Frozen 222-task scope mismatch')
    files=[{'path':p.name,'sha256':sha(p)} for p in sorted(s.glob('*.py'))]
    if (a/'release.json').exists():
        release=json.loads((a/'release.json').read_text())
        if release['config_sha256']!=config_sha or release['files']!=files or release['runtime_manifest_sha256']!=runtime_sha:raise RuntimeError('Existing run configuration/code changed; refusing to mutate or duplicate it')
        runs=json.loads((a/'task-runs.json').read_text());plan=json.loads((a/'plan.json').read_text())
        if len(runs)!=222 or len(plan['tasks'])!=222:raise RuntimeError('Incomplete prior preparation; inspect before retry')
        sys.path.insert(0,str(h));from judge.core.package_inputs import validate_materialized
        for run in runs:
            if validate_materialized(run['package_dir'])!='verified':raise RuntimeError('Existing package integrity failed')
        return {'status':'already_prepared','packages':222,'new_model_calls':0}
    denied=w/'content-denial-tasks.json'
    if not denied.exists():
        with denied.open('x') as f:json.dump({'tasks':[],'receipts':{}},f)
    # Unlike experiment migration, a new portable run must not import prior status/results.
    if any((a/name).exists() for name in ('task-status','generation-results','verdicts','launch-claims')):raise RuntimeError('Unbound result directory present; refusing historical result import')
    def inputs_for(row):
        return {'config_sha256':config_sha,'runner_files':files,'runtime_manifest_sha256':runtime_sha,
                'task_spec_sha256':row['task_spec_sha256'],'effective_spec_sha256':row['effective_spec_sha256']}
    def build(row,pkg):
        spec=w/'generation-inputs'/row['task_id']/'task_spec.public.json'
        return prepare_package(pkg,row,spec.read_bytes(),r,h,expected_runtime_manifest_sha256=runtime_sha,model=cfg['model'],generation_timeout=cfg['generation_timeout'],allowed_host=urlsplit(cfg['api_base_url']).hostname)
    sys.path.insert(0,str(h))
    try:
        from judge.core.package_inputs import validate_materialized
        runs=prepared_packages(rows,a/'packages',inputs_for,build,lambda pkg:validate_materialized(str(pkg)))
    finally:
        sys.path.remove(str(h))
    # Deterministic category first pass; unrelated to scores or labels.
    order=['AppWorld','τ²-bench','AgentDojo user','AgentDojo injection','BFCL v4','ACEBench','SWE-bench Verified'];lead=[]
    for bm in order:lead.append(next(t for t in rows if t['benchmark']==bm))
    ids={t['task_id'] for t in lead};ordered=lead+[t for t in rows if t['task_id'] not in ids]
    plan={'revision':REVISION,'tasks':ordered,'max_workers':cfg['max_workers'],'initial_adaptive_cap':cfg['max_workers'],'initial_cooldown_until':0,'last_rate_error':0,'runtime_manifest_sha256':runtime_sha,'generation_environment_contract':RUNTIME_CONTRACT,'at':time.time()}
    release={'revision':REVISION,'files':files,'config_sha256':config_sha,'runtime_manifest_sha256':runtime_sha,'generation_python':'3.12.14','generation_image':cfg['generation_image'],'generation_image_id':cfg['generation_image_id'],'generation_site_packages_sha256':cfg['generation_site_packages_sha256'],'model':cfg['model']}
    # release.json is written last: its presence marks a complete preparation.
    for path,obj in ((a/'task-runs.json',runs),(a/'plan.json',plan),(a/'release.json',release)):write_atomic(path,obj)
    result={'status':'prepared','packages':222,'by_benchmark':dict(collections.Counter(t['benchmark'] for t in rows)),'runtime_manifest_sha256':runtime_sha,'config_sha256':config_sha,'new_model_calls':0}
    save_json(a/'preparation-receipt.json',result);return result

if __name__=='__main__':print(json.dumps(prepare(load()),ensure_ascii=False))
