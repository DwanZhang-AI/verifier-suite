"""Generation sessions: attempt A, probe classification, one feedback retry B, merge.

Port of ``generate_roll`` and its helpers in the upstream harness's
``judge/core/session.py``, on Harbor's own docker environment and Job (see
:mod:`gavel_harness.run.job`). For the packages given to :func:`generate`:

1. Each package is checked against its sealed identity
   (:func:`~gavel_harness.method.identity.validate_materialized`).
2. Attempt A: every package is copied into a private input snapshot
   ``<jobs_dir>/input_snapshots/<session>/0/<package>`` and one Harbor job runs
   all snapshots. Each trial's probe output is classified with
   :func:`gavel_harness.method.probe_core.classify` under its paradigm's
   probe spec.
3. Attempt B: every task whose A outcome is CRASH or NODIRECTION gets one more
   trial, from a snapshot of its A snapshot (never the live package) whose
   ``instruction.md`` ends with the feedback marker and the spec's feedback
   text, ``{diag}`` replaced by the last 1500 characters of A's probe output.
   All B trials run in one job.
4. :func:`gavel_harness.method.probe_core.merge` decides what ships: B only
   when its own probe is OK, otherwise A; probing can upgrade a verifier,
   never lose one.

Every counted attempt is a record with the keys of the upstream manifest's
``attempts`` rows (:data:`ATTEMPT_KEYS`); a task's records are written to
``<snapshot root>/<package>.attempts.json`` once its delivery is decided.

With an exec cap, every agent command that sets no time limit of its own ends
after that many seconds with ExecCapError
(:mod:`gavel_harness.run.executors.tagged`), as the upstream environments'
transport cap (3900 s unless ``VERITAS_EXEC_TIMEOUT`` said otherwise) ended
it: the trial records the exception and Harbor collects its artifacts without
running the probe, so the attempt's outcome is SKIP (no retry B) and the
verifier written so far ships when it is non-empty.

A counted attempt can take more than one job. A trial is discarded and its
attempt rerun in a fresh job from the same frozen input when:

* rate limiting reached it (metered runs): the metering proxy passed a 429 to
  its agent (``passed_429``), the agent's client gave up on a request while
  the proxy was waiting out 429 answers (``abandoned_429``), or the agent ran
  out of its budget (``AgentTimeoutError``) or into the exec cap
  (``ExecCapError``) in a trial whose requests the proxy held back for 429
  answers (``absorbed_429``), so that the waits took time the agent did not
  get to use. None of these is a capability outcome.
  At most :data:`MAX_RATE_LIMIT_RERUNS` reruns per attempt; one more
  contaminated trial raises InfraError(RATE_LIMITED);
* the upstream did not answer one of its requests (metered runs): the proxy
  could not reach it, or its answer broke off mid-stream (``upstream_errors``).
  At most :data:`MAX_ENDPOINT_RERUNS` reruns per attempt; one more such trial
  raises InfraError(ENDPOINT_UNAVAILABLE). Answers the upstream did send,
  errors included, reach the agent as they did upstream and the trial stands;
* it failed before its agent ran (environment start or agent setup) while the
  Docker daemon answers: at most :data:`MAX_SETUP_RERUNS` rerun. A second
  failure is counted, and when it decides the task (the shipped attempt) it is
  the task's ``env_error``: the run reports the task as an infrastructure
  error and goes on with the other tasks.

Reruns after rate limiting or upstream errors start after a pause of
:data:`RERUN_DELAY_SEC`. Discarded trials are written to
``<snapshot root>/<package>.discarded.json`` with the reason, never into
``attempts``.

System-level infrastructure failures stop the session with InfraError, the
running job cancelled first: the job watchdog's stall and Docker daemon checks,
a setup failure while the Docker daemon does not answer, the metering proxy
failing its own health check (its ledger stopped being writable), a metered
trial whose agent ran without the proxy seeing one request from it
(METER_UNAVAILABLE) or without one of its requests being answered by the model
(ENDPOINT_UNAVAILABLE: no 2xx, no 4xx answer about the request itself, no
rate limiting), and a job that leaves a package without a trial or Harbor
failing outside its trials (HARBOR_INTERNAL). Without a meter, rate limiting
and upstream errors are not observed: ``contaminated_429`` stays False and no
trial is discarded for them.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from harbor.models.trial.config import AgentConfig
from harbor.trial.errors import AgentTimeoutError

from ..config import check_run_id
from ..errors import ConfigError, InfraCategory, InfraError
from ..meter import MeterEndpoint, TrialUsage
from ..method import probe_core
from ..method.identity import (
    BUILD_FILE,
    Snapshot,
    file_manifest,
    snapshot_package,
    validate_materialized,
)
from ..method.probe_core import ProbeResult, ProbeSpec
from ..paradigms.base import Paradigm, get_paradigm
from .collect import RESULT_FILE, TrialOutput, agent_ran, collect_job, read_result
from .executors import ExecutorSpec, executor_spec
from .executors.tagged import ExecCapError
from .job import (
    agent_config,
    check_exec_cap,
    job_config,
    needs_rubric,
    package_agent_budget,
    run_job,
)
from .usage import meter_row, task_usage
from .watchdog import Check, DockerDaemonCheck, Trip, docker_daemon_problem

ATTEMPT_KEYS = (
    "attempt", "attempted", "completed", "collected", "job_completed", "job_name",
    "job_elapsed_sec", "outcome", "reward", "artifact_dir", "trial_dir", "diagnostic",
    "input_snapshot", "artifact_files", "usage", "step_results", "started_at",
    "finished_at", "exception_info", "budget", "shipped", "build_identity_status",
)
"""Keys of an attempt record, in the order of the upstream manifest rows."""
FEEDBACK_FILE = "instruction.md"
"""The package file that carries the retry feedback."""
DIAG_CHARS = 1500
"""Characters of the first probe output quoted in the retry feedback."""
MAX_RATE_LIMIT_RERUNS = 3
MAX_ENDPOINT_RERUNS = 3
MAX_SETUP_RERUNS = 1
RERUN_DELAY_SEC = 300.0
"""Pause before rerunning trials discarded for rate limiting or upstream errors, so the
rerun does not meet the same burst or outage."""
RATE_LIMITED = "rate_limited"
UPSTREAM_ERRORS = "upstream_errors"
"""Reasons of discarded trials, besides ``setup_failed:<phase>``."""

_LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class GenerationResult:
    """What one task's generation produced."""

    task_id: str
    verifier_sh: Path | None
    """The shipped attempt's verifier product, None when it delivered none or an empty one."""
    probe: str
    """probe_core outcome of the shipped attempt."""
    attempts: list[dict]
    """A and optional B, keys :data:`ATTEMPT_KEYS`; the shipped one has ``shipped`` True."""
    usage: dict
    """Tokens of the counted attempts summed, or ``{"unavailable": reason}``; see :mod:`.usage`."""
    contaminated_429: bool
    """Whether a trial of this task was discarded because rate limiting reached it."""
    env_error: str | None
    """The environment failure of the shipped attempt (its environment or agent setup
    failed twice); not a capability outcome. None when the shipped attempt's agent ran."""


