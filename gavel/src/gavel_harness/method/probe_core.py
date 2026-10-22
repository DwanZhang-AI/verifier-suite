#!/usr/bin/env python3
"""probe_core: validity-probe orchestration for the judge harness.

Runs a dataset-specific PROBE against the produced verifier in its real environment,
classifies the outcome with precision-first rules, optionally re-runs the generating
session once with the probe's diagnostic as feedback, and ships under a
delivery-invariant rule (the original artifact ships on any doubt; a retry artifact
ships only if its own probe is clean).

Rules:
- a trigger must be deterministic failure evidence (build error, passes on the
  unfixed code), never a liveness or timing heuristic.
- budget cap: at most one extra generation per task, whatever the trigger.
- delivery invariance: probing may upgrade an artifact, never lose one.

The module is pure orchestration: callers supply two callables (run_probe, regenerate)
so it works the same for a shell driver, a Harbor job, or a local test.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Optional


# probe outcome classes (the ONLY vocabulary downstream code may branch on)
OK = "ok"                    # artifact valid as far as the probe can tell
CRASH = "crash"              # cannot execute: build/import/collection-class failure
NODIRECTION = "nodirection"  # executes but provably carries no signal (passes unfixed base)
SKIP = "skip"                # probe infrastructure failed / not applicable — NEVER a trigger


@dataclass
class ProbeSpec:
    """dataset adapter's probe configuration (judge/adapters/<ds>.py provides one)."""
    crash_patterns: list[str] = field(default_factory=list)   # regex on probe output -> CRASH
    nodirection_patterns: list[str] = field(default_factory=list)  # regex -> NODIRECTION
    ok_patterns: list[str] = field(default_factory=list)      # regex -> OK (checked last)
    crash_feedback: str = ("your previously generated verifier FAILED TO EXECUTE in the "
                           "target environment. Diagnostic:\n{diag}\nRewrite it so it "
                           "builds and runs: use only identifiers you can actually see "
                           "in the provided material.")
    nodirection_feedback: str = ("your previously generated verifier PASSES on the "
                                 "UNFIXED material, so it cannot distinguish a correct "
                                 "solution from no change.\nDiagnostic:\n{diag}\nWrite "
                                 "assertions that witness the described problem: they "
                                 "must fail before the fix and pass after it.")
    skip_patterns: list[str] = field(default_factory=list)  # explicit unknown beats presence


def classify(output: str, spec: ProbeSpec) -> str:
    """Order: CRASH > NODIRECTION > explicit SKIP > OK > implicit SKIP.
    An output matching nothing is SKIP (precision-first: unknown never triggers)."""
    for pat in spec.crash_patterns:
        if re.search(pat, output, re.M):
            return CRASH
    for pat in spec.nodirection_patterns:
        if re.search(pat, output, re.M):
            return NODIRECTION
    for pat in spec.skip_patterns:
        if re.search(pat, output, re.M):
            return SKIP
    for pat in spec.ok_patterns:
        if re.search(pat, output, re.M):
            return OK
    return SKIP


@dataclass
class ProbeResult:
    outcome: str                 # final artifact's probe class
    shipped: str                 # "original" | "retry"
    retried: bool
    first_outcome: str
    diag: str = ""
    markers: list[str] = field(default_factory=list)   # provenance lines for gen.log


def merge(task_id: str, spec: ProbeSpec, first_output: str,
          retry_output: str | None = None, *, retry_attempted: bool = False,
          retry_artifact_available: bool = True) -> ProbeResult:
    """Single source of truth for single-task and batch delivery decisions."""
    first = classify(first_output, spec)
    markers = [f"PROBE_{first.upper()} {task_id}"]
    if retry_attempted:
        second = classify(retry_output or "", spec)
        if second == OK and retry_artifact_available:
            markers.append(f"PROBE_RESCUED {task_id}")
            return ProbeResult(OK, "retry", True, first, (retry_output or "")[-1500:], markers)
        markers.append(f"PROBE_KEPT_ORIGINAL {task_id} retry_{second}")
        if retry_output is None:
            markers.append(f"PROBE_RETRY_NOARTIFACT {task_id}")
    return ProbeResult(first, "original", retry_attempted, first, first_output[-1500:], markers)


def run(task_id: str,
        spec: ProbeSpec,
        run_probe: Callable[[], str],
        regenerate: Optional[Callable[[str], bool]] = None,
        reprobe: Optional[Callable[[], str]] = None) -> ProbeResult:
    """Orchestrate probe -> classify -> (one feedback retry) -> ship-invariant decision.

    run_probe() -> probe output for the CURRENT artifact.
    regenerate(feedback_text) -> True if a retry artifact was produced (the caller is
        responsible for setting aside the original — ship rules below assume it can
        restore the original if the retry is not clean).
    reprobe() -> probe output for the retry artifact.

    Returns which artifact ships. SKIP and OK ship the original with no retry; CRASH and
    NODIRECTION spend the single retry (if regenerate is provided); the retry ships only
    if its own probe classifies OK — anything else restores the original.
    """
    out1 = run_probe()
    first = classify(out1, spec)
    if first in (OK, SKIP) or regenerate is None or reprobe is None:
        return merge(task_id, spec, out1)
    feedback = (spec.crash_feedback if first == CRASH else spec.nodirection_feedback)
    feedback = feedback.replace("{diag}", out1[-1500:])
    if not regenerate(feedback):
        return merge(task_id, spec, out1, retry_attempted=True,
                     retry_artifact_available=False)
    out2 = reprobe()
    return merge(task_id, spec, out1, out2, retry_attempted=True)


def _selftest():
    spec = ProbeSpec(crash_patterns=[r"^BUILD_PROBE=FAIL", r"build failed"],
                     nodirection_patterns=[r"^PROBE=NODIRECTION"],
                     ok_patterns=[r"^BUILD_PROBE=OK", r"^PROBE=OK"])
    # ok -> ships original, no retry
    r = run("t1", spec, run_probe=lambda: "BUILD_PROBE=OK")
    assert (r.outcome, r.shipped, r.retried) == (OK, "original", False)
    # crash -> retry clean -> ships retry
    calls = {}
    r = run("t2", spec, run_probe=lambda: "build failed\nundefined: Foo",
            regenerate=lambda fb: calls.setdefault("fb", fb) or True,
            reprobe=lambda: "BUILD_PROBE=OK")
    assert (r.outcome, r.shipped, r.retried) == (OK, "retry", True)
    assert "undefined: Foo" in calls["fb"] and "FAILED TO EXECUTE" in calls["fb"]
    assert "PROBE_RESCUED t2" in r.markers
    # nodirection -> retry still bad -> original restored, honest outcome
    r = run("t3", spec, run_probe=lambda: "PROBE=NODIRECTION",
            regenerate=lambda fb: True, reprobe=lambda: "PROBE=NODIRECTION")
    assert (r.outcome, r.shipped, r.retried) == (NODIRECTION, "original", True)
    # unknown output -> SKIP, never triggers
    r = run("t4", spec, run_probe=lambda: "something weird",
            regenerate=lambda fb: (_ for _ in ()).throw(AssertionError("must not retry")),
            reprobe=lambda: "")
    assert (r.outcome, r.shipped, r.retried) == (SKIP, "original", False)
    # crash with no regenerate hook -> ships original
    r = run("t5", spec, run_probe=lambda: "BUILD_PROBE=FAIL x")
    assert (r.outcome, r.shipped) == (CRASH, "original")
    print("probe_core selftest OK")


if __name__ == "__main__":
    _selftest()
