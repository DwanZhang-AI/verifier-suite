"""Write a generated verifier back into a copy of its task, as a runnable Harbor task.

:func:`write_back` writes ``<out_tasks>/<task_id>/``:

* everything of the input task except ``tests/``, ``solution/`` and
  ``task.toml``, copied unchanged; ``environment/`` is the input task's own, or
  the generation package's when the profile's anchors run in the packaged
  image, or empty for a task that runs a prebuilt image and has none (Harbor
  runs compose from that directory);
* ``task.toml``: the input task's own file with ``[verifier]`` set to the
  anchor judge environment (see :func:`merge_task_toml`);
* ``solution/``: the reference solution, when there is one;
* ``tests/test.sh``: the bridge (``veritas-bridge/1``), which stages the
  verifier, runs it and writes the raw exit status to
  ``/logs/verifier/veritas_verdict.json`` and the Harbor reward (1 for exit 0,
  else 0) to ``reward.txt``, after removing any reward or verdict file already
  present;
* ``tests/veritas/verifier.sh``: the generated verifier, byte for byte;
* ``tests/veritas/provenance.json``: the caller's provenance with the verifier
  sha256, the bridge version and the anchor settings.

The bridge serves the paradigms judged by exit status (terminal_state,
deliverable), whose verifier lives at ``/app/verifier.sh``. The input task is
only read. The written task is assembled in a hidden staging directory and
moved into place when complete; an existing destination is never overwritten.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shlex
import shutil
import tempfile
import tomllib
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from importlib import resources
from pathlib import Path, PurePosixPath
from typing import Any

from harbor.models.task.config import TaskConfig, TaskOS
from harbor.models.task.verifier_mode import VerifierEnvironmentMode, resolve_task_verifier_mode
from harbor.utils.scripts import discover_script
from pydantic import ValidationError

from ..errors import ConfigError
from ..paradigms.base import AnchorEnvironment
from ..paradigms.terminal_state import TerminalState

AnchorSettings = AnchorEnvironment
"""The anchor judge environment of a profile (its ``[anchor]`` table)."""

BRIDGE_VERSION = "veritas-bridge/1"
WRITEBACK_SCHEMA = "gavel-harness/writeback/1"
VERDICT_FILE = "veritas_verdict.json"
"""File name, under the verifier log directory, of the bridge's raw verdict."""
VERIFIER_FILE = PurePosixPath("tests/veritas/verifier.sh")
PROVENANCE_FILE = PurePosixPath("tests/veritas/provenance.json")
BRIDGE_FILE = PurePosixPath("tests/test.sh")

_BRIDGE_ASSET = resources.files("gavel_harness.export").joinpath(
    "assets", "bridge_exit_code.sh")
_BRIDGE_SLOTS = ("@WORKDIR@", "@VERIFIER@")
_REPLACED_ROOT_ENTRIES = ("tests", "solution", "task.toml", "environment")
_TASK_ID_PART = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")

_MANAGED_KEYS = ("timeout_sec", "environment_mode", "network_mode", "allowed_hosts", "user",
                 "environment")
"""``[verifier]`` keys the write-back owns; ``environment`` covers inline tables."""
_HEADER = re.compile(r"^\s*(\[\[?)([^\[\]]+?)(\]\]?)\s*(#.*)?$")
_KEY_PART = re.compile(r'\s*(?:"((?:[^"\\]|\\.)*)"|\'([^\']*)\'|([A-Za-z0-9_-]+))\s*')
_MANAGED_LINE = re.compile(rf"^\s*({'|'.join(_MANAGED_KEYS)})\s*=(.*)$", re.S)


@dataclass(frozen=True)
class WrittenTask:
    """A task written back by :func:`write_back`."""

    task_id: str
    task_dir: Path
    """The written-back Harbor task."""
    oracle_dir: Path | None
    """The reference solution the oracle anchor stages, or None when the task has none."""
    verifier_sha256: str


