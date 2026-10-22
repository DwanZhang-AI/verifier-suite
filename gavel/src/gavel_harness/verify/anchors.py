"""The null, oracle and swap anchors: Harbor jobs that judge a written-back verifier.

Each anchor of each task is one Harbor job with one trial on the written-back
task: docker environment, the image built from the task's Dockerfile whenever
it has one, resource limits ignored, the anchors' compose overlay
(:func:`gavel_harness.run.job.write_compose_overlay`: the task container
labelled ``veritas.run=<run_id>`` and started with ``sleep infinity`` in place
of the image's ``ENTRYPOINT``; unlike generation, a task's own compose services
start too), containers removed and images kept when the trial ends. No model is
called.

* null: Harbor's ``nop`` agent; the verifier judges the environment as built.
* oracle: :class:`~gavel_harness.verify.replay_agent.ReplayAgent` stages the
  task's own reference solution.
* swap: the same agent stages the donor task's reference solution (planned by
  :func:`plan_swaps` over every task of the run, delivered or not) into this
  task's environment.

A task's anchors run one after another; up to ``concurrency`` tasks run at a
time. The verifier phase runs with the network policy written into the task
(see :func:`gavel_harness.export.writeback.merge_task_toml`).

Verdicts come from the bridge's ``veritas_verdict.json`` through
:func:`~gavel_harness.verify.verdict.from_exit_code`, cross-checked with the
reward Harbor read. Reasons besides ``exit_<n>``, all NO_VERDICT:

``timeout``
    Harbor's verifier timeout fired.
``staging_failed:<what>``
    The oracle or swap solution was not staged (``<what>`` from the replay
    agent, or ``agent_timeout``), or Harbor could not upload ``tests/``.
``reward_missing``, ``reward_unreadable``
    The bridge wrote no reward, or Harbor could not read it.
``verdict_missing``, ``verdict_unreadable``, ``bridge_mismatch``
    The bridge's verdict file is absent, malformed, or disagrees with the reward.
``environment_failed:<exception>``
    The environment could not be built or started (``raw["infra"]`` =
    :data:`ENV_BUILD_FAILED`).
``harbor_error:<exception>``, ``verifier_not_run``
    Harbor failed in a way that says nothing about the verifier
    (``raw["infra"]`` = ``harbor_internal``).
``not_run``
    An earlier anchor of the task hit an infrastructure failure, so this one
    was skipped (``raw["infra"]`` as that anchor's, ``raw["after"]`` names it).
``image_drift``, ``image_unknown``
    The anchors of one task ran on different image contents, or an anchor's
    image could not be read; every record of the task gets this reason
    (``raw["infra"]`` = ``env_image_drift``, the measured verdict kept in
    ``raw["measured"]``).

Images. When the agent phase starts, the container's image is read: its ID
(:attr:`AnchorRecord.image_id`), the reference it was started from
(``raw["image"]``) and the digest of its filesystem layer list
(``raw["image_layers"]``). Harbor's compose build names each trial's image
``<compose project>-main`` and labels it with the project, so image IDs differ
between anchors even when every layer came from the build cache; the anchors of
a task are therefore pinned on the layer digest, which changes exactly when a
layer was rebuilt. With ``keep_images=False`` each anchor's image is removed by
that exact name once all anchors of the task have finished
(:func:`remove_trial_image`); an image Harbor did not build for the trial (a
prebuilt ``docker_image``) is never removed.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import subprocess
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any

from harbor.constants import MAIN_SERVICE_NAME
from harbor.environments.definition import DOCKERFILE_NAME, should_use_prebuilt_docker_image
from harbor.environments.docker.docker import _sanitize_docker_compose_project_name
from harbor.job import Job
from harbor.models.environment_type import EnvironmentType
from harbor.models.job.config import JobConfig, RetryConfig
from harbor.models.task.config import TaskConfig
from harbor.models.task.verifier_mode import VerifierEnvironmentMode, resolve_task_verifier_mode
from harbor.models.trial.config import AgentConfig, EnvironmentConfig, ResourceMode
from harbor.models.trial.config import TaskConfig as TaskReference
from harbor.models.trial.result import TrialResult
from harbor.trial.errors import AgentTimeoutError, VerifierTimeoutError
from harbor.trial.hooks import TrialHookEvent
from harbor.verifier.verifier import (
    AddTestsDirError,
    DownloadVerifierDirError,
    RewardFileEmptyError,
    RewardFileNotFoundError,
    VerifierOutputParseError,
)

from ..config import check_run_id, slug
from ..errors import ConfigError, InfraCategory
from ..export.writeback import (
    BRIDGE_VERSION,
    VERDICT_FILE,
    VERIFIER_FILE,
    AnchorSettings,
    WrittenTask,
    solution_deliverables,
)
from ..method.identity import sha256_file
from ..paradigms.base import SWAP_POLICIES
from ..run.job import write_compose_overlay
from .replay_agent import AGENT_IMPORT_PATH, STAGING_FILE, SolutionStagingError
from .verdict import AnchorKind, AnchorRecord, Verdict, from_exit_code, from_reward

ENV_BUILD_FAILED = InfraCategory.ENV_BUILD_FAILED.value
"""``raw["infra"]`` of an anchor whose environment could not be built or started."""

_PROJECT_LABEL = "com.docker.compose.project"
_DOCKER_TIMEOUT_SEC = 120
_MESSAGE_LIMIT = 2000


@dataclass(frozen=True)
class SwapPlan:
    """The donor whose reference solution a task's swap anchor stages."""

    donor_task: str
    donor_solution: Path
    cross_type: bool
    """True when the donor's primary extension differs from the task's (or the
    task has none)."""


