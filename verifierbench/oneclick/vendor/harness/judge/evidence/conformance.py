#!/usr/bin/env python3
"""T5 declaration-vs-behavior conformance audit — record-only, offline, gold-free.

The declaration says which judge-time evidence each check reads; this audit asks
the cheapest honest question: does the shipped verifier source actually REFERENCE
those evidence names? Static word-boundary text match over the verifier package
(the evidence/ subtree itself excluded). 'referenced' means the name occurs in
verifier code — it cannot prove the read is causal, and a verifier may read
evidence through an alias the match misses; both limitations are recorded in
every report. No gating, no retry, no runtime component."""
from __future__ import annotations

import argparse
import json
import os
import re
import fnmatch

try:
    from .trial import TrialView
    from .certificate import validate_structure
except ImportError:
    from trial import TrialView
    from certificate import validate_structure

MAX_FILE_BYTES = 512 * 1024          # verifier sources are small; skip blobs

# Verifier families (from an audit of generated verifiers): interpreter-style verifiers
# (tau2/mcp checkers) READ named artifacts, so a declared name must appear in source
# — measured 100% on both. Exec-style verifiers (swe/ds test files) are RUN inside
# the environment; the declared evidence (test_output/testbed) is materialized by
# the runner, never named in test source — name-matching is structurally
# inapplicable there and must not be scored as inconsistency.
EXEC_STYLE = ("swe_verified",)


def _verifier_texts(trial_dir: str) -> list[tuple[str, str]]:
    trial = TrialView(trial_dir)
    out = []
    for relative in trial.deliverable_files():
        filename = os.path.basename(relative)
        is_entry = any(fnmatch.fnmatch(filename, pattern) for pattern in
                       ("checker.py", "verifier.py", "judge_prompt.txt", "test_*.py"))
        is_check_source = "/checks/" in relative and relative.endswith((".py", ".sh", ".js", ".ts"))
        if not (is_entry or is_check_source):
            continue
        p = trial.rel(relative)
        try:
            if os.path.getsize(p) > MAX_FILE_BYTES:
                continue
            with open(p, "rb") as fh:
                blob = fh.read()
            if b"\x00" in blob[:4096]:
                continue
            out.append((relative, blob.decode("utf-8", errors="replace")))
        except OSError:
            continue
    return out


def audit_trial(trial_dir: str, exec_style: bool = False) -> dict | None:
    """-> conformance record for one trial, or None when no declaration exists."""
    dp = os.path.join(trial_dir, "verifier", "evidence", "gen_declaration.json")
    if not (os.path.exists(dp) and os.path.getsize(dp)):
        return None
    try:
        with open(dp, encoding="utf-8") as fh:
            decl = json.load(fh)
        validate_structure(decl)
    except (ValueError, OSError) as e:
        return {"trial": os.path.basename(trial_dir.rstrip("/")),
                "declared": True, "parse_error": f"{type(e).__name__}", "checks": []}
    texts = _verifier_texts(trial_dir)
    joined = "\n".join(txt for _p, txt in texts)
    checks = []
    for c in decl.get("checks", []):
        ev = {}
        for name in (c.get("evidence") or []):
            if exec_style:
                ev[str(name)] = "consumed_by_runner"
            else:
                hit = re.search(
                    r"(?<![A-Za-z0-9_])" + re.escape(str(name)) + r"(?![A-Za-z0-9_])",
                    joined) is not None
                ev[str(name)] = "referenced" if hit else "not_referenced"
        checks.append({"check_id": c.get("check_id"), "evidence": ev})
    names = [(n, v) for c in checks for n, v in c["evidence"].items()]
    applicable = [(n, v) for n, v in names if v != "consumed_by_runner"]
    return {"trial": os.path.basename(trial_dir.rstrip("/")),
            "declared": True,
            "exec_style": exec_style,
            "n_verifier_files": len(texts),
            "verifier_files": [path for path, _text in texts],
            "checks": checks,
            "n_names": len(names),
            "n_applicable": len(applicable),
            "n_referenced": sum(1 for _n, v in applicable if v == "referenced"),
            "method": "static word-boundary match; not causal proof; aliases unseen"}


