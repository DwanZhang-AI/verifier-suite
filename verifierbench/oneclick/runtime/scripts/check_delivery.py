"""Non-executing delivery warnings; never rewrites a verifier or its verdicts."""
import argparse
import ast
import json
from pathlib import Path


def warnings(source):
    tree = ast.parse(source)
    findings = []
    pass_return = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and node.value is not None:
            # Conservative lint, not reachability proof: a PASS literal in any
            # returned expression counts as a possible path. Dynamic dispatch
            # may require manual review; never block or rewrite based on this.
            pass_return |= any(isinstance(x, ast.Constant) and x.value == 'PASS'
                               for x in ast.walk(node.value))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'run_public':
            for arg in node.args:
                if isinstance(arg, ast.Dict):
                    for key, value in zip(arg.keys, arg.values):
                        if (isinstance(key, ast.Constant) and key.value == 'code'
                            and isinstance(value, ast.Subscript) and isinstance(value.slice, ast.Constant)
                            and value.slice.value == 'solution'):
                            findings.append({'line': node.lineno, 'warning': 'solution_source_sent_as_probe_code'})
    if not pass_return:
        findings.append({'warning': 'no_literal_PASS_in_return_expressions',
                         'meaning': 'Review only; static heuristic cannot prove dynamic reachability.'})
    return findings


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checker', type=Path)
    args = parser.parse_args()
    print(json.dumps({'warnings': warnings(args.checker.read_text()), 'source_modified': False}))