def primary_extension(deliverables: Sequence[tuple[str, int]]) -> str | None:
    """The lower-cased suffix of the largest deliverable, or None when there is none.

    ``deliverables`` are ``(relative path, bytes)`` pairs; a size tie goes to
    the lexicographically first path. A file without suffix gives ``""``.
    """
    if not deliverables:
        return None
    path, _ = min(deliverables, key=lambda item: (-item[1], item[0]))
    return PurePosixPath(path).suffix.lower()


def plan_swaps(
    tasks: Sequence[WrittenTask],
    *,
    policy: str,
    pool: Mapping[str, Path | None],
    deliverables_subdir: str | None = None,
) -> dict[str, SwapPlan | None]:
    """The swap donor of every task, keyed by task id in input order.

    ``pool`` maps every task of the run, whether it delivered a verifier or
    not, to its reference solution (None when it has none); it must hold every
    task of ``tasks``. Donors are drawn from the pool, so a task's donor does
    not depend on which other tasks delivered. ``policy`` is the profile's
    ``[anchor] swap``. ``none`` gives no swap anchor.
    ``same_extension_deliverables`` (needs ``deliverables_subdir``, the
    profile's ``[anchor] deliverables_subdir``): the pool's tasks are taken in
    order of id, cyclically; a task's donor is the next other task whose
    reference solution has deliverables with the task's primary extension
    (:func:`primary_extension` of its own deliverables), else the next other
    task with any deliverable (``cross_type``). A task without deliverables of
    its own takes the next task with any deliverable, ``cross_type``. None when
    no other task of the pool has a deliverable.
    """
    ids = [task.task_id for task in tasks]
    if len(set(ids)) != len(ids):
        raise ConfigError("task ids repeat")
    missing = sorted(set(ids) - set(pool))
    if missing:
        raise ConfigError(f"the swap pool lacks tasks {missing[:5]}")
    if policy not in SWAP_POLICIES:
        raise ConfigError(f"swap policy must be one of {SWAP_POLICIES}, got {policy!r}")
    if policy == "none":
        if deliverables_subdir is not None:
            raise ConfigError("deliverables_subdir applies only to same_extension_deliverables")
        return {task_id: None for task_id in ids}
    if deliverables_subdir is None:
        raise ConfigError("swap policy same_extension_deliverables needs deliverables_subdir")

    ordered = sorted(pool)
    extension: dict[str, str | None] = {}
    for task_id in ordered:
        solution = pool[task_id]
        if solution is not None and not solution.is_dir():
            raise ConfigError(f"reference solution {solution} of {task_id} is not a directory")
        files = (solution_deliverables(solution, deliverables_subdir)
                 if solution is not None else [])
        extension[task_id] = primary_extension(files)
    plans: dict[str, SwapPlan | None] = {}
    for task_id in ids:
        index = ordered.index(task_id)
        following = [ordered[(index + step) % len(ordered)] for step in range(1, len(ordered))]
        donors = [other for other in following if extension[other] is not None]
        own = extension[task_id]
        same = next((other for other in donors if own is not None and extension[other] == own),
                    None)
        donor = same or (donors[0] if donors else None)
        solution = pool[donor] if donor is not None else None
        plans[task_id] = (None if donor is None or solution is None else
                          SwapPlan(donor_task=donor, donor_solution=solution,
                                   cross_type=same is None))
    return plans


