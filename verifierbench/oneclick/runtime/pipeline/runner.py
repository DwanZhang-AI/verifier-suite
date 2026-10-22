#!/usr/bin/env python3
"""可信 runner：在**隔离**环境里执行 verifier artifact，产出 `VerifierOutput`。

方案 §8.6.3 的 ABI 是固定的：

    entrypoint --task <task_spec.public.json>
               --candidate <candidate_view.json>
               --output <verifier_decision_payload.json>

    退出码 0 只表示产生了可解析 payload，**不等于 PASS**；
    最终判决来自 payload 的 verdict。
    非零退出、超时、越权、输出缺失或 schema 错误统一进 ERROR taxonomy。

## 隔离不是可选项

`AW-E2`：判据与被判方共享进程 —— 候选把 `TestTracker.success` 一改，
145/145 全部判过。`44_` 的结论是「判据是代码、或候选能写到判据的加载路径 →
3/3 全部失守」。**现在要执行的是模型生成的、我们没读过的代码**，
它同时是判据，且天然知道自己在被打分。共享进程等于把主表交给它写。

darwin 上用 `sandbox-exec`，实测能拒掉两件最要紧的事：

    网络       socket.create_connection → PermissionError
    越界写     写 /Users/... → PermissionError

再叠三层：

    setrlimit  CPU 秒 / 地址空间 / 文件大小 / 进程数
    环境变量   只留 PATH 与 locale —— 不给 API key、不给仓库路径
    工作目录   每次执行一个临时目录，跑完即删

`requires_network: true` 的 artifact 直接拒绝注册，不是「放行但记一笔」。

## crash ≠ FAIL

方案写得很死：「artifact 崩溃时 runner 生成 execution_status=error、
verdict=null 的 VerifierOutput；**不能把 crash 记为 FAIL**」。
这条与本轮反复踩的坑同源 —— 候选执行出错被当成「判据漏了」。
一个全崩的 artifact 若被记成全 FAIL，它会拿到「全拒基线」的分数，
看起来像个保守但可用的 verifier。实际上它什么都没做。
"""

# User-requested pause: repair code and inspect evidence without model reruns.
if __name__ == "__main__":
    import json as _pause_json
    from pathlib import Path as _PausePath
    _pause_root = _PausePath(globals().get("__file__", "/opt/vgb_run/vgb-certfix-20260919/__inline__.py")).resolve().parent
    _pause_file = _pause_root / "execution_policy.json"
    _pause_policy = _pause_json.loads(_pause_file.read_text()) if _pause_file.exists() else {}
    if not _pause_policy.get("rejudging_allowed", False) and (
            (_pause_root / "PAUSE_REPAIR_RUNS").exists()
            or _pause_policy.get("mode") == "repair_only"):
        raise SystemExit("PAUSED_BY_USER: repair only; generation, judging and route probes are disabled")

import concurrent.futures
import hashlib
import json
import os
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
# 整个基准目录对 artifact 不可读：答案键、候选池原文、审计中间产物都在里面
SECRET_ROOT = os.path.dirname(HERE)

# **SECRET_ROOT 挡不住上游数据。** profile 是 `allow file-read*` 再
# `deny SECRET_ROOT`，所以**只有基准目录被挡**，仓库/机器上其他地方全可读。
# 实撞发现两处泄漏：
#
#   Mac（§5.1–5.4 的判定环境）：`_v4v_sources/gorilla/.../possible_answer/*.json`
#       —— BFCL 的答案键。而 `tools` 与 `problem_statement` 是逐字的上游文本，
#       verifier 可以反查上游条目再直接读答案。
#   Linux 服务器（§5.6–5.7 的判定环境）：`/opt/vgb_src/aw_root/data/tasks/<id>/`（AppWorld
#       任务真值）、`/opt/vgb_src/tau2_data/tau2/domains/`（τ² 期望结果）。
#
# 这两处都在 SECRET_ROOT 之外。**判定执行的是模型生成的代码，而它同时是判据**
# —— 读权限就是全部泄漏，光挡写没有意义。
#
# 判定不需要上游源：能力层跑在沙箱外的 broker 里，verifier 只通过文件 RPC
# 请求执行。所以这些根整个 deny 掉，没有功能损失。
#
# `VGB_DENY_ROOTS` 可覆盖（冒号分隔）；默认覆盖当前两套部署的数据根。
def _find_upward(name, start, limit=4):
    """向上找目录，别硬拼相对层级。

    第一版写的是 `os.path.join(os.path.dirname(SECRET_ROOT), "_v4v_sources")`
    —— 少退了一层。`SECRET_ROOT` 的父目录是**仓库目录**（而且这个仓库目录名
    末尾带一个空格），而 `_v4v_sources` 是**仓库的兄弟目录**，在再上一层。
    """
    d = start
    for _ in range(limit):
        d = os.path.dirname(d)
        if not d or d == "/":
            break
        c = os.path.join(d, name)
        if os.path.isdir(c):
            return c
    return None


