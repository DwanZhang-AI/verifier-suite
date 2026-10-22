#!/usr/bin/env python3
"""`interactive_resettable` 能力层的统一 ABI（方案 §8.6 的 mode 2）。

## 三个 API，规格原文

> generator 通过注册的 `inspect/run_public/reset` API 与临时公开环境交互。
> 每次 `run_public` 后必须可 `reset` 到同一 `initial_state_hash`；
> **API 返回值经过泄漏扫描**。

同一套 ABI 覆盖四个来源，backend 各自实现：

    inspect()        读环境的公开面（工具表、初始状态、仓库文件树）
    run_public(x)    在临时环境里执行一段东西，返回可观测结果
    reset()          回到 initial_state_hash

## 为什么必须有泄漏扫描，而不是"小心一点"

给执行能力，等于把真实环境交到被测方手里，而**判据往往就住在环境里**：

    τ²          task.evaluation_criteria.actions   —— gold 动作序列
    AppWorld    evaluation.py 里的 test.case 断言
    AgentDojo   task.utility / task.security
    SWE         FAIL_TO_PASS / PASS_TO_PASS 清单、eval.sh、gold patch

一次疏忽就把答案给出去了，而且**不会报错**：模型分数会变好，看起来像"给了
环境所以变强了"。所以泄漏扫描不是防御性编程，是这个实验成立的前提 ——
`scrub()` 在每个返回值上跑，命中即抛，不是静默删除。

## 三条不变量

    1  `run_public` 之后 `reset()`，`state_hash()` 必须回到 initial
    2  返回值不含任何 oracle 面（由各 backend 声明 FORBIDDEN 并实撞验证）
    3  预算受控：每次 episode 的 run_public 次数有上限，超了抛 BudgetExceeded

第 3 条是规格 §6.5 的公平性要求 —— 不同 harness 档必须统一
`verifier execution budget`，否则"给了环境"会退化成"给了更多算力"。
"""
import hashlib
import json
import re


class LeakDetected(Exception):
    """返回值命中 oracle 面。**抛出而不是静默过滤** —— 静默过滤会让
    一次真实的泄漏变成一次看不见的删除，而我们再也不知道它发生过。"""


class BudgetExceeded(Exception):
    pass


def canon(obj):
    """稳定序列化，用于 state hash。"""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), default=str)


def state_hash(obj):
    return "sha256:" + hashlib.sha256(canon(obj).encode()).hexdigest()