def run_anchors(
    tasks: Sequence[WrittenTask],
    swaps: Mapping[str, SwapPlan | None],
    *,
    settings: AnchorSettings,
    jobs_dir: Path,
    run_id: str,
    concurrency: int,
    keep_images: bool,
) -> list[AnchorRecord]:
    """Run the anchors of every task; return their records, task by task in input order.

    Each task gets a null record, an oracle record when it has a reference
    solution and a swap record when ``swaps`` names a donor. ``swaps`` must have
    an entry for every task. Jobs are written to ``jobs_dir/<run_id>__<task>__<anchor>``,
    next to the compose overlay ``<run_id>__anchors.compose.json`` (see the
    module docstring).

    Raises ConfigError, before any job starts, for an invalid run id or
    concurrency, repeated or unmatched task ids, an existing job directory or
    overlay of the run, a verifier whose bytes differ from its recorded sha256, or a written task
    whose ``[verifier]`` does not match ``settings``. Must be called outside a
    running event loop.
    """
    check_run_id(run_id)
    if isinstance(concurrency, bool) or not isinstance(concurrency, int) or concurrency < 1:
        raise ConfigError(f"concurrency must be a positive integer, got {concurrency!r}")
    jobs_dir = Path(jobs_dir).absolute()
    ids = [task.task_id for task in tasks]
    if len(set(ids)) != len(ids):
        raise ConfigError("task ids repeat")
    if set(swaps) != set(ids):
        raise ConfigError("swaps must have exactly one entry per task")
    slugs = {task_id: slug(task_id) for task_id in ids}
    if len(set(slugs.values())) != len(ids):
        raise ConfigError("two task ids map to one job name")
    for task in tasks:
        _check_written_task(task, settings)
        plan = swaps[task.task_id]
        if plan is not None and not plan.donor_solution.is_dir():
            raise ConfigError(f"swap donor solution {plan.donor_solution} is not a directory")
        for kind in AnchorKind:
            if (jobs_dir / _job_name(run_id, slugs[task.task_id], kind)).exists():
                raise ConfigError(f"job directory for {task.task_id} {kind} exists in {jobs_dir}")
    overlay = jobs_dir / f"{run_id}__anchors.compose.json"
    if overlay.exists():
        raise ConfigError(f"the anchors of run {run_id} already ran in {jobs_dir}")
    jobs_dir.mkdir(parents=True, exist_ok=True)
    write_compose_overlay(overlay, run_id)
    runner = _Runner(swaps=swaps, settings=settings, jobs_dir=jobs_dir, run_id=run_id,
                     slugs=slugs, keep_images=keep_images, overlay=overlay)
    return asyncio.run(runner.run_all(tasks, concurrency))


