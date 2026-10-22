#!/usr/bin/env python3
"""AppWorld 的 `interactive_resettable` backend。

## oracle 面

    task.ground_truth        GroundTruth 对象（正确解法与期望状态）  ← 必挡
    w.evaluate()             TestTracker：passes / failures / requirement
                             —— **整个方法都不暴露为 API**

公开面正是 agent 本来就能看到的：`task.instruction`、`supervisor`、
`allowed_apps`、`app_descriptions`、`api_docs`。

## state 表示

使用 AppWorld 原生 ModelCollection.model_hashes 计算不透明摘要。
读取不改变环境，公开写操作改变摘要，reset 恢复初始摘要。
原生哈希缺失则明确报错，不用 ERR 字符串作为正常状态。
只返回摘要，不返回数据库记录或官方判据。

## 为什么 execute 的返回可以给

`w.execute(code)` 返回的是**代码自己打印的东西** —— 那是调用方写的代码
产生的，不含任何判据信息。真正要挡的是 `evaluate()`，而它根本不在 API 里。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.dirname(HERE)
AB = os.path.dirname(PIPE)
sys.path[:0] = [f"{AB}/data", HERE]

from registry import SRC
import uuid
os.environ.setdefault("APPWORLD_ROOT", os.path.join(SRC, "aw_root"))

from vgb_env import Capability, oracle_surface           # noqa: E402

# State identity uses native database model hashes, not a public API call.
# This returns one opaque digest and never exposes database records or grading data.


class AppWorldCapability(Capability):

    MAX_RUNS = 10          # 建世界比 τ²/AgentDojo 贵，预算收紧

    def __init__(self, task_id, budget=None):
        self._w = None
        self._task_id = task_id
        self._experiment_name = "vgb_cap_" + uuid.uuid4().hex
        super().__init__(task_id, budget)

    def _close(self):
        try:
            if self._w is not None:
                self._w.__exit__(None, None, None)
        except Exception:
            pass
        self._w = None

    def _reset(self):
        from appworld import AppWorld
        self._close()
        self._w = AppWorld(task_id=self._task_id,
                           experiment_name=self._experiment_name)
        self._w.__enter__()
        if not getattr(self, "FORBIDDEN", ()):
            self._build_forbidden()

    def _build_forbidden(self):
        t = self._w.task
        # 公开面由 `_inspect` 自己声明 —— 手工列字段表漏过五次。
        pub = self.public_surface() + [
            str(getattr(t, "app_descriptions", "")),
            str(getattr(t, "api_docs", ""))]
        gt = getattr(t, "ground_truth", None)
        secrets = []
        if gt is not None:
            # GroundTruth 对象的字符串化就含正确解法；整体与逐字段都挡。
            secrets.append(str(gt))
            for f in dir(gt):
                if f.startswith("_"):
                    continue
                try:
                    v = getattr(gt, f)
                except Exception:
                    continue
                if isinstance(v, str):
                    secrets.append(v)
                elif isinstance(v, (list, tuple)):
                    secrets.extend(str(x) for x in v)
        self.FORBIDDEN = oracle_surface(secrets, pub, min_len=8)

    def _state(self):
        from appworld.collections.models import ModelCollection
        from appworld_state import fingerprint
        return fingerprint(ModelCollection.model_hashes(self._w.models))

    def _inspect(self, what=None):
        if what == "execution":
            return {"probe": {"code": "Python code executed as a cell; functions are NOT auto-called"},
                    "candidate": {"solution": "Python source defining solution(apis, requester)"},
                    "entrypoint": "solution(apis, requester)",
                    "completed_is_correct": False}
        t = self._w.task
        base = {"task_id": self._task_id,
                "instruction": str(getattr(t, "instruction", "")),
                "supervisor": str(getattr(t, "supervisor", "")),
                "allowed_apps": list(getattr(t, "allowed_apps", []) or [])}
        if what == "apis":
            return {"api_docs": str(getattr(t, "api_docs", ""))}
        if what == "state":
            return {"fingerprint": self._state()}
        return base

    def _run(self, payload):
        """在世界里执行一段 Python，返回它自己打印的东西。

        **不调用 `evaluate()`** —— 那是判据。调用方要判定，得自己从
        API 读状态然后下结论，这正是被测能力。
        """
        if isinstance(payload, dict) and "solution" in payload:
            if set(payload) != {"solution"}:
                return {"execution_status": "error", "error": "solution payload must have exactly one key"}
            from appworld_execution import execute_solution
            return execute_solution(self._w, payload["solution"])
        code = payload.get("code") if isinstance(payload, dict) else payload
        if not isinstance(code, str) or not code.strip():
            return {"error": "payload 需要 {'code': '<python>'}"}
        try:
            out = self._w.execute(code)
        except Exception as e:
            return {"error": f"{type(e).__name__}: {str(e)[:200]}"}
        # Keep structured public observations intact. The broker scrubs the full
        # result; model-facing pagination belongs to ObservationStore.
        return {"output": str(out)}
