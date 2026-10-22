"""Judge-harness Codex agent (VERITAS_HARNESS=codex; not used by the one-click suite).

Same salvage rule as JudgeOpenCode (the session's purpose is the judge artifact; if
the CLI errors after a non-empty artifact is on disk, treat the run as a success)
applied to Harbor's Codex agent. Install is skipped when a working codex is already
baked into the task image (an allowlisted network blocks npm), the same
pre-baked-or-stock pattern JudgeOpenCode uses.

Plug in via AgentConfig.import_path: "judge_codex:JudgeCodex".
Point it at an OpenAI-compatible endpoint by setting OPENAI_BASE_URL in the agent env.
"""
from __future__ import annotations

import asyncio
import random
import subprocess
from typing import override

from harbor.agents.installed.base import NonZeroAgentExitCodeError
from harbor.agents.installed.codex import Codex
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

_SALVAGE_EXCEPTIONS = (
    NonZeroAgentExitCodeError,
    RuntimeError,
    TimeoutError,
    subprocess.TimeoutExpired,
)


class JudgeCodex(Codex):
    def __init__(self, *args, artifact_path: str = "/app/checker.py", **kwargs):
        super().__init__(*args, **kwargs)
        self._artifact_path = artifact_path

    @staticmethod
    @override
    def name() -> str:
        return "judge-codex"

    @override
    async def run(self, instruction: str, environment: BaseEnvironment,
                  context: AgentContext) -> None:
        for attempt in (0, 1):
            try:
                await super().run(instruction, environment, context)
                return
            except _SALVAGE_EXCEPTIONS as exc:
                probe = await environment.exec(
                    command=f"test -s {self._artifact_path}", timeout_sec=60)
                if probe.return_code == 0:
                    self.logger.warning(
                        "Codex errored (%s) but judge artifact %s exists — salvage.",
                        type(exc).__name__, self._artifact_path)
                    return
                if attempt == 0 and isinstance(exc, NonZeroAgentExitCodeError):
                    await asyncio.sleep(5 + random.random() * 25)
                    continue
                raise

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        probe = await environment.exec(
            command=self.get_version_command() or "codex --version", timeout_sec=60)
        if probe.return_code == 0 and (probe.stdout or "").strip():
            self._version = self.parse_version(probe.stdout)
            return
        await super().install(environment)
