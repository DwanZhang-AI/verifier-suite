#!/usr/bin/env python3
"""SWE-bench 的 `interactive_resettable` backend（Docker）。

## 这是整个 v2 实验的核心

v1 里 code form 的 verifier 只拿到一个 diff 字符串和 `{repo, base_commit}` ——
**跑 FAIL_TO_PASS 在设计上不可能**。三个模型分别退到「凭记忆匹配关键词」
「手写 diff 解析器」「git apply 到不存在的仓库」，后两条必然失败。

这个 backend 把仓库真的交出去。

## oracle 面 —— 这里最容易泄漏，因为判据就住在容器里

    FAIL_TO_PASS / PASS_TO_PASS   受评测试清单        ← 必挡
    eval.sh                        官方评测脚本        ← 必挡（容器里就有）
    gold patch                     正确解              ← 必挡
    /root/run_tests.sh 之类         官方入口            ← 必挡

**`run_public` 只跑调用方自己写的命令**，且返回值过泄漏扫描。
调用方可以 `git apply` 候选的 patch、写自己的测试、跑 pytest ——
但它拿不到"哪些测试算数"。

## reset 靠镜像不可变

每题一个预构建 instance 镜像（本地已有 500 个），容器销毁重建即回初态，
不需要自己做快照回滚。**这正是 `interactive_resettable` 最干净的实现形态**：
reset 的幂等性由镜像层保证，而不是由我们记得回滚哪些文件。

## 成本

起停一个容器约几秒。预算默认 8 次 —— 比 state 那三个低，因为贵。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.dirname(HERE)
AB = os.path.dirname(PIPE)
sys.path[:0] = [HERE]

from vgb_env import Capability, oracle_surface           # noqa: E402

# 容器里绝不能被读到的路径 —— 官方评测脚本与测试清单都在这些位置。
# 单条命令超时（对齐 Terminal-Bench 的 max_timeout_sec）与**整道题**的
# 累计执行预算。后者是防挂死的，前者防单条命令。
EXEC_TIMEOUT_SEC = 180
TOTAL_EXEC_BUDGET_SEC = 1800

BLOCKED_PATHS = ("/eval.sh", "/run_tests.sh", "/root/run_tests.sh",
                 "/root/eval.sh", "/eval_script", "/root/patch.diff")


def _sh(*args, timeout=180):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _sh_out(*args, timeout=180):
    """只要 stdout。`docker run -d` 在 arm64 上会往 stderr 写平台警告，
    把 stdout+stderr 拼起来再取最后一行，拿到的是警告不是容器 ID。"""
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


class SWECapability(Capability):

    MAX_RUNS = 8

    def __init__(self, instance_id, budget=None, image=None):
        self.instance_id = instance_id
        self.image = image or self._guess_image(instance_id)
        self.container = None
        self._inst = None
        self._load_instance()
        super().__init__(instance_id, budget)

    @staticmethod
    def _guess_image(iid):
        # swebench 的命名：sweb.eval.<arch>.<repo>_1776_<name>:latest
        import json
        from pathlib import Path
        records = json.loads((Path(__file__).resolve().parents[2] / "environment/observed_execution_host.json").read_text())
        return records["swe_images"][iid]["repo_digests"][0]

    def _load_instance(self):
        from datasets import load_dataset
        ds = {r["instance_id"]: r for r in
              load_dataset("princeton-nlp/SWE-bench_Verified", split="test")}
        self._inst = ds.get(self.instance_id)
        if self._inst is None:
            raise KeyError(f"SWE 没有这道题：{self.instance_id}")

    def _build_forbidden(self):
        import json as _j
        inst = self._inst

        def lst(x):
            return _j.loads(x) if isinstance(x, str) else list(x or [])

        secrets = []
        # 受评测试清单：**逐条测试名 + 整条清单**都挡
        f2p, p2p = lst(inst["FAIL_TO_PASS"]), lst(inst["PASS_TO_PASS"])
        secrets.extend(f2p)
        secrets.append(_j.dumps(sorted(f2p), ensure_ascii=False))
        # PASS_TO_PASS 常有上千条且多是仓库里本就存在的测试名 —— 挡整条清单，
        # 不逐条挡（逐条会把"仓库里有哪些测试"这个公开事实也挡掉，
        # 而那是调用方 `ls tests/` 就能看到的）。
        secrets.append(_j.dumps(sorted(p2p), ensure_ascii=False))
        # gold patch
        for k in ("patch", "test_patch"):
            v = inst.get(k)
            if isinstance(v, str) and v.strip():
                secrets.append(v)
        pub = self.public_surface()
        self.FORBIDDEN = oracle_surface(secrets, pub, min_len=8)

    # ---- 子类实现 ----------------------------------------------------
    def _reset(self):
        if self.container:
            _sh("docker", "rm", "-f", self.container, timeout=60)
            self.container = None
        rc, out, err = _sh_out("docker", "run", "-d", "--rm",
                               "--network", "none", self.image,
                               "sleep", "3600", timeout=180)
        cid = ""
        for line in out.split("\n"):
            line = line.strip()
            if len(line) >= 12 and all(c in "0123456789abcdef" for c in line):
                cid = line
        if rc != 0 or not cid:
            raise RuntimeError(f"起容器失败 rc={rc}：{(err or out)[:200]}")
        self.container = cid
        # Cached instance images may contain committed setup residue or a dirty
        # working tree. Recreating that image alone is not a task reset.
        import shlex
        base = self._inst["base_commit"]
        rc, state = self._exec("cd /testbed && git reset --hard --quiet " + shlex.quote(base) +
                               " && git clean -fd && git rev-parse HEAD")
        if rc or base not in state.splitlines():
            _sh("docker", "rm", "-f", self.container, timeout=60)
            self.container = None
            raise RuntimeError("Cannot restore SWE task base commit: " + state[-500:])
        if not getattr(self, "FORBIDDEN", ()):
            self._build_forbidden()

    def _state(self):
        """仓库的 git 状态就是状态 —— HEAD + 工作区是否干净。

        **退化的指纹必须当场抛，不能当成一个合法状态。**
        实测踩过：容器 ID 取错导致每次 `docker exec` 都返回
        `No such container`，两次"状态"字符串相同 —— `reset` 幂等性检查
        于是平凡通过，报了一个漂亮的 True，而容器根本没起来。
        空覆盖与全覆盖在计数上长得一样，这是同一个坑。
        """
        rc, out = self._exec(
            "cd /testbed 2>/dev/null || cd $(ls -d /*/ | head -1); "
            "git rev-parse HEAD 2>/dev/null; "
            "git status --porcelain 2>/dev/null | head -50")
        st = out.strip()
        head = st.split("\n")[0] if st else ""
        if not (len(head) == 40 and all(c in "0123456789abcdef" for c in head)):
            raise RuntimeError(
                f"状态指纹退化（拿不到 git HEAD）：{st[:160]!r} —— "
                f"容器多半没起来；不能把错误串当成一个合法状态")
        return st

    def _exec(self, cmd, timeout=180):
        return _sh("docker", "exec", "-e", "LANG=C.UTF-8",
                   "-e", "LC_ALL=C.UTF-8", "-e", "PYTHONIOENCODING=utf-8",
                   "-e", "PYTHONUTF8=1", self.container, "bash", "-lc", cmd,
                   timeout=timeout)

    def _inspect(self, what=None):
        if what == "state":
            return {"git": self._state()}
        rc, tree = self._exec(
            "cd /testbed 2>/dev/null || cd $(ls -d /*/ | head -1); pwd; "
            "git log -1 --format=%H; ls")
        return {"instance_id": self.instance_id,
                "repo": self._inst.get("repo"),
                "base_commit": self._inst.get("base_commit"),
                "problem_statement":
                    str(self._inst.get("problem_statement", ""))[:8000],
                "workdir_listing": tree[:4000]}

    def _run(self, payload):
        """跑一条调用方自己写的 shell 命令。

        **官方评测入口被显式屏蔽** —— 调用方可以 apply patch、写自己的
        测试、跑 pytest，但读不到 `eval.sh` 和受评清单。
        """
        cmd = payload.get("cmd") if isinstance(payload, dict) else payload
        if not isinstance(cmd, str) or not cmd.strip():
            return {"error": "payload 需要 {'cmd': '<shell>'}"}
        for bad in BLOCKED_PATHS:
            if bad in cmd:
                return {"error": f"拒绝：{bad} 是官方评测入口，不在公开面内"}
        # **单条命令超时不够，还要有整道题的累计上限。**
        # 实测 `django__django-11734` 上某条命令把容器占住，单命令超时没能
        # 整组收掉，整个生成进程挂了 9.5 小时、CPU 0%。
        # 这与之前 TB 那次 `max_timeout_sec=inf` 的死锁同源：
        # **失败表现成"还在跑"，比报错更难发现。**
        import time as _t
        if not hasattr(self, "_t_spent"):
            self._t_spent = 0.0
        if self._t_spent > TOTAL_EXEC_BUDGET_SEC:
            return {"error": f"该题累计执行时间已超 {TOTAL_EXEC_BUDGET_SEC}s，"
                             f"拒绝继续（防单题挂死）"}
        t0 = _t.time()
        try:
            rc, out = self._exec(cmd, timeout=EXEC_TIMEOUT_SEC)
        except subprocess.TimeoutExpired:
            self._t_spent += EXEC_TIMEOUT_SEC
            # 超时后容器可能仍被占住 —— 重建，否则后续命令全部排队等死
            try:
                self._reset()
            except Exception:
                pass
            return {"error": f"命令超时（{EXEC_TIMEOUT_SEC}s），容器已重建"}
        self._t_spent += _t.time() - t0
        return {"exit_code": rc, "output": out[-20000:]}

    def _close(self):
        if self.container:
            _sh("docker", "rm", "-f", self.container, timeout=60)
            self.container = None