@dataclass(frozen=True)
class _Package:
    task_id: str
    path: Path
    paradigm: Paradigm
    spec: ProbeSpec

    @property
    def name(self) -> str:
        return self.path.name


@dataclass
class _Slot:
    """One counted attempt of one task, over as many jobs as its reruns take."""

    package: _Package
    attempt: int
    snapshot: Snapshot
    discarded: list[dict[str, Any]] = field(default_factory=list)
    rate_limit_reruns: int = 0
    endpoint_reruns: int = 0
    setup_reruns: int = 0


@dataclass(frozen=True)
class _Decided:
    record: dict[str, Any]
    output: TrialOutput
    meter: TrialUsage | None


@dataclass(frozen=True)
class _Session:
    name: str
    run_id: str
    jobs_dir: Path
    snapshot_root: Path
    executor: ExecutorSpec
    model: str
    agent: AgentConfig
    agent_timeout_sec: float
    exec_cap_sec: float | None
    meter: MeterEndpoint | None
    concurrency: int
    watchdog_sec: int
    rubric: bool


def generate(packages: Sequence[Path], *, run_id: str, jobs_dir: Path, executor: str,
             model: str, provider: Mapping[str, object], meter: MeterEndpoint | None,
             concurrency: int, watchdog_sec: int = 1200,
             exec_cap_sec: float | None = None) -> list[GenerationResult]:
    """Generate a verifier for every sealed package; see the module docstring.

    ``executor`` names a ``run/executors/registry.toml`` entry; ``model`` is
    ``<provider>/<model id>`` and ``provider`` the executor's provider block
    (see :func:`gavel_harness.run.job.agent_config`). ``meter`` routes every
    trial through the metering proxy under its own tag; None runs unmetered.
    ``concurrency`` caps the trials running at once; ``watchdog_sec`` is the
    stall window of each job; ``exec_cap_sec`` is the exec cap of every agent
    command (None: none). All packages must agree on the agent budget in
    their task.toml and on whether their evidence surface has a ``process.*``
    type (which mounts the rubric library). Results come in package order.

    Raises ConfigError for a package that fails its identity check or a
    configuration the packages disagree on, and InfraError for a system-level
    failure. An InfraError returns no result: the input snapshots, job
    directories and ``<package>.discarded.json`` files stay on disk, and the
    affected packages are generated again in a new call.
    """
    check_run_id(run_id)
    if concurrency < 1:
        raise ConfigError(f"concurrency must be at least 1, got {concurrency}")
    if watchdog_sec <= 0:
        raise ConfigError(f"watchdog_sec must be positive, got {watchdog_sec}")
    if exec_cap_sec is not None:
        exec_cap_sec = check_exec_cap(exec_cap_sec)
    loaded = [_load_package(Path(path)) for path in packages]
    if not loaded:
        return []
    for attr, what in (("task_id", "task id"), ("name", "package directory name")):
        values = [getattr(package, attr) for package in loaded]
        repeated = sorted({value for value in values if values.count(value) > 1})
        if repeated:
            raise ConfigError(f"duplicate {what}s in the generation request: {repeated}")
    timeout = _agree(loaded, lambda package: package_agent_budget(package.path),
                     "agent budget ([agent] timeout_sec)")
    rubric = _agree(loaded, lambda package: needs_rubric(package.path),
                    "need for the rubric library (process.* evidence)")
    spec = executor_spec(executor)
    jobs_dir = Path(jobs_dir).absolute()
    name = f"gen-{run_id}-{uuid.uuid4().hex[:12]}"
    session = _Session(
        name=name, run_id=run_id, jobs_dir=jobs_dir,
        snapshot_root=jobs_dir / "input_snapshots" / name, executor=spec, model=model,
        agent=agent_config(spec, model=model, provider=provider, agent_timeout_sec=timeout,
                           meter=meter, run_id=run_id, exec_cap_sec=exec_cap_sec),
        agent_timeout_sec=timeout, exec_cap_sec=exec_cap_sec, meter=meter,
        concurrency=concurrency, watchdog_sec=watchdog_sec, rubric=rubric)
    session.snapshot_root.mkdir(parents=True, exist_ok=False)

    first_slots = [_Slot(package, 0, _snapshot(session, package.path, package, 0, None))
                   for package in loaded]
    first = _run_attempt(session, first_slots, "a")
    feedback: dict[str, str] = {}
    for package in loaded:
        text = retry_feedback(first[package.task_id].record["outcome"],
                              first[package.task_id].record["diagnostic"], package.spec)
        if text is not None:
            feedback[package.task_id] = text
    retry_slots = [_Slot(slot.package, 1, _snapshot(session, slot.snapshot.package_dir,
                                                    slot.package, 1,
                                                    feedback[slot.package.task_id]))
                   for slot in first_slots if slot.package.task_id in feedback]
    second = _run_attempt(session, retry_slots, "b") if retry_slots else {}
    slots = {(slot.package.task_id, slot.attempt): slot for slot in first_slots + retry_slots}
    return [_finish(session, package, first[package.task_id], second.get(package.task_id),
                    package.task_id in feedback,
                    [slots[(package.task_id, n)] for n in (0, 1)
                     if (package.task_id, n) in slots])
            for package in loaded]


