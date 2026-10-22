"""One resumable dispatcher per workspace, with immutable task claims.

Live workers are adopted by PID/boot/start/argv. Completed and failed task units
are never duplicated. Resource gates and adaptive rate-limit cooldowns persist.
"""
import collections
from contextlib import ExitStack
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from config import load,paths
S=Path(__file__).resolve().parent
W=A=PY=None
LIVE_PHASES = {'preparing', 'generating', 'scoring'}
TERMINAL_PHASES = {'complete', 'needs_review'}
AST_BENCHMARKS = {'BFCL v4', 'ACEBench'}


def read_json(path, default=None):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def identity(pid, proc=Path('/proc')):
    """Read start ticks before and after argv to reject PID reuse and zombies."""
    try:
        root = proc / str(int(pid))
        first = (root / 'stat').read_text().split(') ', 1)[1].split()
        argv = (root / 'cmdline').read_bytes().split(b'\0')
        second = (root / 'stat').read_text().split(') ', 1)[1].split()
        if first[19] != second[19] or second[0] == 'Z':
            return None
        return {'pid': int(pid), 'start_ticks': second[19],
                'boot_id': (proc / 'sys/kernel/random/boot_id').read_text().strip(),
                'argv': [x.decode(errors='replace') for x in argv if x]}
    except (FileNotFoundError, ProcessLookupError):
        return None


def same_identity(actual, expected):
    return bool(actual and expected and all(str(actual.get(k)) == str(expected.get(k))
                                           for k in ('pid', 'start_ticks', 'boot_id', 'argv')))


def worker_task(ident, script):
    if not ident or str(script) not in ident['argv']:
        return None
    argv = ident['argv']
    try:
        return argv[argv.index('--task') + 1]
    except (ValueError, IndexError):
        return None


def resource_reserve(row, state):
    scoring = state.get('phase') == 'scoring'
    if row['benchmark'] in AST_BENCHMARKS:
        return 0.5 if scoring else 2.0
    if row['benchmark'] == 'SWE-bench Verified':
        return 4.0 if scoring else 6.0
    return 2.0 if scoring else 4.0


