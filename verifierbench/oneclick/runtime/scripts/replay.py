#!/usr/bin/env python3
"""Replay one verifier against a frozen paper222 task on Linux x86_64."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE_CONTRACT = 'task-serial-reset-shared-budget-20260917-v2'
PAGED_CONTRACT = BASE_CONTRACT+'+public-observation-pages-20260926-v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_views(views, freeze):
    bindings = json.loads((views/'paper222_bindings.json').read_text())
    expected = json.loads((ROOT/'paper/input_hashes.json').read_text())
    if bindings != expected:
        raise ValueError('View bindings differ from the immutable paper222 input hashes')
    if bindings['version'] != freeze['version'] or bindings['tasks'] != 222 or bindings['candidates'] != 4993:
        raise ValueError('Expected frozen paper222 views')
    ids = json.loads((views/'private/id_map.json').read_text())
    if set(ids) != set(freeze['tasks']):
        raise ValueError('Task membership differs from frozen paper222')
    for task, identity in ids.items():
        wanted = freeze['tasks'][task]
        if identity != {'task_id':wanted['source_task_id'], 'benchmark':wanted['benchmark'], 'form':wanted['form']}:
            raise ValueError('Task identity differs from paper222')
    for rel, digest in bindings['sha256'].items():
        p = views/rel
        if not p.resolve().is_relative_to(views.resolve()) or sha(p) != digest:
            raise ValueError('Modified view: '+rel)
    return bindings


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--views', type=Path, required=True)
    p.add_argument('--task', required=True)
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--appworld-root', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--check-only', action='store_true')
    a = p.parse_args()
    freeze = json.loads((ROOT/'paper/freeze.json').read_text())
    if a.task not in freeze['tasks']:
        raise ValueError('Task outside frozen paper222')
    views, bundle, src = a.views.resolve(), a.bundle.resolve(), a.source_root.resolve()
    bindings = validate_views(views, freeze)
    if not src.is_dir():
        raise ValueError('Missing source root')
    manifest = json.loads((bundle/'manifest.json').read_text())
    if manifest.get('generation_inputs', {}).get('suite_manifest_sha256') != sha(ROOT/'MANIFEST.json'):
        raise ValueError('Generation and replay suite manifest SHA differ')
    for record in manifest['files']:
        path = bundle/record['path']
        if not path.resolve().is_relative_to(bundle) or 'sha256:'+sha(path) != record['sha256']:
            raise ValueError('Verifier source/hash mismatch')
    for key in list(os.environ):
        if key.startswith(('VGB_', 'V4V_')):
            del os.environ[key]
    os.environ['VGB_SRC_ROOT'] = str(src)
    os.environ['VGB_DENY_ROOTS'] = os.pathsep.join((str(src), str(views)))
    aw = a.appworld_root.resolve() if a.appworld_root else src/'aw_root'
    os.environ['APPWORLD_ROOT'] = str(aw)
    cap = manifest.get('environment_capabilities')
    contract = manifest.get('generation_inputs', {}).get('generation_environment_contract')
    if cap and contract != PAGED_CONTRACT:
        raise ValueError('Aligned capability artifacts require the frozen public-observation contract')
    os.environ['VGB_PUBLIC_OBSERVATION_V2'] = '1' if contract == PAGED_CONTRACT else '0'
    sys.path.insert(0, str(ROOT/'pipeline'))
    from generation_provenance import stale_reason
    reason = stale_reason(a.task, manifest)
    if reason:
        raise ValueError(reason)
    from pool_policy import exclusions
    if set(exclusions()) & set(freeze['tasks']):
        raise ValueError('Historical exclusion registry does not match paper222')
    argv = manifest.get('entrypoint', {}).get('argv', [])
    if not argv or Path(argv[0]).name not in ('python', 'python3', 'python3.12'):
        raise ValueError('This portable replay wrapper supports Python verifier entrypoints only')
    report = {'version':freeze['version'], 'task':a.task, 'source_files_verified':len(manifest['files']),
              'view_files_verified':len(bindings['sha256']), 'capability_contract':contract,
              'original_manifest_sha256':sha(bundle/'manifest.json')}
    report['runtime_revision'] = 'integration-alignment-20261021-v4'
    report['runtime_manifest_sha256'] = sha(ROOT/'MANIFEST.json')
    report['runtime_sources_sha256'] = {
        str(p.relative_to(ROOT)): sha(p)
        for p in sorted(ROOT.rglob('*.py')) if '__pycache__' not in p.parts
    }
    if a.check_only:
        print(json.dumps({**report, 'status':'input checks passed; environment execution not tested'}))
        return
    if not a.out or a.out.exists():
        raise ValueError('--out must name a new result file')
    if sys.platform != 'linux' or platform.machine() not in ('x86_64', 'amd64') or sys.version_info[:2] != (3, 12):
        raise ValueError('Historical replay requires Linux x86_64 and Python 3.12')
    if not shutil.which('bwrap'):
        raise ValueError('Install bubblewrap; unsandboxed fallback is disabled')
    a.out = a.out.resolve()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    # Stage sources so runner's client shim injection cannot modify the original artifact.
    with tempfile.TemporaryDirectory(prefix='paper222-artifact-') as td:
        staged = Path(td)/'bundle'
        staged.mkdir()
        for record in manifest['files']:
            dest = staged/record['path']
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bundle/record['path'], dest)
        manifest['entrypoint']['argv'][0] = sys.executable
        (staged/'manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2))
        with a.out.with_suffix(a.out.suffix+'.log').open('x') as log:
            completed = subprocess.run([sys.executable, str(ROOT/'pipeline/runner.py'), str(staged), '--views', str(views),
                                        '--task', a.task, '--workers', '1', '--out', str(a.out)], stdout=log, stderr=subprocess.STDOUT)
        if completed.returncode:
            raise RuntimeError('Runner failed; inspect '+str(a.out)+'.log')
    rows = [json.loads(line) for line in a.out.read_text().splitlines() if line.strip()]
    labels = [json.loads(line) for line in (views/'private/labels.jsonl').read_text().splitlines()]
    wanted = {x['candidate_handle'] for x in labels if x['task_handle'] == a.task}
    if len(rows) != len(wanted) or {x['candidate_handle'] for x in rows} != wanted:
        raise RuntimeError('Incomplete or duplicate candidate judgments')
    for x in rows:
        audit = x['decision_audit']
        audit_root = Path(str(a.out) + '.decisions')
        audit_path = audit_root / audit['file']
        if audit_path.parent != audit_root or audit_path.is_symlink() or sha(audit_path) != audit['sha256']:
            raise RuntimeError('Decision audit path/hash mismatch')
        detail = json.loads(audit_path.read_text())
        if detail['task'] != x['task_handle'] or detail['candidate'] != x['candidate_handle']:
            raise RuntimeError('Decision audit identity mismatch')
        payload = detail['verifier_payload_untrusted']
        payload_hash = 'sha256:' + hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest() if payload else None
        if payload_hash != x['decision_payload_hash'] or detail['execution_status'] != x['execution_status'] or detail['execution_error'] != x['error']:
            raise RuntimeError('Decision audit/result mismatch')
        if x.get('cap_error') or x.get('error_type') in ('infrastructure', 'stale_generation'):
            raise RuntimeError('Unresolved infrastructure/provenance error')
        if x['task_handle'] != a.task:
            raise RuntimeError('Wrong-task verdict')
        rel = f"public/{a.task}/candidates/{x['candidate_handle']}.json"
        if x['candidate_view_sha256'] != 'sha256:'+bindings['sha256'][rel]:
            raise RuntimeError('Candidate judgment hash mismatch')
        if cap and x['runtime_contract'] != contract:
            raise RuntimeError('Judging/generation capability contract mismatch')
    if cap:
        from runtime_contract_check import validate_runtime_rows
        validate_runtime_rows(rows, freeze['tasks'][a.task]['form'], contract)
    report.update(status='completed', candidates=len(rows), output_sha256=sha(a.out))
    a.out.with_suffix(a.out.suffix+'.receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
