"""Boundary check for directory copies that follow symlinks.

``shutil.copytree`` copies the target of a symlink, not the link. A link that
points outside the copied tree would therefore bring files from elsewhere into
the copy, such as a task's reference solution or a readable host file.
"""

from __future__ import annotations

import os
from pathlib import Path


def escaping_symlinks(root: str | Path) -> list[str]:
    """Relative paths of the symlinks under ``root`` that do not stay inside ``root``.

    Links are inspected without being followed. A link counts as escaping when its
    resolved target lies outside ``root``, when it cannot be resolved (dangling or
    looping), because a copy would follow it to an unknown place, or when it points
    at a directory that contains the link, which a copy would follow forever.
    ``root`` itself being a symlink is reported as ``"."``.
    """
    root = Path(root)
    if root.is_symlink():
        return ["."]
    base = root.resolve()
    found: list[str] = []
    for directory, dirs, names in os.walk(base, followlinks=False):
        for name in dirs + names:
            path = Path(directory) / name
            if not path.is_symlink():
                continue
            try:
                target = path.resolve(strict=True)
            except (OSError, RuntimeError):
                found.append(path.relative_to(base).as_posix())
                continue
            outside = target != base and base not in target.parents
            cycle = target.is_dir() and (target == path.parent or target in path.parents)
            if outside or cycle:
                found.append(path.relative_to(base).as_posix())
    return sorted(found)
