"""Build sealed generation packages from input tasks.

:func:`build_packages` sniffs each input task, assembles its package with the
paradigm, seals it with its identity (``.veritas_build.json``) and writes two
manifests into the output directory:

* ``_runs.json``: one row per built package, a JSON list in the format of the
  upstream ``rebuild_packages`` output (``task_id``, ``package_dir``,
  ``inject_box_files``, ``contract_feedback_file``) with further keys
  (``paradigm``, ``profile``, ``env``, ``wording``, ``identity_sha256``,
  ``stripped_tests``, ``dropped_task_config``).
* ``refused.jsonl``: one line per refused task (``task_id``, ``task_dir``,
  ``reason``, ``message``); empty when nothing was refused.

A package directory that already exists is reused only when it was sealed
from exactly the same inputs; any other existing directory is an error, never
overwritten. A package is assembled in a hidden staging directory and moved
into place after sealing, so an interrupted build leaves no partial package.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..errors import ConfigError, RefusalError
from ..intake.sniff import TaskSpec, sniff
from ..method.compose import DEFAULT_SWITCHES, PromptSwitches
from ..method.identity import build_identity, identity_digest, seal_build, validate_cache
from ..paradigms.base import PackagePlan, Paradigm, get_paradigm
from ..profiles import EnvProfile, Profile, load_env, load_profile

RUNS_FILE = "_runs.json"
REFUSED_FILE = "refused.jsonl"


@dataclass(frozen=True)
class BuildResult:
    """Rows of one :func:`build_packages` call, in input order."""

    rows: tuple[dict[str, Any], ...]
    """One ``_runs.json`` row per built package."""
    refused: tuple[dict[str, Any], ...]
    """One ``refused.jsonl`` row per refused task."""


def resolve_plan(
    profile: Profile,
    env: EnvProfile,
    paradigm: Paradigm,
    *,
    switches: PromptSwitches = DEFAULT_SWITCHES,
    cli_extras: Sequence[str] = (),
    deliverable_dir: str | None = None,
) -> PackagePlan:
    """The package plan of ``paradigm`` under ``profile`` and ``env``, checked.

    ``deliverable_dir`` overrides the profile's ``[deliverable] dir``; both
    apply only to a paradigm with a deliverable directory. Raises ConfigError
    when the paradigm cannot build packages from the result.
    """
    if deliverable_dir is None and paradigm.default_deliverable_dir is not None:
        deliverable_dir = profile.deliverable_dir or paradigm.default_deliverable_dir
    plan = PackagePlan(
        profile=profile.name,
        env=env.name,
        contract=profile.contract,
        judge_evidence=profile.judge_evidence or paradigm.judge_evidence,
        package_prefix=profile.package_prefix,
        install_block=profile.install_block,
        task_toml=profile.task_toml,
        from_injection=profile.from_injection,
        mirror=env.mirror_for(profile.from_injection),
        cli_extras=tuple(cli_extras),
        timeouts=profile.timeouts,
        switches=switches,
        wording=profile.wording,
        deliverable_dir=deliverable_dir,
        declare_verifier_timeout_sec=profile.declare_verifier_timeout_sec,
    )
    paradigm.check_plan(plan)
    return plan


def build_packages(
    task_dirs: Sequence[str | Path],
    paradigm: str | None,
    profile: str | Path | Profile,
    out: str | Path,
    *,
    env: str | Path | None = None,
    root: str | Path | None = None,
    switches: PromptSwitches = DEFAULT_SWITCHES,
    cli_extras: Sequence[str] = (),
    deliverable_dir: str | None = None,
    replace_tests: bool = False,
) -> BuildResult:
    """Build the generation package of every task in ``task_dirs`` under ``out``.

    ``paradigm`` overrides the profile's paradigm when not None. ``env`` names
    the environment profile (default: the profile's ``env``). A task's id is
    its path relative to ``root`` when ``root`` is given (nested ids such as
    TB-Science's ``<field>/<subfield>/<task>``), else its directory name.
    ``replace_tests`` accepts tasks that ship ``tests/`` even when the profile
    does not strip them. ``switches``, ``cli_extras`` and ``deliverable_dir``
    are described at :class:`~gavel_harness.paradigms.base.PackagePlan`.

    Refused tasks are reported, not built; every other failure raises before
    ``_runs.json`` is written. Raises ConfigError for duplicate task ids or
    package names and for a task outside ``root``.
    """
    loaded = profile if isinstance(profile, Profile) else load_profile(profile)
    env_profile = load_env(env if env is not None else loaded.env)
    handler = get_paradigm(paradigm or loaded.paradigm)
    plan = resolve_plan(loaded, env_profile, handler, switches=switches,
                        cli_extras=cli_extras, deliverable_dir=deliverable_dir)
    out_dir = Path(out).absolute()

    named = _task_ids(task_dirs, root)
    package_names: dict[str, str] = {}
    for task_id, _ in named:
        name, _tid = handler.package_name(task_id, plan)
        if name in package_names:
            raise ConfigError(
                f"tasks {package_names[name]!r} and {task_id!r} map to one package {name!r}"
            )
        package_names[name] = task_id

    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    refused: list[dict[str, Any]] = []
    for task_id, task_dir in named:
        name, tid = handler.package_name(task_id, plan)
        try:
            task = sniff(
                task_dir,
                strip_tests=loaded.intake.strip_tests or replace_tests,
                allow_compose=loaded.intake.allow_compose,
                allow_mcp_servers=loaded.intake.allow_mcp_servers,
                allow_missing_gpus=loaded.intake.allow_missing_gpus,
            )
        except RefusalError as exc:
            refused.append({"task_id": task_id, "task_dir": str(task_dir),
                            "reason": str(exc.reason), "message": str(exc)})
            continue
        package_dir = out_dir / name
        digest = _build_one(handler, task, task_id, tid, package_dir, plan)
        rows.append({
            "task_id": task_id,
            "package_dir": str(package_dir),
            "inject_box_files": {},
            "contract_feedback_file": str(package_dir / "instruction.md"),
            "paradigm": handler.name,
            "profile": plan.profile,
            "env": plan.env,
            "wording": plan.wording,
            "identity_sha256": digest,
            "stripped_tests": task.strip_tests,
            "dropped_task_config": task.dropped_task_config,
        })

    _write_atomic(out_dir / RUNS_FILE, json.dumps(rows, indent=1))
    _write_atomic(out_dir / REFUSED_FILE,
                  "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in refused))
    return BuildResult(rows=tuple(rows), refused=tuple(refused))


def _task_ids(task_dirs: Sequence[str | Path], root: str | Path | None) -> list[tuple[str, Path]]:
    base = Path(os.path.abspath(root)) if root is not None else None
    named: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for entry in task_dirs:
        path = Path(os.path.abspath(entry))
        if base is None:
            task_id = path.name
        else:
            try:
                task_id = path.relative_to(base).as_posix()
            except ValueError as exc:
                raise ConfigError(f"task {path} is not inside the task root {base}") from exc
        if not task_id or task_id == ".":
            raise ConfigError(f"cannot derive a task id for {path}")
        if task_id in seen:
            raise ConfigError(f"task {task_id!r} is listed twice")
        seen.add(task_id)
        named.append((task_id, path))
    return named


def _build_one(handler: Paradigm, task: TaskSpec, task_id: str, tid: str,
               package_dir: Path, plan: PackagePlan) -> str:
    """Build (or reuse) one sealed package; return its identity digest."""
    sources: dict[str, Path] = {"upstream_instruction": task.task_dir / "instruction.md"}
    if task.env_kind == "dockerfile":
        sources["upstream_env"] = task.environment_dir
    sources.update(handler.code_sources())
    identity = build_identity(
        sources=sources,
        materials={"task_id": task_id, "image": task.image if task.env_kind == "image" else None},
        configuration=handler.configuration(task, plan),
    )
    if validate_cache(package_dir, identity):
        return identity_digest(identity)
    staging = Path(tempfile.mkdtemp(prefix=f".{package_dir.name}.", dir=package_dir.parent))
    try:
        built = staging / package_dir.name
        handler.package(task, tid, built, plan)
        digest = seal_build(built, identity)
        os.rename(built, package_dir)
    finally:
        shutil.rmtree(staging)
    return digest


def _write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
