#!/usr/bin/env python3
"""Recompute the frozen paper222 main/effort tables from task-round records."""
import argparse
import csv
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
METRICS = ('ba', 'tpr', 'tnr', 'fprh')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def aggregate(rows, freeze, kind):
    tasks = freeze['tasks']
    expected = (set(freeze['models']) if kind == 'main' else set(freeze['expected_effort']))
    groups = {}
    for x in rows:
        key = x['model'] if kind == 'main' else '__'.join((x['model'], x['arm'], x['condition']))
        require(key in expected, 'Unexpected model/condition: ' + key)
        require(x['arm'] == 'S1' if kind == 'main' else x['condition'] in ('low', 'high'), 'Wrong arm/condition')
        require(type(x['round']) is int and x['round'] in (1, 2, 3), 'Invalid round')
        require(x['task'] in tasks, 'Task outside paper222')
        require(type(x.get('delivered')) is bool, 'Explicit delivery metadata required')
        for k in METRICS:
            require(type(x.get(k)) in (int, float) and math.isfinite(x[k]) and 0 <= x[k] <= 1, 'Invalid rate: ' + k)
        require(abs(x['ba'] - (x['tpr'] + x['tnr']) / 2) < 1e-10, 'Inconsistent BA')
        require(x['delivered'] or all(x[k] == 0 for k in METRICS), 'Nondelivery must contribute zero')
        group = groups.setdefault(key, {})
        cell = x['task'], x['round']
        require(cell not in group, 'Duplicate task/round: ' + str(cell))
        group[cell] = x
    require(set(groups) == expected, 'Missing model/condition groups')
    result = {}
    for key, cells in groups.items():
        required = {(t, r) for t in tasks for r in (1, 2, 3)}
        require(set(cells) == required, 'Incomplete task/round grid: ' + key)
        for t, task in tasks.items():
            if task['form'] == 'ast':
                require(len({tuple(cells[t, r][k] for k in (*METRICS, 'delivered')) for r in (1, 2, 3)}) == 1,
                        'AST r1 was not replicated: ' + t)
        rounds = []
        for r in (1, 2, 3):
            xs = [cells[t, r] for t in tasks]
            q = {k: 100 * statistics.mean(x[k] for x in xs) for k in METRICS}
            q.update(ba_norm=2*q['ba']-100, delivered=sum(x['delivered'] for x in xs), denominator=len(tasks), round=r)
            rounds.append(q)
        result[key] = {'rounds': rounds, 'selected': sorted(rounds, key=lambda x: x['ba'])[1]}
    return result


def check_expected(result, freeze, kind):
    expected = freeze['expected_main' if kind == 'main' else 'expected_effort']
    for key, rows in result.items():
        q = rows['selected']
        for metric in (*METRICS, 'ba_norm', 'delivered', 'denominator', 'round'):
            require(abs(q[metric]-expected[key][metric]) < 1e-9, 'Frozen result differs: ' + key + '/' + metric)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--table', choices=('main', 'effort', 'all'), default='all')
    p.add_argument('--records', type=Path, help='Alternative records; requires --table main or effort')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(argv)
    require(not a.records or a.table != 'all', '--records requires one table')
    freeze = json.loads((ROOT/'paper/freeze.json').read_text())
    require(len(freeze['tasks']) == freeze['task_count'] == 222 and len(freeze['models']) == 19, 'Wrong frozen scope')
    result = {}
    for kind in (('main', 'effort') if a.table == 'all' else (a.table,)):
        path = a.records or ROOT/'paper'/f'{kind}_task_rounds.json'
        result[kind] = aggregate(json.loads(path.read_text()), freeze, kind)
        if not a.records:
            check_expected(result[kind], freeze, kind)
    a.output.mkdir(parents=True, exist_ok=True)
    fields = ['model', 'ba_norm', *METRICS, 'delivered', 'denominator', 'round']
    for kind, values in result.items():
        with (a.output/(kind+'.csv')).open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for key in sorted(values, key=lambda k: -values[k]['selected']['ba']):
                writer.writerow({'model': key, **values[key]['selected']})
    (a.output/'metrics.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'version':freeze['version'], 'tasks':222, 'groups':{k:len(v) for k,v in result.items()},
                      'matches_frozen_tables':not bool(a.records), 'output':str(a.output)}))


if __name__ == '__main__':
    main()