def builds_image(task_dir: Path) -> bool:
    """Whether the anchors build the task's image (else they run its prebuilt ``docker_image``).

    The anchors build whenever ``environment/Dockerfile`` exists, also when
    task.toml names a ``docker_image``. Raises ConfigError when the task has
    neither.
    """
    config = TaskConfig.model_validate_toml((task_dir / "task.toml").read_text("utf-8"))
    environment_dir = task_dir / "environment"
    docker_image = config.environment.docker_image
    if should_use_prebuilt_docker_image(environment_dir, docker_image=docker_image,
                                        force_build=True):
        return False
    if not (environment_dir / DOCKERFILE_NAME).is_file():
        raise ConfigError(f"{task_dir}: neither environment/Dockerfile nor docker_image")
    return True


def trial_image_name(trial_name: str) -> str:
    """The name Harbor's compose build gives the image of a trial's main container."""
    return f"{_compose_project(trial_name)}-{MAIN_SERVICE_NAME}"


def remove_trial_image(trial_name: str) -> str:
    """Remove the image Harbor built for trial ``trial_name``, by exact name; the outcome.

    The image (:func:`trial_image_name`) is removed only when it carries the
    trial's compose-project label. Outcomes: ``removed``, ``absent``,
    ``kept: not built for trial <name>``, or ``error: <why>``. A docker call that
    fails, times out or cannot start gives an ``error`` outcome; nothing is raised.
    """
    name = trial_image_name(trial_name)
    try:
        inspect = subprocess.run(
            ["docker", "image", "inspect", "--format",
             f'{{{{index .Config.Labels "{_PROJECT_LABEL}"}}}}', name],
            capture_output=True, text=True, timeout=_DOCKER_TIMEOUT_SEC, check=False)
        if inspect.returncode != 0:
            return "absent"
        if inspect.stdout.strip() != _compose_project(trial_name):
            return f"kept: not built for trial {trial_name}"
        removed = subprocess.run(["docker", "image", "rm", name], capture_output=True,
                                 text=True, timeout=_DOCKER_TIMEOUT_SEC, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"error: {_clip(f'{type(exc).__name__}: {exc}')}"
    if removed.returncode != 0:
        return f"error: {_clip(removed.stderr.strip())}"
    return "removed"


def _compose_project(trial_name: str) -> str:
    return _sanitize_docker_compose_project_name(f"{trial_name}__env")


def _job_name(run_id: str, slug: str, kind: AnchorKind) -> str:
    return f"{run_id}__{slug}__{kind.value}"


def _check_written_task(task: WrittenTask, settings: AnchorSettings) -> None:
    verifier = task.task_dir / VERIFIER_FILE
    if not verifier.is_file() or sha256_file(verifier) != task.verifier_sha256:
        raise ConfigError(f"{verifier} does not hold the verifier with the recorded sha256")
    if task.oracle_dir is not None and not task.oracle_dir.is_dir():
        raise ConfigError(f"reference solution {task.oracle_dir} is not a directory")
    config = TaskConfig.model_validate_toml(
        (task.task_dir / "task.toml").read_text(encoding="utf-8"))
    verifier_config = config.verifier
    mismatch = (
        resolve_task_verifier_mode(config) != VerifierEnvironmentMode.SHARED
        or verifier_config.timeout_sec != settings.timeout_sec
        or verifier_config.network_mode is None
        or verifier_config.network_mode.value != settings.network
        or verifier_config.user != settings.user
    )
    if mismatch:
        raise ConfigError(f"{task.task_dir}/task.toml [verifier] was not written for these "
                          "anchor settings")


class _Runner:
    """Runs anchor jobs and removes their images; one instance per :func:`run_anchors` call."""

    def __init__(self, *, swaps: Mapping[str, SwapPlan | None], settings: AnchorSettings,
                 jobs_dir: Path, run_id: str, slugs: Mapping[str, str],
                 keep_images: bool, overlay: Path) -> None:
        self._overlay = overlay
        self._swaps = swaps
        self._settings = settings
        self._jobs_dir = jobs_dir
        self._run_id = run_id
        self._slugs = slugs
        self._keep_images = keep_images

    async def run_all(self, tasks: Sequence[WrittenTask], concurrency: int) -> list[AnchorRecord]:
        slots = asyncio.Semaphore(concurrency)

        async def one(task: WrittenTask) -> list[AnchorRecord]:
            async with slots:
                records = await self._run_task(task)
                if self._keep_images or not builds_image(task.task_dir):
                    return records
                return [await _remove_trial_image(record) for record in records]

        results = await asyncio.gather(*(one(task) for task in tasks))
        return [record for records in results for record in records]

    async def _run_task(self, task: WrittenTask) -> list[AnchorRecord]:
        anchors: list[tuple[AnchorKind, AgentConfig]] = [(AnchorKind.NULL, AgentConfig(name="nop"))]
        if task.oracle_dir is not None:
            anchors.append((AnchorKind.ORACLE, self._replay(task, task.oracle_dir)))
        plan = self._swaps[task.task_id]
        if plan is not None:
            anchors.append((AnchorKind.SWAP, self._replay(task, plan.donor_solution)))
        records: list[AnchorRecord] = []
        for kind, agent in anchors:
            failed = next((record for record in records if record.infra), None)
            if failed is None:
                records.append(await self._run_anchor(task, kind, agent))
            else:
                raw = {"infra": failed.infra, "after": failed.anchor.value}
                records.append(AnchorRecord(
                    task=task.task_id, anchor=kind, verdict=Verdict.NO_VERDICT,
                    reason="not_run", raw=raw, verifier_sha256=task.verifier_sha256,
                    image_id=None, duration_s=0.0))
        return _pin_image(records)

    def _replay(self, task: WrittenTask, solution: Path) -> AgentConfig:
        return AgentConfig(
            import_path=AGENT_IMPORT_PATH,
            override_timeout_sec=self._settings.timeout_sec,
            kwargs={
                "task_dir": str(task.task_dir),
                "solution_dir": str(solution),
                "agent_timeout_sec": self._settings.timeout_sec,
            },
        )

    async def _run_anchor(self, task: WrittenTask, kind: AnchorKind,
                          agent: AgentConfig) -> AnchorRecord:
        job_name = _job_name(self._run_id, self._slugs[task.task_id], kind)
        config = JobConfig(
            job_name=job_name,
            jobs_dir=self._jobs_dir,
            n_attempts=1,
            n_concurrent_trials=1,
            quiet=True,
            retry=RetryConfig(max_retries=0),
            environment=EnvironmentConfig(
                type=EnvironmentType.DOCKER,
                force_build=True,
                delete=False,
                cpu_enforcement_policy=ResourceMode.IGNORE,
                memory_enforcement_policy=ResourceMode.IGNORE,
                extra_docker_compose=[self._overlay],
            ),
            agents=[agent],
            tasks=[TaskReference(path=task.task_dir)],
        )
        probe = _ImageProbe()
        started = time.monotonic()
        raw: dict[str, Any] = {"job": job_name}
        try:
            job = await Job.create(config)
            job.on_agent_started(probe.capture)
            result = await job.run()
        except Exception as exc:
            raw.update(infra=InfraCategory.HARBOR_INTERNAL.value, error=_clip(str(exc)))
            return _record(task, kind, Verdict.NO_VERDICT, f"harbor_error:{type(exc).__name__}",
                           raw, None, started)
        trials = result.trial_results
        if len(trials) != 1:
            raw.update(infra=InfraCategory.HARBOR_INTERNAL.value,
                       error=f"expected one trial, got {len(trials)}")
            return _record(task, kind, Verdict.NO_VERDICT, "harbor_error:trial_count",
                           raw, None, started)
        trial = trials[0]
        trial_dir = self._jobs_dir / job_name / trial.trial_name
        verdict, reason, detail = _judge(kind, trial, trial_dir)
        raw.update(detail, trial=trial.trial_name,
                   environment_started=trial.agent_execution is not None)
        image = probe.images.get(trial.trial_name)
        if image is not None:
            raw.update(image=image.reference, image_layers=image.layers)
        if trial.trial_name in probe.errors:
            raw["image_error"] = probe.errors[trial.trial_name]
        return _record(task, kind, verdict, reason, raw,
                       image.image_id if image is not None else None, started)


def _record(task: WrittenTask, kind: AnchorKind, verdict: Verdict, reason: str,
            raw: dict[str, Any], image_id: str | None, started: float) -> AnchorRecord:
    return AnchorRecord(task=task.task_id, anchor=kind, verdict=verdict, reason=reason,
                        raw=raw, verifier_sha256=task.verifier_sha256, image_id=image_id,
                        duration_s=round(time.monotonic() - started, 3))


def _judge(kind: AnchorKind, trial: TrialResult,
           trial_dir: Path) -> tuple[Verdict, str, dict[str, Any]]:
    """Verdict, reason and detail of one finished anchor trial."""
    raw: dict[str, Any] = {}
    exception = trial.exception_info
    if exception is not None:
        name = exception.exception_type
        raw.update(exception=name, exception_message=_clip(exception.exception_message))
        if trial.agent_execution is None:
            raw["infra"] = ENV_BUILD_FAILED
            return Verdict.NO_VERDICT, f"environment_failed:{name}", raw
        if name == SolutionStagingError.__name__:
            verdict, reason = from_exit_code(None, staging_error=_staging_failure(trial_dir))
            return verdict, reason, raw
        if name == AgentTimeoutError.__name__:
            verdict, reason = from_exit_code(None, staging_error="agent_timeout")
            return verdict, reason, raw
        if name == VerifierTimeoutError.__name__:
            verdict, reason = from_exit_code(None, timed_out=True)
            return verdict, reason, raw
        if name in (AddTestsDirError.__name__, DownloadVerifierDirError.__name__):
            verdict, reason = from_exit_code(None, staging_error=name)
            return verdict, reason, raw
        if name == RewardFileNotFoundError.__name__:
            return Verdict.NO_VERDICT, "reward_missing", raw
        if name in (RewardFileEmptyError.__name__, VerifierOutputParseError.__name__):
            return Verdict.NO_VERDICT, "reward_unreadable", raw
        raw["infra"] = InfraCategory.HARBOR_INTERNAL.value
        return Verdict.NO_VERDICT, f"harbor_error:{name}", raw

    if kind != AnchorKind.NULL:
        failure = _staging_failure(trial_dir)
        if failure != "ok":
            verdict, reason = from_exit_code(None, staging_error=failure)
            return verdict, reason, raw
    if trial.verifier_result is None:
        raw["infra"] = InfraCategory.HARBOR_INTERNAL.value
        return Verdict.NO_VERDICT, "verifier_not_run", raw
    reward = (trial.verifier_result.rewards or {}).get("reward")
    raw["reward"] = reward
    verdict_path = trial_dir / "verifier" / VERDICT_FILE
    if not verdict_path.is_file():
        return Verdict.NO_VERDICT, "verdict_missing", raw
    code = _exit_code(verdict_path)
    if code is None:
        return Verdict.NO_VERDICT, "verdict_unreadable", raw
    raw["exit_code"] = code
    reward_verdict, _ = from_reward(reward)
    if reward_verdict != (Verdict.PASS if code == 0 else Verdict.FAIL):
        return Verdict.NO_VERDICT, "bridge_mismatch", raw
    verdict, reason = from_exit_code(code)
    return verdict, reason, raw


def _exit_code(path: Path) -> int | None:
    """The exit status in a bridge verdict file, or None when the file is malformed."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or data.get("bridge") != BRIDGE_VERSION:
        return None
    code = data.get("exit_code")
    if isinstance(code, bool) or not isinstance(code, int) or not 0 <= code <= 255:
        return None
    return code


def _staging_failure(trial_dir: Path) -> str:
    """``ok``, the replay agent's failure code, or why its status cannot be read."""
    path = trial_dir / "agent" / STAGING_FILE
    if not path.is_file():
        return "status_missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "status_unreadable"
    if data == {"status": "ok"}:
        return "ok"
    what = data.get("what") if isinstance(data, dict) else None
    return what if isinstance(what, str) and what else "status_unreadable"


def _pin_image(records: list[AnchorRecord]) -> list[AnchorRecord]:
    """The records, all NO_VERDICT when the anchors that started ran on different layers."""
    started = [record for record in records if record.raw.get("environment_started")]
    if len(started) < 2:
        return records
    layers = {record.raw.get("image_layers") for record in started}
    if len(layers) == 1 and None not in layers:
        return records
    reason = "image_unknown" if None in layers else "image_drift"
    return [
        replace(record, verdict=Verdict.NO_VERDICT, reason=reason,
                raw={**record.raw, "infra": InfraCategory.ENV_IMAGE_DRIFT.value,
                     "measured": {"verdict": record.verdict.value, "reason": record.reason}})
        for record in records
    ]


async def _remove_trial_image(record: AnchorRecord) -> AnchorRecord:
    """The record after :func:`remove_trial_image` for its trial.

    An anchor whose environment started must have an image of its own; any
    outcome but ``removed`` is recorded as ``image_remove_error``.
    """
    trial = record.raw.get("trial")
    if trial is None or not record.raw.get("environment_started"):
        return record
    outcome = await asyncio.to_thread(remove_trial_image, trial)
    removed: dict[str, Any] = {"image_removed": outcome == "removed"}
    if outcome != "removed":
        removed["image_remove_error"] = outcome
    return replace(record, raw={**record.raw, **removed})


class _DockerError(Exception):
    """A docker CLI call failed."""


async def _docker(*args: str) -> str:
    """Stdout of ``docker <args>``; raises _DockerError on failure or timeout."""
    try:
        process = await asyncio.create_subprocess_exec(
            "docker", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    except OSError as exc:
        raise _DockerError(f"cannot run docker: {exc}") from exc
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), _DOCKER_TIMEOUT_SEC)
    except TimeoutError as exc:
        process.kill()
        await process.wait()
        raise _DockerError(f"docker {args[0]} timed out") from exc
    if process.returncode != 0:
        raise _DockerError(f"docker {' '.join(args)} exited {process.returncode}: "
                           f"{stderr.decode(errors='replace').strip()}")
    return stdout.decode()