# **不存在的根不能静默丢掉。** 第一版写的是 `if p and os.path.exists(p)`，
# 于是路径算错时列表直接空掉、一行 deny 都不生成，而且**不报错不告警**——
# 落盘的 sandbox.sb 看起来一切正常。对抗测试实撞出来：`DENY_ROOTS == []`，
# 补丁在 Mac 上是彻底的 no-op，BFCL 答案键、AppWorld 732 个 ground_truth、
# 候选池原文全部可读。
#
# 这与 `enforced_limits()` 里那条教训同构（"跳过可以，但必须留在记录里"），
# 那个函数早就这么做了，DENY_ROOTS 没照做。现在补上：
#   * 显式配置（`VGB_DENY_ROOTS`）里的路径缺失 → **raise**，绝不放行
#   * 内置默认里缺失的 → 记进 `DENY_ROOTS_SKIPPED`，随每次 run 报出去
_explicit = os.environ.get("VGB_DENY_ROOTS")
if _explicit:
    DENY_ROOTS, DENY_ROOTS_SKIPPED = [], []
    for _p in _explicit.split(":"):
        if not _p:
            continue
        if not os.path.exists(_p):
            raise RuntimeError(
                f"VGB_DENY_ROOTS 里的 {_p!r} 不存在。显式配置写错等于静默取消隔离，"
                "不允许放行 —— 要么改对路径，要么从变量里去掉。")
        DENY_ROOTS.append(_p)
else:
    _defaults = ["/opt/vgb_src", _find_upward("_v4v_sources", SECRET_ROOT)]
    DENY_ROOTS = [p for p in _defaults if p and os.path.exists(p)]
    DENY_ROOTS_SKIPPED = [p for p in _defaults if not (p and os.path.exists(p))]

# 资源上限。宽到正常 verifier 用不完，紧到跑飞的进程拖不垮机器。
LIMITS = {"cpu_seconds": 30, "address_space_mb": 2048,
          "file_size_mb": 64, "processes": 64}
WALL_CLOCK = 60          # 墙钟超时；CPU 上限拦不住 sleep 与 IO 阻塞

# 读权限踩了两次才对。
#
# 第一版 `(allow file-read*)`：一个对抗 artifact 用它读到了
# `private/labels.jsonl` 全部 4472 行答案 —— 判 PASS 就是满分。
#
# 第二版改成 deny-by-default 再白名单放行系统路径：**python 起不来**，
# SIGABRT 且没有任何 stderr。逐条试出来，要放行到能启动就得放行 `/`，
# 那等于没限制。（沙箱把解释器自己也拦死了，这是 deny-default 的常见结局。）
#
# 第三版用 sandbox profile 的**后规则覆盖前规则**：先放行全部读，
# 再把整个基准目录 deny 掉，最后单独放回 bundle 与工作目录。
# 挡住的是这次真正要挡的东西 —— 答案键、候选池原文、审计中间产物。
PROFILE = """(version 1)
(deny default)
(allow process-exec process-fork)
(allow sysctl-read mach-lookup signal)
(allow file-read*)
(deny file-read* (subpath "{secret}"))
(allow file-read* (subpath "{bundle}") (subpath "{work}"))
(allow file-write* (subpath "{work}") (literal "/dev/null"))
"""


# RLIMIT_NPROC 不在名单里：macOS 上它算的是**该用户的全部进程**，不是本沙箱的。
# 设成 64 会让 fork 直接 BlockingIOError —— 连 artifact 都起不来。
# 挡 fork 炸弹改用「新会话 + 超时后按进程组整组 kill」。
_WANT = [("RLIMIT_CPU", "cpu_seconds", 1),
         ("RLIMIT_AS", "address_space_mb", 1 << 20),
         ("RLIMIT_FSIZE", "file_size_mb", 1 << 20)]


