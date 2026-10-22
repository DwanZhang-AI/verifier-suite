"""Run reports: ``results.jsonl``, ``summary.md``, one ``VERIFIER_REPORT.md`` per task, exit code.

Every task that entered generation has exactly one :class:`TaskResult`, whatever
happened to it; infrastructure failures (a task environment that could not be
built or started included) and undelivered tasks are rows like any other and
are listed in the summary, never dropped. Tasks refused before generation have no row; the summary lists them
from the refusal list the caller passes.

Label precedence (first match wins), as computed by
:func:`gavel_harness.verify.verdict.label_task` and stated in every report:
``infra_error`` → ``undelivered`` → ``unvalidated`` → ``null_accepted`` →
``oracle_rejected`` → ``anchor_inconclusive`` → ``no_oracle`` → ``validated_2way``
→ ``validated_strict`` → ``validated``. A row keeps all three anchor records, so
any other tabulation can be re-derived from ``results.jsonl``.

Denominator of every share: the result rows minus ``infra_error`` rows, which
are not capability outcomes and are re-run. Only ``validated_strict`` and
``validated`` count as validated;
``validated_2way`` (the verifier accepted another task's solution) is reported
but does not.

Report files are created, never overwritten.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import PARADIGMS
from ..errors import ConfigError, ExitCode
from ..verify.verdict import (
    SUCCESS_LABELS,
    AnchorKind,
    AnchorRecord,
    TaskLabel,
    Verdict,
    label_task,
)

RESULTS_FILE = "results.jsonl"
SUMMARY_FILE = "summary.md"
TASK_REPORT_FILE = "VERIFIER_REPORT.md"
RESULT_SCHEMA = "veritas-result/1"

LABEL_PRECEDENCE: tuple[TaskLabel, ...] = (
    TaskLabel.INFRA_ERROR,
    TaskLabel.UNDELIVERED,
    TaskLabel.UNVALIDATED,
    TaskLabel.NULL_ACCEPTED,
    TaskLabel.ORACLE_REJECTED,
    TaskLabel.ANCHOR_INCONCLUSIVE,
    TaskLabel.NO_ORACLE,
    TaskLabel.VALIDATED_2WAY,
    TaskLabel.VALIDATED_STRICT,
    TaskLabel.VALIDATED,
)
"""Order in which :func:`~gavel_harness.verify.verdict.label_task` tests the labels."""

LABEL_CONDITIONS: Mapping[TaskLabel, str] = {
    TaskLabel.INFRA_ERROR: "an infrastructure failure hit the task; not a capability outcome",
    TaskLabel.UNDELIVERED: "generation delivered no verifier",
    TaskLabel.UNVALIDATED: "a verifier was delivered; the anchors were not run",
    TaskLabel.NULL_ACCEPTED: "null PASS: the verifier accepts the untouched environment",
    TaskLabel.ORACLE_REJECTED: "oracle FAIL: the verifier rejects the reference solution",
    TaskLabel.ANCHOR_INCONCLUSIVE: "an anchor that was run gave NO_VERDICT",
    TaskLabel.NO_ORACLE: "null FAIL; no reference solution to confirm acceptance",
    TaskLabel.VALIDATED_2WAY: (
        "null FAIL, oracle PASS, swap PASS: the verifier accepts another task's solution"
    ),
    TaskLabel.VALIDATED_STRICT: "null FAIL, oracle PASS, swap FAIL",
    TaskLabel.VALIDATED: "null FAIL, oracle PASS; no swap could be constructed",
}
"""One-line condition of each label, as printed in the reports."""

ANCHOR_ORDER: tuple[AnchorKind, ...] = (AnchorKind.NULL, AnchorKind.ORACLE, AnchorKind.SWAP)
EXPECTED_VERDICTS: Mapping[AnchorKind, Verdict] = {
    AnchorKind.NULL: Verdict.FAIL,
    AnchorKind.ORACLE: Verdict.PASS,
    AnchorKind.SWAP: Verdict.FAIL,
}
"""The verdict a sound verifier gives on each anchor."""
_ANCHOR_SETUP = {
    AnchorKind.NULL: "untouched environment",
    AnchorKind.ORACLE: "the task's reference solution applied",
    AnchorKind.SWAP: "another task's reference solution applied",
}
_IMAGE_DRIFT_REASON = "image_drift"
_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class TaskResult:
    """The result row of one task; written as one line of ``results.jsonl``.

    Construction checks the row for consistency and raises ValueError when it
    is inconsistent; in particular ``label`` must equal what
    :func:`~gavel_harness.verify.verdict.label_task` gives for the row's
    anchors, delivery, oracle, swap donor and ``infra_error``.
    """

    task: str
    paradigm: str
    profile: str
    identity_sha256: str | None
    """Identity digest of the generation package; None when the run recorded none."""
    delivered: bool
    probe: str | None
    """Probe outcome of the shipped attempt; None when no probe ran."""
    attempts: int
    """Generation attempts made (A, plus B after a feedback retry)."""
    verifier_sha256: str | None
    """sha256 of the delivered verifier; None exactly when nothing was delivered."""
    has_oracle: bool
    """Whether the task has a reference solution for the oracle anchor."""
    swap_donor: str | None
    """Task whose solution the swap anchor used; None when no swap could be constructed."""
    swap_cross_type: bool | None
    """Whether the donor's deliverable type differs; None exactly when there is no donor."""
    anchors: tuple[AnchorRecord, ...]
    """The anchors that ran, at most one per kind, in null, oracle, swap order."""
    label: TaskLabel
    usage: Mapping[str, Any]
    """Token counts of all attempts (A+B) by name, or ``{"unavailable": reason}``."""
    absorbed_429: int | None
    """Rate-limit responses the metering proxy absorbed; None when not metered."""
    contaminated_429: bool | None
    """Whether a 429 reached the agent; None when not metered."""
    dropped_task_config: Mapping[str, Any]
    """task.toml settings the generation package did not carry, by ``<section>.<field>``."""
    infra_error: str | None = None
    """``[<category>] <detail>`` of a task-level infrastructure failure (e.g. the
    task's environment could not be built or started). A row is also
    ``infra_error`` when one of its anchor records carries an infrastructure failure."""
    anchors_run: bool = True
    """Whether the anchors were run for this task; False for ``gavel-harness gen`` without
    ``--validate``, whose delivered tasks are ``unvalidated``."""
    meter: Mapping[str, int] | None = None
    """The metering proxy's ledger totals over the trials of the counted attempts
    (:class:`~gavel_harness.meter.TrialUsage` fields); None when not metered."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", TaskLabel(self.label))
        object.__setattr__(self, "dropped_task_config", dict(self.dropped_task_config))
        object.__setattr__(self, "usage", dict(self.usage))
        if self.meter is not None:
            object.__setattr__(self, "meter", dict(self.meter))
        records = tuple(self.anchors)
        if not all(isinstance(record, AnchorRecord) for record in records):
            raise ValueError(f"{self.task}: anchors must be AnchorRecord instances")
        by_kind = {AnchorKind(record.anchor): record for record in records}
        if len(by_kind) != len(records):
            raise ValueError(f"{self.task}: more than one anchor record of one kind")
        object.__setattr__(self, "anchors",
                           tuple(by_kind[kind] for kind in ANCHOR_ORDER if kind in by_kind))
        self._check()
        expected = label_task(self.anchors, delivered=self.delivered, has_oracle=self.has_oracle,
                              swap_constructible=self.swap_donor is not None,
                              infra=self.infra_error is not None, anchors_run=self.anchors_run)
        if self.label != expected:
            raise ValueError(f"{self.task}: label {self.label} contradicts the row, "
                             f"which gives {expected}")

    def _check(self) -> None:
        name = self.task
        if not name:
            raise ValueError("task must not be empty")
        if self.paradigm not in PARADIGMS:
            raise ValueError(f"{name}: unknown paradigm {self.paradigm!r}")
        if not self.profile:
            raise ValueError(f"{name}: profile must not be empty")
        for what in ("delivered", "has_oracle", "anchors_run"):
            if not isinstance(getattr(self, what), bool):
                raise ValueError(f"{name}: {what} must be a bool")
        if self.swap_cross_type is not None and not isinstance(self.swap_cross_type, bool):
            raise ValueError(f"{name}: swap_cross_type must be a bool or None")
        for what in ("identity_sha256", "verifier_sha256"):
            value = getattr(self, what)
            if value is not None and not _SHA256.fullmatch(value):
                raise ValueError(f"{name}: {what} must be a hex sha256, got {value!r}")
        if self.delivered != (self.verifier_sha256 is not None):
            raise ValueError(
                f"{name}: verifier_sha256 is set exactly when a verifier was delivered")
        if not _count(self.attempts) or (self.delivered and self.attempts < 1):
            raise ValueError(f"{name}: attempts must be a count, at least 1 when delivered")
        if (self.swap_donor is None) != (self.swap_cross_type is None):
            raise ValueError(f"{name}: swap_cross_type is set exactly when there is a swap donor")
        if self.swap_donor == name:
            raise ValueError(f"{name}: a task cannot be its own swap donor")
        for record in self.anchors:
            if record.task != name:
                raise ValueError(f"{name}: holds an anchor record of task {record.task!r}")
            if record.verifier_sha256 != self.verifier_sha256:
                raise ValueError(f"{name}: the {record.anchor} anchor judged another verifier")
        kinds = {record.anchor for record in self.anchors}
        if AnchorKind.ORACLE in kinds and not self.has_oracle:
            raise ValueError(f"{name}: an oracle anchor ran without a reference solution")
        if AnchorKind.SWAP in kinds and self.swap_donor is None:
            raise ValueError(f"{name}: a swap anchor ran without a swap donor")
        _check_usage(name, self.usage)
        if self.absorbed_429 is not None and not _count(self.absorbed_429):
            raise ValueError(f"{name}: absorbed_429 must be a count or None")
        if self.contaminated_429 is not None and not isinstance(self.contaminated_429, bool):
            raise ValueError(f"{name}: contaminated_429 must be a bool or None")
        if self.meter is not None and not (self.meter and all(
                isinstance(key, str) and _count(value) for key, value in self.meter.items())):
            raise ValueError(f"{name}: meter must map names to counts, or be None")
        for what in ("infra_error", "probe"):
            value = getattr(self, what)
            if value is not None and not (isinstance(value, str) and value.strip()):
                raise ValueError(f"{name}: {what} must be a non-empty string or None")

    def anchor(self, kind: AnchorKind) -> AnchorRecord | None:
        """The record of anchor ``kind``, or None when that anchor did not run."""
        return next((record for record in self.anchors if record.anchor == kind), None)

    @property
    def in_denominator(self) -> bool:
        """Whether the row counts toward shares: every row but ``infra_error``."""
        return self.label is not TaskLabel.INFRA_ERROR

    def to_json(self) -> dict[str, Any]:
        """The ``results.jsonl`` row: anchors keyed by kind, an anchor that did not run as null."""
        return {
            "schema": RESULT_SCHEMA,
            "task": self.task,
            "paradigm": self.paradigm,
            "profile": self.profile,
            "identity_sha256": self.identity_sha256,
            "delivered": self.delivered,
            "probe": self.probe,
            "attempts": self.attempts,
            "verifier_sha256": self.verifier_sha256,
            "has_oracle": self.has_oracle,
            "swap_donor": self.swap_donor,
            "swap_cross_type": self.swap_cross_type,
            "anchors": {str(kind): _record_json(self.anchor(kind)) for kind in ANCHOR_ORDER},
            "label": str(self.label),
            "usage": dict(self.usage),
            "absorbed_429": self.absorbed_429,
            "contaminated_429": self.contaminated_429,
            "dropped_task_config": dict(self.dropped_task_config),
            "infra_error": self.infra_error,
            "anchors_run": self.anchors_run,
            "meter": None if self.meter is None else dict(self.meter),
        }

    @classmethod
    def from_json(cls, row: Mapping[str, Any]) -> TaskResult:
        """Rebuild a row from :meth:`to_json` output; raises ValueError for any other shape."""
        if not isinstance(row, Mapping) or row.get("schema") != RESULT_SCHEMA:
            found = row.get("schema") if isinstance(row, Mapping) else type(row).__name__
            raise ValueError(f"expected schema {RESULT_SCHEMA!r}, got {found!r}")
        values = {key: value for key, value in row.items() if key != "schema"}
        anchors = values.pop("anchors", None)
        names = sorted(str(kind) for kind in ANCHOR_ORDER)
        if not isinstance(anchors, dict) or sorted(anchors) != names:
            raise ValueError(f"'anchors' must map each of {names} to a record or null")
        records = []
        try:
            for name, data in anchors.items():
                if data is None:
                    continue
                if data.get("anchor") != name:
                    raise ValueError(
                        f"the record under {name!r} is a {data.get('anchor')!r} record")
                records.append(AnchorRecord(**data))
            return cls(**values, anchors=tuple(records))
        except (TypeError, KeyError, AttributeError) as exc:
            raise ValueError(f"malformed result row: {exc!r}") from exc


def exit_code(rows: Iterable[TaskResult], *, refused: int = 0) -> ExitCode:
    """The process exit code of a run, highest applicable first (3 > 2 > 1 > 0).

    INFRA when any row is ``infra_error``; CONFIG when ``refused`` tasks were
    refused, or when there is no row at all (nothing was validated); NOT_VALIDATED
    when any row is not ``validated_strict`` or ``validated``; OK otherwise.
    """
    labels = [row.label for row in rows]
    if refused < 0:
        raise ValueError(f"refused must be a count, got {refused}")
    if TaskLabel.INFRA_ERROR in labels:
        return ExitCode.INFRA
    if refused or not labels:
        return ExitCode.CONFIG
    if any(label not in SUCCESS_LABELS for label in labels):
        return ExitCode.NOT_VALIDATED
    return ExitCode.OK


def write_report(
    results: Sequence[TaskResult],
    out_dir: Path,
    *,
    refused: Mapping[str, str] | None = None,
    task_dirs: Mapping[str, Path] | None = None,
) -> ExitCode:
    """Write ``results.jsonl`` and ``summary.md`` into ``out_dir`` and return the exit code.

    ``refused`` maps each task refused before generation to its reason.
    ``task_dirs`` maps tasks to the directory that receives their
    ``VERIFIER_REPORT.md`` (the written-back task); every key must have a row.
    """
    refused = dict(refused or {})
    task_dirs = dict(task_dirs or {})
    by_task = _by_task(results, refused)
    unknown = sorted(set(task_dirs) - set(by_task))
    if unknown:
        raise ValueError(f"report directories for tasks without a result row: {unknown[:5]}")
    out_dir = Path(out_dir)
    rows = [by_task[task] for task in sorted(by_task)]
    files = {out_dir / RESULTS_FILE: "".join(
        json.dumps(row.to_json(), ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"
        for row in rows)}
    files[out_dir / SUMMARY_FILE] = render_summary(rows, refused=refused)
    for task, directory in sorted(task_dirs.items()):
        files[Path(directory) / TASK_REPORT_FILE] = render_task_report(by_task[task])
    existing = sorted(str(path) for path in files if path.exists())
    if existing:
        raise ConfigError(f"report files already exist and are never overwritten: {existing[:5]}")
    out_dir.mkdir(parents=True, exist_ok=True)
    for path, text in files.items():
        with path.open("x", encoding="utf-8") as handle:
            handle.write(text)
    return exit_code(rows, refused=len(refused))


def read_results(path: Path) -> list[TaskResult]:
    """The rows of a ``results.jsonl``; raises ConfigError naming the first bad line."""
    rows = []
    for lineno, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(TaskResult.from_json(json.loads(line)))
        except ValueError as exc:
            raise ConfigError(f"{path}:{lineno}: {exc}") from exc
    return rows


def render_summary(
    results: Sequence[TaskResult], *, refused: Mapping[str, str] | None = None
) -> str:
    """The text of ``summary.md``; see the module docstring for what it states."""
    refused = dict(refused or {})
    rows = [row for _, row in sorted(_by_task(results, refused).items())]
    code = exit_code(rows, refused=len(refused))
    outcomes = Counter(row.label for row in rows)
    infra = outcomes[TaskLabel.INFRA_ERROR]
    denominator = sum(row.in_denominator for row in rows)
    validated = sum(row.label in SUCCESS_LABELS for row in rows)

    lines = ["# Run summary", ""]
    lines.append(f"{_plural(len(rows), 'task')} with a result row; "
                 f"{_plural(len(refused), 'task')} refused before generation "
                 f"(listed under Refused tasks, in no denominator). "
                 f"Exit code {int(code)} ({code.name}).")
    lines += ["", "## Labels", "",
              "Each task gets the first label in this table whose condition holds "
              "(label precedence, first match wins).", "",
              "| # | Label | Condition | Tasks | Share |", "|---:|---|---|---:|---:|"]
    for rank, label in enumerate(LABEL_PRECEDENCE, 1):
        count = outcomes[label]
        share = "not counted" if label is TaskLabel.INFRA_ERROR else _share(count, denominator)
        lines.append(f"| {rank} | `{label}` | {LABEL_CONDITIONS[label]} | {count} | {share} |")
    lines += [f"| | **total** | | {len(rows)} | |", "",
              f"Denominator: {denominator} = {_plural(len(rows), 'result row')} − {infra} "
              "`infra_error`.", "",
              f"Validated (`validated_strict` + `validated`): {_share(validated, denominator)}. "
              "`validated_2way` is reported but not counted as validated."]

    lines += ["", "## Tasks not validated", ""]
    failing = sorted((row for row in rows if row.label not in SUCCESS_LABELS),
                     key=lambda row: (LABEL_PRECEDENCE.index(row.label), row.task))
    if failing:
        lines += ["| Task | Label | null | oracle | swap | Detail |", "|---|---|---|---|---|---|"]
        lines += [f"| {_cell(row.task)} | `{row.label}` | "
                  + " | ".join(_verdict_cell(row.anchor(kind)) for kind in ANCHOR_ORDER)
                  + f" | {_cell(_detail(row))} |" for row in failing]
    else:
        lines.append("None.")

    infra_lines = []
    for row in rows:
        if row.label is TaskLabel.INFRA_ERROR:
            infra_lines.append(f"- {_cell(row.task)}: {_cell(_infra_detail(row))}")
        elif any(record.reason == _IMAGE_DRIFT_REASON for record in row.anchors):
            infra_lines.append(f"- {_cell(row.task)}: the environment image changed between "
                               "anchors (env_image_drift); the affected records are NO_VERDICT")
    lines += ["", "## Infrastructure errors", "", *(infra_lines or ["None."])]

    lines += ["", "## Undelivered tasks", ""]
    undelivered = [row for row in rows if not row.delivered]
    if undelivered:
        lines += ["| Task | Label | Probe | Attempts |", "|---|---|---|---:|"]
        lines += [f"| {_cell(row.task)} | `{row.label}` | {_cell(row.probe or 'none')} | "
                  f"{row.attempts} |" for row in undelivered]
    else:
        lines.append("None.")

    lines += ["", "## Refused tasks", ""]
    if refused:
        lines += ["| Task | Reason |", "|---|---|"]
        lines += [f"| {_cell(task)} | {_cell(reason)} |"
                  for task, reason in sorted(refused.items())]
    else:
        lines.append("None.")

    lines += ["", "## Tokens and rate limits", ""]
    lines += _usage_lines(rows)

    dropped = [row for row in rows if row.dropped_task_config]
    lines += ["", "## Task configuration not carried into generation", ""]
    if dropped:
        lines += ["| Task | Settings |", "|---|---|"]
        lines += [f"| {_cell(row.task)} | {_cell(_settings(row.dropped_task_config))} |"
                  for row in dropped]
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def render_task_report(result: TaskResult) -> str:
    """The text of one task's ``VERIFIER_REPORT.md``."""
    row = result
    lines = [f"# Verifier report: {row.task}", "",
             f"Label: `{row.label}` ({LABEL_CONDITIONS[row.label]}).", "",
             "| Field | Value |", "|---|---|",
             f"| Paradigm | `{row.paradigm}` |",
             f"| Profile | `{row.profile}` |",
             f"| Package identity (sha256) | {_code_or(row.identity_sha256, 'not recorded')} |",
             f"| Delivered | {'yes' if row.delivered else 'no'}; probe "
             f"{_code_or(row.probe, 'none')}; {_plural(row.attempts, 'attempt')} |",
             f"| Verifier (sha256) | {_code_or(row.verifier_sha256, 'none')} |",
             f"| Reference solution | {'present' if row.has_oracle else 'absent'} |",
             f"| Swap donor | {_swap(row)} |",
             f"| Tokens (A+B) | {_cell(_usage(row.usage))} |",
             f"| Metering proxy ledger | {_cell(_meter(row.meter))} |",
             f"| Rate limits (429) | {_rate_limits(row)} |"]
    if row.label is TaskLabel.INFRA_ERROR:
        lines.append(f"| Infrastructure error | {_cell(_infra_detail(row))} |")

    lines += ["", "## Anchors", "",
              "| Anchor | Setup | Expected | Verdict | Reason | Image | Duration |",
              "|---|---|---|---|---|---|---:|"]
    for kind in ANCHOR_ORDER:
        record = row.anchor(kind)
        head = f"| {kind} | {_ANCHOR_SETUP[kind]} | {EXPECTED_VERDICTS[kind]} |"
        if record is None:
            lines.append(f"{head} not run: {_not_run(row, kind)} | | | |")
        else:
            lines.append(f"{head} {record.verdict} | `{_cell(record.reason)}` | "
                         f"{_code_or(record.image_id, 'not recorded')} | "
                         f"{record.duration_s:.1f} s |")
    if row.anchors:
        raw = json.dumps({str(record.anchor): record.raw for record in row.anchors},
                         indent=2, sort_keys=True, ensure_ascii=False)
        fence = "`" * max(3, _longest_backtick_run(raw) + 1)
        lines += ["", "Raw anchor results:", "", f"{fence}json", raw, fence]

    lines += ["", "## How the label was decided", "",
              "Label precedence, first match wins: "
              + " → ".join(f"`{label}`" for label in LABEL_PRECEDENCE) + "."]
    if row.dropped_task_config:
        lines += ["", "## Task configuration not carried into generation", ""]
        lines += [f"- `{key}` = {_cell(json.dumps(value, ensure_ascii=False))}"
                  for key, value in sorted(row.dropped_task_config.items())]
    return "\n".join(lines) + "\n"


