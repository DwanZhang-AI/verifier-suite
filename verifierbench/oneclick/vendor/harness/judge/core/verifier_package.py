#!/usr/bin/env python3
"""VerifierPackage: the judge harness's structured output format.

A verifier is not a bare file: it is a versioned, self-describing package

    <task_id>-verifier/
    ├── package.json             index: schema_version, dataset, task_id, parts present
    ├── contract.json            acceptance criteria           (staged pipeline D1)
    ├── env_map.json             observables + capabilities    (staged pipeline D2)
    ├── evidence_manifest.json   criterion -> evidence binding (staged pipeline D3)
    ├── checks/                  executable artifacts (checker.py / verifier.py / ...)
    ├── rubric.json              optional structured rubric (MCP-style judges)
    ├── aggregation.json         verdict rule (default all_checks_pass)
    └── provenance.json          generator model/params, probe outcome, source trial

Honesty rule: parts the generation mode did not produce are ABSENT and listed as such
in package.json — a monolithic (pre-stage-split) generation ships checks/ + provenance
only; it never fabricates a post-hoc contract. The staged pipeline fills the rest.

Schema files: harness/judge/schemas/*.schema.json (informal draft-07). Validation here
is stdlib-only (required keys + referential integrity), not full JSON Schema.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone

SCHEMA_VERSION = "0.1"
OPTIONAL_PARTS = ("contract", "env_map", "evidence_manifest", "rubric", "aggregation")

_CONTRACT_KINDS = {"outcome", "constraint", "invariant", "forbidden_side_effect", "quality"}
_BINDING_STATUS = {"bound", "unsupported"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10,
                              cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip()
    except Exception:
        return "unknown"


def _write_json(path: str, value: dict) -> None:
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=1, ensure_ascii=False)


def build_package(out_dir: str, dataset: str, task_id: str, checks: dict,
                  provenance: dict, contract: dict | None = None,
                  env_map: dict | None = None, evidence_manifest: dict | None = None,
                  rubric: dict | None = None, aggregation: dict | None = None) -> str:
    """Assemble a VerifierPackage. checks = {filename: source_path} (copied in).
    Returns the package dir. Absent optional parts are recorded, never faked."""
    assert checks, "a package with no checks is not a verifier"
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(os.path.join(out_dir, "checks"))
    for name, src in checks.items():
        shutil.copy2(src, os.path.join(out_dir, "checks", name))

    prov = dict(provenance)
    prov.setdefault("created_utc", _now())
    prov.setdefault("generator", {})
    prov["generator"].setdefault("harness", "judge-v2")
    prov["generator"].setdefault("harness_version", _git_sha())
    prov.setdefault("source", {})
    prov["source"].setdefault("dataset", dataset)
    prov["source"].setdefault("task_id", task_id)
    _write_json(os.path.join(out_dir, "provenance.json"), prov)

    if aggregation is None:
        aggregation = {"rule": "all_checks_pass"}
    parts = {"checks": sorted(checks), "provenance": True, "aggregation": True}
    _write_json(os.path.join(out_dir, "aggregation.json"), aggregation)
    for part, obj in (("contract", contract), ("env_map", env_map),
                      ("evidence_manifest", evidence_manifest), ("rubric", rubric)):
        if obj is not None:
            _write_json(os.path.join(out_dir, part + ".json"), obj)
        parts[part] = obj is not None

    _write_json(os.path.join(out_dir, "package.json"),
                {"schema_version": SCHEMA_VERSION, "dataset": dataset,
               "task_id": task_id, "parts": parts},
                )
    return out_dir


def from_trial(out_root: str, dataset: str, task_id: str, artifact_path: str,
               probe: dict, model: str, roll_tag: str | None = None,
               trial_dir: str | None = None, mode: str = "monolithic",
               extra_provenance: dict | None = None, **parts) -> str:
    """Package one generated verifier from batch/trial data."""
    import re
    safe = re.sub(r"[^A-Za-z0-9_.-]", "-", task_id)
    prov = {"generator": {"model": model},
            "pipeline": {"mode": mode},
            "probe": probe,
            "source": {"dataset": dataset, "task_id": task_id,
                       "roll_tag": roll_tag, "trial_dir": trial_dir}}
    if extra_provenance:
        prov.update(extra_provenance)
    return build_package(os.path.join(out_root, f"{safe}-verifier"), dataset, task_id,
                         checks={os.path.basename(artifact_path): artifact_path},
                         provenance=prov, **parts)


def validate_package(pkg_dir: str) -> list[str]:
    """Referential-integrity validation. Returns [] when the package is well-formed."""
    errs: list[str] = []

    def load(name, required):
        p = os.path.join(pkg_dir, name)
        if not os.path.exists(p):
            if required:
                errs.append(f"missing {name}")
            return None
        try:
            with open(p, encoding="utf-8") as stream:
                value = json.load(stream)
            if not isinstance(value, dict):
                errs.append(f"{name} must be a JSON object")
                return None
            return value
        except Exception as e:
            errs.append(f"unparseable {name}: {e}")
            return None

    idx = load("package.json", True)
    if idx is None:
        return errs
    for k in ("schema_version", "dataset", "task_id", "parts"):
        if k not in idx:
            errs.append(f"package.json missing key {k}")
    cdir = os.path.join(pkg_dir, "checks")
    parts = idx.get("parts", {})
    if not isinstance(parts, dict):
        errs.append("package.json parts must be an object")
        parts = {}
    checks = parts.get("checks", [])
    if not isinstance(checks, list) or any(not isinstance(x, str) for x in checks):
        errs.append("package.json checks must be a list of filenames")
        checks = []
    listed = set(checks)
    actual = set(os.listdir(cdir)) if os.path.isdir(cdir) else set()
    if not actual:
        errs.append("checks/ empty or missing")
    if listed != actual:
        errs.append(f"package.json checks index != checks/ contents ({sorted(listed ^ actual)})")

    prov = load("provenance.json", True)
    if prov is not None:
        for k in ("generator", "probe", "source", "created_utc"):
            if k not in prov:
                errs.append(f"provenance.json missing key {k}")

    load("aggregation.json", True)

    def objects(value, key, label):
        rows = value.get(key) if value is not None else None
        if not isinstance(rows, list):
            errs.append(f"{label}.{key} must be a list")
            return []
        if any(not isinstance(row, dict) for row in rows):
            errs.append(f"{label}.{key} entries must be objects")
        return [row for row in rows if isinstance(row, dict)]

    contract = load("contract.json", parts.get("contract", False))
    crit_ids = set()
    if contract is not None:
        for c in objects(contract, "criteria", "contract"):
            cid = c.get("id")
            if not isinstance(cid, str) or not cid or cid in crit_ids:
                errs.append(f"contract criterion bad/duplicate id: {c}")
            else:
                crit_ids.add(cid)
            if not isinstance(c.get("kind"), str) or c["kind"] not in _CONTRACT_KINDS:
                errs.append(f"contract criterion {cid} bad kind: {c.get('kind')}")

    env = load("env_map.json", parts.get("env_map", False))
    obs_ids = set()
    if env is not None:
        for o in objects(env, "observables", "env_map"):
            oid = o.get("id")
            if not isinstance(oid, str) or not oid or oid in obs_ids:
                errs.append(f"env_map observable bad/duplicate id: {o}")
            else:
                obs_ids.add(oid)

    ev = load("evidence_manifest.json", parts.get("evidence_manifest", False))
    if ev is not None:
        if "judge_evidence" in ev or ev.get("schema") in (
                "veritas/evidence-manifest/1", "veritas/evidence-surface/1"):
            errs.append("evidence_manifest.json is an evidence surface, not criterion bindings")
        for b in objects(ev, "bindings", "evidence_manifest"):
            status = b.get("status")
            if not isinstance(status, str) or status not in _BINDING_STATUS:
                errs.append(f"binding bad status: {b}")
            cid = b.get("criterion")
            if not isinstance(cid, str) or cid not in crit_ids:
                errs.append(f"binding references unknown criterion {b.get('criterion')}")
            evidence = b.get("evidence")
            if not isinstance(evidence, list) or any(not isinstance(e, str) for e in evidence):
                errs.append("binding evidence must be a list of observable IDs")
                evidence = []
            for e in evidence:
                if e not in obs_ids:
                    errs.append(f"binding references unknown observable {e}")
            if status == "bound":
                if not evidence:
                    errs.append("bound binding must cite evidence")
                check = b.get("check")
                if not isinstance(check, str) or not check:
                    errs.append("bound binding must name a check")
                else:
                    file_name = check.split("::", 1)[0]
                    target = (Path(pkg_dir) / file_name).resolve()
                    if Path(cdir).resolve() not in target.parents or not target.is_file():
                        errs.append(f"binding references missing/outside check {check}")
    load("rubric.json", parts.get("rubric", False))
    return errs


def _selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "checker.py")
        open(src, "w").write("print('hi')\n")
        # monolithic: checks + provenance only
        p1 = from_trial(d, "tau2", "airline:0", src,
                        probe={"outcome": "ok", "shipped": "original"},
                        model="endpoint/model", roll_tag="aa1")
        assert validate_package(p1) == [], validate_package(p1)
        idx = json.load(open(os.path.join(p1, "package.json")))
        assert idx["parts"]["contract"] is False and idx["parts"]["checks"] == ["checker.py"]
        # staged: full parts + referential integrity
        contract = {"task_id": "t", "criteria": [
            {"id": "c1", "kind": "outcome", "statement": "final DB state reflects the booking"},
            {"id": "c2", "kind": "forbidden_side_effect", "statement": "no unrelated rows changed"}]}
        env = {"observables": [{"id": "o1", "kind": "file", "path_or_ref": "/app/db_after.json",
                                "access": "read"}], "capabilities_used": ["filesystem"]}
        ev = {"bindings": [
            {"criterion": "c1", "evidence": ["o1"], "check": "checks/checker.py", "status": "bound"},
            {"criterion": "c2", "evidence": [], "check": None, "status": "unsupported"}]}
        p2 = build_package(os.path.join(d, "full"), "tau2", "airline:1",
                           {"checker.py": src},
                           provenance={"generator": {"model": "m"}, "probe": {},
                                       "source": {}, "pipeline": {"mode": "staged"}},
                           contract=contract, env_map=env, evidence_manifest=ev)
        assert validate_package(p2) == [], validate_package(p2)
        # broken reference is caught
        ev_bad = {"bindings": [{"criterion": "cX", "evidence": ["oY"], "status": "bound"}]}
        p3 = build_package(os.path.join(d, "bad"), "tau2", "airline:2",
                           {"checker.py": src}, provenance={"generator": {}, "probe": {},
                                                            "source": {}},
                           contract=contract, env_map=env, evidence_manifest=ev_bad)
        errs = validate_package(p3)
        assert any("unknown criterion" in e for e in errs) and any("unknown observable" in e for e in errs)
    print("verifier_package selftest OK")


if __name__ == "__main__":
    _selftest()
