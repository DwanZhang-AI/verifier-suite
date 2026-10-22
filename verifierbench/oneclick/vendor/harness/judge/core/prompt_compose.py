#!/usr/bin/env python3
"""Judge-side prompt composition: evidence header, benchmark contract and shared core
manual, joined with the pinned SEP. judge/prompts/{core_manual,contracts/*} hold the
wording as data; this module is plumbing. The judge package is self-contained, so the
composition lives here."""
import os

JUDGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEP = "\n\n---\n\n### 本 benchmark 契约(固定,不可改)\n\n"


def _prompts_root() -> str:
    """VERITAS_PROMPTS_DIR points package builds at another prompts dir (the one-click
    suite points it at each package's copied prompts) without touching the shipped
    files; default = the shipped judge prompts."""
    return os.environ.get("VERITAS_PROMPTS_DIR") or os.path.join(JUDGE_ROOT, "prompts")


def core_text() -> str:
    return open(os.path.join(_prompts_root(), "core_manual.txt"), encoding="utf-8").read()


def identity_sources(dataset: str) -> dict:
    """Package-identity dependency surface for prompts: ONLY the files compose()
    actually reads for this dataset. Hashing the whole prompts dir made ADDING one
    dataset's contract invalidate every other dataset's sealed packages.

    All prompt WORDING lives in the prompts dir as data (evidence_header.txt
    included) so wording revisions are per-file identity events and freezes are
    plain directory snapshots via VERITAS_PROMPTS_DIR; prompt_compose code itself
    is plumbing, excluded from identity comparison like package_inputs. Bare arms
    (any *_BARE switch) don't embed the header, so it is not part of their surface."""
    root = _prompts_root()
    out = {"prompts_core": os.path.join(root, "core_manual.txt"),
           "prompts_contract": os.path.join(root, "contracts", dataset + ".txt")}
    bare = any(os.environ.get(k) == "1" for k in
               ("VERITAS_BARE_CONTRACT", "VERITAS_TB4_BARE", "VERITAS_TBSCI_BARE"))
    if bare or os.environ.get("VERITAS_NO_EVIDENCE") == "1":
        out.pop("prompts_evidence_header", None)
    else:
        out["prompts_evidence_header"] = os.path.join(root, "evidence_header.txt")
    if bare or os.environ.get("VERITAS_NO_CORE") == "1":
        out.pop("prompts_core", None)
    return out


def contract_text(dataset: str) -> str:
    return open(os.path.join(_prompts_root(), "contracts", dataset + ".txt"),
                encoding="utf-8").read()


def compose(dataset: str, judge_evidence: dict | None = None) -> str:
    """Evidence-first composition (all verifier generation derives from the
    evidence): evidence surface header, then the benchmark contract,
    then the shared core. The header + rubric directive render from the adapter's
    JUDGE_EVIDENCE map — single source of truth, nothing hand-typed per benchmark.
    T5 declaration directive appended ONLY on VERITAS_DECLARE=1 candidate builds."""
    # Bare generator contract (ablation): the dataset's I/O contract
    # VERBATIM and nothing else — no evidence header, no shared core, no rubric
    # directive, no declaration. Same text for every harness by construction.
    if os.environ.get("VERITAS_BARE_CONTRACT") == "1":
        return contract_text(dataset).rstrip() + "\n"
    # Ablation switches (one module removed, everything else byte-identical):
    #   VERITAS_NO_EVIDENCE=1 drops the evidence surface header (-E)
    #   VERITAS_NO_RUBRIC=1   drops the rubric-library directive (-R)
    #   VERITAS_NO_CORE=1     drops the shared judge core manual (-H)
    drop_e = os.environ.get("VERITAS_NO_EVIDENCE") == "1"
    drop_r = os.environ.get("VERITAS_NO_RUBRIC") == "1"
    drop_h = os.environ.get("VERITAS_NO_CORE") == "1"
    out = ""
    if judge_evidence and not drop_e:
        out += evidence_header(judge_evidence).strip() + _SEP
    out += contract_text(dataset).rstrip()
    if not drop_h:
        out += _SEP + core_text().strip()
    out += "\n"
    if (judge_evidence and not drop_r
            and any(et.startswith("process.") for et in judge_evidence.values())):
        out += "\n\n---\n\n" + rubric_directive().strip() + "\n"
    if os.environ.get("VERITAS_DECLARE") == "1":
        out += _SEP + declaration_directive(judge_evidence or {}).strip() + "\n"
    return out


#: one-line semantics per evidence type (subset actually used by adapters; grow as needed)
_ETYPE_DESC = {
    "baseline.state":      "动作前快照——起点锚,一切「发生了什么变化」以它为基准",
    "process.action":      "工具调用流——候选实际执行了哪些操作",
    "process.language":    "消息文本流——候选说了什么",
    "process.interaction": "交互轮次流——完整对话(含 assistant/user/tool 消息与工具调用)",
    "process.checkpoint":  "逐步快照——中间状态",
    "final.artifact":      "最终交付物——候选产出的文件/环境",
    "final.diff":          "相对基线的变更集——改了什么",
    "final.manifest":      "终态指纹——结束时刻的状态清单",
    "final.container":     "工作区之外的副作用",
    "final.deps":          "依赖变化",
    "external.network":    "实际外部访问记录",
    "derived.metrics":     "平台派生指标——只作旁证,不作主判据",
}


