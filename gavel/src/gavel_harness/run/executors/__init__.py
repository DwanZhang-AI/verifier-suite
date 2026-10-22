"""Generation executors, loaded by Harbor through ``AgentConfig.import_path``.

The code of ``judge_opencode``, ``judge_codex`` and ``judge_pi`` is the upstream
harness executors' code (only comments and docstrings differ), recorded in
``UPSTREAM.lock``; change them only by re-running
``tools/extract_assets.py`` against a changed upstream. Each subclasses the Harbor
agent of the same CLI, e.g. ``gavel_harness.run.executors.judge_opencode:JudgeOpenCode``,
and differs from it in two ways: installation is skipped when the CLI already
answers ``--version`` in the container, and a run that raises is treated as
successful when ``artifact_path`` (default ``/app/checker.py``) is a non-empty file,
otherwise retried once in the same container after a 5-30 s random delay if the
first failure was a non-zero CLI exit.

``tagged`` wraps a verbatim executor so that each trial reaches the metering proxy
under its own tag and, when asked, each agent command ends at an exec cap as the
upstream transport cap ended it. ``registry.toml`` names the executors a run can
select; :func:`executor_spec` reads it.
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from types import MappingProxyType
from typing import Any

from ...errors import ConfigError

_REGISTRY = resources.files("gavel_harness.run.executors").joinpath("registry.toml")
_FIELDS = {"import_path", "cli_version", "endpoint_api", "config_kwarg", "env", "permission"}


@dataclass(frozen=True)
class ExecutorSpec:
    """One ``registry.toml`` entry: how Harbor loads an executor and what it needs."""

    name: str
    import_path: str
    """``module:Class`` of the agent Harbor instantiates."""
    cli_version: str
    """CLI version the packages pre-install."""
    endpoint_api: str
    """Model API the endpoint must serve."""
    config_kwarg: str
    """Agent keyword argument carrying the CLI configuration (provider and permission blocks)."""
    env: Mapping[str, str]
    """Environment of every agent command."""
    permission: Mapping[str, str]
    """The CLI's permission block."""


def executor_names() -> tuple[str, ...]:
    """Names of the executors in ``registry.toml``, sorted."""
    return tuple(sorted(_load()))


def executor_spec(name: str) -> ExecutorSpec:
    """The registry entry of executor ``name``; ConfigError when there is none."""
    registry = _load()
    if name not in registry:
        raise ConfigError(
            f"unknown executor {name!r}; available: {', '.join(sorted(registry))}"
        )
    return registry[name]


def _load() -> dict[str, ExecutorSpec]:
    data = tomllib.loads(_REGISTRY.read_text(encoding="utf-8"))
    specs = {}
    for name, entry in data.items():
        if not isinstance(entry, dict) or set(entry) != _FIELDS:
            raise ConfigError(
                f"registry.toml [{name}] must have exactly the keys {sorted(_FIELDS)}"
            )
        specs[name] = ExecutorSpec(
            name=name,
            import_path=_text(entry, name, "import_path"),
            cli_version=_text(entry, name, "cli_version"),
            endpoint_api=_text(entry, name, "endpoint_api"),
            config_kwarg=_text(entry, name, "config_kwarg"),
            env=_strings(entry, name, "env"),
            permission=_strings(entry, name, "permission"),
        )
    return specs


def _text(entry: Mapping[str, Any], name: str, key: str) -> str:
    value = entry[key]
    if not isinstance(value, str) or not value:
        raise ConfigError(f"registry.toml [{name}] {key} must be a non-empty string")
    return value


def _strings(entry: Mapping[str, Any], name: str, key: str) -> Mapping[str, str]:
    table = entry[key]
    if not isinstance(table, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in table.items()):
        raise ConfigError(f"registry.toml [{name}.{key}] must map names to strings")
    return MappingProxyType(dict(table))