def retry_feedback(outcome: str, diagnostic: str, spec: ProbeSpec) -> str | None:
    """The feedback attempt B gets after a first attempt with this probe outcome.

    None unless the outcome is CRASH or NODIRECTION; otherwise the spec's
    feedback for that outcome with ``{diag}`` replaced by the last
    :data:`DIAG_CHARS` characters of ``diagnostic``.
    """
    if outcome == probe_core.CRASH:
        text = spec.crash_feedback
    elif outcome == probe_core.NODIRECTION:
        text = spec.nodirection_feedback
    else:
        return None
    return text.replace("{diag}", diagnostic[-DIAG_CHARS:])


def ship(task_id: str, spec: ProbeSpec, first: Mapping[str, Any],
         retry: Mapping[str, Any] | None, *, retry_attempted: bool) -> ProbeResult:
    """The delivery decision over a task's attempt records (upstream ``generate_roll``)."""
    return probe_core.merge(
        task_id, spec, first["diagnostic"], retry["diagnostic"] if retry else None,
        retry_attempted=retry_attempted,
        retry_artifact_available=bool(retry and retry["artifact_dir"]))


def _load_package(path: Path) -> _Package:
    validate_materialized(path)
    identity = json.loads((path / BUILD_FILE).read_text(encoding="utf-8"))["identity"]
    task_id = identity["materials"].get("task_id")
    paradigm_name = identity["configuration"].get("paradigm")
    if not isinstance(task_id, str) or not isinstance(paradigm_name, str):
        raise ConfigError(f"{path / BUILD_FILE} names no task id or paradigm")
    paradigm = get_paradigm(paradigm_name)
    return _Package(task_id=task_id, path=path.absolute(), paradigm=paradigm,
                    spec=paradigm.probe_spec())


