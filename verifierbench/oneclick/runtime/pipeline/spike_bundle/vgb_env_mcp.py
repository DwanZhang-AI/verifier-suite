#!/usr/bin/env python3
"""把我们的能力层包成 **MCP server**（stdio / JSON-RPC 2.0）。

## 为什么是 MCP 而不是再写一个框架专属扩展

pi 刻意不内置 MCP，所以那边只能写 TS 扩展（`vgb_env_pi.ts`）。
但 Codex / opencode / OpenHands 都支持 MCP —— **这个文件写一次，
后面每加一个 harness 都能直接复用**，而 TS 扩展只对 pi 有效。

ALE 也是这个形态：「a unified CUA MCP bridge exposes 14 desktop-action
tools … as standard entries in the agent's tool system」。

## 语义与 pi 扩展**完全相同**

走的是同一条**文件 RPC**（`capabilities/vgb_env_client.py` 定义的协议）：

    $VGB_CAP_DIR/req.<cid>.json    本客户端写请求 {seq, cid, op, ...}
    $VGB_CAP_DIR/res.<cid>.json    broker 只回给它

同一个 broker、同一份 20 次 episode 预算、同一套泄漏扫描。
**这是刻意的**：S 轴要隔离的只有脚手架，能力层任何差异都会污染 Δ。

两条正确性要求逐字照搬 Python 客户端（那边用 0/24 的错配换来的）：

1 **cid 进文件名。** 共用 `req.json` 时，多个客户端的 `seq` 各自从 1 开始，
  broker 的去重会静默丢请求，客户端则读到别人的响应当成自己的。
2 **写请求原子替换**（tmp → rename），否则 broker 读到半个 JSON。

## 协议实现范围

只实现 harness 实际会用的三个方法：`initialize` / `tools/list` /
`tools/call`，外加吞掉 `notifications/*`。不做完整 MCP —— 多出来的表面
都是可能出错而不会被用到的代码。
"""
import json
import os
import sys
import time
import uuid

CAP_DIR = os.environ.get("VGB_CAP_DIR", "")
TIMEOUT = float(os.environ.get("VGB_CAP_TIMEOUT", "300"))
CID = f"{os.getpid()}-{uuid.uuid4().hex[:8]}"      # 每进程唯一，见上文第 1 条
_seq = 0
PAGED = os.environ.get("VGB_PUBLIC_OBSERVATION_V2") == "1"

TOOLS = [
    {"name": "inspect",
     "description": "Inspect the task environment's public surface. Pass "
                    "what=null for an overview. Oracle surfaces (official "
                    "test lists, eval scripts, gold patches) are blocked.",
     "inputSchema": {"type": "object", "properties": {
         "what": {"type": ["string", "null"],
                  "description": "What to inspect; null for an overview"}}}},
    {"name": "run_public",
     "description": "Execute something in a temporary copy of the environment "
                    "and return what was observed. Payload shape depends on "
                    "the source; call inspect first. Budget-limited.",
     "inputSchema": {"type": "object", "properties": {
         "payload": {"type": "object",
                     "description": "Source-specific, e.g. {\"cmd\": \"ls\"}"}},
         "required": ["payload"]}},
    {"name": "reset",
     "description": "Restore the environment to its initial state.",
     "inputSchema": {"type": "object", "properties": {}}},
]


if PAGED:
    TOOLS[0]["inputSchema"]["properties"]["what"]["type"] = ["string", "object", "null"]
    TOOLS[0]["description"] += " Large results are paged. Pass what={response_id, path:[], offset:0, limit:20} to read a saved public result; follow item.ref and next_offset. Pages do not rerun candidates."


def rpc(op, **kw):
    """文件 RPC —— 与 `vgb_env_client.py` / `vgb_env_pi.ts` 同一条通道。"""
    global _seq
    if not CAP_DIR or not os.path.isdir(CAP_DIR):
        raise RuntimeError("vgb_env 未接通（本次运行没有 "
                           "interactive_resettable 能力）")
    _seq += 1
    mine = _seq
    tmp = os.path.join(CAP_DIR, f"req.{CID}.tmp")
    with open(tmp, "w") as f:
        json.dump({"seq": mine, "cid": CID, "op": op,
                   **({"presentation": "paged-v1"} if PAGED else {}), **kw}, f,
                  ensure_ascii=False, default=str)
    os.replace(tmp, os.path.join(CAP_DIR, f"req.{CID}.json"))   # 原子替换
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


def call(name, args):
    if name == "inspect":
        return rpc("inspect", what=args.get("what"))
    if name == "run_public":
        return rpc("run_public", payload=args.get("payload") or {})
    if name == "reset":
        return rpc("reset")
    raise ValueError(f"unknown tool {name}")


def send(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        mid, method = req.get("id"), req.get("method", "")
        # 通知类没有 id，**不能回响应** —— 回了会让对端协议错乱
        if mid is None:
            continue
        try:
            if method == "initialize":
                send({"jsonrpc": "2.0", "id": mid, "result": {
                    "protocolVersion": req.get("params", {}).get(
                        "protocolVersion", "2024-11-05"),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "vgb-env", "version": "1.0"}}})
            elif method == "tools/list":
                send({"jsonrpc": "2.0", "id": mid,
                      "result": {"tools": TOOLS}})
            elif method == "tools/call":
                p = req.get("params") or {}
                out = call(p.get("name"), p.get("arguments") or {})
                txt = out if isinstance(out, str) else json.dumps(
                    out, ensure_ascii=False, indent=None if PAGED else 1,
                    separators=(",", ":") if PAGED else None, default=str)
                send({"jsonrpc": "2.0", "id": mid, "result": {
                    "content": [{"type": "text", "text": txt or "null"}]}})
            elif method == "ping":
                send({"jsonrpc": "2.0", "id": mid, "result": {}})
            else:
                send({"jsonrpc": "2.0", "id": mid, "error": {
                    "code": -32601, "message": f"method not found: {method}"}})
        except Exception as e:
            # **业务错误要作为 tool result 回去，不是协议错误。**
            # LeakDetected / BudgetExceeded 是模型该看到并据以调整的信息；
            # 报成 JSON-RPC error 会让有些 harness 直接中断整轮。
            if method == "tools/call":
                send({"jsonrpc": "2.0", "id": mid, "result": {
                    "content": [{"type": "text",
                                 "text": f"{type(e).__name__}: {e}"}],
                    "isError": True}})
            else:
                send({"jsonrpc": "2.0", "id": mid, "error": {
                    "code": -32603, "message": f"{type(e).__name__}: {e}"}})


if __name__ == "__main__":
    main()
