"""Paradigm declarations: what a generation package asks for and how its product is judged.

A paradigm fixes the verifier product (its in-container path and verdict
protocol), the probe the generation trial runs on that product, the default
judge-time evidence surface and benchmark contract, and how a package is
assembled from an input task. Benchmarks differ only in profile data (the
fields of :class:`PackagePlan` and :class:`AnchorEnvironment`), never in
paradigm code.

Every byte a paradigm writes into a package comes from ``paradigms/assets/``,
``method/`` or the input task; :func:`asset_text` is the only reader of the
assets.
"""

from __future__ import annotations

import inspect
import json
import os
import re
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from importlib import import_module, resources
from pathlib import Path, PurePosixPath
from typing import Any, ClassVar, Literal, get_args

from ..config import PARADIGMS, VERIFIER_NETWORK_MODES
from ..errors import ConfigError
from ..intake.sniff import TaskSpec
from ..method.compose import PromptSwitches, Wording
from ..method.probe_core import ProbeSpec

FromRule = Literal["first", "final"]
"""Which ``FROM`` line of a Dockerfile an injected block follows.

``first``: the first line that starts with ``FROM `` after stripping (the
upstream tb4 adapter). ``final``: the last line matching
``assets/tbsci_final_from.regex`` (case-insensitive) that does not continue the
previous line (the upstream tbsci adapter).
"""
FROM_RULES: tuple[str, ...] = get_args(FromRule)

AnchorImage = Literal["packaged", "original"]
"""Image an anchor runs the verifier in: the generation package's environment
(with its CLI install block and ``TASK.md``), or the input task's own environment."""
ANCHOR_IMAGES: tuple[str, ...] = get_args(AnchorImage)

SwapPolicy = Literal["none", "same_extension_deliverables"]
"""How the swap anchor picks a donor task whose reference solution it stages.

``none``: no swap anchor. ``same_extension_deliverables``: the GDPval rule; among
the tasks sorted by id, cyclically, the next task whose reference deliverables
share this task's primary extension, else the next task with any deliverable
(see :func:`gavel_harness.verify.anchors.plan_swaps`).
"""
SWAP_POLICIES: tuple[str, ...] = get_args(SwapPolicy)

VERDICT_EXIT_CODE = "exit_code"
"""Verdict protocol of a verifier script: exit 0 is PASS, any other exit is a verdict
too, except the codes and failures the three-state verdict layer maps to NO_VERDICT."""

_ASSETS = resources.files("gavel_harness.paradigms").joinpath("assets")
_ASSET_NAME = re.compile(r"[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*")
_IMPLEMENTED = {
    "terminal_state": "gavel_harness.paradigms.terminal_state:TerminalState",
    "deliverable": "gavel_harness.paradigms.deliverable:Deliverable",
}


def asset_text(name: str) -> str:
    """The text of ``paradigms/assets/<name>``, read as UTF-8 without newline translation.

    ``name`` is a relative POSIX path inside the assets directory. Raises
    ConfigError when it is malformed or names no shipped asset.
    """
    if not _ASSET_NAME.fullmatch(name) or ".." in PurePosixPath(name).parts:
        raise ConfigError(f"malformed asset name {name!r}")
    path = _ASSETS.joinpath(*PurePosixPath(name).parts)
    if not path.is_file():
        raise ConfigError(f"no paradigm asset named {name!r}")
    return path.read_bytes().decode("utf-8")


