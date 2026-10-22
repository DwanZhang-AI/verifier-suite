"""The terminal_state paradigm: a closed-book ``/app/verifier.sh`` judged by its exit code.

Port of ``package_task`` of the upstream tb4, tbsci and harbor_generic adapters.
The package lives in the task's own environment, with ``solution/`` and
``tests/`` left out:

* ``environment/``: the task's ``environment/`` copied whole (or, for a
  prebuilt image, a Dockerfile ``FROM <image>``), plus ``TASK.md`` holding the
  task instruction. The Dockerfile gets, in this order: the environment
  profile's package-source rewrite after the profile's ``FROM`` line, the
  profile's CLI install block, the CLI blocks of the requested extra executors,
  and the block that copies ``TASK.md`` to ``/app``.
* ``instruction.md``: the generation prompt composed in the profile's wording,
  the task heading and the task instruction verbatim, then a newline.
* ``tests/test.sh``: the artifact-presence and bash-syntax probe (mode 0755).
* ``task.toml``: the profile's template with the task's ``tid`` and the
  profile's budgets.
* ``evidence_manifest.json``: the machine-readable evidence surface.

With the same profile and environment profile, the bytes equal those of the
upstream adapter.
"""

from __future__ import annotations

import re
import shutil
import tomllib
from collections.abc import Mapping
from importlib import resources
from pathlib import Path
from types import MappingProxyType
from typing import ClassVar

from ..errors import ConfigError
from ..fsguard import escaping_symlinks
from ..intake.sniff import TaskSpec
from ..method import compose
from ..method.evidence import model as evidence_model
from .base import VERDICT_EXIT_CODE, PackagePlan, Paradigm, Timeouts, asset_text

CLI_EXTRA_ORDER = ("pi", "tmux", "claude_code", "gemini")
"""CLI blocks of extra executors, in the order the upstream adapters append them."""

_FRAGMENTS = resources.files("gavel_harness.method").joinpath("fragments")
_TIMEOUT_KEYS = (
    ("environment", "build_timeout_sec", "build_sec"),
    ("agent", "timeout_sec", "agent_sec"),
    ("verifier", "timeout_sec", "verifier_sec"),
)
"""(task.toml section, key, :class:`Timeouts` field) of each budget."""


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def first_from(lines: list[str]) -> int | None:
    """Index of the first line that starts with ``FROM `` after stripping, or None."""
    for index, line in enumerate(lines):
        if line.strip().startswith("FROM "):
            return index
    return None


def final_from(lines: list[str]) -> int | None:
    """Index of the last ``FROM`` line that does not continue the previous line, or None.

    A line continues the previous one when that line ends in a backslash.
    """
    pattern = re.compile(asset_text("tbsci_final_from.regex"), re.I)
    found, continued = None, False
    for index, line in enumerate(lines):
        if not continued and pattern.match(line):
            found = index
        continued = line.rstrip().endswith("\\")
    return found


_FROM_RULES = {"first": first_from, "final": final_from}


def render_task_toml(template: str, tid: str, timeouts: Timeouts) -> str:
    """``template`` formatted with ``tid``, with each budget set to ``timeouts``.

    A budget line is rewritten only when its value differs, so a profile whose
    budgets match the template reproduces the template bytes. Raises
    ConfigError when the template does not carry all three budgets.
    """
    text = template.format(tid=tid)
    current = tomllib.loads(text)
    for section, key, field in _TIMEOUT_KEYS:
        value = getattr(timeouts, field)
        have = current.get(section, {}).get(key)
        if have is None:
            raise ConfigError(f"task.toml template has no [{section}] {key}")
        if float(have) != value:
            text = _set_value(text, section, key, value)
    rendered = tomllib.loads(text)
    for section, key, field in _TIMEOUT_KEYS:
        if float(rendered[section][key]) != getattr(timeouts, field):
            raise ConfigError(f"could not set [{section}] {key} in the task.toml template")
    return text


def _set_value(text: str, section: str, key: str, value: float) -> str:
    lines = text.split("\n")
    current = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("["):
            current = stripped.strip("[]").strip()
        elif current == section and re.match(rf"{re.escape(key)}\s*=", stripped):
            lines[index] = f"{key} = {value!r}"
            return "\n".join(lines)
    raise ConfigError(f"task.toml template has no [{section}] {key} line")


