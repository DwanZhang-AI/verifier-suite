"""Harbor job configuration and execution.

:func:`agent_config` gives the generating executor the agent configuration the
upstream harness gave JudgeOpenCode (``judge/core/session.py`` ``_agent_spec``):
the model, the packages' agent budget as ``override_timeout_sec``, the CLI
configuration holding the caller's provider block and the executor's permission
block, and the executor's environment. Three things are new. In a metered run the
agent gets a ``meter`` argument from which each trial derives its own proxy URL
(see :mod:`gavel_harness.run.executors.tagged`), and the provider block may
not reference an environment variable, so the API key stays on the host. In an
unmetered run every ``{env:NAME}`` reference in the provider block is passed to
the agent as ``NAME=${NAME}``, which Harbor resolves from the host environment
when the trial starts. An exec cap, when given, becomes the executor's
``exec_cap_sec`` argument: the time limit of every agent command that sets none
(the upstream environments' transport cap). No ``exclude_logs``: the CLI's own
log stays with the trial.

:func:`job_config` builds one generation job on Harbor's docker environment,
with ``delete=False`` (a trial ends with ``docker compose down`` without
``--rmi``, so the image it built stays and a rerun or an anchor of the same
environment builds from the layer cache instead of fetching packages anew), cpu
and memory enforcement ignored (the packages' task.toml values are not
container limits, as in the upstream environments), the rubric library mounted
read-only at :data:`RUBRIC_TARGET` when asked, and the compose overlay of
:func:`write_generation_overlay`: each package's ``environment/Dockerfile``
image run alone, labelled ``veritas.run=<run_id>`` and started as the upstream
environments started it, ``sleep infinity`` in place of the image's
``ENTRYPOINT`` and ``CMD``; a package's own ``environment/docker-compose.yaml``
starts no service and changes nothing. Harbor names a trial's image
``<compose project>-main``, the project being the trial name with ``__env``
appended. The anchors use :func:`write_compose_overlay` instead, which keeps a
task's own compose services.

:func:`run_job` runs a job in this process under a
:class:`~gavel_harness.run.watchdog.Watchdog` and raises InfraError when the
watchdog cancelled it or Harbor failed outside its trials.
"""

from __future__ import annotations

import asyncio
import copy
import json
import os
import re
import time
import tomllib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from types import MappingProxyType
from typing import Any

from harbor.job import Job
from harbor.models.environment_type import EnvironmentType
from harbor.models.job.config import JobConfig
from harbor.models.trial.config import (
    AgentConfig,
    EnvironmentConfig,
    ResourceMode,
    ServiceVolumeConfig,
    TaskConfig,
)

from ..config import RUN_LABEL, check_run_id
from ..errors import ConfigError, InfraCategory, InfraError, GavelError
from ..meter import MeterEndpoint
from .executors import ExecutorSpec
from .watchdog import DEFAULT_INTERVAL_SEC, Check, Trip, Watchdog, docker_children_running

RUBRIC_TARGET = "/rubric_lib"
"""Where a job that asks for it sees the rubric library (read-only)."""
EVIDENCE_MANIFEST = "evidence_manifest.json"
"""The package file holding its judge-time evidence surface."""
HARBOR_BUILD_SERVICE: Mapping[str, Any] = MappingProxyType(
    {"build": {"context": "${CONTEXT_DIR}"}, "pull_policy": "build"})
"""Harbor 0.21.0's ``main`` service for a task with an ``environment/Dockerfile``
(``environments/docker/docker-compose-build.yaml``) without its ``command``;
Harbor sets ``CONTEXT_DIR`` to the task's environment directory."""

_ENV_REF = re.compile(r"\{env:([A-Za-z_][A-Za-z0-9_]*)\}")


@dataclass(frozen=True)
class JobRun:
    """A Harbor job that ran to its end."""

    job_dir: Path
    elapsed_sec: float


def _upstream_start(run_id: str) -> dict[str, Any]:
    """Settings of ``main`` that start it as the upstream environments did, labelled."""
    return {"labels": {RUN_LABEL: check_run_id(run_id)}, "entrypoint": ["sleep"],
            "command": ["infinity"]}


def _write_new(path: Path, text: str) -> Path:
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(text)
    except FileExistsError as exc:
        raise ConfigError(f"refusing to reuse the existing compose overlay {path}") from exc
    return path


def write_compose_overlay(path: Path, run_id: str) -> Path:
    """Write the compose overlay of the anchor jobs to ``path`` (new file) and return it.

    The overlay labels the task's ``main`` service ``veritas.run=<run_id>`` and
    starts it with entrypoint ``sleep`` and command ``infinity``, as the
    upstream environments' ``docker run --entrypoint sleep <image> infinity``
    did: an image ``ENTRYPOINT`` that starts services or rewrites files never
    runs. Only ``main`` is named; other services of a task's own compose file
    start and keep their settings. Raises ConfigError when ``path`` exists.
    """
    return _write_new(path, json.dumps({"services": {"main": _upstream_start(run_id)}},
                                       indent=1))


