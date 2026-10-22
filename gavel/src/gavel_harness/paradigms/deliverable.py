"""The deliverable paradigm: terminal_state packaging for tasks that hand in files.

Outside declare mode a deliverable package is byte-identical to the
terminal_state package of the same profile (the upstream harbor_generic path
GDPval was generated with). The paradigm adds the in-container deliverable
directory the anchors fill (oracle and swap copy deliverables into it, null
leaves it as the environment built it) and declare mode.

Declare mode (``switches.declare``) asks the agent for ``declaration.json``
next to the verifier (the T5 check declaration) and brings the declaration and
the task material home through the verifier channel:

* the prompt ends with the declaration directive (``compose`` in declare mode);
* ``tests/test.sh`` runs the upstream evidence-capture block right after the
  probe creates ``/logs/verifier``, inside a subshell that sets
  ``V=/logs/verifier``. The probe's own ``V`` names the verifier file, which
  would send the capture to ``/app/verifier.sh/evidence``; and the probe exits
  early when the verifier is missing, which would skip a block appended at the
  end. The capture writes ``/logs/verifier/evidence/gen_declaration.json`` and
  ``material_TASK.md`` on every probe path and never changes the probe's
  output or reward;
* the probe budget becomes the profile's ``[declare] verifier_timeout_sec``,
  which must exceed the sum of the capture block's ``timeout`` caps.
"""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Any, ClassVar

from ..errors import ConfigError
from ..intake.sniff import TaskSpec
from .base import PackagePlan, Timeouts, asset_text
from .terminal_state import TerminalState

DEFAULT_DELIVERABLE_DIR = "/app/output"
DECLARATION_ARTIFACT = "/app/declaration.json"
"""Where the declare-mode prompt asks for the declaration (next to the verifier)."""

CAPTURE_ASSET = "evidence_capture.sh"
_PROBE_LOG_DIR_LINE = 'mkdir -p "$REWARD_DIR"\n'
_CAPTURE_OPEN = (
    "# gavel-harness declare mode: evidence capture into /logs/verifier/evidence\n"
    "(\n"
    "V=/logs/verifier"
)
_CAPTURE_CLOSE = ")\n"


def capture_budget_sec() -> int:
    """Sum of the ``timeout`` caps in the evidence-capture block, in seconds."""
    return sum(int(cap) for cap in re.findall(r"\btimeout (\d+)\b", asset_text(CAPTURE_ASSET)))


def with_capture(probe: str) -> str:
    """``probe`` with the evidence-capture subshell after its ``mkdir -p "$REWARD_DIR"`` line.

    Raises ConfigError unless that line occurs exactly once.
    """
    if probe.count(_PROBE_LOG_DIR_LINE) != 1:
        raise ConfigError(
            f"the probe must create its log directory exactly once with {_PROBE_LOG_DIR_LINE!r}"
        )
    block = _CAPTURE_OPEN + asset_text(CAPTURE_ASSET) + _CAPTURE_CLOSE
    return probe.replace(_PROBE_LOG_DIR_LINE, _PROBE_LOG_DIR_LINE + block, 1)


class Deliverable(TerminalState):
    """A verifier that judges files the agent handed in under the deliverable directory."""

    name = "deliverable"
    default_deliverable_dir = DEFAULT_DELIVERABLE_DIR
    supports_declare: ClassVar[bool] = True

    def check_plan(self, plan: PackagePlan) -> None:
        super().check_plan(plan)
        if not plan.switches.declare:
            return
        if plan.switches.bare:
            raise ConfigError("declare mode needs the declaration directive, which bare omits")
        budget = plan.declare_verifier_timeout_sec
        if budget is None:
            raise ConfigError(
                f"profile {plan.profile} has no [declare] verifier_timeout_sec; "
                "it does not support declare mode"
            )
        if budget <= capture_budget_sec():
            raise ConfigError(
                f"[declare] verifier_timeout_sec = {budget} does not exceed the "
                f"{capture_budget_sec()} s of capped steps in the evidence-capture block"
            )
        with_capture(asset_text(self.probe_asset))

    def configuration(self, task: TaskSpec, plan: PackagePlan) -> dict[str, Any]:
        configuration = super().configuration(task, plan)
        configuration["deliverable_dir"] = self.deliverable_dir(plan)
        return configuration

    def deliverable_dir(self, plan: PackagePlan) -> str:
        """The in-container directory the deliverables land in."""
        return plan.deliverable_dir or DEFAULT_DELIVERABLE_DIR

    def artifacts(self, plan: PackagePlan) -> tuple[str, ...]:
        if plan.switches.declare:
            return (self.artifact_path, DECLARATION_ARTIFACT)
        return (self.artifact_path,)

    def test_script(self, plan: PackagePlan) -> str:
        probe = super().test_script(plan)
        return with_capture(probe) if plan.switches.declare else probe

    def timeouts(self, plan: PackagePlan) -> Timeouts:
        if plan.switches.declare and plan.declare_verifier_timeout_sec is not None:
            return replace(plan.timeouts, verifier_sec=plan.declare_verifier_timeout_sec)
        return plan.timeouts
