#!/usr/bin/env python3
"""能力层 broker：把沙箱内 verifier 的文件 RPC 转给能力层子进程。

## 拓扑

    verifier（sandbox-exec：无网络、只能写 work）
        │  写 work/cap/req.<cid>.json，轮询 res.<cid>.json
        ▼
    broker（runner 进程里的线程，沙箱外）
        │  行式 JSON over stdin/stdout
        ▼
    能力层子进程（该来源自己的 venv；SWE/TB 还要 docker）

## 为什么不直接在 runner 进程里 import backend

五个 backend 分属四个 venv（tau2 / ad / aw / swe），runner 跑在系统
python 上，装不下它们的依赖。子进程是唯一干净的做法。

## Isolation contract

Judging creates one broker per task. Serial candidates reset the world and share the task-total budget.
Generation creates one broker per exploration episode. Child stdout is reserved
for JSON RPC; backend logs go to stderr. Close gives the backend time to release
its containers and worlds before terminating an unresponsive child.
"""
import json
import os
import subprocess
import threading
import re
import stat

# 能力层子进程必须在这么多秒内打出 `__READY__`，否则杀掉。
# **没有上限就等于没有守卫** —— 见 `_start` 里的注释：
# 缺这一行时父子进程一起挂死 3 小时 16 分，表现成"生成还在跑"。
READY_TIMEOUT_SEC = float(os.environ.get("VGB_CAP_READY_TIMEOUT", "420"))
import time

HERE = os.path.dirname(os.path.abspath(__file__))

SERVER = r'''
import json, sys, os
from contextlib import redirect_stdout
sys.path.insert(0, %(caps)r)
import registry as REG
from vgb_env import LeakDetected, BudgetExceeded
paging = os.environ.get("VGB_PUBLIC_OBSERVATION_V2") == "1"
if paging:
    from public_observation import ObservationStore
    pages = ObservationStore()
with redirect_stdout(sys.stderr):
    cap = REG.make(%(bm)r, %(tid)r, budget=%(budget)r)
sys.stdout.write("__READY__\n"); sys.stdout.flush()
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        req = json.loads(line)
        op = req.get("op")
        with redirect_stdout(sys.stderr):
            if op == "inspect":
                what = req.get("what")
                if paging and isinstance(what, dict):
                    res = {"ok": pages.page(what)}
                else:
                    res = {"ok": cap.inspect(what)}
            elif op == "run_public":
                res = {"ok": cap.run_public(req.get("payload") or {})}
            elif op == "reset":
                res = {"ok": {"state_hash": cap.reset()}}
            elif op == "close":
                break
            else:
                res = {"err": "unknown op: %%s" %% op}
            if paging and req.get("presentation") == "paged-v1" and "ok" in res:
                res = {"ok": pages.present(res["ok"])}
    except LeakDetected:
        res = {"err": "LeakDetected: response withheld"}
    except BudgetExceeded as e:
        res = {"err": "BudgetExceeded: " + str(e)}
    except Exception as e:
        res = {"err": type(e).__name__ + ": " + str(e)[:300]}
    sys.stdout.write(json.dumps(res, ensure_ascii=False, default=str) + "\n")
    sys.stdout.flush()
try:
    with redirect_stdout(sys.stderr):
        cap.close()
except Exception:
    pass
'''