def write_generation_overlay(path: Path, run_id: str) -> Path:
    """Write the compose overlay of the generation jobs to ``path`` (new file) and return it.

    The upstream environments built a package's ``environment/Dockerfile`` and
    ran that image alone, ``docker run -d --entrypoint sleep <image> infinity``;
    a package's ``environment/docker-compose.yaml`` was never read. Harbor
    merges that file into every trial's project before the job's overlays, so
    this overlay replaces the whole ``services`` mapping (compose's
    ``!override`` tag) with a single ``main``: :data:`HARBOR_BUILD_SERVICE`
    with the settings of :func:`write_compose_overlay`. A package's sidecar
    services then never start and its settings for ``main`` (image name,
    network, environment, dependencies, health check) do not apply, while the
    environment and mount overlays Harbor merges after this one still do. The
    package's bytes are not touched. Docker Compose honours ``!override`` from
    2.24.4 on; earlier versions ignore it without an error and merge the
    package's file, which :func:`gavel_harness.doctor.check_compose_override`
    detects before a generation run starts. Every generation package has an
    ``environment/Dockerfile``, as upstream required. A package with both a
    compose file and a network policy would fail to start: Harbor's
    egress-control overlay, merged after this one, names the package's own
    services. Raises ConfigError when ``path`` exists.
    """
    main = {**HARBOR_BUILD_SERVICE, **_upstream_start(run_id)}
    return _write_new(path, "services: !override\n  main: "
                      + json.dumps(main, sort_keys=True) + "\n")


def agent_config(executor: ExecutorSpec, *, model: str, provider: Mapping[str, Any],
                 agent_timeout_sec: float, meter: MeterEndpoint | None,
                 run_id: str, exec_cap_sec: float | None = None) -> AgentConfig:
    """The AgentConfig of a generation job; see the module docstring.

    ``model`` is ``<provider>/<model id>`` and ``provider`` the CLI's provider
    block, holding exactly that provider. ``exec_cap_sec`` (None: no cap) is
    passed to the executor as its ``exec_cap_sec`` argument. Raises ConfigError
    for a malformed model or provider block, for an environment reference in a
    metered run, for a referenced variable the host environment does not set,
    and for an exec cap that is not a positive number.
    """
    provider_id, _, model_id = model.partition("/")
    if not provider_id or not model_id:
        raise ConfigError(f"model must be <provider>/<model id>, got {model!r}")
    if list(provider) != [provider_id] or not isinstance(provider[provider_id], Mapping):
        raise ConfigError(
            f"the provider block must hold exactly the model's provider {provider_id!r}, "
            f"got {sorted(provider)}")
    try:
        refs = sorted(set(_ENV_REF.findall(json.dumps(provider))))
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"the provider block must be JSON data: {exc}") from exc
    env = dict(executor.env)
    kwargs: dict[str, Any] = {executor.config_kwarg: {
        "provider": copy.deepcopy(dict(provider)),
        "permission": dict(executor.permission),
    }}
    if exec_cap_sec is not None:
        kwargs["exec_cap_sec"] = check_exec_cap(exec_cap_sec)
    if meter is not None:
        if refs:
            raise ConfigError(
                "a metered run keeps the API key on the host, but the provider block "
                f"references {', '.join('{env:' + name + '}' for name in refs)}; give it a "
                "placeholder key, the metering proxy sends the real one")
        kwargs["meter"] = {"gateway": meter.gateway, "port": meter.port,
                           "run_id": check_run_id(run_id), "upstream_path": meter.upstream_path}
    else:
        missing = [name for name in refs if name not in os.environ]
        if missing:
            raise ConfigError(
                f"the provider block references {', '.join(missing)}, which the host "
                "environment does not set")
        env.update({name: "${" + name + "}" for name in refs})
    return AgentConfig(import_path=executor.import_path, model_name=model,
                       override_timeout_sec=agent_timeout_sec, kwargs=kwargs, env=env)


def check_exec_cap(exec_cap_sec: float) -> float:
    """``exec_cap_sec`` as a float; ConfigError unless it is a positive number."""
    if isinstance(exec_cap_sec, bool) or not isinstance(exec_cap_sec, (int, float)) \
            or not exec_cap_sec > 0:
        raise ConfigError(f"the exec cap must be a positive number of seconds, "
                          f"got {exec_cap_sec!r}")
    return float(exec_cap_sec)