class TerminalState(Paradigm):
    """Closed-book verifier of a terminal task's end state: ``/app/verifier.sh``, exit 0 = PASS."""

    name = "terminal_state"
    artifact_path = "/app/verifier.sh"
    verdict_protocol = VERDICT_EXIT_CODE
    judge_evidence: ClassVar[Mapping[str, str]] = MappingProxyType(
        {"testbed": "final.artifact", "fs_manifest": "final.manifest"})
    contract = "harbor_generic"
    probe_asset = "tb4_test.sh"
    probe_spec_asset = "tb4_probe_spec.json"
    supports_declare: ClassVar[bool] = False
    """Whether declare mode (the T5 check declaration) is available."""

    def check_plan(self, plan: PackagePlan) -> None:
        super().check_plan(plan)
        if plan.switches.declare and not self.supports_declare:
            raise ConfigError(
                f"declare mode is not available in the {self.name} paradigm; "
                "use the deliverable paradigm"
            )
        unknown = sorted(set(plan.cli_extras) - set(CLI_EXTRA_ORDER))
        if unknown:
            raise ConfigError(
                f"unknown CLI extra(s) {unknown}; available: {', '.join(CLI_EXTRA_ORDER)}"
            )
        if len(set(plan.cli_extras)) != len(plan.cli_extras):
            raise ConfigError(f"CLI extras repeat: {list(plan.cli_extras)}")
        compose.compose(plan.contract, plan.judge_evidence, plan.switches, wording=plan.wording)
        render_task_toml(asset_text(plan.task_toml), "check", self.timeouts(plan))

    def package(self, task: TaskSpec, tid: str, dst: Path, plan: PackagePlan) -> None:
        if dst.exists():
            raise FileExistsError(f"{dst} exists; packages are built into fresh directories")
        (dst / "tests").mkdir(parents=True)
        env_dir = dst / "environment"
        if task.env_kind == "dockerfile":
            escaping = escaping_symlinks(task.environment_dir)
            if escaping:
                raise ConfigError(
                    f"{task.environment_dir}: symlinks point outside the environment: "
                    + ", ".join(escaping[:5])
                )
            shutil.copytree(task.environment_dir, env_dir)
        else:
            env_dir.mkdir()
            _write(env_dir / "Dockerfile", f"FROM {task.image}\n")
        _write(env_dir / "TASK.md", task.instruction)
        dockerfile = env_dir / "Dockerfile"
        _write(dockerfile, self.dockerfile(dockerfile.read_text(encoding="utf-8"), plan))
        _write(dst / "task.toml", render_task_toml(asset_text(plan.task_toml), tid,
                                                   self.timeouts(plan)))
        probe = dst / "tests" / "test.sh"
        _write(probe, self.test_script(plan))
        probe.chmod(0o755)
        evidence_model.write_judge_manifest(str(dst), dict(plan.judge_evidence))
        _write(dst / "instruction.md", self.instruction(task.instruction, plan))

    def dockerfile(self, text: str, plan: PackagePlan) -> str:
        """The generation Dockerfile assembled from the task's Dockerfile ``text``."""
        lines = text.splitlines()
        if plan.mirror is not None:
            index = _FROM_RULES[plan.from_injection](lines)
            if index is not None:
                lines.insert(index + 1, asset_text(plan.mirror).rstrip())
        out = "\n".join(lines).rstrip() + "\n" + asset_text(plan.install_block)
        for extra in CLI_EXTRA_ORDER:
            if extra in plan.cli_extras:
                out += asset_text(f"cli_extra/{extra}.sh")
        return out + asset_text("task_md_block.sh")

    def instruction(self, statement: str, plan: PackagePlan) -> str:
        """The composed prompt, the task heading and the task statement ``statement`` verbatim."""
        heading = _FRAGMENTS.joinpath("task_heading.txt").read_text(encoding="utf-8")
        prompt = compose.compose(plan.contract, plan.judge_evidence, plan.switches,
                                 wording=plan.wording)
        return prompt + heading + statement + "\n"

    def test_script(self, plan: PackagePlan) -> str:
        """The probe ``tests/test.sh``."""
        return asset_text(self.probe_asset)

    def timeouts(self, plan: PackagePlan) -> Timeouts:
        """The budgets written into task.toml."""
        return plan.timeouts
