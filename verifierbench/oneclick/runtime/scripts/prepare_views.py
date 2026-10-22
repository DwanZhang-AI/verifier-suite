#!/usr/bin/env python3
"""Build evaluator-only paper222 views from the bundled public dataset."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'dataset/scripts'))


def prepare(output, appworld_root):
    import materialize as M
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Keep reconstructed AppWorld plaintext outside this package.')
    if output.exists():
        raise ValueError('Choose an output directory that does not exist.')
    freeze = json.loads((ROOT/'paper/freeze.json').read_text())
    tasks, candidates = M.rows('paper', 'tasks'), M.rows('paper', 'evaluation')
    if {r['task_id'] for r in tasks} != set(freeze['tasks']) or len(candidates) != 4993:
        raise ValueError('Dataset does not match the paper222 freeze')
    aw = {r['task_id']:r for r in json.loads((ROOT/'dataset/metadata/appworld_reconstruction.json').read_text())}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='paper222-views-', dir=output.parent) as td:
        stage = Path(td)/'views'
        (stage/'private').mkdir(parents=True)
        ids, labels, bindings = {}, [], {}
        for r in tasks:
            # Preserve original source bytes. Runner backfills AppWorld at execution time.
            raw = (r['task_spec_json'] if r['task_spec_json'] is not None else aw[r['task_id']]['template_json']).encode()
            if M.sha(raw) != r['task_spec_sha256']:
                raise ValueError('Task hash mismatch: '+r['task_id'])
            if r['task_spec_json'] is None:
                M.reconstruct_task(r, aw, appworld_root)
            elif M.sha(M.canonical(json.loads(raw))) != r['effective_spec_sha256']:
                raise ValueError('Effective task hash mismatch')
            rel = Path('public')/r['task_id']/'task_spec.public.json'
            dest = stage/rel
            dest.parent.mkdir(parents=True)
            dest.write_bytes(raw)
            bindings[str(rel)] = M.sha(raw)
            ids[r['task_id']] = {'task_id':r['source_task_id'], 'benchmark':r['benchmark'], 'form':freeze['tasks'][r['task_id']]['form']}
        cache = {}
        seen = set()
        for r in candidates:
            cid, task = r['candidate_id'], r['task_id']
            if cid in seen or task not in ids or r['label'] not in ('PASS', 'FAIL'):
                raise ValueError('Duplicate candidate or invalid task/label')
            seen.add(cid)
            raw = r['candidate_view_json'].encode() if r['candidate_view_json'] is not None else M.reconstruct_candidate(r, appworld_root, cache)
            if M.sha(raw) != r['candidate_view_sha256']:
                raise ValueError('Candidate hash mismatch: '+cid)
            rel = Path('public')/task/'candidates'/(cid+'.json')
            dest = stage/rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
            bindings[str(rel)] = M.sha(raw)
            labels.append({'task_handle':task, 'candidate_handle':cid, 'truth':r['label'], 'klass':r['candidate_class'],
                           'benchmark':r['benchmark'], 'form':ids[task]['form'], 'split':'full'})
        (stage/'private/id_map.json').write_text(json.dumps(ids, ensure_ascii=False, indent=2))
        (stage/'private/labels.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in labels))
        for rel in ('private/id_map.json', 'private/labels.jsonl'):
            bindings[rel] = hashlib.sha256((stage/rel).read_bytes()).hexdigest()
        (stage/'paper222_bindings.json').write_text(json.dumps({'version':freeze['version'], 'tasks':222, 'candidates':4993, 'sha256':bindings}, indent=2))
        shutil.move(str(stage), str(output))
    return {'tasks':222, 'candidates':4993, 'output':str(output), 'purpose':'evaluation only; do not expose to verifier generation'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--appworld-root', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(prepare(a.output, a.appworld_root)))


if __name__ == '__main__':
    main()
