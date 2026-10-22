"""Judge-harness Pi agent: Harbor's Pi with the JudgeOpenCode salvage.

The purpose of the session is the judge artifact; if the CLI errors after a
non-empty artifact is on disk, the run counts as a success. The install is
skipped when the image already has a working pi, as in JudgeOpenCode.

Plug in via AgentConfig.import_path: "judge_pi:JudgePi".
Configure the endpoint through pi's provider config (model_name in provider/model form).
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
        # pi's default per-request max_tokens (16384) is too small for GLM-5-2: it
        # reasons until the budget is spent, and the checker it drafts inside the
        # reasoning stream is cut off (stopReason=length) before the file-write turn;
        # --thinking low does not help, as GLM ignores it. Raising the model's
        # maxTokens leaves room for the write. The field is maxTokens in pi's
        # model-config.d.ts (maxTokens: TOptional<TNumber> -> request max_tokens).
        mj = super()._build_custom_models_json(access, model_id)
        if mj:
            for prov in mj.get("providers", {}).values():
                for model in prov.get("models", []):
                    model["maxTokens"] = 32768
                    # reasoning=false: GLM-5-2's reasoning is unbounded; even on the
                    # responses protocol it can spend the whole output budget on one
                    # turn's reasoning (reasoning==output==32768 -> incomplete.length)
                    # and stop the checker mid-write. Writing a checker.py is a
                    # mechanical task; turning reasoning off frees the budget for
                    # the answer or tool call. codex works because its responses
                    # path defaults to low reasoning effort; pi needs it stated.
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
