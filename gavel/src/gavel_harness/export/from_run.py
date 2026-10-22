"""Read the delivered verifiers of a finished run of the upstream one-command driver.

The upstream driver leaves one directory per run, written in this order:

* ``tasks/<id>``: a symlink to every input task directory, refused ones included;
* ``refused.json``: ``{task id: reason}`` for the tasks outside its paradigm;
* ``tasks.txt``: the in-paradigm task ids, one per line;
* ``manifest.json``: the generation run's manifest, copied in only after the
  whole run finished: ``{task id: {probe, shipped, verifier_path, attempts, ...}}``;
  a task without ``verifier_path`` delivered no verifier;
* ``results.jsonl``: the driver's own null/oracle replay. It is not read: its
  labels count exit 127 and failed copies into the container as FAIL.

The run directory is only read. Every inconsistency between these files is a
:class:`~gavel_harness.errors.ConfigError`; nothing is skipped or repaired.

The run recorded every attempt, infrastructure failures included, and counted
a task without a verifier as undelivered whatever stopped it.
:func:`attempt_failure` reads the attempt that decided such a task and names
the infrastructure failure, if any, by the attempt's structured fields and the
type name of its recorded exception (never by its message):

* no trial collected, or a job that did not complete (``collected`` or
  ``job_completed`` false), or a cancelled trial (``CancelledError``):
  ``harbor_internal``;
* a rate-limit exception (:data:`RATE_LIMIT_EXCEPTIONS`): ``rate_limited``;
* an exception that says the model endpoint failed
  (:data:`ENDPOINT_EXCEPTIONS`): ``endpoint_unavailable``;
* any other exception recorded before the agent started (``usage`` null:
  Harbor creates the agent result when the agent starts): ``env_build_failed``.

Any other undelivered task is a capability outcome. :func:`rate_limited` says
whether rate limiting reached any attempt of a task.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Any

from ..errors import ConfigError, InfraCategory, InfraError
from ..method.identity import sha256_file

MANIFEST_FILE = "manifest.json"
TASKS_FILE = "tasks.txt"
REFUSED_FILE = "refused.json"
"""``{task id: refusal reason}``; this harness writes its own run's refusals under the
same name."""
TASKS_DIR = "tasks"
RATE_LIMIT_EXCEPTIONS = frozenset({"ApiRateLimitError", "ApiUsageLimitError", "RateLimitError"})
"""Exception types an attempt records when rate limiting or a usage quota stopped its agent:
Harbor's installed-agent errors and LiteLLM's."""
ENDPOINT_EXCEPTIONS = frozenset({
    "ApiInternalServerError", "ApiOverloadedError", "ApiConnectionClosedError",
    "ApiResponseStalledError", "NetworkConnectionError", "InternalServerError",
})
"""Exception types an attempt records when the model endpoint failed: Harbor's
installed-agent errors and LiteLLM's."""


@dataclass(frozen=True)
class DeliveredVerifier:
    """One in-paradigm task of an upstream run and the verifier it delivered."""

    task_id: str
    source_task: Path
    """The original task directory: the resolved target of ``tasks/<id>``."""
    verifier_sh: Path | None
    """The delivered verifier script; None when the task delivered none."""
    probe: str | None
    """Probe outcome of the shipped attempt, as the run recorded it."""
    attempts: list[dict[str, Any]]
    """The run manifest's attempt rows for this task, verbatim (at least one)."""


@dataclass(frozen=True)
class _Layout:
    tasks: list[str]
    refused: dict[str, str]
    sources: dict[str, Path]


def load_run(run_dir: Path) -> list[DeliveredVerifier]:
    """The tasks of the upstream run in ``run_dir``, in ``tasks.txt`` order.

    Raises ConfigError when the run is unfinished (no ``manifest.json``), when
    a delivered ``verifier_path`` is not an existing file or no longer holds the
    bytes the shipped attempt recorded (:func:`_check_recorded_sha`), and when
    the run's files disagree: the manifest must hold exactly the ``tasks.txt`` ids, each
    row with a non-empty ``attempts`` list; ``tasks/`` must link exactly the
    ``tasks.txt`` and ``refused.json`` ids, the in-paradigm ones to existing
    directories.
    """
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        raise ConfigError(f"{run_dir} is not a directory")
    manifest_path = run_dir / MANIFEST_FILE
    if not manifest_path.is_file():
        raise ConfigError(
            f"{run_dir} has no {MANIFEST_FILE}: the run is unfinished (the upstream driver "
            "writes it only after the whole generation run finished)"
        )
    layout = _read_layout(run_dir)
    manifest = _read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ConfigError(f"{manifest_path}: expected a JSON object keyed by task id")
    missing = sorted(set(layout.tasks) - set(manifest))
    extra = sorted(set(manifest) - set(layout.tasks))
    if missing or extra:
        raise ConfigError(
            f"{manifest_path} does not match {TASKS_FILE}: "
            f"missing {missing[:5]} ({len(missing)}), unexpected {extra[:5]} ({len(extra)})"
        )
    return [_delivered(task_id, manifest[task_id], layout.sources[task_id], manifest_path)
            for task_id in layout.tasks]


