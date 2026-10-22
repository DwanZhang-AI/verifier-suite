#!/usr/bin/env python3
"""v2 的预算与守卫。**每个数字都有出处，不拍脑袋。**

## 为什么不用轮数当预算

SWE-agent 明确弃用步数作为停止信号，理由是：

> 步数在模型之间差异极大 —— Claude 用少而长的步，GPT-4-Turbo 用多而短的步。

它改用 `per_instance_cost_limit = $3.00`，并把 `per_instance_call_limit`
设为 0（不限 LLM 调用次数）。

我们四个模型走三条不同网关、单价不一，按美元设限会让不同模型拿到**不同的
实际预算** —— 那正是规格 §6.5「harness 公平性」要禁止的。所以：

    预算（会绑定，影响公平性）   run_public 次数 · 单次超时 · 返回截断
    守卫（不该绑定，只防失控）   连续无进展 · 轮数天花板

**轮数天花板是守卫不是预算。** 它一旦真的绑定，就是要报的异常，
不是正常收尾 —— 所以记 `turn_cap_hit`，跑完必须看它是不是 0。

## 出处

    RUN_PUBLIC            BFCL `MAXIMUM_STEP_LIMIT = 20`
                          （容器贵的两家减到 8）
    EXEC_TIMEOUT_SEC      Terminal-Bench `max_timeout_sec = 180.0`
    MAX_OBSERVATION       SWE-agent `max_observation_length = 100000`
    NO_PROGRESS_TURNS     SWE-agent `max_consecutive_execution_timeouts = 5`
                          （我们的 run_public 粒度更粗，收紧到 3）
    TURN_CAP              无出处 —— 纯失控守卫，正常不该碰到
"""

# run_public 预算：**每条候选**，不是每道题。
#
# 第一版按「每道题 20 次」给，而每题恰好有 20 条候选 —— 于是一个每条候选
# 调一次 run_public 的 verifier 判到最后一条时预算刚好耗尽，只要某条多调
# 一次（先 reset 再 run），后面全部拿不到执行结果、落成 FAIL。
# 强制臂因此测出 VDC 7.414（vs 禁止臂 2.914），看起来像
# 「强制执行让 verifier 变差」—— 实际测的是预算耗尽。
#
# 出处也套错了粒度：`BFCL MAXIMUM_STEP_LIMIT = 20` 指的是**单次任务**的
# 步数上限，对应这里的**单条候选**，不是一整道题。
RUN_PUBLIC = {
    "τ²-bench": 20,
    "AgentDojo user": 20,
    "AgentDojo injection": 20,
    "AppWorld": 10,             # 建世界比另外两个进程内的贵
    "SWE-bench Verified": 8,    # 容器
    "Terminal-Bench": 8,        # 容器 + 可能联网
    # ExploitBench 也是容器来源，但**不按容器价减到 8**：
    # `cap_exploitbench` 每道题只起一次容器（`_reset` 里 `docker run -d`），
    # 每次 `run_public` 只是往常驻容器里 `docker exec` 一次 d8 —— 秒级，
    # 与 τ²/AgentDojo 的进程内调用同量级，不是 SWE 那种每次都要在容器里
    # 跑测试套件。按"容器"这个标签减到 8 是按名字定预算，不是按代价定。
    # **写进表里而不是靠 RUN_PUBLIC_DEFAULT 兜底**：兜底值是个隐式决定，
    # 改动 default 时会连带改掉这里，而没人会注意到。
    "ExploitBench": 20,
}
RUN_PUBLIC_DEFAULT = 20

# ---- 探索期与判定期是两个不同的预算 --------------------------------
#
# 判定期（verifier 判每一条候选）按**每条候选**给 —— 见 RUN_PUBLIC。
# 探索期（generator 写代码前摸环境）是**一次 episode**，与候选数无关。
#
# 第一版让探索期误用了每候选值：SWE 因此只有 8 次探索预算，
# 实测 `run_public` 中位 9、**预算拦截 48 次**（50 道题几乎每题都撞墙），
# 而 τ² 那边有 20 次、只撞过 1 次。两臂探索预算不对等，
# 跨来源比较会把"参数错配"读成"SWE 上执行能力更/更不有用"。
#
# 统一取 20 = `BFCL MAXIMUM_STEP_LIMIT`，其语义正是**单次任务 episode**
# 的步数上限 —— 与探索期一一对应。**对所有来源相同**，
# 否则跨来源的使用率与效果就不可比（规格 §6.5 的 harness 公平性）。
EXPLORE_RUN_PUBLIC = 20

EXEC_TIMEOUT_SEC = 180.0        # Terminal-Bench
MAX_OBSERVATION = 100_000       # SWE-agent
NO_PROGRESS_TURNS = 3           # 连续这么多轮不调工具 → 强制交付
TURN_CAP = 40                   # 失控守卫，不是预算
# 单题墙钟上限：纯防挂死。容器类来源上单命令超时收不掉被占住的容器，
# 实测一道 SWE 题挂了 9.5 小时。绑定即异常，记 wall_clock_hit。
TASK_WALL_CLOCK_SEC = 1800

# 每轮给模型的最大输出 token（防单轮爆炸；不是总预算）
MAX_TOKENS_PER_TURN = 8192


def run_public_budget(benchmark, n_candidates=1):
    """Task-total execution budget, shared by serial candidates after world reset.

    The historical aggregate is preserved: per-candidate allowance times the
    number of scored candidates. Reset does not replenish this allowance.
    """
    return RUN_PUBLIC.get(benchmark, RUN_PUBLIC_DEFAULT) * max(1, n_candidates)


def per_candidate_budget(benchmark):
    return RUN_PUBLIC.get(benchmark, RUN_PUBLIC_DEFAULT)


def as_manifest():
    """冻结清单里要原样记下来 —— 换了预算，v2 的数就不是同一批数。"""
    return {
        "run_public_per_candidate": dict(RUN_PUBLIC),
        "explore_run_public": EXPLORE_RUN_PUBLIC,
        "run_public_scope": "每题共享总预算（基准额度 × 计分候选数）；题内串行，reset 不补充额度",
        "run_public_default": RUN_PUBLIC_DEFAULT,
        "exec_timeout_sec": EXEC_TIMEOUT_SEC,
        "max_observation_chars": MAX_OBSERVATION,
        "no_progress_turns": NO_PROGRESS_TURNS,
        "turn_cap": TURN_CAP,
        "task_wall_clock_sec": TASK_WALL_CLOCK_SEC,
        "max_tokens_per_turn": MAX_TOKENS_PER_TURN,
        "sources": {
            "run_public": "BFCL MAXIMUM_STEP_LIMIT=20（单次任务的步数上限，"
                          "对应单条候选）；容器来源减至 8/10",
            "explore_run_public": "BFCL MAXIMUM_STEP_LIMIT=20（单次 episode），"
                                  "对所有来源相同以保证跨来源可比",
            "exec_timeout_sec": "Terminal-Bench max_timeout_sec=180.0",
            "max_observation_chars": "SWE-agent max_observation_length=100000",
            "no_progress_turns":
                "SWE-agent max_consecutive_execution_timeouts=5，收紧到 3",
            "turn_cap": "无出处；失控守卫，绑定即异常（记 turn_cap_hit）",
        },
        "no_turn_budget_rationale":
            "SWE-agent 明确弃用步数作停止信号（步数在模型间差异极大），"
            "改用成本；我们四个模型走三条网关单价不一，按美元设限会让"
            "不同模型拿到不同实际预算，违反规格 §6.5 的 harness 公平性。",
    }