def _positive(value: float, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ConfigError(f"{what} must be a positive number of seconds, got {value!r}")
    return float(value)


def _container_path(value: str, what: str) -> str:
    if not isinstance(value, str) or not PurePosixPath(value).is_absolute():
        raise ConfigError(f"{what} must be an absolute container path, got {value!r}")
    return value


@dataclass(frozen=True)
class Timeouts:
    """Budgets written into the generation package's task.toml, in seconds."""

    build_sec: float
    """``[environment] build_timeout_sec``: building the generation image."""
    agent_sec: float
    """``[agent] timeout_sec``: the generating agent's wall-clock budget."""
    verifier_sec: float
    """``[verifier] timeout_sec``: the probe run on the generated product."""

    def __post_init__(self) -> None:
        for name in ("build_sec", "agent_sec", "verifier_sec"):
            object.__setattr__(self, name, _positive(getattr(self, name), f"timeouts.{name}"))


@dataclass(frozen=True)
class AnchorEnvironment:
    """Where the null, oracle and swap anchors run a delivered verifier.

    Declared per profile and aligned with the benchmark's verdict gate where one
    exists, so anchor labels and gate verdicts are measured in the same setting.
    """

    image: AnchorImage
    """``packaged`` or ``original``; see :data:`AnchorImage`."""
    workdir: str
    """Absolute working directory the verifier runs in."""
    network: str
    """``no-network`` or ``public`` (Harbor ``NetworkMode`` spelling)."""
    timeout_sec: float
    """Wall-clock cap of one verifier run."""
    user: str | None = None
    """User the verifier runs as; None runs it as the image's own ``USER``."""
    network_reason: str | None = None
    """Why the anchors need the network. Required for ``public``, refused otherwise."""
    swap: SwapPolicy = "none"
    """How the swap anchor picks its donor; see :data:`SwapPolicy`."""
    deliverables_subdir: str | None = None
    """Where a reference solution keeps its deliverable files, relative to the
    solution directory. Required for ``same_extension_deliverables``, refused otherwise."""
    keep_images: bool = False
    """Whether the images Harbor builds for a run's generation and anchor trials stay
    after the run. True where verdicts are re-taken on the same images later (the
    verdict-gate fields): a rebuilt image can resolve other package versions."""

    def __post_init__(self) -> None:
        if not isinstance(self.keep_images, bool):
            raise ConfigError(f"anchor.keep_images must be true or false, got {self.keep_images!r}")
        if self.image not in ANCHOR_IMAGES:
            raise ConfigError(f"anchor.image must be one of {ANCHOR_IMAGES}, got {self.image!r}")
        _container_path(self.workdir, "anchor.workdir")
        if self.network not in VERIFIER_NETWORK_MODES:
            raise ConfigError(
                f"anchor.network must be one of {VERIFIER_NETWORK_MODES}, got {self.network!r}"
            )
        object.__setattr__(self, "timeout_sec", _positive(self.timeout_sec, "anchor.timeout_sec"))
        if self.user is not None and (not isinstance(self.user, str) or not self.user):
            raise ConfigError(f"anchor.user must be a non-empty user name, got {self.user!r}")
        reason = self.network_reason
        if self.network == "public" and not (isinstance(reason, str) and reason.strip()):
            raise ConfigError("anchor.network = 'public' needs anchor.network_reason saying why")
        if self.network != "public" and reason is not None:
            raise ConfigError("anchor.network_reason applies only to anchor.network = 'public'")
        if self.swap not in SWAP_POLICIES:
            raise ConfigError(f"anchor.swap must be one of {SWAP_POLICIES}, got {self.swap!r}")
        subdir = self.deliverables_subdir
        if self.swap == "same_extension_deliverables":
            parts = PurePosixPath(subdir).parts if isinstance(subdir, str) else ()
            if (not parts or PurePosixPath(subdir).is_absolute() or ".." in parts
                    or "\\" in subdir):
                raise ConfigError(
                    "anchor.swap = 'same_extension_deliverables' needs "
                    "anchor.deliverables_subdir, a relative path inside the solution "
                    f"directory; got {subdir!r}"
                )
        elif subdir is not None:
            raise ConfigError(
                "anchor.deliverables_subdir applies only to "
                "anchor.swap = 'same_extension_deliverables'"
            )


@dataclass(frozen=True)
class PackagePlan:
    """Everything that shapes one paradigm's packages, resolved from profile and options.

    Asset fields name files in ``paradigms/assets/``. ``mirror`` is the
    package-source rewrite inserted after the ``from_injection`` line, or None
    when the environment profile has none. ``cli_extras`` name blocks in
    ``assets/cli_extra/``. ``wording`` is the evidence header text of the
    generation prompt (:data:`~gavel_harness.method.compose.Wording`).
    ``declare_verifier_timeout_sec`` is the probe budget in declare mode, None
    when the profile does not support declare mode.
    """

    profile: str
    env: str
    contract: str
    judge_evidence: Mapping[str, str]
    package_prefix: str
    install_block: str
    task_toml: str
    from_injection: FromRule
    mirror: str | None
    cli_extras: tuple[str, ...]
    timeouts: Timeouts
    switches: PromptSwitches
    wording: Wording
    deliverable_dir: str | None = None
    declare_verifier_timeout_sec: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "judge_evidence", dict(self.judge_evidence))
        object.__setattr__(self, "cli_extras", tuple(self.cli_extras))
        if self.declare_verifier_timeout_sec is not None:
            object.__setattr__(self, "declare_verifier_timeout_sec", _positive(
                self.declare_verifier_timeout_sec, "declare.verifier_timeout_sec"))

    def to_json(self) -> dict[str, Any]:
        """The plan as JSON data, for the package identity."""
        data = asdict(self)
        data["judge_evidence"] = dict(sorted(self.judge_evidence.items()))
        data["cli_extras"] = list(self.cli_extras)
        return data


@dataclass(frozen=True)
class Collected:
    """The verifier product found among a trial's downloaded artifacts."""

    artifact_path: Path | None
    """The product file, or None when the trial delivered none."""
    ok: bool
    """True when the product exists and is not empty."""


