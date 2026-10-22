#!/usr/bin/env python3
"""Terminal-Bench 的 `interactive_resettable` backend（Docker）。

## 与 SWE 的关键差别：`/tests` 就是判据本身

    SWE   FAIL_TO_PASS 是从仓库里**挑**哪些测试算数 —— 测试文件本身
          是公开的仓库内容，`ls tests/` 谁都看得到
    TB    `/tests/test_outputs.py` **就是评分标准** ——
          给了它，等于把答案原样交出去

所以 TB 上整个 `/tests` 目录、`run-tests.sh`、`solution.*` 全部屏蔽。
调用方能拿到的是任务环境本身（`/app` 及其内容）和题面，
要判定就得自己写检查 —— 那正是被测能力。

## 镜像

任务镜像每题现 build（`client/Dockerfile`），但层缓存命中后约 2 秒。
基础镜像 `ghcr.io/laude-institute/t-bench/*` 本地已有。

## 网络

TB 的题里有一批在解题时联网装包，而本机出网经企业 SWG 做 TLS 拦截。
容器起来后注入企业根证书（与 PoolAgent 同一份），否则 `run_public`
里任何 `pip install` 都会 CERTIFICATE_VERIFY_FAILED。
**这是环境干预，要记进冻结清单**（v1 已记，v2 沿用）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.dirname(HERE)
AB = os.path.dirname(PIPE)
from registry import SRC
TASKS = f"{SRC}/terminal-bench/original-tasks"
CERTS = f"{SRC}/scripts/certs/corp_roots.crt"
sys.path[:0] = [HERE]

from vgb_env import Capability, oracle_surface           # noqa: E402

# `/tests` 是判据本身；`solution.*` 是 gold。命令里出现即拒。
BLOCKED = ("/tests", "run-tests.sh", "solution.sh", "solution.yaml",
           "test_outputs.py", "/oracle")


def _sh(*args, timeout=300):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


class TBCapability(Capability):

    MAX_RUNS = 8

    def __init__(self, task_id, budget=None):
        self.task_id = task_id
        self.dir = f"{TASKS}/{task_id}"
        if not os.path.isdir(self.dir):
            raise KeyError(f"TB 没有这道题：{task_id}")
        # **两种布局都要支持。** 实测 60 道题里 59 道 Dockerfile 在任务根
        # 目录，只有 1 道在 `client/` —— 第一版按 `client/` 写死（那是我
        # 手工翻的第一道题的样子），于是绝大多数题 build 直接失败。
        # 「拿第一个样本当通例」在这里错得很彻底。
        self.build_ctx = (f"{self.dir}/client"
                          if os.path.isfile(f"{self.dir}/client/Dockerfile")
                          else self.dir)
        if not os.path.isfile(f"{self.build_ctx}/Dockerfile"):
            raise KeyError(f"TB 这道题没有 Dockerfile：{task_id}")
        self.image = f"v4v-tb:{task_id}"
        self.container = None
        super().__init__(task_id, budget)

    # ---- 子类实现 ----------------------------------------------------
    def _reset(self):
        if self.container:
            _sh("docker", "rm", "-f", self.container, timeout=60)
            self.container = None
        # Reuse the provisioned task image and pin its immutable id for this
        # episode. Rebuilding each reset can invoke the network and move the tag.
        if not getattr(self, "image_id", None):
            rc, out, err = _sh("docker", "image", "inspect", self.image,
                               "--format", "{{.Id}}", timeout=60)
            if rc != 0:
                rc, out, err = _sh("docker", "build", "-q", "-t", self.image,
                                   self.build_ctx, timeout=900)
                if rc != 0:
                    raise RuntimeError(f"build 失败：{(err or out)[-2000:]}")
                rc, out, err = _sh("docker", "image", "inspect", self.image,
                                   "--format", "{{.Id}}", timeout=60)
            if rc != 0 or not out.strip().startswith("sha256:"):
                raise RuntimeError(f"无法确定任务镜像：{(err or out)[-1000:]}")
            self.image_id = out.strip()
        rc, out, err = _sh("docker", "run", "-d", "--rm", self.image_id,
                           "sleep", "3600", timeout=180)
        cid = ""
        for line in out.split("\n"):
            line = line.strip()
            if len(line) >= 12 and all(c in "0123456789abcdef" for c in line):
                cid = line
        if rc != 0 or not cid:
            raise RuntimeError(f"起容器失败：{(err or out)[:200]}")
        self.container = cid
        self._install_certs()
        if not getattr(self, "FORBIDDEN", ()):
            self._build_forbidden()

    def _install_certs(self):
        """注入企业根证书 —— 与 PoolAgent 同一份，同一理由（§8.6）。"""
        if not os.path.exists(CERTS):
            return
        _sh("docker", "cp", CERTS, f"{self.container}:/tmp/v4v_corp.crt",
            timeout=60)
        self._exec(
            "cp /tmp/v4v_corp.crt /usr/local/share/ca-certificates/ "
            "2>/dev/null; update-ca-certificates 2>/dev/null; "
            "for f in $(find / -name cacert.pem -not -path '*/proc/*' "
            "2>/dev/null); do cat /tmp/v4v_corp.crt >> $f; done; "
            "printf '[global]\\ncert = /tmp/v4v_corp.crt\\n' > /etc/pip.conf; "
            "mkdir -p /etc/uv && printf 'native-tls = true\\n' "
            "> /etc/uv/uv.toml; true", timeout=180)

    def _build_forbidden(self):
        """判据面 = `tests/` 目录里的一切 + gold 解法。"""
        secrets = []
        for root, _dirs, files in os.walk(f"{self.dir}/tests"):
            for fn in files:
                try:
                    secrets.append(open(os.path.join(root, fn),
                                        errors="ignore").read())
                except Exception:
                    pass
        for fn in ("run-tests.sh", "solution.sh", "solution.yaml"):
            p = f"{self.dir}/{fn}"
            if os.path.exists(p):
                try:
                    secrets.append(open(p, errors="ignore").read())
                except Exception:
                    pass
        # 整文件太长，切成行级片段才挡得住"抄一段出来"的情况。
        frags = []
        for s in secrets:
            for line in s.split("\n"):
                line = line.strip()
                if len(line) >= 20:
                    frags.append(line)
        self.FORBIDDEN = oracle_surface(frags, self.public_surface(),
                                        min_len=20)

    def _state(self):
        rc, out, _ = _sh("docker", "exec", self.container, "bash", "-lc",
                         "ls -lAR /app 2>/dev/null | head -200; "
                         "echo ---; pwd", timeout=120)
        st = out.strip()
        if not st or "---" not in st:
            raise RuntimeError(
                f"状态指纹退化：{st[:120]!r} —— 容器多半没起来，"
                f"不能把错误串当成一个合法状态")
        return st

    def _exec(self, cmd, timeout=600):
        rc, out, err = _sh("docker", "exec", self.container, "bash", "-lc",
                           cmd, timeout=timeout)
        return rc, (out + ("\n" + err if err else ""))

    def _inspect(self, what=None):
        if what == "state":
            return {"fs": self._state()[:4000]}
        instr = ""
        p = f"{self.dir}/task.yaml"
        if os.path.exists(p):
            try:
                instr = open(p, errors="ignore").read()[:6000]
            except Exception:
                pass
        rc, tree = self._exec("ls -la /app 2>/dev/null; echo ---; "
                              "cat /etc/os-release 2>/dev/null | head -2")
        return {"task_id": self.task_id, "task_yaml": instr,
                "workdir_listing": tree[:4000], "image_id": self.image_id}

    def _run(self, payload):
        cmd = payload.get("cmd") if isinstance(payload, dict) else payload
        if not isinstance(cmd, str) or not cmd.strip():
            return {"error": "payload 需要 {'cmd': '<shell>'}"}
        for bad in BLOCKED:
            if bad in cmd:
                return {"error": f"拒绝：{bad} 属于判据面（TB 的 tests/ "
                                 f"就是评分标准本身），不在公开面内"}
        rc, out = self._exec(cmd)
        return {"exit_code": rc, "output": out[-20000:]}

    def _close(self):
        if self.container:
            _sh("docker", "rm", "-f", self.container, timeout=60)
            self.container = None
