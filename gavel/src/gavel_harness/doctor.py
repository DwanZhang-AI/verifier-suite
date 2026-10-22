"""Host checks run before ``gavel-harness gen`` (``gavel-harness doctor``).

Every check is a function that returns a :class:`CheckResult` (name, ok,
detail) and never raises for the condition it checks; a failed check makes the
run exit with ``ExitCode.CONFIG``, and every result, passed or failed, is
recorded in ``run.json``. Checks that run commands take a ``run`` callable with
the signature of :func:`subprocess.run`, and the endpoint check takes an
``httpx.Client``, so they can be exercised offline.

Containers a check starts are removed when they exit and carry the label
``veritas.run=<run_id>``; no check pulls an image on purpose, but ``docker run``
pulls an image that is not present locally.
"""

from __future__ import annotations

import csv
import fnmatch
import hashlib
import json
import os
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from importlib import metadata, resources
from pathlib import Path, PurePosixPath
from typing import Any

import httpx

from .config import RUN_LABEL, VERIFIER_NETWORK_MODES
from .errors import ConfigError
from .method.identity import file_manifest
from .provenance import GitState, package_state

Runner = Callable[..., subprocess.CompletedProcess[str]]
"""A callable with the signature of :func:`subprocess.run`, called with text output."""

ENDPOINT_APIS = ("chat_completions", "responses")
"""Model APIs an executor can require (``endpoint_api`` in the executor registry)."""

ABLATION_SWITCHES = ("VERITAS_NO_*", "VERITAS_*_BARE", "VERITAS_PROMPTS_DIR")
"""Environment variables (glob patterns) through which the original harness switched
prompt ablations and alternative prompt directories. This harness reads none of them; a run
refuses to start while one is set, so nobody believes it took effect."""


@dataclass(frozen=True)
class HarborPin:
    """The Harbor build every run of the method used.

    ``content_sha256`` is the sha256 of the ``sha256sum``-style listing
    (``<file sha256>  <path>\\n`` per file, sorted by path) of the installed
    ``harbor`` package files, bytecode and ``harbor/viewer/static/`` excluded;
    for a correct install it equals the same listing of ``src/harbor`` at
    ``commit`` with ``src/`` removed from the paths.
    """

    version: str
    commit: str
    content_sha256: str


HARBOR_PIN = HarborPin(
    version="0.21.0",
    commit="2fe1615503fed39ad82b7ce09b22497996b30f1f",
    content_sha256="4542f84b9fb794ad372cdcc661b96bb5ea55fa0ab704c591284b8bbaaee44db8",
)
# The harbor 0.21.0 wheel on PyPI is not this commit (its agent and docker
# environment sources differ), so the version alone does not identify the build.

RUBRIC_LIBRARY_SHA256 = "b07fb5e94918b18e61e8abfdb46c7ecea9aa962d7129681e94e67cb00894dee0"
"""sha256 of the canonical JSON of :func:`~gavel_harness.method.identity.file_manifest`
over the shipped ``rubric/library_v1`` tree; see :func:`rubric_tree_sha256`."""

_PROCESS_EVIDENCE_PREFIX = "process."
_DOCKER_RUN_FAILURES = frozenset({125, 126, 127})
# docker run exits 125 when the daemon cannot create or start the container,
# 126 when the entrypoint is not executable and 127 when it does not exist;
# the commands the checks run in containers never exit with these statuses.
_ENDPOINT_PROMPT = "Reply with the single word OK."
_COMPOSE_PROBE_MAIN: Mapping[str, Any] = {
    "image": "veritas-doctor-probe", "environment": {"VERITAS_DOCTOR_PROBE": "1"},
    "depends_on": ["sidecar"]}
_COMPOSE_PROBE_PACKAGE: Mapping[str, Any] = {"services": {
    "main": _COMPOSE_PROBE_MAIN,
    "sidecar": {"image": "veritas-doctor-probe", "command": ["sleep", "infinity"]}}}


