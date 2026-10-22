"""Parse one Harbor task directory into a :class:`TaskSpec`, or refuse it.

A supported input is a single-step Harbor task whose main container is
Linux, built from ``environment/Dockerfile`` or pulled from
``[environment].docker_image``, with no compose file and no MCP servers unless
the caller allows them. task.toml is parsed with Harbor's own ``TaskConfig``.
Every other input raises :class:`RefusalError` with a :class:`RefusalReason`;
nothing is skipped silently. Sniffing only reads the task directory.
"""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from harbor.models.environment_type import EnvironmentType
from harbor.models.task.config import EnvironmentConfig, TaskConfig, TaskOS
from harbor.models.task.paths import TaskPaths
from pydantic import BaseModel, ValidationError

from ..errors import ConfigError, RefusalError, RefusalReason
from ..fsguard import escaping_symlinks

EnvKind = Literal["dockerfile", "image"]

COMPOSE_FILE_NAMES = ("docker-compose.yaml", "docker-compose.yml", "compose.yaml", "compose.yml")
"""Compose file names looked for in the task root and in ``environment/``."""

_PROVIDER_SECTIONS = frozenset(
    member.value for member in EnvironmentType if member is not EnvironmentType.DOCKER
) - set(EnvironmentConfig.model_fields)
# TaskConfig ignores unknown keys, so a provider-specific [environment.<type>]
# table would pass validation unseen; these names come from Harbor's own list.

_DROPPED_FIELDS: dict[str, tuple[str, ...]] = {
    "environment": (
        "env",
        "mcp_servers",
        "cpus",
        "memory_mb",
        "storage_mb",
        "gpus",
        "gpu_types",
        "workdir",
        "healthcheck",
        "network_mode",
        "allowed_hosts",
        "skills_dir",
        "build_timeout_sec",
    ),
    "agent": ("timeout_sec", "user", "network_mode", "allowed_hosts"),
}
# The generation package carries a fixed task.toml (upstream adapter template),
# so these settings of the input task do not reach the generation trial.
_EMPTY_SETTINGS: tuple[Any, ...] = (None, 0, "", [], {})
# An empty setting (e.g. ``gpus = 0``, ``[environment.env]`` with no keys) asks
# for nothing, so dropping it changes nothing.

_NVIDIA_DEVICE = re.compile(r"nvidia\d+")


@dataclass(frozen=True)
class TaskSpec:
    """One accepted input task.

    ``name`` is ``[task].name`` when task.toml declares it, else the directory
    name (Harbor's rule). ``instruction`` is instruction.md read as UTF-8 text
    and otherwise unmodified (no canary stripping): the package builder copies
    it verbatim, as the upstream adapters do.

    ``env_kind`` is ``"dockerfile"`` whenever ``environment/Dockerfile`` exists,
    even if task.toml also names a ``docker_image``: the generation package
    builds the Dockerfile (upstream adapter rule), whereas Harbor on its own
    would pull the image. ``image`` is ``[environment].docker_image`` as
    declared, or None.

    ``compose_files`` lists the compose files found (task-relative POSIX
    paths); it is non-empty only when the caller allowed compose.
    ``strip_tests`` is True when the input ships ``tests/`` and the caller asked
    for them to be stripped; the input directory itself is left untouched.
    ``dropped_task_config`` maps ``"<section>.<field>"`` to every non-empty
    task.toml setting that differs from Harbor's default and that the
    generation package does not carry; the run writes it to the task's result
    row.
    """

    task_dir: Path
    name: str
    instruction: str
    env_kind: EnvKind
    image: str | None
    compose_files: tuple[str, ...]
    has_tests: bool
    has_solution: bool
    gpus: int
    strip_tests: bool
    dropped_task_config: dict[str, Any]
    config: TaskConfig

    @property
    def environment_dir(self) -> Path:
        """The task's ``environment/`` directory (the build context for ``dockerfile``)."""
        return self.task_dir / "environment"


