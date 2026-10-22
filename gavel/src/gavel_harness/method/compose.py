"""Generation prompt composition: evidence header, benchmark contract, shared core.

Port of the upstream ``prompt_compose`` module. The prompt words are data: the
prompts (``prompts/``) and fragments (``fragments/``) are byte copies or
extractions of the upstream harness, recorded in ``UPSTREAM.lock``; this module
only assembles them. The upstream environment switches are the fields of
:class:`PromptSwitches`, and the upstream prompt directory
(``VERITAS_PROMPTS_DIR``) is the explicit ``wording`` argument (see
:data:`Wording`). For every contract, wording and switch combination the
output is byte-equal to the upstream ``compose``.

Order of the composed prompt: evidence header, separator and contract, separator
and core manual, the rubric-library directive when the evidence surface has a
``process.*`` type, then the check-declaration directive in declare mode.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from typing import Literal, get_args

from ..errors import ConfigError

_ROOT = resources.files("gavel_harness.method")
_DATASET = re.compile(r"[a-z0-9_]+")

Wording = Literal["state_gate", "frozen_evh1"]
"""Which evidence header text the prompt opens with.

The two texts differ in one derivation rule; contracts, core manual and every
other prompt word are shared. ``state_gate``: when state evidence (a baseline
snapshot and an end state that can be reconciled) can witness a requirement,
the state comparison decides it, and process or conversation evidence cannot
overturn a failed state check; process assertions decide only what state
evidence cannot witness. This is the wording for new tasks. ``frozen_evh1``:
the earlier rule, which asks for state assertions written as code comparisons
when state evidence exists and for process assertions otherwise, without making
the state comparison the gate.
"""
WORDINGS: tuple[str, ...] = get_args(Wording)
_EVIDENCE_HEADERS: dict[str, tuple[str, ...]] = {
    "state_gate": ("prompts", "evidence_header.txt"),
    "frozen_evh1": ("prompts", "frozen_evh1", "evidence_header.txt"),
}

# Line formats of the upstream evidence_header() and declaration_directive(). They
# are format strings in upstream code rather than prompt files, so they stay here.
_HEADER_LINE = "- {ref} → {etype}:{desc}"
_VOCAB_LINE = "- {ref}(证据类型 {etype})"


@dataclass(frozen=True)
class PromptSwitches:
    """Which parts of the generation prompt are rendered.

    The defaults are the standard method. Each field replaces one upstream
    environment switch: ``evidence=False`` is ``VERITAS_NO_EVIDENCE=1``,
    ``rubric=False`` is ``VERITAS_NO_RUBRIC=1``, ``core=False`` is
    ``VERITAS_NO_CORE=1``, ``declare=True`` is ``VERITAS_DECLARE=1`` and
    ``bare=True`` is ``VERITAS_BARE_CONTRACT=1``. ``bare`` renders the contract
    alone, so the other fields have no effect when it is set.
    """

    evidence: bool = True
    """Render the evidence-surface header first."""
    rubric: bool = True
    """Render the rubric-library directive when the surface has a ``process.*`` type."""
    core: bool = True
    """Render the shared judge core manual after the contract."""
    declare: bool = False
    """Append the check-declaration directive."""
    bare: bool = False
    """Render the benchmark contract verbatim and nothing else."""


DEFAULT_SWITCHES = PromptSwitches()
"""The switches of the standard method: everything rendered, declaration off."""


def contract_names() -> tuple[str, ...]:
    """Datasets that have a benchmark contract, sorted."""
    contracts = _ROOT.joinpath("prompts", "contracts")
    return tuple(sorted(
        entry.name.removesuffix(".txt") for entry in contracts.iterdir()
        if entry.is_file() and entry.name.endswith(".txt")
    ))


def contract_text(dataset: str) -> str:
    """The benchmark contract of ``dataset``, verbatim.

    Raises ConfigError when no contract of that name ships with the package.
    """
    if not _DATASET.fullmatch(dataset) or dataset not in contract_names():
        raise ConfigError(
            f"no benchmark contract named {dataset!r}; available: {', '.join(contract_names())}"
        )
    return _read("prompts", "contracts", f"{dataset}.txt")


def core_text() -> str:
    """The shared judge core manual, verbatim."""
    return _read("prompts", "core_manual.txt")


def evidence_types() -> dict[str, str]:
    """The evidence vocabulary: each type with the one-line meaning the header renders."""
    table: dict[str, str] = {}
    rows = _read("fragments", "etype_desc.tsv").removesuffix("\n").split("\n")
    for lineno, row in enumerate(rows, 1):
        etype, tab, desc = row.partition("\t")
        if not tab or not etype or not desc or "\t" in desc or etype in table:
            raise ValueError(f"fragments/etype_desc.tsv:{lineno}: malformed row {row!r}")
        table[etype] = desc
    return table


def evidence_header(judge_evidence: Mapping[str, str], *, wording: Wording) -> str:
    """The evidence-surface section: what the verifier can see when it judges.

    One line per evidence reference, sorted by reference, inside the header
    text of ``wording``. Raises ConfigError for an unknown wording, an empty
    surface or a type outside the vocabulary.
    """
    template = _evidence_header_template(wording)
    descriptions = _checked_surface(judge_evidence)
    lines = "\n".join(
        _HEADER_LINE.format(ref=ref, etype=etype, desc=descriptions[etype])
        for ref, etype in sorted(judge_evidence.items())
    )
    return template.rstrip("\n").format(lines=lines)


def rubric_directive() -> str:
    """The directive to consult the on-box rubric library before process assertions."""
    return _read("fragments", "rubric_directive.txt")


def declaration_directive(judge_evidence: Mapping[str, str]) -> str:
    """The T5 directive: ship ``declaration.json`` binding every check to the surface.

    Raises ConfigError for an empty surface or a type outside the vocabulary.
    """
    _checked_surface(judge_evidence)
    vocab = "\n".join(
        _VOCAB_LINE.format(ref=ref, etype=etype)
        for ref, etype in sorted(judge_evidence.items())
    )
    return _read("fragments", "declaration_directive.txt").format(vocab_lines=vocab)


def compose(
    dataset: str,
    judge_evidence: Mapping[str, str],
    switches: PromptSwitches = DEFAULT_SWITCHES,
    *,
    wording: Wording,
) -> str:
    """The generation prompt for one dataset and its judge-time evidence surface.

    ``judge_evidence`` maps each evidence reference the verifier reads to its
    evidence type. It must be non-empty and use only vocabulary types. Upstream
    rendered placeholders for an empty surface or an unknown type, but every
    upstream adapter passes a non-empty surface and rejects unknown types when it
    writes the evidence manifest, so no package carried those placeholders.
    ``wording`` selects the evidence header text; it has no effect when the
    header is not rendered (``evidence=False`` or ``bare=True``). Raises
    ConfigError for an unknown dataset or wording, or an invalid surface.
    """
    _evidence_header_template(wording)
    _checked_surface(judge_evidence)
    if switches.bare:
        return contract_text(dataset).rstrip() + "\n"
    sep = _read("fragments", "sep.txt")
    out = ""
    if switches.evidence:
        out += evidence_header(judge_evidence, wording=wording).strip() + sep
    out += contract_text(dataset).rstrip()
    if switches.core:
        out += sep + core_text().strip()
    out += "\n"
    if switches.rubric and any(etype.startswith("process.") for etype in judge_evidence.values()):
        out += _read("fragments", "rubric_sep.txt") + rubric_directive().strip() + "\n"
    if switches.declare:
        out += sep + declaration_directive(judge_evidence).strip() + "\n"
    return out


def _evidence_header_template(wording: str) -> str:
    """The evidence header text of ``wording``; raises ConfigError for an unknown wording."""
    if wording not in _EVIDENCE_HEADERS:
        raise ConfigError(f"unknown prompt wording {wording!r}; available: {', '.join(WORDINGS)}")
    return _read(*_EVIDENCE_HEADERS[wording])


def _checked_surface(judge_evidence: Mapping[str, str]) -> dict[str, str]:
    """Return the vocabulary after checking ``judge_evidence`` against it."""
    if not judge_evidence:
        raise ConfigError(
            "the judge-time evidence surface is empty; every verifier derives from it"
        )
    vocabulary = evidence_types()
    for ref, etype in judge_evidence.items():
        if not isinstance(ref, str) or not ref:
            raise ConfigError(f"evidence references must be non-empty strings, got {ref!r}")
        if etype not in vocabulary:
            raise ConfigError(
                f"evidence {ref!r} has unknown type {etype!r}; known types: {', '.join(vocabulary)}"
            )
    return vocabulary


def _read(*parts: str) -> str:
    return _ROOT.joinpath(*parts).read_text(encoding="utf-8")
