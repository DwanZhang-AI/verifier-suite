#!/usr/bin/env python3
"""Copy and extract the generation-determining bytes of the upstream harness.

Cluster-only maintenance tool: nothing under ``src/`` imports it. The upstream
harness root comes from ``GAVEL_UPSTREAM_HARNESS`` and is only read. Its modules are
imported with bytecode writing disabled (run with ``python -B``) and with a private
``sys.pycache_prefix``, so no bytecode is written into, or read from, the upstream
tree. Any ``VERITAS_*`` variable in the environment is refused, because the upstream
modules change their output on those switches.

The second prompt wording (``frozen_evh1``) is not in the upstream harness tree: it is
the prompt directory the original TB-Science and pairwise runs selected with
``VERITAS_PROMPTS_DIR`` (the TB4 run had the same header inline in its code), kept in
the sealed copy of the original harness named by ``GAVEL_SEALED``. Only its
evidence header differs from the shipped prompts, so only that file is landed (lock
entry with ``"root": "$GAVEL_SEALED"``); every other file of that directory must equal
the upstream prompt file the repository ships, or be a contract the repository does
not ship, else the tool stops.

Every landed file is either

* ``verbatim``  -- a byte copy of one upstream file,
* ``verbatim-code`` -- a Python file of this repository whose code is the code of one
  upstream file: with docstrings removed, both parse to the same ``ast.dump``. Only
  comments and docstrings differ. The tool never writes it; it checks the code and
  records the sha256 of both files, so ``--check`` reports an upstream code change,
* ``extracted`` -- the value of an upstream module constant, of a string literal in
  an upstream function, or of the block an upstream function appends, encoded as
  UTF-8 and otherwise unchanged. ``etype_desc.tsv`` (a dict) and
  ``tb4_probe_spec.json`` (a dataclass) are lossless serialisations, or
* ``ported``    -- a file of this repository adapted from one upstream file. The tool
  never writes it; the lock records only the upstream sha256, so ``--check`` reports
  an upstream change that the port may have to follow.

An extracted value that several upstream modules hold separately is landed once;
the tool requires the copies to be equal and lists all of them in the lock entry.
Before anything is written, the upstream adapters package synthetic tasks and the
extracted pieces must reassemble their Dockerfile, tests/test.sh, task.toml and
instruction.md byte for byte. Every landed file is recorded in ``UPSTREAM.lock``
(JSON) with its upstream path(s), the sha256 of each upstream file and its own sha256.

Usage::

    export GAVEL_UPSTREAM_HARNESS=<harness root> GAVEL_SEALED=<sealed harness>
    python -B tools/extract_assets.py           # write
    python -B tools/extract_assets.py --check   # compare only

Exit codes: 0 done (or everything matches); 1 ``--check`` found a difference;
2 the tool cannot run (environment, missing upstream or sealed file, failed reassembly,
a frozen_evh1 prompt file that differs from the shipped one without being landed,
unexpected file in a lock-managed directory, a ``verbatim-code`` file whose code
differs from upstream when writing).
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import hashlib
import importlib
import json
import os
import re
import sys
import tempfile
import types
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOCK = REPO / "UPSTREAM.lock"
LOCK_SCHEMA = "gavel-harness/upstream-lock/1"
ROOT_ENV = "GAVEL_UPSTREAM_HARNESS"
SEALED_ENV = "GAVEL_SEALED"

PKG = "src/gavel_harness"
PROMPTS = f"{PKG}/method/prompts"
FRAGMENTS = f"{PKG}/method/fragments"
ASSETS = f"{PKG}/paradigms/assets"
LIBRARY = f"{PKG}/rubric/library_v1"
# Directories whose every file is a lock entry. Other landed files sit next to code
# written in this repository (method/, method/evidence/, run/executors/, rubric/).
MANAGED_DIRS = (PROMPTS, FRAGMENTS, ASSETS, LIBRARY)

# Contracts copied verbatim. harbor_generic.txt is byte-equal to tb4.txt upstream and
# is still copied, so the dataset -> contracts/<dataset>.txt lookup stays as upstream.
CONTRACTS = ("harbor_generic", "metabench_pair", "swe_verified", "tau2", "tb4", "tbsci")
# Upstream contracts deliberately not shipped, with the reason.
EXCLUDED_CONTRACTS = {"traj_full": "trajectory benchmark was dropped; no paradigm uses it"}

# The frozen_evh1 prompt directory in the sealed harness, and its files landed here
# (path relative to that directory -> landed path). Its other files are checked, not landed.
FROZEN_DIR = "prompts/frozen_evh1"
FROZEN_FILES = (("evidence_header.txt", f"{PROMPTS}/frozen_evh1/evidence_header.txt"),)
# Contracts of the frozen directory that are not shipped, with the reason.
FROZEN_EXCLUDED_CONTRACTS = {
    **EXCLUDED_CONTRACTS,
    "deepswe": "no longer in the upstream harness; no shipped profile uses it",
    "mcpatlas": "no longer in the upstream harness; no shipped profile uses it",
}

VERBATIM_FILES = (
    ("judge/prompts/core_manual.txt", f"{PROMPTS}/core_manual.txt"),
    ("judge/prompts/evidence_header.txt", f"{PROMPTS}/evidence_header.txt"),
    *((f"judge/prompts/contracts/{c}.txt", f"{PROMPTS}/contracts/{c}.txt") for c in CONTRACTS),
    ("harbor_integration/verifier_execution.py", f"{ASSETS}/execution_status.py"),
    ("judge/rubric/ingest.py", f"{PKG}/rubric/ingest.py"),
    ("judge/rubric/library.py", f"{PKG}/rubric/library.py"),
)
VERBATIM_TREES = (("judge/rubric/library_v1", LIBRARY),)

# Upstream code with comments and docstrings rewritten for this repository.
VERBATIM_CODE_FILES = (
    ("judge/core/probe_core.py", f"{PKG}/method/probe_core.py"),
    ("judge/evidence/model.py", f"{PKG}/method/evidence/model.py"),
    ("judge/evidence/certificate.py", f"{PKG}/method/evidence/certificate.py"),
    ("judge/evidence/trial.py", f"{PKG}/method/evidence/trial.py"),
    ("harbor_integration/judge_opencode.py", f"{PKG}/run/executors/judge_opencode.py"),
    ("harbor_integration/judge_codex.py", f"{PKG}/run/executors/judge_codex.py"),
    ("harbor_integration/judge_pi.py", f"{PKG}/run/executors/judge_pi.py"),
)

# Upstream reads its inputs from fixed cluster paths; the ports take them as arguments.
PORTED_FILES = (
    ("judge/rubric/build.py", f"{PKG}/rubric/build.py"),
    ("judge/rubric/cli.py", f"{PKG}/rubric/cli.py"),
)

# VERITAS_TB_CLI_EXTRA tokens in upstream append order -> landed file under cli_extra/.
# The hermes block is not extracted: it copies from a private runner image.
CLI_EXTRAS = (("pi", "pi.sh"), ("tmux", "tmux.sh"), ("claude", "claude_code.sh"),
              ("gemini", "gemini.sh"))

PROMPT_COMPOSE = "judge/core/prompt_compose.py"
PACKAGE_INPUTS = "judge/core/package_inputs.py"
TASK_TRANSFORM = "judge/core/task_transform.py"
TB4 = "judge/adapters/tb4.py"
TBSCI = "judge/adapters/tbsci.py"
HARBOR_GENERIC = "judge/adapters/harbor_generic.py"


class ToolError(Exception):
    """The tool cannot produce a trustworthy result; nothing has been written."""


@dataclass(frozen=True)
class Source:
    """One upstream origin of a landed file; ``symbol`` is None for a file copy.

    ``sealed`` marks a path relative to ``GAVEL_SEALED`` instead of the upstream harness.
    """

    path: str
    symbol: str | None = None
    sealed: bool = False


@dataclass(frozen=True)
class Landed:
    """A lock entry: its path, method and origins; ``data`` is None for a ported file."""

    path: str
    method: str
    data: bytes | None
    sources: tuple[Source, ...]


@dataclass(frozen=True)
class Upstream:
    """The imported upstream modules the extraction reads."""

    prompt_compose: types.ModuleType
    package_inputs: types.ModuleType
    task_transform: types.ModuleType
    tb4: types.ModuleType
    tbsci: types.ModuleType
    harbor_generic: types.ModuleType


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _root(env: str, marker: str, what: str) -> Path:
    value = os.environ.get(env)
    if not value:
        raise ToolError(f"set {env} to the {what}")
    root = Path(value).resolve()
    if not (root / marker).exists():
        raise ToolError(f"{env}={value} is not the {what} (no {marker})")
    if root == REPO or root in REPO.parents or REPO in root.parents:
        raise ToolError(f"{env} must not overlap this repository")
    return root


def _upstream_root() -> Path:
    return _root(ROOT_ENV, "judge/core/prompt_compose.py", "upstream harness root")


def _sealed_root() -> Path:
    return _root(SEALED_ENV, FROZEN_DIR, "sealed copy of the original harness")


def _check_interpreter() -> None:
    if not sys.flags.dont_write_bytecode:
        raise ToolError("run with `python -B` (or PYTHONDONTWRITEBYTECODE=1): "
                        "importing upstream modules must not write bytecode")
    switches = sorted(k for k in os.environ if k.startswith("VERITAS_"))
    if switches:
        raise ToolError(f"unset {', '.join(switches)}: upstream output depends on them")


def _import_upstream(root: Path) -> Upstream:
    """Import the upstream modules from source; ``sys.pycache_prefix`` must be private."""
    sys.path.insert(0, str(root))
    try:
        mods = {name: importlib.import_module(f"judge.{name}") for name in (
            "core.prompt_compose", "core.package_inputs", "core.task_transform",
            "adapters.tb4", "adapters.tbsci", "adapters.harbor_generic")}
    finally:
        sys.path.remove(str(root))
    for name, mod in mods.items():
        if root not in Path(mod.__file__).resolve().parents:
            raise ToolError(f"judge.{name} resolved outside {ROOT_ENV}: {mod.__file__}")
    return Upstream(prompt_compose=mods["core.prompt_compose"],
                    package_inputs=mods["core.package_inputs"],
                    task_transform=mods["core.task_transform"], tb4=mods["adapters.tb4"],
                    tbsci=mods["adapters.tbsci"], harbor_generic=mods["adapters.harbor_generic"])


def _string_literals(code: types.CodeType) -> Iterator[str]:
    for const in code.co_consts:
        if isinstance(const, str):
            yield const
        elif isinstance(const, types.CodeType):
            yield from _string_literals(const)


def _literal(fn: Callable[..., object], what: str, match: Callable[[str], bool]) -> str:
    """The one distinct string literal in ``fn`` (nested code included) that ``match`` selects."""
    found = sorted({s for s in _string_literals(fn.__code__) if match(s)})
    if len(found) != 1:
        raise ToolError(f"{what}: expected one matching literal in "
                        f"{fn.__qualname__}, found {len(found)}")
    return found[0]


def _same[T](what: str, values: dict[str, T]) -> T:
    """Require every upstream copy of a value to be equal; return the value."""
    first, *rest = values.values()
    if any(value != first for value in rest):
        raise ToolError(f"{what}: upstream copies differ ({', '.join(values)}); "
                        "land them as separate assets")
    return first


def _etype_tsv(table: dict[str, str]) -> str:
    rows = []
    for key, desc in table.items():
        if any(ch in f"{key}{desc}" for ch in "\t\r\n"):
            raise ToolError(f"_ETYPE_DESC[{key!r}] cannot be written as one TSV row")
        rows.append(f"{key}\t{desc}\n")
    return "".join(rows)


def _probe_spec_json(spec: object) -> str:
    return json.dumps(dataclasses.asdict(spec), ensure_ascii=False, indent=2) + "\n"


@contextmanager
def _cli_extra(value: str) -> Iterator[None]:
    os.environ["VERITAS_TB_CLI_EXTRA"] = value
    try:
        yield
    finally:
        del os.environ["VERITAS_TB_CLI_EXTRA"]


def _synthetic_task(root: Path, task_id: str, statement: str, *,
                    dockerfile: str | None = None, task_toml: str | None = None) -> None:
    task = root / task_id
    task.mkdir(parents=True)
    (task / "instruction.md").write_text(statement, encoding="utf-8")
    if dockerfile is not None:
        (task / "environment").mkdir()
        (task / "environment" / "Dockerfile").write_text(dockerfile, encoding="utf-8")
    if task_toml is not None:
        (task / "task.toml").write_text(task_toml, encoding="utf-8")


def _package(adapter: types.ModuleType, root_attr: str, task_root: Path, task_id: str,
             out: Path, extra: str) -> dict[str, str]:
    """Run ``adapter.package_task`` on a synthetic task; return its text files."""
    setattr(adapter, root_attr, str(task_root))
    with _cli_extra(extra):
        result = adapter.package_task(task_id, str(out))
    pkg = Path(result["package_dir"])
    return {name: (pkg / name).read_text(encoding="utf-8") for name in (
        "environment/Dockerfile", "environment/TASK.md", "tests/test.sh", "task.toml",
        "instruction.md")}


def _cli_extra_blocks(up: Upstream, tail: str) -> dict[str, str]:
    """What harbor_generic.package_task appends to the Dockerfile for each extra token."""
    with tempfile.TemporaryDirectory(prefix="vh-extract-") as tmp:
        root = Path(tmp) / "tasks"
        _synthetic_task(root, "probe", "probe\n", dockerfile="FROM scratch-base\n")
        base = _package(up.harbor_generic, "TASK_ROOT", root, "probe", Path(tmp) / "none", "")
        base_df = base["environment/Dockerfile"]
        if not base_df.endswith(tail):
            raise ToolError("harbor_generic Dockerfile does not end with the TASK.md block")
        prefix = base_df[: len(base_df) - len(tail)]
        blocks = {}
        for token, _name in CLI_EXTRAS:
            df = _package(up.harbor_generic, "TASK_ROOT", root, "probe",
                          Path(tmp) / token, token)["environment/Dockerfile"]
            if not (df.startswith(prefix) and df.endswith(tail)):
                raise ToolError(f"extra {token!r} changed the Dockerfile outside its block")
            blocks[token] = df[len(prefix): len(df) - len(tail)]
            if not blocks[token]:
                raise ToolError(f"extra {token!r} appended nothing")
    return blocks


def _extract(up: Upstream) -> tuple[list[Landed], dict[str, str]]:
    """Extracted landed files, and the named values the reassembly check needs."""
    pc, pi, tt = up.prompt_compose, up.package_inputs, up.task_transform
    tb4, tbsci, hg = up.tb4, up.tbsci, up.harbor_generic

    every_adapter = ((HARBOR_GENERIC, hg), (TB4, tb4), (TBSCI, tbsci))
    first_from_adapters = ((TB4, tb4), (HARBOR_GENERIC, hg))

    def package_literal(what: str, adapters: tuple[tuple[str, types.ModuleType], ...],
                        match: Callable[[str], bool]) -> tuple[str, tuple[Source, ...]]:
        copies = {path: _literal(mod.package_task, what, match) for path, mod in adapters}
        value = _same(what, copies)
        return value, tuple(Source(path, f"package_task: {what}") for path, _ in adapters)

    heading, heading_src = package_literal("task heading literal", every_adapter,
                                           lambda s: s.startswith("\n\n## "))
    tail, tail_src = package_literal("TASK.md Dockerfile block", every_adapter,
                                     lambda s: s.startswith("\nRUN mkdir -p /app\n"))
    cn_mirror, cn_mirror_src = package_literal("CN mirror RUN line", first_from_adapters,
                                               lambda s: s.startswith("RUN (sed -i "))
    rubric_sep = _literal(pc.compose, "rubric separator",
                          lambda s: bool(s.strip()) and set(s.strip()) == {"-"})
    final_from = _literal(tbsci._inject_after_final_from, "final FROM pattern",
                          lambda s: s.startswith("^"))
    test_sh = _same("probe test.sh", {f"{TB4}:_TEST_SH": tb4._TEST_SH,
                                      f"{TBSCI}:_TEST_SH": tbsci._TEST_SH})
    probe_spec = _same("probe spec", {f"{TB4}:probe_spec()": tb4.probe_spec(),
                                      f"{TBSCI}:probe_spec()": tbsci.probe_spec()})
    if hg.probe_spec is not tb4.probe_spec:
        raise ToolError("harbor_generic.probe_spec is no longer tb4.probe_spec")
    if hg.tb4 is not tb4:
        raise ToolError("harbor_generic no longer imports the tb4 adapter")
    cli_blocks = _cli_extra_blocks(up, tail)

    def text(path: str, value: str, *sources: Source) -> Landed:
        return Landed(path, "extracted", value.encode("utf-8"), sources)

    landed = [
        text(f"{FRAGMENTS}/sep.txt", pc._SEP, Source(PROMPT_COMPOSE, "_SEP")),
        text(f"{FRAGMENTS}/rubric_sep.txt", rubric_sep,
             Source(PROMPT_COMPOSE, "compose: separator before the rubric directive")),
        text(f"{FRAGMENTS}/etype_desc.tsv", _etype_tsv(pc._ETYPE_DESC),
             Source(PROMPT_COMPOSE, "_ETYPE_DESC")),
        text(f"{FRAGMENTS}/rubric_directive.txt", pc.rubric_directive(),
             Source(PROMPT_COMPOSE, "rubric_directive()")),
        text(f"{FRAGMENTS}/declaration_directive.txt", pc._DECLARATION_DIRECTIVE,
             Source(PROMPT_COMPOSE, "_DECLARATION_DIRECTIVE")),
        text(f"{FRAGMENTS}/feedback_marker.txt", pi.FEEDBACK_MARKER,
             Source(PACKAGE_INPUTS, "FEEDBACK_MARKER")),
        text(f"{FRAGMENTS}/task_heading.txt", heading, *heading_src),
        text(f"{ASSETS}/tb4_install_block.sh", tb4._INSTALL_BLOCK,
             Source(TB4, "_INSTALL_BLOCK")),
        text(f"{ASSETS}/tb4_test.sh", test_sh,
             Source(TB4, "_TEST_SH"), Source(TBSCI, "_TEST_SH")),
        text(f"{ASSETS}/tb4_task.toml.tmpl", tb4._TASK_TOML, Source(TB4, "_TASK_TOML")),
        text(f"{ASSETS}/tb4_cn_mirror.sh", cn_mirror, *cn_mirror_src),
        text(f"{ASSETS}/tb4_probe_spec.json", _probe_spec_json(probe_spec),
             Source(TB4, "probe_spec()"), Source(TBSCI, "probe_spec()")),
        text(f"{ASSETS}/task_md_block.sh", tail, *tail_src),
        text(f"{ASSETS}/harbor_generic_task.toml.tmpl", hg._TASK_TOML,
             Source(HARBOR_GENERIC, "_TASK_TOML")),
        text(f"{ASSETS}/tbsci_mirror.sh", tbsci._MIRROR, Source(TBSCI, "_MIRROR")),
        text(f"{ASSETS}/tbsci_install_block.sh", tbsci._INSTALL_BLOCK,
             Source(TBSCI, "_INSTALL_BLOCK")),
        text(f"{ASSETS}/tbsci_task.toml.tmpl", tbsci._TASK_TOML, Source(TBSCI, "_TASK_TOML")),
        text(f"{ASSETS}/tbsci_final_from.regex", final_from,
             Source(TBSCI, "_inject_after_final_from: FROM-line pattern (re.I)")),
        text(f"{ASSETS}/evidence_capture.sh", tt.EVIDENCE_CAPTURE_SH,
             Source(TASK_TRANSFORM, "EVIDENCE_CAPTURE_SH")),
        text(f"{ASSETS}/usage_harvest.sh", tt.USAGE_HARVEST_SH,
             Source(TASK_TRANSFORM, "USAGE_HARVEST_SH")),
        *(text(f"{ASSETS}/cli_extra/{name}", cli_blocks[token],
               Source(HARBOR_GENERIC, f"package_task: block for VERITAS_TB_CLI_EXTRA={token}"))
          for token, name in CLI_EXTRAS),
    ]
    values = {"heading": heading, "tail": tail, "cn_mirror": cn_mirror, "rubric_sep": rubric_sep,
              "final_from": final_from, "test_sh": test_sh,
              **{f"cli:{token}": block for token, block in cli_blocks.items()}}
    return landed, values


def _verify_reassembly(up: Upstream, v: dict[str, str]) -> None:
    """Upstream adapters on synthetic tasks must equal the extracted pieces, reassembled."""
    pc, tb4, tbsci, hg = up.prompt_compose, up.tb4, up.tbsci, up.harbor_generic
    all_extras = " ".join(token for token, _ in CLI_EXTRAS)
    extras_block = "".join(v[f"cli:{token}"] for token, _ in CLI_EXTRAS)
    statement = "Synthetic task statement.\n"
    flags = re.I
    if not (re.match(v["final_from"], "FROM base AS build", flags)
            and re.match(v["final_from"], "FROM base", flags)
            and not re.match(v["final_from"], "RUN echo FROM base", flags)):
        raise ToolError("the extracted final-FROM pattern does not select FROM lines")

    def expect(mod: types.ModuleType, files: dict[str, str], dockerfile: str, tid: str) -> None:
        wanted = {
            "environment/Dockerfile": dockerfile,
            "environment/TASK.md": statement,
            "tests/test.sh": v["test_sh"],
            "task.toml": mod._TASK_TOML.format(tid=tid),
            "instruction.md": pc.compose(mod.DATASET, mod.JUDGE_EVIDENCE) + v["heading"]
            + statement + "\n",
        }
        for name, want in wanted.items():
            if files[name] != want:
                raise ToolError(f"{mod.__name__}: reassembled {name} differs from upstream output")

    with tempfile.TemporaryDirectory(prefix="vh-extract-") as tmp:
        root = Path(tmp) / "tasks"
        first_from = "FROM debian:12\nRUN true\n"
        multi_stage = "FROM base AS build\nRUN make\nFROM runtime\nRUN true\n"
        _synthetic_task(root, "t-df", statement, dockerfile=first_from)
        _synthetic_task(root, "t-img", statement,
                        task_toml='[environment]\ndocker_image = "registry.invalid/img:1"\n')
        _synthetic_task(root, "field/sub/t-ms", statement, dockerfile=multi_stage)
        for n, extra in enumerate(("", all_extras)):
            block = extras_block if extra else ""
            out = Path(tmp) / f"out{n}"
            after_first = ("FROM debian:12\n" + v["cn_mirror"] + "\nRUN true\n" + tb4._INSTALL_BLOCK
                           + block + v["tail"])
            expect(tb4, _package(tb4, "TB_ROOT", root, "t-df", out, extra), after_first, "t-df")
            expect(hg, _package(hg, "TASK_ROOT", root, "t-df", out, extra), after_first, "t-df")
            expect(hg, _package(hg, "TASK_ROOT", root, "t-img", out, extra),
                   "FROM registry.invalid/img:1\n" + v["cn_mirror"] + "\n" + tb4._INSTALL_BLOCK
                   + block + v["tail"], "t-img")
            expect(tbsci, _package(tbsci, "TB_ROOT", root, "field/sub/t-ms", out, extra),
                   "FROM base AS build\nRUN make\nFROM runtime\n" + tbsci._MIRROR.rstrip()
                   + "\nRUN true\n" + tbsci._INSTALL_BLOCK + block + v["tail"], "t-ms")

    with_process = pc.compose("tb4", {"messages": "process.interaction"})
    if not with_process.endswith(v["rubric_sep"] + pc.rubric_directive().strip() + "\n"):
        raise ToolError("the extracted rubric separator is not the one compose() uses")


def _frozen_wording(root: Path, sealed: Path) -> list[Landed]:
    """The frozen_evh1 files that differ from the shipped prompts, after checking the rest."""
    base = sealed / FROZEN_DIR
    landed = dict(FROZEN_FILES)
    shipped = {"core_manual.txt", *(f"contracts/{c}.txt" for c in CONTRACTS)}
    excluded = {f"contracts/{c}.txt" for c in FROZEN_EXCLUDED_CONTRACTS}
    found = sorted(path.relative_to(base).as_posix() for path in base.rglob("*")
                   if not path.is_dir())
    for rel in found:
        if (base / rel).is_symlink():
            raise ToolError(f"refusing to read symlink {FROZEN_DIR}/{rel}")
        if rel in landed or rel in excluded:
            continue
        if rel not in shipped:
            raise ToolError(f"{FROZEN_DIR}/{rel} is neither landed, shipped nor excluded")
        if (base / rel).read_bytes() != (root / "judge" / "prompts" / rel).read_bytes():
            raise ToolError(f"{FROZEN_DIR}/{rel} differs from judge/prompts/{rel}; "
                            "land it as a frozen_evh1 file")
    missing = sorted(set(landed) - set(found))
    if missing:
        raise ToolError(f"missing sealed file(s) {', '.join(missing)} in {FROZEN_DIR}")
    return [Landed(dest, "verbatim", (base / rel).read_bytes(),
                   (Source(f"{FROZEN_DIR}/{rel}", sealed=True),)) for rel, dest in FROZEN_FILES]


def _verbatim(root: Path) -> list[Landed]:
    upstream_contracts = {p.stem for p in (root / "judge/prompts/contracts").glob("*.txt")}
    unknown = upstream_contracts - set(CONTRACTS) - set(EXCLUDED_CONTRACTS)
    if unknown:
        raise ToolError(f"upstream has contracts neither shipped nor excluded: {sorted(unknown)}")
    pairs = list(VERBATIM_FILES)
    for up_dir, dest in VERBATIM_TREES:
        base = root / up_dir
        for directory, dirs, names in os.walk(base):
            dirs[:] = sorted(dirs)
            for name in sorted(names):
                path = Path(directory) / name
                if path.is_symlink():
                    raise ToolError(f"refusing to copy symlink {path.relative_to(root)}")
                rel = path.relative_to(base).as_posix()
                pairs.append((f"{up_dir}/{rel}", f"{dest}/{rel}"))
    out = []
    for up_rel, dest in pairs:
        path = root / up_rel
        if not path.is_file():
            raise ToolError(f"missing upstream file {up_rel}")
        out.append(Landed(dest, "verbatim", path.read_bytes(), (Source(up_rel),)))
    return out


def code_dump(source: bytes) -> str:
    """``ast.dump`` of a Python module with every docstring removed; comments never enter it."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
    return ast.dump(tree)


