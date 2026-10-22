#!/usr/bin/env python3
"""evidence CLI.

    python -m judge.evidence.cli collect  <trial_dir> [...]     # write evidence_map.json per trial
    python -m judge.evidence.cli coverage <trial_dir> [...]     # aggregate coverage table
    python -m judge.evidence.cli certify  --vocab '{"ref":"etype"}' <trial_dir> [...]

Exit 0 on success; per-trial failures are reported and counted, not fatal.
"""
from __future__ import annotations

import argparse
import json
import sys


def main(argv=None) -> int:
    try:
        from .collectors import collect
        from .model import coverage, load_map, ETYPES
    except ImportError:
        from collectors import collect
        from model import coverage, load_map, ETYPES
    ap = argparse.ArgumentParser(prog="evidence")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("collect", "coverage", "certify"):
        s = sub.add_parser(c)
        s.add_argument("trial_dirs", nargs="+")
        if c == "certify":
            s.add_argument("--vocab", required=True,
                           help="JSON dict: judge-time evidence name -> etype")
    args = ap.parse_args(argv)

    if args.cmd == "certify":
        try:
            from .certificate import build_certificate
        except ImportError:
            from certificate import build_certificate
        vocab = json.loads(args.vocab)
        n_ok = n_err = 0
        for d in args.trial_dirs:
            try:
                print(build_certificate(d, vocab))
                n_ok += 1
            except Exception as e:
                n_err += 1
                print(f"error: {d}: {type(e).__name__}: {e}", file=sys.stderr)
        print(f"certified {n_ok} trials, {n_err} errors")
        return 0 if n_err == 0 else 1

    if args.cmd == "collect":
        n_ok = n_err = 0
        for d in args.trial_dirs:
            try:
                collect(d)
                n_ok += 1
            except Exception as e:
                n_err += 1
                print(f"error: {d}: {type(e).__name__}: {e}", file=sys.stderr)
        print(f"collected {n_ok} trials, {n_err} errors")
        return 0 if n_err == 0 else 1

    maps = []
    for d in args.trial_dirs:
        try:
            maps.append(load_map(d))
        except Exception as e:
            print(f"error: {d}: {type(e).__name__}: {e}", file=sys.stderr)
    tab = coverage(maps)
    print(f"{'etype':<24} {'present':>8} {'missing':>8} {'generated':>10}   (n={len(maps)})")
    for t in ETYPES:
        r = tab[t]
        print(f"{t:<24} {r['present']:>8} {r['missing']:>8} {r['generated']:>10}")
    print(json.dumps({"n": len(maps), "coverage": tab}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
