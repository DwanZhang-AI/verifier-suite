"""Run configuration: every knob of a run is an explicit field, recorded in ``run.json``.

The harness reads no configuration from environment variables. The only
environment lookup is the API key, by the name given in ``api_key_env``; the
key value itself is never stored in a configuration or written to disk.

Three commands start runs, each with its own configuration: :class:`RunConfig`
(``gavel-harness gen``), :class:`ValidateConfig` (``gavel-harness validate --from-run``)
and :class:`MatrixConfig` (``gavel-harness matrix``). ``run.json`` holds the
command, its configuration, the provenance and the sections the run adds while
it proceeds (:func:`write_run_json`, :func:`update_run_json`).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, fields
from pathlib import Path, PurePosixPath
from typing import Any, ClassVar

from .errors import ConfigError
from .provenance import Provenance

PARADIGMS = ("terminal_state", "deliverable", "repo_patch", "dialog_state", "pairwise_text")
"""The five task paradigms; every supported task belongs to exactly one."""

VERIFIER_NETWORK_MODES = ("no-network", "public")
"""Network policy of the verification phase, in Harbor's ``NetworkMode`` spelling."""

RUN_SCHEMA = "veritas-run/1"

RUN_LABEL = "veritas.run"
"""Docker label carrying the run id on every container a run starts."""

RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
"""Accepted run ids: they appear in job names, container labels and metering tags."""

DEFAULT_METER_PORT = 8878
"""Default port of the host-side metering proxy."""

METER_PLACEHOLDER_KEY = "metered"
"""The ``apiKey`` a metered run writes into the provider block; the proxy sends the real key."""

GENERIC_PROVIDER_NAME = "OpenAI-compatible endpoint"
"""Display name of the provider block."""

_ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_PROVIDER_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
_SLUG_UNSAFE = re.compile(r"[^A-Za-z0-9_-]+")


def check_run_id(run_id: str) -> str:
    """Return ``run_id``; ConfigError unless it matches :data:`RUN_ID`."""
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise ConfigError(f"run id {run_id!r} must be 1-64 letters, digits, '_' or '-', "
                          "starting with a letter or digit")
    return run_id


def slug(text: str) -> str:
    """``text`` with every run of characters outside ``[A-Za-z0-9_-]`` replaced by ``-``.

    The one rule by which names become parts of run ids, job names and cache paths.
    """
    return _SLUG_UNSAFE.sub("-", text)


def _check_path_fields(config: Any, names: tuple[str, ...]) -> None:
    for name in names:
        value = getattr(config, name)
        if value is not None and not isinstance(value, Path):
            raise ConfigError(f"{name} must be a path, got {value!r}")


def _check_network(network: str | None) -> None:
    if network is not None and network not in VERIFIER_NETWORK_MODES:
        raise ConfigError(
            f"verifier_network must be one of {VERIFIER_NETWORK_MODES}, got {network!r}")