class Broker:
    def __init__(self, benchmark, task_id, cap_dir, budget=None):
        import registry as REG
        self.dir = cap_dir
        self.proc = None
        self._stop = threading.Event()
        self._t = None
        self._closed = False
        self.stats = {"inspect": 0, "run_public": 0, "reset": 0,
                      "errors": 0, "leak_blocks": 0, "budget_blocks": 0,
                      "transport_errors": 0}
        os.makedirs(cap_dir, exist_ok=True)
        self._dir_fd = os.open(cap_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for f in os.listdir(cap_dir):
            if f.startswith(("req.", "res.")):
                try:
                    os.remove(os.path.join(cap_dir, f))
                except OSError:
                    pass
        code = SERVER % {"caps": HERE, "bm": benchmark, "tid": task_id,
                         "budget": budget}
        # **stderr 不能扔。** 第一版是 DEVNULL，于是子进程起不来时
        # 上层只拿到 `能力层子进程未就绪：''` —— 一个没有原因的错误。
        # 实测 28 道 AppWorld 里 14 道这样失败，查不到根因，
        # 只能靠手动复现。留一个临时文件接住它。
        import tempfile as _tf
        self._errf = _tf.NamedTemporaryFile(prefix="vgb-caperr-", suffix=".log",
                                            delete=False, mode="w+")
        try:
            self.proc = subprocess.Popen(
                [REG.interpreter(benchmark), "-c", code],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=self._errf, text=True,
                env=REG.env_for(benchmark), bufsize=1)
        except Exception:
            self.close()
            raise
        # **`readline()` 没有超时，会永久阻塞。**
        #
        # 子进程若卡在 docker（拉镜像、起容器、等网络）就永远不打
        # `__READY__`，父进程停在这一行 —— 表现成"生成还在跑"。
        # 实测：L3 × SWE 的第 4 道题上父子进程双双挂死 **3 小时 16 分**，
        # 父进程 CPU 累计 0.66s，容器 `Up 3 hours` 没退。
        #
        # 这是 §16 #4 / #19 / #23 的第四次实例，形状完全一样：
        # **守卫加在了会报错的那条路上，没加在会静默挂住的那条。**
        # 前三次分别是 `max_timeout_sec=inf`、超时值不一致、
        # per-read 超时冒充总时限；这次是"根本没有超时"。
        #
        # 用与 `generate_v2._call_with_deadline` 相同的办法：
        # 读操作丢进 daemon 线程，join(deadline)。
        _box = {}

        def _rd():
            try:
                # A dependency may write directly to fd 1 before Python redirect.
                while True:
                    line = self.proc.stdout.readline()
                    _box["line"] = line
                    if not line or line.strip() == "__READY__":
                        break
                    self._errf.write("startup stdout: " + line)
                    self._errf.flush()
            except Exception as e:                       # noqa: BLE001
                _box["line"] = f"__READ_ERROR__ {type(e).__name__}: {e}"

        _rt = threading.Thread(target=_rd, daemon=True)
        _rt.start()
        _rt.join(READY_TIMEOUT_SEC)
        if _rt.is_alive():
            try:
                self.proc.kill()
                self.proc.wait(timeout=10)
            except Exception:
                pass
            self.close()
            raise RuntimeError(
                f"能力层子进程 {READY_TIMEOUT_SEC}s 内未打出 __READY__ —— "
                f"已杀掉。多半卡在容器启动/网络上；"
                f"stderr 见 {self._errf.name}")
        line = _box.get("line")
        if (line or "").strip() != "__READY__":
            try:
                self._errf.flush()
                with open(self._errf.name) as f:
                    err = f.read()[-2500:].strip()
            except Exception:
                err = "(stderr 读不到)"
            self.close()
            raise RuntimeError(
                f"能力层子进程未就绪：stdout={line!r} stderr尾部={err!r}")
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()

    def reset_env(self, timeout=420):
        """Reset the existing backend between serial candidates; keep task budget.

        Route through the same file RPC queue as verifier calls. Direct stdin
        writes would race the broker reader and corrupt response ownership.
        """
        import uuid
        token = "reset_" + uuid.uuid4().hex
        request = os.path.join(self.dir, "req." + token + ".json")
        response = os.path.join(self.dir, "res." + token + ".json")
        tmp = request + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"cid": token, "seq": 1, "op": "reset"}, f)
        os.replace(tmp, request)
        deadline = time.monotonic() + timeout
        try:
            while time.monotonic() < deadline:
                if self.proc.poll() is not None:
                    raise RuntimeError("Capability process exited during reset")
                try:
                    with open(response) as f:out = json.load(f)
                    if out.get("seq") == 1:
                        if "err" in out:raise RuntimeError(out["err"])
                        return out["ok"]["state_hash"]
                except (FileNotFoundError, json.JSONDecodeError):
                    pass
                time.sleep(.02)
            raise TimeoutError("Capability reset timed out")
        finally:
            for name in (request, response, tmp):
                try:os.remove(name)
                except FileNotFoundError:pass

    def _loop(self):
        """轮询 `req.<cid>.json`，**每个客户端一条通道**。

        第一版全体候选共用 `req.json`，而 shim 的 `seq` 是进程内计数器、
        人人从 1 开始 —— runner 用 6 线程并发跑同一道题的候选、共享同一个
        cap_dir，于是后写的请求被下面这行 `seq == last` 静默丢掉，
        而丢掉的那个客户端读到 `res.json` 里 `seq == 1`，**把别人的答案
        当成自己的**。实测 6 并发 × 4 次：对上自己的 0/24。

        判定结果因此与候选无关，表现成"给了执行能力，判别力崩塌"。
        `seq` 现在只防同一客户端的自我错位，跨客户端靠文件名隔离。
        """
        last = {}                                   # cid -> 上一个 seq
        while not self._stop.is_set():
            try:
                names = [n for n in os.listdir(self._dir_fd)
                         if n.startswith("req.") and n.endswith(".json")]
            except OSError:
                names = []
            worked = False
            for name in names:
                try:
                    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self._dir_fd)
                    if not stat.S_ISREG(os.fstat(fd).st_mode):
                        os.close(fd)
                        continue
                    with os.fdopen(fd) as f:
                        req = json.load(f)
                except (OSError, json.JSONDecodeError):
                    continue
                if not isinstance(req, dict):continue
                cid, seq = req.get("cid"), req.get("seq")
                if not isinstance(cid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',cid) or name != f'req.{cid}.json' or type(seq) is not int or seq < 1:
                    continue
                if req.get('op') not in {'inspect','run_public','reset'}:continue
                if last.get(cid) == seq:
                    continue
                last[cid] = seq
                worked = True
                op = req.get("op")
                self.stats[op] = self.stats.get(op, 0) + 1
                try:
                    self.proc.stdin.write(json.dumps(
                        {k: v for k, v in req.items()
                         if k not in ("seq", "cid")}) + "\n")
                    self.proc.stdin.flush()
                    out = self.proc.stdout.readline()
                    if not out:
                        raise BrokenPipeError("Capability child exited")
                    res = json.loads(out)
                except Exception as e:
                    self.stats["transport_errors"] += 1
                    res = {"err": f"broker: {type(e).__name__}"}
                if "err" in res:
                    self.stats["errors"] += 1
                    if "LeakDetected" in res["err"]:
                        self.stats["leak_blocks"] += 1
                    if "BudgetExceeded" in res["err"]:
                        self.stats["budget_blocks"] += 1
                res["seq"], res["cid"] = seq, cid
                res_p = f"res.{cid}.json"
                import uuid
                tmp = '.broker-' + uuid.uuid4().hex
                try:
                    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=self._dir_fd)
                    with os.fdopen(fd,'w') as f:json.dump(res,f,ensure_ascii=False,default=str)
                    os.replace(tmp,res_p,src_dir_fd=self._dir_fd,dst_dir_fd=self._dir_fd)
                except OSError:
                    self.stats['transport_errors'] += 1
                    try:os.unlink(tmp,dir_fd=self._dir_fd)
                    except OSError:pass
            if not worked:
                time.sleep(0.03)

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._stop.set()
        if self._t is not None:
            self._t.join(timeout=1)
        proc = self.proc
        if proc is not None:
            try:
                if proc.poll() is None:
                    proc.stdin.write(json.dumps({"op": "close"}) + "\n")
                    proc.stdin.flush()
                    proc.wait(timeout=20)
            except (OSError, subprocess.TimeoutExpired, ValueError):
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=5)
            if self._t is not None:
                self._t.join(timeout=2)
            for stream in (proc.stdin, proc.stdout):
                if stream is not None:
                    stream.close()
        self._errf.close()
        if getattr(self,'_dir_fd',None) is not None:
            os.close(self._dir_fd)
            self._dir_fd=None
        # Retain the bounded startup diagnostics path for failed launches.
        if proc is not None and proc.returncode == 0:
            try:
                os.unlink(self._errf.name)
            except FileNotFoundError:
                pass
