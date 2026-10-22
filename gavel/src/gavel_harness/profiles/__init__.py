"""Benchmark and environment profiles: every per-benchmark difference as TOML data.

A benchmark profile (``profiles/<name>.toml``, e.g. ``paper/tb4``) selects the
paradigm, contract, evidence surface, install block, task.toml template,
budgets, intake policy and anchor judge environment of one benchmark. An
environment profile (``profiles/env/<name>.toml``) selects host-specific
Dockerfile rewrites; package-source mirrors appear only there. A profile is
named by its path under ``profiles/`` without ``.toml``, or given as the path
of a ``.toml`` file.

Benchmark profile keys (all required unless marked optional):

``description``
    One line saying what the profile reproduces.
``paradigm``
    Default paradigm of the profile's tasks.
``contract``
    Benchmark contract under ``method/prompts/contracts``.
``wording``
    Evidence header text of the generation prompt, ``state_gate`` or
    ``frozen_evh1`` (see :data:`gavel_harness.method.compose.Wording`).
``env``
    Default environment profile.
``package_prefix``
    Package directories are named ``<package_prefix>_<tid>``.
``install_block``, ``task_toml``
    Assets (under ``paradigms/assets``): the CLI install block appended to the
    generation Dockerfile, and the task.toml template.
``from_injection``
    ``first`` or ``final``: the ``FROM`` line a mirror block follows.
``[evidence]`` (optional)
    Judge-time evidence surface, reference = evidence type. Defaults to the
    paradigm's surface.
``[timeouts]``
    ``build_sec``, ``agent_sec``, ``verifier_sec`` of the generation package.
``[intake]``
    ``strip_tests``, ``allow_compose``, ``allow_mcp_servers``,
    ``allow_missing_gpus``: what the intake accepts (see
    :func:`gavel_harness.intake.sniff.sniff`).
``[anchor]``
    ``image``, ``workdir``, ``network``, ``timeout_sec``, ``swap``,
    ``keep_images``, optional ``user`` (omitted: the image's own ``USER``),
    ``network_reason`` (required for ``public``) and ``deliverables_subdir``
    (required for ``swap = "same_extension_deliverables"``); see
    :class:`~gavel_harness.paradigms.base.AnchorEnvironment`.
``[deliverable]`` (optional)
    ``dir``: the deliverable directory, used by the deliverable paradigm.
``[declare]`` (optional)
    ``verifier_timeout_sec``: the probe budget in declare mode. A profile
    without it does not support declare mode.
``[run]`` (optional)
    ``agent_exec_cap_sec``: the exec cap of the generation trials, the time
    limit of every agent command that sets none (see
    :func:`gavel_harness.run.generate`). Without it only the agent budget
    bounds the agent.

Environment profile keys: ``description``, and an optional ``[mirror]`` table
mapping a ``from_injection`` rule (``first``, ``final``) to the mirror block
asset inserted after that ``FROM`` line.

Unknown keys are an error everywhere.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from ..config import PARADIGMS
from ..errors import ConfigError
from ..method import compose
from ..method.compose import Wording
from ..paradigms.base import FROM_RULES, AnchorEnvironment, FromRule, Timeouts, asset_text

_ROOT = resources.files("gavel_harness.profiles")
_NAME = re.compile(r"[a-z0-9][a-z0-9_-]*(/[a-z0-9][a-z0-9_-]*)*")
_PREFIX = re.compile(r"[A-Za-z0-9_-]+")
_ENV_DIR = "env"


@dataclass(frozen=True)
class IntakePolicy:
    """What the intake accepts for a profile's tasks."""

    strip_tests: bool
    """Accept tasks that ship ``tests/``; the package never carries them."""
    allow_compose: bool
    """Accept tasks with a compose file; ``environment/`` is copied whole."""
    allow_mcp_servers: bool
    """Accept tasks that declare MCP servers; the package task.toml does not carry them."""
    allow_missing_gpus: bool
    """Accept tasks that request more GPUs than the host has; the package task.toml
    does not carry the request."""


@dataclass(frozen=True)
class Profile:
    """A loaded benchmark profile; field meanings are in the module docstring."""

    name: str
    """The shipped profile name, or the file name of a profile loaded from a path."""
    description: str
    paradigm: str
    contract: str
    wording: Wording
    env: str
    package_prefix: str
    install_block: str
    task_toml: str
    from_injection: FromRule
    judge_evidence: Mapping[str, str] | None
    timeouts: Timeouts
    intake: IntakePolicy
    anchor: AnchorEnvironment
    deliverable_dir: str | None
    declare_verifier_timeout_sec: float | None
    agent_exec_cap_sec: float | None