def render_bridge(workdir: str) -> str:
    """The bridge ``tests/test.sh`` running the verifier from ``workdir``."""
    text = _BRIDGE_ASSET.read_text(encoding="utf-8")
    values = (shlex.quote(workdir), shlex.quote(TerminalState.artifact_path))
    for slot, value in zip(_BRIDGE_SLOTS, values, strict=True):
        if text.count(slot) != 1:
            raise ConfigError(f"bridge asset must carry {slot} exactly once")
        text = text.replace(slot, value)
    return text


def solution_deliverables(solution_dir: Path, subdir: str) -> list[tuple[str, int]]:
    """The deliverable files of a reference solution as ``(relative path, bytes)``.

    Deliverables are the regular files (symlinks excluded) anywhere under
    ``<solution_dir>/<subdir>``, with POSIX paths relative to that directory,
    sorted by path. A missing directory has none.
    """
    root = solution_dir / subdir
    if not root.is_dir():
        return []
    found = []
    for directory, dirs, names in os.walk(root):
        dirs.sort()
        for name in names:
            path = Path(directory) / name
            if path.is_file() and not path.is_symlink():
                found.append((path.relative_to(root).as_posix(), path.stat().st_size))
    return sorted(found)


def merge_task_toml(text: str | None, settings: AnchorSettings) -> str:
    """The task's own task.toml with ``[verifier]`` set to the anchor judge environment.

    ``text`` is the task's task.toml, or None when it has none. In ``[verifier]``,
    ``timeout_sec`` becomes the anchor cap, ``environment_mode`` is ``shared``
    (the verifier judges the container the agent worked in), ``network_mode`` is
    the anchor network and ``user`` the anchor user (removed when the anchors run
    as the image's own user); ``allowed_hosts`` and ``[verifier.environment]``
    (with its sub-tables) are removed. Every other line is kept byte for byte.

    The result is checked by parsing it: it must equal the input's data with
    exactly these changes and be a valid Harbor task configuration. A layout
    the line edit cannot handle (``verifier`` as an inline table or as dotted
    keys outside ``[verifier]``) raises ConfigError.
    """
    try:
        original = tomllib.loads(text or "")
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"task.toml does not parse: {exc}") from exc
    values = _verifier_values(settings)
    expected = copy.deepcopy(original)
    verifier = expected.setdefault("verifier", {})
    if not isinstance(verifier, dict):
        raise ConfigError("task.toml: verifier is not a table")
    for key in _MANAGED_KEYS:
        verifier.pop(key, None)
    verifier.update(values)

    managed = ["# anchor judge environment, set by gavel-harness write-back\n"]
    managed += [f"{key} = {_toml_value(value)}\n" for key, value in values.items()]
    out: list[str] = []
    section: tuple[str, ...] = ()
    dropping_section = False
    depth = 0
    wrote_verifier = False
    for line in (text or "").splitlines(keepends=True):
        if depth > 0:
            depth += _nesting(line)
            continue
        header = _header(line)
        if header is not None:
            section, is_array = header
            dropping_section = section[:2] == ("verifier", "environment")
            if dropping_section:
                continue
            out.append(line if line.endswith("\n") else line + "\n")
            if section == ("verifier",) and not is_array:
                out.extend(managed)
                wrote_verifier = True
            continue
        if dropping_section:
            continue
        if section == ("verifier",):
            match = _MANAGED_LINE.match(line)
            if match is not None:
                depth = max(0, _nesting(match.group(2)))
                continue
        out.append(line)
    if not wrote_verifier:
        if out and not out[-1].endswith("\n"):
            out[-1] += "\n"
        out.extend(["\n" if out else "", "[verifier]\n", *managed])
    merged = "".join(out)

    try:
        parsed = tomllib.loads(merged)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"cannot rewrite this task.toml layout: {exc}") from exc
    if parsed != expected:
        raise ConfigError(
            "cannot rewrite this task.toml layout: the [verifier] table is not a plain "
            "[verifier] section (inline table or dotted keys)"
        )
    try:
        config = TaskConfig.model_validate(parsed)
    except ValidationError as exc:
        raise ConfigError(f"the written-back task.toml is not a Harbor task: {exc}") from exc
    if resolve_task_verifier_mode(config) != VerifierEnvironmentMode.SHARED:
        raise ConfigError("the written-back task.toml does not resolve to shared verifier mode")
    return merged