def update_backoff(cap, cooldown, last_rate, audit_rows, now, maximum):
    rate = max([float(r.get('ended', 0)) for r in audit_rows if r.get('status') == 429] + [0])
    if rate > last_rate:
        return max(1, cap // 2), max(cooldown, rate + 120), rate
    if now > max(last_rate, cooldown) + 600 and cap < maximum:
        return cap + 1, now, last_rate
    return cap, cooldown, last_rate


def protocol_errors(rows, denied):
    """Only task-bound, already registered content refusals leave the hold."""
    errors = []
    for row in rows:
        status = row.get('status')
        known_denial = status == 403 and any(
            '/t/' + prefix + task + '/' in str(row.get('path', ''))
            for task in denied for prefix in ('vgb-'+load()['run_id']+'-',))
        if status in (400, 401) or (status == 403 and not known_denial):
            errors.append({'status': status, 'ended': row.get('ended'),
                           'reason': 'unregistered_content_refusal' if status == 403 else 'protocol_error'})
    return errors


def read_audit(path):
    """An unfinished append is ignored; malformed complete records fail closed."""
    try:
        raw = path.read_text()
    except FileNotFoundError:
        return []
    lines = raw.splitlines()
    if raw and not raw.endswith('\n'):
        lines = lines[:-1]
    return [json.loads(line) for line in lines if line.strip()]



def resources(work):
    mem = next(int(line.split()[1]) / 1048576 for line in Path('/proc/meminfo').read_text().splitlines()
               if line.startswith('MemAvailable:'))
    docker_root=Path(subprocess.check_output(['docker','info','--format','{{.DockerRootDir}}'],text=True).strip())
    if not docker_root.is_absolute() or not docker_root.is_dir():raise RuntimeError('Docker root filesystem is not locally observable')
    workspace_free=shutil.disk_usage(work).free / 2**30;docker_free=shutil.disk_usage(docker_root).free / 2**30
    return {'cpu': os.cpu_count(), 'load': list(os.getloadavg()),
            'mem_available_gib': mem, 'disk_free_gib': min(workspace_free,docker_free),
            'workspace_free_gib':workspace_free,'docker_root':str(docker_root),'docker_free_gib':docker_free}


def task_ready(work, row):
    if row['benchmark'] != 'SWE-bench Verified':
        return True
    info = read_json(work / 'swe-images' / (row['source_task_id'] + '.json'), {})
    return info.get('ok') is True


def startup_failures(aligned, rows):
    """Fail closed across the run if any attempt failed before result capture.

    Absence of a generation result does not itself prove zero model calls. This
    guard only stops new dispatch; it never retries, deletes or clears a failure.
    """
    failures = []
    for row in rows:
        tid = row['task_id']
        state = read_json(aligned / 'task-status' / (tid + '.json'), {})
        if state.get('phase') == 'needs_review' and not (aligned / 'generation-results' / (tid + '.json')).exists():
            failures.append({'task': tid, 'phase': 'needs_review',
                             'reason': 'missing_generation_result'})
    return failures


def main():
    global W,A,PY
    cfg=load();W,A,_,_=paths(cfg);PY=cfg['generation_python']
    A.mkdir(parents=True, exist_ok=True)
    with ExitStack() as locks:
        for path in (W / 'dispatch.lock', A / 'controller.lock'):
            fd = locks.enter_context(path.open('a'))
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run_controller()


def run_controller():
    plan = read_json(A / 'plan.json')
    rows = plan['tasks']
    assert len({r['task_id'] for r in rows}) == len(rows)
    maximum = int(plan['max_workers'])
    assert 1 <= maximum <= 6
    runs = read_json(A / 'task-runs.json')
    run_ids = {r['task_id'] for r in runs}
    assert {r['task_id'] for r in rows} <= run_ids
    old = read_json(A / 'dispatch-state.json', {})
    cap = int(old.get('adaptive_cap', plan['initial_adaptive_cap']))
    cooldown = float(old.get('cooldown_until', plan['initial_cooldown_until']))
    last_rate = float(old.get('last_rate_error', plan['last_rate_error']))
    assert 1 <= cap <= maximum
    for name in ('task-status', 'launch-claims', 'worker-logs'):
        (A / name).mkdir(exist_ok=True)
    controller = identity(os.getpid())
    children = {}
    while True:
        now = time.time()
        denied = set(read_json(W / 'content-denial-tasks.json', {'tasks': []})['tasks'])
        audit = read_audit(W / 'responses-transport-audit.jsonl')
        cap, cooldown, last_rate = update_backoff(cap, cooldown, last_rate, audit, now, maximum)
        errors = protocol_errors(audit, denied)
        statuses = {r['task_id']: read_json(A / 'task-status' / (r['task_id'] + '.json'), {}) for r in rows}
        active = []
        claimed_unresolved = []
        for row in rows:
            tid = row['task_id']
            claim = read_json(A / 'launch-claims' / (tid + '.json'))
            if not claim:
                continue
            expected = claim.get('worker_identity')
            actual = identity(expected['pid']) if expected else None
            if same_identity(actual, expected) and worker_task(actual, S / 'task_worker.py') == tid:
                active.append(dict(actual, task=tid, benchmark=row['benchmark'],
                                   phase=statuses[tid].get('phase', 'launching'),
                                   reserve_gib=resource_reserve(row, statuses[tid])))
            elif statuses[tid].get('phase') not in TERMINAL_PHASES:
                claimed_unresolved.append(tid)
                # Do not launch it again, including after an interrupted controller launch.
        for tid, (child, log) in list(children.items()):
            rc = child.poll()
            if rc is not None:
                log.close()
                del children[tid]
                state = read_json(A / 'task-status' / (tid + '.json'), {})
                if state.get('phase') not in TERMINAL_PHASES:
                    save_json(A / 'task-status' / (tid + '.json'), dict(state, task=tid,
                        phase='needs_review', error='worker exited before terminal status',
                        returncode=rc, ended=now))
        remaining = [r for r in rows if r['task_id'] not in denied and not statuses[r['task_id']]
                     and not (A / 'launch-claims' / (r['task_id'] + '.json')).exists()]
        sample = resources(W)
        held = sum(x['reserve_gib'] for x in active)
        launched = []
        skipped = []
        holds = []
        startup_faults = startup_failures(A, rows)
        if startup_faults:
            holds.append('startup_failure_before_generation')
        if errors:
            holds.append('protocol_errors')
        if claimed_unresolved:
            holds.append('unresolved_launch_claim')
        if sample['disk_free_gib'] < 50:
            holds.append('disk_runtime_guard_below_50GiB_no_new_launch')
        elif sample['disk_free_gib'] < 100:
            holds.append('disk_start_gate_below_100GiB')
        if now < cooldown:
            holds.append('adaptive_cooldown')
        if sample['load'][0] > 16:
            holds.append('load_above_16')
        for row in remaining:
            # Recheck between launches, not only on the next 15-second sample.
            # A fast package/import failure must not consume the whole queue.
            if not startup_faults:
                startup_faults = startup_failures(A, rows)
                if startup_faults:
                    holds.append('startup_failure_before_generation')
            if holds or len(active) >= cap:
                break
            tid = row['task_id']
            if not task_ready(W, row):
                skipped.append({'task': tid, 'reason': 'SWE_image_not_ready'})
                continue
            reserve = resource_reserve(row, {})
            if sample['mem_available_gib'] - held - reserve < 2:
                skipped.append({'task': tid, 'reason': 'memory_reservation_plus_2GiB_headroom'})
                continue
            # Content denials can be registered by a finishing worker since the sample.
            if tid in set(read_json(W / 'content-denial-tasks.json', {'tasks': []})['tasks']):
                continue
            tasklock = (W / 'locks' / tid).open('a')
            try:
                try:
                    fcntl.flock(tasklock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    skipped.append({'task': tid, 'reason': 'task_lock_held'})
                    continue
                claim_path = A / 'launch-claims' / (tid + '.json')
                try:
                    with claim_path.open('x') as f:
                        json.dump({'task': tid, 'claimed_at': time.time(), 'controller': controller}, f)
                        f.flush()
                        os.fsync(f.fileno())
                except FileExistsError:
                    continue
            finally:
                tasklock.close()
            log = (A / 'worker-logs' / (tid + '.log')).open('ab')
            cmd = [PY, str(S / 'task_worker.py'), '--task', tid]
            child = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                                     stdin=subprocess.DEVNULL, start_new_session=True, cwd=A)
            children[tid] = (child, log)
            ident = identity(child.pid)
            # Popen may return before exec has replaced the inherited cmdline.
            deadline = time.monotonic() + 2
            while ident and worker_task(ident, S / 'task_worker.py') != tid and time.monotonic() < deadline:
                time.sleep(0.02)
                ident = identity(child.pid)
            if worker_task(ident, S / 'task_worker.py') != tid:
                ident = None
            claim = {'task': tid, 'launched_at': time.time(), 'controller': controller,
                     'worker_identity': ident, 'command': cmd, 'reserve_gib': reserve}
            save_json(claim_path, claim)
            with (A / 'dispatch-events.jsonl').open('a') as f:
                f.write(json.dumps(claim) + '\n')
            launched.append(claim)
            if ident:
                active.append(dict(ident, task=tid, benchmark=row['benchmark'], phase='launching', reserve_gib=reserve))
            else:
                holds.append('worker_identity_unconfirmed')
            held += reserve
        statuses = {r['task_id']: read_json(A / 'task-status' / (r['task_id'] + '.json'), {}) for r in rows}
        counts = collections.Counter(s.get('phase', 'pending') if tid not in denied or s else 'excluded_content_denial'
                                     for tid, s in statuses.items())
        out = dict(sample, at=time.time(), controller_identity=controller, pid=os.getpid(),
                   active=active, counts=dict(counts), configured_max=maximum,
                   adaptive_cap=cap, cooldown_until=cooldown, last_rate_error=last_rate,
                   protocol_error_hold=bool(errors), protocol_errors=errors,
                   holds=holds, reserved_gib=held, skipped=skipped,
                   startup_failures=startup_faults,
                   newly_started=[x['task'] for x in launched], planned_tasks=len(rows),
                   denied_tasks=sorted(set(statuses) & denied), claimed_unresolved=claimed_unresolved,
                   remaining_unstarted=len(remaining) - len(launched), outputs_preserved=True)
        save_json(A / 'dispatch-state.json', out)
        all_terminal = all(s.get('phase') in TERMINAL_PHASES or (tid in denied and not s)
                           for tid, s in statuses.items())
        if all_terminal and not active:
            save_json(A / 'ended.json', dict(out, ended=time.time()))
            return
        time.sleep(15)


if __name__ == '__main__':
    main()