def enforced_limits():
    """哪些上限**真的生效了** —— 逐条试，不能一句 try/except 全吞。

    darwin 上 `RLIMIT_AS` 会抛 `ValueError: current limit exceeds maximum`，
    因为它根本没实现。如果这里静默跳过，我会以为内存有上限，其实没有；
    这与本轮所有踩过的坑同形 —— **失败伪装成成功**。
    所以：跳过可以，但必须留在记录里，跟着每一次 run 报出去。
    """
    ok, skipped = {}, {}
    for name, key, mul in _WANT:
        r = getattr(resource, name, None)
        if r is None:
            skipped[name] = "平台无此限制"
            continue
        try:
            soft, hard = resource.getrlimit(r)
            # **只动 soft，hard 原样留着** —— 把 hard 一起压下去就再也抬不回来，
            # 于是探测本身会给 runner 自己套上 30 秒 CPU 上限，长跑必死。
            # 第一版就是这么写的，症状是三条限制全报「未生效」。
            resource.setrlimit(r, (LIMITS[key] * mul, hard))
            resource.setrlimit(r, (soft, hard))
            ok[name] = LIMITS[key]
        except (ValueError, OSError) as e:
            skipped[name] = type(e).__name__
    return ok, skipped


_OK, _SKIPPED = enforced_limits()


def _limits():
    for name, key, mul in _WANT:
        if name in _OK:
            r = getattr(resource, name)
            _soft, hard = resource.getrlimit(r)
            resource.setrlimit(r, (LIMITS[key] * mul, hard))


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def validate_bundle(bundle):
    """注册前的静态检查（方案 §8.6.4 的前四步）。

    路径必须是 bundle 相对 POSIX path，禁止绝对路径、`..`、symlink。
    这不是形式主义 —— 一个 `"path": "../../data/candidates.jsonl"`
    就能让 artifact 把答案键读进自己的 bundle。
    """
    mf = os.path.join(bundle, "manifest.json")
    if not os.path.exists(mf):
        return None, "manifest.json 缺失"
    m = json.load(open(mf))
    for k in ("schema_version", "artifact_api_version", "verifier_form",
              "entrypoint", "files"):
        if k not in m:
            return None, f"manifest 缺字段 {k}"
    if m.get("requires_network"):
        return None, "requires_network=true —— 拒绝注册"
    if m["entrypoint"].get("protocol") != "vgb-json-file-v1":
        return None, "entrypoint.protocol 不是 vgb-json-file-v1"
    for f in m["files"]:
        p = f["path"]
        if os.path.isabs(p) or ".." in p.split("/"):
            return None, f"非法路径 {p}"
        full = os.path.join(bundle, p)
        if os.path.islink(full):
            return None, f"symlink {p}"
        if not os.path.exists(full):
            return None, f"声明的文件不存在 {p}"
        if f.get("sha256") and f["sha256"] != sha256_file(full):
            return None, f"哈希不符 {p}"
    return m, None


