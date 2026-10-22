"""LocalDockerEnvironment: BoxEnvironment with the transport swapped from the
remote command transport to local bash, running containers on the driver host's
docker daemon.

Every box interaction in BoxEnvironment funnels through five seams: `_run`
(bash on the box), `_stage_bytes_sync`/`_stage_dir_sync` (driver->box files),
`_pull_bytes_sync` (box->driver files), and the airgap/telemetry helpers. This
subclass reroutes those seams to the local host and keeps the entire container
lifecycle (build / run / inject / exec / probe / stop) byte-identical.

Concurrency: the inherited per-box asyncio lock stays the capacity governor:
callers pass pseudo-box names (local1..localN) and get exactly N concurrent
containers, one container per box.

Difference from the remote provider: no iptables airgap wall. ALLOWLIST tasks run
on a plain bridge network with full egress unless a subclass overrides the network
seams (the one-click suite's VGBEnvironment does: an internal network whose only
route out is the model proxy).

Closed-tree paths: adapters may emit remote-host paths under _BOX_CLOSED_PREFIX.
The driver-host mirror lives at $VERITAS_LOCAL_CLOSED (default
runtime/local_closed); inject paths are prefix-rewritten at construction.
"""
from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import uuid
from pathlib import Path

from box_provider import (
    AIRGAP_NET, ExecResult, BoxEnvironment, _DEFAULT_EXEC_TIMEOUT,
    _ERR_MARK, _EXEC_OUT_CAP, _OUT_MARK, _RC_MARK,
)

_BOX_CLOSED_PREFIX = "/root/box_closed"
_RUNTIME = Path(os.environ.get("LOOP_RUNTIME", str(Path(__file__).resolve().parents[1] / "runtime")))
_LOCAL_CLOSED = os.environ.get(
    "VERITAS_LOCAL_CLOSED", str(_RUNTIME / "local_closed"))
_LOCAL_STAGE = os.environ.get(
    "VERITAS_LOCAL_STAGE", str(_RUNTIME / "local_stage"))


class LocalDockerEnvironment(BoxEnvironment):
    """One docker container on the local daemon, same contract as the remote box."""

    def __init__(self, *args, **kwargs):
        # Default a pseudo-box ONLY for single-box callers: a non-empty `box` would
        # shadow box_map/boxes placement upstream and serialize the whole batch on
        # one per-box lock.
        if not kwargs.get("box_map") and not kwargs.get("boxes"):
            kwargs.setdefault("box", os.environ.get("BOX_NAME", "local1"))
        super().__init__(*args, **kwargs)
        self._inject_box_files = {
            (p.replace(_BOX_CLOSED_PREFIX, _LOCAL_CLOSED, 1)
             if p.startswith(_BOX_CLOSED_PREFIX) else p): c
            for p, c in self._inject_box_files.items()
        }
        # box paths (/root/harbor_stage/...) are not writable on the driver host:
        # relocate the per-session staging root under the local runtime.
        self._sess_root = _LOCAL_STAGE + self._sess_root

    @classmethod
    def preflight(cls) -> None:
        r = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise RuntimeError(f"local docker daemon unreachable: {r.stderr[-300:]}")

    # ---- transport seams -> local host ----------------------------------------------

    def _run(self, script: str, timeout: int = 60, name: str = "hb",
             stdin: str | None = None) -> str:
        try:
            r = subprocess.run(
                ["bash", "-c", script], capture_output=True, text=True,
                input=stdin,
                timeout=max(10, int(timeout)))
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(
                f"local transport {name} timed out after {timeout}s: "
                f"{(e.stdout or b'')[-300:]}") from e
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode != 0:
            raise RuntimeError(
                f"local transport {name} failed (rc={r.returncode}): {out[-800:]}")
        return out

    def _exec_sync(self, command, cwd, env, timeout_sec, user) -> ExecResult:
        """Keep local exec environment values out of shell and Docker argv."""
        user = self._resolve_user(user)
        merged = {**self._pass_env, **(self._merge_env(env) or {})}
        if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) for key in merged):
            raise ValueError("local exec environment names must be POSIX identifiers")
        # The host shell runs only this static Docker command. Environment values
        # go through stdin into a container subshell, never host argv or host env.
        # The outer container shell retains its PATH for output collection.
        exports = "\n".join(f"export {key}={shlex.quote(value)}" for key, value in merged.items())
        uflag = f"-u {shlex.quote(str(user))} " if user is not None else ""
        wflag = f"-w {shlex.quote(cwd)} " if cwd else ""
        tag = uuid.uuid4().hex[:8]
        o, e = f"/tmp/hb_{tag}.out", f"/tmp/hb_{tag}.err"
        c = shlex.quote(self._container)
        script = (
            f"(\n{exports}\nexec /bin/bash -c {shlex.quote(command)} </dev/null\n) > {o} 2> {e}\n"
            f"rc=$?\n"
            f"echo {_RC_MARK}$rc\n"
            f"echo {_OUT_MARK}$(head -c {_EXEC_OUT_CAP} {o} | base64 -w0)\n"
            f"echo {_ERR_MARK}$(head -c {_EXEC_OUT_CAP} {e} | base64 -w0)\n"
            f"rm -f {o} {e}"
        )
        text = self._run(
            f"docker exec -i {uflag}{wflag}{c} bash -s",
            timeout=int(timeout_sec or _DEFAULT_EXEC_TIMEOUT),
            name="hb-exec", stdin=script,
        )
        rc, out, err = self._parse_marks(text)
        if self._rt_on:
            self._rt["execs"] += 1
            if rc != 0:
                self._rt["exec_failures"] += 1
        return ExecResult(stdout=out, stderr=err, return_code=rc)

    def _stage_bytes_sync(self, data: bytes, remote_path: str) -> None:
        Path(remote_path).parent.mkdir(parents=True, exist_ok=True)
        Path(remote_path).write_bytes(data)

    def _stage_dir_sync(self, source_dir, remote_dir: str) -> None:
        shutil.copytree(str(source_dir), remote_dir, dirs_exist_ok=True)

    def _pull_bytes_sync(self, producer: str, box_file: str, timeout: int = 120) -> bytes:
        self._run(f"set -e\n{producer}", timeout=timeout, name="hb-pull")
        p = Path(box_file)
        if not p.is_file():
            raise FileNotFoundError(f"pull producer did not create {box_file}")
        data = p.read_bytes()
        p.unlink()
        return data

    # ---- network / telemetry --------------------------------------------------------

    def _net_flags(self) -> str:
        # ALLOWLIST -> plain bridge net (no wall, no pinned host IP: local DNS works).
        from harbor.models.task.config import NetworkMode
        mode = self._network_policy.network_mode
        if mode == NetworkMode.NO_NETWORK:
            return "--network none "
        if mode == NetworkMode.ALLOWLIST:
            return f"--network {AIRGAP_NET} "
        return ""

    def _ensure_airgap_sync(self) -> None:
        self._run(
            f"docker network inspect {AIRGAP_NET} >/dev/null 2>&1 || "
            f"docker network create {AIRGAP_NET}", name="hb-net")

    def _wall_counters(self) -> list:
        return []          # no iptables wall locally; per-trial deltas stay empty
