"""The verbatim JudgeOpenCode with a per-trial metering base URL and an optional exec cap.

:class:`TaggedJudgeOpenCode` takes two keyword arguments more than
:class:`~gavel_harness.run.executors.judge_opencode.JudgeOpenCode`:

* ``meter``: the metering proxy's ``gateway``, ``port``, ``run_id`` and
  ``upstream_path``. Before each run it sets ``options.baseURL`` of the single
  provider in its ``opencode_config`` to :func:`gavel_harness.meter.tagged_base_url`
  for this trial, the trial being the name of the trial directory Harbor
  created (the parent of the agent's ``logs_dir``), so the proxy can book every
  request to it.
* ``exec_cap_sec``: the time limit of every agent command that sets none, the
  CLI run among them. The upstream environments ran each command through a
  transport that gave up after ``VERITAS_EXEC_TIMEOUT`` seconds (3900 by
  default) and raised a RuntimeError; a command over the cap here raises
  :class:`ExecCapError`, a RuntimeError as well, so the run continues as it did
  upstream: JudgeOpenCode's salvage looks for its ``artifact_path`` and, when
  that is not a non-empty file, re-raises; Harbor then records the exception,
  skips the verifier stage and collects the trial's artifacts. The command
  keeps running in the container until the trial stops the environment, as
  the upstream command did after its transport gave up.

Nothing else changes: install, the run command, salvage and the same-container
retry are JudgeOpenCode's. Without ``meter`` and ``exec_cap_sec`` the class is
JudgeOpenCode.
"""

from __future__ import annotations

import asyncio
import copy
from collections.abc import Mapping
from typing import Any, override

from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from ...meter import tagged_base_url
from .judge_opencode import JudgeOpenCode

METER_KEYS = ("gateway", "port", "run_id", "upstream_path")
"""Keys of the ``meter`` keyword argument."""


class ExecCapError(RuntimeError):
    """An agent command was still running when the executor's exec cap ran out.

    Not a NonZeroAgentExitCodeError: after one of those Harbor runs the verifier
    stage, which the upstream transport cap never reached.
    """


class TaggedJudgeOpenCode(JudgeOpenCode):
    """JudgeOpenCode with a per-trial metering URL and an exec cap; see the module docstring."""

    def __init__(self, *args: Any, meter: Mapping[str, Any] | None = None,
                 exec_cap_sec: float | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if meter is not None and set(meter) != set(METER_KEYS):
            raise ValueError(f"meter must have exactly the keys {METER_KEYS}, got {sorted(meter)}")
        if exec_cap_sec is not None and not exec_cap_sec > 0:
            raise ValueError(f"exec_cap_sec must be positive, got {exec_cap_sec!r}")
        self._meter = dict(meter) if meter is not None else None
        self._exec_cap_sec = exec_cap_sec
        # Harbor hands every trial of a job the same kwargs objects; the URL is per trial.
        self._opencode_config = copy.deepcopy(self._opencode_config)

    @override
    async def run(self, instruction: str, environment: BaseEnvironment,
                  context: AgentContext) -> None:
        if self._meter is not None:
            providers = self._opencode_config.get("provider")
            if not isinstance(providers, dict) or len(providers) != 1:
                raise ValueError("a metered opencode_config needs exactly one provider block")
            (block,) = providers.values()
            block.setdefault("options", {})["baseURL"] = tagged_base_url(
                self._meter["gateway"], self._meter["port"], self._meter["run_id"],
                self.logs_dir.parent.name, self._meter["upstream_path"])
        await super().run(instruction, environment, context)

    @override
    async def exec_as_agent(self, environment: BaseEnvironment, command: str,
                            env: dict[str, str] | None = None, cwd: str | None = None,
                            timeout_sec: int | None = None) -> Any:
        if self._exec_cap_sec is None or timeout_sec is not None:
            return await super().exec_as_agent(environment, command, env=env, cwd=cwd,
                                               timeout_sec=timeout_sec)
        cap = asyncio.timeout(self._exec_cap_sec)
        try:
            async with cap:
                return await super().exec_as_agent(environment, command, env=env, cwd=cwd)
        except TimeoutError as exc:
            if not cap.expired():
                raise
            raise ExecCapError(f"agent command still running after the exec cap of "
                               f"{self._exec_cap_sec:g} s") from exc