def sandbox_argv(inner, work, bundle, cap_dir=None):
    """把要执行的命令包进本平台的沙箱。**两条实现必须等价，不是各写各的。**

    darwin 走 `sandbox-exec` + `.sb` profile（原实现，一字未改）。
    linux 走 `bwrap`，逐条对应 profile 里的每一行：

        (deny default)                      --unshare-net（无网）+ 只读根
        (allow file-read*)                  --ro-bind / /
        (deny file-read* SECRET_ROOT)       --tmpfs SECRET_ROOT（盖成空目录）
        (allow file-read* bundle)           --ro-bind bundle bundle（盖回来）
        (allow file-write* work)            --bind work work（唯一可写处）
        (allow file-write* /dev/null)       --dev /dev
        cap_dir 读写                        --bind cap cap

    **顺序有意义**：`--tmpfs SECRET_ROOT` 必须排在 `--ro-bind / /` 之后、
    bundle/work 的重新绑定之前 —— bundle 就在 SECRET_ROOT 里面，
    先盖 tmpfs 再绑回来，才复现 profile 的"先 deny 再 allow"。

    ## 与 darwin 的两处**不等价**，都记在这里而不是藏着

    1 `--unshare-pid --proc /proc`：darwin 的 profile 不隔离进程视图。
      加它是为了让超时收割可靠（namespace init 一死全组死），**更严格**。
      代价是 artifact 看到的 /proc 与 Mac 上不同 —— 如果某个 verifier 靠
      读 /proc 判断环境，两侧行为会不一样。等价性探针里有一条专门测它。
    2 `--dev /dev` 给的是一小组设备（null/zero/random/urandom/tty），
      darwin 只放行了 `/dev/null` 一个 literal。**更宽**。

    这两条都由 `sandbox_equiv_probe.py` 对着 darwin 实撞，不靠推理。
    """
    work_r, bundle_r = os.path.realpath(work), os.path.realpath(bundle)
    secret_r = os.path.realpath(SECRET_ROOT)
    cap_r = os.path.realpath(cap_dir) if cap_dir else None

    if sys.platform == "darwin":
        prof = f"{work}/sandbox.sb"
        profile = PROFILE.format(work=work_r, bundle=bundle_r, secret=secret_r)
        for d in DENY_ROOTS:
            # **deny 根不能是 bundle/work 的祖先。** sandbox-exec 是后规则覆盖
            # 前规则，而这些 deny 追加在 bundle/work 的 allow 之后 —— 实撞过：
            # 把上一层整个目录设成 deny 根，artifact 连自己都读不出来
            # （rc=2，"can't open file .../bundle/probe.py: Operation not permitted"）。
            # 第一版这里写着"bundle/work 不在这些根里面"，是个没校验的假设。
            dr = os.path.realpath(d)
            for name, tgt in (("bundle", bundle_r), ("work", work_r)):
                if tgt == dr or tgt.startswith(dr + os.sep):
                    raise RuntimeError(
                        f"deny 根 {dr!r} 是 {name} 目录 {tgt!r} 的祖先 —— "
                        "它会把 bundle/work 的 allow 盖掉，artifact 读不到自己。")
            profile += f'(deny file-read* (subpath "{dr}"))\n'
        if cap_r:
            # **沙箱只放行 work 与 bundle。** cap 目录是独立临时目录，
            # 不额外放行的话 verifier 写 req.json 会 PermissionError ——
            # 而 `vgb_env.available()` 仍返回 True（目录存在、可读），
            # 于是"能力层可用"与"能力层写不进去"分不开：
            # 表现成模型没用能力层，实际是沙箱把它挡了。
            profile += (f'(allow file-write* (subpath "{cap_r}"))\n'
                        f'(allow file-read* (subpath "{cap_r}"))\n')
        open(prof, "w").write(profile)
        return ["/usr/bin/sandbox-exec", "-f", prof] + inner

    if not sys.platform.startswith("linux"):
        raise RuntimeError(f"没有 {sys.platform} 的沙箱实现 —— "
                           "隔离不是可选项，不许无沙箱兜底执行")

    bwrap = shutil.which("bwrap")
    if not bwrap:
        # **不允许退回"没有沙箱也跑"。** 判定执行的是模型生成的、
        # 我们没读过的代码，它同时是判据。没有隔离就该停，
        # 而不是产出一批看起来正常、实际不可信的判定。
        raise RuntimeError("linux 上找不到 bwrap（apt install bubblewrap）")

    # A recursive bind of / includes Docker's transient netns and containerd
    # mounts. They can disappear during remount, before the verifier starts.
    # Build a private root from stable OS/interpreter paths instead; host /tmp,
    # /run, Docker sockets, and benchmark data are never imported into it.
    argv = [bwrap, "--tmpfs", "/"]
    for path in ("/usr", "/bin", "/sbin", "/lib", "/lib64", "/etc"):
        if os.path.islink(path):
            argv += ["--symlink", os.readlink(path), path]
        elif os.path.isdir(path):
            argv += ["--ro-bind", path, path]
    for prefix in dict.fromkeys((os.path.realpath(sys.base_prefix), os.path.realpath(sys.prefix))):
        if prefix not in ("/", "/usr") and not prefix.startswith("/usr/"):
            argv += ["--ro-bind", prefix, prefix]
    argv += ["--tmpfs", "/tmp", "--dir", "/run",
            "--dev", "/dev",
            "--unshare-pid", "--proc", "/proc",
            "--unshare-net",
            "--die-with-parent",
            "--tmpfs", secret_r,
            "--ro-bind", bundle_r, bundle_r,
            "--bind", work_r, work_r]
    if cap_r:
        argv += ["--bind", cap_r, cap_r]
    # 解释器若落在 SECRET_ROOT 里（venv 装在仓库内），tmpfs 会把它一起盖掉，
    # 表现成 "No such file or directory" 而不是"沙箱挡了" —— 显式绑回来。
    # 上游数据根同样盖成 tmpfs。**必须排在 bundle/work 重绑之后**（与
    # SECRET_ROOT 同理），否则嵌套挂载点建不出来。
    extra = [os.path.realpath(d) for d in DENY_ROOTS]
    extra = [d for d in extra
             if not (d == secret_r or d.startswith(secret_r + os.sep))]
    for d in extra:
        argv += ["--tmpfs", d]
    exe_prefix = os.path.realpath(sys.prefix)
    # 解释器若落在任何一个被盖掉的根里（venv 装在仓库或 /opt/vgb_src 内），
    # tmpfs 会把它一起盖掉，表现成 "No such file or directory" 而不是
    # "沙箱挡了" —— 显式绑回来。
    for root in [secret_r] + extra:
        if exe_prefix == root or exe_prefix.startswith(root + os.sep):
            argv += ["--ro-bind", exe_prefix, exe_prefix]
            break
    # **tmpfs 默认可写** —— 实撞发现 verifier 能在 SECRET_ROOT 的覆盖层里
    # 建文件（darwin 那边是 deny）。虽然这层是每次执行独立、退出即毁、
    # 外面看不见，仍然要按等价性补齐：不等价的地方越少，"两套沙箱可比"
    # 这句话才站得住。
    #
    # `--remount-ro` 必须排在**所有嵌套绑定之后**：先 remount 会让 tmpfs
    # 变只读，后面 bundle/work 的挂载点就建不出来了。反过来，
    # 嵌套挂载是独立的 mount，父层 remount 不会把它们也变只读 ——
    # 这一点由探针里的 write_work / write_cap 两条正控兜底验证。
    argv += ["--remount-ro", secret_r]
    for d in extra:
        argv += ["--remount-ro", d]
    for d in ("/tmp", "/"):
        argv += ["--remount-ro", d]
    argv += ["--chdir", bundle_r, "--"]
    return argv + inner


