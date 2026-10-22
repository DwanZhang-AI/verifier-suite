"""Build and run provenance: which code produced a result.

The harness commit comes from one of two places, never guessed:

- a source checkout (the package lives at ``<root>/src/gavel_harness`` and
  ``<root>/.git`` exists): ``git`` is asked for HEAD and for uncommitted changes;
- an installed wheel: ``_build_info.json``, written into the wheel at build time
  by ``hatch_build.py``.

A package with neither raises :class:`~gavel_harness.errors.ConfigError`.
"""

from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import asdict, dataclass
from importlib import metadata, resources
from pathlib import Path
from typing import Any, Literal

from . import __version__
from .errors import ConfigError

BUILD_INFO_NAME = "_build_info.json"
"""Name of the build-time provenance file inside the package."""


@dataclass(frozen=True)
class GitState:
    """HEAD and cleanliness of a git work tree.

    ``commit`` is None only when the repository has no commit yet. ``dirty``
    counts tracked modifications and untracked files that are not ignored.
    """

    commit: str | None
    dirty: bool


@dataclass(frozen=True)
class Provenance:
    """Everything a result row needs to name the code that produced it."""

    version: str
    commit: str | None
    dirty: bool
    source: Literal["checkout", "wheel"]
    harbor_version: str
    harbor_editable: bool
    harbor_commit: str | None
    """Harbor's VCS commit; recorded only when Harbor was installed from a git URL."""
    harbor_url: str | None
    """Where Harbor was installed from; None for an index install."""
    python: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def in_git_work_tree(root: Path) -> bool:
    """Whether ``root`` is the top of a git work tree or lies inside one."""
    return any((p / ".git").exists() for p in (root, *root.parents))


def read_git_state(root: Path) -> GitState:
    """Read HEAD and dirtiness of ``root`` in its git work tree.

    Only changes under ``root`` count, so a project kept inside a larger
    repository is not marked dirty by edits elsewhere in that repository.
    Raises ConfigError when git is missing or ``root`` is not in a work tree.
    """
    head = _git(root, "rev-parse", "--verify", "--quiet", "HEAD", check=False)
    status = _git(root, "status", "--porcelain", "--untracked-files=normal", "--", ".")
    return GitState(
        commit=head.stdout.strip() if head.returncode == 0 else None,
        dirty=bool(status.stdout.strip()),
    )


def checkout_root() -> Path | None:
    """Return the repository root when this package runs from a source checkout."""
    package_dir = Path(__file__).resolve().parent
    root = package_dir.parents[1]
    if package_dir == root / "src" / "gavel_harness" and in_git_work_tree(root):
        return root
    return None


def package_state() -> tuple[GitState, Literal["checkout", "wheel"]]:
    """Return the harness commit state and where it was read from."""
    root = checkout_root()
    if root is not None:
        return read_git_state(root), "checkout"
    info = resources.files("gavel_harness").joinpath(BUILD_INFO_NAME)
    if not info.is_file():
        raise ConfigError(
            f"{BUILD_INFO_NAME} is missing from the installed package and no source "
            "checkout was found; install from a git checkout or from a wheel built by "
            "this project's build backend"
        )
    data = json.loads(info.read_text(encoding="utf-8"))
    return GitState(commit=data["commit"], dirty=bool(data["dirty"])), "wheel"


def collect() -> Provenance:
    """Collect harness, Harbor and interpreter provenance for ``run.json``."""
    state, source = package_state()
    try:
        harbor = metadata.distribution("harbor")
    except metadata.PackageNotFoundError as exc:
        raise ConfigError("harbor is not installed; gavel-harness requires it") from exc
    direct_url_text = harbor.read_text("direct_url.json")
    direct_url: dict[str, Any] = json.loads(direct_url_text) if direct_url_text else {}
    return Provenance(
        version=__version__,
        commit=state.commit,
        dirty=state.dirty,
        source=source,
        harbor_version=harbor.version,
        harbor_editable=bool(direct_url.get("dir_info", {}).get("editable", False)),
        harbor_commit=direct_url.get("vcs_info", {}).get("commit_id"),
        harbor_url=direct_url.get("url"),
        python=platform.python_version(),
    )


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
        )
    except FileNotFoundError as exc:
        raise ConfigError("git is required to read provenance of a source checkout") from exc
    if check and result.returncode != 0:
        raise ConfigError(f"git {' '.join(args)} failed in {root}: {result.stderr.strip()}")
    return result
