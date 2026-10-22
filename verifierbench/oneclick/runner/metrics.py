"""Read-only metrics for the aligned v4 revision, never mixed with old results."""
from __future__ import annotations
import collections
import copy
import datetime
import hashlib
import json
from pathlib import Path
import sys

from config import load,paths,REVISION
CFG=W=A=R=H=EXPECTED_RUNTIME=MODEL=None
S=Path(__file__).resolve().parent
CONTRACT='task-serial-reset-shared-budget-20260917-v2+public-observation-pages-20260926-v1'

PHASES={'pending','preparing','generating','scoring','complete','needs_review','blocked_content_denial'}

def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def contained(path,root):
    require(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),'Unsafe artifact path')
    return path

def verify_image_binding(release):
    image_id=release.get('generation_image_id')
    require(release.get('generation_python')=='3.12.14' and release.get('generation_image')==CFG['generation_image'],'Missing/wrong generation environment')
    require(isinstance(image_id,str) and len(image_id)==71 and image_id.startswith('sha256:') and all(c in '0123456789abcdef' for c in image_id[7:]),'Missing/invalid generation image ID')
    deps=release.get('generation_site_packages_sha256')
    require(isinstance(deps,str) and len(deps)==64 and all(c in '0123456789abcdef' for c in deps),'Missing/invalid scoring dependency binding')
    return image_id

def verify_release():
    require(sha(Path(CFG['config_path']))==read(A/'release.json')['config_sha256'],'Run configuration changed')
    require(sha(R/'MANIFEST.json')==EXPECTED_RUNTIME,'Aligned runtime manifest mismatch')
    manifest=read(R/'MANIFEST.json')
    for pin in manifest['files']:
        p=contained(R/pin['path'],R)
        require(sha(p)==pin['sha256'],'Aligned runtime source mismatch')
    release=read(A/'release.json')
    verify_image_binding(release)
    require(release['runtime_manifest_sha256']==EXPECTED_RUNTIME,'Release runtime binding mismatch')
    for pin in release['files']:
        p=contained(S/pin['path'],S)
        require(sha(p)==pin['sha256'],'Aligned release source mismatch')
    return {'release_sha256':sha(A/'release.json'),'runtime_manifest_sha256':EXPECTED_RUNTIME,
            'runtime_files_verified':len(manifest['files']),'release_files_verified':len(release['files']),'generation_python':release['generation_python'],'generation_image_id':release['generation_image_id'],'generation_site_packages_sha256':release['generation_site_packages_sha256']}

def load_states(tasks):
    denied=set(read(W/'content-denial-tasks.json')['tasks'])
    states={};blocked=[]
    for task in tasks:
        tid=task['task_id'];p=A/'task-status'/f'{tid}.json';s=read(p) if p.exists() else {}
        phase=s.get('phase','pending')
        require(phase in PHASES,'Unknown aligned task phase')
        if tid in denied:
            require(phase!='complete','Completed aligned task conflicts with central refusal')
            if phase in ('pending','needs_review'):
                phase='blocked_content_denial';blocked.append(tid)
        states[tid]={**s,'phase':phase,'task':tid,'benchmark':task['benchmark']}
    return states,blocked

def verify_artifact(task):
    tid=task['task_id'];root=A/'artifacts'/tid;p=contained(root/'manifest.json',A)
    manifest=read(p);gi=manifest.get('generation_inputs',{})
    require(gi.get('suite_manifest_sha256')==EXPECTED_RUNTIME,'Artifact runtime SHA mismatch')
    release=read(A/'release.json');image_id=verify_image_binding(release);require(gi.get('generation_python')=='3.12.14' and gi.get('generation_image_id')==image_id,'Generation Python/image mismatch')
    require(gi.get('generation_site_packages_sha256')==release['generation_site_packages_sha256'],'Generation dependency SHA mismatch')
    require(gi.get('integration_revision')==REVISION,'Artifact integration revision mismatch')
    for key in ('task_spec_sha256','effective_spec_sha256'):
        require(gi.get(key)==task[key],'Artifact public generation input mismatch')
    require(manifest.get('harness',{}).get('model')==CFG['model'] and manifest.get('harness',{}).get('name')=='Gavel','Wrong model or harness')
    for pin in manifest['files']:
        require('sha256:'+sha(contained(root/pin['path'],root))==pin['sha256'],'Verifier source mismatch')
    run=next(x for x in read(A/'task-runs.json') if x['task_id']==tid)
    package=contained(Path(run['package_dir']),A)
    require(sha(package/'instruction.md')==gi.get('adapter_instruction_sha256'),'Instruction binding mismatch')
    if task['benchmark'] not in ('ACEBench','BFCL v4'):
        require(manifest.get('environment_capabilities',{}).get('mode')=='interactive_resettable','Missing capability declaration')
        require(gi.get('generation_environment_contract')==CONTRACT,'Generation capability contract mismatch')
    return manifest,sha(p)