def sniff(
    task_dir: str | Path,
    *,
    strip_tests: bool = False,
    allow_compose: bool = False,
    allow_mcp_servers: bool = False,
    allow_missing_gpus: bool = False,
    host_gpus: int | None = None,
) -> TaskSpec:
    """Parse ``task_dir`` into a :class:`TaskSpec`, or raise :class:`RefusalError`.

    ``strip_tests`` accepts a task that already ships ``tests/`` (otherwise
    refused with ``has_tests``). ``allow_compose`` accepts compose files
    (otherwise refused with ``compose``): the upstream TB4 adapter packaged such
    tasks with ``environment/`` copied whole, and Harbor's docker environment
    merges ``environment/docker-compose.yaml`` into its own.
    ``allow_mcp_servers`` accepts declared MCP servers (otherwise refused with
    ``mcp_servers``); like the upstream adapters' fixed task.toml, the
    generation package does not carry them, and ``dropped_task_config`` lists
    them. ``allow_missing_gpus`` accepts a task that requests more GPUs than
    the host offers (otherwise refused with ``gpu_unavailable``); like the
    upstream TB adapters' fixed task.toml, the generation package does not carry
    the request, and ``dropped_task_config`` lists it. ``host_gpus`` is the
    number of GPUs the host offers; None counts them with
    :func:`host_gpu_count`, and only when the task requests GPUs and missing
    GPUs are not allowed.

    When several refusal reasons apply, the first in this order is raised:
    compose, toml_error, multi_step, mcp_servers, windows, remote_env,
    no_environment, no_instruction, gpu_unavailable, has_tests.

    Raises ConfigError when ``task_dir`` is not a directory.
    """
    paths = TaskPaths(task_dir)
    root = paths.task_dir
    if not root.is_dir():
        raise ConfigError(f"not a task directory: {root}")

    compose_files = tuple(
        candidate.relative_to(root).as_posix()
        for base in (root, paths.environment_dir)
        for name in COMPOSE_FILE_NAMES
        if (candidate := base / name).is_file()
    )
    if compose_files and not allow_compose:
        raise RefusalError(
            RefusalReason.COMPOSE,
            f"{', '.join(compose_files)} defines a multi-container environment",
        )

    config, providers = _load_config(paths)
    environment = config.environment
    if config.steps:
        raise RefusalError(
            RefusalReason.MULTI_STEP,
            f"task.toml declares {len(config.steps)} [[steps]]; "
            "only single-step tasks are supported",
        )
    if environment.mcp_servers and not allow_mcp_servers:
        names = ", ".join(server.name for server in environment.mcp_servers)
        raise RefusalError(RefusalReason.MCP_SERVERS, f"task.toml declares MCP servers: {names}")
    if environment.os == TaskOS.WINDOWS:
        raise RefusalError(
            RefusalReason.WINDOWS,
            "[environment].os is 'windows'; only Linux containers are supported",
        )
    if providers:
        raise RefusalError(
            RefusalReason.REMOTE_ENV,
            f"[environment] configures remote provider(s) {', '.join(providers)}; "
            "tasks run in Harbor's docker environment",
        )
    if environment.tpu is not None:
        raise RefusalError(
            RefusalReason.REMOTE_ENV,
            f"[environment.tpu] requests a {environment.tpu.type} {environment.tpu.topology} "
            "TPU slice; only remote providers allocate TPUs",
        )

    env_kind = _environment_kind(paths, environment.docker_image)
    if env_kind == "dockerfile":
        escaping = escaping_symlinks(paths.environment_dir)
        if escaping:
            raise RefusalError(
                RefusalReason.ESCAPING_SYMLINK,
                "environment/ has symlinks that point outside it: " + ", ".join(escaping[:5]),
            )
    instruction = _read_instruction(paths)

    gpus = environment.gpus or 0
    if gpus > 0 and not allow_missing_gpus:
        available = host_gpu_count() if host_gpus is None else host_gpus
        if gpus > available:
            raise RefusalError(
                RefusalReason.GPU_UNAVAILABLE,
                f"the task requests {gpus} GPU(s); this host has {available}",
            )

    has_tests = paths.tests_dir.is_dir()
    if has_tests and not strip_tests:
        raise RefusalError(
            RefusalReason.HAS_TESTS,
            "the task already ships tests/; it is accepted only when tests/ are stripped "
            "(--replace-tests, or a profile that strips them)",
        )

    return TaskSpec(
        task_dir=root,
        name=config.task.name if config.task is not None else root.name,
        instruction=instruction,
        env_kind=env_kind,
        image=environment.docker_image or None,
        compose_files=compose_files,
        has_tests=has_tests,
        has_solution=paths.discovered_solve_path_for(environment.os) is not None,
        gpus=gpus,
        strip_tests=has_tests and strip_tests,
        dropped_task_config=_dropped_task_config(config, env_kind),
        config=config,
    )