@dataclass(frozen=True)
class EnvProfile:
    """A loaded environment profile."""

    name: str
    description: str
    mirror: Mapping[str, str]
    """``from_injection`` rule -> mirror block asset; empty when nothing is rewritten."""

    def mirror_for(self, rule: str) -> str | None:
        """The mirror block asset for a ``from_injection`` rule, or None."""
        return self.mirror.get(rule)


def profile_names() -> tuple[str, ...]:
    """Names of the benchmark profiles shipped with the package, sorted."""
    return _names(exclude_env=True)


def env_names() -> tuple[str, ...]:
    """Names of the environment profiles shipped with the package, sorted."""
    return tuple(name.removeprefix(f"{_ENV_DIR}/") for name in _names(exclude_env=False)
                 if name.startswith(f"{_ENV_DIR}/"))


def load_profile(name: str | Path) -> Profile:
    """Load a benchmark profile by name or ``.toml`` path; raises ConfigError if invalid."""
    profile_name, label, data = _load(name, env=False)
    reader = _Reader(data, label)
    paradigm = reader.string("paradigm")
    if paradigm not in PARADIGMS:
        raise ConfigError(f"{label}: paradigm must be one of {PARADIGMS}, got {paradigm!r}")
    contract = reader.string("contract")
    _labelled(label, compose.contract_text, contract)
    wording = reader.string("wording")
    if wording not in compose.WORDINGS:
        raise ConfigError(f"{label}: wording must be one of {compose.WORDINGS}, got {wording!r}")
    env = reader.string("env")
    load_env(env)
    prefix = reader.string("package_prefix")
    if not _PREFIX.fullmatch(prefix):
        raise ConfigError(f"{label}: package_prefix must match [A-Za-z0-9_-]+, got {prefix!r}")
    install_block = reader.asset("install_block")
    task_toml = reader.asset("task_toml")
    from_injection = reader.string("from_injection")
    if from_injection not in FROM_RULES:
        raise ConfigError(f"{label}: from_injection must be one of {FROM_RULES}")

    judge_evidence = None
    if "evidence" in data:
        judge_evidence = reader.table("evidence").string_map()
        _labelled(label, compose.evidence_header, judge_evidence, wording=wording)

    timeouts_table = reader.table("timeouts")
    timeouts = _labelled(
        label, Timeouts,
        build_sec=timeouts_table.number("build_sec"),
        agent_sec=timeouts_table.number("agent_sec"),
        verifier_sec=timeouts_table.number("verifier_sec"),
    )
    timeouts_table.done()

    intake_table = reader.table("intake")
    intake = IntakePolicy(
        strip_tests=intake_table.boolean("strip_tests"),
        allow_compose=intake_table.boolean("allow_compose"),
        allow_mcp_servers=intake_table.boolean("allow_mcp_servers"),
        allow_missing_gpus=intake_table.boolean("allow_missing_gpus"),
    )
    intake_table.done()

    anchor_table = reader.table("anchor")
    anchor = _labelled(
        label, AnchorEnvironment,
        image=anchor_table.string("image"),
        workdir=anchor_table.string("workdir"),
        network=anchor_table.string("network"),
        timeout_sec=anchor_table.number("timeout_sec"),
        user=anchor_table.string("user", optional=True),
        network_reason=anchor_table.string("network_reason", optional=True),
        swap=anchor_table.string("swap"),
        deliverables_subdir=anchor_table.string("deliverables_subdir", optional=True),
        keep_images=anchor_table.boolean("keep_images"),
    )
    anchor_table.done()

    deliverable_dir = None
    if "deliverable" in data:
        deliverable_table = reader.table("deliverable")
        deliverable_dir = deliverable_table.string("dir")
        deliverable_table.done()

    declare_timeout = None
    if "declare" in data:
        declare_table = reader.table("declare")
        declare_timeout = declare_table.number("verifier_timeout_sec")
        declare_table.done()

    agent_exec_cap_sec = None
    if "run" in data:
        run_table = reader.table("run")
        agent_exec_cap_sec = run_table.number("agent_exec_cap_sec")
        run_table.done()
        if agent_exec_cap_sec <= 0:
            raise ConfigError(f"{label}: [run] agent_exec_cap_sec must be positive")

    description = reader.string("description")
    reader.done()
    return Profile(
        name=profile_name, description=description, paradigm=paradigm, contract=contract,
        wording=wording, env=env, package_prefix=prefix, install_block=install_block,
        task_toml=task_toml, from_injection=from_injection,
        judge_evidence=judge_evidence, timeouts=timeouts, intake=intake, anchor=anchor,
        deliverable_dir=deliverable_dir, declare_verifier_timeout_sec=declare_timeout,
        agent_exec_cap_sec=agent_exec_cap_sec,
    )


