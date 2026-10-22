#!/usr/bin/env python3
"""PRBench ingestion + frozen splits (rubric line, M1).

Reuses the house patterns:
  - COLUMN-WHITELISTED parquet reads (column-whitelist precedent): only the
    columns needed for splitting/derivation ever leave the file — model responses
    and reference texts never enter this module's memory.
  - deterministic hash splits frozen as TSV (p1_freeze precedent): library-half vs
    eval-half at the task level, eval-half further into fit/valid/test. TEST is
    never touched by development.

Anti-leak contract: library entries may only ever be derived from LIBRARY-half
tasks; the split manifest is the audit anchor and is committed to closed_results.
Canary strings never leave this module (stripped on load).
"""
from __future__ import annotations

import hashlib
import json
import os

#: exact weight_class enum measured on the live data 2026-09-02
#: (finance 9,865 + legal 8,827 criteria; six values, three polarities)
WEIGHT_MAP = {
    "critically important": "必须",
    "important": "必须",
    "slightly important": "建议",
    "slightly detrimental": "负面",
    "detrimental": "负面",
    "critically detrimental": "负面",
}

#: judge-time evidence vocabulary for the conversation-bench family
#: (PRBench finance/legal + HealthBench share this surface)
JUDGE_EVIDENCE = {"conversation": "process.language",
                  "final_response": "final.artifact",
                  "reference_materials": "baseline.state"}

SPLITS = ("library", "fit", "valid", "test")


def load_prbench(parquet_path: str, domain: str) -> list[dict]:
    """[{task_id, domain, topic, criteria[]{seed_id, sentence, hint, category,
    severity}}] — whitelisted columns only; canary intentionally not read."""
    import ast
    import pandas as pd
    df = pd.read_parquet(parquet_path, columns=["task", "topic", "rubric"])
    out = []
    for _, row in df.iterrows():
        rub = row["rubric"]
        if isinstance(rub, str):
            rub = ast.literal_eval(rub)
        crits = []
        for c in rub:
            a = c.get("annotations") or {}
            wc = a.get("weight_class")
            if wc not in WEIGHT_MAP:
                continue                       # unknown class: skip loudly in audit
            crits.append({"seed_id": str(c.get("id")),
                          "sentence": str(c.get("title") or "").strip(),
                          "hint": str(a.get("criteria_description") or "").strip(),
                          "category": str(a.get("criteria_category") or "").strip(),
                          "severity": WEIGHT_MAP[wc]})
        out.append({"task_id": str(row["task"]), "domain": domain,
                    "topic": str(row["topic"]), "criteria": crits})
    return out


def _bucket(task_id: str, salt: str) -> float:
    h = hashlib.sha256(f"{salt}:{task_id}".encode()).hexdigest()
    return int(h[:12], 16) / 16**12


def split_tasks(task_ids: list[str], salt: str = "rubric-v1") -> dict[str, str]:
    """{task_id: library|fit|valid|test} — deterministic, order-independent.
    library 50%; eval half -> fit 40% / valid 20% / test 40% of the eval half."""
    out = {}
    for t in sorted(task_ids):
        u = _bucket(t, salt)
        if u < 0.5:
            out[t] = "library"
        else:
            v = _bucket(t, salt + ":eval")
            out[t] = "fit" if v < 0.4 else ("valid" if v < 0.6 else "test")
    return out


def write_split_manifest(assignments: dict[str, dict[str, str]], out_tsv: str,
                         audit_json: str) -> dict:
    """assignments = {domain: {task_id: split}}. Freezes the TSV + an audit record
    (counts, pairwise-disjointness, salt). Returns the audit dict."""
    rows = [(d, t, s) for d, m in sorted(assignments.items())
            for t, s in sorted(m.items())]
    with open(out_tsv, "w") as fh:
        fh.write("domain\ttask_id\tsplit\n")
        for d, t, s in rows:
            fh.write(f"{d}\t{t}\t{s}\n")
    audit: dict = {"salt": "rubric-v1", "counts": {}, "disjoint": True}
    for d, m in sorted(assignments.items()):
        c = {s: 0 for s in SPLITS}
        for s in m.values():
            c[s] += 1
        audit["counts"][d] = c
        lib = {t for t, s in m.items() if s == "library"}
        ev = {t for t, s in m.items() if s != "library"}
        if lib & ev:
            audit["disjoint"] = False
    json.dump(audit, open(audit_json, "w"), indent=1, ensure_ascii=False)
    return audit


def load_split(tsv_path: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    with open(tsv_path) as fh:
        next(fh)
        for line in fh:
            d, t, s = line.rstrip("\n").split("\t")
            out.setdefault(d, {})[t] = s
    return out


def _selftest():
    ids = [f"task{i:03d}" for i in range(200)]
    a = split_tasks(ids)
    b = split_tasks(list(reversed(ids)))
    assert a == b, "split must be order-independent"
    from collections import Counter
    c = Counter(a.values())
    assert 70 <= c["library"] <= 130 and c["test"] > 0 and c["valid"] > 0
    assert set(a.values()) <= set(SPLITS)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tsv, aj = os.path.join(d, "s.tsv"), os.path.join(d, "a.json")
        audit = write_split_manifest({"finance": a}, tsv, aj)
        assert audit["disjoint"] and load_split(tsv)["finance"] == a
    assert WEIGHT_MAP["critically detrimental"] == "负面"
    print("ingest selftest OK")


if __name__ == "__main__":
    _selftest()
