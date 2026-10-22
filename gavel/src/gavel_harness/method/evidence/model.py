#!/usr/bin/env python3
"""Evidence protocol data model.

The contract in one sentence: after EVERY agent run the harness produces an
evidence map — a total, typed account of the run's observable record, where every
one of the 12 evidence types is either PRESENT (with verifiable file references)
or MISSING-DECLARED (with the concrete reason). Nothing is silently absent; the
collector is honest about its own blind spots.

Design rules
  - records REFERENCE files in the trial dir (relative paths); the bundle copies
    nothing. Derived files the collector computes (e.g. the final-state manifest)
    live under evidence/ and are marked generated=true.
  - deterministic: same trial dir -> byte-identical evidence_map.json (no wall
    clock in records; digests + sorted output).
  - stdlib only; no LLM; no dependency on the execution backend.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field, asdict

PROTOCOL_VERSION = "evidence-map/0.1"

#: The 12 evidence types (user's E1-E6 master table, memo §5.1).
ETYPES = (
    "baseline.state",        # E1-4  pre-action snapshot (initial-state anchor)
    "process.action",        # E2-1  tool-call stream
    "process.language",      # E2-1  message-text stream
    "process.interaction",   # E2-1  interaction-turn stream
    "process.checkpoint",    # E2-10 per-step snapshots
    "final.artifact",        # E3-1  deliverables
    "final.diff",            # E3-2  change set vs baseline
    "final.manifest",        # E3-3  end-state fingerprint (listing + digests)
    "final.container",       # E3-5  effects outside the workspace
    "final.deps",            # E3-6  dependency changes
    "external.network",      # E5-11 actual external access
    "derived.metrics",       # E6    platform-derived (second-hand corroboration only)
)

PRESENT, MISSING = "present", "missing_declared"


@dataclass
class EvidenceRecord:
    """One entry of the map: a file (or declared absence) under one etype."""
    etype: str
    availability: str                    # present | missing_declared
    path: str | None = None              # trial-dir-relative; None iff missing
    sha256: str | None = None
    bytes: int | None = None
    generated: bool = False              # True = derived by the collector itself
    reason: str | None = None            # required iff missing_declared
    meta: dict = field(default_factory=dict)

    def validate(self) -> list[str]:
        errs = []
        if self.etype not in ETYPES:
            errs.append(f"bad etype {self.etype!r}")
        if self.availability == PRESENT and not self.path:
            errs.append(f"{self.etype}: present without path")
        if self.availability == PRESENT and (not isinstance(self.sha256, str)
                or len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256)):
            errs.append(f"{self.etype}: present without a full sha256")
        if self.availability == MISSING and not self.reason:
            errs.append(f"{self.etype}: missing without a declared reason")
        if self.availability not in (PRESENT, MISSING):
            errs.append(f"{self.etype}: bad availability {self.availability!r}")
        return errs


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class EvidenceBundle:
    """Accumulates records for one trial; writes evidence/ + evidence_map.json.

    add()            register an existing file under the trial dir
    add_generated()  write a collector-derived file under evidence/ and register it
    declare_missing() record an absence with its concrete reason
    """

    def __init__(self, trial_dir: str):
        self.trial_dir = os.path.abspath(trial_dir)
        self.records: list[EvidenceRecord] = []

    # ---------------------------------------------------------------- building
    def add(self, etype: str, path: str, **meta) -> EvidenceRecord:
        ap = path if os.path.isabs(path) else os.path.join(self.trial_dir, path)
        if os.path.commonpath((os.path.realpath(ap), os.path.realpath(self.trial_dir))) != os.path.realpath(self.trial_dir):
            raise ValueError("evidence reference escapes the trial directory")
        rel = os.path.relpath(ap, self.trial_dir)
        rec = EvidenceRecord(etype=etype, availability=PRESENT, path=rel,
                             sha256=_sha256(ap), bytes=os.path.getsize(ap),
                             meta=meta)
        self.records.append(rec)
        return rec

    def add_generated(self, etype: str, name: str, content: str | bytes,
                      **meta) -> EvidenceRecord:
        d = os.path.join(self.trial_dir, "evidence")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, name)
        if os.path.commonpath((os.path.realpath(p), os.path.realpath(d))) != os.path.realpath(d):
            raise ValueError("generated evidence name escapes evidence directory")
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(p, mode) as fh:
            fh.write(content)
        rec = self.add(etype, p, **meta)
        rec.generated = True
        return rec

    def declare_missing(self, etype: str, reason: str, **meta) -> EvidenceRecord:
        rec = EvidenceRecord(etype=etype, availability=MISSING, reason=reason,
                             meta=meta)
        self.records.append(rec)
        return rec

    # ---------------------------------------------------------------- output
    def to_map(self, collector_id: str) -> dict:
        errs = [e for r in self.records for e in r.validate()]
        covered = {r.etype for r in self.records}
        errs += [f"etype not accounted for: {t}" for t in ETYPES if t not in covered]
        errs += [f"{t}: both present and missing_declared; use source-level metadata for partial absence"
                 for t in covered if len({r.availability for r in self.records if r.etype == t}) > 1]
        if errs:
            raise ValueError("invalid bundle: " + "; ".join(errs))
        recs = sorted((asdict(r) for r in self.records),
                      key=lambda r: (ETYPES.index(r["etype"]), r["path"] or ""))
        for r in recs:                                   # drop empty optionals
            for k in ("path", "sha256", "bytes", "reason"):
                if r[k] is None:
                    del r[k]
            if not r["meta"]:
                del r["meta"]
            if not r["generated"]:
                del r["generated"]
        return {"protocol": PROTOCOL_VERSION, "collected_by": collector_id,
                "records": recs}

    def write(self, collector_id: str) -> str:
        out = os.path.join(self.trial_dir, "evidence_map.json")
        payload = self.to_map(collector_id)  # validate before opening/truncating an existing map
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1, ensure_ascii=False, sort_keys=False)
        return out


def load_map(trial_dir: str) -> dict:
    with open(os.path.join(trial_dir, "evidence_map.json"), encoding="utf-8") as fh:
        return json.load(fh)


def coverage(maps: list[dict]) -> dict:
    """Aggregate: per etype -> {present, missing, generated} counts."""
    tab = {t: {"present": 0, "missing": 0, "generated": 0} for t in ETYPES}
    for m in maps:
        seen = {}
        for r in m.get("records", []):
            t = r["etype"]
            if r["availability"] == PRESENT:
                seen[t] = "present"
                if r.get("generated"):
                    tab[t]["generated"] += 1
            else:
                seen.setdefault(t, "missing")
        for t, s in seen.items():
            tab[t][s] += 1
    return tab


MANIFEST_SCHEMA = "veritas/evidence-surface/1"


def write_judge_manifest(package_dir: str, judge_evidence: dict) -> str:
    """the machine-readable twin of the prompt's evidence header (verifier
    generation starts from the evidence). One file per task package: the
    judge-time evidence surface the shipped verifier may consume.
    Downstream conformance validates certificate declarations against exactly this set.
    The legacy filename stays evidence_manifest.json for adapter compatibility;
    this is a vocabulary surface, NOT the staged criterion-binding manifest.
    Its schema lives in schemas/evidence_surface.schema.json."""
    bad = [et for et in judge_evidence.values() if et not in ETYPES]
    if bad:
        raise ValueError(f"unknown evidence types in manifest: {bad}")
    p = os.path.join(package_dir, "evidence_manifest.json")
    with open(p, "w") as fh:
        json.dump({"schema": MANIFEST_SCHEMA,
                   "judge_evidence": dict(sorted(judge_evidence.items()))},
                  fh, ensure_ascii=False, indent=1, sort_keys=True)
    return p


def _selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "result.json"), "w").write("{}")
        b = EvidenceBundle(d)
        b.add("derived.metrics", "result.json")
        b.add_generated("final.manifest", "final_manifest.json", '{"files": []}')
        for t in ETYPES:
            if t not in ("derived.metrics", "final.manifest"):
                b.declare_missing(t, "selftest: not collected")
        p = b.write("selftest/0")
        m1 = load_map(d)
        b2 = EvidenceBundle(d)                        # determinism: rebuild -> same bytes
        b2.add("derived.metrics", "result.json")
        b2.add_generated("final.manifest", "final_manifest.json", '{"files": []}')
        for t in ETYPES:
            if t not in ("derived.metrics", "final.manifest"):
                b2.declare_missing(t, "selftest: not collected")
        assert json.dumps(m1, sort_keys=True) == json.dumps(b2.to_map("selftest/0"),
                                                            sort_keys=True)
        assert coverage([m1])["derived.metrics"]["present"] == 1
        assert coverage([m1])["process.action"]["missing"] == 1
        bad = EvidenceBundle(d)
        bad.declare_missing("process.action", "")     # missing without reason
        try:
            bad.to_map("x")
            raise AssertionError("must reject empty reason / uncovered etypes")
        except ValueError:
            pass
        assert os.path.basename(p) == "evidence_map.json"
    print("model selftest OK")


if __name__ == "__main__":
    _selftest()