def run_one(bundle, manifest, task_file, cand_file, work, cap_dir=None):
    """跑一条候选。返回 (payload | None, execution_status, error, ms)。

    `cap_dir` 非空时给 artifact 注入 `vgb_env`（规格 §8.6 的
    `interactive_resettable`）。走**文件 RPC**：sandbox 里无网络、
    只有 work 目录可写，而五个 backend 分属四个 venv、两个还要 docker ——
    沙箱里既连不上也 import 不了。
    """
    inp, outp = f"{work}/input", f"{work}/output"
    os.makedirs(inp, exist_ok=True)
    os.makedirs(outp, exist_ok=True)
    shutil.copy(task_file, f"{inp}/task_spec.public.json")
    shutil.copy(cand_file, f"{inp}/candidate_view.json")
    out_json = f"{outp}/verifier_decision_payload.json"

    inner = (manifest["entrypoint"]["argv"]
             + ["--task", f"{inp}/task_spec.public.json",
                "--candidate", f"{inp}/candidate_view.json",
                "--output", out_json])
    argv = sandbox_argv(inner, work, bundle, cap_dir)
    env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C.UTF-8",
           "PYTHONDONTWRITEBYTECODE": "1", "HOME": work}
    if cap_dir:
        # shim 落在 bundle 根，`import vgb_env` 直接可用（cwd=bundle）。
        # **每次运行都重拷** —— artifact 可能覆盖过它，而一个被改写的
        # vgb_env 会让"用了能力层"变成"用了自己伪造的能力层"。
        shutil.copy(f"{os.path.dirname(os.path.abspath(__file__))}"
                    f"/capabilities/vgb_env_client.py",
                    f"{bundle}/vgb_env.py")
        os.makedirs(cap_dir, exist_ok=True)
        env["VGB_CAP_DIR"] = cap_dir
        env["VGB_CAP_TIMEOUT"] = str(int(WALL_CLOCK * 0.8))

    t0 = time.time()
    # start_new_session：artifact 及其所有子进程独立成组，超时能整组收掉。
    # 只 kill 父进程会留下后台子进程，它们仍在跑、仍能写盘。
    proc = subprocess.Popen(argv, cwd=bundle, env=env, start_new_session=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            preexec_fn=_limits)
    try:
        out, errb = proc.communicate(timeout=WALL_CLOCK)
    except subprocess.TimeoutExpired:
        _kill_group(proc)
        proc.communicate()
        return None, "error", "TIMEOUT", int((time.time() - t0) * 1000)
    _kill_group(proc)          # 正常退出后也收一次 —— 清掉 artifact 留下的孤儿
    ms = int((time.time() - t0) * 1000)
    p = subprocess.CompletedProcess(argv, proc.returncode, out, errb)

    if p.returncode != 0:
        tail = (p.stderr or b"")[-200:].decode(errors="replace").strip()
        if (p.stderr or b"").lstrip().startswith(b"bwrap:"):
            return None, "error", f"SANDBOX_STARTUP: {tail}", ms
        return None, "error", f"NONZERO_EXIT({p.returncode}): {tail}", ms
    if not os.path.exists(out_json):
        # **stderr 必须带上。** 原来这里只返回 `MISSING_OUTPUT` 四个字，
        # 于是"退出码 0 但没写文件"变成不可诊断 —— 与缺陷 #17
        # （broker 用 `stderr=DEVNULL` 起子进程）同一族：
        # **把可诊断的故障变成不可诊断的。**
        #
        # 这一类 artifact 的典型写法是把输出写包在
        # `try: ... except Exception: pass` 里再 `sys.exit(0)`，
        # 于是它自己也把真因吞了 —— 两层吞噬叠加，
        # 剩下的信息量恰好为零。至少要保住我们这一层。
        tail = (p.stderr or b"")[-200:].decode(errors="replace").strip()
        return None, "error", f"MISSING_OUTPUT: {tail}" if tail \
            else "MISSING_OUTPUT: (stderr 为空 —— artifact 很可能自己吞了异常)", ms
    try:
        pl = json.load(open(out_json))
    except Exception as e:
        return None, "error", f"MALFORMED_OUTPUT: {type(e).__name__}", ms
    err = check_payload(pl)
    if err:
        return None, "error", f"MALFORMED_OUTPUT: {err}", ms
    return pl, "completed", None, ms