@dataclass(frozen=True)
class CheckResult:
    """Outcome of one check; ``detail`` is for people and is never parsed."""

    name: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_repo_clean(
    *,
    allow_dirty: bool,
    state: Callable[[], tuple[GitState, str]] = package_state,
) -> CheckResult:
    """The harness code is committed, or ``--allow-dirty`` accepts that it is not.

    ``state`` returns the harness commit state and its source (``checkout`` or
    ``wheel``; see :func:`gavel_harness.provenance.package_state`). A checkout
    without a commit counts as uncommitted. Accepted uncommitted changes pass
    and say so in the detail.
    """
    name = "repo_clean"
    try:
        git, source = state()
    except ConfigError as exc:
        return CheckResult(name, False, str(exc))
    where = "source checkout" if source == "checkout" else "wheel build record"
    commit = git.commit[:12] if git.commit else "no commit"
    if git.commit is not None and not git.dirty:
        return CheckResult(name, True, f"gavel-harness {commit}, clean ({where})")
    if allow_dirty:
        return CheckResult(
            name, True,
            f"gavel-harness {commit} has uncommitted changes ({where}); "
            "accepted by --allow-dirty",
        )
    return CheckResult(
        name, False,
        f"gavel-harness {commit} has uncommitted changes ({where}); "
        "commit them or pass --allow-dirty",
    )


def check_harbor_pin(
    *,
    distribution: metadata.Distribution | None = None,
    pin: HarborPin = HARBOR_PIN,
) -> CheckResult:
    """The installed Harbor is ``pin``: same version, not editable, same files.

    ``distribution`` defaults to the installed ``harbor`` distribution. A
    commit recorded by a VCS install must equal ``pin.commit``; the file
    content check (:func:`harbor_content_sha256`) applies to every install and
    is what identifies the commit for path and index installs.
    """
    name = "harbor_pin"
    if distribution is None:
        try:
            distribution = metadata.distribution("harbor")
        except metadata.PackageNotFoundError:
            return CheckResult(name, False, "harbor is not installed")
    problems = []
    if distribution.version != pin.version:
        problems.append(f"version {distribution.version} is not the pinned {pin.version}")
    direct_url = json.loads(distribution.read_text("direct_url.json") or "{}")
    if direct_url.get("dir_info", {}).get("editable", False):
        problems.append("editable install: its code can change while a run uses it")
    vcs_commit = direct_url.get("vcs_info", {}).get("commit_id")
    if vcs_commit is not None and vcs_commit != pin.commit:
        problems.append(f"installed from commit {vcs_commit}, not the pinned {pin.commit}")
    digest, missing = harbor_content_sha256(distribution)
    if missing:
        problems.append(f"{len(missing)} installed file(s) are missing, e.g. {missing[0]}")
    elif digest is None:
        problems.append("the install records no file list (RECORD), so its content is unknown")
    elif digest != pin.content_sha256:
        problems.append(
            f"installed files (content sha256 {digest[:12]}) are not the source of commit "
            f"{pin.commit[:7]} (content sha256 {pin.content_sha256[:12]})"
        )
    if problems:
        return CheckResult(name, False, "; ".join(problems))
    return CheckResult(name, True, f"harbor {pin.version} at commit {pin.commit[:7]} "
                                   f"(content sha256 {pin.content_sha256[:12]})")


def harbor_content_sha256(distribution: metadata.Distribution) -> tuple[str | None, list[str]]:
    """The content digest of an installed ``harbor`` (see :class:`HarborPin`), and missing files.

    The file list is the install's ``RECORD``, read directly: ``Distribution.files``
    leaves out listed files that no longer exist. Returns ``(None, [])`` when
    the install has no ``RECORD``; otherwise the digest over the files that
    exist and the sorted relative paths of those that do not.
    """
    record = distribution.read_text("RECORD")
    if record is None:
        return None, []
    lines = []
    missing = []
    for row in csv.reader(record.splitlines()):
        if not row:
            continue
        rel = PurePosixPath(row[0])
        if (rel.parts[:1] != ("harbor",) or "__pycache__" in rel.parts
                or rel.suffix in (".pyc", ".pyo") or rel.is_relative_to("harbor/viewer/static")):
            continue
        located = Path(str(distribution.locate_file(row[0])))
        if not located.is_file():
            missing.append(rel.as_posix())
            continue
        lines.append(f"{hashlib.sha256(located.read_bytes()).hexdigest()}  {rel.as_posix()}\n")
    lines.sort(key=lambda line: line.split("  ", 1)[1])
    return hashlib.sha256("".join(lines).encode()).hexdigest(), sorted(missing)


def check_docker(*, run: Runner = subprocess.run, timeout_sec: float = 30.0) -> CheckResult:
    """The Docker daemon answers and the ``docker compose`` plugin is installed."""
    name = "docker"
    server = _command(run, ["docker", "version", "--format", "{{.Server.Version}}"], timeout_sec)
    if server.problem is not None:
        return CheckResult(name, False, f"the Docker daemon does not answer: {server.problem}")
    compose = _command(run, ["docker", "compose", "version", "--short"], timeout_sec)
    if compose.problem is not None:
        return CheckResult(name, False, f"docker compose is unavailable: {compose.problem}")
    return CheckResult(name, True, f"docker server {server.stdout.strip()}, "
                                   f"compose {compose.stdout.strip()}")