def _verbatim_code(root: Path) -> tuple[list[Landed], list[str]]:
    """The shipped ``verbatim-code`` files, and those whose code no longer equals upstream."""
    out, stale = [], []
    for up_rel, dest in VERBATIM_CODE_FILES:
        upstream, shipped = root / up_rel, REPO / dest
        if not upstream.is_file():
            raise ToolError(f"missing upstream file {up_rel}")
        if not shipped.is_file():
            raise ToolError(f"missing {dest}; copy {up_rel} and rewrite only its comments")
        data = shipped.read_bytes()
        if code_dump(data) != code_dump(upstream.read_bytes()):
            stale.append(f"{dest}: code differs from upstream {up_rel}")
        out.append(Landed(dest, "verbatim-code", data, (Source(up_rel),)))
    return out, stale


def _ported(root: Path) -> list[Landed]:
    out = []
    for up_rel, dest in PORTED_FILES:
        if not (root / up_rel).is_file():
            raise ToolError(f"missing upstream file {up_rel}")
        out.append(Landed(dest, "ported", None, (Source(up_rel),)))
    return out


def _lock_bytes(root: Path, sealed: Path, landed: list[Landed]) -> bytes:
    def upstream(src: Source) -> dict[str, str]:
        base = sealed if src.sealed else root
        entry = {"path": src.path, "sha256": _sha256((base / src.path).read_bytes())}
        if src.sealed:
            entry = {"root": f"${SEALED_ENV}", **entry}
        if src.symbol is not None:
            entry["symbol"] = src.symbol
        return entry

    def entry(item: Landed) -> dict[str, object]:
        out: dict[str, object] = {"path": item.path, "method": item.method}
        if item.data is not None:
            out |= {"sha256": _sha256(item.data), "bytes": len(item.data)}
        return out | {"upstream": [upstream(s) for s in item.sources]}

    lock = {
        "schema": LOCK_SCHEMA,
        "generator": "tools/extract_assets.py",
        "upstream_root": f"${ROOT_ENV}",
        "managed_dirs": list(MANAGED_DIRS),
        "files": [entry(item) for item in sorted(landed, key=lambda item: item.path)],
    }
    return (json.dumps(lock, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def _unexpected_files(landed: list[Landed]) -> list[str]:
    owned = {item.path for item in landed}
    found = []
    for directory in MANAGED_DIRS:
        for path in (REPO / directory).rglob("*"):
            if path.is_dir() or "__pycache__" in path.parts or path.suffix in (".pyc", ".pyo"):
                continue
            rel = path.relative_to(REPO).as_posix()
            if rel not in owned:
                found.append(rel)
    return sorted(found)


def _plan(root: Path, sealed: Path) -> tuple[list[Landed], bytes, list[str]]:
    previous_prefix = sys.pycache_prefix
    with tempfile.TemporaryDirectory(prefix="vh-extract-pycache-") as cache:
        sys.pycache_prefix = cache
        try:
            up = _import_upstream(root)
            extracted, values = _extract(up)
            _verify_reassembly(up, values)
        finally:
            sys.pycache_prefix = previous_prefix
    code, stale = _verbatim_code(root)
    landed = _verbatim(root) + _frozen_wording(root, sealed) + code + extracted + _ported(root)
    paths = [item.path for item in landed]
    if len(set(paths)) != len(paths):
        raise ToolError("two upstream sources land on the same path")
    return landed, _lock_bytes(root, sealed, landed), stale


def _differences(landed: list[Landed], lock: bytes) -> list[str]:
    out = []
    for item in landed:
        path = REPO / item.path
        if not path.is_file():
            out.append(f"{item.path}: missing")
        elif item.data is not None and path.read_bytes() != item.data:
            out.append(f"{item.path}: differs from upstream")
    if not LOCK.is_file() or LOCK.read_bytes() != lock:
        out.append(f"{LOCK.name}: differs from the upstream tree")
    out += [f"{rel}: in a lock-managed directory but not produced"
            for rel in _unexpected_files(landed)]
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="compare the repository with the upstream tree; write nothing")
    args = parser.parse_args(argv)
    try:
        _check_interpreter()
        root = _upstream_root()
        landed, lock, stale = _plan(root, _sealed_root())
        if args.check:
            diffs = stale + _differences(landed, lock)
            for line in diffs:
                print(line, file=sys.stderr)
            print(f"{len(landed)} landed files checked, {len(diffs)} differences")
            return 1 if diffs else 0
        if stale:
            raise ToolError("port the upstream code change, keeping the comments: "
                            + "; ".join(stale))
        unexpected = _unexpected_files(landed)
        if unexpected:
            raise ToolError("remove files the upstream tree no longer yields: "
                            + ", ".join(unexpected))
        missing_ports = [item.path for item in landed
                         if item.data is None and not (REPO / item.path).is_file()]
        if missing_ports:
            raise ToolError("ported files are missing: " + ", ".join(missing_ports))
        for item in landed:
            if item.data is None or item.method == "verbatim-code":
                continue
            path = REPO / item.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(item.data)
        LOCK.write_bytes(lock)
    except ToolError as exc:
        print(f"extract_assets: {exc}", file=sys.stderr)
        return 2
    counts = {m: sum(item.method == m for item in landed)
              for m in ("verbatim", "verbatim-code", "extracted", "ported")}
    print(f"wrote {counts['verbatim']} verbatim and {counts['extracted']} extracted files, "
          f"checked {counts['verbatim-code']} verbatim-code files, recorded "
          f"{counts['ported']} ported files, and wrote {LOCK.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
