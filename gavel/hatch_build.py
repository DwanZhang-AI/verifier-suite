"""Build hook: record the harness commit in ``gavel_harness/_build_info.json``.

From a git checkout, wheels and sdists get the current HEAD and dirty flag. A
wheel built from an unpacked sdist reuses the file the sdist already carries.
Editable installs skip the file: they read git state at run time. Building
without either source of truth fails instead of shipping an unattributed package.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class BuildInfoHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        if version == "editable":
            return
        root = Path(self.root)
        in_tree = root / "src" / "gavel_harness" / "_build_info.json"
        if not any((p / ".git").exists() for p in (root, *root.parents)):
            if in_tree.is_file():
                return
            raise RuntimeError(
                "cannot attribute this build: no git checkout and no "
                "src/gavel_harness/_build_info.json"
            )
        if in_tree.exists():
            raise RuntimeError(f"remove stray {in_tree}; the build hook generates it")

        sys.path.insert(0, str(root / "src"))
        from gavel_harness.provenance import BUILD_INFO_NAME, read_git_state

        state = read_git_state(root)
        if state.commit is None:
            raise RuntimeError("cannot attribute this build: the repository has no commit yet")
        self._tmp = Path(tempfile.mkdtemp(prefix="gavel-build-info-"))
        info = self._tmp / BUILD_INFO_NAME
        info.write_text(json.dumps({"commit": state.commit, "dirty": state.dirty}) + "\n")
        package_dir = "gavel_harness" if self.target_name == "wheel" else "src/gavel_harness"
        build_data["force_include"][str(info)] = f"{package_dir}/{BUILD_INFO_NAME}"

    def finalize(self, version: str, build_data: dict[str, Any], artifact_path: str) -> None:
        tmp = getattr(self, "_tmp", None)
        if tmp is not None:
            shutil.rmtree(tmp)