class Capability:
    """backend 基类。子类必须实现 `_inspect / _run / _reset / _state`
    并声明 `FORBIDDEN`（一组必须不出现在任何返回值里的字符串/正则）。"""

    FORBIDDEN = ()          # 子类覆盖：oracle 面的字面量或正则
    MAX_RUNS = 20           # 每 episode 的 run_public 预算

    def __init__(self, task_id, budget=None):
        self.task_id = task_id
        self.budget = self.MAX_RUNS if budget is None else budget
        self._runs = 0
        self._initial = None
        self.reset()

    # ---- 子类实现 ----------------------------------------------------
    def _inspect(self, what=None):
        raise NotImplementedError

    def _run(self, payload):
        raise NotImplementedError

    def _reset(self):
        raise NotImplementedError

    def _state(self):
        raise NotImplementedError

    # ---- 公开 API ----------------------------------------------------
    def inspect(self, what=None):
        # inspect 描述环境本身，调用方没给任何输入 —— 全量扫描。
        return self._scrub(self._inspect(what))

    def run_public(self, payload):
        if self._runs >= self.budget:
            raise BudgetExceeded(
                f"run_public 预算已用尽（{self.budget} 次）—— "
                f"预算受控是 harness 公平性要求（规格 §6.5），不是可选项")
        self._runs += 1
        # **不可能向一个人泄漏他自己刚给你的东西。**
        #
        # 跑一条候选轨迹时，返回的 tool_calls 当然含该候选的参数值；
        # 如果这条候选恰好是 gold，那些值就等于 gold 的取值，
        # 全量扫描会当场报泄漏 —— 而 verifier 手里本来就有这条候选的
        # payload。把它算成泄漏，`run_public` 对 gold 永远不可用。
        #
        # 所以 `run_public` 的扫描要减去输入回声：命中 FORBIDDEN 但
        # **同时出现在输入里**的，不是泄漏。
        return self._scrub(self._run(payload),
                           echo="\x00".join(_strings(payload)))

    def reset(self):
        self._reset()
        h = state_hash(self._state())
        if self._initial is None:
            self._initial = h
        elif h != self._initial:
            # **reset 不幂等就不是 `interactive_resettable`。**
            # 规格 conformance 第 2 条要求 reset 后 state hash 一致；
            # 不一致时必须抛，否则后面每一次比较都建立在漂移的初态上。
            raise RuntimeError(
                f"reset 不幂等：initial={self._initial} 现在={h}")
        return h

    def close(self):
        """拆掉环境。**基类必须有这个方法。**

        原先只有 `cap_swe` / `cap_tb` 各自定义了 `close`，`cap_appworld`
        定义的是 `_close`，τ²/AgentDojo 两个都没有。而调用方（broker 与
        generator）写的是 `try: cap.close() except Exception: pass` ——
        于是 AppWorld 每次都抛 `AttributeError` 并被吞掉，
        **世界从来没被拆过**。

        后果不是报错，是**后面的题起不来**：实测 28 道 AppWorld 里 14 道
        在判定期 `能力层子进程未就绪`，而单独手动起同一道题是成功的。
        没有 `cap_ready` 落盘的话，那 141 条候选会原样混进能力臂的统计，
        表现成"AppWorld 上模型不会用执行能力"。

        统一在基类分发到 `_close()`：子类只实现 `_close`，
        没有 `_close` 的就是真的无需拆卸。
        """
        fn = getattr(self, "_close", None)
        if fn is not None:
            fn()

    @property
    def initial_state_hash(self):
        return self._initial

    def runs_used(self):
        return self._runs

    # ---- 公开面 ------------------------------------------------------
    INSPECT_VARIANTS = (None, "tools", "state", "apis")

    def public_surface(self):
        """**公开面 = `_inspect()` 实际会返回的一切**，不是手工列的字段表。

        这个定义是被迫改出来的：手工枚举公开面时我连划错五次，
        每次都是漏了一项 ——

            gold 动作的函数名   其实是公开工具之一
            订单号             其实写在用户场景里
            日期               其实就在初始环境数据里
            task_id            其实是寻址这道题的方式

        每错一次，`inspect()` 就当场抛泄漏、能力层不可用。
        而手工枚举永远不可能穷尽，因为「公开面」的定义就散在
        `_inspect` 的实现里。

        **让它自己声明自己**：凡是 `_inspect` 能返回的，按定义就是公开的。
        这样这一整类错误在构造上消失，而不是靠下次更小心。
        """
        acc = []
        for w in self.INSPECT_VARIANTS:
            try:
                acc.append(self._inspect(w))
            except Exception:
                pass
        return acc

    # ---- 泄漏扫描 ----------------------------------------------------
    def _scrub(self, obj, echo=""):
        """**逐个字符串值比，不扫序列化后的整块。**

        第一版扫 `json.dumps(obj)`，于是一个本身就是 JSON 的 FORBIDDEN 项
        （gold 动作序列 `["a","b"]`）被塞进返回值后会再转义一次，
        变成 `{"leak":"[\"a\",\"b\"]"}` —— **原串不再匹配，扫描静默失效**。
        实撞时表现成"泄漏扫描没抓到"，而不是报错。

        本项目在发布泄漏检查上踩过一模一样的（原始文件文本 vs JSON 转义），
        所以这里改成遍历对象、对每个 `str` 叶子直接比对，
        转义层被绕开，不存在这类盲区。
        """
        leaves = list(_strings(obj))
        echo_leaves = echo if isinstance(echo, str) else canon(echo)
        for rule, pat in enumerate(self.FORBIDDEN):
            for leaf in leaves:
                if isinstance(pat, str):
                    hit = bool(pat) and pat in leaf and pat not in echo_leaves
                else:
                    hit = (bool(pat.search(leaf))
                           and not pat.search(echo_leaves))
                if hit:
                    # 只报规则序号：命中的内容本身（或其哈希）都不能出现在错误里。
                    raise LeakDetected(
                        f"{type(self).__name__} 的返回值命中 oracle 面（规则 #{rule}），已拦截")
        return obj


def _strings(obj, _depth=0):
    """递归取出所有 str 叶子（含 dict 的键）。深度上限防环。"""
    if _depth > 12:
        return
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                yield k
            yield from _strings(v, _depth + 1)
    elif isinstance(obj, (list, tuple, set)):
        for v in obj:
            yield from _strings(v, _depth + 1)
    elif obj is not None and not isinstance(obj, (int, float, bool)):
        yield str(obj)


def oracle_surface(secrets, public, min_len=6):
    """从 oracle 候选串里**减去公开面**，得到真正的 FORBIDDEN。

    ## 为什么必须共用一个定义

    这个边界我连划错三次，每次都是"公开面算窄了"：

        1  gold 动作的函数名 —— 其实是 16 个公开工具之一
        2  订单号 `#W2378156` —— 其实写在用户场景里
        3  日期 `2022-01-01` —— 其实就在初始环境数据里

    每一次的后果都一样：`inspect()` 当场抛泄漏，能力层整个不可用。
    而如果反过来划宽了（漏挡真 oracle），**不会有任何报错**，
    只会让模型分数变好，看起来像"给了环境所以变强了"。

    所以正确的原则只有一条：

    > **凡是调用方通过合法公开通道已经能拿到的，都不算泄漏。**

    `public` 应当传入该 backend 的**全部公开面**（题面 + inspect 会返回的
    一切），而不只是题面。

    参数
        secrets  oracle 侧的候选串（gold 取值、期望输出、动作序列……）
        public   公开面对象（任意嵌套结构，内部取其全部 str 叶子）
    """
    pub = "\x00".join(_strings(public))
    out = []
    for x in secrets:
        if isinstance(x, re.Pattern):
            out.append(x)
        elif isinstance(x, str) and len(x) >= min_len and x not in pub:
            out.append(x)
    return tuple(out)


def compile_forbidden(items):
    """把字面量与正则混合列表编译成扫描器。空串会匹配一切，直接丢掉 ——
    一个空的 FORBIDDEN 项会让扫描器对每个返回值都报泄漏，
    表现成"能力层全坏了"，而真实原因只是某个 oracle 字段恰好是空的。"""
    out = []
    for x in items:
        if isinstance(x, str):
            if x.strip():
                out.append(x)
        elif isinstance(x, re.Pattern):
            out.append(x)
    return tuple(out)
