"""The support matrix: one row per task sampled from a Harbor registry (``gavel-harness matrix``).

Files in the matrix output directory:

* ``matrix.jsonl``: one :class:`MatrixRow` per line, appended as each task
  finishes (:func:`append_row`), read back by :func:`read_rows`.
* ``SUPPORT_MATRIX.md``: the rendering of those rows (:func:`write_matrix`),
  regenerated from the rows on every write.

A row carries the task's family and pin, the paradigm it ran under or the
reason it was refused, its label and anchor records, the package identity
hash, the model, the executor and the harness and Harbor versions. Its outcome
is read from structured fields only, in this order: an infrastructure category
(``no_result``: the task produced no result, e.g. the fetch, the docker host or
the task's own environment build failed), a refusal reason, the label. Error
messages are kept for people (``no_result_detail``) and never parsed.

Shares in the summary have the same denominator: every row except rows without
a result, which say nothing about the task's support. Refused rows count, since
a refusal is a support outcome.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import PARADIGMS
from ..errors import ConfigError, InfraCategory, InfraError, RefusalError, RefusalReason
from ..intake.registry_fetch import FamilySample, Registry, RegistryTask
from ..verify.verdict import SUCCESS_LABELS, AnchorKind, AnchorRecord, TaskLabel, Verdict
from .report import LABEL_PRECEDENCE

ROWS_FILE = "matrix.jsonl"
MATRIX_FILE = "SUPPORT_MATRIX.md"
ROW_SCHEMA = "veritas-matrix-row/1"

_ANCHORS = (AnchorKind.NULL, AnchorKind.ORACLE, AnchorKind.SWAP)
_DETAIL_CHARS = 120


@dataclass(frozen=True)
class RunIdentity:
    """What produced a row: model, executor, harness and Harbor versions.

    ``harness_commit`` and ``harness_dirty`` come from the run's provenance.
    ``harbor_commit`` is the commit the ``harbor_pin`` doctor check verified, or
    the VCS commit provenance recorded; None when neither is known.
    """

    model: str
    executor: str
    harness_commit: str | None
    harness_dirty: bool
    harbor_version: str
    harbor_commit: str | None


@dataclass(frozen=True)
class MatrixRow:
    """One sampled task. Build rows with :meth:`refused`, :meth:`infra` or :meth:`result`.

    Exactly one outcome applies: ``refusal`` (no paradigm, label, records or
    identity), ``no_result`` (an infrastructure category, with
    ``no_result_detail``; no label), or a result (``paradigm``, ``label`` and
    ``identity_sha256`` set).
    ``records`` holds at most one record per anchor, all of one task.
    """

    task: RegistryTask
    run: RunIdentity
    paradigm: str | None = None
    refusal: RefusalReason | None = None
    label: TaskLabel | None = None
    records: tuple[AnchorRecord, ...] = ()
    identity_sha256: str | None = None
    no_result: InfraCategory | None = None
    no_result_detail: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", tuple(self.records))
        where = f"matrix row {self.task.family}/{self.task.name}"
        if self.paradigm is not None and self.paradigm not in PARADIGMS:
            raise ConfigError(f"{where}: unknown paradigm {self.paradigm!r}")
        kinds = [record.anchor for record in self.records]
        if len(set(kinds)) != len(kinds):
            raise ConfigError(f"{where}: more than one record for an anchor")
        if len({record.task for record in self.records}) > 1:
            raise ConfigError(f"{where}: records of several tasks")
        if self.refusal is not None:
            if (self.no_result is not None or self.paradigm is not None or self.label is not None
                    or self.records or self.identity_sha256 is not None
                    or self.no_result_detail is not None):
                raise ConfigError(f"{where}: a refused task has no other outcome")
        elif self.no_result is not None:
            if self.label is not None:
                raise ConfigError(f"{where}: a task without a result has no label")
            if not self.no_result_detail:
                raise ConfigError(f"{where}: no_result needs no_result_detail")
        else:
            if self.paradigm is None or self.label is None or self.identity_sha256 is None:
                raise ConfigError(f"{where}: a result needs paradigm, label and identity_sha256")
            if self.label == TaskLabel.INFRA_ERROR:
                raise ConfigError(f"{where}: an infra_error label is a row without a result")
            if self.no_result_detail is not None:
                raise ConfigError(f"{where}: no_result_detail belongs to a row without a result")

    @classmethod
    def refused(cls, task: RegistryTask, run: RunIdentity, error: RefusalError) -> MatrixRow:
        """The row of a task refused before packaging."""
        return cls(task=task, run=run, refusal=error.reason)

    @classmethod
    def infra(
        cls,
        task: RegistryTask,
        run: RunIdentity,
        error: InfraError,
        *,
        paradigm: str | None = None,
        identity_sha256: str | None = None,
        records: Sequence[AnchorRecord] = (),
    ) -> MatrixRow:
        """The row of a task an infrastructure failure left without a result.

        ``paradigm``, ``identity_sha256`` and ``records`` keep what the task
        reached before the failure.
        """
        detail = str(error).removeprefix(f"[{error.category}] ")
        return cls(task=task, run=run, paradigm=paradigm, identity_sha256=identity_sha256,
                   records=tuple(records), no_result=error.category, no_result_detail=detail)

    @classmethod
    def result(
        cls,
        task: RegistryTask,
        run: RunIdentity,
        *,
        paradigm: str,
        identity_sha256: str,
        label: TaskLabel,
        records: Sequence[AnchorRecord],
    ) -> MatrixRow:
        """The row of a task that went through generation (and the anchors, when delivered).

        ``label`` is :func:`~gavel_harness.verify.verdict.label_task` of
        ``records``. An ``infra_error`` label becomes a row without a result
        whose category is the first record's ``raw["infra"]``; ConfigError
        when no record carries one or it is not an infrastructure category.
        """
        if label != TaskLabel.INFRA_ERROR:
            return cls(task=task, run=run, paradigm=paradigm, identity_sha256=identity_sha256,
                       label=label, records=tuple(records))
        failed = next((record for record in records if record.infra), None)
        value = None if failed is None else failed.infra
        if failed is None or value is None:
            raise ConfigError(
                f"{task.family}/{task.name}: an infra_error label needs a record carrying "
                "raw['infra'], or a row built with MatrixRow.infra"
            )
        try:
            category = InfraCategory(value)
        except ValueError as exc:
            raise ConfigError(f"{task.family}/{task.name}: {value!r} is not an "
                              "infrastructure category") from exc
        return cls(task=task, run=run, paradigm=paradigm, identity_sha256=identity_sha256,
                   records=tuple(records), no_result=category,
                   no_result_detail=f"{failed.anchor} anchor: {failed.reason}")

    @property
    def key(self) -> tuple[str, str, str]:
        """``(family, task name, task path)``: unique within one matrix."""
        return (self.task.family, self.task.name, self.task.path)

    @property
    def outcome(self) -> str:
        """``no_result:<category>``, ``refused:<reason>`` or the label."""
        if self.no_result is not None:
            return f"no_result:{self.no_result.value}"
        if self.refusal is not None:
            return f"refused:{self.refusal.value}"
        assert self.label is not None
        return self.label.value

    @property
    def counted(self) -> bool:
        """Whether the row is in the denominator of the summary shares."""
        return self.no_result is None

    def anchor(self, kind: AnchorKind) -> AnchorRecord | None:
        """The record of anchor ``kind``, or None when it was not run."""
        return next((record for record in self.records if record.anchor == kind), None)

    def to_json(self) -> dict[str, Any]:
        """The row as one JSON object (``matrix.jsonl`` line)."""
        task, run = self.task, self.run
        return {
            "schema": ROW_SCHEMA,
            "family": task.family,
            "version": task.version,
            "task": task.name,
            "git_url": task.git_url,
            "commit": task.commit,
            "path": task.path,
            "pinned_by": task.pinned_by,
            "outcome": self.outcome,
            "paradigm": self.paradigm,
            "refusal": None if self.refusal is None else self.refusal.value,
            "label": None if self.label is None else self.label.value,
            "anchors": {kind.value: _verdict(self.anchor(kind)) for kind in _ANCHORS},
            "records": [record.to_dict() for record in self.records],
            "identity_sha256": self.identity_sha256,
            "no_result": None if self.no_result is None else self.no_result.value,
            "no_result_detail": self.no_result_detail,
            "model": run.model,
            "executor": run.executor,
            "harness_commit": run.harness_commit,
            "harness_dirty": run.harness_dirty,
            "harbor_version": run.harbor_version,
            "harbor_commit": run.harbor_commit,
        }

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> MatrixRow:
        """Rebuild a row from :meth:`to_json` output; ConfigError when it is not one."""
        if data.get("schema") != ROW_SCHEMA:
            raise ConfigError(f"expected a {ROW_SCHEMA} row, got schema {data.get('schema')!r}")
        try:
            row = cls(
                task=RegistryTask(family=data["family"], version=data["version"],
                                  name=data["task"], git_url=data["git_url"],
                                  commit=data["commit"], path=data["path"],
                                  pinned_by=data["pinned_by"]),
                run=RunIdentity(model=data["model"], executor=data["executor"],
                                harness_commit=data["harness_commit"],
                                harness_dirty=data["harness_dirty"],
                                harbor_version=data["harbor_version"],
                                harbor_commit=data["harbor_commit"]),
                paradigm=data["paradigm"],
                refusal=_optional(RefusalReason, data["refusal"]),
                label=_optional(TaskLabel, data["label"]),
                records=tuple(AnchorRecord(**record) for record in data["records"]),
                identity_sha256=data["identity_sha256"],
                no_result=_optional(InfraCategory, data["no_result"]),
                no_result_detail=data["no_result_detail"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ConfigError(f"malformed matrix row: {type(exc).__name__}: {exc}") from exc
        if row.to_json() != dict(data):
            raise ConfigError(f"matrix row {row.task.family}/{row.task.name} is inconsistent "
                              "with its own fields")
        return row


def append_row(out_dir: Path, row: MatrixRow) -> None:
    """Append ``row`` to ``<out_dir>/matrix.jsonl``; ConfigError when its key is already there."""
    if any(existing.key == row.key for existing in read_rows(out_dir)):
        raise ConfigError(f"{row.task.family}/{row.task.name} already has a row in "
                          f"{out_dir / ROWS_FILE}")
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / ROWS_FILE).open("a", encoding="utf-8") as sink:
        sink.write(json.dumps(row.to_json(), ensure_ascii=False, sort_keys=True) + "\n")
        sink.flush()
        os.fsync(sink.fileno())


def read_rows(out_dir: Path) -> list[MatrixRow]:
    """The rows of ``<out_dir>/matrix.jsonl`` in file order; none when the file does not exist.

    ConfigError for a line that is not a row and for two rows with one key.
    """
    path = out_dir / ROWS_FILE
    if not path.exists():
        return []
    rows: list[MatrixRow] = []
    seen: set[tuple[str, str, str]] = set()
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"{path}:{lineno}: not JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"{path}:{lineno}: not a JSON object")
        try:
            row = MatrixRow.from_json(data)
        except ConfigError as exc:
            raise ConfigError(f"{path}:{lineno}: {exc}") from exc
        if row.key in seen:
            raise ConfigError(
                f"{path}:{lineno}: a second row for {row.task.family}/{row.task.name}"
            )
        seen.add(row.key)
        rows.append(row)
    return rows


def write_matrix(
    out_dir: Path,
    *,
    registry: Registry,
    seed: int,
    samples: Sequence[FamilySample],
    rows: Sequence[MatrixRow],
) -> Path:
    """Write ``<out_dir>/SUPPORT_MATRIX.md`` from ``rows`` and return its path.

    ``samples`` are the family samples the rows were drawn from (all of them,
    including families that yielded fewer tasks than requested or none).
    ConfigError when a row is not among the sampled tasks.
    """
    text = render_matrix(registry=registry, seed=seed, samples=samples, rows=rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / MATRIX_FILE
    tmp = target.with_name(f".{target.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)
    return target


def render_matrix(
    *,
    registry: Registry,
    seed: int,
    samples: Sequence[FamilySample],
    rows: Sequence[MatrixRow],
) -> str:
    """The Markdown text of ``SUPPORT_MATRIX.md``; see :func:`write_matrix`.

    ConfigError when a row's task is not one of the sampled tasks, field for field.
    """
    sampled = {(task.family, task.name, task.path): task
               for item in samples for task in item.tasks}
    stray = [row for row in rows if sampled.get(row.key) != row.task]
    if stray:
        raise ConfigError(f"{len(stray)} row(s) are not among the sampled tasks (or name "
                          f"another version or commit), e.g. "
                          f"{stray[0].task.family}/{stray[0].task.name}")
    ordered = sorted(rows, key=lambda row: row.key)
    requested = sorted({item.requested for item in samples})
    lines = [
        "# Support matrix",
        "",
        f"Registry `{registry.source}` (sha256 `{registry.sha256[:12]}`), seed {seed}, "
        f"{'/'.join(map(str, requested)) or 0} task(s) requested per family; "
        f"{len(rows)} of {len(sampled)} sampled task(s) have a row.",
        "",
        "## Summary",
        "",
        *_summary(ordered),
        "",
        "## Tasks",
        "",
        "| family | task | paradigm or refusal | label | null | oracle | swap | no result "
        "| model | executor | gavel-harness | harbor | identity |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        *(_task_line(row) for row in ordered),
    ]
    short = [item for item in samples if item.short]
    if short:
        lines += [
            "",
            "## Families with fewer tasks than requested",
            "",
            "| family | sampled | requested | fetchable | not fetchable |",
            "|---|---:|---:|---:|---|",
        ]
        for item in sorted(short, key=lambda item: item.family.name):
            excluded = ", ".join(f"{reason} {count}"
                                 for reason, count in item.family.excluded.items()) or "-"
            lines.append(f"| {_cell(item.family.name)}@{_cell(item.family.version)} "
                         f"| {len(item.tasks)} | {item.requested} | {len(item.family.tasks)} "
                         f"| {excluded} |")
    missing = sorted(set(sampled) - {row.key for row in rows})
    if missing:
        lines += ["", "## Sampled tasks without a row", ""]
        lines += [f"- {family}/{name} (`{path}`)" for family, name, path in missing]
    return "\n".join(lines) + "\n"


def _summary(rows: Sequence[MatrixRow]) -> list[str]:
    counted = [row for row in rows if row.counted]
    denominator = len(counted)
    counts = Counter(row.outcome for row in rows)
    order = ([label.value for label in TaskLabel]
             + sorted(key for key in counts if key.startswith("refused:"))
             + sorted(key for key in counts if key.startswith("no_result:")))
    validated = sum(1 for row in counted if row.label in SUCCESS_LABELS)
    lines = [
        f"Validated ({' or '.join(sorted(label.value for label in SUCCESS_LABELS))}): "
        f"**{validated}/{denominator}**.",
        "",
        f"Denominator: {denominator} row(s); rows without a result (infrastructure failure) "
        "are listed but not counted.",
        "",
        "| outcome | tasks | share |",
        "|---|---:|---:|",
    ]
    for key in order:
        if counts[key]:
            share = "not counted" if key.startswith("no_result:") \
                else f"{counts[key]}/{denominator}"
            lines.append(f"| {key} | {counts[key]} | {share} |")
    lines += [
        "",
        "Labels are assigned by the first matching rule: "
        + " → ".join(label.value for label in LABEL_PRECEDENCE)
        + ". A `—` anchor was not run (not constructible, or the task stopped earlier).",
    ]
    return lines


def _task_line(row: MatrixRow) -> str:
    task, run = row.task, row.run
    paradigm = row.paradigm or ""
    if row.refusal is not None:
        paradigm = f"refused: {row.refusal.value}"
    no_result = "" if row.no_result is None else \
        f"{row.no_result.value}: {_short(row.no_result_detail or '')}"
    harness = (run.harness_commit[:12] if run.harness_commit else "no commit") \
        + ("+dirty" if run.harness_dirty else "")
    harbor = run.harbor_version + (f" @{run.harbor_commit[:7]}" if run.harbor_commit
                                   else " (commit not recorded)")
    cells = [
        f"{task.family}@{task.version}", task.name, paradigm,
        "" if row.label is None else row.label.value,
        *(_verdict_cell(row.anchor(kind)) for kind in _ANCHORS),
        no_result, run.model, run.executor, harness, harbor,
        (row.identity_sha256 or "")[:12],
    ]
    return "| " + " | ".join(_cell(cell) for cell in cells) + " |"


def _verdict(record: AnchorRecord | None) -> str | None:
    return None if record is None else record.verdict.value


def _verdict_cell(record: AnchorRecord | None) -> str:
    if record is None:
        return "—"
    if record.verdict == Verdict.NO_VERDICT:
        return f"NO_VERDICT ({record.reason})"
    return record.verdict.value


def _optional[E: (RefusalReason, TaskLabel, InfraCategory)](kind: type[E], value: Any) -> E | None:
    return None if value is None else kind(value)


def _short(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= _DETAIL_CHARS else text[:_DETAIL_CHARS] + "..."


def _cell(text: str) -> str:
    return text.replace("\\", "\\\\").replace("|", "\\|")