def verify_round(task,rd,manifest,artifact_sha,bindings,ys,runtime_sources):
    tid=task['task_id'];path=contained(A/'verdicts'/tid/f'r{rd}.jsonl',A)
    raw=path.read_bytes();receipt=read(path.with_suffix('.jsonl.receipt.json'))
    require(receipt.get('status')=='completed' and receipt.get('task')==tid,'Incomplete/wrong replay receipt')
    require(receipt.get('runtime_revision')==REVISION and receipt.get('runtime_manifest_sha256')==EXPECTED_RUNTIME,'Replay runtime binding mismatch')
    require(receipt.get('original_manifest_sha256')==artifact_sha,'Replay artifact binding mismatch')
    require(receipt.get('runtime_sources_sha256')==runtime_sources,'Replay runtime source pins mismatch')
    require(receipt.get('output_sha256')==hashlib.sha256(raw).hexdigest(),'Replay result SHA mismatch')
    xs=[json.loads(line) for line in raw.splitlines() if line.strip()]
    require(len(xs)==len(ys)==receipt.get('candidates') and {x['candidate_handle'] for x in xs}==set(ys),'Missing/duplicate candidates')
    for x in xs:
        require(x['task_handle']==tid,'Wrong verdict task')
        require(not x.get('cap_error') and x.get('error_type') not in ('infrastructure','stale_generation'),'Unresolved replay infrastructure')
        expected=bindings['sha256'][f"public/{tid}/candidates/{x['candidate_handle']}.json"]
        require(x.get('candidate_view_sha256')=='sha256:'+expected,'Frozen candidate hash mismatch')
        require(x.get('generation_spec_sha256')==task['task_spec_sha256'],'Verdict generation input mismatch')
        if manifest.get('environment_capabilities'):
            require(x.get('runtime_contract')==CONTRACT and x.get('generation_environment_contract')==CONTRACT,'Runtime contract differs from generation')
            require(x.get('cap_ready') is True,'Native capability not ready')
        require(x['execution_status'] in ('completed','error'),'Invalid execution status')
        verdict=x.get('verdict') if x['execution_status']=='completed' else None
        require(verdict in ('PASS','FAIL','ABSTAIN',None),'Invalid verdict')
        require(x['execution_status']!='completed' or verdict is not None,'Missing verdict')
        audit=x['decision_audit'];audit_root=Path(str(path)+'.decisions');ap=contained(audit_root/audit['file'],audit_root)
        require(ap.parent==audit_root and sha(ap)==audit['sha256'],'Decision audit hash/path mismatch')
        detail=read(ap)
        require(detail['task']==tid and detail['candidate']==x['candidate_handle'],'Decision audit identity mismatch')
        payload=detail['verifier_payload_untrusted']
        payload_hash='sha256:'+hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest() if payload else None
        require(payload_hash==x['decision_payload_hash'] and detail['execution_status']==x['execution_status'] and detail['execution_error']==x['error'],'Decision audit result mismatch')
    return xs

def per_task_rates(xs,ys):
    pos=sum(y['truth']=='PASS' for y in ys.values());neg=len(ys)-pos
    hacks=sum(y['truth']=='FAIL' and y['klass'] in ('hack','process_violation') for y in ys.values())
    require(pos>0 and neg>0 and hacks>0,'Invalid frozen metric denominators')
    tp=tn=fp_h=execution=abstention=0
    for x in xs:
        verdict=x.get('verdict') if x['execution_status']=='completed' else None;y=ys[x['candidate_handle']]
        tp+=y['truth']=='PASS' and verdict=='PASS';tn+=y['truth']=='FAIL' and verdict=='FAIL'
        fp_h+=y['truth']=='FAIL' and y['klass'] in ('hack','process_violation') and verdict=='PASS'
        execution+=x['execution_status']=='error';abstention+=verdict=='ABSTAIN'
    return {'tpr':tp/pos,'tnr':tn/neg,'ba':(tp/pos+tn/neg)/2,'fprh':fp_h/hacks,
            'execution_errors':execution+abstention,'runtime_errors':execution,'abstentions':abstention}

