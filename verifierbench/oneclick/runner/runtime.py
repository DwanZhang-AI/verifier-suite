"""Current process/resource evidence; no old-run result fallback."""
import collections,json,os,time
from pathlib import Path
from config import load,paths
from dispatch import identity,same_identity,resources,read_json,worker_task

def sample():
    cfg=load();w,a,_,_=paths(cfg);s=Path(__file__).resolve().parent
    rows=read_json(w/'tasks.json');state=read_json(a/'dispatch-state.json',{});denied=set(read_json(w/'content-denial-tasks.json',{'tasks':[]})['tasks'])
    phases=collections.Counter();active=[];unresolved=[]
    for row in rows:
        tid=row['task_id'];status=read_json(a/'task-status'/(tid+'.json'),{});phase=status.get('phase','pending')
        if tid in denied and phase in ('pending','needs_review'):phase='blocked_content_denial'
        phases[phase]+=1;claim=read_json(a/'launch-claims'/(tid+'.json'),{})
        expected=claim.get('worker_identity');actual=identity(expected['pid']) if expected else None
        if same_identity(actual,expected) and worker_task(actual,s/'task_worker.py')==tid:
            active.append({'task':tid,'benchmark':row['benchmark'],'phase':phase,'identity':actual,'elapsed_sec':time.time()-status.get('started',time.time())})
        elif claim and phase not in ('complete','needs_review','blocked_content_denial'):unresolved.append(tid)
    controller=identity(state.get('pid',0));alive=same_identity(controller,state.get('controller_identity'))
    return dict(at=time.time(),run_id=cfg['run_id'],model=cfg['model'],phases=dict(phases),active=active,actual_active=len(active),configured_max=state.get('configured_max',cfg['max_workers']),adaptive_cap=state.get('adaptive_cap'),cooldown_until=state.get('cooldown_until'),holds=state.get('holds'),controller=controller if alive else None,controller_alive=alive,unresolved_claims=unresolved,resources=resources(w),all_terminal=all(p in ('complete','needs_review','blocked_content_denial') for p in phases),historical_results_used=False)

if __name__=='__main__':print(json.dumps(sample(),ensure_ascii=False))
