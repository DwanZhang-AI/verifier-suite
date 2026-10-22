"""Harbor's oracle agent fed an explicit solution directory: the oracle and swap anchors.

:class:`ReplayAgent` is Harbor's ``OracleAgent`` (upload the solution directory
to ``/solution``, run its solve script there) with two differences:

* the solution directory is a constructor argument instead of the task's own
  ``solution/``, so the swap anchor can stage another task's reference solution
  into this task's environment;
* after the solve script succeeds, ``/solution`` is removed (as root) before
  the verifier phase, so the verifier judges the environment the solution left
  and never sees the solution itself (as the TB4 and TB-Science verdict gates
  did).

Staging fails when the solve script is missing, the upload or the script
fails, or the clean-up fails. The agent then writes
``veritas_staging.json`` (``{"status": "failed", "what": <code>, "detail": ...}``)
into its log directory and raises :class:`SolutionStagingError`, which ends the
trial before the verifier runs. On success the file reads ``{"status": "ok"}``.
``what`` is ``solve_exit_<n>``, ``solution_cleanup``, or the name of the
exception the oracle mechanism raised (``FileNotFoundError`` for a missing
solve script).

Load it through ``AgentConfig(import_path=AGENT_IMPORT_PATH, kwargs={...})``
with ``task_dir`` and ``solution_dir`` as strings; Harbor passes those kwargs.
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Any, NoReturn, override

from harbor.agents.oracle import OracleAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from harbor.models.trial.paths import EnvironmentPaths, TrialPaths
from harbor.utils.scripts import discover_script

AGENT_IMPORT_PATH = "gavel_harness.verify.replay_agent:ReplayAgent"
STAGING_FILE = "veritas_staging.json"
"""Name of the staging status file in the agent log directory."""


class SolutionStagingError(RuntimeError):
    """A reference solution could not be staged; the anchor has no verdict."""


class ReplayAgent(OracleAgent):
    """Stage a given reference solution with Harbor's oracle mechanism, then remove it."""

    SUPPORTS_WINDOWS = False

    @staticmethod
    @override
    def name() -> str:
        return "veritas-replay"

    def __init__(
        self,
        logs_dir: Path,
        *,
        task_dir: str,
        solution_dir: str,
        agent_timeout_sec: float | None = None,
        model_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """``logs_dir`` is the trial's agent log directory, as Harbor passes it."""
        logs_dir = Path(logs_dir)
        trial_paths = TrialPaths(trial_dir=logs_dir.parent)
        if trial_paths.agent_dir != logs_dir:
            raise ValueError(f"{logs_dir} is not the agent directory of a Harbor trial")
        super().__init__(
            logs_dir=logs_dir,
            task_dir=Path(task_dir),
            trial_paths=trial_paths,
            model_name=model_name,
            agent_timeout_sec=agent_timeout_sec,
            **kwargs,
        )
        self._solution_dir = Path(solution_dir)

    @override
    def _resolve_solution_paths(self) -> tuple[Path, Path]:
        task_os = self._task.config.environment.os
        solve = discover_script(self._solution_dir, "solve", task_os=task_os)
        if solve is None:
            raise FileNotFoundError(f"no solve script in {self._solution_dir}")
        return self._solution_dir, solve

    @override
    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        try:
            await super().run(instruction, environment, context)
        except Exception as exc:
            self._fail(type(exc).__name__, str(exc), cause=exc)
        exit_code = self.logs_dir / "exit-code.txt"
        if exit_code.exists():
            code = exit_code.read_text(encoding="utf-8").strip()
            self._fail(f"solve_exit_{code}", f"the solve script exited {code}")
        solution = EnvironmentPaths.for_os(environment.os).solution_dir
        cleanup = await environment.exec(f"rm -rf {shlex.quote(str(solution))}", user="root")
        if cleanup.return_code != 0:
            self._fail("solution_cleanup",
                       f"rm -rf {solution} exited {cleanup.return_code}: {cleanup.stderr}")
        (self.logs_dir / STAGING_FILE).write_text(json.dumps({"status": "ok"}) + "\n",
                                                  encoding="utf-8")

    def _fail(self, what: str, detail: str, *, cause: BaseException | None = None) -> NoReturn:
        record = {"status": "failed", "what": what, "detail": detail}
        (self.logs_dir / STAGING_FILE).write_text(json.dumps(record) + "\n", encoding="utf-8")
        raise SolutionStagingError(f"{what}: {detail}") from cause