@dataclass(frozen=True)
class _Image:
    image_id: str
    reference: str
    """The image reference the container was started from."""
    layers: str
    """``sha256:`` digest of the JSON list of the image's filesystem layer diff IDs."""


class _ImageProbe:
    """Reads the image of each trial's main container when its agent phase starts."""

    def __init__(self) -> None:
        self.images: dict[str, _Image] = {}
        self.errors: dict[str, str] = {}

    async def capture(self, event: TrialHookEvent) -> None:
        trial = event.config.trial_name
        project = _compose_project(trial)
        try:
            containers = (await _docker(
                "ps", "--quiet", "--no-trunc",
                "--filter", f"label={_PROJECT_LABEL}={project}",
                "--filter", f"label=com.docker.compose.service={MAIN_SERVICE_NAME}",
            )).split()
            if len(containers) != 1:
                raise _DockerError(f"expected one {MAIN_SERVICE_NAME} container in compose "
                                   f"project {project}, found {len(containers)}")
            image_id, reference = json.loads(await _docker(
                "inspect", "--format", "[{{json .Image}}, {{json .Config.Image}}]",
                containers[0]))
            layers = json.loads(await _docker(
                "image", "inspect", "--format", "{{json .RootFS.Layers}}", image_id))
        except (_DockerError, ValueError) as exc:
            self.errors[trial] = _clip(str(exc))
            return
        if not isinstance(layers, list) or not layers:
            self.errors[trial] = f"image {image_id} lists no filesystem layers"
            return
        digest = hashlib.sha256(json.dumps(layers).encode()).hexdigest()
        self.images[trial] = _Image(image_id=image_id, reference=reference,
                                    layers=f"sha256:{digest}")


def _clip(text: str) -> str:
    return text if len(text) <= _MESSAGE_LIMIT else text[:_MESSAGE_LIMIT] + "..."