def _agree[T](packages: Sequence[_Package], read: Callable[[_Package], T], what: str) -> T:
    values = {package.task_id: read(package) for package in packages}
    distinct = set(values.values())
    if len(distinct) != 1:
        raise ConfigError(f"the packages of one generation call differ in their {what}: {values}")
    return distinct.pop()


def _snapshot(session: _Session, source: Path, package: _Package, attempt: int,
              feedback: str | None) -> Snapshot:
    destination = session.snapshot_root / str(attempt) / package.name
    return snapshot_package(source, destination,
                            destination.parent / f"{package.name}.snapshot.json",
                            feedback_file=FEEDBACK_FILE, feedback=feedback)


def _run_attempt(session: _Session, slots: Sequence[_Slot], letter: str) -> dict[str, _Decided]:
    """Run one counted attempt of every slot, rerunning discarded trials; by task id."""
    decided: dict[str, _Decided] = {}
    pending = list(slots)
    wave = 0
    while pending:
        job_name = f"{session.name}-{letter}" + (f"-r{wave}" if wave else "")
        if any(slot.discarded and slot.discarded[-1]["reason"] in (RATE_LIMITED, UPSTREAM_ERRORS)
               for slot in pending):
            _LOG.info("pausing %.0f s before rerunning trials the endpoint failed",
                      RERUN_DELAY_SEC)
            time.sleep(RERUN_DELAY_SEC)
        outputs, elapsed = _run_wave(session, job_name, pending)
        rerun: list[_Slot] = []
        for slot in pending:
            output = outputs[slot.package.name]
            record = _attempt_record(session, slot, job_name, elapsed, output)
            usage = (session.meter.ledger.trial(session.run_id, output.trial_name)
                     if session.meter is not None else None)
            if usage is not None and rate_limit_reached(usage, output):
                _discard(session, slot, {"reason": RATE_LIMITED, "meter": meter_row(usage),
                                         "record": record})
                if slot.rate_limit_reruns >= MAX_RATE_LIMIT_RERUNS:
                    raise InfraError(
                        InfraCategory.RATE_LIMITED,
                        f"task {slot.package.task_id}: attempt {slot.attempt} stayed "
                        f"rate-limited over {MAX_RATE_LIMIT_RERUNS} reruns "
                        f"(last trial {output.trial_dir})")
                slot.rate_limit_reruns += 1
                rerun.append(slot)
            elif usage is not None and usage.upstream_errors > 0:
                _discard(session, slot, {"reason": UPSTREAM_ERRORS, "meter": meter_row(usage),
                                         "record": record})
                if slot.endpoint_reruns >= MAX_ENDPOINT_RERUNS:
                    raise InfraError(
                        InfraCategory.ENDPOINT_UNAVAILABLE,
                        f"task {slot.package.task_id}: attempt {slot.attempt} met requests the "
                        f"upstream did not answer over {MAX_ENDPOINT_RERUNS} reruns "
                        f"(last trial {output.trial_dir})")
                slot.endpoint_reruns += 1
                rerun.append(slot)
            elif output.setup_failure is not None and slot.setup_reruns < MAX_SETUP_RERUNS:
                _discard(session, slot, {"reason": f"setup_failed:{output.setup_failure}",
                                         "error": output.failure_summary(), "record": record})
                slot.setup_reruns += 1
                rerun.append(slot)
            else:
                decided[slot.package.task_id] = _Decided(record, output, usage)
        if rerun:
            _LOG.info("%s: rerunning %d trial(s) in a fresh job", job_name, len(rerun))
        pending = rerun
        wave += 1
    return decided


