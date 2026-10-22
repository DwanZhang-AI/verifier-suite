"""Three-state verdicts, anchor records and the per-task label.

A verdict is PASS, FAIL or NO_VERDICT. NO_VERDICT means the run produced no
judgment of the verifier: the verifier could not be staged or started, timed
out, was killed, or left no readable result. It is never folded into FAIL.

Two adapters turn raw outcomes into verdicts:

* :func:`from_exit_code` for verifier scripts judged by exit status (the
  bridge's ``veritas_verdict.json``, the upstream ``/app/verifier.sh`` runs):
  0 is PASS; 126, 127 and 137 (not executable, command not found, killed),
  a timeout, a staging failure or a missing status are NO_VERDICT; any other
  status is FAIL.
* :func:`from_reward` for Harbor reward files: 1 is PASS, 0 is FAIL; a missing
  reward, a value outside {0, 1} or a read error is NO_VERDICT. There is no 0.5
  threshold.

:func:`label_task` combines a task's anchor records into one
:class:`TaskLabel`. The first matching row wins:

1. ``infra_error``: an infrastructure failure (the caller's ``infra`` flag, or
   a record carrying ``raw["infra"]``); re-run, never counted.
2. ``undelivered``: no verifier was delivered.
3. ``unvalidated``: a verifier was delivered but the anchors were not run
   (``gavel-harness gen`` without ``--validate``).
4. ``null_accepted``: the null anchor is PASS.
5. ``oracle_rejected``: the oracle anchor is FAIL.
6. ``anchor_inconclusive``: any anchor that was run is NO_VERDICT.
7. ``no_oracle``: the task has no reference solution.
8. ``validated_2way``: the swap anchor is PASS (reported, not a success).
9. ``validated_strict``: the swap anchor is FAIL.
10. ``validated``: no swap anchor could be constructed.

Rows 8 to 10 are reached only with null FAIL and oracle PASS. Every result row
keeps all anchor records, so any other tabulation can be re-derived.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Verdict(StrEnum):
    """Outcome of one verifier run."""

    PASS = "PASS"
    FAIL = "FAIL"
    NO_VERDICT = "NO_VERDICT"


class AnchorKind(StrEnum):
    """What the environment holds when an anchor runs the verifier."""

    NULL = "null"
    """The environment as built; nothing was done."""
    ORACLE = "oracle"
    """The task's own reference solution was applied."""
    SWAP = "swap"
    """Another task's reference solution was applied."""


NO_VERDICT_EXIT_CODES = frozenset({126, 127, 137})
"""Exit statuses that say the verifier did not run to a judgment: not executable,
command not found, killed (SIGKILL)."""


@dataclass(frozen=True)
class AnchorRecord:
    """One anchor run of one task's verifier.

    ``reason`` is machine-readable: ``exit_<n>``, ``timeout``,
    ``staging_failed:<what>``, ``reward_missing``, ``image_drift``, and the
    other codes listed in :mod:`gavel_harness.verify.anchors`. ``raw`` holds
    the measured value (``exit_code``, ``reward``) and detail; a record whose
    failure lies in the infrastructure carries ``raw["infra"]``.
    ``duration_s`` is the wall-clock time of the anchor run, environment build
    included.
    """

    task: str
    anchor: AnchorKind
    verdict: Verdict
    reason: str
    raw: dict[str, Any] = field(hash=False)
    verifier_sha256: str
    image_id: str | None
    duration_s: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "anchor", AnchorKind(self.anchor))
        object.__setattr__(self, "verdict", Verdict(self.verdict))
        object.__setattr__(self, "raw", dict(self.raw))

    @property
    def infra(self) -> str | None:
        """The infrastructure failure this record carries, or None."""
        value = self.raw.get("infra")
        return str(value) if value else None

    def to_dict(self) -> dict[str, Any]:
        """The record as JSON data."""
        return {
            "task": self.task,
            "anchor": self.anchor.value,
            "verdict": self.verdict.value,
            "reason": self.reason,
            "raw": dict(self.raw),
            "verifier_sha256": self.verifier_sha256,
            "image_id": self.image_id,
            "duration_s": self.duration_s,
        }


def from_exit_code(
    code: int | None,
    *,
    timed_out: bool = False,
    staging_error: str | None = None,
) -> tuple[Verdict, str]:
    """The verdict and reason for a verifier judged by its exit status.

    A staging error wins over a timeout, and a timeout over the status: neither
    leaves a status that judges the staged content. ``code`` is a shell exit
    status (0 to 255) or None when none was recorded; any other integer is a
    caller error (ValueError).
    """
    if staging_error is not None:
        if not staging_error:
            raise ValueError("staging_error must name what failed")
        return Verdict.NO_VERDICT, f"staging_failed:{staging_error}"
    if timed_out:
        return Verdict.NO_VERDICT, "timeout"
    if code is None:
        return Verdict.NO_VERDICT, "exit_missing"
    if isinstance(code, bool) or not isinstance(code, int) or not 0 <= code <= 255:
        raise ValueError(f"an exit status is an integer from 0 to 255, got {code!r}")
    if code == 0:
        return Verdict.PASS, "exit_0"
    if code in NO_VERDICT_EXIT_CODES:
        return Verdict.NO_VERDICT, f"exit_{code}"
    return Verdict.FAIL, f"exit_{code}"


