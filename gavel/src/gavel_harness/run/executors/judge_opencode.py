"""Judge-harness opencode agent: Harbor's OpenCode without a forced install.

Harbor's `OpenCode.install()` always runs `npm i -g opencode-ai@latest`
(agents/installed/opencode.py:104-127), which fails in an environment without
access to the npm registry. This subclass skips the install when the image
already has a working opencode and falls back to Harbor's install otherwise.

Plug in via AgentConfig.import_path: "judge_opencode:JudgeOpenCode".

Salvage: the purpose of the session is the judge artifact. If opencode exits
non-zero or reports an error (for example, the model stream breaks on the last
turn after the checker was written) but the artifact exists and is non-empty,
the run counts as a success: the agent error is dropped so the verifier still
runs. Without an artifact the original error is raised unchanged.
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

# What salvage catches: the failures that can occur after the artifact is
# already on disk.
#   NonZeroAgentExitCodeError  the CLI exited non-zero (e.g. a broken model stream)
#   RuntimeError               exec_as_agent wraps non-zero execs
#   TimeoutError               transport/asyncio timeout family (asyncio.TimeoutError
#                              is an alias since 3.11)
#   subprocess.TimeoutExpired  a transport's subprocess-level time limit
# Deliberately not caught:
#   asyncio.CancelledError: external cancellation is Harbor's cancel protocol, a
#     BaseException; swallowing it would fight Harbor's cancel path, which still
#     collects artifacts on its own.
#   AgentTimeoutError: raised at the trial layer around agent.run
#     (trial.py:480), never visible inside it; Harbor still runs the verifier
#     after it (single_step.py:75-87).
_SALVAGE_EXCEPTIONS = (
    NonZeroAgentExitCodeError,
    RuntimeError,
    TimeoutError,
    subprocess.TimeoutExpired,
)


class JudgeOpenCode(OpenCode):
    # The judge artifact path the generation prompt names (./checker.py in /app).
    # Override per task via agents[].kwargs.artifact_path.
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
                    # Start burst: when many trials start in the same second,
                    # some opencode execs die at once (exit 125, empty
                    # stdout/stderr, no artifact). Nothing was generated, so one
                    # retry after a random delay costs nothing and moves this
                    # trial out of the burst.
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
            # opencode is already in the image. No network needed; also record
            # the version so BaseInstalledAgent.setup() skips its re-probe.
            self._version = self.parse_version(probe.stdout)
            return
        # Not in the image: Harbor's install, which needs access to the npm
        # registry and fails loudly without it.
        await super().install(environment)
