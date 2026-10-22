#!/usr/bin/env python3
"""Build the full-data rubric library tree from the frozen LIBRARY split.

All library-half criteria go in (no compression or selection); the domain/category
tree plus INDEX.tsv is the scale mechanism. Zero LLM, deterministic, rebuildable.

    python -m judge.rubric.build            # both domains -> judge/rubric/library_v1/
"""
from __future__ import annotations

import json
import os

try:
    from . import ingest, library
except ImportError:
    import ingest
    import library

DATA = "/opt/gavel/runtime/rubric_data/prbench"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FROZEN_TSV = os.path.join(REPO, "closed_results", "rubric_bench", "prbench_splits_v1.tsv")
P1_FREEZE = os.path.join(REPO, "closed_results", "p1_freeze")
TAU2_DOMAINS = ("/opt/gavel/harbor/.cache/tau2-bench"
                "/data/tau2/domains")
LIB_ROOT = os.path.join(HERE, "library_v1")
PARQUET = {"finance": "finance.parquet", "legal": "legal.parquet",
           "finance_hard": "finance_hard.parquet", "legal_hard": "legal_hard.parquet"}
DOMAINS = sorted(PARQUET) + ["airline_ops", "banking_ops"]


def _tau2_eval_ids(prefix: str) -> set[str]:
    """task ids inside the frozen fit/valid/test universe — NEVER library material.
    tsv rows look like 'airline__11' / 'banking_knowledge__task_015'."""
    out = set()
    for sp in ("fit", "valid", "test"):
        for line in open(os.path.join(P1_FREEZE, f"tau2_{sp}_v5.tsv")):
            line = line.strip()
            if line.startswith(prefix + "__"):
                out.add(line.split("__", 1)[1])
    return out


def _airline_tasks() -> list[dict]:
    """zero-extraction: airline nl_assertions verbatim (already rule sentences).
    Library-half = tasks OUTSIDE the frozen v5 universe (task-level anti-leak,
    same contract as the PRBench library-half)."""
    evald = _tau2_eval_ids("airline")
    ts = json.load(open(os.path.join(TAU2_DOMAINS, "airline", "tasks.json")))
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


def _banking_tasks() -> list[dict]:
    """zero-extraction: the 698 bank procedure documents VERBATIM, one entry per
    document (title = 判据行, full content = 提示). No sentence splitting, no LLM —
    the judge browses INDEX titles and reads the relevant procedure, the same way
    a service agent uses the operations manual. These documents are solver-visible
    task material (closed-book legal); provenance recorded per file."""
    droot = os.path.join(TAU2_DOMAINS, "banking_knowledge", "documents")
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


def library_tasks(domain: str) -> list[dict]:
    if domain == "airline_ops":
        return _airline_tasks()
    if domain == "banking_ops":
        return _banking_tasks()
    tasks = ingest.load_prbench(os.path.join(DATA, PARQUET[domain]), domain)
    if domain in ("finance", "legal"):
        split = ingest.load_split(FROZEN_TSV)[domain]
        tasks = [t for t in tasks if split.get(t["task_id"]) == "library"]
    # hard variants: not part of ANY eval universe we use -> 100% library, recorded
    for t in tasks:
        t["task_id"] = f"prbench:{t['task_id']}"
    return tasks


def build_domain(domain: str) -> dict:
    tasks = library_tasks(domain)
    entries = library.entries_from_tasks(domain, tasks)
    errs = library.write_domain(LIB_ROOT, domain, entries, ingest.JUDGE_EVIDENCE)
    assert not errs, errs[:5]
    n_in = sum(len(t["criteria"]) for t in tasks)
    assert n_in == len(entries), (n_in, len(entries))     # totality: nothing dropped
    audit = {"domain": domain, "library_tasks": len(tasks), "entries": len(entries),
             "categories": len({e.category for e in entries}),
             "severity_mix": {s: sum(1 for e in entries if e.severity == s)
                              for s in library.SEVERITIES}}
    print(json.dumps(audit, ensure_ascii=False))
    return audit


if __name__ == "__main__":
    audits = [build_domain(d) for d in DOMAINS]
    json.dump(audits, open(os.path.join(LIB_ROOT, "build_audit.json"), "w"),
              indent=1, ensure_ascii=False)