def _by_task(results: Iterable[TaskResult], refused: Mapping[str, str]) -> dict[str, TaskResult]:
    by_task: dict[str, TaskResult] = {}
    for row in results:
        if row.task in by_task:
            raise ValueError(f"more than one result row for task {row.task!r}")
        by_task[row.task] = row
    both = sorted(set(by_task) & set(refused))
    if both:
        raise ValueError(f"tasks both refused and with a result row: {both[:5]}")
    return by_task


def _record_json(record: AnchorRecord | None) -> dict[str, Any] | None:
    return None if record is None else record.to_dict()


def _count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _check_usage(task: str, usage: Mapping[str, Any]) -> None:
    if "unavailable" in usage:
        reason = usage["unavailable"]
        if len(usage) != 1 or not (isinstance(reason, str) and reason.strip()):
            raise ValueError(f"{task}: unavailable usage is exactly {{'unavailable': <reason>}}")
        return
    if not usage:
        raise ValueError(f"{task}: usage is empty; record {{'unavailable': <reason>}} instead")
    for name, value in usage.items():
        valid = (isinstance(value, (int, float)) and not isinstance(value, bool)
                 and math.isfinite(value) and value >= 0)
        if not (isinstance(name, str) and valid):
            raise ValueError(f"{task}: usage {name!r} must be a non-negative number, got {value!r}")


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _share(count: int, denominator: int) -> str:
    if not denominator:
        return f"{count}/0"
    return f"{count}/{denominator} ({100 * count / denominator:.1f} %)"


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")