def host_gpu_count(device_dir: Path = Path("/dev")) -> int:
    """Count the NVIDIA GPU device nodes (``nvidia<N>``) in ``device_dir``.

    Only NVIDIA devices are counted. Whether the container runtime can pass
    them into a container is not checked here.
    """
    try:
        names = os.listdir(device_dir)
    except FileNotFoundError:
        return 0
    return sum(1 for name in names if _NVIDIA_DEVICE.fullmatch(name))


def _load_config(paths: TaskPaths) -> tuple[TaskConfig, list[str]]:
    """Parse task.toml with Harbor's ``TaskConfig``; a missing file means Harbor's defaults.

    Also returns the sorted provider sections found in ``[environment]``, which
    ``TaskConfig`` itself ignores. Raises ``toml_error`` when the file is not
    UTF-8 TOML or does not match Harbor's task schema.
    """
    if not paths.config_path.is_file():
        return TaskConfig(), []
    try:
        raw = tomllib.loads(paths.config_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise RefusalError(RefusalReason.TOML_ERROR, f"task.toml does not parse: {exc}") from exc
    environment = raw.get("environment")
    providers = (
        sorted(_PROVIDER_SECTIONS & set(environment)) if isinstance(environment, dict) else []
    )
    try:
        config = TaskConfig.model_validate(raw)
    except ValidationError as exc:
        raise RefusalError(
            RefusalReason.TOML_ERROR, f"task.toml does not match Harbor's task schema: {exc}"
        ) from exc
    return config, providers


def _environment_kind(paths: TaskPaths, docker_image: str | None) -> EnvKind:
    if (paths.environment_dir / "Dockerfile").is_file():
        return "dockerfile"
    if docker_image:
        return "image"
    raise RefusalError(
        RefusalReason.NO_ENVIRONMENT,
        "neither environment/Dockerfile nor [environment].docker_image is present",
    )


def _read_instruction(paths: TaskPaths) -> str:
    path = paths.instruction_path
    if not path.is_file():
        raise RefusalError(RefusalReason.NO_INSTRUCTION, "instruction.md is missing")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise RefusalError(
            RefusalReason.NO_INSTRUCTION, f"instruction.md is not UTF-8 text: {exc}"
        ) from exc
    if not text.strip():
        raise RefusalError(RefusalReason.NO_INSTRUCTION, "instruction.md is empty")
    return text


def _dropped_task_config(config: TaskConfig, env_kind: EnvKind) -> dict[str, Any]:
    dropped: dict[str, Any] = {}
    for section_name, names in _DROPPED_FIELDS.items():
        section: BaseModel = getattr(config, section_name)
        current = section.model_dump(mode="json", include=set(names))
        default = type(section)().model_dump(mode="json", include=set(names))
        for name in names:
            value = current[name]
            if value != default[name] and value not in _EMPTY_SETTINGS:
                dropped[f"{section_name}.{name}"] = value
    if env_kind == "dockerfile" and config.environment.docker_image:
        dropped["environment.docker_image"] = config.environment.docker_image
    return dropped