def rate_limit_reached(usage: TrialUsage, output: TrialOutput) -> bool:
    """Whether rate limiting reached a metered trial (see the module docstring).

    A 429 passed to the agent, a request its client abandoned while the proxy
    waited out 429 answers, or an agent that ran out of budget or into the exec
    cap after the proxy held back some of its requests for 429 answers.
    """
    timed_out = output.exception_type in (AgentTimeoutError.__name__, ExecCapError.__name__)
    return (usage.passed_429 > 0 or usage.abandoned_429 > 0
            or (timed_out and usage.absorbed_429 > 0))


def _run_wave(session: _Session, job_name: str,
              slots: Sequence[_Slot]) -> tuple[dict[str, TrialOutput], float]:
    """Run one Harbor job over the slots' frozen inputs; the trials by package name."""
    config = job_config(job_name=job_name, jobs_dir=session.jobs_dir,
                        tasks=[slot.snapshot.package_dir for slot in slots], agent=session.agent,
                        run_id=session.run_id, concurrency=session.concurrency,
                        rubric=session.rubric)
    job_dir = session.jobs_dir / job_name
    checks: list[Check] = [DockerDaemonCheck()]
    if session.meter is not None:
        checks += [_meter_health(session.meter),
                   _meter_check(job_dir, session.meter, session.run_id)]
    _LOG.info("%s: running %d trial(s)", job_name, len(slots))
    run = run_job(config, watchdog_sec=session.watchdog_sec, checks=checks)
    if session.meter is not None:
        session.meter.check()
    outputs = collect_job(run.job_dir)
    wanted = {slot.package.name for slot in slots}
    if set(outputs) != wanted:
        raise InfraError(
            InfraCategory.HARBOR_INTERNAL,
            f"job {job_name} left packages without a trial {sorted(wanted - set(outputs))} "
            f"or with an unexpected one {sorted(set(outputs) - wanted)}")
    for output in outputs.values():
        if output.exception_type == "CancelledError":
            raise InfraError(InfraCategory.HARBOR_INTERNAL,
                             f"trial {output.trial_dir} was cancelled inside a finished job")
    if session.meter is not None:
        for output in outputs.values():
            trip = _model_unreached(output.trial_dir, output.result, session.meter,
                                    session.run_id)
            if trip is not None:
                raise InfraError(trip.category, trip.message)
    failed = sorted(name for name, output in outputs.items() if output.setup_failure)
    if failed:
        problem = docker_daemon_problem()
        if problem is not None:
            raise InfraError(InfraCategory.DOCKER_UNAVAILABLE,
                             f"job {job_name}: {len(failed)} trial(s) failed to start while the "
                             f"Docker daemon does not answer: {problem}")
    return outputs, run.elapsed_sec


def _model_unreached(trial_dir: Path, result: Mapping[str, Any], meter: MeterEndpoint,
                     run_id: str) -> Trip | None:
    """Why a metered trial's agent ran without one answer from the model, else None.

    METER_UNAVAILABLE when the proxy saw no request from the trial;
    ENDPOINT_UNAVAILABLE when it saw requests but none got a 2xx answer (no
    token counts and no 2xx without them), none got a 4xx answer about the
    request itself (``client_errors``: the model's endpoint judged the request,
    e.g. a context too long for it, which is the task's outcome) and none met
    rate limiting, which the rate-limit rule handles.
    """
    if not agent_ran(result):
        return None
    usage = meter.ledger.trial(run_id, trial_dir.name)
    if usage.requests == 0:
        return Trip(InfraCategory.METER_UNAVAILABLE,
                    f"the agent of trial {trial_dir} ran but the metering proxy recorded no "
                    "request from it: the agent could not reach the model through the proxy "
                    "(proxy down, unreachable gateway, or a CLI that failed before its first "
                    "request)")
    answered = usage.total_tokens > 0 or usage.usage_missing > 0
    if not (answered or usage.client_errors or usage.passed_429 or usage.abandoned_429):
        return Trip(InfraCategory.ENDPOINT_UNAVAILABLE,
                    f"none of the {usage.requests} model request(s) of trial {trial_dir} got "
                    "an answer from the model through the metering proxy "
                    f"({usage.upstream_errors} did not reach the upstream or broke off "
                    "mid-answer; the ledger has the status of every request)")
    return None