def _code_or(value: str | None, absent: str) -> str:
    return absent if value is None else f"`{_cell(value)}`"


def _verdict_cell(record: AnchorRecord | None) -> str:
    return "—" if record is None else f"{record.verdict} ({_cell(record.reason)})"


def _infra_detail(row: TaskResult) -> str:
    parts = [] if row.infra_error is None else [row.infra_error]
    parts += [f"{record.anchor} anchor: {record.infra}" for record in row.anchors if record.infra]
    return "; ".join(parts)


def _detail(row: TaskResult) -> str:
    if row.label is TaskLabel.INFRA_ERROR:
        return _infra_detail(row)
    if not row.delivered:
        return f"probe {row.probe or 'none'}, {_plural(row.attempts, 'attempt')}"
    parts = [] if row.has_oracle else ["no reference solution"]
    if row.swap_donor is not None:
        parts.append(f"swap donor {row.swap_donor}" + (" (cross-type)" if row.swap_cross_type
                                                       else ""))
    return "; ".join(parts)


def _not_run(row: TaskResult, kind: AnchorKind) -> str:
    if not row.delivered:
        return "no verifier delivered"
    if not row.anchors_run:
        return "anchors not run (no --validate)"
    if row.label is TaskLabel.INFRA_ERROR:
        return "infrastructure error"
    if kind is AnchorKind.ORACLE and not row.has_oracle:
        return "no reference solution"
    if kind is AnchorKind.SWAP and row.swap_donor is None:
        return "no swap could be constructed"
    return "not recorded"


