"""Judge-harness opencode agent: the built-in OpenCode, minus in-container install.

Harbor's `OpenCode.install()` runs `npm i -g opencode-ai@latest` unconditionally
(agents/installed/opencode.py). On an allowlisted network the npm registry is
unreachable by design, so agent setup would fail. The task image ships opencode
instead (version 1.18.3), and this subclass skips the install when a working
opencode is already present, falling back to the stock install path otherwise
(e.g. local docker images without opencode).

Plug in via AgentConfig.import_path: "judge_opencode:JudgeOpenCode".

Salvage semantics: the session's purpose is the judge artifact. If opencode exits
non-zero or emits error events (e.g. the model stream dies on the last turn after a
complete checker.py is already on disk) but the artifact exists and is non-empty,
the run is a success: swallow the agent error so the verifier still runs. A genuine
failure (no artifact) re-raises the original error untouched.
"""

from __future__ import annotations

import asyncio
import random
import subprocess
from typing import override

from harbor.agents.installed.base import NonZeroAgentExitCodeError
from harbor.agents.installed.opencode import OpenCode
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

# What salvage catches: the failure modes that can strike after the artifact is
# already on disk:
#   NonZeroAgentExitCodeError  the model stream died late and opencode exited 1
#   RuntimeError               exec_as_agent wraps non-zero execs
#   TimeoutError               transport/asyncio timeout family (asyncio.TimeoutError
#                              is an alias since 3.11)
#   subprocess.TimeoutExpired  the transport's subprocess-level cap
# Deliberately NOT caught:
#   asyncio.CancelledError: external cancellation is the cancel protocol, a
#     BaseException; swallowing it would fight Harbor's cancel path, which itself
#     still collects artifacts.
#   AgentTimeoutError: raised at the trial layer around agent.run (trial.py),
#     never visible inside it; Harbor natively still verifies on it
#     (single_step.py), so that salvage already exists upstream.
_SALVAGE_EXCEPTIONS = (
    NonZeroAgentExitCodeError,
    RuntimeError,
    TimeoutError,
    subprocess.TimeoutExpired,
)


class JudgeOpenCode(OpenCode):
    # The judge artifact contract path (tau2 gen prompt: ./checker.py in /app).
    # Override per-task via agents[].kwargs.artifact_path.
    def __init__(self, *args, artifact_path: str = "/app/checker.py", **kwargs):
        super().__init__(*args, **kwargs)
        self._artifact_path = artifact_path

    @staticmethod
    @override
    def name() -> str:
        return "judge-opencode"

    @override
    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        for attempt in (0, 1):
            try:
                await super().run(instruction, environment, context)
                return
            except _SALVAGE_EXCEPTIONS as exc:
                probe = await environment.exec(
                    command=f"test -s {self._artifact_path}", timeout_sec=60
                )
                if probe.return_code == 0:
                    self.logger.warning(
                        "Agent errored (%s) but judge artifact %s exists and is "
                        "non-empty — salvage: treating the session as successful.",
                        type(exc).__name__,
                        self._artifact_path,
                    )
                    return
                if attempt == 0 and isinstance(exc, NonZeroAgentExitCodeError):
                    # Start burst: when many trials launch in the same second,
                    # some opencode execs die instantly (exit 125, empty
                    # stdout/stderr, no artifact). Nothing was generated, so one
                    # jittered retry is free and desynchronizes this trial from
                    # the burst.
                    delay = 5 + random.random() * 25
                    self.logger.warning(
                        "Agent exec died with no artifact (%s) — wave-burst "
                        "signature; retrying once in %.0fs.",
                        type(exc).__name__, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        probe = await environment.exec(
            command=self.get_version_command() or "opencode --version",
            timeout_sec=60,
        )
        if probe.return_code == 0 and (probe.stdout or "").strip():
            # Pre-baked opencode in the task image. No network needed; also record
            # the version so BaseInstalledAgent.setup() skips its re-probe.
            self._version = self.parse_version(probe.stdout)
            return
        # Not pre-baked (e.g. plain local docker image): stock install path, which
        # needs registry egress; on an allowlisted network it fails loudly.
        await super().install(environment)
