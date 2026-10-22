#!/usr/bin/env python3
"""能力层的 **shell 命令**形态 —— 给 mini-swe-agent 用。

## 为什么要有这一份

π 用原生工具循环（`vgb_env_pi.ts`）、OpenClaw 用 MCP（`vgb_env_mcp.py`），
而 **mini-swe-agent 的设计里只有一个 bash 工具**。把它改造成"也有三个原生
工具"就不是 mini-swe 了 —— 那样测的是"被我们改过的 mini-swe"。

所以这里把同一个能力层包成命令行：

    vgb_env inspect [--what X]
    vgb_env run_public --payload '{"cmd": "ls"}'
    vgb_env reset

**通道、broker、预算与另外两个 harness 完全相同**（同一份
`$VGB_CAP_DIR` 文件 RPC），差别只在 agent 看到的**形态**——
而形态差异正是 scaffold 轴要测的东西，不是要消除的东西。

## 与 `vgb_env_mcp.py` 逐字同源

`rpc()` 的实现是从那边抄过来的**同一段**：同样的 `seq/cid` 协议、
同样的原子替换、同样的超时。两份实现漂移会让两条线的能力层行为不同，
而那种差异无法归因到 scaffold。
"""
import argparse
import json
import os
import sys
import time
import uuid

CAP_DIR = os.environ.get("VGB_CAP_DIR", "")
CID = os.environ.get("VGB_CID") or uuid.uuid4().hex[:8]
TIMEOUT = float(os.environ.get("VGB_CAP_TIMEOUT", "900"))
_SEQ_FILE = os.path.join(CAP_DIR, f"seq.{CID}") if CAP_DIR else ""


def _next_seq():
    """序号必须跨进程递增 —— 每次 shell 调用都是新进程，不能用内存计数。"""
    n = 0
    try:
        n = int(open(_SEQ_FILE).read().strip())
    except Exception:
        pass
    n += 1
    with open(_SEQ_FILE, "w") as f:
        f.write(str(n))
    return n


def rpc(op, **kw):
    if not CAP_DIR or not os.path.isdir(CAP_DIR):
        raise RuntimeError("vgb_env 未接通（本次运行没有 "
                           "interactive_resettable 能力）")
    mine = _next_seq()
    tmp = os.path.join(CAP_DIR, f"req.{CID}.tmp")
    with open(tmp, "w") as f:
        json.dump({"seq": mine, "cid": CID, "op": op, **kw}, f,
                  ensure_ascii=False, default=str)
    os.replace(tmp, os.path.join(CAP_DIR, f"req.{CID}.json"))
    res_path = os.path.join(CAP_DIR, f"res.{CID}.json")
    t0 = time.time()
    while time.time() - t0 < TIMEOUT:
        try:
            with open(res_path) as f:
                res = json.load(f)
            if res.get("seq") == mine:
                if "err" in res:
                    raise RuntimeError(res["err"])
                return res.get("ok")
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        time.sleep(0.05)
    raise TimeoutError(f"vgb_env.{op} 超时（{TIMEOUT}s）")


def main():
    ap = argparse.ArgumentParser(prog="vgb_env",
                                 description="Task environment access.")
    sub = ap.add_subparsers(dest="op", required=True)
    p_i = sub.add_parser("inspect", help="Read-only view of the environment.")
    p_i.add_argument("--what", default=None)
    p_r = sub.add_parser("run_public", help="Execute against the environment. "
                                            "Budget-limited.")
    p_r.add_argument("--payload", required=True,
                     help='JSON, source-specific, e.g. \'{"cmd": "ls"}\'')
    sub.add_parser("reset", help="Restore the environment to initial state.")
    a = ap.parse_args()
    try:
        if a.op == "inspect":
            out = rpc("inspect", what=a.what)
        elif a.op == "run_public":
            try:
                payload = json.loads(a.payload)
            except json.JSONDecodeError as e:
                print(f"ERROR: --payload 不是合法 JSON: {e}", file=sys.stderr)
                return 2
            out = rpc("run_public", payload=payload)
        else:
            out = rpc("reset")
    except Exception as e:
        # **错误走 stderr + 非零退出** —— mini-swe 靠 returncode 判断成败，
        # 把错误印到 stdout 会让它以为成功了。
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(json.dumps(out, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
