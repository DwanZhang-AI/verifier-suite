#!/usr/bin/env python3
"""rubric CLI.

    python -m judge.rubric.cli split     # freeze the PRBench splits (path: FROZEN below)
    python -m judge.rubric.cli validate <rubric_root>   # validate all domain trees
"""
from __future__ import annotations

import argparse
import json
import os
import sys

DATA = "/opt/gavel/runtime/rubric_data/prbench"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FROZEN = os.path.join(REPO, "closed_results", "rubric_bench")


def main(argv=None) -> int:
    try:
        from . import ingest, library
    except ImportError:
        import ingest
        import library
    ap = argparse.ArgumentParser(prog="rubric")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("split")
    v = sub.add_parser("validate")
    v.add_argument("rubric_root")
    args = ap.parse_args(argv)

    if args.cmd == "split":
        os.makedirs(FROZEN, exist_ok=True)
        assignments = {}
        for domain, fname in (("finance", "finance.parquet"), ("legal", "legal.parquet")):
            tasks = ingest.load_prbench(os.path.join(DATA, fname), domain)
            assignments[domain] = ingest.split_tasks([t["task_id"] for t in tasks])
        tsv = os.path.join(FROZEN, "prbench_splits_v1.tsv")
        aj = os.path.join(FROZEN, "prbench_splits_v1_audit.json")
        if os.path.exists(tsv):
            print(f"REFUSING to overwrite frozen split: {tsv}", file=sys.stderr)
            return 2
        audit = ingest.write_split_manifest(assignments, tsv, aj)
        print(json.dumps(audit, ensure_ascii=False, indent=1))
        return 0 if audit["disjoint"] else 1

    errs = []
    for domain in sorted(os.listdir(args.rubric_root)):
        if not os.path.isdir(os.path.join(args.rubric_root, domain)):
            continue
        try:
            for e in library.load_domain(args.rubric_root, domain):
                errs += e.validate()
        except (OSError, ValueError) as exc:
            errs.append(f"{domain}: {exc}")
    print(json.dumps({"errors": errs[:20], "n_errors": len(errs)}, ensure_ascii=False))
    return 0 if not errs else 1


if __name__ == "__main__":
    sys.exit(main())
