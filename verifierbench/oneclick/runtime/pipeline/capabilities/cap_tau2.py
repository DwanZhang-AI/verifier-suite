#!/usr/bin/env python3
"""τ²-bench 的 `interactive_resettable` backend。

## 能给什么、必须挡什么

实测 τ² 的 task 对象上，oracle 面集中在 `evaluation_criteria`：

    actions            gold 的动作序列（含函数名与逐参数取值）  ← 必挡
    communicate_info   必须说出的信息                          ← 必挡
    reward_basis       哪几个分量算分                          ← 必挡

可以给的是环境的**公开面**：16 个工具的签名、初始 DB、DB 哈希。
这些对任何调用方都是可见的，不构成泄漏。

## 为什么 DB 终态可以给

verifier 的任务是"判断这条轨迹有没有正确改动状态"，而它连状态都看不到
（v1 就是这样）。给它读 DB 的能力，正是这个实验要测的东西。

关键在于：**给的是"读状态"的能力，不是"哪些状态改动算对"的答案**。
后者在 `evaluation_criteria.actions` 里，被 FORBIDDEN 挡住。

## reset 的实现

τ² 的环境由 `registry.get_env_constructor(domain)()` 现造，
每次重建即回到初态 —— 天然幂等，不需要自己做快照回滚。
`banking_knowledge` 域要固定 retrieval variant，否则每次取不同变体、
DB 哈希漂移，`reset` 幂等性检查会当场抛（这正是它该做的）。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.dirname(HERE)
AB = os.path.dirname(PIPE)
sys.path[:0] = [f"{PIPE}/data/tau2_full", f"{PIPE}/data",
                f"{AB}/data/tau2_full", f"{AB}/data", HERE]

from registry import env_for
# Configure before tau2 imports its module-level dataset paths.
os.environ["TAU2_DATA_DIR"] = env_for("τ²-bench")["TAU2_DATA_DIR"]

from vgb_env import Capability, oracle_surface          # noqa: E402


class Tau2Capability(Capability):
    """`inspect / run_public / reset`，作用于一个 τ² 域环境。"""

    def __init__(self, task_id, budget=None):
        self.task_id = task_id
        self.domain, self.tid = task_id.split("/", 1)
        self._env = None
        self._task = None
        self._load_task()
        super().__init__(task_id, budget)

    def _load_task(self):
        import tau2_all as A
        from tau2.registry import registry as R
        if self.domain == "banking_knowledge":
            from tau2.domains.banking_knowledge.environment import (
                get_environment as _ge)

            def fixed(*a, **k):
                k.pop("retrieval_variant", None)
                return _ge(*a, retrieval_variant=A.BANKING_VARIANT, **k)
            R._domains[self.domain] = fixed
        self._R = R
        self._A = A
        tasks = {t.id: t for t in R.get_tasks_loader(self.domain)()}
        self._task = tasks.get(self.tid)
        if self._task is None:
            raise KeyError(f"τ² 没有这道题：{self.task_id}")
        ec = self._task.evaluation_criteria
        # ---- 什么才真的算 oracle 面 --------------------------------------
        #
        # 第一版把 gold 动作的**函数名**也列进 FORBIDDEN，结果 `inspect()`
        # 当场抛泄漏 —— 因为 `find_user_id_by_name_zip` 就是 16 个**公开
        # 工具**之一，每个调用方都看得见。挡掉它，能力层直接没用了。
        #
        # 同理，参数值里的订单号（`#W2378156`）很可能就写在用户场景里
        # （"我收到的订单……"），那也是公开信息。
        #
        # 真正保密的只有两样：
        #   1 gold 动作的**序列**（哪几个工具、什么顺序）—— 整体序列化后当整串挡
        #   2 **公开题面里查不到**的参数值 / communicate_info
        #
        # 这一版是被泄漏扫描器自己抓出来的：一个过宽的 FORBIDDEN
        # 会让能力层表现成"全坏了"，而真实原因是判据面划错了。
        # 公开面 = 题面 + 用户场景 + **初始环境**（inspect 本来就会返回工具与
        # DB 状态；只算题面会把环境里本来就有的取值误判成 oracle）。
        try:
            _env0 = self._new_environment()
            _tools = [getattr(t, "name", str(t)) for t in
                      (_env0.get_tools() or [])]
            _dbh = _env0.get_db_hash()
            _policy = _env0.get_policy()
            _schemas = [t.openai_schema for t in (_env0.get_tools() or [])]
        except Exception:
            _tools, _dbh, _policy, _schemas = [], "", "", []
        pub = {"description": str(getattr(self._task, "description", "")),
               "user_scenario": str(getattr(self._task, "user_scenario", "")),
               "tools": _tools, "db_hash": _dbh,
               "domain_policy": _policy, "tool_schemas": _schemas}
        acts = [{"name": getattr(a, "name", None),
                 "arguments": getattr(a, "arguments", None)}
                for a in (getattr(ec, "actions", None) or [])]
        forb = []
        if len(acts) >= 2:
            # 整条序列（含顺序）—— 自然文本里不可能出现，只有泄漏才会
            import json as _j
            forb.append(_j.dumps([a["name"] for a in acts], ensure_ascii=False))
        for a in acts:
            for v in (a["arguments"] or {}).values():
                if isinstance(v, str):
                    forb.append(v)
        for c in (getattr(ec, "communicate_info", None) or []):
            if isinstance(c, str):
                forb.append(c)
        self.FORBIDDEN = oracle_surface(forb, pub)
        self._n_actions = len(acts)

    # ---- 子类实现 ----------------------------------------------------
    def _new_environment(self, messages=()):
        env = self._R.get_env_constructor(self.domain)()
        init = self._task.initial_state
        env.set_state(
            initialization_data=init.initialization_data if init else None,
            initialization_actions=init.initialization_actions if init else None,
            message_history=list(messages), strict=True)
        return env

    def _reset(self):
        self._env = self._new_environment()

    def _state(self):
        # DB 哈希就是 τ² 自己用来比状态的东西，直接借用。
        value = self._env.get_db_hash()
        if value is None:
            raise RuntimeError("Environment has no observable DB hash")
        return value

    def _inspect(self, what=None):
        """公开面：工具签名 + 当前 DB 哈希 + 题面。**不含 evaluation_criteria。**"""
        tools = []
        try:
            for t in (self._env.get_tools() or []):
                schema = dict(t.openapi_schema["function"]) if hasattr(t, "openapi_schema") else dict(t.openai_schema["function"])
                schema["doc"] = schema.get("description", "")
                tools.append(schema)
        except Exception as exc:
            raise RuntimeError("Cannot expose environment tools") from exc
        out = {"domain": self.domain, "n_tools": len(tools), "tools": tools,
               "db_hash": self._state(),
               "domain_policy": self._env.get_policy(),
               "retrieval_variant": self._A.BANKING_VARIANT if self.domain == "banking_knowledge" else None,
               "task_description": str(getattr(self._task, "description", "")),
               "user_scenario": str(getattr(self._task, "user_scenario", ""))}
        if what == "tools":
            return {"tools": tools}
        if what == "state":
            return {"db_hash": out["db_hash"]}
        return out

    def _run(self, payload):
        """在**临时环境**里重放一段 messages，返回可观测终态。

        不改动 `self._env` —— 每次 run 用自己的一份环境，
        这样 `reset` 之后 state hash 必然回到 initial（而不是靠调用方自觉）。
        """
        msgs = payload.get("messages") if isinstance(payload, dict) else payload
        if not isinstance(msgs, list):
            return {"error": "payload 需要 {'messages': [...]}"}
        from tau2.data_model.simulation import SimulationRun  # noqa: F401
        try:
            sim = self._A.run(self.tid, msgs)
            env = self._new_environment(sim.messages)
        except Exception as e:
            return {"error": f"{type(e).__name__}: {str(e)[:200]}"}
        # 只回可观测项：终态哈希 + 助手侧文本 + 实际发生的工具调用
        calls = []
        for m in (getattr(sim, "messages", None) or []):
            for tc in (getattr(m, "tool_calls", None) or []):
                calls.append({"name": getattr(tc, "name", None),
                              "arguments": getattr(tc, "arguments", None)})
        texts = [getattr(m, "content", None) for m in
                 (getattr(sim, "messages", None) or [])
                 if getattr(m, "role", "") == "assistant"]
        db = env.get_db_hash()
        return {"replay_mode": "strict_mutating_tools", "final_db_hash": db, "n_tool_calls": len(calls),
                "tool_calls": calls,
                "assistant_texts": [t for t in texts if t]}