def from_reward(value: object | None, *, error: str | None = None) -> tuple[Verdict, str]:
    """The verdict and reason for a Harbor reward value.

    ``value`` is the reward itself (the ``reward`` entry of a reward file), or
    None when the file is missing. Booleans are not rewards. ``error`` names a
    failure to read the reward and wins over ``value``.
    """
    if error is not None:
        if not error:
            raise ValueError("error must name what failed")
        return Verdict.NO_VERDICT, f"reward_error:{error}"
    if value is None:
        return Verdict.NO_VERDICT, "reward_missing"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return Verdict.NO_VERDICT, "reward_invalid"
    if value == 1:
        return Verdict.PASS, "reward_1"
    if value == 0:
        return Verdict.FAIL, "reward_0"
    return Verdict.NO_VERDICT, "reward_invalid"


class TaskLabel(StrEnum):
    """Per-task outcome; the precedence is in the module docstring."""

    VALIDATED_STRICT = "validated_strict"
    """Null FAIL, oracle PASS, swap FAIL."""
    VALIDATED = "validated"
    """Null FAIL, oracle PASS, no swap anchor could be constructed."""
    VALIDATED_2WAY = "validated_2way"
    """Null FAIL, oracle PASS, swap PASS: accepts another task's solution; not a success."""
    NULL_ACCEPTED = "null_accepted"
    """The untouched environment passes."""
    ORACLE_REJECTED = "oracle_rejected"
    """The task's own reference solution fails."""
    NO_ORACLE = "no_oracle"
    """No reference solution; null (and swap, when constructed) gave verdicts."""
    ANCHOR_INCONCLUSIVE = "anchor_inconclusive"
    """An anchor that was run gave NO_VERDICT."""
    UNDELIVERED = "undelivered"
    """No verifier was delivered."""
    UNVALIDATED = "unvalidated"
    """A verifier was delivered; its anchors were not run."""
    INFRA_ERROR = "infra_error"
    """An infrastructure failure; not counted, re-run."""


SUCCESS_LABELS = frozenset({TaskLabel.VALIDATED_STRICT, TaskLabel.VALIDATED})
"""Labels counted as a validated verifier."""


def label_task(
    records: Sequence[AnchorRecord],
    *,
    delivered: bool,
    has_oracle: bool,
    swap_constructible: bool,
    infra: bool = False,
    anchors_run: bool = True,
) -> TaskLabel:
    """The label of one task from its anchor records (precedence in the module docstring).

    Unless the task is an infrastructure failure, the records must be exactly
    the anchors that were run: none for an undelivered task or when
    ``anchors_run`` is False, otherwise one null record, one oracle record when
    ``has_oracle`` and one swap record when ``swap_constructible``. Records of
    several tasks, repeated anchors or a mismatch raise ValueError.
    """
    by_kind: dict[AnchorKind, AnchorRecord] = {}
    for record in records:
        if record.anchor in by_kind:
            raise ValueError(f"task {record.task!r} has two {record.anchor} records")
        by_kind[record.anchor] = record
    tasks = {record.task for record in records}
    if len(tasks) > 1:
        raise ValueError(f"records of several tasks given: {sorted(tasks)}")

    if infra or any(record.infra for record in records):
        return TaskLabel.INFRA_ERROR
    if not delivered:
        if records:
            raise ValueError("an undelivered task has no anchor records")
        return TaskLabel.UNDELIVERED
    if not anchors_run:
        if records:
            raise ValueError("anchor records given for a task whose anchors were not run")
        return TaskLabel.UNVALIDATED
    expected = {AnchorKind.NULL}
    if has_oracle:
        expected.add(AnchorKind.ORACLE)
    if swap_constructible:
        expected.add(AnchorKind.SWAP)
    if set(by_kind) != expected:
        raise ValueError(
            f"anchor records {sorted(by_kind)} do not match the anchors that apply "
            f"({sorted(expected)})"
        )

    null = by_kind[AnchorKind.NULL]
    oracle = by_kind.get(AnchorKind.ORACLE)
    swap = by_kind.get(AnchorKind.SWAP)
    if null.verdict == Verdict.PASS:
        return TaskLabel.NULL_ACCEPTED
    if oracle is not None and oracle.verdict == Verdict.FAIL:
        return TaskLabel.ORACLE_REJECTED
    if any(record.verdict == Verdict.NO_VERDICT for record in records):
        return TaskLabel.ANCHOR_INCONCLUSIVE
    if oracle is None:
        return TaskLabel.NO_ORACLE
    if swap is None:
        return TaskLabel.VALIDATED
    if swap.verdict == Verdict.PASS:
        return TaskLabel.VALIDATED_2WAY
    return TaskLabel.VALIDATED_STRICT