def load_refusals(run_dir: Path) -> dict[str, str]:
    """``{task id: reason}`` of the tasks the upstream run refused, from ``refused.json``.

    Checks the same ``tasks.txt``/``refused.json``/``tasks/`` consistency as
    :func:`load_run`; a refusal list is known before generation, so an
    unfinished run has one too.
    """
    return dict(_read_layout(Path(run_dir)).refused)


def attempt_failure(attempts: Sequence[Mapping[str, Any]]) -> InfraError | None:
    """The infrastructure failure of the attempt that decided a task, or None.

    That attempt is the one marked ``shipped``, else the last. The rules are in
    the module docstring; a field the attempt does not record never counts as
    a failure.
    """
    if not attempts:
        raise ConfigError("a task has at least one attempt")
    attempt = next((row for row in attempts if row.get("shipped") is True), attempts[-1])
    job = attempt.get("job_name")
    where = f"attempt {attempt.get('attempt')}" + (f" (job {job})" if job else "")
    info = attempt.get("exception_info")
    info = info if isinstance(info, Mapping) else {}
    exception = info.get("exception_type")
    lines = str(info.get("exception_message") or "").strip().splitlines()
    raised = f"{exception}: {lines[0][:300]}" if lines else str(exception)
    if attempt.get("collected") is False:
        return InfraError(InfraCategory.HARBOR_INTERNAL, f"{where}: no trial was collected")
    if attempt.get("job_completed") is False:
        return InfraError(InfraCategory.HARBOR_INTERNAL,
                          f"{where}: the job did not complete (cancelled or failed outside "
                          "its trials)")
    if exception is None:
        return None
    if exception == "CancelledError":
        return InfraError(InfraCategory.HARBOR_INTERNAL, f"{where}: the trial was cancelled")
    if exception in RATE_LIMIT_EXCEPTIONS:
        return InfraError(InfraCategory.RATE_LIMITED, f"{where}: {raised}")
    if exception in ENDPOINT_EXCEPTIONS:
        return InfraError(InfraCategory.ENDPOINT_UNAVAILABLE, f"{where}: {raised}")
    if attempt.get("usage") is None:
        return InfraError(InfraCategory.ENV_BUILD_FAILED,
                          f"{where}: failed before its agent started: {raised}")
    return None


def rate_limited(attempts: Sequence[Mapping[str, Any]]) -> bool:
    """Whether any attempt recorded a rate-limit exception (:data:`RATE_LIMIT_EXCEPTIONS`).

    False only says that no attempt stopped on rate limiting: the original
    harness did not record 429 answers its agents' clients retried.
    """
    return any(isinstance(row.get("exception_info"), Mapping)
               and row["exception_info"].get("exception_type") in RATE_LIMIT_EXCEPTIONS
               for row in attempts)


