"""Remote-host container provider for Harbor (base class of LocalDockerEnvironment).

Harbor `BaseEnvironment` implementation in which one provider instance is one docker
container on one named host ("box"); every lifecycle operation is a `docker ...`
command run on that host through the `_run` transport seam. The default seam is a
remote command transport (`box_transport.box_run`). The one-click suite never uses
it: it runs LocalDockerEnvironment, which replaces every transport seam with local
bash and keeps the container lifecycle defined here.

Plug in via import_path:

    environment:
      import_path: "box_provider:BoxEnvironment"
      kwargs: {box: "<host name>"}

Network policy mapping (static, no dynamic phase switching, so tasks must put their
policy on the [environment] baseline):
  no-network -> docker run --network none
  allowlist  -> docker run on a dedicated network with one pinned endpoint host,
                behind an iptables wall (default DROP + the pinned host on 443 +
                DNS) installed idempotently and verified fail-closed before the
                container starts. Only that exact host allowlist is enforceable;
                anything else is rejected.
  public     -> default bridge (NAT egress)

Transport constraints designed around:
  - remote command size cap   -> uploads are gzip+base64 chunk-appended (16KB),
    with a content-addressed host cache (/root/harbor_stage/cache/<sha256>) so large
    task materials staged once never re-upload.
  - remote output cap         -> downloads split the payload on the host and cat
    16KB chunks; exec stdout/stderr are head-capped at 12KB each (bulk data must go
    through download_*, matching how Harbor itself uses exec).
  - the transport is blocking -> every transport call runs in a worker thread
    (asyncio.to_thread) so Harbor's wall-clock timeouts can actually fire.
"""

from __future__ import annotations

import asyncio
import base64
import gzip
import hashlib
import io
import json
import os
import shlex
import sys
import tarfile
import threading
import uuid
from pathlib import Path

# --- transport import: box_transport (same dir) owns box_run ---------------------------
_HERE_DIR = os.path.dirname(os.path.abspath(__file__))
if _HERE_DIR not in sys.path:
    sys.path.insert(0, _HERE_DIR)

from box_transport import box_run  # noqa: E402  (signature: box_run(box, script,
#                                                 timeout=60, name="sw", state_file=None)
#                                                 -> merged stdout+stderr str, status
#                                                 lines filtered)

from harbor.environments.base import (  # noqa: E402
    BaseEnvironment,
    ExecResult,
)
from harbor.environments.capabilities import EnvironmentCapabilities  # noqa: E402
from harbor.models.task.config import NetworkMode, NetworkPolicy  # noqa: E402


async def _drain_owned_task(task):
    """Cancellation cannot stop an already-dispatched blocking transport worker.

    Keep its box lease until it finishes. Repeated caller cancellation must not
    cancel the underlying worker or let another trial enter the same box.
    """
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            continue
    return task.result()

# Allowlist network constants of the remote transport (unused by LocalDockerEnvironment
# except AIRGAP_NET, see local_docker_provider._net_flags).
ALLOW_HOST = "model-endpoint.example"
PIN_IP = os.environ.get("BOX_PIN_IP", "192.0.2.1")
AIRGAP_NET = "box-airgap"
AIRGAP_SUBNET = "172.31.44.0/24"
AIRGAP_GW = "172.31.44.1"

STAGE_ROOT = "/root/harbor_stage"          # box-side staging area (cache + sessions)
_CHUNK = 16000                              # b64 bytes per remote command (cap-safe)
_EXEC_OUT_CAP = 12000                       # bytes of stdout/stderr echoed per exec
_MAX_PULL_CHUNKS = 400                      # ~6.4MB b64 ≈ 4.8MB payload patience bound
_DEFAULT_EXEC_TIMEOUT = int(os.environ.get("VERITAS_EXEC_TIMEOUT", "3900"))
#                                             transport cap when Harbor passes None;
#                                             must exceed the agent session budget so
#                                             Harbor's own wall clock cuts first.
#                                             agents with a longer budget need
#                                             VERITAS_EXEC_TIMEOUT set above it.

# Sentinels that carry rc/stdout/stderr through the merged transport output.
_RC_MARK = "HARBOR_RC="
_OUT_MARK = "HARBOR_OUT_B64="
_ERR_MARK = "HARBOR_ERR_B64="