def load_env(name: str | Path) -> EnvProfile:
    """Load an environment profile by name or ``.toml`` path; raises ConfigError if invalid."""
    env_name, label, data = _load(name, env=True)
    reader = _Reader(data, label)
    description = reader.string("description")
    mirror: dict[str, str] = {}
    if "mirror" in data:
        mirror_table = reader.table("mirror")
        for rule in FROM_RULES:
            asset = mirror_table.asset(rule, optional=True)
            if asset is not None:
                mirror[rule] = asset
        mirror_table.done()
    reader.done()
    return EnvProfile(name=env_name, description=description, mirror=mirror)


def _labelled[T](label: str, check: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """``check(*args, **kwargs)``, with ``label`` prefixed to the message of a ConfigError."""
    try:
        return check(*args, **kwargs)
    except ConfigError as exc:
        raise ConfigError(f"{label}: {exc}") from exc


def _names(*, exclude_env: bool) -> tuple[str, ...]:
    names = []
    stack = [("", _ROOT)]
    while stack:
        prefix, node = stack.pop()
        for entry in node.iterdir():
            if entry.is_dir() and not entry.name.startswith(("_", ".")):
                stack.append((f"{prefix}{entry.name}/", entry))
            elif entry.is_file() and entry.name.endswith(".toml"):
                names.append(prefix + entry.name.removesuffix(".toml"))
    if exclude_env:
        names = [name for name in names if not name.startswith(f"{_ENV_DIR}/")]
    return tuple(sorted(names))


def _load(name: str | Path, *, env: bool) -> tuple[str, str, dict[str, Any]]:
    """Read a profile as ``(name, label, TOML data)``.

    A name ending in ``.toml`` is a file path; any other name is looked up
    among the shipped profiles (environment profiles under ``env/``). The
    returned name is the shipped name or the file's name (it is recorded in
    package identities, which hold no paths); the label, used in messages, is
    the shipped name or the file's path.
    """
    kind = "environment profile" if env else "profile"
    text_name = str(name)
    if text_name.endswith(".toml"):
        path = Path(text_name)
        if not path.is_file():
            raise ConfigError(f"{kind} file {path} does not exist")
        profile_name, label = path.name, str(path)
        source = path.read_text(encoding="utf-8")
    else:
        if not _NAME.fullmatch(text_name) or (not env and text_name.startswith(f"{_ENV_DIR}/")):
            raise ConfigError(f"malformed {kind} name {text_name!r}")
        entry = _ROOT.joinpath(*([_ENV_DIR] if env else []), *f"{text_name}.toml".split("/"))
        if not entry.is_file():
            known = env_names() if env else profile_names()
            raise ConfigError(f"no {kind} named {text_name!r}; available: {', '.join(known)}")
        profile_name = label = text_name
        source = entry.read_text(encoding="utf-8")
    try:
        return profile_name, label, tomllib.loads(source)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{kind} {label} is not valid TOML: {exc}") from exc


class _Reader:
    """Typed, exhaustive access to one TOML table; :meth:`done` rejects unread keys."""

    def __init__(self, data: Mapping[str, Any], where: str) -> None:
        self._data = data
        self._where = where
        self._seen: set[str] = set()

    def _get(self, key: str, optional: bool) -> Any:
        self._seen.add(key)
        if key not in self._data:
            if optional:
                return None
            raise ConfigError(f"{self._where}: missing key {key!r}")
        return self._data[key]

    def string(self, key: str, *, optional: bool = False) -> Any:
        value = self._get(key, optional)
        if value is not None and (not isinstance(value, str) or not value):
            raise ConfigError(f"{self._where}: {key} must be a non-empty string, got {value!r}")
        return value

    def number(self, key: str) -> float:
        value = self._get(key, False)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError(f"{self._where}: {key} must be a number, got {value!r}")
        return float(value)

    def boolean(self, key: str) -> bool:
        value = self._get(key, False)
        if not isinstance(value, bool):
            raise ConfigError(f"{self._where}: {key} must be true or false, got {value!r}")
        return value

    def asset(self, key: str, *, optional: bool = False) -> Any:
        value = self.string(key, optional=optional)
        if value is not None:
            try:
                asset_text(value)
            except ConfigError as exc:
                raise ConfigError(f"{self._where}: {key}: {exc}") from exc
        return value

    def table(self, key: str) -> _Reader:
        value = self._get(key, False)
        if not isinstance(value, dict):
            raise ConfigError(f"{self._where}: [{key}] must be a table")
        return _Reader(value, f"{self._where} [{key}]")

    def string_map(self) -> dict[str, str]:
        for key, value in self._data.items():
            self._seen.add(key)
            if not isinstance(value, str):
                raise ConfigError(f"{self._where}: {key} must be a string, got {value!r}")
        return dict(self._data)

    def done(self) -> None:
        unknown = sorted(set(self._data) - self._seen)
        if unknown:
            raise ConfigError(f"{self._where}: unknown key(s) {', '.join(unknown)}")