def _read_layout(run_dir: Path) -> _Layout:
    if not run_dir.is_dir():
        raise ConfigError(f"{run_dir} is not a directory")
    tasks_path = run_dir / TASKS_FILE
    if not tasks_path.is_file():
        raise ConfigError(f"{run_dir} has no {TASKS_FILE}; not a run of the upstream driver")
    tasks = [line.strip() for line in tasks_path.read_text(encoding="utf-8").splitlines()
             if line.strip()]
    if not tasks:
        raise ConfigError(f"{tasks_path} lists no task")
    duplicates = sorted(task for task, count in Counter(tasks).items() if count > 1)
    if duplicates:
        raise ConfigError(f"{tasks_path} lists tasks more than once: {duplicates[:5]}")
    for task_id in tasks:
        _check_task_id(task_id, tasks_path)

    refused_path = run_dir / REFUSED_FILE
    if not refused_path.is_file():
        raise ConfigError(f"{run_dir} has no {REFUSED_FILE}; not a run of the upstream driver")
    refused = _read_json(refused_path)
    if not isinstance(refused, dict) or not all(
            isinstance(reason, str) for reason in refused.values()):
        raise ConfigError(f"{refused_path}: expected a JSON object of task id -> reason")
    for task_id in refused:
        _check_task_id(task_id, refused_path)
    both = sorted(set(tasks) & set(refused))
    if both:
        raise ConfigError(f"tasks both in {TASKS_FILE} and refused: {both[:5]}")

    links = run_dir / TASKS_DIR
    if not links.is_dir():
        raise ConfigError(f"{run_dir} has no {TASKS_DIR}/ directory")
    linked = {entry.name for entry in links.iterdir()}
    expected = set(tasks) | set(refused)
    if linked != expected:
        raise ConfigError(
            f"{links} does not link exactly the listed and refused tasks: "
            f"unlinked {sorted(expected - linked)[:5]}, unlisted {sorted(linked - expected)[:5]}"
        )
    sources: dict[str, Path] = {}
    for task_id in tasks:
        source = (links / task_id).resolve()
        if not source.is_dir():
            raise ConfigError(f"{links / task_id} does not lead to a task directory ({source})")
        sources[task_id] = source
    return _Layout(tasks=tasks, refused=dict(refused), sources=sources)


def _delivered(task_id: str, row: object, source: Path, manifest_path: Path) -> DeliveredVerifier:
    where = f"{manifest_path} [{task_id}]"
    if not isinstance(row, dict):
        raise ConfigError(f"{where}: expected a JSON object")
    attempts = row.get("attempts")
    if (not isinstance(attempts, list) or not attempts
            or not all(isinstance(attempt, dict) for attempt in attempts)):
        raise ConfigError(f"{where}: 'attempts' must be a non-empty list of objects")
    probe = row.get("probe")
    if probe is not None and not isinstance(probe, str):
        raise ConfigError(f"{where}: 'probe' must be a string or null, got {probe!r}")
    raw_path = row.get("verifier_path")
    verifier: Path | None = None
    if raw_path:
        if not isinstance(raw_path, str) or not Path(raw_path).is_absolute():
            raise ConfigError(
                f"{where}: 'verifier_path' must be an absolute path, got {raw_path!r}")
        verifier = Path(raw_path)
        if not verifier.is_file():
            raise ConfigError(f"{where}: the delivered verifier {verifier} does not exist")
        _check_recorded_sha(verifier, attempts, where)
    return DeliveredVerifier(task_id=task_id, source_task=source, verifier_sh=verifier,
                             probe=probe, attempts=attempts)


def _check_recorded_sha(verifier: Path, attempts: Sequence[Mapping[str, Any]],
                        where: str) -> None:
    """ConfigError unless ``verifier`` has the sha256 the shipped attempt recorded for it.

    The shipped attempt's ``artifact_files`` lists every artifact relative to
    its ``artifact_dir``. An attempt that recorded no artifact list cannot be
    checked; one that did must list the verifier with its current bytes, so a
    file changed after the run (a rerun into the same trial directory, a
    regrade, an edit) is never judged as the generated verifier.
    """
    shipped = [row for row in attempts if row.get("shipped") is True]
    if len(shipped) != 1:
        raise ConfigError(f"{where}: a delivered task needs exactly one attempt marked "
                          f"shipped, found {len(shipped)}")
    files = shipped[0].get("artifact_files")
    if not files:
        return
    artifact_dir = shipped[0].get("artifact_dir")
    if not isinstance(artifact_dir, str) or not verifier.is_relative_to(artifact_dir):
        raise ConfigError(f"{where}: the delivered verifier {verifier} is not under the shipped "
                          f"attempt's artifact_dir {artifact_dir!r}")
    rel = verifier.relative_to(artifact_dir).as_posix()
    recorded = [row.get("sha256") for row in files
                if isinstance(row, Mapping) and row.get("path") == rel]
    if len(recorded) != 1:
        raise ConfigError(f"{where}: the shipped attempt's artifact_files does not list {rel}")
    actual = sha256_file(verifier)
    if recorded[0] != actual:
        raise ConfigError(f"{where}: {verifier} has sha256 {actual}, not the {recorded[0]} the "
                          "run recorded; the file changed after generation")


def _check_task_id(task_id: str, where: Path) -> None:
    if not task_id or PurePath(task_id).name != task_id or task_id in (".", ".."):
        raise ConfigError(f"{where}: {task_id!r} is not a single path component")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path} is not valid JSON: {exc}") from exc