def evidence_header(judge_evidence: dict) -> str:
    """the FIRST section of every generation prompt: what the verifier will be able
    to see at judge time, and the derivation rule (form & every assertion follow
    from what this evidence can witness — three-state on anything it cannot)."""
    lines = "\n".join(
        f"- {ref} → {et}:{_ETYPE_DESC.get(et, '(未注释的证据类型)')}"
        for ref, et in sorted(judge_evidence.items()))
    template = open(os.path.join(_prompts_root(), "evidence_header.txt"),
                    encoding="utf-8").read().rstrip("\n")
    return template.format(lines=lines)


def write_judge_manifest(package_dir: str, judge_evidence: dict) -> str:
    """composition-side bridge to the evidence protocol: every package carries the
    machine-readable twin of its evidence header. Canonical impl lives in
    judge/evidence/model.py (stdlib-only); loaded by file path so the adapters'
    standalone-import fallback works without the evidence package import."""
    import sys
    import importlib.util
    mod = sys.modules.get("_veritas_evidence_model")
    if mod is None:
        mp = os.path.join(JUDGE_ROOT, "evidence", "model.py")
        spec = importlib.util.spec_from_file_location("_veritas_evidence_model", mp)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_veritas_evidence_model"] = mod    # dataclass reflection needs it
        spec.loader.exec_module(mod)
    return mod.write_judge_manifest(package_dir, judge_evidence)


def rubric_directive() -> str:
    """rendered whenever the judge-time evidence carries a process.* stream: the
    process-assertion prior lives in the in-container rubric library tree. The judge
    browses and instantiates it itself (tree-browse design, no host-side selector);
    images without the library degrade gracefully."""
    return """## 过程断言先验:rubric 库(写过程/沟通类断言前先查)

容器固定路径 /rubric_lib 存放一棵领域规则树(README → 各域 INDEX.tsv → 类目文件,
每条规则有稳定 id、原句与出处)。写过程/沟通/合规类断言之前:
1. 先 `ls /rubric_lib` ——若目录不存在,跳过本节,直接依据任务材料写断言;
2. 读 README 与相关域的 INDEX.tsv(可 grep 关键词),打开相关类目文件;
3. 只把与本任务领域和场景真正相关的规则实例化为断言,并在断言旁注释规则 id;
4. 库里没有的、但任务材料明确要求的照常检查——库是先验补充,不是判据上限;
   库里有的、但与本任务无关的一律不用。"""


# T5 declaration protocol (shared, bench-agnostic): the judge ships a declaration
# binding every check to the FIXED judge-time evidence surface (T1 vocabulary) plus an
# honest `unchecked` list for information the evidence environment cannot witness.
# Pure protocol: validated host-side into the certificate — no in-container lint,
# no retry gating, no runtime component.
_DECLARATION_DIRECTIVE = """## 检查申报(与判官产物一起交付)

在判官产物所在目录写出 declaration.json,结构:
{{"schema": "veritas/declaration/1",
 "checks": [{{"check_id": "C1",
             "claim": "<任务材料中的原文短语,逐字复制:这条检查在验什么>",
             "evidence": ["<判定时证据名,见下表>"]}}, ...],
 "unchecked": [{{"need": "<判官需要但判定环境中不存在的信息>",
               "reason": "<为什么无法检查>"}}, ...]}}

判定时可用的证据名(只能用这些;不存在的证据不许臆造):
{vocab_lines}

规则:
- claim 必须逐字来自任务材料(不许改写、不许概括);
- 判官里的每条实质检查登记为一条 check,evidence 只能取自上表;
- 判官需要、但上表证据无法见证的信息,如实写进 unchecked——这就是申报,不丢分;
- 申报与判官行为不符属不诚实,会记入判官的审计证书。"""


def declaration_directive(judge_evidence: dict) -> str:
    vocab = "\n".join(f"- {ref}(证据类型 {et})"
                      for ref, et in sorted(judge_evidence.items())) or "-(本数据集未定义)"
    return _DECLARATION_DIRECTIVE.format(vocab_lines=vocab)


def _selftest():
    tau2_ev = {"messages": "process.interaction",
               "db_before": "baseline.state", "db_after": "final.manifest"}
    got = compose("tau2", tau2_ev)
    assert got.startswith("## 判定时证据面"), "evidence header must lead the prompt"
    assert "/rubric_lib" in got, "process evidence must render the rubric directive"
    assert "### 本 benchmark 契约" in got and "判官核心准则" in got
    swe = compose("swe_verified", {"testbed": "final.artifact",
                                   "test_output": "derived.metrics"})
    assert swe.startswith("## 判定时证据面") and "/rubric_lib" not in swe, \
        "no process evidence -> no rubric directive"
    want = open("/opt/gavel/runtime/v2_packages/tau2/tau2_airline_11/instruction.md",
                encoding="utf-8").read()
    assert got == want, f"compose('tau2') diverges from shipped package ({len(got)} vs {len(want)}) — rebuild v2_packages"
    print("prompt_compose selftest OK (evidence-first; tau2 byte-equal to shipped package)")


if __name__ == "__main__":
    _selftest()
