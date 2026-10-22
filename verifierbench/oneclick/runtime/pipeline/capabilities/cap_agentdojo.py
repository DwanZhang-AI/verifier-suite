#!/usr/bin/env python3
"""AgentDojo 的 `interactive_resettable` backend。

## oracle 面

    task.ground_truth(env)   gold 的调用序列        ← 必挡
    task.utility(...)        判据谓词本身            ← 必挡（不暴露为 API）
    task.GROUND_TRUTH_OUTPUT 期望输出字面量          ← 必挡

公开面：`task.PROMPT`、套件的 11 个工具、环境对象的字段结构与取值。

## injection 题的额外注意

injection 任务用 `task.security(...)` 而不是 `utility`，且它判的是
"注入有没有得逞"。**两者都不暴露**；但环境终态照给 —— verifier 的活儿
正是从终态判断有没有被注入。

## reset

`suite.load_and_inject_default_environment({})` 每次现造一个新环境，
天然幂等。**不做增量回滚** —— 增量回滚要自己维护快照，而漏掉一个字段
就会让 `initial_state_hash` 悄悄漂移，那正是 conformance 第 2 条要防的。
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.dirname(HERE)
AB = os.path.dirname(PIPE)
sys.path[:0] = [f"{PIPE}/data/agentdojo", f"{PIPE}/data",
                f"{AB}/data/agentdojo", f"{AB}/data", HERE]

from vgb_env import Capability, oracle_surface          # noqa: E402


class AgentDojoCapability(Capability):

    def __init__(self, task_id, benchmark="AgentDojo user", budget=None):
        self.task_id = task_id
        self.suite_name, self.tid = task_id.split("/", 1)
        self.injection = str(benchmark).endswith("injection")
        self._suite = None
        self._task = None
        self._env = None
        self._load()
        super().__init__(task_id, budget)

    def _load(self):
        from agentdojo.task_suite.load_suites import get_suites
        import ad_gates as G
        self._G = G
        self._suite = get_suites(os.environ.get("VGB_AD_SUITE_VERSION", "v1.2")).get(self.suite_name)
        if self._suite is None:
            raise KeyError(f"AgentDojo 没有这个套件：{self.suite_name}")
        pool = (self._suite.injection_tasks if self.injection
                else self._suite.user_tasks)
        self._task = pool.get(self.tid)
        if self._task is None:
            raise KeyError(f"AgentDojo 没有这道题：{self.task_id}")

        # **公开面 = 题面 + 初始环境**，不只是题面。
        # 只用题面时，`2022-01-01` 这种 gold 参数值会被误判成 oracle ——
        # 它其实就写在 banking 的初始数据里，`inspect()` 本来就会返回。
        try:
            pre0 = self._suite.load_and_inject_default_environment({})
            pub_env = pre0.model_dump()
        except Exception:
            pub_env = {}
        pub = {"prompt": str(getattr(self._task, "PROMPT", "") or ""),
               "env": pub_env}
        forb = []
        gto = getattr(self._task, "GROUND_TRUTH_OUTPUT", "") or ""
        if isinstance(gto, str):
            forb.append(gto)
        try:
            pre = self._suite.load_and_inject_default_environment({})
            gt = self._task.ground_truth(pre)
            names = [getattr(c, "function", None) for c in (gt or [])]
            if len(names) >= 2:
                import json as _j
                forb.append(_j.dumps(names, ensure_ascii=False))
            for c in (gt or []):
                for v in (getattr(c, "args", None) or {}).values():
                    if isinstance(v, str):
                        forb.append(v)
        except Exception:
            # 构造 ground truth 失败不能让整个 backend 不可用 ——
            # 但**必须留痕**，否则 FORBIDDEN 为空会被当成"这题没有 oracle 面"。
            self.ground_truth_available = False
        else:
            self.ground_truth_available = True
        self.FORBIDDEN = oracle_surface(forb, pub)

    # ---- 子类实现 ----------------------------------------------------
    def _reset(self):
        self._env = self._suite.load_and_inject_default_environment({})

    def _state(self):
        try:
            return self._env.model_dump()
        except Exception:
            return {k: str(v)[:2000] for k, v in vars(self._env).items()}

    def _inspect(self, what=None):
        tools = []
        try:
            for t in (self._suite.tools or []):
                tools.append({"name": getattr(t, "name", str(t)),
                              "doc": (getattr(t, "description", "") or "")[:300]})
        except Exception:
            pass
        if what == "tools":
            return {"tools": tools}
        if what == "state":
            return {"state": self._state()}
        return {"suite": self.suite_name, "task_id": self.tid,
                "is_injection": self.injection,
                "prompt": str(getattr(self._task, "PROMPT", ""))[:3000],
                "n_tools": len(tools), "tools": tools,
                "initial_state": self._state()}

    def _run(self, payload):
        """跑一串调用，返回环境终态 —— **不判定对错**。"""
        from agentdojo.functions_runtime import FunctionCall
        modern = os.environ.get("VGB_PUBLIC_OBSERVATION_V2") == "1"
        include = payload.get("include_only") if isinstance(payload, dict) else None
        if include is not None and modern:
            if (not isinstance(include, list) or not include or
                    any(k not in ("n_calls", "observations", "final_state") for k in include)):
                raise ValueError("include_only must select n_calls, observations or final_state")
        calls = payload.get("calls") if isinstance(payload, dict) else payload
        if not isinstance(calls, list):
            return {"error": "payload 需要 {'calls': [{'function':..,'args':{..}}]}"}
        fc = []
        for c in calls:
            try:
                fc.append(FunctionCall(function=c["function"],
                                       args=c.get("args") or {}))
            except Exception as e:
                return {"error": f"调用格式错误：{type(e).__name__}"}
        try:
            if modern:
                from agentdojo.functions_runtime import FunctionsRuntime
                post = self._suite.load_and_inject_default_environment({})
                runtime = FunctionsRuntime(self._suite.tools)
                observations = []
                for c in fc:
                    try:
                        value, error = runtime.run_function(post, c.function, dict(c.args), raise_on_error=False)
                        value = json.loads(json.dumps(value, ensure_ascii=False,
                            default=lambda v: v.model_dump() if hasattr(v, "model_dump") else str(v)))
                        observations.append({"function": c.function, "output": value, "error": error})
                    except Exception as exc:
                        observations.append({"function": c.function, "output": None,
                                             "error": type(exc).__name__ + ": " + str(exc)[:200]})
            else:
                post = self._G.run_calls(self._suite, self._task, fc)
        except Exception as e:
            return {"error": f"{type(e).__name__}: {str(e)[:200]}"}
        try:
            st = post.model_dump()
        except Exception:
            st = {k: str(v)[:2000] for k, v in vars(post).items()}
        result = {"n_calls": len(fc), "final_state": st}
        if modern:
            result["observations"] = observations
        return {k: result[k] for k in include} if include is not None and modern else result
