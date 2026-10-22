"""Read what a finished Harbor job left on disk, one :class:`TrialOutput` per trial.

Port of ``_collect_roll`` and ``_collect_one`` of the upstream harness's
``judge/core/session.py``. A trial belongs to the package whose directory name
is the last component of ``task_id.path`` in its ``result.json``: neither the
task name nor the trial directory name identifies the package reliably (Harbor
truncates long trial names). The probe output is the verifier stage's
``verifier/test-stdout.txt``; the reward is ``verifier/reward.txt``, else the
``reward`` key of ``verifier/reward.json``.

Anything that contradicts Harbor's on-disk contract -- a trial directory
without a readable ``result.json``, a result without a task path, two trials of
one package -- raises InfraError(HARBOR_INTERNAL); a job's output is never
partially read.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from ..errors import InfraCategory, InfraError

RESULT_FILE = "result.json"
SETUP_PHASES = ("environment", "agent_setup")
"""Phases before the agent runs; a failure there is an environment failure, not an outcome."""


@dataclass(frozen=True)
class TrialOutput:
    """One trial of a finished job."""

    trial_dir: Path
    package: str
    """Directory name of the task package the trial ran."""
    result: Mapping[str, Any]
    """The trial's ``result.json``."""
    reward: float | None
    """The probe's reward, None when the probe wrote none or an unreadable one."""
    artifact_dir: Path | None
    """The trial's downloaded artifacts, None when Harbor made no artifacts directory."""
    probe_output: str
    """The probe's stdout; empty when the probe did not run."""

    @property
    def trial_name(self) -> str:
        """The trial directory's name, which is also the trial's metering tag."""
        return self.trial_dir.name

    @property
    def agent_ran(self) -> bool:
        """Whether the agent phase started."""
        return agent_ran(self.result)

    @property
    def exception_type(self) -> str | None:
        """The type name of the exception the trial recorded, if any."""
        info = self.result.get("exception_info")
        return info.get("exception_type") if isinstance(info, dict) else None

    @property
    def setup_failure(self) -> str | None:
        """The phase that failed before the agent ran, one of :data:`SETUP_PHASES`, or None.

        ``environment`` when the trial recorded an exception after starting its
        environment and before agent setup; ``agent_setup`` when it recorded one
        after starting agent setup and before the agent ran.
        """
        if self.exception_type is None or self.agent_ran:
            return None
        if self.result.get("agent_setup") is not None:
            return "agent_setup"
        return "environment"

    def failure_summary(self) -> str:
        """``<ExceptionType>: <first line of its message>``, or an empty string."""
        info = self.result.get("exception_info")
        if not isinstance(info, dict):
            return ""
        lines = str(info.get("exception_message") or "").strip().splitlines()
        kind = str(info.get("exception_type"))
        return f"{kind}: {lines[0][:300]}" if lines else kind


def agent_ran(result: Mapping[str, Any]) -> bool:
    """Whether the trial with this ``result.json`` started its agent phase."""
    return result.get("agent_execution") is not None


def read_result(trial_dir: Path) -> dict[str, Any]:
    """The parsed ``result.json`` of ``trial_dir``; InfraError when it is missing or unreadable."""
    path = trial_dir / RESULT_FILE
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InfraError(InfraCategory.HARBOR_INTERNAL,
                         f"trial {trial_dir} has no readable {RESULT_FILE}: {exc}") from exc
    if not isinstance(result, dict):
        raise InfraError(InfraCategory.HARBOR_INTERNAL, f"{path} is not a JSON object")
    return result


def read_trial(trial_dir: Path) -> TrialOutput:
    """Read one finished trial directory."""
    result = read_result(trial_dir)
    task_id = result.get("task_id")
    task_path = task_id.get("path") if isinstance(task_id, dict) else None
    if not isinstance(task_path, str) or not task_path.strip("/"):
        raise InfraError(InfraCategory.HARBOR_INTERNAL,
                         f"{trial_dir / RESULT_FILE} names no task path")
    verifier = trial_dir / "verifier"
    stdout = verifier / "test-stdout.txt"
    artifacts = trial_dir / "artifacts"
    return TrialOutput(
        trial_dir=trial_dir,
        package=PurePosixPath(task_path.rstrip("/")).name,
        result=result,
        reward=_reward(verifier),
        artifact_dir=artifacts if artifacts.is_dir() else None,
        probe_output=(stdout.read_text(encoding="utf-8", errors="replace")
                      if stdout.is_file() else ""),
    )


def collect_job(job_dir: Path) -> dict[str, TrialOutput]:
    """Every trial of the job in ``job_dir``, by package directory name."""
    outputs: dict[str, TrialOutput] = {}
    if not job_dir.is_dir():
        raise InfraError(InfraCategory.HARBOR_INTERNAL, f"job directory {job_dir} does not exist")
    for trial_dir in sorted(path for path in job_dir.iterdir() if path.is_dir()):
        output = read_trial(trial_dir)
        if output.package in outputs:
            raise InfraError(
                InfraCategory.HARBOR_INTERNAL,
                f"package {output.package} has two trials in {job_dir}: "
                f"{outputs[output.package].trial_name} and {output.trial_name}")
        outputs[output.package] = output
    return outputs


def _reward(verifier: Path) -> float | None:
    text_path = verifier / "reward.txt"
    json_path = verifier / "reward.json"
    try:
        if text_path.is_file():
            return float(text_path.read_text(encoding="utf-8").strip())
        if json_path.is_file():
            data = json.loads(json_path.read_text(encoding="utf-8"))
            return float(data["reward"]) if isinstance(data, dict) and "reward" in data else None
    except (ValueError, TypeError):
        return None
    return None
