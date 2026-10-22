#!/usr/bin/env python3
"""Per-verifier audit certificate: a pure record, written on the host, never a gate.

Validates the judge's declaration against the FIXED judge-time evidence vocabulary
and the task material, then writes certificate.json next to evidence_map.json.
Nothing here blocks, retries, or alters a verdict: findings are recorded for the
telemetry layer and the shipped verifier package. Honesty comes from the
declaration, the accounting and this certificate, not from runtime enforcement.

Certificate fields:
  verifier_sha        sha256 of the collected verifier artifact (or null)
  declaration         present | absent
  binding_check       ids_valid / citations {verbatim, total} / unknown_refs
  unchecked           the judge's own honest gap list (count + entries)
  evidence_bundle     pointer: evidence_map protocol + per-etype presence count
"""
from __future__ import annotations

import hashlib
import json
import os

try:
    from .trial import TrialView
    from .model import load_map, PRESENT
except ImportError:
    from trial import TrialView
    from model import load_map, PRESENT

CERT_SCHEMA = "veritas/certificate/1"
_DECL = "verifier/evidence/gen_declaration.json"


def _norm(s: str) -> str:
    return " ".join(str(s).split())


def _material_text(t: TrialView) -> str:
    parts = []
    base = t.rel("verifier", "evidence")
    if os.path.isdir(base):
        for f in sorted(os.listdir(base)):
            if f.startswith("material_") and os.path.isfile(os.path.join(base, f)):
                with open(os.path.join(base, f), encoding="utf-8", errors="replace") as fh:
                    parts.append(fh.read())
    return _norm("\n".join(parts))


def validate_structure(decl) -> None:
    """Malformed JSON structure is an audit finding, not an uncaught exception."""
    if not isinstance(decl, dict):
        raise ValueError("declaration must be an object")
    for field in ("checks", "unchecked"):
        entries = decl.get(field, [])
        if not isinstance(entries, list) or any(not isinstance(item, dict) for item in entries):
            raise ValueError(f"declaration.{field} must be an array of objects")
    ids = []
    for check in decl.get("checks", []):
        refs = check.get("evidence", [])
        if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
            raise ValueError("check.evidence must be an array of strings")
        if "claim" in check and not isinstance(check["claim"], str):
            raise ValueError("check.claim must be a string")
        if "check_id" in check:
            if not isinstance(check["check_id"], str) or not check["check_id"]:
                raise ValueError("check.check_id must be a non-empty string")
            ids.append(check["check_id"])
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate check_id")


def validate_declaration(decl: dict, vocab: dict, material: str) -> dict:
    """Pure check: vocabulary membership + verbatim citations. Returns findings."""
    validate_structure(decl)
    checks = [c for c in decl.get("checks", []) if isinstance(c, dict)]
    unknown_refs = sorted({e for c in checks for e in (c.get("evidence") or [])
                           if e not in vocab})
    cited = [c for c in checks if _norm(c.get("claim", ""))]
    verbatim = sum(1 for c in cited if material and _norm(c["claim"]) in material)
    unchecked = [u for u in decl.get("unchecked", []) if isinstance(u, dict)]
    return {"n_checks": len(checks),
            "ids_valid": not unknown_refs,
            "unknown_refs": unknown_refs,
            "citations": {"verbatim": verbatim, "total": len(cited)},
            "unchecked": {"count": len(unchecked),
                          "entries": [{k: _norm(u.get(k, ""))[:200]
                                       for k in ("need", "reason")} for u in unchecked[:20]]}}


def build_certificate(trial_dir: str, vocab: dict,
                      verifier_path: str | None = None) -> str:
    """Write certificate.json into the trial dir; returns its path."""
    t = TrialView(trial_dir)
    cert: dict = {"schema": CERT_SCHEMA}

    if verifier_path is None:
        for path in t.deliverable_files():
            if os.path.basename(path) in ("checker.py", "verifier.py", "judge_prompt.txt"):
                verifier_path = t.rel(path)
                break
    if verifier_path and os.path.exists(verifier_path):
        with open(verifier_path, "rb") as fh:
            cert["verifier_sha"] = hashlib.sha256(fh.read()).hexdigest()
        cert["verifier_path"] = os.path.relpath(verifier_path, t.root)
    else:
        cert["verifier_sha"] = None

    dp = t.rel(*_DECL.split("/"))
    if os.path.exists(dp):
        try:
            with open(dp, encoding="utf-8") as fh:
                decl = json.load(fh)
            cert["declaration"] = "present"
            cert["binding_check"] = validate_declaration(decl, vocab, _material_text(t))
        except (ValueError, OSError) as e:
            cert["declaration"] = "present"
            cert["binding_check"] = {"error": f"unparseable: {e}"}
    else:
        cert["declaration"] = "absent"

    try:
        em = load_map(trial_dir)
        cert["evidence_bundle"] = {
            "protocol": em.get("protocol"),
            "etypes_present": len({r["etype"] for r in em.get("records", [])
                                   if r.get("availability") == PRESENT})}
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        cert["evidence_bundle"] = None

    out = t.rel("certificate.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(cert, fh, indent=1, ensure_ascii=False)
    return out


def _selftest():
    import tempfile
    vocab = {"messages": "process.interaction", "db_after": "final.manifest"}
    with tempfile.TemporaryDirectory() as d:
        ev = os.path.join(d, "verifier", "evidence")
        os.makedirs(ev)
        os.makedirs(os.path.join(d, "artifacts", "app"))
        open(os.path.join(d, "artifacts", "app", "checker.py"), "w").write("code")
        open(os.path.join(ev, "material_task_info.json"), "w").write(
            '{"purpose": "the agent must issue a refund of 50 dollars"}')
        json.dump({"schema": "veritas/declaration/1",
                   "checks": [
                       {"check_id": "C1", "claim": "issue a refund of 50 dollars",
                        "evidence": ["db_after"]},
                       {"check_id": "C2", "claim": "totally invented promise",
                        "evidence": ["telepathy"]}],
                   "unchecked": [{"need": "network access log",
                                  "reason": "external.network not collected"}]},
                  open(os.path.join(ev, "gen_declaration.json"), "w"))
        p = build_certificate(d, vocab)
        c = json.load(open(p))
        b = c["binding_check"]
        assert c["declaration"] == "present" and c["verifier_sha"]
        assert b["unknown_refs"] == ["telepathy"] and not b["ids_valid"]
        assert b["citations"] == {"verbatim": 1, "total": 2}     # C2 not in material
        assert b["unchecked"]["count"] == 1
        # absent declaration is a recorded fact, not an error
        os.remove(os.path.join(ev, "gen_declaration.json"))
        c2 = json.load(open(build_certificate(d, vocab)))
        assert c2["declaration"] == "absent" and "binding_check" not in c2
    print("certificate selftest OK")


if __name__ == "__main__":
    _selftest()
