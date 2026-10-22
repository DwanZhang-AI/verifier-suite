#!/usr/bin/env python3
"""Build the full-data rubric library tree from the frozen LIBRARY split.

Replaces the retired M2 compressor (upmap/cluster/select/polish, cap 50) per the
2026-09-04 ruling: all library-half criteria go in, the domain/category tree plus
INDEX.tsv is the scale mechanism. Zero LLM, deterministic, rebuildable.

    python -m gavel_harness.rubric.build \\
        --prbench <dir with finance/legal/finance_hard/legal_hard .parquet> \\
        --prbench-splits <prbench_splits_v1.tsv from `rubric.cli split`> \\
        --tau2-domains <tau2-bench checkout>/data/tau2/domains \\
        [--tau2-held-out <id list>]   # default: library_v1_inputs/tau2_held_out_ids.txt
        --out <library root>          # all domains -> <out>/<domain>/, build_audit.json

Every input is public or ships with this package, so library_v1 is rebuilt from
the PRBench parquet files, the split `rubric.cli split` writes from them, and a
tau2-bench checkout at the commit named in NOTICE (docs/rubric_library.md has
the recipe). The default held-out list is the one library_v1 was built with.
Reading the PRBench parquet files needs pandas and pyarrow.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from importlib import resources

from . import ingest, library

PARQUET = {"finance": "finance.parquet", "legal": "legal.parquet",
           "finance_hard": "finance_hard.parquet", "legal_hard": "legal_hard.parquet"}
DOMAINS = sorted(PARQUET) + ["airline_ops", "banking_ops"]
HELD_OUT = resources.files(__package__).joinpath("library_v1_inputs", "tau2_held_out_ids.txt")
"""The tau2 tasks library_v1 holds out: the airline tasks of the evaluation task set."""


@dataclass(frozen=True)
class Inputs:
    """Where the build reads its sources; every path is given by the caller."""

    prbench: str            # directory holding the PARQUET files
    prbench_splits: str     # frozen PRBench split TSV (domain, task_id, split)
    tau2_domains: str       # tau2-bench data/tau2/domains
    tau2_held_out: str      # held-out task list, e.g. HELD_OUT


def _tau2_eval_ids(inputs: Inputs, prefix: str) -> set[str]:
    """task ids of the evaluation task set — NEVER library material.
    rows look like 'airline__11' / 'banking_knowledge__task_015'; '#' starts a comment."""
    out = set()
    with open(inputs.tau2_held_out, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "__" not in line:
                raise ValueError(f"{inputs.tau2_held_out}:{lineno}: expected <domain>__<id>")
            if line.startswith(prefix + "__"):
                out.add(line.split("__", 1)[1])
    return out


def _airline_tasks(inputs: Inputs) -> list[dict]:
    """zero-extraction: airline nl_assertions verbatim (already rule sentences).
    Library-half = tasks OUTSIDE the held-out evaluation set (task-level anti-leak,
    same contract as the PRBench library-half)."""
    evald = _tau2_eval_ids(inputs, "airline")
    ts = json.load(open(os.path.join(inputs.tau2_domains, "airline", "tasks.json")))
    out = []
    for t in ts:
        tid = str(t.get("id"))
        if tid in evald:
            continue
        nl = (t.get("evaluation_criteria") or {}).get("nl_assertions") or []
        if not nl:
            continue
        out.append({"task_id": f"tau2:airline:{tid}", "domain": "airline_ops",
                    "topic": "airline customer service",
                    "criteria": [{"seed_id": f"a{i}", "sentence": str(a).strip(),
                                  "hint": "", "category": "service-assertions",
                                  "severity": "必须"}
                                 for i, a in enumerate(nl)]})
    return out


def _banking_doc_category(fname: str) -> str:
    """deterministic coarse category from the filename: doc_<cat...>_<product>_NNN.
    business_* categories carry three tokens, the rest two."""
    stem = fname[len("doc_"):].rsplit("_", 1)[0]        # drop trailing _NNN
    toks = stem.split("_")
    k = 3 if toks and toks[0] == "business" else 2
    return "_".join(toks[:k]) if len(toks) >= k else stem


def _banking_tasks(inputs: Inputs) -> list[dict]:
    """zero-extraction: the 698 bank procedure documents VERBATIM, one entry per
    document (title = 判据行, full content = 提示). No sentence splitting, no LLM —
    the judge browses INDEX titles and reads the relevant procedure, the same way
    a service agent uses the operations manual. These documents are solver-visible
    task material (closed-book legal); provenance recorded per file."""
    droot = os.path.join(inputs.tau2_domains, "banking_knowledge", "documents")
    out = []
    for f in sorted(os.listdir(droot)):
        if not f.endswith(".json"):
            continue
        d = json.load(open(os.path.join(droot, f)))
        out.append({"task_id": f"tau2doc:{d['id']}", "domain": "banking_ops",
                    "topic": "banking operations manual",
                    "criteria": [{"seed_id": "doc", "sentence": str(d["title"]).strip(),
                                  "hint": str(d["content"]).strip(),
                                  "category": _banking_doc_category(f),
                                  "severity": "建议"}]})
    return out


def library_tasks(domain: str, inputs: Inputs) -> list[dict]:
    if domain == "airline_ops":
        return _airline_tasks(inputs)
    if domain == "banking_ops":
        return _banking_tasks(inputs)
    tasks = ingest.load_prbench(os.path.join(inputs.prbench, PARQUET[domain]), domain)
    if domain in ("finance", "legal"):
        split = ingest.load_split(inputs.prbench_splits)[domain]
        tasks = [t for t in tasks if split.get(t["task_id"]) == "library"]
    # hard variants: not part of ANY eval universe we use -> 100% library, recorded
    for t in tasks:
        t["task_id"] = f"prbench:{t['task_id']}"
    return tasks


def build_domain(domain: str, inputs: Inputs, lib_root: str) -> dict:
    tasks = library_tasks(domain, inputs)
    entries = library.entries_from_tasks(domain, tasks)
    errs = library.write_domain(lib_root, domain, entries, ingest.JUDGE_EVIDENCE)
    assert not errs, errs[:5]
    n_in = sum(len(t["criteria"]) for t in tasks)
    assert n_in == len(entries), (n_in, len(entries))     # totality: nothing dropped
    audit = {"domain": domain, "library_tasks": len(tasks), "entries": len(entries),
             "categories": len({e.category for e in entries}),
             "severity_mix": {s: sum(1 for e in entries if e.severity == s)
                              for s in library.SEVERITIES}}
    print(json.dumps(audit, ensure_ascii=False))
    return audit


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m gavel_harness.rubric.build",
                                 description=__doc__.split("\n\n")[0])
    ap.add_argument("--prbench", required=True,
                    help="directory holding " + ", ".join(sorted(PARQUET.values())))
    ap.add_argument("--prbench-splits", required=True,
                    help="frozen PRBench split TSV written by `rubric.cli split`")
    ap.add_argument("--tau2-domains", required=True,
                    help="tau2-bench data/tau2/domains directory")
    ap.add_argument("--tau2-held-out", default=None,
                    help="tau2 tasks kept out of the library, one <domain>__<id> per line "
                         "(default: the list library_v1 was built with)")
    ap.add_argument("--out", required=True, help="library root; each domain directory is replaced")
    args = ap.parse_args(argv)
    with resources.as_file(HELD_OUT) as default_held_out:
        inputs = Inputs(prbench=args.prbench, prbench_splits=args.prbench_splits,
                        tau2_domains=args.tau2_domains,
                        tau2_held_out=args.tau2_held_out or str(default_held_out))
        audits = [build_domain(d, inputs, args.out) for d in DOMAINS]
    json.dump(audits, open(os.path.join(args.out, "build_audit.json"), "w"),
              indent=1, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