def _is_exec_style(jobs_dir: str) -> bool:
    base = os.path.basename(jobs_dir.rstrip("/"))
    return any(f"-{b}-" in base or base.startswith(f"roll-{b}") for b in EXEC_STYLE)


def audit_roll(jobs_dir: str, exec_style: bool | None = None) -> dict:
    """aggregate over every trial dir in one batch's jobs dir. exec_style=None
    autodetects from the job dir name (roll-<bench>-...)."""
    if exec_style is None:
        exec_style = _is_exec_style(jobs_dir)
    rows = []
    n_trials = 0
    for d in sorted(os.listdir(jobs_dir)):
        td = os.path.join(jobs_dir, d)
        if not os.path.isdir(td):
            continue
        n_trials += 1
        r = audit_trial(td, exec_style)
        if r is not None:
            rows.append(r)
    applicable = sum(r.get("n_applicable", 0) for r in rows)
    refd = sum(r.get("n_referenced", 0) for r in rows)
    full = sum(1 for r in rows
               if r.get("n_applicable") and r["n_referenced"] == r["n_applicable"])
    return {"jobs_dir": jobs_dir, "n_trials": n_trials, "n_declared": len(rows),
            "exec_style": exec_style,
            "n_names_declared": sum(r.get("n_names", 0) for r in rows),
            "n_names_applicable": applicable,
            "n_names_referenced": refd,
            "name_reference_rate": round(refd / applicable, 3) if applicable else None,
            "trials_fully_consistent": full,
            "per_trial": rows,
            "method": "static word-boundary match; not causal proof; aliases unseen; "
                      "exec-style verifiers consume evidence via the runner "
                      "(name audit inapplicable, recorded as consumed_by_runner)"}


def _selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        t = os.path.join(d, "trial_x")
        os.makedirs(os.path.join(t, "verifier", "evidence"))
        open(os.path.join(t, "verifier", "checker.py"), "w").write(
            "load('db_before')\ncompare(db_after_x, x)\n")   # db_after only as prefix
        json.dump({"checks": [
            {"check_id": "C1", "evidence": ["db_before", "db_after"]}]},
            open(os.path.join(t, "verifier", "evidence", "gen_declaration.json"), "w"))
        r = audit_trial(t)
        assert r["checks"][0]["evidence"] == {"db_before": "referenced",
                                              "db_after": "not_referenced"}, r
        assert r["n_referenced"] == 1 and r["n_names"] == 2
        # declaration must never match itself: name present ONLY in declaration
        t2 = os.path.join(d, "trial_y")
        os.makedirs(os.path.join(t2, "verifier", "evidence"))
        open(os.path.join(t2, "verifier", "run.sh"), "w").write("echo hi\n")
        json.dump({"checks": [{"check_id": "C1", "evidence": ["messages"]}]},
                  open(os.path.join(t2, "verifier", "evidence",
                                    "gen_declaration.json"), "w"))
        assert audit_trial(t2)["n_referenced"] == 0
        # no declaration -> None; batch aggregate counts both kinds
        t3 = os.path.join(d, "trial_z")
        os.makedirs(os.path.join(t3, "verifier"))
        assert audit_trial(t3) is None
        agg = audit_roll(d)
        assert agg["n_trials"] == 3 and agg["n_declared"] == 2
        assert agg["n_names_declared"] == 3 and agg["n_names_referenced"] == 1
        # exec-style: same trials, every name recorded consumed_by_runner, rate None
        agg2 = audit_roll(d, exec_style=True)
        assert agg2["n_names_applicable"] == 0 and agg2["name_reference_rate"] is None
        r2 = audit_trial(t, exec_style=True)
        assert set(r2["checks"][0]["evidence"].values()) == {"consumed_by_runner"}
        assert _is_exec_style("/x/roll-swe_verified-r31cand-a")
        assert not _is_exec_style("/x/roll-tau2-r31cand-a")
    print("conformance selftest OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs_dir", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest or not a.jobs_dir:
        _selftest()
    else:
        agg = audit_roll(a.jobs_dir)
        agg.pop("per_trial")
        print(json.dumps(agg, ensure_ascii=False, indent=1))