def _swap(row: TaskResult) -> str:
    if row.swap_donor is None:
        return "none could be constructed"
    kind = "cross-type" if row.swap_cross_type else "same type"
    return f"`{_cell(row.swap_donor)}` ({kind})"


def _usage(usage: Mapping[str, Any]) -> str:
    if "unavailable" in usage:
        return f"unavailable ({usage['unavailable']})"
    return ", ".join(f"{name} {value}" for name, value in sorted(usage.items()))


def _meter(meter: Mapping[str, int] | None) -> str:
    if meter is None:
        return "not metered"
    return ", ".join(f"{name} {value}" for name, value in sorted(meter.items()))


def _rate_limits(row: TaskResult) -> str:
    absorbed = ("not measured" if row.absorbed_429 is None
                else f"{row.absorbed_429} absorbed by the metering proxy")
    contaminated = {None: "contamination not measured", True: "a 429 reached the agent",
                    False: "none reached the agent"}[row.contaminated_429]
    return f"{absorbed}; {contaminated}"


def _usage_lines(rows: Sequence[TaskResult]) -> list[str]:
    available = [row for row in rows if "unavailable" not in row.usage]
    unavailable = [row for row in rows if "unavailable" in row.usage]
    totals: Counter[str] = Counter()
    counts: Counter[str] = Counter()
    for row in available:
        for name, value in row.usage.items():
            totals[name] += value
            counts[name] += 1
    lines = []
    if totals:
        lines.append("Tokens (A+B), summed: " + ", ".join(
            f"{name} {totals[name]} over {_plural(counts[name], 'task')}"
            for name in sorted(totals)) + ".")
    lines.append(f"Usage unavailable for {_plural(len(unavailable), 'task')}"
                 + (":" if unavailable else "."))
    lines += [f"- {_cell(row.task)}: {_cell(str(row.usage['unavailable']))}"
              for row in unavailable]
    ledger: Counter[str] = Counter()
    for row in rows:
        ledger.update(row.meter or {})
    ledger_tasks = sum(row.meter is not None for row in rows)
    if ledger_tasks:
        lines.append(f"Metering proxy ledger over {_plural(ledger_tasks, 'task')}: "
                     + ", ".join(f"{name} {ledger[name]}" for name in sorted(ledger)) + ".")
    metered = [row for row in rows if row.absorbed_429 is not None]
    lines.append(f"429 absorbed by the metering proxy: {sum(r.absorbed_429 or 0 for r in metered)} "
                 f"over {_plural(len(metered), 'metered task')}; "
                 f"not measured for {_plural(len(rows) - len(metered), 'task')}.")
    contaminated = [row for row in rows if row.contaminated_429]
    unknown = sum(row.contaminated_429 is None for row in rows)
    lines.append(f"429 reached the agent in {_plural(len(contaminated), 'task')}"
                 + (": " + ", ".join(_cell(row.task) for row in contaminated) if contaminated
                    else "")
                 + f"; not measured for {_plural(unknown, 'task')}.")
    return lines


def _settings(config: Mapping[str, Any]) -> str:
    return "; ".join(f"{key} = {json.dumps(value, ensure_ascii=False)}"
                     for key, value in sorted(config.items()))


def _longest_backtick_run(text: str) -> int:
    return max((len(run) for run in re.findall(r"`+", text)), default=0)