def _kill_group(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def check_payload(pl):
    """decision payload schema（方案 §3.3）。`additionalProperties=false` ——
    artifact 想在 payload 里自己写 candidate_id 之类的可信字段，直接判 MALFORMED。"""
    if not isinstance(pl, dict):
        return "不是 object"
    allowed = {"schema_version", "verdict", "score", "confidence", "checks"}
    extra = set(pl) - allowed
    if extra:
        return f"多余字段 {sorted(extra)}（可信字段只能由 runner 写）"
    for k in ("schema_version", "verdict", "score", "confidence", "checks"):
        if k not in pl:
            return f"缺字段 {k}"
    # `ABSTAIN` = 判据自己声明判不了。**加它是为了可测，不是为了给出路。**
    # 原来只有 PASS/FAIL，"判不了"只能伪装成判决，而在没验证成功的代码上
    # 输出 PASS 更糟，于是全部折进 FAIL —— A+ 的功能门崩塌因此混着
    # 一部分"没处放弃权"（§10.5.8）。`score.py` 把 ABSTAIN 与执行失败同档
    # 计入 WAR，**计分上没有任何便宜可占**。
    if pl["verdict"] not in ("PASS", "FAIL", "ABSTAIN"):
        return f"verdict={pl['verdict']!r}"
    for k in ("score", "confidence"):
        v = pl[k]
        if v is not None and not (isinstance(v, (int, float))
                                  and not isinstance(v, bool) and 0 <= v <= 1):
            return f"{k}={v!r} 越界"
    if not isinstance(pl["checks"], list):
        return "checks 不是 array"
    return None


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle")
    ap.add_argument("--views", default=f"{HERE}/views")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--form", default="")
    ap.add_argument("--workers", type=int, default=6)
    # 逐题 artifact：一个 bundle 只对它自己那道题的候选负责（§8.6.4
    # 把 artifact 绑定到 task_id）。不加这个限制会拿 A 题的 verifier 去判 B 题。
    ap.add_argument("--task", default="")
    a = ap.parse_args()
    from decision_audit import persist as persist_decision
    audit_root = a.out + '.decisions'
    # A fresh replay owns a fresh audit directory. Do not reuse partial output.
    os.mkdir(audit_root, mode=0o700)
    DENY_ROOTS.append(os.path.realpath(audit_root))

    print(f"资源上限生效：{_OK}" + (f"  未生效：{_SKIPPED}" if _SKIPPED else ""))
    manifest, err = validate_bundle(a.bundle)
    if err:
        print(f"artifact 注册失败：{err}")
        return 2
    artifact_id = "vgb-v-" + hashlib.sha256(
        open(f"{a.bundle}/manifest.json", "rb").read()
        + b"".join(sha256_file(f"{a.bundle}/{f['path']}").encode()
                   for f in manifest["files"])).hexdigest()[:16]

    idmap = json.load(open(f"{a.views}/private/id_map.json"))
    from pool_policy import exclusions
    upstream_drop = exclusions()

    # AppWorld 的题面**判定时也要回填**。
    #
    # `task_specs.py` 的 `RUNTIME_ONLY = {"AppWorld"}` 是合规设计：AppWorld 带
    # 再分发限制，原始题面不落本仓库，所以 `views/public/*/task_spec.public.json`
    # 里存的是占位符，真内容在运行时从 `APPWORLD_ROOT` 重建。
    #
    # 生成侧一直有这一步（`runner_spec.render` → `appworld_backfill`），
    # **判定侧原本没有** —— 直接把占位符 copy 给 verifier。后果实测过：28 道
    # AppWorld 的 verifier 在生成和判定两端都看不到题，22 模型均值 BA 53.6
    # （≈随机），其中 8 个模型 PASS=0（全判 FAIL，退化 verifier 的签名）。
    #
    # 回填结果只写进进程级临时目录，不碰仓库，合规边界不变。
    # **拿不到就报错停下，不退回占位符** —— 静默判一个空壳会产出看起来
    # 正常的假数字，比判定失败危险得多。
    aw_specs = {}
    aw_tmp = None
    aw_handles = [th for th in os.listdir(f"{a.views}/public")
                  if idmap.get(th, {}).get("benchmark") == "AppWorld"
                  and th not in upstream_drop
                  and (not a.task or th == a.task)]
    if aw_handles:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from spike_bundle.runner_spec import appworld_backfill
        aw_tmp = tempfile.mkdtemp(prefix="vgb-aw-spec-")
        for th in aw_handles:
            base = json.load(open(f"{a.views}/public/{th}/task_spec.public.json"))
            tid = idmap[th].get("task_id")
            filled = appworld_backfill(base, tid)
            if filled is None or not (filled.get("problem_statement") or "").strip():
                raise RuntimeError(
                    f"AppWorld 题面回填失败：{th} (task_id={tid})。"
                    " 检查 APPWORLD_ROOT 是否指向含 data/tasks 的目录。"
                    " 拒绝用占位符判定。")
            p = f"{aw_tmp}/{th}.json"
            with open(p, "w") as f:
                json.dump(filled, f, ensure_ascii=False)
            aw_specs[th] = p
        print(f"AppWorld 题面已回填 {len(aw_specs)} 道（判定用，临时目录）")

    jobs = []
    for th in sorted(os.listdir(f"{a.views}/public")):
        if th in upstream_drop:
            continue
        d = f"{a.views}/public/{th}"
        if a.task and th != a.task:
            continue
        if a.form and idmap.get(th, {}).get("form") != a.form:
            continue
        tf = aw_specs.get(th) or f"{d}/task_spec.public.json"
        for cf in sorted(os.listdir(f"{d}/candidates")):
            jobs.append((th, cf[:-5], tf, f"{d}/candidates/{cf}"))
    if a.limit:
        jobs = jobs[:a.limit]

    # One worker per task; serial candidates reset the same backend and share
    # the original task-total budget. No two candidates mutate one world together.
    cap_mode = (manifest.get("environment_capabilities") or {}).get("mode")
    cap_fail = {}
    lab_bm = {}
    sys.path.insert(0, f"{HERE}/capabilities")
    import registry as REG
    if cap_mode == "interactive_resettable":
        import broker as BRK
        import budgets as BG
        for line in open(f"{a.views}/private/labels.jsonl"):
            r = json.loads(line)
            lab_bm[r["task_handle"]] = r["benchmark"]

    def one(job, backend=None, cd=None, startup_error=None, budget=None):
        th, ch, tf, cf = job
        work = tempfile.mkdtemp(prefix="vgb-run-")
        cap_error = startup_error
        cap_required = cap_mode == "interactive_resettable" and lab_bm.get(th) not in REG.NOT_APPLICABLE
        started = time.monotonic()
        from generation_provenance import stale_reason
        generated_spec = (manifest.get("generation_inputs") or {}).get("task_spec_sha256")
        generation_error = stale_reason(th, manifest)
        if th in aw_specs:
            effective = json.dumps(json.load(open(tf)), ensure_ascii=False,
                                   separators=(",", ":"), sort_keys=True)
            expected_effective = hashlib.sha256(effective.encode()).hexdigest()
            if manifest.get("generation_inputs", {}).get("effective_spec_sha256") != expected_effective:
                generation_error = "AppWorld generation input is not bound to the current complete public task"
        stale_generation = generation_error is not None
        pl, status, error, ms = None, "error", None, 0
        try:
            if stale_generation:
                cap_error = generation_error
                cap_fail[th] = cap_error
            if not stale_generation and cap_required and not cap_error:
                try:
                    backend.reset_env()
                except Exception as exc:
                    cap_error = "reset: " + type(exc).__name__ + ": " + str(exc)[:500]
                    cap_fail[th] = cap_error
            if cap_error:
                pl, status, error = None, "error", "capability_startup: " + cap_error
                ms = int((time.monotonic() - started) * 1000)
            else:
                pl, status, error, ms = run_one(
                    a.bundle, manifest, tf, cf, work, cap_dir=cd)
                if error and error.startswith("SANDBOX_STARTUP:"):
                    cap_error = error
                if backend is not None and backend.stats.get("transport_errors", 0):
                    cap_error = "Capability RPC transport failed"
                    cap_fail[th] = cap_error
                    pl, status, error = None, "error", cap_error
        finally:
            shutil.rmtree(work, ignore_errors=True)
        audit = persist_decision(audit_root, th, ch, pl, status, error)
        rec = {"schema_version": "1.0",
                   "artifact_id": artifact_id, "task_handle": th,
                   "candidate_handle": ch,
                   "verifier_form": manifest["verifier_form"],
                   "execution_status": status,
                   # crash 不是 FAIL —— 崩掉的 artifact 不该拿到全拒基线的分
                   "verdict": pl["verdict"] if pl else None,
                   "score": pl.get("score") if pl else None,
                   "confidence": pl.get("confidence") if pl else None,
                   "error": error,
                   "decision_payload_hash": (
                       "sha256:" + hashlib.sha256(json.dumps(
                           pl, sort_keys=True).encode()).hexdigest()
                       if pl else None),
                   "wall_clock_ms": ms,
                   "decision_audit": audit,
                   "enforced_limits": _OK, "unenforced_limits": _SKIPPED}
        rec["runtime_contract"] = REG.RUNTIME_CONTRACT
        rec["task_spec_sha256"] = sha256_file(tf)
        rec["generation_spec_sha256"] = generated_spec
        from repair_profile import reuse_binding
        rec["generation_reuse_binding"] = reuse_binding(th, manifest)
        rec["spec_renderer_version"] = (manifest.get("generation_inputs") or {}).get("spec_renderer_version")
        rec["generation_used_capability"] = bool(manifest.get("environment_capabilities"))
        rec["generation_environment_contract"] = (manifest.get("generation_inputs") or {}).get("generation_environment_contract")
        if stale_generation:
            rec["error_type"] = "stale_generation"
        elif error and error.startswith("SANDBOX_STARTUP:"):
            rec["error_type"] = "infrastructure"
        rec["candidate_view_sha256"] = sha256_file(cf)
        if cap_mode == "interactive_resettable":
            rec["cap_required"] = cap_required
            rec["cap_ready"] = backend is not None
            rec["cap_budget"] = budget
            rec["cap_stats"] = dict(backend.stats) if backend is not None else None
            if cap_error:
                rec["cap_error"] = cap_error
                rec["error_type"] = "stale_generation" if stale_generation else "infrastructure"
        return rec

    grouped = {}
    for job in jobs:grouped.setdefault(job[0], []).append(job)

    def task_worker(task_jobs):
        th = task_jobs[0][0]
        backend = cd = None
        error = budget = None
        from generation_provenance import stale_reason
        stale = stale_reason(th, manifest) is not None
        try:
            if cap_mode == "interactive_resettable" and not stale:
                bm = lab_bm.get(th)
                if bm not in REG.NOT_APPLICABLE:
                    try:
                        tid = idmap.get(th, {}).get("task_id")
                        if not bm or not REG.has_capability(bm) or not tid:
                            raise RuntimeError("Missing capability registration or task ID")
                        cd = tempfile.mkdtemp(prefix="vgb-cap-task-")
                        budget = BG.run_public_budget(bm, len(task_jobs))
                        backend = BRK.Broker(bm, tid, cd, budget=budget)
                    except Exception as exc:
                        error = type(exc).__name__ + ": " + str(exc)[:500]
                        cap_fail[th] = error
            return [one(job, backend, cd, error, budget) for job in task_jobs]
        finally:
            if backend is not None:backend.close()
            if cd is not None:shutil.rmtree(cd, ignore_errors=True)

    n_err = 0
    with open(a.out, "w") as fh, concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
        for records in ex.map(task_worker, grouped.values()):
            for rec in records:
                n_err += rec["execution_status"] == "error"
                fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"{artifact_id}  {len(jobs)} 条  错误 {n_err}  → {a.out}")
    if cap_mode == "interactive_resettable" and cap_fail:
        # Startup failures have no verifier verdict and require an infrastructure rerun.
        print(f"   ★ 能力层未就绪的题 {len(cap_fail)} 道：")
        for th, why in list(cap_fail.items())[:10]:
            print(f"      {th}  {why}")
    return 2 if cap_fail else 0


if __name__ == "__main__":
    sys.exit(main())