def check_compose_override(*, run_id: str, run: Runner = subprocess.run,
                           timeout_sec: float = 30.0) -> CheckResult:
    """``docker compose`` leaves a package's own compose file out of a generation trial.

    The generation overlay (:func:`gavel_harness.run.job.write_generation_overlay`)
    replaces a trial's services with ``main`` alone through compose's
    ``!override`` tag. Docker Compose honours the tag from 2.24.4 on; earlier
    versions ignore it without an error and merge the package's services and
    its settings for ``main``. The check writes a probe package to a temporary
    directory (a Dockerfile and a compose file with a sidecar service and
    settings for ``main``) and resolves it with ``docker compose config``,
    which needs no daemon, from Harbor's build service, the package's compose
    file and the generation overlay, in Harbor's order. It passes when the
    result is ``main`` alone with none of the package's settings.
    """
    from harbor.environments.docker import COMPOSE_BUILD_PATH

    from .run.job import write_generation_overlay

    name = "compose_override"
    with tempfile.TemporaryDirectory(prefix="veritas-doctor-") as scratch:
        environment = Path(scratch)
        (environment / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
        package = environment / "docker-compose.yaml"
        package.write_text(json.dumps(_COMPOSE_PROBE_PACKAGE, indent=1), encoding="utf-8")
        overlay = write_generation_overlay(environment / "generation.yaml", run_id)
        argv = ["docker", "compose", "--project-name", "veritas-doctor",
                "--project-directory", str(environment)]
        for path in (COMPOSE_BUILD_PATH, package, overlay):
            argv += ["-f", str(path)]
        outcome = _command(run, [*argv, "config", "--format", "json"], timeout_sec,
                           env={**os.environ, "CONTEXT_DIR": str(environment)})
    if outcome.problem is not None:
        return CheckResult(name, False,
                           f"docker compose could not resolve a generation project: "
                           f"{outcome.problem}")
    try:
        services = json.loads(outcome.stdout)["services"]
        added = sorted(set(services) - {"main"})
        applied = sorted(set(services["main"]) & set(_COMPOSE_PROBE_MAIN))
    except (ValueError, KeyError, TypeError) as exc:
        return CheckResult(name, False, "docker compose config gave no main service: "
                                        f"{type(exc).__name__}: {exc}")
    if added or applied:
        return CheckResult(
            name, False,
            "docker compose ignores the generation overlay's !override tag (Compose before "
            "2.24.4 does, without an error): a package's compose file would add services "
            f"{added} and set {applied} for main; install Docker Compose 2.24.4 or later",
        )
    return CheckResult(name, True, "a package's compose file is left out of generation "
                                   "(!override honoured)")


def check_meter_reachable(
    gateway: str,
    port: int,
    *,
    run_id: str,
    image: str | None = None,
    run: Runner = subprocess.run,
    timeout_sec: float = 120.0,
) -> CheckResult:
    """A container on Docker's default bridge network gets an answer from the meter.

    ``gateway`` and ``port`` are the address trial containers use to reach the
    metering proxy. The container fetches the proxy's health route
    (:data:`gavel_harness.meter.proxy.HEALTH_PATH`) with busybox ``wget``
    (10 s timeout); ``image`` must provide it and defaults to the Alpine image
    Harbor's own egress-control probe uses.
    """
    from harbor.environments.docker.docker import DockerEnvironment

    from .meter.proxy import HEALTH_PATH

    name = "meter_reachable"
    if isinstance(port, bool) or not isinstance(port, int) or not 0 < port < 65536:
        return CheckResult(name, False, f"port must be an integer from 1 to 65535, got {port!r}")
    image = image or DockerEnvironment._EGRESS_CONTROL_KERNEL_PROBE_IMAGE
    host = f"[{gateway}]" if ":" in gateway else gateway
    url = f"http://{host}:{port}{HEALTH_PATH}"
    argv = [
        "docker", "run", "--rm", "--label", f"{RUN_LABEL}={run_id}",
        "--entrypoint", "wget", image, "-q", "-T", "10", "-O", "/dev/null", url,
    ]
    outcome = _command(run, argv, timeout_sec)
    if outcome.problem is None:
        return CheckResult(name, True, f"a container reached the meter at {url}")
    if outcome.code is None or outcome.code in _DOCKER_RUN_FAILURES:
        return CheckResult(
            name, False,
            f"could not run wget in {image} to test {url}: {outcome.problem}",
        )
    return CheckResult(name, False, f"a container could not reach {url}: {outcome.problem}")


def check_endpoint(
    base_url: str,
    model: str,
    endpoint_api: str,
    *,
    api_key_env: str,
    environ: Mapping[str, str] = os.environ,
    client: httpx.Client | None = None,
    timeout_sec: float = 120.0,
) -> CheckResult:
    """The endpoint answers one minimal request on the API the executor needs.

    ``endpoint_api`` is one of :data:`ENDPOINT_APIS`: ``chat_completions`` posts
    one user message to ``<base_url>/chat/completions`` and expects a non-empty
    ``choices`` list; ``responses`` posts one input to ``<base_url>/responses``
    and expects an ``output`` list. The key is read from ``environ[api_key_env]``
    and sent as a bearer token; it never appears in the result. ``client``
    defaults to a fresh ``httpx.Client``.
    """
    name = "endpoint"
    if endpoint_api not in ENDPOINT_APIS:
        return CheckResult(name, False, f"unknown endpoint API {endpoint_api!r}; "
                                        f"expected one of {ENDPOINT_APIS}")
    key = environ.get(api_key_env)
    if not key:
        return CheckResult(name, False, f"environment variable {api_key_env} is not set")
    if endpoint_api == "chat_completions":
        url = f"{base_url.rstrip('/')}/chat/completions"
        body: dict[str, Any] = {"model": model,
                                "messages": [{"role": "user", "content": _ENDPOINT_PROMPT}]}
        answer_key = "choices"
    else:
        url = f"{base_url.rstrip('/')}/responses"
        body = {"model": model, "input": _ENDPOINT_PROMPT}
        answer_key = "output"
    own = client is None
    http = httpx.Client(timeout=timeout_sec) if client is None else client
    try:
        response = http.post(url, json=body, headers={"Authorization": f"Bearer {key}"},
                             timeout=timeout_sec)
    except httpx.HTTPError as exc:
        return CheckResult(name, False, f"POST {url}: {type(exc).__name__}: {exc}")
    finally:
        if own:
            http.close()
    if response.status_code != 200:
        return CheckResult(name, False, f"POST {url}: HTTP {response.status_code}: "
                                        f"{_excerpt(response.text)}")
    try:
        answer = response.json()
    except ValueError:
        return CheckResult(name, False, f"POST {url}: the answer is not JSON: "
                                        f"{_excerpt(response.text)}")
    produced = answer.get(answer_key) if isinstance(answer, dict) else None
    if not isinstance(produced, list) or (answer_key == "choices" and not produced):
        return CheckResult(name, False, f"POST {url}: the answer has no {answer_key} list: "
                                        f"{_excerpt(response.text)}")
    return CheckResult(name, True, f"{model} answered on {url} ({endpoint_api})")


def rubric_needed(judge_evidence: Mapping[str, str], *, rubric: bool = True) -> bool:
    """Whether packages with this evidence surface tell the agent to read ``/rubric_lib``.

    The rule of :func:`gavel_harness.method.compose.compose`: the rubric
    directive is rendered when the rubric switch is on and some evidence type
    starts with ``process.``.
    """
    return rubric and any(etype.startswith(_PROCESS_EVIDENCE_PREFIX)
                          for etype in judge_evidence.values())


def shipped_rubric_library() -> Path:
    """The ``rubric/library_v1`` directory shipped with the package (the mount source)."""
    return Path(str(resources.files("gavel_harness.rubric").joinpath("library_v1")))


def rubric_tree_sha256(root: Path) -> str:
    """sha256 of the canonical JSON of the file manifest of ``root``."""
    manifest = file_manifest(root)
    return hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def check_rubric_mount(
    judge_evidence: Mapping[str, str],
    *,
    rubric: bool = True,
    source: Path | None = None,
    expected_sha256: str = RUBRIC_LIBRARY_SHA256,
) -> CheckResult:
    """When packages need the rubric library, its mount source exists and is the pinned tree.

    ``source`` defaults to :func:`shipped_rubric_library`; it is mounted
    read-only at ``/rubric_lib`` and must be a real directory whose
    :func:`rubric_tree_sha256` equals ``expected_sha256``. When
    :func:`rubric_needed` is false the check passes without looking.
    """
    name = "rubric_mount"
    if not rubric_needed(judge_evidence, rubric=rubric):
        return CheckResult(name, True, "not needed: no process.* evidence in the surface")
    root = shipped_rubric_library() if source is None else source
    if not root.is_dir():
        return CheckResult(name, False, f"rubric library {root} is not a directory")
    digest = rubric_tree_sha256(root)
    if digest != expected_sha256:
        return CheckResult(name, False, f"rubric library {root} has tree sha256 {digest[:12]}, "
                                        f"not the pinned {expected_sha256[:12]}")
    return CheckResult(name, True, f"rubric library {root} (tree sha256 {digest[:12]})")


def check_verifier_egress(
    network: str,
    *,
    run_id: str,
    run: Runner = subprocess.run,
    timeout_sec: float = 120.0,
) -> CheckResult:
    """Harbor can cut the verifier phase off the network when ``network`` is ``no-network``.

    Harbor's docker environment enforces a phase network policy with an
    egress-control sidecar, which needs a Linux Docker host whose kernel has
    nftables ``fib`` support. The check asks the daemon for its OS type and
    runs Harbor's own kernel probe (its image and script) in a labelled
    container; like Harbor, it passes when the kernel configuration is not
    readable. A ``public`` verifier network needs no egress control. Raises
    ConfigError for an unknown network mode.
    """
    name = "verifier_egress"
    if network not in VERIFIER_NETWORK_MODES:
        raise ConfigError(f"verifier network must be one of {VERIFIER_NETWORK_MODES}, "
                          f"got {network!r}")
    if network == "public":
        return CheckResult(name, True, "not needed: the verifier network is public")
    remedy = "pass --verifier-network public to run the verifier phase with network"
    os_type = _command(run, ["docker", "info", "--format", "{{.OSType}}"], timeout_sec)
    if os_type.problem is not None:
        return CheckResult(name, False, f"cannot read the Docker host OS: {os_type.problem}")
    if os_type.stdout.strip() != "linux":
        return CheckResult(name, False, f"the Docker host OS is {os_type.stdout.strip()!r}, "
                                        f"egress control needs linux; {remedy}")
    from harbor.environments.docker.docker import DockerEnvironment

    argv = [
        "docker", "container", "run", "--rm", "--label", f"{RUN_LABEL}={run_id}",
        DockerEnvironment._EGRESS_CONTROL_KERNEL_PROBE_IMAGE,
        "sh", "-c", DockerEnvironment._EGRESS_CONTROL_KERNEL_PROBE_SCRIPT,
    ]
    probe = _command(run, argv, timeout_sec)
    if probe.problem is None:
        return CheckResult(name, True, "linux Docker host; Harbor's nftables kernel probe passed")
    if probe.code is not None and probe.code not in _DOCKER_RUN_FAILURES:
        return CheckResult(name, False, "the Docker host kernel lacks nftables fib support "
                                        f"(CONFIG_NFT_FIB_INET); {remedy}")
    return CheckResult(name, False, f"could not run Harbor's kernel probe: {probe.problem}; "
                                    f"{remedy}")


def check_ablation_switches(environ: Mapping[str, str] = os.environ) -> CheckResult:
    """No variable matching :data:`ABLATION_SWITCHES` is set (case-sensitive glob match).

    Other ``VERITAS_*`` variables are not switches and are ignored.
    """
    name = "ablation_switches"
    found = sorted(variable for variable in environ
                   if any(fnmatch.fnmatchcase(variable, pattern) for pattern in ABLATION_SWITCHES))
    if found:
        return CheckResult(
            name, False,
            f"{', '.join(found)} set: gavel-harness does not read the original harness's "
            "ablation and prompt-directory switches; unset them (method switches are command-line flags; "
            "the prompt wording is the profile's wording key)",
        )
    return CheckResult(name, True, "no ablation or prompt-directory switch is set")


@dataclass(frozen=True)
class _Outcome:
    code: int | None
    """Exit status; None when the command could not be started or timed out."""
    stdout: str
    problem: str | None
    """None on exit 0; otherwise what went wrong, for the detail."""


def _command(run: Runner, argv: list[str], timeout_sec: float,
             env: Mapping[str, str] | None = None) -> _Outcome:
    try:
        result = run(argv, capture_output=True, text=True, timeout=timeout_sec, check=False,
                     env=env)
    except FileNotFoundError:
        return _Outcome(None, "", f"{argv[0]} is not installed")
    except subprocess.TimeoutExpired:
        return _Outcome(None, "", f"{' '.join(argv[:3])} timed out after {timeout_sec:g} s")
    if result.returncode == 0:
        return _Outcome(0, result.stdout, None)
    return _Outcome(result.returncode, result.stdout,
                    f"exit {result.returncode}: {_excerpt(result.stderr or result.stdout)}")


def _excerpt(text: str, limit: int = 300) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "..."