class BoxEnvironment(BaseEnvironment):
    """One docker container on one named host, driven through the `_run` seam."""

    # ---- construction ----------------------------------------------------------------

    def __init__(
        self,
        *args,
        box: str | None = None,
        boxes: list[str] | None = None,
        box_map: dict[str, str] | None = None,
        inject_map: dict[str, dict[str, str]] | None = None,
        state_file: str | None = None,
        image_prefix: str = "harborbox",
        inject_box_files: dict[str, str] | None = None,
        pass_env: list[str] | None = None,
        **kwargs,
    ):
        """`box`/`state_file`/`inject_box_files` arrive via the job config's
        environment.kwargs (Harbor merges config.kwargs into constructor kwargs); an
        environment-variable fallback keeps plain-flag CLI runs working.

        inject_box_files: {box_path: container_path}: host-local closed-book staging.
        Task inputs that already live on the host are docker-cp'd into the container
        right after start, with no bytes over the transport. Each injection is
        non-empty-verified, fail-loud. These bytes are outside Harbor's task
        checksum; the host path is their provenance."""
        super().__init__(*args, **kwargs)
        self._inject_box_files = dict(inject_box_files or {})
        # One job per batch: a static per-task injection map keyed by task/environment
        # name; each trial instance selects its own entry (exact, then substring match
        # on environment_name).
        if inject_map and not self._inject_box_files:
            m = inject_map.get(self.environment_name)
            if m is None:
                for k, v in inject_map.items():
                    if k in self.environment_name or self.environment_name in k:
                        m = v
                        break
            if m:
                self._inject_box_files = dict(m)
        # pass_env: NAMES of driver-env vars injected into every container exec
        # (lowest precedence). This is how secrets reach the session without ever
        # touching a config file: the config names the variable, the operator's shell
        # holds the value.
        self._pass_env = {
            name: os.environ[name] for name in (pass_env or []) if name in os.environ
        }
        # Explicit placement: the batch driver passes box_map {environment_name: box},
        # balanced (queue depth <= ceil(n/boxes)) and cache-affine (crc32-seeded, only
        # overflow moves). Raw crc32 alone skews on large batches, and waiters can burn
        # their whole env-start budget behind the per-box mutex.
        if box_map and not box:
            box = box_map.get(self.environment_name)
            if box is None:                      # underscore/dash normalization drift
                for k in (self.environment_name.replace("_", "-"),
                          self.environment_name.replace("-", "_")):
                    if k in box_map:
                        box = box_map[k]
                        break
        # Box-pool fallback for callers without a box_map: hash the task
        # (environment_name), not the session, so the same task lands on the same box
        # every batch and its docker image stays warm.
        if boxes and not box:
            import zlib
            box = boxes[zlib.crc32(self.environment_name.encode()) % len(boxes)]
        self._box = box or os.environ.get("BOX_NAME") or ""
        self._state_file = state_file  # None -> the transport's default state file
        safe = "".join(c if c.isalnum() or c == "-" else "-" for c in self.session_id)
        self._image = f"{image_prefix}-{self.environment_name}".lower()
        self._container = f"{self._image}-{safe}".lower()
        self._sess_root = f"{STAGE_ROOT}/sess/{safe.lower()}"
        # Sandbox-runtime collection (VERITAS_RUNTIME=1): container info rides
        # /logs/artifacts at start; final state and exec counters spool host-side at
        # stop. Must never affect the trial.
        self._rt_on = os.environ.get("VERITAS_RUNTIME") == "1"
        self._rt = {"execs": 0, "exec_failures": 0}
        if not self._box:
            raise ValueError(
                "BoxEnvironment needs a box name: environment.kwargs.box "
                "in the job config, or $BOX_NAME."
            )

    # ---- identity / capabilities -----------------------------------------------------

    @staticmethod
    def type() -> str:
        # Arbitrary strings are allowed for third-party providers.
        return "box-docker"

    @property
    def capabilities(self) -> EnvironmentCapabilities:
        return EnvironmentCapabilities(
            # /logs dirs live inside the container; Harbor downloads them
            # (mounted=False path), which our download_* serve.
            mounted=False,
            disable_internet=True,               # docker run --network none
            network_allowlist=True,              # the one pinned host, and only that
            network_allowlist_hostnames=True,
            dynamic_network_policy=False,        # posture fixed at container start
            gpus=False,
        )

    def validate_network_policy_support(
        self, network_policy: NetworkPolicy | None = None
    ) -> None:
        """Generic capability check, then the honest one: the only allowlist this
        provider can enforce is its one pinned host. Reject anything else rather
        than pretend (Harbor contract: enforce exactly or reject before start)."""
        super().validate_network_policy_support(network_policy)
        policy = network_policy or self._network_policy
        if policy.network_mode == NetworkMode.ALLOWLIST:
            extra = set(policy.allowed_hosts) - {ALLOW_HOST}
            if extra:
                raise ValueError(
                    f"box-docker can only enforce allowlist={{{ALLOW_HOST}}} (the "
                    f"box-airgap pin); cannot enforce: {sorted(extra)}"
                )

    def _validate_definition(self):
        # Single-container Dockerfile tasks only (no compose): sidecars would need
        # per-service docker orchestration on the host.
        dockerfile = Path(self.environment_dir) / "Dockerfile"
        if not dockerfile.exists():
            raise ValueError(
                f"box-docker requires environment/Dockerfile (no compose): "
                f"{self.environment_dir}"
            )

    @classmethod
    def preflight(cls) -> None:
        import box_transport  # noqa: F401  (import failure = misconfigured driver)
        for var in ("BOX_TRANSPORT_ACCESS_KEY",):
            if var not in os.environ:
                raise RuntimeError(
                    f"box-docker transport needs {var} in the driver env "
                    "(see the box transport's credential setup)"
                )

    # ---- sync transport core (always called via asyncio.to_thread) ------------------

    # The remote transport rejects small invocation timeouts (a floor around 30 s).
    # Harbor hardcodes 10 s for is_dir/is_file probes, so every probe would fail
    # without this clamp. Clamping up is safe: Harbor's own wall clocks
    # (asyncio.wait_for) govern phase duration; this only bounds the transport.
    _MIN_BOX_TIMEOUT = 30

    def _run(self, script: str, timeout: int = 60, name: str = "hb") -> str:
        return box_run(
            self._box,
            script,
            timeout=max(self._MIN_BOX_TIMEOUT, int(timeout)),
            name=name,
            state_file=self._state_file,
        )

    @staticmethod
    def _parse_marks(text: str) -> tuple[int, str, str]:
        rc, out, err = 125, "", ""
        for line in text.splitlines():
            if line.startswith(_RC_MARK):
                try:
                    rc = int(line[len(_RC_MARK):].strip())
                except ValueError:
                    pass
            elif line.startswith(_OUT_MARK):
                out = base64.b64decode(line[len(_OUT_MARK):].strip() or b"").decode(
                    errors="replace"
                )
            elif line.startswith(_ERR_MARK):
                err = base64.b64decode(line[len(_ERR_MARK):].strip() or b"").decode(
                    errors="replace"
                )
        return rc, out, err

    def _stage_bytes_sync(self, data: bytes, remote_path: str) -> None:
        """Stage bytes to a host path via the content-addressed cache: HIT = one
        sha-verified cp; MISS = gzip+b64 chunk-append, sha-verified, then cached."""
        sha = hashlib.sha256(data).hexdigest()
        cache = f"{STAGE_ROOT}/cache/{sha}"
        rp, cp = shlex.quote(remote_path), shlex.quote(cache)
        hit = self._run(
            f"mkdir -p {shlex.quote(os.path.dirname(remote_path))} {STAGE_ROOT}/cache\n"
            f"if [ -f {cp} ] && echo '{sha}  '{cp} | sha256sum -c --quiet - "
            f">/dev/null 2>&1; then cp {cp} {rp} && echo CACHE_HIT; else echo CACHE_MISS; fi"
        )
        if "CACHE_HIT" in hit:
            return
        b64 = base64.b64encode(gzip.compress(data)).decode()
        tmp = shlex.quote(f"{remote_path}.b64")
        # a dropped/duplicated transport chunk corrupts the whole append chain, so the
        # mismatch is retried from a clean temp file (one clean retry clears it)
        last = ""
        for _attempt in range(3):
            self._run(f": > {tmp}")
            for i in range(0, len(b64), _CHUNK):
                self._run(f"printf %s {shlex.quote(b64[i:i + _CHUNK])} >> {tmp}")
            out = self._run(
                f"base64 -d {tmp} | gunzip > {rp} && rm -f {tmp} && "
                f"cp {rp} {cp} && sha256sum {rp} | cut -d' ' -f1"
            )
            last = out.strip().splitlines()[-1].strip() if out.strip() else ""
            if last == sha:
                return
        raise RuntimeError(
            f"stage sha mismatch for {remote_path} after 3 attempts: "
            f"want {sha[:16]} got {last[:16]}"
        )

    def _stage_dir_sync(self, source_dir: Path | str, remote_dir: str) -> None:
        """Per-file staging so the cache works per artifact (a large file already in
        the cache is a HIT; small files upload in one chunk each)."""
        src = Path(source_dir)
        for p in sorted(src.rglob("*")):
            if p.is_file():
                rel = p.relative_to(src).as_posix()
                self._stage_bytes_sync(p.read_bytes(), f"{remote_dir}/{rel}")

    def _pull_bytes_sync(self, producer: str, box_file: str, timeout: int = 120) -> bytes:
        """Run `producer` (a script that must create `box_file`), then pull it via
        b64 split + chunk cat. Loud failure beyond the patience bound."""
        bf = shlex.quote(box_file)
        xd = shlex.quote(f"{box_file}.chunks")
        prep = self._run(
            f"set -e\n{producer}\n"
            f"rm -rf {xd} && mkdir -p {xd}\n"
            f"base64 -w0 {bf} | split -b {_CHUNK} -d -a 4 - {xd}/c_\n"
            f"echo NCHUNKS=$(ls {xd}/c_* | wc -l)",
            timeout=timeout,
        )
        n = None
        for line in prep.splitlines():
            if line.startswith("NCHUNKS="):
                n = int(line.split("=", 1)[1])
        if not n:
            raise FileNotFoundError(f"pull producer failed on {self._box}: {prep[-500:]}")
        if n > _MAX_PULL_CHUNKS:
            raise RuntimeError(
                f"pull of {box_file}: {n} chunks exceeds patience bound "
                f"{_MAX_PULL_CHUNKS} — route bulk downloads through another channel"
            )
        parts = []
        for i in range(n):
            out = self._run(f"cat {xd}/c_{i:04d}").strip()
            if not out:
                raise RuntimeError(f"empty pull chunk {i}/{n} for {box_file}")
            parts.append(out)
        self._run(f"rm -rf {xd} {bf}")
        return base64.b64decode("".join(parts))

    # ---- network posture -------------------------------------------------------------

    def _net_flags(self) -> str:
        mode = self._network_policy.network_mode
        if mode == NetworkMode.NO_NETWORK:
            return "--network none "
        if mode == NetworkMode.ALLOWLIST:
            return f"--network {AIRGAP_NET} --add-host {ALLOW_HOST}:{PIN_IP} "
        return ""

    def _ensure_airgap_sync(self) -> None:
        """Install (idempotent) + verify the allowlist wall, fail-closed. The probe
        uses the just-built task image's node (the host has no alpine)."""
        self._run(f"""
set -e
if docker network inspect {AIRGAP_NET} >/dev/null 2>&1 && \
   iptables -S DOCKER-USER 2>/dev/null | grep -q -- "{AIRGAP_SUBNET}.*DROP"; then
  echo AIRGAP_REUSE
else
  docker network create --subnet {AIRGAP_SUBNET} --gateway {AIRGAP_GW} {AIRGAP_NET} >/dev/null 2>&1 || true
  iptables -S DOCKER-USER 2>/dev/null | grep -- "{AIRGAP_SUBNET}" | sed 's/^-A/-D/' | \
    while read -r r; do iptables $r 2>/dev/null; done
  iptables -I DOCKER-USER -s {AIRGAP_SUBNET} -j DROP
  iptables -I DOCKER-USER -s {AIRGAP_SUBNET} -p udp --dport 53 -j RETURN
  iptables -I DOCKER-USER -s {AIRGAP_SUBNET} -p tcp --dport 53 -j RETURN
  iptables -I DOCKER-USER -s {AIRGAP_SUBNET} -d {PIN_IP} -p tcp --dport 443 -j RETURN
  echo AIRGAP_INSTALLED
fi
""", name="hb-airgap")
        probe_js = (
            "const t=(m,c)=>{const s=require('net')"
            ".connect(443,c);s.setTimeout(5000);"
            "s.on('connect',()=>{console.log(m+'_CONNECT');s.destroy();next()});"
            "const f=()=>{console.log(m+'_BLOCKED');s.destroy();next()};"
            "s.on('error',f);s.on('timeout',f)};"
            "const q=[['PIN','" + PIN_IP + "'],['GH','140.82.112.3']];"
            "let i=0;const next=()=>{if(i<q.length){const[m,c]=q[i++];t(m,c)}else process.exit(0)};"
            "next();"
        )
        out = self._run(
            f"docker run --rm --network {AIRGAP_NET} --entrypoint node "
            f"{shlex.quote(self._image)} -e {shlex.quote(probe_js)}",
            timeout=60, name="hb-airgapverify",
        )
        if "PIN_CONNECT" not in out or "GH_CONNECT" in out:
            raise RuntimeError(
                f"airgap verify FAILED on {self._box} (fail-closed, refusing to "
                f"start): {out[-300:]}"
            )

    # ---- lifecycle -------------------------------------------------------------------

    # One container per box: co-resident sandboxes interfere, so capacity scales by
    # adding boxes, never by stacking. The name-hash box pick can collide, so the
    # mutex is enforced here, not by the scheduler's global concurrency cap.
    _box_locks: dict = {}
    _box_lock_loops: dict = {}
    _box_locks_guard = threading.Lock()

    @classmethod
    def _box_lock(cls, box: str) -> "asyncio.Lock":
        loop = asyncio.get_running_loop()
        with cls._box_locks_guard:
            lock = cls._box_locks.get(box)
            previous = cls._box_lock_loops.get(box)
            if lock is not None and previous is not loop:
                waiters = getattr(lock, "_waiters", None) or ()
                if lock.locked() or any(not waiter.done() for waiter in waiters):
                    raise RuntimeError(f"box {box} retains a lease in another event loop")
                # Sequential asyncio.run invocations can reuse a released box,
                # but must never silently replace a held/quarantined old lease.
                lock = None
            if lock is None:
                lock = cls._box_locks[box] = asyncio.Lock()
                cls._box_lock_loops[box] = loop
            return lock

    async def start(self, force_build: bool) -> None:
        if getattr(self, "_held_box_lock", None) is not None:
            raise RuntimeError("this environment already owns a box lease")
        lock = self._box_lock(self._box)
        # An awaiting/cancelled waiter owns nothing. stop() must not release the
        # lease held by some other environment.
        await lock.acquire()
        self._held_box_lock = lock
        self._cleanup_task = None
        self._start_task = asyncio.create_task(asyncio.to_thread(self._start_sync, force_build))
        try:
            await asyncio.shield(self._start_task)
        except BaseException:
            # stop drains the still-running start worker, confirms cleanup, then
            # releases ownership. Cleanup failure deliberately quarantines the box.
            await BoxEnvironment.stop(self, delete=False)
            raise

    def _start_sync(self, force_build: bool) -> None:
        env_remote = f"{self._sess_root}/env"
        self._stage_dir_sync(self.environment_dir, env_remote)
        no_cache = "--no-cache " if force_build else ""
        # One build retry: registry pulls intermittently die mid-layer ("short read
        # ... unexpected EOF"). A second attempt resumes from the already-downloaded
        # layers, so the retry is cheap and usually completes.
        tail = ""
        for attempt in ("", " (retry)"):
            out = self._run(
                f"docker build {no_cache}-t {shlex.quote(self._image)} "
                f"{shlex.quote(env_remote)} >{self._sess_root}/build.log 2>&1; "
                f"echo {_RC_MARK}$?",
                timeout=int(self.task_env_config.build_timeout_sec or 600),
                name="hb-build",
            )
            if f"{_RC_MARK}0" in out:
                break
            tail = self._run(f"tail -c 1500 {self._sess_root}/build.log")
        else:
            raise RuntimeError(f"docker build failed on {self._box}: {tail}")

        if self._network_policy.network_mode == NetworkMode.ALLOWLIST:
            self._ensure_airgap_sync()

        out = self._run(
            f"docker rm -f {shlex.quote(self._container)} >/dev/null 2>&1 || true\n"
            f"docker run -d {self._net_flags()}--name {shlex.quote(self._container)} "
            f"--entrypoint sleep {shlex.quote(self._image)} infinity "
            f">/dev/null 2>&1; echo {_RC_MARK}$?\n"
            f"docker exec {shlex.quote(self._container)} "
            f"mkdir -p /logs/agent /logs/verifier /logs/artifacts /tests; "
            f"echo {_RC_MARK}$?",
            name="hb-start",
        )
        rcs = [ln for ln in out.splitlines() if ln.startswith(_RC_MARK)]
        if len(rcs) != 2 or any(ln != f"{_RC_MARK}0" for ln in rcs):
            raise RuntimeError(f"box-docker start failed on {self._box}: {out[-800:]}")

        if self._inject_box_files:
            self._inject_box_files_sync()

        if self._rt_on:
            try:
                # wall-counter baseline: turns cumulative per-rule counters
                # into per-trial deltas at stop (_rt_spool_final)
                self._rt["wall0"] = self._wall_counters()
            except Exception:
                pass
            try:
                c, img = shlex.quote(self._container), shlex.quote(self._image)
                self._run(
                    f"INFO=$(docker inspect --format "
                    f"'{{{{.Id}}}} {{{{.State.StartedAt}}}}' {c} 2>/dev/null | head -1)\n"
                    f"DIG=$(docker image inspect --format '{{{{index .RepoDigests 0}}}}' "
                    f"{img} 2>/dev/null | head -1)\n"
                    f"[ -n \"$DIG\" ] || DIG=local-build-no-digest\n"
                    f"printf '{{\"box\":\"%s\",\"container\":\"%s\","
                    f"\"image\":\"%s\",\"image_digest\":\"%s\","
                    f"\"container_id_started\":\"%s\"}}' "
                    f"'{self._box}' {c} {img} \"$DIG\" \"$INFO\" "
                    f"| docker exec -i {c} sh -c 'cat > /logs/artifacts/runtime-info.json'",
                    name="hb-rtinfo",
                )
            except Exception:
                pass                      # telemetry must never fail the trial

    def _inject_box_files_sync(self) -> None:
        """Host-local closed-book staging: docker cp host-resident files into the
        container; verify each landed non-empty (fail-loud: a missing input would
        otherwise surface as a confusing agent failure)."""
        c = shlex.quote(self._container)
        lines = ["set -e"]
        for box_path, ctr_path in sorted(self._inject_box_files.items()):
            bp, cp = shlex.quote(box_path), shlex.quote(ctr_path)
            parent = shlex.quote(os.path.dirname(ctr_path) or "/")
            lines += [
                f"test -s {bp}",
                f"docker exec {c} mkdir -p {parent}",
                f"docker cp {bp} {c}:{cp}",
                f"docker exec {c} test -s {cp}",
            ]
        lines.append("echo INJECT_OK")
        out = self._run("\n".join(lines), name="hb-inject")
        if "INJECT_OK" not in out:
            raise RuntimeError(
                f"box-file injection failed on {self._box} "
                f"({sorted(self._inject_box_files)}): {out[-500:]}"
            )

    def _stop_sync(self, delete: bool):
        if self._rt_on:
            try:
                self._rt_spool_final()
            except Exception:
                pass                      # telemetry must never block teardown
        name_filter = shlex.quote("name=^/" + self._container + "$")
        script = ("set -e\n"
                  f"IDS=$(docker ps -aq --filter {name_filter})\n"
                  'if [ -n "$IDS" ]; then docker rm -f "$IDS" >/dev/null; fi\n'
                  f"IDS=$(docker ps -aq --filter {name_filter})\n"
                  '[ -z "$IDS" ]\n')
        if delete:
            script += f"rm -rf {shlex.quote(self._sess_root)}\n"
        script += "echo BOX_CLEANUP_CONFIRMED\n"
        out = self._run(script, name="hb-stop")
        if "BOX_CLEANUP_CONFIRMED" not in out.splitlines():
            raise RuntimeError(f"box cleanup unconfirmed on {self._box}; lease retained")

    async def _cleanup_owned(self, delete: bool):
        starter = getattr(self, "_start_task", None)
        if starter is not None:
            try:
                await _drain_owned_task(starter)
            except BaseException:
                pass                      # failed startup can still have left a container
        await asyncio.to_thread(self._stop_sync, delete)
        lock = getattr(self, "_held_box_lock", None)
        if lock is not None:
            lock.release()
            self._held_box_lock = None

    async def stop(self, delete: bool):
        if getattr(self, "_held_box_lock", None) is None:
            return                        # cancelled waiter / already confirmed teardown
        task = getattr(self, "_cleanup_task", None)
        if task is None or (task.done() and task.exception() is not None):
            task = self._cleanup_task = asyncio.create_task(self._cleanup_owned(delete))
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            await _drain_owned_task(task)
            raise
        # The content cache (STAGE_ROOT/cache) survives deliberately: it is shared
        # across trials of the same task materials. Operator-level cleanup.

    def _wall_counters(self) -> list:
        """DOCKER-USER per-rule packet/byte counters (allowed dsts + drops)."""
        rows = []
        out = self._run(
            "iptables -L DOCKER-USER -vxn 2>/dev/null | grep -E 'RETURN|DROP' | "
            "awk '{print $1, $2, $3, $9, $10, $11}'",
            name="hb-wall",
        )
        for line in out.splitlines():
            p = line.split()
            if len(p) >= 3 and p[0].isdigit() and p[1].isdigit():
                rows.append({"pkts": int(p[0]), "bytes": int(p[1]),
                             "rule": " ".join(p[2:])[:70]})
        return rows

    def _rt_spool_final(self) -> None:
        """Final container state: ExitCode/OOMKilled/Status from docker inspect just
        before rm, plus provider-side exec counters. Written to a host-side spool
        keyed by session id; the evidence collector joins it in."""
        out = self._run(
            f"docker inspect --format "
            f"'{{{{.State.Status}}}} {{{{.State.ExitCode}}}} {{{{.State.OOMKilled}}}}' "
            f"{shlex.quote(self._container)} 2>/dev/null | head -1 || echo gone",
            name="hb-rtfinal",
        ).strip().splitlines()
        raw = out[-1].strip() if out else "gone"
        # Interface traffic totals while the container still exists (exec fails on a
        # stopped container: recorded as unavailable, never fatal)
        net = None
        try:
            nout = self._run(
                f"docker exec {shlex.quote(self._container)} sh -c "
                f"'cd /sys/class/net/eth0/statistics 2>/dev/null && "
                f"cat rx_bytes tx_bytes rx_packets tx_packets' 2>/dev/null || true",
                name="hb-rtnet",
            ).split()
            if len(nout) >= 4 and all(x.isdigit() for x in nout[-4:]):
                rx_b, tx_b, rx_p, tx_p = (int(x) for x in nout[-4:])
                net = {"rx_bytes": rx_b, "tx_bytes": tx_b,
                       "rx_packets": rx_p, "tx_packets": tx_p, "iface": "eth0"}
        except Exception:
            pass
        # Per-destination flows. Hosts may ship neither the conntrack CLI nor
        # /proc/net/nf_conntrack, so the record is built from what is there:
        #   (a) iptables DOCKER-USER per-rule byte/packet counters: allowed
        #       destinations and dropped (blocked-attempt) traffic. Counters are
        #       cumulative since rule creation; a start-time snapshot (wall0, taken
        #       in _start_sync) turns them into per-trial deltas. Per-subnet, which
        #       is per-trial here (one container per box, mutex-enforced).
        #   (b) live TCP connections read host-side from the container's own netns
        #       (/proc/<pid>/net/tcp): long-lived connections still open at stop
        # Host-side only; nothing enters the container or the verdict path.
        flows = None
        try:
            wall0 = {r["rule"]: r for r in self._rt.get("wall0", [])}
            rules = []
            for r in self._wall_counters():
                base = wall0.get(r["rule"])
                rules.append({
                    "rule": r["rule"],
                    "pkts": r["pkts"] - base["pkts"] if base else r["pkts"],
                    "bytes": r["bytes"] - base["bytes"] if base else r["bytes"],
                    "per_trial_delta": bool(base)})
            conns = []
            cout = self._run(
                f"PID=$(docker inspect -f '{{{{.State.Pid}}}}' "
                f"{shlex.quote(self._container)} 2>/dev/null); "
                f"[ -n \"$PID\" ] && [ \"$PID\" != 0 ] && "
                f"awk 'NR>1 {{print $3}}' /proc/$PID/net/tcp 2>/dev/null "
                f"| sort | uniq -c | head -20 || true",
                name="hb-rtflow",
            )
            for line in cout.splitlines():
                parts = line.split()
                if len(parts) == 2 and parts[0].isdigit() and ":" in parts[1]:
                    ip_hex, _, port_hex = parts[1].partition(":")
                    try:
                        ip = ".".join(str(int(ip_hex[i:i + 2], 16))
                                      for i in range(6, -2, -2))
                        conns.append({"n": int(parts[0]),
                                      "dst": f"{ip}:{int(port_hex, 16)}"})
                    except ValueError:
                        continue
            if rules or conns:
                flows = {"wall": rules or None,
                         "open_conns_at_stop": conns or None}
        except Exception:
            pass
        spool = os.environ.get(
            "VERITAS_RUNTIME_SPOOL",
            "/opt/gavel/runtime/v2_runtime_spool")
        os.makedirs(spool, exist_ok=True)
        rec = {"session_id": self.session_id, "box": self._box,
               "container": self._container, "final_raw": raw,
               "oom_killed": raw.endswith("true"),
               "net": net,
               "net_flows": flows,
               "execs": self._rt.get("execs", 0),
               "exec_failures": self._rt.get("exec_failures", 0)}
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in self.session_id)
        with open(os.path.join(spool, f"{safe}.json"), "w") as fh:
            json.dump(rec, fh, indent=1)

    # ---- exec ------------------------------------------------------------------------

    async def exec(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout_sec: int | None = None,
        user: str | int | None = None,
    ) -> ExecResult:
        return await asyncio.to_thread(
            self._exec_sync, command, cwd, env, timeout_sec, user
        )

    def _exec_sync(self, command, cwd, env, timeout_sec, user) -> ExecResult:
        """docker exec wrapped so rc/stdout/stderr survive the transport's merged
        output. stdout/stderr are head-capped (_EXEC_OUT_CAP): Harbor only parses small
        exec outputs (pwd, versions, find listings); bulk data goes through download_*.
        Note: env values (incl. API keys) ride the transport payload."""
        user = self._resolve_user(user)
        merged = {**self._pass_env, **(self._merge_env(env) or {})}
        envflags = " ".join(f"-e {shlex.quote(f'{k}={v}')}" for k, v in merged.items())
        uflag = f"-u {shlex.quote(str(user))} " if user is not None else ""
        wflag = f"-w {shlex.quote(cwd)} " if cwd else ""
        tag = uuid.uuid4().hex[:8]
        o, e = f"/tmp/hb_{tag}.out", f"/tmp/hb_{tag}.err"
        # bash, not sh: Harbor's POSIX provider contract is `bash -c` (docker_unix.py);
        # the installed-agent layer prefixes commands with `set -o pipefail`
        # (agents/installed/base.py), which dash rejects ("sh: 1: set: Illegal option
        # -o pipefail"). Images must ship bash, same as for Harbor's own docker
        # provider.
        inner = f"bash -c {shlex.quote(command)} > {o} 2> {e}"
        c = shlex.quote(self._container)
        script = (
            f"docker exec {uflag}{wflag}{envflags} {c} bash -c {shlex.quote(inner)}\n"
            f"rc=$?\n"
            f"echo {_RC_MARK}$rc\n"
            f"echo {_OUT_MARK}$(docker exec {c} sh -c "
            f"{shlex.quote(f'head -c {_EXEC_OUT_CAP} {o} | base64 -w0')})\n"
            f"echo {_ERR_MARK}$(docker exec {c} sh -c "
            f"{shlex.quote(f'head -c {_EXEC_OUT_CAP} {e} | base64 -w0')})\n"
            f"docker exec {c} rm -f {o} {e}"
        )
        text = self._run(
            script,
            timeout=int(timeout_sec or _DEFAULT_EXEC_TIMEOUT),
            name="hb-exec",
        )
        rc, out, err = self._parse_marks(text)
        if self._rt_on:
            self._rt["execs"] += 1
            if rc != 0:
                self._rt["exec_failures"] += 1
        return ExecResult(stdout=out, stderr=err, return_code=rc)

    # ---- file transfer ---------------------------------------------------------------

    async def upload_file(self, source_path: Path | str, target_path: str):
        await asyncio.to_thread(self._upload_file_sync, source_path, target_path)

    def _upload_file_sync(self, source_path, target_path) -> None:
        box_tmp = f"{self._sess_root}/xfer/{uuid.uuid4().hex[:8]}"
        self._stage_bytes_sync(Path(source_path).read_bytes(), box_tmp)
        c = shlex.quote(self._container)
        out = self._run(
            f"docker exec {c} mkdir -p "
            f"{shlex.quote(os.path.dirname(target_path) or '/')} && "
            f"docker cp {shlex.quote(box_tmp)} {c}:{shlex.quote(target_path)}; "
            f"echo {_RC_MARK}$?; rm -f {shlex.quote(box_tmp)}"
        )
        if f"{_RC_MARK}0" not in out:
            raise RuntimeError(f"upload_file({target_path}) failed: {out[-400:]}")

    async def upload_dir(self, source_dir: Path | str, target_dir: str):
        await asyncio.to_thread(self._upload_dir_sync, source_dir, target_dir)

    def _upload_dir_sync(self, source_dir, target_dir) -> None:
        box_tmp = f"{self._sess_root}/xfer/{uuid.uuid4().hex[:8]}"
        self._stage_dir_sync(source_dir, box_tmp)
        c = shlex.quote(self._container)
        out = self._run(
            # mkdir box_tmp too: staging an empty source dir stages zero files, and
            # `docker cp` of a nonexistent dir fails.
            f"mkdir -p {shlex.quote(box_tmp)} && "
            f"docker exec {c} mkdir -p {shlex.quote(target_dir)} && "
            f"docker cp {shlex.quote(box_tmp)}/. {c}:{shlex.quote(target_dir)}; "
            f"echo {_RC_MARK}$?; rm -rf {shlex.quote(box_tmp)}"
        )
        if f"{_RC_MARK}0" not in out:
            raise RuntimeError(f"upload_dir({target_dir}) failed: {out[-400:]}")

    async def download_file(self, source_path: str, target_path: Path | str):
        data = await asyncio.to_thread(self._download_file_sync, source_path)
        Path(target_path).parent.mkdir(parents=True, exist_ok=True)
        Path(target_path).write_bytes(data)

    def _download_file_sync(self, source_path: str) -> bytes:
        tag = uuid.uuid4().hex[:8]
        box_tmp = f"{self._sess_root}/xfer/{tag}"
        producer = (
            f"mkdir -p {self._sess_root}/xfer\n"
            f"docker cp {shlex.quote(self._container)}:{shlex.quote(source_path)} "
            f"{shlex.quote(box_tmp)}"
        )
        return self._pull_bytes_sync(producer, box_tmp)

    async def download_dir(self, source_dir: str, target_dir: Path | str):
        data = await asyncio.to_thread(self._download_dir_sync, source_dir)
        target = Path(target_dir)
        target.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
            tf.extractall(path=target, filter="data")

    def _download_dir_sync(self, source_dir: str) -> bytes:
        tag = uuid.uuid4().hex[:8]
        box_tmp = f"{self._sess_root}/xfer/{tag}.tgz"
        c = shlex.quote(self._container)
        producer = (
            f"mkdir -p {self._sess_root}/xfer\n"
            f"docker exec {c} sh -c "
            f"{shlex.quote(f'tar czf /tmp/hb_{tag}.tgz -C {shlex.quote(source_dir)} .')}\n"
            f"docker cp {c}:/tmp/hb_{tag}.tgz {shlex.quote(box_tmp)}\n"
            f"docker exec {c} rm -f /tmp/hb_{tag}.tgz"
        )
        return self._pull_bytes_sync(producer, box_tmp)


if __name__ == "__main__":
    # Import-shape smoke check only (no remote contact): class loads, contract holds.
    abstract = getattr(BoxEnvironment, "__abstractmethods__", frozenset())
    print(json.dumps({
        "class": BoxEnvironment.__name__,
        "type": BoxEnvironment.type(),
        "unimplemented_abstract": sorted(abstract),
        "box_run_imported_from": sys.modules["box_transport"].__file__,
    }, indent=2))