class Paradigm(ABC):
    """One task paradigm. Subclasses are stateless; the build layer instantiates them.

    Class attributes declare the paradigm; :meth:`package` assembles a package
    into a fresh directory. Sealing, caching and the package identity belong to
    the build layer.
    """

    name: ClassVar[str]
    """Paradigm name, one of :data:`gavel_harness.config.PARADIGMS`."""
    artifact_path: ClassVar[str]
    """In-container path of the verifier product the agent must write."""
    verdict_protocol: ClassVar[str]
    """How the product's verdict is read; :data:`VERDICT_EXIT_CODE` for scripts."""
    judge_evidence: ClassVar[Mapping[str, str]]
    """Default judge-time evidence surface (reference -> evidence type)."""
    contract: ClassVar[str]
    """Default benchmark contract (a name under ``method/prompts/contracts``)."""
    probe_asset: ClassVar[str]
    """Asset holding the probe ``tests/test.sh`` the generation trial runs."""
    probe_spec_asset: ClassVar[str]
    """Asset holding the probe classification patterns and feedback texts (JSON)."""
    default_deliverable_dir: ClassVar[str | None] = None
    """Default in-container deliverable directory; None when the paradigm has none."""

    def package_name(self, task_id: str, plan: PackagePlan) -> tuple[str, str]:
        """``(package directory name, tid)`` for ``task_id``.

        ``tid`` is the last ``/``-separated component of ``task_id`` with every
        character outside ``[A-Za-z0-9_-]`` replaced by ``-`` (upstream rule);
        the directory is ``<package_prefix>_<tid>``.
        """
        tid = re.sub(r"[^A-Za-z0-9_-]", "-", task_id.split("/")[-1])
        return f"{plan.package_prefix}_{tid}", tid

    def check_plan(self, plan: PackagePlan) -> None:
        """Raise ConfigError when this paradigm cannot build packages from ``plan``."""
        for name in (self.probe_asset, self.probe_spec_asset, plan.install_block, plan.task_toml):
            asset_text(name)
        if plan.mirror is not None:
            asset_text(plan.mirror)
        if plan.from_injection not in FROM_RULES:
            raise ConfigError(
                f"from_injection must be one of {FROM_RULES}, got {plan.from_injection!r}"
            )
        if plan.deliverable_dir is not None:
            if self.default_deliverable_dir is None:
                raise ConfigError(f"the {self.name} paradigm has no deliverable directory")
            _container_path(plan.deliverable_dir, "deliverable_dir")

    @abstractmethod
    def package(self, task: TaskSpec, tid: str, dst: Path, plan: PackagePlan) -> None:
        """Write the generation package of ``task`` into ``dst``, which must not exist."""

    def configuration(self, task: TaskSpec, plan: PackagePlan) -> dict[str, Any]:
        """The explicit build configuration recorded in the package identity."""
        return {
            "paradigm": self.name,
            "plan": plan.to_json(),
            "env_kind": task.env_kind,
            "stripped_tests": task.strip_tests,
        }

    def code_sources(self) -> dict[str, Path]:
        """Source files of this paradigm's class hierarchy, for the package identity."""
        sources: dict[str, Path] = {}
        for cls in type(self).__mro__:
            module = cls.__module__
            if module.startswith("gavel_harness.paradigms."):
                sources[f"paradigm_{module.rsplit('.', 1)[1]}"] = Path(inspect.getfile(cls))
        return sources

    def artifacts(self, plan: PackagePlan) -> tuple[str, ...]:
        """In-container paths the generation job downloads after each trial."""
        return (self.artifact_path,)

    def probe_spec(self) -> ProbeSpec:
        """The probe classification patterns and retry feedback texts."""
        return ProbeSpec(**json.loads(asset_text(self.probe_spec_asset)))

    def collect(self, artifact_dir: str | Path) -> Collected:
        """Find the verifier product under a trial's downloaded artifacts.

        The first file named like :attr:`artifact_path` in a top-down walk with
        directories visited in sorted order.
        """
        wanted = PurePosixPath(self.artifact_path).name
        for directory, dirs, files in os.walk(artifact_dir):
            dirs.sort()
            if wanted in files:
                path = Path(directory) / wanted
                return Collected(artifact_path=path, ok=path.stat().st_size > 0)
        return Collected(artifact_path=None, ok=False)


def get_paradigm(name: str) -> Paradigm:
    """An instance of the paradigm called ``name``.

    Raises ConfigError for an unknown name or a paradigm this build does not
    implement yet.
    """
    if name not in PARADIGMS:
        raise ConfigError(f"unknown paradigm {name!r}; expected one of {PARADIGMS}")
    target = _IMPLEMENTED.get(name)
    if target is None:
        raise ConfigError(
            f"the {name} paradigm is not implemented in this build; "
            f"available: {', '.join(sorted(_IMPLEMENTED))}"
        )
    module, _, attr = target.partition(":")
    cls = getattr(import_module(module), attr)
    return cls()