def _check_count(name: str, value: int, minimum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ConfigError(f"{name} must be at least {minimum}, got {value!r}")


def _check_keep_images(value: bool | None) -> None:
    if value is not None and not isinstance(value, bool):
        raise ConfigError(f"keep_images must be true, false or None, got {value!r}")


class _Recorded:
    """A frozen configuration dataclass recorded in ``run.json`` (paths as strings)."""

    COMMAND: ClassVar[str]
    _PATHS: ClassVar[tuple[str, ...]] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready mapping; paths become strings, tuples lists."""
        data: dict[str, Any] = {}
        for field in fields(self):  # type: ignore[arg-type]
            value = getattr(self, field.name)
            if isinstance(value, Path):
                value = str(value)
            elif isinstance(value, tuple):
                value = list(value)
            elif isinstance(value, _Recorded):
                value = value.to_dict()
            data[field.name] = value
        return data


@dataclass(frozen=True)
class RunConfig(_Recorded):
    """One ``gavel-harness gen`` run.

    ``inputs`` are task directories, directories of tasks, or registry
    references (``registry:<dataset>@<commit>``, read from ``registry`` and
    sampled with ``sample`` and ``seed``). ``paradigm`` overrides the per-task
    paradigm resolution when set. ``env`` (environment profile) and
    ``verifier_network`` (network of the verification phase) override the
    benchmark profile's ``env`` and ``[anchor] network`` when set; None keeps
    the profile's choice. ``deliverable_dir`` is the in-container directory a
    deliverable task's output lands in. ``oracle_root`` holds reference
    solutions kept outside the task directories (``<oracle_root>/<task id>/solution``).
    ``tasks_file`` restricts the inputs to the listed task IDs.

    ``model`` is ``<provider id>/<model id>``. ``meter`` routes every model
    request through the host-side metering proxy on ``meter_port``, which
    containers reach at ``meter_gateway`` (None: the Docker bridge gateway) and
    which listens on ``meter_bind`` (None: the gateway address). ``run_id``
    labels containers and jobs; None derives one from the output directory name
    when the run starts. ``keep_images`` overrides the profile's
    ``[anchor] keep_images`` when set: whether the images Harbor built for the
    run's trials stay, or are removed by exact name when the run ends.
    ``declare`` asks for the declaration of checked and unchecked requirements;
    this build refuses it when the method resolves (the declaration is not
    collected yet).
    """

    COMMAND: ClassVar[str] = "gen"
    _PATHS: ClassVar[tuple[str, ...]] = ("out_dir", "tasks_file", "oracle_root")

    inputs: tuple[str, ...]
    model: str
    base_url: str
    api_key_env: str
    out_dir: Path
    executor: str = "opencode"
    profile: str = "paper/generic"
    env: str | None = None
    paradigm: str | None = None
    concurrency: int = 4
    validate: bool = False
    declare: bool = False
    verifier_network: str | None = None
    tasks_file: Path | None = None
    oracle_root: Path | None = None
    deliverable_dir: str | None = None
    replace_tests: bool = False
    allow_dirty: bool = False
    run_id: str | None = None
    meter: bool = True
    meter_port: int = DEFAULT_METER_PORT
    meter_gateway: str | None = None
    meter_bind: str | None = None
    keep_images: bool | None = None
    registry: str | None = None
    sample: int | None = None
    seed: int = 0
    watchdog_sec: int = 1200

    def __post_init__(self) -> None:
        if not self.inputs:
            raise ConfigError("at least one input is required: a task, directory or registry ref")
        for name in ("model", "base_url", "api_key_env", "executor", "profile"):
            if not getattr(self, name):
                raise ConfigError(f"{name} must not be empty")
        if self.env is not None and not self.env:
            raise ConfigError("env must not be empty; omit it to use the profile's env")
        if not _ENV_NAME.fullmatch(self.api_key_env):
            raise ConfigError(
                "api_key_env must name an environment variable (letters, digits, "
                "underscores); pass the variable's name, not the key"
            )
        if not self.base_url.startswith(("http://", "https://")):
            raise ConfigError(f"base_url must be an http(s) URL, got {self.base_url!r}")
        provider_id, _, model_id = self.model.partition("/")
        if not _PROVIDER_ID.fullmatch(provider_id) or not model_id:
            raise ConfigError(f"model must be <provider id>/<model id>, got {self.model!r}")
        _check_count("concurrency", self.concurrency, 1)
        _check_count("watchdog_sec", self.watchdog_sec, 1)
        if self.paradigm is not None and self.paradigm not in PARADIGMS:
            raise ConfigError(f"unknown paradigm {self.paradigm!r}; expected one of {PARADIGMS}")
        _check_network(self.verifier_network)
        deliverable_dir = self.deliverable_dir
        if deliverable_dir is not None and not PurePosixPath(deliverable_dir).is_absolute():
            raise ConfigError(
                f"deliverable_dir is a container path and must be absolute, got {deliverable_dir!r}"
            )
        if self.run_id is not None:
            check_run_id(self.run_id)
        _check_keep_images(self.keep_images)
        if isinstance(self.meter_port, bool) or not isinstance(self.meter_port, int) \
                or not 0 < self.meter_port < 65536:
            raise ConfigError(f"meter_port must be a TCP port, got {self.meter_port!r}")
        for name in ("meter_gateway", "meter_bind"):
            value = getattr(self, name)
            if value is not None and (not value or any(char in value for char in "/ \t")):
                raise ConfigError(f"{name} must be a host name or address, got {value!r}")
        if self.sample is not None:
            _check_count("sample", self.sample, 1)
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise ConfigError(f"seed must be an integer, got {self.seed!r}")
        if self.registry is not None and not self.registry:
            raise ConfigError("registry must not be empty")
        _check_path_fields(self, self._PATHS)


@dataclass(frozen=True)
class ValidateConfig(_Recorded):
    """One ``gavel-harness validate --from-run`` run: the anchors on an upstream run's verifiers.

    ``from_run`` is the upstream run directory (only read). ``profile`` gives
    the paradigm and the anchor judge environment, ``verifier_network`` and
    ``keep_images`` overriding its network and image retention when set.
    ``oracle_root`` holds reference solutions as
    ``<oracle_root>/<task id>/solution``; a task's own ``solution/`` is used
    otherwise.
    """

    COMMAND: ClassVar[str] = "validate"
    _PATHS: ClassVar[tuple[str, ...]] = ("from_run", "out_dir", "oracle_root")

    from_run: Path
    profile: str
    out_dir: Path
    oracle_root: Path | None = None
    concurrency: int = 4
    keep_images: bool | None = None
    verifier_network: str | None = None
    run_id: str | None = None
    allow_dirty: bool = False

    def __post_init__(self) -> None:
        if not self.profile:
            raise ConfigError("profile must not be empty")
        _check_count("concurrency", self.concurrency, 1)
        _check_network(self.verifier_network)
        if self.run_id is not None:
            check_run_id(self.run_id)
        _check_keep_images(self.keep_images)
        _check_path_fields(self, self._PATHS)
        run_dir = Path(self.from_run).resolve()
        out_dir = Path(self.out_dir).resolve()
        if out_dir == run_dir or out_dir.is_relative_to(run_dir):
            raise ConfigError(f"the output directory {out_dir} lies inside the run directory "
                              f"{run_dir}, which validate only reads")


@dataclass(frozen=True)
class MatrixConfig(_Recorded):
    """One ``gavel-harness matrix`` run: ``per_family`` tasks of every registry family.

    ``registry`` is the registry file or URL; ``families`` restricts the matrix
    to the named families (empty: every family). Every sampled task is fetched,
    generated and validated with ``run``, whose ``inputs`` name the registry.
    """

    COMMAND: ClassVar[str] = "matrix"

    registry: str
    per_family: int
    seed: int
    run: RunConfig
    families: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.registry:
            raise ConfigError("registry must not be empty")
        _check_count("per_family", self.per_family, 1)
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise ConfigError(f"seed must be an integer, got {self.seed!r}")
        if not isinstance(self.run, RunConfig):
            raise ConfigError("run must be a RunConfig")


def provider_block(config: RunConfig) -> dict[str, Any]:
    """The opencode provider block of a run, holding exactly the model's provider.

    The OpenAI-compatible provider of ``@ai-sdk/openai-compatible`` at
    ``base_url`` with the one model of the run. A metered run carries
    :data:`METER_PLACEHOLDER_KEY` (the proxy sends the key); an unmetered run
    references the key variable as ``{env:<api_key_env>}``, which the executor
    resolves inside the container.
    """
    provider_id, _, model_id = config.model.partition("/")
    key = METER_PLACEHOLDER_KEY if config.meter else f"{{env:{config.api_key_env}}}"
    return {provider_id: {
        "npm": "@ai-sdk/openai-compatible",
        "name": GENERIC_PROVIDER_NAME,
        "options": {"baseURL": config.base_url, "apiKey": key},
        "models": {model_id: {}},
    }}


def write_run_json(path: Path, config: RunConfig | ValidateConfig | MatrixConfig,
                   provenance: Provenance, **sections: Any) -> None:
    """Write ``run.json``: command, config, provenance and ``sections``; never overwrites.

    ``sections`` are further top-level entries (JSON data). Raises ConfigError
    when the file exists.
    """
    document = {
        "schema": RUN_SCHEMA,
        "command": config.COMMAND,
        "config": config.to_dict(),
        "provenance": provenance.to_dict(),
        **sections,
    }
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError as exc:
        raise ConfigError(f"{path} already exists; choose a fresh output directory") from exc


def update_run_json(path: Path, **sections: Any) -> None:
    """Add or replace top-level ``sections`` of an existing ``run.json``, atomically.

    The schema, command, config and provenance written at the start are never replaced.
    """
    protected = sorted(set(sections) & {"schema", "command", "config", "provenance"})
    if protected:
        raise ConfigError(f"run.json sections {protected} are written once, at the start")
    document = json.loads(path.read_text(encoding="utf-8"))
    document.update(sections)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)