def _meter_health(meter: MeterEndpoint) -> Check:
    """A watchdog check that raises the metering proxy's own failure (see MeterEndpoint.check)."""

    def check() -> Trip | None:
        meter.check()
        return None

    return check


def _meter_check(job_dir: Path, meter: MeterEndpoint, run_id: str) -> Check:
    """A watchdog check applying :func:`_model_unreached` to each trial as it finishes."""
    done: set[str] = set()

    def check() -> Trip | None:
        if not job_dir.is_dir():
            return None
        for trial_dir in sorted(path for path in job_dir.iterdir() if path.is_dir()):
            if trial_dir.name in done or not (trial_dir / RESULT_FILE).is_file():
                continue
            try:
                result = read_result(trial_dir)
            except InfraError:
                continue  # Harbor is still writing it; read again at the next look
            done.add(trial_dir.name)
            trip = _model_unreached(trial_dir, result, meter, run_id)
            if trip is not None:
                return trip
        return None

    return check


def _attempt_record(session: _Session, slot: _Slot, job_name: str, elapsed: float,
                    output: TrialOutput) -> dict[str, Any]:
    raw = output.result
    art = output.artifact_dir
    snapshot = {"package_dir": str(slot.snapshot.package_dir),
                "manifest_path": str(slot.snapshot.manifest_path),
                "sha256": slot.snapshot.manifest_sha256}
    record = {
        "attempt": slot.attempt, "attempted": True, "completed": bool(raw.get("finished_at")),
        "collected": True, "job_completed": True, "job_name": job_name,
        "job_elapsed_sec": elapsed,
        "outcome": probe_core.classify(output.probe_output, slot.package.spec),
        "reward": output.reward, "artifact_dir": str(art) if art else None,
        "trial_dir": str(output.trial_dir), "diagnostic": output.probe_output,
        "input_snapshot": snapshot, "artifact_files": file_manifest(art) if art else [],
        "usage": raw.get("agent_result"), "step_results": raw.get("step_results"),
        "started_at": raw.get("started_at"), "finished_at": raw.get("finished_at"),
        "exception_info": raw.get("exception_info"),
        "budget": {"agent_timeout_sec": session.agent_timeout_sec,
                   "exec_cap_sec": session.exec_cap_sec, "model": session.model,
                   "harness": session.executor.name},
        "shipped": False,
        "build_identity_status": "verified",
    }
    (output.trial_dir / "input_snapshot.json").write_text(
        json.dumps(snapshot, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return record


def _finish(session: _Session, package: _Package, first: _Decided, second: _Decided | None,
            retry_attempted: bool, slots: Sequence[_Slot]) -> GenerationResult:
    probe = ship(package.task_id, package.spec, first.record,
                 second.record if second else None, retry_attempted=retry_attempted)
    shipped = second if probe.shipped == "retry" and second is not None else first
    shipped.record["shipped"] = True
    counted = [first] + ([second] if second else [])
    attempts = [decided.record for decided in counted]
    collected = (package.paradigm.collect(shipped.output.artifact_dir)
                 if shipped.output.artifact_dir else None)
    failure = shipped.output.setup_failure
    env_error = (None if failure is None else
                 f"attempt {shipped.record['attempt']}: {failure} failed "
                 f"{MAX_SETUP_RERUNS + 1} times ({shipped.output.failure_summary()})")
    meter = ([decided.meter for decided in counted if decided.meter is not None]
             if session.meter is not None else None)
    (session.snapshot_root / f"{package.name}.attempts.json").write_text(
        json.dumps(attempts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return GenerationResult(
        task_id=package.task_id,
        verifier_sh=collected.artifact_path if collected and collected.ok else None,
        probe=probe.outcome,
        attempts=attempts,
        usage=task_usage(attempts, meter),
        contaminated_429=any(entry["reason"] == RATE_LIMITED
                             for slot in slots for entry in slot.discarded),
        env_error=env_error,
    )


def _discard(session: _Session, slot: _Slot, entry: dict[str, Any]) -> None:
    """Record a discarded trial on the slot and in ``<package>.discarded.json`` at once."""
    entry = {"attempt": slot.attempt, **entry}
    slot.discarded.append(entry)
    path = session.snapshot_root / f"{slot.package.name}.discarded.json"
    entries = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    path.write_text(json.dumps(entries + [entry], ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
