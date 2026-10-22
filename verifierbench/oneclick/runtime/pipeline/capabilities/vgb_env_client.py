"""`vgb_env` —— 注入给 verifier 的客户端 shim（运行时能力）。

这个文件会被 runner 原样拷进 bundle 根目录，命名为 `vgb_env.py`，
于是 verifier 里 `import vgb_env` 就能用。

## 为什么走文件 RPC 而不是网络或直接 import

verifier 跑在 `sandbox-exec` 里：**无网络、只能写 work 目录**，
而且五个 backend 分属四个 venv、有两个还要 docker —— sandbox 里
既连不上也 import 不了。

work 目录是沙箱里唯一可写可读的地方，所以协议就落在那儿：

    work/cap/req.json     verifier 写请求（带自增 seq）
    work/cap/res.json     broker 写响应（seq 对上才算这次的）

broker 跑在沙箱外（runner 进程里），转发给能力层子进程。

## 通道必须**每个客户端一条**，seq 只在通道内唯一

    work/cap/req.<client>.json    该 verifier 写请求（带进程内自增 seq）
    work/cap/res.<client>.json    broker 只回给它

第一版所有 verifier 共用 `req.json` / `res.json`，而 `seq` 是**进程内**
全局、每个 verifier 都从 1 开始 —— runner 用 6 线程并发跑**同一道题**的
候选，它们共享同一个 cap_dir，于是：

* 后写的 `seq=1` 被 broker 的 `if seq == last: continue` **静默丢掉**；
* 它去读 `res.json`，看到 `seq == 1`，**把别人的答案当成自己的收下**。

实测 6 并发 × 4 次调用：broker 只收到 8/24，对上自己的 **0/24**，
拿到别人响应 10/24，其余超时。判定结果因此与候选无关 ——
表现成"给了执行能力，verifier 判别力崩塌"。

**跨进程的唯一性不能靠进程内计数器。** 客户端 id 进文件名，
seq 只用来防同一客户端的自我错位。
"""
import json
import os
import time
import uuid

_DIR = os.environ.get("VGB_CAP_DIR", "")
_TIMEOUT = float(os.environ.get("VGB_CAP_TIMEOUT", "300"))
_CID = f"{os.getpid()}-{uuid.uuid4().hex[:8]}"
_seq = 0


class CapabilityUnavailable(RuntimeError):
    pass


def available():
    """能力层是否接通。**verifier 应当先问再用** —— 没接通时
    `import vgb_env` 仍然成功，但调用会抛。"""
    return bool(_DIR) and os.path.isdir(_DIR)


def _rpc(op, **kw):
    global _seq
    if not available():
        raise CapabilityUnavailable(
            "vgb_env 未接通（本次运行没有 interactive_resettable 能力）")
    _seq += 1
    req = {"seq": _seq, "cid": _CID, "op": op, **kw}
    tmp = os.path.join(_DIR, f"req.{_CID}.tmp")
    with open(tmp, "w") as f:
        json.dump(req, f, ensure_ascii=False, default=str)
    # 原子替换，避免读到半个；文件名带 cid，别的 verifier 覆不掉
    os.replace(tmp, os.path.join(_DIR, f"req.{_CID}.json"))
    res_path = os.path.join(_DIR, f"res.{_CID}.json")
    t0 = time.time()
    while time.time() - t0 < _TIMEOUT:
        try:
            with open(res_path) as f:
                res = json.load(f)
            if res.get("seq") == _seq:
                if "err" in res:
                    raise RuntimeError(res["err"])
                return res.get("ok")
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        time.sleep(0.05)
    raise TimeoutError(f"vgb_env.{op} 超时（{_TIMEOUT}s）")


def inspect(what=None):
    """读环境公开面。"""
    return _rpc("inspect", what=what)


def run_public(payload):
    """在临时环境里执行一段东西，返回可观测结果。预算受控。"""
    return _rpc("run_public", payload=payload)


def run_appworld_solution(source):
    """Call the candidate's solution(apis, requester), consuming one run_public.

    execution_status=completed means invocation finished, NOT correctness.
    Verify the resulting state independently. This helper is AppWorld-only.
    """
    return run_public({"solution": source})


def reset():
    """回到 initial_state_hash。"""
    return _rpc("reset")
