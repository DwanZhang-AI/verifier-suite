#!/usr/bin/env python3
"""session: the judge harness's one generation entry.

Every dataset generates verifiers the same way: a Harbor job runs the JudgeOpenCode
agent inside the task's packaged environment; the package's tests/ stage doubles as the
dataset's validity probe; probe_core orchestrates the single feedback retry. Datasets
differ only in the package their adapter builds (materials + environment + probe) and
the contract text appended to the shared core prompt.

Self-containment: this package depends on stdlib, the Harbor Python API and the
harbor_integration provider/agent modules. The one-click suite runs the opencode
executor (VERITAS_HARNESS=opencode) on LocalDockerEnvironment; the other executor
branches below are kept from the original harness and are not used by the suite.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Optional

try:
    from . import probe_core, package_inputs
except ImportError:                                # direct-script execution (selftest)
    import probe_core
    import package_inputs

HERE = os.path.dirname(os.path.abspath(__file__))
JUDGE_ROOT = os.path.dirname(HERE)
REPO_HARNESS = os.path.dirname(JUDGE_ROOT)                      # .../harness
HARBOR_VENV = "/opt/gavel/runtime/harbor_venv"
HARBOR_BIN = os.path.join(HARBOR_VENV, "bin", "harbor")
PROVIDER_DIR = os.path.join(REPO_HARNESS, "harbor_integration")  # box_provider / JudgeOpenCode


@dataclass
class SessionConfig:
    model: str                                    # "<provider id>/<model id>"
    boxes: list[str]                              # box names usable as environments
    jobs_dir: str                                 # where Harbor writes trials
    # agent budget sized for the worst case, not the median: token rates drop when
    # many agents share one endpoint, and slow trials must still finish.
    timeout_sec: float = 7200.0
    api_key_env: str = "MODEL_API_KEY"
    opencode_provider: dict = field(default_factory=dict)   # opencode provider block (adapter-agnostic)
    retry: bool = True                            # probe-triggered single feedback retry
    allow_unversioned_packages: bool = False       # explicit legacy replay, never verified
    # Harbor natively converts the agent's event stream into an ATIF trajectory.json
    # (opencode.populate_context_post_run; codex/pi do the same): the standard,
    # cross-harness behaviour record, which is kept. The bulky raw stdout
    # (opencode.txt, opencode/**) is excluded by default; callers may keep it.
    exclude_agent_logs: list = field(default_factory=lambda: ["opencode.txt", "opencode/**"])


@dataclass
class TaskRun:
    task_id: str
    package_dir: str                              # Harbor task package (adapter-built)
    inject_box_files: dict = field(default_factory=dict)     # box path -> container path
    contract_feedback_file: Optional[str] = None  # source splice point; only private copies change


@dataclass
class TrialResult:
    task_id: str
    ok: bool
    reward: Optional[float]
    artifact_dir: Optional[str]
    probe: Optional[probe_core.ProbeResult]
    trial_dir: Optional[str]
    error: str = ""
    attempts: list[dict] = field(default_factory=list)


def _agent_spec(cfg: "SessionConfig", agent_env: dict) -> dict:
    """the one agent block both job builders share. VERITAS_HARNESS selects
    opencode (default; the only executor the one-click suite uses) | codex | pi |
    terminus | hermes | openhands | claude_code | gemini. The non-opencode branches
    are kept from the original harness; they need their own pre-baked images and
    endpoint routing."""
    harness = os.environ.get("VERITAS_HARNESS", "opencode")

    def _endpoint_base(container: bool) -> str:
        """Endpoint base URL for the non-opencode branches, optionally via the
        metering proxy (VERITAS_METER=1): containers reach the host meter at the docker
        bridge gateway; driver-side agents use loopback. Tag set by the batch driver."""
        if os.environ.get("VERITAS_METER") == "1":
            tag = os.environ.get("VERITAS_METER_TAG", "untagged")
            host = "172.17.0.1" if container else "127.0.0.1"
            return f"http://{host}:8877/t/{tag}/api/v3"
        return "https://model-endpoint.example/api/v3"
    if harness in ("codex", "pi"):
        # Both resolve provider from the model-name prefix (harbor model_connection):
        # "openai/<slug>" + OPENAI_API_KEY/OPENAI_BASE_URL in the agent env routes the
        # OpenAI-compatible client at the endpoint. Same endpoint+key as opencode.
        endpoint_model = "openai/" + cfg.model.split("/", 1)[1]
        endpoint_env = {**agent_env,
                   "OPENAI_API_KEY": os.environ.get(cfg.api_key_env, ""),
                   "OPENAI_BASE_URL": _endpoint_base(container=True)}
        if harness == "codex":
            return {
                "import_path": "judge_codex:JudgeCodex",
                "model_name": endpoint_model,
                "override_timeout_sec": cfg.timeout_sec,
                # explicit provider block. codex >=0.153 dropped chat-completions
                # (config load hard-errors on wire_api="chat"), so the endpoint must
                # serve the Responses API. Request/stream retry caps are raised:
                # under rate limiting codex's default retry budget gives up mid-task
                # ("exceeded retry limit... 429").
                "kwargs": {"config": {
                    # VERITAS_CODEX_NO_IMAGE=1: codex auto-attaches viewed images
                    # to the model context; a text-only model rejects the request,
                    # which is fatal on image-centric tasks.
                    **({"tools": {"view_image": False}}
                       if os.environ.get("VERITAS_CODEX_NO_IMAGE") == "1" else {}),
                    "model_provider": "endpoint",
                    "model_providers": {"endpoint": {
                        "name": "endpoint",
                        "base_url": _endpoint_base(container=True),
                        "env_key": "OPENAI_API_KEY",
                        "wire_api": "responses",
                        "request_max_retries": 10,
                        "stream_max_retries": 10,
                    }},
                }},
                "env": endpoint_env,
                "exclude_logs": cfg.exclude_agent_logs,
            }
        return {
            "import_path": "judge_pi:JudgePi",
            "model_name": endpoint_model,
            "override_timeout_sec": cfg.timeout_sec,
            # model_api: pi custom endpoints declare the wire-protocol (models.json "api").
            # openai-responses, not -completions: under chat/completions a reasoning
            # model's reasoning_content counts against the same max_tokens as the
            # answer, so it can reason until stopReason=length and never reach the
            # file-write tool call. The Responses API separates reasoning. maxTokens
            # (judge_pi) still caps the answer, not reasoning.
            "kwargs": {"model_api": "openai-responses"},
            "env": endpoint_env,
            "exclude_logs": cfg.exclude_agent_logs,
        }
    # Generic harbor-native agents: same litellm-style routing, default model
    # "openai/<slug>" pointed at the endpoint; VERITAS_AGENT_MODEL overrides the full
    # model string (e.g. VERITAS_AGENT_MODEL=anthropic/<model> with ANTHROPIC_API_KEY).
    _GENERIC = {
        "terminus": ("harbor.agents.terminus_2:Terminus2", {"api_base": _endpoint_base(container=False)}),
        "hermes": ("judge_hermes:JudgeHermes", {"endpoint_base": _endpoint_base(container=True)}),
        "openhands": ("judge_openhands:JudgeOpenHands", {}),
        # claude_code/gemini speak their native wire protocols (Anthropic Messages /
        # Gemini generateContent); for an OpenAI-compatible endpoint both route
        # through a litellm protocol bridge on the host (port 8899). Version pins
        # match the pre-baked CLIs, so the install step short-circuits on the PATH
        # probe.
        "claude_code": ("harbor.agents.installed.claude_code:ClaudeCode", {"version": "2.1.278"}),
        "gemini": ("harbor.agents.installed.gemini_cli:GeminiCli", {"version": "0.60.0"}),
    }
    if harness in _GENERIC:
        import_path, extra_kwargs = _GENERIC[harness]
        slug = cfg.model.split("/", 1)[1]
        prefix = {"claude_code": "anthropic", "gemini": "gemini"}.get(harness, "openai")
        model = os.environ.get("VERITAS_AGENT_MODEL") or f"{prefix}/{slug}"
        env = {**agent_env}
        bridge = "http://172.17.0.1:8899"
        if model == f"anthropic/{slug}":
            env.update({"ANTHROPIC_BASE_URL": bridge, "ANTHROPIC_AUTH_TOKEN": "sk-bridge"})
        elif model.startswith("anthropic/"):
            env["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY", "")
        elif model.startswith("gemini/"):
            env.update({"GOOGLE_GEMINI_BASE_URL": bridge, "GEMINI_API_KEY": "sk-bridge"})
        else:
            base_c = _endpoint_base(container=True)
            env.update({"OPENAI_API_KEY": os.environ.get(cfg.api_key_env, ""),
                        "OPENAI_BASE_URL": base_c,
                        "OPENAI_API_BASE": base_c})
            # driver-process copies too: Terminus (and other non-installed agents)
            # call litellm FROM the harbor process, not from inside the container —
            # container-only env left the canary with "Missing credentials".
            for k, v in env.items():
                if k.startswith(("OPENAI_",)):
                    os.environ.setdefault(k, v)
        return {
            "import_path": import_path,
            "model_name": model,
            "override_timeout_sec": cfg.timeout_sec,
            "kwargs": extra_kwargs,
            "env": env,
            "exclude_logs": cfg.exclude_agent_logs,
        }
    assert harness == "opencode", f"unknown VERITAS_HARNESS {harness!r}"
    return {
        "import_path": "judge_opencode:JudgeOpenCode",
        "model_name": cfg.model,
        "override_timeout_sec": cfg.timeout_sec,
        "kwargs": {"opencode_config": {
            "provider": cfg.opencode_provider,
            "permission": {"webfetch": "deny", "bash": "allow", "edit": "allow"},
        }},
        "env": agent_env,
        "exclude_logs": cfg.exclude_agent_logs,
    }


def _env_import_path() -> str:
    """Environment backend switch: VERITAS_ENV_LOCAL=1 (set by the one-click suite)
    runs containers on the driver host's docker daemon; the default is the remote
    transport provider of the original harness."""
    if os.environ.get("VERITAS_ENV_LOCAL") == "1":
        return "local_docker_provider:LocalDockerEnvironment"
    return "box_provider:BoxEnvironment"


def _job_config(run: TaskRun, box: str, cfg: SessionConfig, job_name: str,
                extra_agent_env: Optional[dict] = None) -> dict:
    agent_env = {"OPENCODE_DISABLE_AUTOUPDATE": "1", "OPENCODE_DISABLE_LSP_DOWNLOAD": "1"}
    agent_env.update(extra_agent_env or {})
    return {
        "job_name": job_name,
        "jobs_dir": cfg.jobs_dir,
        "n_concurrent_trials": 1,
        "quiet": True,
        "environment": {
            "import_path": _env_import_path(),
            "kwargs": {"box": box, "pass_env": [cfg.api_key_env],
                       "inject_box_files": run.inject_box_files},
        },
        "agents": [_agent_spec(cfg, agent_env)],
        "tasks": [{"path": run.package_dir}],
    }


def _run_harbor(config: dict, log_path: str) -> tuple[bool, str]:
    """Run a job through Harbor's Python API directly (`import harbor`, no shelling
    out, no re-implementation). Requires executing under the Harbor venv's interpreter,
    the judge package's declared runtime. In-process import also lets Harbor resolve
    our provider/agent import_paths from sys.path."""
    cfg_path = log_path.replace(".log", ".config.json")
    json.dump(config, open(cfg_path, "w"), indent=1)
    if PROVIDER_DIR not in sys.path:
        sys.path.insert(0, PROVIDER_DIR)
    import asyncio
    import logging
    from harbor.job import Job                              # noqa: PLC0415
    from harbor.models.job.config import JobConfig          # noqa: PLC0415
    handler = logging.FileHandler(log_path)
    logging.getLogger().addHandler(handler)
    # Progress-stall watchdog: Harbor's async scheduler can deadlock mid-job (main
    # thread idle in select(), containers at 0% CPU, no new results). A wall-clock cap
    # would penalize a slow but advancing job; instead abort only on stalled progress:
    # cancel the job coroutine when nothing progressed for VERITAS_HARNESS_STALL
    # seconds (default 1200). Aborting turns an infinite hang into an ordinary "job
    # failed" that the retry/collect path already handles (undelivered tasks ->
    # no_verifier).
    job_dir = os.path.join(os.path.dirname(log_path), os.path.basename(log_path)[:-4])
    stall = float(os.environ.get("VERITAS_HARNESS_STALL", "1200"))
    stop_watch = threading.Event()

    # Progress signal = completed trials (result.json count) OR an active docker
    # build/exec child of this process. Rationale for the two-part signal:
    #   - result.json count can't be faked by Harbor's continuous job.log appends
    #     (a deadlocked job still writes job.log every second).
    #   - But a single task can legitimately run for hours with no result.json (a cold
    #     multi-GB image build plus the agent budget). Counting trials alone, a tail
    #     of slow cold builds would false-trigger a stall. A real
    #     scheduler deadlock has the main thread idle in select() with NO docker
    #     build/exec subprocess alive; a slow cold build always has one. So an active
    #     docker child counts as progress and the stall only fires when BOTH the trial
    #     count is frozen AND nothing is actually building/executing.
    def _docker_active() -> bool:
        try:
            out = subprocess.run(
                ["pgrep", "-af", "docker (build|exec)"], capture_output=True,
                text=True, timeout=10).stdout
            if out.strip():
                return True
            # builds driven through the docker API leave no CLI process; probe the
            # buildkit worker containers instead (heavy environment builds are
            # otherwise invisible)
            names = subprocess.run(
                ["docker", "ps", "--filter", "name=buildx_buildkit",
                 "--format", "{{.Names}}"], capture_output=True, text=True,
                timeout=10).stdout.split()
            for n in names:
                top = subprocess.run(["docker", "top", n], capture_output=True,
                                     text=True, timeout=10).stdout.strip().splitlines()
                # header + the long-lived buildkitd is idle; extra rows = active build
                if len(top) > 2:
                    return True
            # agent phases may exec through the provider API with no docker CLI
            # process, so a job whose trials are all mid-agent would look dead. A live
            # task container (the provider's image-prefix name) counts as activity;
            # the watchdog's real target (scheduler deadlock) leaves no containers
            # running.
            live = subprocess.run(
                ["docker", "ps", "--filter", "name=harborbox", "-q"],
                capture_output=True, text=True, timeout=10).stdout.strip()
            if live:
                return True
        except Exception:
            return False
        return False

    def _progress_count() -> int:
        n = 0
        for root, _dirs, files in os.walk(job_dir):
            n += "result.json" in files
        return n

    try:
        async def _amain():
            jc = JobConfig.model_validate(config)
            job = await Job.create(jc) if hasattr(Job, "create") else Job(jc)
            task = asyncio.ensure_future(job.run())
            loop = asyncio.get_running_loop()

            def _watch():
                last_progress = time.monotonic()
                last_seen = -1
                while not stop_watch.wait(30):
                    m = _progress_count()
                    now = time.monotonic()
                    if m > last_seen or _docker_active():
                        last_seen, last_progress = m, now
                    elif now - last_progress > stall:
                        logging.getLogger(__name__).error(
                            "harbor stall watchdog: %d trials done, none finished and no "
                            "docker build/exec active for %.0fs; aborting job",
                            m, now - last_progress)
                        loop.call_soon_threadsafe(task.cancel)
                        return

            watcher = threading.Thread(target=_watch, daemon=True)
            watcher.start()
            try:
                await task
            except asyncio.CancelledError:
                # watchdog abort: swallow here so it becomes an ordinary failed job
                # (CancelledError is BaseException, not Exception; it would otherwise
                # escape asyncio.run and crash the whole batch, losing the manifest for
                # every already-delivered task in this attempt).
                logging.getLogger(__name__).error("harbor job cancelled by stall watchdog")
                return False
            finally:
                stop_watch.set()
            return True
        completed = asyncio.run(_amain())
        return bool(completed), cfg_path
    except Exception as e:                                  # honest failure, never silent
        logging.getLogger(__name__).error("harbor job failed: %r", e)
        return False, cfg_path
    finally:
        stop_watch.set()
        logging.getLogger().removeHandler(handler)


def _collect(job_dir: str) -> tuple[Optional[float], Optional[str], Optional[str], str]:
    """single-task job: -> (reward, artifact_dir, trial_dir, verifier_output) of the
    latest trial. Harbor writes one trial dir per task; the verifier stage's stdout
    carries the probe output."""
    if not os.path.isdir(job_dir):
        return None, None, None, ""
    trials = [os.path.join(job_dir, d) for d in os.listdir(job_dir)
              if os.path.isdir(os.path.join(job_dir, d))]
    if not trials:
        return None, None, None, ""
    reward, art, trial, out = _collect_one(max(trials, key=os.path.getmtime))
    return reward, art, trial, out


def run_task(run: TaskRun, box: str, cfg: SessionConfig, spec: probe_core.ProbeSpec,
             tag: str = "a") -> TrialResult:
    """One task through the unified pipeline: Harbor trial -> probe classify -> optional
    single feedback retry (feedback lands only in a frozen-input private variant)
    -> ship-invariant result with complete attempt provenance."""
    return _generate_attempts([run], cfg, spec,
                              f"{os.path.basename(run.package_dir)}-{tag}", box=box)[run.task_id]


def _balanced_box_map(names: list[str], boxes: list[str]) -> dict[str, list[str]]:
    """{box: [env_name...]}: deterministic placement, queue depth capped at
    ceil(n/boxes). Seeded with the provider's crc32 placement so already-warm task
    images stay on their box; only the overflow beyond the cap moves (to the emptiest
    box, sorted-stable). Raw crc32 alone skews queue depths on large batches."""
    import zlib
    # cap floor 2: on small batches a cap of 1 evicts every hash-collided task to a
    # cold box, and simultaneous multi-GB image pulls can exhaust the environment
    # budget. Waiting for one warm holder beats a contended cold pull; depth 2 keeps
    # the waiter's budget sufficient.
    cap = max(2, -(-len(names) // len(boxes)))
    load: dict[str, list[str]] = {b: [] for b in boxes}
    for n in sorted(names):
        load[boxes[zlib.crc32(n.encode()) % len(boxes)]].append(n)
    overflow = []
    for b in boxes:
        load[b], spill = load[b][:cap], load[b][cap:]
        overflow += spill
    for n in overflow:
        tgt = min(boxes, key=lambda b: (len(load[b]), boxes.index(b)))
        load[tgt].append(n)
    return load


def _roll_job_config(runs: list[TaskRun], cfg: SessionConfig, job_name: str) -> dict:
    """One Harbor job for a whole batch: all task packages, box-pool environment (the
    provider places each trial via an explicit balanced box_map), Harbor-native
    n_concurrent_trials."""
    # per-task injection rides a static inject_map keyed by package name; each trial
    # picks its own entry.
    inject_map = {}
    for r in runs:
        if r.inject_box_files:
            base = os.path.basename(r.package_dir)
            inject_map[base] = dict(r.inject_box_files)
            inject_map[base.replace("_", "-")] = dict(r.inject_box_files)
    # balanced cache-affine placement + box-interleaved launch order: Harbor starts
    # tasks in list order, so emitting one task per box per round keeps every in-flight
    # trial on its own box (the per-box mutex then queues at most ONE waiter, and the
    # waiter's env-start budget only has to survive a single holder trial).
    by_run = {os.path.basename(r.package_dir).replace("_", "-"): r for r in runs}
    assert len(by_run) == len(runs), "duplicate package basenames in roll"
    placement = _balanced_box_map(sorted(by_run), cfg.boxes)
    box_map = {n: b for b, ns in placement.items() for n in ns}
    depth = max((len(v) for v in placement.values()), default=0)
    ordered = [by_run[ns[i]] for i in range(depth)
               for _b, ns in sorted(placement.items()) if i < len(ns)]
    assert len(ordered) == len(runs)
    return {
        "job_name": job_name,
        "jobs_dir": cfg.jobs_dir,
        "n_concurrent_trials": len(cfg.boxes),
        "quiet": True,
        "environment": {
            "import_path": _env_import_path(),
            "kwargs": {"boxes": cfg.boxes, "box_map": box_map,
                       "pass_env": [cfg.api_key_env],
                       "inject_map": inject_map},
        },
        "agents": [_agent_spec(cfg, {"OPENCODE_DISABLE_AUTOUPDATE": "1",
                                     "OPENCODE_DISABLE_LSP_DOWNLOAD": "1"})],
        "tasks": [{"path": r.package_dir} for r in ordered],
    }


def _collect_roll(job_dir: str) -> dict[str, tuple[Optional[float], Optional[str], Optional[str], str]]:
    """trial dirs -> {package_basename: (reward, artifact_dir, trial_dir, verifier_output)}.

    Keyed by result.json task_id.path basename, the authoritative package dir. Neither
    task.toml's task_name (upstream-derived formats need not match) nor the trial dir
    prefix (Harbor truncates long trial names to 32 chars, so long names collide) is
    reliable."""
    out = {}
    if not os.path.isdir(job_dir):
        return out
    for d in os.listdir(job_dir):
        t = os.path.join(job_dir, d)
        rj = os.path.join(t, "result.json")
        if not os.path.isdir(t) or not os.path.exists(rj):
            continue
        try:
            key = os.path.basename(json.load(open(rj))["task_id"]["path"].rstrip("/"))
        except (ValueError, KeyError, TypeError):
            key = d.rsplit("__", 1)[0]
        reward, art, _trial, vout = _collect_one(t)
        out[key] = (reward, art, t, vout)
    return out


def _collect_one(trial_dir: str):
    reward = None
    rp = os.path.join(trial_dir, "verifier", "reward.txt")
    rj = os.path.join(trial_dir, "verifier", "reward.json")
    if os.path.exists(rp):
        try:
            reward = float(open(rp).read().strip())
        except ValueError:
            pass
    elif os.path.exists(rj):
        try:
            reward = float(json.load(open(rj)).get("reward"))
        except (ValueError, TypeError):
            pass
    out = ""
    so = os.path.join(trial_dir, "verifier", "test-stdout.txt")
    if os.path.exists(so):
        out = open(so, encoding="utf-8", errors="replace").read()
    art = os.path.join(trial_dir, "artifacts")
    return reward, (art if os.path.isdir(art) else None), trial_dir, out


def generate_roll(runs: list[TaskRun], cfg: SessionConfig, spec: probe_core.ProbeSpec,
                  roll_tag: str) -> dict[str, TrialResult]:
    """The judge harness entry point for a dataset batch: one Harbor job for all tasks
    (attempt A), batch probe classification, ONE retry job for CRASH/NODIRECTION tasks
    with feedback appended to private package copies (attempt B), ship-invariant merge."""
    return _generate_attempts(runs, cfg, spec, f"roll-{roll_tag}")


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _attempt_record(run: TaskRun, snapshot: dict, attempt: int, job_name: str,
                    cfg: SessionConfig, spec: probe_core.ProbeSpec, result: tuple,
                    job_completed: bool, elapsed: float) -> dict:
    reward, art, trial, output = result
    raw = _read_json(Path(trial) / "result.json") if trial else None
    raw = raw if isinstance(raw, dict) else {}
    usage = raw.get("agent_result")
    record = {
        "attempt": attempt, "attempted": True, "completed": bool(raw.get("finished_at")),
        "collected": trial is not None, "job_completed": job_completed,
        "job_name": job_name, "job_elapsed_sec": elapsed,
        "outcome": probe_core.classify(output or "", spec),
        "reward": reward, "artifact_dir": art, "trial_dir": trial,
        "diagnostic": output or "", "input_snapshot": snapshot,
        "artifact_files": package_inputs.file_manifest(art) if art and os.path.isdir(art) else [],
        "usage": usage, "step_results": raw.get("step_results"),
        "started_at": raw.get("started_at"), "finished_at": raw.get("finished_at"),
        "exception_info": raw.get("exception_info"),
        "budget": {"agent_timeout_sec": cfg.timeout_sec, "model": cfg.model,
                   "harness": os.environ.get("VERITAS_HARNESS", "opencode")},
        "shipped": False,
    }
    # Only attach to this attempt's newly-created job, never to historical/foreign trials.
    if trial and os.path.isdir(trial):
        trial_path = Path(trial).resolve()
        job_path = (Path(cfg.jobs_dir) / job_name).resolve()
        if job_path in trial_path.parents:
            pointer = trial_path / "input_snapshot.json"
            pointer.write_text(json.dumps(snapshot, sort_keys=True, indent=2) + "\n")
    return record


def _run_attempt(runs: list[TaskRun], cfg: SessionConfig, spec: probe_core.ProbeSpec,
                 name: str, attempt: int, snapshot_root: Path,
                 feedback: dict[str, str], box: str | None = None) -> tuple[dict, dict]:
    job_name = name + ("-a" if attempt == 0 else "-b")
    if (Path(cfg.jobs_dir) / job_name).exists():
        raise FileExistsError(f"Refusing to reuse an existing Harbor job: {job_name}")
    prepared, snapshots = {}, {}
    for run in runs:
        destination = snapshot_root / str(attempt) / os.path.basename(run.package_dir)
        manifest = destination.parent / (destination.name + ".snapshot.json")
        splice, snapshots[run.task_id] = package_inputs.snapshot_package(
            run.package_dir, str(destination), str(manifest),
            feedback_file=run.contract_feedback_file, feedback=feedback.get(run.task_id),
            injected_files=run.inject_box_files)
        prepared[run.task_id] = TaskRun(run.task_id, str(destination),
                                       dict(run.inject_box_files), splice)
    config = (_job_config(next(iter(prepared.values())), box, cfg, job_name) if box else
              _roll_job_config(list(prepared.values()), cfg, job_name))
    before = time.monotonic()
    job_completed, _ = _run_harbor(config, os.path.join(cfg.jobs_dir, job_name + ".log"))
    elapsed = time.monotonic() - before
    if box:
        only = next(iter(prepared.values()))
        collected = {os.path.basename(only.package_dir): _collect(os.path.join(cfg.jobs_dir, job_name))}
    else:
        collected = _collect_roll(os.path.join(cfg.jobs_dir, job_name))
    records = {}
    for tid, run in prepared.items():
        result = collected.get(os.path.basename(run.package_dir), (None, None, None, ""))
        records[tid] = _attempt_record(run, snapshots[tid], attempt, job_name, cfg, spec,
                                        result, job_completed, elapsed)
    return prepared, records


def _generate_attempts(runs: list[TaskRun], cfg: SessionConfig, spec: probe_core.ProbeSpec,
                       tag: str, box: str | None = None) -> dict[str, TrialResult]:
    if not runs:
        return {}
    if len({r.task_id for r in runs}) != len(runs):
        raise ValueError("duplicate task IDs in generation request")
    if len({os.path.basename(r.package_dir).replace('_', '-') for r in runs}) != len(runs):
        raise ValueError("duplicate package basenames in generation request")
    if not box and not cfg.boxes:
        raise ValueError("generation needs at least one environment box")
    os.makedirs(cfg.jobs_dir, exist_ok=True)
    allow_legacy = cfg.allow_unversioned_packages or os.environ.get("VERITAS_ALLOW_UNVERSIONED") == "disclosed"
    identities = {run.task_id: package_inputs.validate_materialized(
        run.package_dir, allow_unversioned=allow_legacy) for run in runs}
    # Unique job names avoid collecting stale results if a roll tag is reused.
    name = tag + "-" + uuid.uuid4().hex[:12]
    snapshot_root = (Path(cfg.jobs_dir) / "input_snapshots" / name).resolve()
    prepared, first = _run_attempt(runs, cfg, spec, name, 0, snapshot_root, {}, box)
    for tid, record in first.items():
        record["build_identity_status"] = identities[tid]
    feedback = {}
    for tid, record in first.items():
        run = prepared[tid]
        if cfg.retry and record["outcome"] in (probe_core.CRASH, probe_core.NODIRECTION) \
                and run.contract_feedback_file:
            text = spec.crash_feedback if record["outcome"] == probe_core.CRASH else spec.nodirection_feedback
            feedback[tid] = text.replace("{diag}", record["diagnostic"][-1500:])
    second = {}
    if feedback:
        # Retry copies frozen first inputs, not the possibly changed live base package.
        _, second = _run_attempt([prepared[tid] for tid in feedback], cfg, spec, name, 1,
                                 snapshot_root, feedback, box)
        for tid, record in second.items():
            record["build_identity_status"] = identities[tid]
    results = {}
    for tid, original in first.items():
        retry = second.get(tid)
        probe = probe_core.merge(
            tid, spec, original["diagnostic"], retry["diagnostic"] if retry else None,
            retry_attempted=tid in feedback,
            retry_artifact_available=bool(retry and retry["artifact_dir"]))
        selected = retry if probe.shipped == "retry" else original
        selected["shipped"] = True
        attempts = [original] + ([retry] if retry else [])
        # Persist *all* attempts, including attempts without a collected trial, before
        # returning to a caller which may only retain a summary manifest.
        (snapshot_root / (os.path.basename(prepared[tid].package_dir) + ".attempts.json")).write_text(
            json.dumps(attempts, ensure_ascii=False, indent=2) + "\n")
        results[tid] = TrialResult(tid, selected["artifact_dir"] is not None,
                                  selected["reward"], selected["artifact_dir"], probe,
                                  selected["trial_dir"], attempts=attempts)
    return results


def generate(runs: list[TaskRun], cfg: SessionConfig, spec: probe_core.ProbeSpec,
             parallel: Optional[int] = None) -> dict[str, TrialResult]:
    """Per-task-job fan-out (for single-task smokes and inject-based packages);
    dataset batches should use generate_roll (one Harbor job, box pool)."""
    os.makedirs(cfg.jobs_dir, exist_ok=True)
    par = parallel or len(cfg.boxes)
    results: dict[str, TrialResult] = {}

    def work(i_run):
        i, run = i_run
        return run.task_id, run_task(run, cfg.boxes[i % len(cfg.boxes)], cfg, spec)

    with ThreadPoolExecutor(max_workers=par) as ex:
        for tid, res in ex.map(work, enumerate(runs)):
            results[tid] = res
    return results


def _selftest():
    """offline: config shape + collect parsing on a synthetic trial dir."""
    import tempfile
    cfg = SessionConfig(model="endpoint/m", boxes=["b1", "b2"], jobs_dir="/tmp/x",
                        opencode_provider={"endpoint": {}})
    jc = _job_config(TaskRun("t", "/pkg/t", {"/a": "/b"}), "b1", cfg, "j1")
    assert jc["environment"]["kwargs"]["box"] == "b1"
    assert jc["agents"][0]["model_name"] == "endpoint/m"
    assert jc["tasks"] == [{"path": "/pkg/t"}]
    with tempfile.TemporaryDirectory() as d:
        t = os.path.join(d, "trial__x", "verifier")
        os.makedirs(t)
        open(os.path.join(t, "reward.txt"), "w").write("1.0")
        open(os.path.join(t, "test-stdout.txt"), "w").write("PROBE=OK\n")
        os.makedirs(os.path.join(d, "trial__x", "artifacts"))
        reward, art, trial, out = _collect(d)
        assert reward == 1.0 and art and "PROBE=OK" in out
    print("session selftest OK")


if __name__ == "__main__":
    _selftest()
