#!/usr/bin/env python3
"""OpenHands with probe-skip install (same pattern as JudgeOpenCode/JudgeCodex).

Not used by the one-click suite. The stock adapter re-runs its uv install
unconditionally; on an image with a pre-baked venv (openhands-ai==0.62.0) the
re-install collides with the existing venv ("Failed to create virtual
environment"). Probe first; only fall back to stock install without the baked
venv."""
from typing import override

from harbor.agents.installed.openhands import OpenHands
from harbor.environments.base import BaseEnvironment


class JudgeOpenHands(OpenHands):
    @override
    async def install(self, environment: BaseEnvironment) -> None:
        probe = await environment.exec(
            command=self.get_version_command(), timeout_sec=120)
        if probe.return_code == 0 and (probe.stdout or "").strip():
            self._version = self.parse_version(probe.stdout)
            return
        await super().install(environment)
