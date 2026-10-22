"""Judge-harness Pi agent (VERITAS_HARNESS=pi; not used by the one-click suite).

Same salvage rule as JudgeOpenCode (the session's purpose is the judge artifact; if
the CLI errors after a non-empty artifact is on disk, treat the run as a success)
applied to Harbor's Pi agent. Install is skipped when a working pi is already baked
into the task image (an allowlisted network blocks npm), the same pre-baked-or-stock
pattern JudgeOpenCode uses.

Plug in via AgentConfig.import_path: "judge_pi:JudgePi".
pi model_name must be in provider/model form.
"""
from __future__ import annotations

import asyncio
import random
import subprocess
from typing import override

from harbor.agents.installed.base import NonZeroAgentExitCodeError
from harbor.agents.installed.pi import Pi
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

_SALVAGE_EXCEPTIONS = (
    NonZeroAgentExitCodeError,
    RuntimeError,
    TimeoutError,
    subprocess.TimeoutExpired,
)


class JudgePi(Pi):
    def __init__(self, *args, artifact_path: str = "/app/checker.py", **kwargs):
        super().__init__(*args, **kwargs)
        self._artifact_path = artifact_path

    @staticmethod
    @override
    def name() -> str:
        return "judge-pi"

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
                        "Pi errored (%s) but judge artifact %s exists — salvage.",
                        type(exc).__name__, self._artifact_path)
                    return
                if attempt == 0 and isinstance(exc, NonZeroAgentExitCodeError):
                    await asyncio.sleep(5 + random.random() * 25)
                    continue
                raise

    @override
    def _build_custom_models_json(self, access, model_id):
        # pi's default per-request max_tokens (16384) is too small for reasoning
        # models: they reason until the budget is spent, and the checker drafted inside
        # the reasoning stream is cut off (stopReason=length) before the file-write
        # turn. Raising the model's maxTokens gives the actual write room. Field
        # confirmed in pi's model-config.d.ts (maxTokens -> request max_tokens).
        mj = super()._build_custom_models_json(access, model_id)
        if mj:
            for prov in mj.get("providers", {}).values():
                for model in prov.get("models", []):
                    model["maxTokens"] = 32768
                    # reasoning=false: some models' reasoning is unbounded; even on the
                    # responses protocol one turn's reasoning can spend the whole output
                    # budget (-> incomplete.length), aborting the checker mid-write.
                    # Writing a checker.py is a mechanical task; turning reasoning off
                    # frees the budget for the actual answer/tool-call.
                    model["reasoning"] = False
        return mj

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        probe = await environment.exec(
            command=self.get_version_command() or "pi --version", timeout_sec=60)
        if probe.return_code == 0 and (probe.stdout or "").strip():
            self._version = self.parse_version(probe.stdout)
            return
        await super().install(environment)