def write_back(
    task_src: Path,
    verifier_sh: Path,
    out_tasks: Path,
    *,
    settings: AnchorSettings,
    provenance: Mapping[str, object],
    oracle_dir: Path | None,
    environment_dir: Path | None = None,
) -> WrittenTask:
    """Write ``verifier_sh`` back into a copy of ``task_src`` at ``out_tasks/<task_id>``.

    ``provenance`` is JSON data recorded in ``tests/veritas/provenance.json``;
    its ``task_id`` (the run's id of the task, a relative path for nested ids)
    names the written directory. ``oracle_dir`` is the task's reference
    solution, which must hold a solve script; it is copied to ``solution/``.
    When ``settings.deliverables_subdir`` is set, a solution without deliverable
    files there is no oracle (nothing to hand in) and is not copied.
    ``environment_dir`` is the generation package's ``environment/``: required
    when ``settings.image`` is ``packaged``, refused otherwise.

    Raises ConfigError for a missing or empty verifier, an invalid task id, an
    existing destination, a solution without solve script, or a task.toml the
    merge cannot rewrite. ``task_src`` is never modified.
    """
    task_src = Path(task_src)
    if not task_src.is_dir():
        raise ConfigError(f"not a task directory: {task_src}")
    task_id = _task_id(provenance)
    verifier_sh = Path(verifier_sh)
    verifier = verifier_sh.read_bytes() if verifier_sh.is_file() else b""
    if not verifier:
        raise ConfigError(f"verifier {verifier_sh} is missing or empty")
    verifier_sha256 = hashlib.sha256(verifier).hexdigest()
    env_source = _environment_source(task_src, settings, environment_dir)
    toml_path = task_src / "task.toml"
    task_toml = merge_task_toml(
        toml_path.read_text(encoding="utf-8") if toml_path.is_file() else None, settings)
    task_os = TaskConfig.model_validate_toml(task_toml).environment.os
    oracle = _oracle_source(oracle_dir, settings, task_os)
    bridge = render_bridge(settings.workdir)
    record = {
        "schema": WRITEBACK_SCHEMA,
        "task_id": task_id,
        "bridge": BRIDGE_VERSION,
        "verifier_sha256": verifier_sha256,
        "oracle": oracle is not None,
        "anchor": asdict(settings),
        "provenance": dict(provenance),
    }
    try:
        record_text = json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n"
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"provenance must be JSON data: {exc}") from exc

    destination = Path(out_tasks).absolute() / task_id
    if destination.exists() or destination.is_symlink():
        raise ConfigError(f"{destination} exists; write back into a fresh output directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        built = staging / destination.name
        shutil.copytree(task_src, built, symlinks=True,
                        ignore=lambda directory, names: _root_ignored(task_src, directory, names))
        if env_source is not None:
            shutil.copytree(env_source, built / "environment", symlinks=True)
        else:
            (built / "environment").mkdir()
        if oracle is not None:
            shutil.copytree(oracle, built / "solution", symlinks=True)
        (built / "task.toml").write_text(task_toml, encoding="utf-8")
        _write(built / BRIDGE_FILE, bridge.encode("utf-8"), 0o755)
        _write(built / VERIFIER_FILE, verifier, 0o755)
        _write(built / PROVENANCE_FILE, record_text.encode("utf-8"), 0o644)
        os.rename(built, destination)
    finally:
        shutil.rmtree(staging)
    return WrittenTask(
        task_id=task_id,
        task_dir=destination,
        oracle_dir=destination / "solution" if oracle is not None else None,
        verifier_sha256=verifier_sha256,
    )


def _verifier_values(settings: AnchorSettings) -> dict[str, Any]:
    values: dict[str, Any] = {
        "timeout_sec": float(settings.timeout_sec),
        "environment_mode": VerifierEnvironmentMode.SHARED.value,
        "network_mode": settings.network,
    }
    if settings.user is not None:
        values["user"] = settings.user
    return values


def _toml_value(value: Any) -> str:
    if isinstance(value, float):
        return repr(value)
    return json.dumps(value, ensure_ascii=False)


def _header(line: str) -> tuple[tuple[str, ...], bool] | None:
    """``(key, is_array)`` of a table header line (``[a.b]`` or ``[[a.b]]``), or None."""
    match = _HEADER.match(line)
    if match is None or len(match.group(1)) != len(match.group(3)):
        return None
    parts: list[str] = []
    for chunk in _split_key(match.group(2)):
        part = _KEY_PART.fullmatch(chunk)
        if part is None:
            return None
        parts.append(next(group for group in part.groups() if group is not None))
    return tuple(parts), len(match.group(1)) == 2


def _split_key(key: str) -> list[str]:
    """``key`` split at the dots outside quotes."""
    chunks, current, quote = [], "", ""
    for char in key:
        if quote:
            current += char
            if char == quote:
                quote = ""
        elif char in "\"'":
            quote = char
            current += char
        elif char == ".":
            chunks.append(current)
            current = ""
        else:
            current += char
    chunks.append(current)
    return chunks


def _nesting(text: str) -> int:
    """Open minus closed brackets and braces in ``text``, outside strings and comments."""
    depth, quote = 0, ""
    for char in text:
        if quote:
            if char == quote:
                quote = ""
        elif char in "\"'":
            quote = char
        elif char == "#":
            break
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
    return depth


def check_task_id(task_id: str) -> str:
    """Return ``task_id``; ConfigError unless it can name a written-back task directory.

    A task id is a relative path whose ``/``-separated parts each match
    ``[A-Za-z0-9_][A-Za-z0-9_.-]*``.
    """
    parts = task_id.split("/") if isinstance(task_id, str) else [None]
    if not all(isinstance(part, str) and _TASK_ID_PART.fullmatch(part) for part in parts):
        raise ConfigError(f"task id {task_id!r} is not a relative path of plain names")
    return task_id


def _task_id(provenance: Mapping[str, object]) -> str:
    task_id = provenance.get("task_id")
    if not isinstance(task_id, str):
        raise ConfigError("provenance must carry the task's id as a string under 'task_id'")
    return check_task_id(task_id)


def _environment_source(task_src: Path, settings: AnchorSettings,
                        environment_dir: Path | None) -> Path | None:
    if settings.image == "packaged":
        if environment_dir is None or not Path(environment_dir).is_dir():
            raise ConfigError(
                "anchors run in the packaged image: pass the generation package's "
                f"environment/ directory (got {environment_dir})"
            )
        return Path(environment_dir)
    if environment_dir is not None:
        raise ConfigError(
            "anchors run in the task's own image; a package environment does not apply"
        )
    own = task_src / "environment"
    return own if own.is_dir() else None


def _oracle_source(oracle_dir: Path | None, settings: AnchorSettings,
                   task_os: TaskOS) -> Path | None:
    if oracle_dir is None:
        return None
    oracle_dir = Path(oracle_dir)
    if not oracle_dir.is_dir():
        raise ConfigError(f"reference solution {oracle_dir} is not a directory")
    if discover_script(oracle_dir, "solve", task_os=task_os) is None:
        raise ConfigError(f"reference solution {oracle_dir} has no solve script")
    subdir = settings.deliverables_subdir
    if subdir is not None and not solution_deliverables(oracle_dir, subdir):
        return None
    return oracle_dir


def _root_ignored(task_src: Path, directory: str, names: list[str]) -> list[str]:
    if Path(directory) != task_src:
        return []
    return [name for name in names if name in _REPLACED_ROOT_ENTRIES]


def _write(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(mode)