def package_agent_budget(package_dir: Path) -> float:
    """The ``[agent] timeout_sec`` of a package's task.toml; ConfigError when absent."""
    path = Path(package_dir) / "task.toml"
    try:
        value = tomllib.loads(path.read_text(encoding="utf-8")).get("agent", {}).get("timeout_sec")
    except (OSError, ValueError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ConfigError(f"{path} has no positive [agent] timeout_sec")
    return float(value)


def needs_rubric(package_dir: Path) -> bool:
    """Whether a package's evidence surface (``evidence_manifest.json``) has a ``process.*`` type.

    Only such packages are told to consult the rubric library, so only their
    jobs mount it.
    """
    path = Path(package_dir) / EVIDENCE_MANIFEST
    try:
        surface = json.loads(path.read_text(encoding="utf-8"))["judge_evidence"]
        types = [str(etype) for etype in surface.values()]
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ConfigError(f"{path} does not give the package's judge_evidence: {exc}") from exc
    return any(etype.startswith("process.") for etype in types)


def rubric_mount() -> ServiceVolumeConfig:
    """The read-only bind mount of the shipped rubric library at :data:`RUBRIC_TARGET`."""
    library = resources.files("gavel_harness.rubric").joinpath("library_v1")
    source = Path(str(library))
    if not source.is_dir():
        raise ConfigError(f"the rubric library is not a directory on disk ({library}); "
                          "install gavel-harness unzipped")
    return ServiceVolumeConfig(type="bind", source=str(source.resolve()), target=RUBRIC_TARGET,
                               read_only=True)


def job_config(*, job_name: str, jobs_dir: Path, tasks: Sequence[Path], agent: AgentConfig,
               run_id: str, concurrency: int, rubric: bool) -> JobConfig:
    """The JobConfig of one generation job over ``tasks``; see the module docstring.

    Writes the compose overlay ``<jobs_dir>/<job_name>.compose.yaml``
    (:func:`write_generation_overlay`) and refuses (ConfigError) a job name that
    already has one or already has a job directory.
    """
    check_run_id(run_id)
    if concurrency < 1:
        raise ConfigError(f"concurrency must be at least 1, got {concurrency}")
    if not tasks:
        raise ConfigError("a job needs at least one task")
    jobs_dir = Path(jobs_dir).absolute()
    if (jobs_dir / job_name).exists():
        raise ConfigError(f"refusing to reuse the existing Harbor job {jobs_dir / job_name}")
    jobs_dir.mkdir(parents=True, exist_ok=True)
    overlay = write_generation_overlay(jobs_dir / f"{job_name}.compose.yaml", run_id)
    return JobConfig(
        job_name=job_name,
        jobs_dir=jobs_dir,
        n_attempts=1,
        n_concurrent_trials=concurrency,
        quiet=True,
        environment=EnvironmentConfig(
            type=EnvironmentType.DOCKER,
            delete=False,
            cpu_enforcement_policy=ResourceMode.IGNORE,
            memory_enforcement_policy=ResourceMode.IGNORE,
            mounts=[rubric_mount()] if rubric else None,
            extra_docker_compose=[overlay],
        ),
        agents=[agent],
        tasks=[TaskConfig(path=Path(task).absolute()) for task in tasks],
    )


def run_job(config: JobConfig, *, watchdog_sec: float, checks: Sequence[Check] = (),
            busy: Callable[[], bool] = docker_children_running,
            interval_sec: float = DEFAULT_INTERVAL_SEC) -> JobRun:
    """Run ``config`` to its end in this process and return where it wrote its trials.

    ``watchdog_sec``, ``checks``, ``busy`` and ``interval_sec`` configure the
    :class:`~gavel_harness.run.watchdog.Watchdog`. Raises InfraError with the
    watchdog's category when it cancelled the job (the job's containers are
    stopped first), and InfraError(HARBOR_INTERNAL) when Harbor raised outside
    its trials. Must not be called from a running event loop.
    """
    job_dir = Path(config.jobs_dir) / config.job_name
    started = time.monotonic()
    try:
        trip = asyncio.run(_run(config, job_dir, watchdog_sec, checks, busy, interval_sec))
    except GavelError:
        raise
    except Exception as exc:  # noqa: BLE001 - reclassified, never swallowed
        raise InfraError(
            InfraCategory.HARBOR_INTERNAL,
            f"Harbor job {config.job_name} failed outside its trials: "
            f"{describe_exception(exc)}") from exc
    if trip is not None:
        raise InfraError(trip.category, f"job {config.job_name} cancelled: {trip.message}")
    return JobRun(job_dir=job_dir, elapsed_sec=time.monotonic() - started)


def describe_exception(exc: BaseException) -> str:
    """``<type>: <message>``, with the sub-exceptions of an exception group, recursively."""
    text = f"{type(exc).__name__}: {exc}"
    if isinstance(exc, BaseExceptionGroup):
        text += " [" + "; ".join(describe_exception(sub) for sub in exc.exceptions) + "]"
    return text


async def _run(config: JobConfig, job_dir: Path, watchdog_sec: float, checks: Sequence[Check],
               busy: Callable[[], bool], interval_sec: float) -> Trip | None:
    loop = asyncio.get_running_loop()
    running: list[asyncio.Future[Any]] = []

    def cancel() -> None:
        loop.call_soon_threadsafe(running[0].cancel)

    watchdog = Watchdog(job_dir, stall_sec=watchdog_sec, cancel=cancel, checks=checks,
                        interval_sec=interval_sec, busy=busy)
    job = await Job.create(config)
    running.append(asyncio.ensure_future(job.run()))
    watchdog.start()
    try:
        await running[0]
    except asyncio.CancelledError:
        if watchdog.trip is None:
            raise
        return watchdog.trip
    finally:
        watchdog.stop()
    return None
