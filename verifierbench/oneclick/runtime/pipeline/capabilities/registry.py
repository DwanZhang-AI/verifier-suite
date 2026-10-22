#!/usr/bin/env python3
"""按来源取 backend，并声明**哪些来源天然不适用**执行能力。

## ast 是对照组，不是缺口

BFCL / ACEBench 的 100 道题全部是非执行类（`parallel` / `parallel_multiple` /
`normal_*`）：判定纯粹是"这串调用在结构与取值上对不对"，**没有环境可执行**。

而且 ast 的公开面本来就完整 —— `task_spec.tools` 已经给出函数签名、
参数类型、必填项。这与 state/code 的处境完全不同：那两个是
"判状态对不对却看不到状态"、"判 patch 对不对却没有仓库"。

所以 v1→v2 的对比里：

    ast     无变化   ← **内建对照组**
    state   无 → 有执行能力
    code    无 → 有执行能力

如果 v2 里 ast 的分数也动了，说明变化来自别的东西（模型、prompt、池子），
而不是执行能力。**没有这个对照组，任何提升都可以被归因到别处。**

## 每个 backend 跑在哪个解释器

进程内的三个各有自己的 venv；Docker 那两个只要 docker CLI。
`interpreter()` 返回该来源应当使用的 python，供 generate/runner 起子进程。
"""
import os

from pathlib import Path
import shutil


def source_root():
    explicit = os.environ.get("VGB_SRC_ROOT")
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError("VGB_SRC_ROOT does not exist: " + str(root))
        return str(root)
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "_v4v_sources"
        if candidate.is_dir():
            return str(candidate)
    deployed = Path("/opt/vgb_src")
    if deployed.is_dir():
        return str(deployed)
    raise FileNotFoundError("Cannot locate benchmark sources; set VGB_SRC_ROOT")


SRC = source_root()
RUNTIME_CONTRACT = "task-serial-reset-shared-budget-20260917-v2"
if os.environ.get("VGB_PUBLIC_OBSERVATION_V2") == "1":
    RUNTIME_CONTRACT += "+public-observation-pages-20260926-v1"

# 来源 → (模块, 类名, 解释器)
BACKENDS = {
    "τ²-bench": ("cap_tau2", "Tau2Capability", f"{SRC}/_venv_tau2/bin/python"),
    "AgentDojo user": ("cap_agentdojo", "AgentDojoCapability",
                       f"{SRC}/_venv_ad/bin/python"),
    "AgentDojo injection": ("cap_agentdojo", "AgentDojoCapability",
                            f"{SRC}/_venv_ad/bin/python"),
    "AppWorld": ("cap_appworld", "AppWorldCapability",
                 f"{SRC}/_venv_aw/bin/python"),
    "SWE-bench Verified": ("cap_swe", "SWECapability",
                           f"{SRC}/_venv_swe/bin/python"),
    "Terminal-Bench": ("cap_tb", "TBCapability", "python3"),
    # ExploitBench：run_public 走 docker 跑 d8 --grader，只需 subprocess，
    # 用系统 python3（须在 x86 native Linux 上；thin-v8 二进制 arm+rosetta 起不来）。
    "ExploitBench": ("cap_exploitbench", "ExploitBenchCapability", "python3"),
}

# 天然不适用（不是"没做"）——理由写在这里，供文档与 Limitations 直接引用。
NOT_APPLICABLE = {
    "BFCL v4": "非执行类题（parallel / parallel_multiple）；判定为纯结构比较，"
               "无环境可执行。tool schema 已在 task_spec.tools 中给出。",
    "ACEBench": "非执行类题（normal_*）；同上。",
}

# AgentDojo 的 backend 需要 agentdojo 包在 PYTHONPATH 上（源码布局，非安装）
EXTRA_ENV = {
    "AgentDojo user": {"PYTHONPATH": f"{SRC}/_new/agentdojo/src"},
    "AgentDojo injection": {"PYTHONPATH": f"{SRC}/_new/agentdojo/src"},
    # SWE 的 backend 起手要 `load_dataset("princeton-nlp/SWE-bench_Verified")`。
    # 不设离线它会先去问 HF Hub —— 网络一断就成了"能力层起不来"，
    # 而那几道题会**悄悄退回无能力模式**跑完（见 runner 的 cap_ready）。
    # 数据集本地已缓存（实测离线加载 500 条），钉死离线消掉这个依赖。
    "SWE-bench Verified": {"HF_HUB_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1"},
}


def has_capability(benchmark):
    return benchmark in BACKENDS


def why_not(benchmark):
    return NOT_APPLICABLE.get(benchmark)


def interpreter(benchmark):
    b = BACKENDS.get(benchmark)
    if not b:
        return None
    executable = b[2]
    if not shutil.which(executable):
        raise FileNotFoundError("Capability interpreter not found: " + executable)
    return executable


def env_for(benchmark):
    e = dict(os.environ)
    e.update(EXTRA_ENV.get(benchmark, {}))
    e.update(VGB_SRC_ROOT=SRC, LANG="C.UTF-8", LC_ALL="C.UTF-8",
             PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    if benchmark == "τ²-bench":
        explicit = e.get("TAU2_DATA_DIR")
        candidates = [Path(explicit)] if explicit else [
            Path(SRC) / "tau2-bench" / "data", Path(SRC) / "tau2_data"]
        root = next((p for p in candidates if (p / "tau2/domains/retail/tasks.json").is_file()), None)
        if root is None:
            raise FileNotFoundError("Cannot locate tau2 data; set TAU2_DATA_DIR")
        e["TAU2_DATA_DIR"] = str(root)
        e.setdefault("V4V_TAU2_RETRIEVAL", "bm25")
    if benchmark.startswith("AgentDojo"):
        e.setdefault("VGB_AD_SUITE_VERSION", "v1.2")
    return e


def make(benchmark, task_id, budget=None):
    """在**当前进程**里构造 backend（调用方须已在正确的解释器里）。"""
    b = BACKENDS.get(benchmark)
    if not b:
        raise KeyError(f"{benchmark} 没有 capability backend："
                       f"{why_not(benchmark) or '未实现'}")
    mod = __import__(b[0])
    cls = getattr(mod, b[1])
    if b[1] == "AgentDojoCapability":
        return cls(task_id, benchmark=benchmark, budget=budget)
    return cls(task_id, budget=budget)