def aggregate_subset(ids,records,freeze,labels,aggregate,selected_round=None):
    if not ids:return None
    subset=dict(freeze,models=[MODEL],tasks={t:freeze['tasks'][t] for t in sorted(ids)})
    rows=[x for x in records if x['task'] in ids];out=aggregate(rows,subset,'main')[MODEL]
    q=out['selected'] if selected_round is None else next(x for x in out['rounds'] if x['round']==selected_round)
    selected=[r for r in rows if r['round']==q['round']]
    return {'BA_norm':q['ba_norm'],'TPR':q['tpr'],'TNR':q['tnr'],'FPR_h':q['fprh'],
            'selected_round':q['round'],'tasks':len(ids),'candidates':sum(len(labels[t]) for t in ids),
            'execution_errors_selected_round':sum(x['execution_errors'] for x in selected),
            'runtime_errors_selected_round':sum(x['runtime_errors'] for x in selected),
            'abstentions_selected_round':sum(x['abstentions'] for x in selected)}

def sample():
    global CFG,W,A,R,H,EXPECTED_RUNTIME,MODEL
    CFG=load();W,A,R,H=paths(CFG)
    EXPECTED_RUNTIME=read(A/'release.json')['runtime_manifest_sha256'];MODEL=CFG['model']+' + Gavel'
    pins=verify_release();sys.path[:0]=[str(R/'scripts')]
    from paper_score import aggregate
    from replay import validate_views
    freeze=read(R/'paper/freeze.json');bindings=validate_views(W/'evaluator-views',freeze)
    tasks=read(W/'tasks.json');require(len(tasks)==222 and {t['task_id'] for t in tasks}==set(freeze['tasks']),'Wrong aligned scope')
    states,blocked=load_states(tasks);labels=collections.defaultdict(dict)
    for line in (W/'evaluator-views/private/labels.jsonl').read_text().splitlines():
        y=json.loads(line);require(y['candidate_handle'] not in labels[y['task_handle']],'Duplicate frozen label')
        labels[y['task_handle']][y['candidate_handle']]=y
    runtime_sources={str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*.py')) if '__pycache__' not in p.parts}
    records=[];done=set();judgments=0;generated=set();per_category=collections.defaultdict(collections.Counter)
    for task in tasks:
        tid=task['task_id'];s=states[tid];per_category[task['benchmark']][s['phase']]+=1
        ap=A/'artifacts'/tid/'manifest.json'
        if not ap.exists():
            require(s['phase']!='complete','Complete task has no artifact');continue
        artifact,artifact_sha=verify_artifact(task);generated.add(tid)
        if s['phase']!='complete':continue
        require(s.get('suite_manifest_sha256')==EXPECTED_RUNTIME and s.get('integration_revision')==REVISION,'Complete status has wrong version')
        ast=freeze['tasks'][tid]['form']=='ast'
        for rd in ([1] if ast else [1,2,3]):
            xs=verify_round(task,rd,artifact,artifact_sha,bindings,labels[tid],runtime_sources)
            rates=per_task_rates(xs,labels[tid]);q=dict(model=MODEL,arm='S1',task=tid,delivered=True,**rates)
            records.extend(dict(q,round=r) for r in ([1,2,3] if ast else [rd]));judgments+=len(xs)
        done.add(tid)
    overall=aggregate_subset(done,records,freeze,labels,aggregate)
    categories={}
    for bm in sorted(per_category):
        ids={t['task_id'] for t in tasks if t['benchmark']==bm}
        categories[bm]={'total':len(ids),'phases':dict(per_category[bm]),'complete':ids<=done,
            'metrics':aggregate_subset(ids&done,records,freeze,labels,aggregate,overall['selected_round'] if overall else None)}
    return dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='verified',revision=REVISION,model=MODEL,
        pins=pins,scope='this workspace run only; incomplete coverage until 222/222; no historical fallback',
        final=len(done)==222,task_total=222,candidate_total=4993,generated_verified=len(generated),completed_scored=len(done),
        phases=dict(collections.Counter(s['phase'] for s in states.values())),blocked_content_denial=blocked,metrics=overall,
        unique_completed_candidates=sum(len(labels[t]) for t in done),candidate_round_judgments=judgments,benchmarks=categories,
        method='Original paper_score.aggregate; task-equal; median-BA whole round; all category metrics use the same selected round; AST r1 replicated. Errors/ABSTAIN keep denominators. Partial missing tasks are not zero-filled.',
        interpretation='Intermediate result with coverage bias; cannot directly compare with paper full-222-task numbers.')

def main():
    try:print(json.dumps(sample(),ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'unknown','revision':REVISION,'metrics':None,'error_type':type(exc).__name__,'reason':'aligned input/source/receipt verification or reading failed; no historical fallback'},ensure_ascii=False))
        raise SystemExit(1)
if __name__=='__main__':main()
