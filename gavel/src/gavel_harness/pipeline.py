"""The runs behind ``gavel-harness gen``, ``gavel-harness validate --from-run`` and ``gavel-harness matrix``.

``gen`` (:func:`run_gen`), in this order:

1. resolve the method (profile, environment profile, paradigm, package plan,
   anchor judge environment with the command line's network and image-retention
   overrides) and check that the given task list and oracle root exist;
   nothing is written before this succeeds;
2. host checks (:mod:`gavel_harness.doctor`); any failed check exits 2;
3. intake: the inputs are resolved to task directories (registry references
   are fetched), each task is sniffed and packaged, and each accepted task must
   be writable back (:func:`check_writable`) before generation starts; refused
   tasks are listed with their reason and get no result row;
4. the metering proxy starts (unless ``--no-meter``);
5. generation (:func:`gavel_harness.run.generate`), every agent command
   capped at the profile's ``[run] agent_exec_cap_sec`` when it sets one; an
   infrastructure error stops it, every generated task becomes an
   ``infra_error`` row and the run exits 3; a task whose own environment could
   not be built or started is an ``infra_error`` row too (exit 3, re-run) while
   the others go on;
6. write-back of every delivered verifier into a copy of its task;
7. with ``--validate``, the null, oracle and swap anchors (swap donors drawn
   from every accepted task); without it the delivered tasks are
   ``unvalidated``;
8. the report (``results.jsonl``, ``summary.md``, one ``VERIFIER_REPORT.md`` per
   written task) and the exit code;
9. the images Harbor built for the run's trials are removed by exact name,
   unless the profile's ``[anchor] keep_images`` (or ``--keep-images``) keeps them.

From step 2 on, an error that stops the run is recorded in ``run.json``
(``outcome``: exit code, step, error) before it propagates.

Output layout of a ``gen`` run directory::

    run.json            config, provenance, host checks, prompt wording and exec cap,
                        anchor settings, outcome
    packages/           sealed generation packages, _runs.json, refused.jsonl
    jobs/               generation jobs and their input snapshots
    meter/ledger.jsonl  metering proxy ledger (metered runs)
    generation.jsonl    one generation result per generated task
    tasks/<id>/         written-back tasks, each with its VERIFIER_REPORT.md
    anchors/            anchor jobs (with --validate)
    refused.json        {task id: refusal reason}
    results.jsonl  summary.md

``validate --from-run`` (:func:`run_validate`) reads a run of the upstream
one-command driver, writes each delivered verifier back onto its original task
and runs the anchors on it; the run directory is only read. An undelivered task
whose deciding attempt failed on infrastructure is an ``infra_error`` row
(:func:`gavel_harness.export.from_run.attempt_failure`). ``matrix``
(:func:`run_matrix`) samples registry families and runs ``gen --validate`` on
every sampled task, one task at a time, appending one support-matrix row each.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from collections.abc import Mapping, Sequence
from contextlib import ExitStack
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from types import TracebackType
from typing import Any, TextIO

from harbor.models.task.config import TaskOS
from harbor.utils.scripts import discover_script

from . import doctor
from .build.package import build_packages, resolve_plan
from .config import (
    MatrixConfig,
    RunConfig,
    ValidateConfig,
    provider_block,
    slug,
    update_run_json,
    write_run_json,
)
from .errors import (
    ConfigError,
    ExitCode,
    InfraCategory,
    InfraError,
    RefusalError,
    RefusalReason,
    GavelError,
)
from .export.from_run import REFUSED_FILE, attempt_failure, load_refusals, load_run, rate_limited
from .export.matrix import MatrixRow, RunIdentity, append_row, read_rows, write_matrix
from .export.report import (
    RESULTS_FILE,
    SUMMARY_FILE,
    TaskResult,
    exit_code,
    read_results,
    render_summary,
    write_report,
)
from .export.writeback import WrittenTask, check_task_id, merge_task_toml, write_back
from .intake import registry_fetch
from .intake.sniff import sniff
from .meter import MeterEndpoint, MeterProxy
from .method.compose import DEFAULT_SWITCHES
from .paradigms.base import AnchorEnvironment, PackagePlan, Paradigm, get_paradigm
from .profiles import Profile, load_env, load_profile
from .provenance import Provenance
from .provenance import collect as collect_provenance
from .run import GenerationResult, generate
from .run.executors import executor_spec
from .run.usage import TOKEN_FIELDS, task_usage
from .verify.anchors import plan_swaps, remove_trial_image, run_anchors, trial_image_name
from .verify.verdict import SUCCESS_LABELS, AnchorRecord, TaskLabel, label_task

RUN_FILE = "run.json"
GENERATION_FILE = "generation.jsonl"
TASK_MARKERS = ("task.toml", "instruction.md")
"""A directory holding one of these files is a task; discovery does not descend into it."""
PUBLIC_NETWORK_REASON = "--verifier-network public was given on the command line"


@dataclass(frozen=True)
class Method:
    """The resolved method of a run: what packages look like and where anchors judge."""

    profile: Profile
    paradigm: Paradigm
    plan: PackagePlan
    anchor: AnchorEnvironment
    """The profile's anchor judge environment with the run's network and image-retention
    overrides applied."""


@dataclass(frozen=True)
class Endpoint:
    """The model endpoint of a run and how its requests reach it."""

    model: str
    """``<provider id>/<model id>``."""
    base_url: str
    api_key_env: str
    executor: str
    meter: bool
    meter_port: int
    meter_gateway: str | None
    meter_bind: str | None

    @classmethod
    def of(cls, config: RunConfig) -> Endpoint:
        return cls(model=config.model, base_url=config.base_url,
                   api_key_env=config.api_key_env, executor=config.executor,
                   meter=config.meter, meter_port=config.meter_port,
                   meter_gateway=config.meter_gateway, meter_bind=config.meter_bind)


@dataclass(frozen=True)
class TaskInput:
    """One input task: its id in this run and its directory."""

    task_id: str
    task_dir: Path


@dataclass(frozen=True)
class GenOutcome:
    """What :func:`generate_tasks` produced for a set of tasks."""

    results: list[TaskResult]
    refused: dict[str, str]
    """Refusal reason by task id."""
    refusal_errors: dict[str, RefusalError]
    written: dict[str, WrittenTask]
    infra: InfraError | None
    """The infrastructure error that stopped generation, if one did."""
    task_infra: dict[str, InfraError]
    """Infrastructure failures of single tasks by task id (a task environment that could
    not be built or started); their rows are ``infra_error``."""


# ------------------------------------------------------------------ resolution


def resolve_method(*, profile: str, env: str | None, paradigm: str | None, declare: bool,
                   deliverable_dir: str | None, verifier_network: str | None,
                   keep_images: bool | None = None) -> Method:
    """Resolve profile, environment profile and paradigm into a checked package plan.

    ``verifier_network`` and ``keep_images`` override the profile's anchor
    settings when given. Raises ConfigError when a name is unknown, when the
    combination cannot build packages, and for ``declare``: this build neither
    collects the declaration nor builds its certificate, so declare mode would
    change the prompt and drop what it asks for.
    """
    if declare:
        raise ConfigError("declare mode is refused: this build does not collect the agent's "
                          "declaration or build its certificate")
    loaded = load_profile(profile)
    handler = get_paradigm(paradigm or loaded.paradigm)
    plan = resolve_plan(loaded, load_env(env or loaded.env), handler, switches=DEFAULT_SWITCHES,
                        deliverable_dir=deliverable_dir)
    return Method(profile=loaded, paradigm=handler, plan=plan,
                  anchor=anchor_settings(loaded.anchor, verifier_network, keep_images))


def anchor_settings(anchor: AnchorEnvironment, network: str | None,
                    keep_images: bool | None = None) -> AnchorEnvironment:
    """``anchor`` with its network and image retention replaced by the given values.

    A command-line ``public`` network gets :data:`PUBLIC_NETWORK_REASON` as its reason.
    """
    if keep_images is not None:
        anchor = replace(anchor, keep_images=keep_images)
    if network is None or network == anchor.network:
        return anchor
    reason = PUBLIC_NETWORK_REASON if network == "public" else None
    return replace(anchor, network=network, network_reason=reason)


def check_input_paths(*, tasks_file: Path | None = None, oracle_root: Path | None = None) -> None:
    """ConfigError unless the task list is a file and the oracle root a directory (when given)."""
    if tasks_file is not None and not tasks_file.is_file():
        raise ConfigError(f"task list {tasks_file} is not a file")
    if oracle_root is not None and not oracle_root.is_dir():
        raise ConfigError(f"oracle root {oracle_root} is not a directory")


def resolve_run_id(run_id: str | None, out_dir: Path) -> str:
    """``run_id``, or one derived from the output directory name and 6 random hex digits."""
    if run_id is not None:
        return run_id
    stem = slug(out_dir.name).strip("-_")[:40] or "run"
    return f"{stem}-{uuid.uuid4().hex[:6]}"


def discover_tasks(inputs: Sequence[str], *, tasks_file: Path | None, registry: str | None,
                   sample: int | None, seed: int,
                   cache_dir: Path) -> tuple[list[TaskInput], Path | None]:
    """The input tasks of a run in input order, and the root their ids are relative to.

    A path input is a task (a directory holding ``task.toml`` or
    ``instruction.md``) or a directory searched for tasks. A single directory
    input is the root: task ids are paths relative to it (nested ids such as
    ``<field>/<task>``); otherwise a task's id is its directory name.
    A ``registry:<name>@<commit>`` input draws ``sample`` tasks (all when None)
    of that dataset from ``registry`` with ``seed`` and fetches them into
    ``cache_dir``. ``tasks_file`` (one id per line, ``#`` comments) keeps only
    the listed tasks and must name no task that is not found. Raises ConfigError
    for a missing input, an input without tasks or a repeated task id.
    """
    found: list[Path] = []
    directory_inputs: list[Path] = []
    loaded: registry_fetch.Registry | None = None
    for item in inputs:
        if registry_fetch.is_ref(item):
            if registry is None:
                raise ConfigError(f"{item}: a registry input needs --registry <file or URL>")
            ref = registry_fetch.parse_ref(item)
            loaded = loaded or registry_fetch.load_registry(registry)
            source = registry_fetch.family(loaded, ref.name, commit=ref.commit)
            if not source.tasks:
                raise ConfigError(f"{item}: the registry lists no fetchable task "
                                  f"(excluded: {dict(source.excluded)})")
            drawn = registry_fetch.sample(source, sample or len(source.tasks), seed)
            found += [fetched.task_dir for fetched in
                      registry_fetch.fetch_tasks(drawn.tasks, cache_dir)]
            continue
        path = Path(item).expanduser().resolve()
        if not path.is_dir():
            raise ConfigError(f"input {item} is not a directory")
        if _is_task(path):
            found.append(path)
            continue
        under = _tasks_under(path)
        if not under:
            raise ConfigError(f"input {item} holds no task (a directory with "
                              f"{' or '.join(TASK_MARKERS)})")
        found += under
        directory_inputs.append(path)
    root = directory_inputs[0] if len(inputs) == 1 and directory_inputs else None
    tasks = [TaskInput(task_id=path.relative_to(root).as_posix() if root else path.name,
                       task_dir=path) for path in found]
    ids = [task.task_id for task in tasks]
    repeated = sorted({task_id for task_id in ids if ids.count(task_id) > 1})
    if repeated:
        raise ConfigError(f"task ids repeat across the inputs: {repeated[:5]}")
    if tasks_file is not None:
        try:
            lines = tasks_file.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            raise ConfigError(f"cannot read the task list {tasks_file}: {exc}") from exc
        wanted = [line.strip() for line in lines
                  if line.strip() and not line.lstrip().startswith("#")]
        missing = sorted(set(wanted) - set(ids))
        if missing:
            raise ConfigError(f"{tasks_file} names tasks the inputs do not hold: {missing[:5]}")
        tasks = [task for task in tasks if task.task_id in set(wanted)]
    return tasks, root


def _is_task(path: Path) -> bool:
    return any((path / marker).is_file() for marker in TASK_MARKERS)


def _tasks_under(root: Path) -> list[Path]:
    tasks: list[Path] = []
    for child in sorted(path for path in root.iterdir() if path.is_dir()):
        if child.name.startswith("."):
            continue
        tasks += [child] if _is_task(child) else _tasks_under(child)
    return tasks


def find_oracle(task_id: str, task_dir: Path, oracle_root: Path | None) -> Path | None:
    """The reference solution of a task, or None.

    The first non-empty directory of ``<oracle_root>/<task id>/solution`` and
    ``<task_dir>/solution`` (the upstream driver's lookup order).
    """
    candidates = ([oracle_root / task_id / "solution"] if oracle_root is not None else [])
    for candidate in [*candidates, task_dir / "solution"]:
        if candidate.is_dir() and any(candidate.iterdir()):
            return candidate
    return None


def check_writable(task: TaskInput, oracle: Path | None, settings: AnchorEnvironment) -> None:
    """Raise RefusalError(NOT_WRITABLE) unless the task can be written back under ``settings``.

    Checked before generation, so a task that could never be written back does
    not spend a generation trial: its id must name a written-back directory
    (:func:`~gavel_harness.export.writeback.check_task_id`), its task.toml must
    merge, and its reference solution, when there is one, must hold a solve script.
    """
    try:
        check_task_id(task.task_id)
        toml = task.task_dir / "task.toml"
        merge_task_toml(toml.read_text(encoding="utf-8") if toml.is_file() else None, settings)
        check_solution(oracle)
    except ConfigError as exc:
        raise RefusalError(RefusalReason.NOT_WRITABLE, f"task {task.task_id}: {exc}") from exc


def check_solution(oracle: Path | None) -> None:
    """ConfigError when ``oracle`` (a reference solution, or None) holds no solve script."""
    if oracle is not None and discover_script(oracle, "solve", task_os=TaskOS.LINUX) is None:
        raise ConfigError(f"reference solution {oracle} has no solve script")


# ---------------------------------------------------------------- host checks


def host_checks(*, allow_dirty: bool, network: str, run_id: str, generation: bool,
                endpoint: Endpoint | None = None,
                judge_evidence: Mapping[str, str] | None = None,
                rubric: bool = True) -> list[doctor.CheckResult]:
    """Run the host checks of design step 0 that need no running metering proxy.

    ``generation`` adds the compose-override check, which only generation jobs
    need (their overlay relies on compose's ``!override`` tag; the anchors'
    overlay does not); ``endpoint`` adds the endpoint check (one minimal request
    on the API the run's executor needs); ``judge_evidence`` adds the
    rubric-mount check.
    """
    results = [
        doctor.check_ablation_switches(),
        doctor.check_repo_clean(allow_dirty=allow_dirty),
        doctor.check_harbor_pin(),
        doctor.check_docker(),
        doctor.check_verifier_egress(network, run_id=run_id),
    ]
    if generation:
        results.append(doctor.check_compose_override(run_id=run_id))
    if judge_evidence is not None:
        results.append(doctor.check_rubric_mount(judge_evidence, rubric=rubric))
    if endpoint is not None:
        api = executor_spec(endpoint.executor).endpoint_api
        results.append(doctor.check_endpoint(
            endpoint.base_url, endpoint.model.partition("/")[2], api,
            api_key_env=endpoint.api_key_env))
    return results


def report_checks(results: Sequence[doctor.CheckResult], out: TextIO) -> bool:
    """Print one line per check; True when every check passed."""
    for result in results:
        print(f"check {result.name}: {'ok' if result.ok else 'FAILED'} - {result.detail}",
              file=out, flush=True)
    return all(result.ok for result in results)


def docker_bridge_gateway() -> str:
    """The gateway address of Docker's default ``bridge`` network.

    Containers reach the host at this address. Raises ConfigError when Docker
    cannot tell it.
    """
    try:
        answer = subprocess.run(
            ["docker", "network", "inspect", "bridge", "--format",
             "{{range .IPAM.Config}}{{.Gateway}} {{end}}"],
            capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ConfigError(f"cannot ask Docker for the bridge gateway: {exc}") from exc
    gateways = answer.stdout.split()
    if answer.returncode != 0 or not gateways:
        raise ConfigError("Docker reports no gateway for its bridge network "
                          f"({answer.stderr.strip()}); pass --meter-gateway")
    return gateways[0]


def start_meter(endpoint: Endpoint, out_dir: Path, run_id: str,
                stack: ExitStack) -> tuple[MeterProxy, MeterEndpoint, doctor.CheckResult]:
    """Start the metering proxy of a run and check that a container reaches it.

    The ledger is ``<out_dir>/meter/ledger.jsonl``. The proxy listens on
    ``meter_bind`` (default: the gateway address, so it is not exposed beyond
    the Docker host) and is stopped when ``stack`` closes.
    """
    gateway = endpoint.meter_gateway or docker_bridge_gateway()
    proxy = MeterProxy(upstream=endpoint.base_url, api_key_env=endpoint.api_key_env,
                       ledger=out_dir / "meter" / "ledger.jsonl",
                       host=endpoint.meter_bind or gateway, port=endpoint.meter_port)
    (out_dir / "meter").mkdir(parents=True, exist_ok=True)
    proxy.start()
    stack.callback(proxy.stop)
    check = doctor.check_meter_reachable(gateway, proxy.port, run_id=run_id)
    return proxy, proxy.endpoint(gateway), check


# ------------------------------------------------------------------ generation


def generate_tasks(config: RunConfig, method: Method, tasks: Sequence[TaskInput],
                   root: Path | None, *, out_dir: Path, run_id: str,
                   meter: MeterEndpoint | None, provenance: Provenance,
                   validate: bool) -> GenOutcome:
    """Package, generate, write back and (``validate``) anchor ``tasks``; see the module docstring.

    Writes ``packages/``, ``jobs/``, ``generation.jsonl``, ``tasks/`` and
    ``anchors/`` under ``out_dir``. A task that sniffing refuses or that could
    not be written back (:func:`check_writable`) is refused and not generated.
    An InfraError from generation is returned in the outcome with an
    ``infra_error`` row for every generated task.
    """
    oracles = {task.task_id: find_oracle(task.task_id, task.task_dir, config.oracle_root)
               for task in tasks}
    built = build_packages([task.task_dir for task in tasks], config.paradigm, method.profile,
                           out_dir / "packages", env=config.env, root=root,
                           switches=method.plan.switches, deliverable_dir=config.deliverable_dir,
                           replace_tests=config.replace_tests)
    refusal_errors = {row["task_id"]: RefusalError(row["reason"], row["message"])
                      for row in built.refused}
    by_id = {task.task_id: task for task in tasks}
    rows: dict[str, Mapping[str, Any]] = {}
    for row in built.rows:
        try:
            check_writable(by_id[row["task_id"]], oracles[row["task_id"]], method.anchor)
        except RefusalError as error:
            refusal_errors[row["task_id"]] = error
            continue
        rows[row["task_id"]] = row
    refused = {task_id: str(error.reason) for task_id, error in refusal_errors.items()}
    if not rows:
        return GenOutcome(results=[], refused=refused, refusal_errors=refusal_errors,
                          written={}, infra=None, task_infra={})

    try:
        generated = generate([Path(row["package_dir"]) for row in rows.values()], run_id=run_id,
                             jobs_dir=out_dir / "jobs", executor=config.executor,
                             model=config.model, provider=provider_block(config), meter=meter,
                             concurrency=config.concurrency, watchdog_sec=config.watchdog_sec,
                             exec_cap_sec=method.profile.agent_exec_cap_sec)
    except InfraError as error:
        results = [_infra_row(row, method, oracles[task_id] is not None, error, validate)
                   for task_id, row in rows.items()]
        return GenOutcome(results=results, refused=refused, refusal_errors=refusal_errors,
                          written={}, infra=error, task_infra={})
    _append_jsonl(out_dir / GENERATION_FILE, [_generation_json(item) for item in generated])
    task_infra = {item.task_id: InfraError(InfraCategory.ENV_BUILD_FAILED,
                                           f"task {item.task_id}: {item.env_error}")
                  for item in generated if item.env_error is not None}

    written: dict[str, WrittenTask] = {}
    for item in generated:
        if item.verifier_sh is None:
            continue
        row = rows[item.task_id]
        written[item.task_id] = write_back(
            by_id[item.task_id].task_dir, item.verifier_sh, out_dir / "tasks",
            settings=method.anchor, oracle_dir=oracles[item.task_id],
            environment_dir=(Path(row["package_dir"]) / "environment"
                             if method.anchor.image == "packaged" else None),
            provenance={"task_id": item.task_id, "run_id": run_id, "model": config.model,
                        "executor": config.executor, "profile": method.profile.name,
                        "paradigm": method.paradigm.name, "probe": item.probe,
                        "identity_sha256": row["identity_sha256"],
                        "harness": provenance.to_dict()})
    swaps, records = _anchor(list(written.values()), {task_id: oracles[task_id] for task_id in rows},
                             method.anchor, out_dir=out_dir, run_id=run_id,
                             concurrency=config.concurrency, validate=validate)
    results = [_gen_row(item, rows[item.task_id], method, written.get(item.task_id),
                        swaps.get(item.task_id), records.get(item.task_id, ()),
                        task_infra.get(item.task_id), metered=meter is not None,
                        validate=validate)
               for item in generated]
    return GenOutcome(results=results, refused=refused, refusal_errors=refusal_errors,
                      written=written, infra=None, task_infra=task_infra)


def _anchor(written: list[WrittenTask], pool: Mapping[str, Path | None],
            settings: AnchorEnvironment, *, out_dir: Path, run_id: str, concurrency: int,
            validate: bool) -> tuple[dict[str, Any], dict[str, tuple[AnchorRecord, ...]]]:
    """Plan the swaps over ``pool`` (every task of the run and its reference solution)
    and run the anchors of the written tasks."""
    if not validate or not written:
        return {}, {}
    swaps = plan_swaps(written, policy=settings.swap, pool=pool,
                       deliverables_subdir=settings.deliverables_subdir)
    records = run_anchors(written, swaps, settings=settings, jobs_dir=out_dir / "anchors",
                          run_id=run_id, concurrency=concurrency,
                          keep_images=settings.keep_images)
    by_task: dict[str, tuple[AnchorRecord, ...]] = {}
    for record in records:
        by_task[record.task] = (*by_task.get(record.task, ()), record)
    return swaps, by_task


def _gen_row(item: GenerationResult, row: Mapping[str, Any], method: Method,
             written: WrittenTask | None, swap: Any, records: Sequence[AnchorRecord],
             infra: InfraError | None, *, metered: bool, validate: bool) -> TaskResult:
    delivered = written is not None
    meter = item.usage.get("meter") if metered else None
    has_oracle = bool(written and written.oracle_dir is not None)
    label = label_task(records, delivered=delivered, has_oracle=has_oracle,
                       swap_constructible=swap is not None, infra=infra is not None,
                       anchors_run=validate)
    return TaskResult(
        task=item.task_id, paradigm=method.paradigm.name, profile=method.profile.name,
        identity_sha256=row["identity_sha256"], delivered=delivered, probe=item.probe,
        attempts=len(item.attempts),
        verifier_sha256=written.verifier_sha256 if written else None,
        has_oracle=has_oracle,
        swap_donor=swap.donor_task if swap is not None else None,
        swap_cross_type=swap.cross_type if swap is not None else None,
        anchors=tuple(records), label=label, usage=_tokens(item.usage),
        absorbed_429=meter["absorbed_429"] if meter is not None else None,
        contaminated_429=item.contaminated_429 if metered else None,
        dropped_task_config=row["dropped_task_config"],
        infra_error=None if infra is None else str(infra),
        anchors_run=validate, meter=meter)


def _infra_row(row: Mapping[str, Any], method: Method, has_oracle: bool, error: InfraError,
               validate: bool) -> TaskResult:
    return TaskResult(
        task=row["task_id"], paradigm=method.paradigm.name, profile=method.profile.name,
        identity_sha256=row["identity_sha256"], delivered=False, probe=None, attempts=0,
        verifier_sha256=None, has_oracle=has_oracle, swap_donor=None, swap_cross_type=None,
        anchors=(), label=TaskLabel.INFRA_ERROR,
        usage={"unavailable": "generation was stopped by an infrastructure error"},
        absorbed_429=None, contaminated_429=None, dropped_task_config=row["dropped_task_config"],
        infra_error=str(error), anchors_run=validate)


def _tokens(usage: Mapping[str, Any]) -> dict[str, Any]:
    """The token counts of a task's usage (:func:`~gavel_harness.run.usage.task_usage`),
    or its unavailability."""
    if "unavailable" in usage:
        return {"unavailable": usage["unavailable"]}
    tokens = {name: usage[name] for name in TOKEN_FIELDS}
    if isinstance(usage.get("cost_usd"), int | float):
        tokens["cost_usd"] = usage["cost_usd"]
    return tokens


def _generation_json(item: GenerationResult) -> dict[str, Any]:
    data = asdict(item)
    data["verifier_sh"] = None if item.verifier_sh is None else str(item.verifier_sh)
    return data


def remove_trial_images(jobs_dir: Path) -> dict[str, str]:
    """Remove the image Harbor built for every trial under ``jobs_dir``, by exact name.

    A trial is a directory with a ``config.json`` inside a job directory with
    one. Returns ``{image: outcome}`` with the outcomes of
    :func:`~gavel_harness.verify.anchors.remove_trial_image`; failures are
    reported there, never raised.
    """
    outcomes: dict[str, str] = {}
    if not jobs_dir.is_dir():
        return outcomes
    for trial in sorted(jobs_dir.glob("*/*")):
        if (trial / "config.json").is_file() and (trial.parent / "config.json").is_file():
            outcomes[trial_image_name(trial.name)] = remove_trial_image(trial.name)
    return outcomes


# ------------------------------------------------------------------- commands


class _Stage:
    """The step a run is in. An exception leaving the ``with`` block is recorded in
    ``run.json`` as the run's outcome (exit code, step, error) and propagates."""

    def __init__(self, run_json: Path) -> None:
        self.run_json = run_json
        self.name = "start"

    def __enter__(self) -> _Stage:
        return self

    def __exit__(self, kind: type[BaseException] | None, error: BaseException | None,
                 traceback: TracebackType | None) -> None:
        if error is None:
            return
        if isinstance(error, GavelError):
            code: int | None = int(error.exit_code)
        else:
            code = int(ExitCode.INTERNAL) if isinstance(error, Exception) else None
        update_run_json(self.run_json, outcome={
            "exit_code": code, "stage": self.name, "error": f"{type(error).__name__}: {error}"})


def run_gen(config: RunConfig, *, out: TextIO) -> ExitCode:
    """``gavel-harness gen``; see the module docstring. Returns the run's exit code."""
    method = resolve_method(profile=config.profile, env=config.env, paradigm=config.paradigm,
                            declare=config.declare, deliverable_dir=config.deliverable_dir,
                            verifier_network=config.verifier_network,
                            keep_images=config.keep_images)
    executor_spec(config.executor)
    check_input_paths(tasks_file=config.tasks_file, oracle_root=config.oracle_root)
    out_dir = config.out_dir
    run_id = resolve_run_id(config.run_id, out_dir)
    config = replace(config, run_id=run_id)
    run_json = _start_run(out_dir, config, method.anchor,
                          generation=_generation_settings(method))
    with _Stage(run_json) as stage:
        stage.name = "host_checks"
        checks = host_checks(allow_dirty=config.allow_dirty, network=method.anchor.network,
                             run_id=run_id, generation=True, endpoint=Endpoint.of(config),
                             judge_evidence=method.plan.judge_evidence,
                             rubric=method.plan.switches.rubric)
        update_run_json(run_json, checks=[check.to_dict() for check in checks])
        if not report_checks(checks, out):
            raise ConfigError("host checks failed; see run.json")

        stage.name = "intake"
        tasks, root = discover_tasks(config.inputs, tasks_file=config.tasks_file,
                                     registry=config.registry, sample=config.sample,
                                     seed=config.seed, cache_dir=out_dir / "_cache")
        update_run_json(run_json, tasks=[task.task_id for task in tasks])
        with ExitStack() as stack:
            endpoint = None
            if config.meter:
                stage.name = "meter"
                proxy, endpoint, check = start_meter(Endpoint.of(config), out_dir, run_id, stack)
                checks.append(check)
                update_run_json(run_json, checks=[c.to_dict() for c in checks],
                                meter={"gateway": endpoint.gateway, "port": endpoint.port,
                                       "upstream": proxy.upstream,
                                       "ledger": str(proxy.ledger_path)})
                if not report_checks([check], out):
                    raise ConfigError("the metering proxy is not reachable from a container")
            stage.name = "generation"
            outcome = generate_tasks(config, method, tasks, root, out_dir=out_dir,
                                     run_id=run_id, meter=endpoint,
                                     provenance=_provenance(run_json), validate=config.validate)
        stage.name = "report"
        return _finish(out_dir, run_json, outcome, keep_images=method.anchor.keep_images, out=out)


def run_validate(config: ValidateConfig, *, out: TextIO) -> ExitCode:
    """``gavel-harness validate --from-run``: the anchors on an upstream run's delivered verifiers.

    Swap donors are drawn from every task of the run with its reference
    solution, delivered or not; every reference solution found must hold a
    solve script.
    """
    profile = load_profile(config.profile)
    settings = anchor_settings(profile.anchor, config.verifier_network, config.keep_images)
    check_input_paths(oracle_root=config.oracle_root)
    out_dir = config.out_dir
    run_id = resolve_run_id(config.run_id, out_dir)
    config = replace(config, run_id=run_id)
    delivered = load_run(config.from_run)
    refused = load_refusals(config.from_run)
    run_json = _start_run(out_dir, config, settings)
    with _Stage(run_json) as stage:
        stage.name = "host_checks"
        checks = host_checks(allow_dirty=config.allow_dirty, network=settings.network,
                             run_id=run_id, generation=False)
        update_run_json(run_json, checks=[check.to_dict() for check in checks])
        if not report_checks(checks, out):
            raise ConfigError("host checks failed; see run.json")

        stage.name = "write_back"
        provenance = _provenance(run_json)
        oracles = {item.task_id: find_oracle(item.task_id, item.source_task, config.oracle_root)
                   for item in delivered}
        for task_id, oracle in oracles.items():
            try:
                check_solution(oracle)
            except ConfigError as exc:
                raise ConfigError(f"task {task_id}: {exc}") from exc
        written: dict[str, WrittenTask] = {}
        for item in delivered:
            verifier = item.verifier_sh
            if verifier is None or verifier.stat().st_size == 0:
                continue
            oracle = oracles[item.task_id]
            check_writable(TaskInput(item.task_id, item.source_task), oracle, settings)
            written[item.task_id] = write_back(
                item.source_task, verifier, out_dir / "tasks", settings=settings,
                oracle_dir=oracle,
                environment_dir=(_packaged_environment(item.task_id, item.attempts)
                                 if settings.image == "packaged" else None),
                provenance={"task_id": item.task_id, "run_id": run_id,
                            "from_run": str(config.from_run), "verifier_source": str(verifier),
                            "profile": profile.name, "probe": item.probe,
                            "harness": provenance.to_dict()})
        stage.name = "anchors"
        swaps, records = _anchor(list(written.values()), oracles, settings, out_dir=out_dir,
                                 run_id=run_id, concurrency=config.concurrency, validate=True)
        stage.name = "report"
        results = []
        for item in delivered:
            task = written.get(item.task_id)
            failure = None if task is not None else attempt_failure(item.attempts)
            swap = swaps.get(item.task_id)
            anchors = records.get(item.task_id, ())
            has_oracle = bool(task and task.oracle_dir is not None)
            results.append(TaskResult(
                task=item.task_id, paradigm=profile.paradigm, profile=profile.name,
                identity_sha256=None, delivered=task is not None, probe=item.probe,
                attempts=len(item.attempts),
                verifier_sha256=task.verifier_sha256 if task else None, has_oracle=has_oracle,
                swap_donor=swap.donor_task if swap else None,
                swap_cross_type=swap.cross_type if swap else None, anchors=anchors,
                label=label_task(anchors, delivered=task is not None, has_oracle=has_oracle,
                                 swap_constructible=swap is not None,
                                 infra=failure is not None),
                usage=_tokens(task_usage(item.attempts, None)), absorbed_429=None,
                contaminated_429=True if rate_limited(item.attempts) else None,
                dropped_task_config=sniff(item.source_task, strip_tests=True,
                                          allow_compose=True, allow_mcp_servers=True,
                                          allow_missing_gpus=True).dropped_task_config,
                infra_error=None if failure is None else str(failure)))
        outcome = GenOutcome(results=results, refused=refused, refusal_errors={},
                             written=written, infra=None, task_infra={})
        return _finish(out_dir, run_json, outcome, keep_images=settings.keep_images, out=out)


def run_matrix(config: MatrixConfig, *, out: TextIO) -> ExitCode:
    """``gavel-harness matrix``: sample every family, run ``gen --validate`` on each sampled task.

    A task-level failure (a refusal, an infrastructure failure of the task) is
    that task's row; the matrix goes on with the next task.
    """
    run = replace(config.run, validate=True)
    method = resolve_method(profile=run.profile, env=run.env, paradigm=run.paradigm,
                            declare=run.declare, deliverable_dir=run.deliverable_dir,
                            verifier_network=run.verifier_network, keep_images=run.keep_images)
    executor_spec(run.executor)
    check_input_paths(oracle_root=run.oracle_root)
    out_dir = run.out_dir
    run_id = resolve_run_id(run.run_id, out_dir)
    run = replace(run, run_id=run_id)
    config = replace(config, run=run)
    registry = registry_fetch.load_registry(config.registry)
    families = registry_fetch.families(registry)
    if config.families:
        unknown = sorted(set(config.families) - {family.name for family in families})
        if unknown:
            raise ConfigError(f"registry {config.registry} has no families {unknown}")
        families = tuple(family for family in families if family.name in config.families)
    samples = [registry_fetch.sample(family, config.per_family, config.seed)
               for family in families]
    run_json = _start_run(out_dir, config, method.anchor,
                          generation=_generation_settings(method),
                          registry_sha256=registry.sha256)
    with _Stage(run_json) as stage:
        stage.name = "host_checks"
        checks = host_checks(allow_dirty=run.allow_dirty, network=method.anchor.network,
                             run_id=run_id, generation=True, endpoint=Endpoint.of(run),
                             judge_evidence=method.plan.judge_evidence,
                             rubric=method.plan.switches.rubric)
        update_run_json(run_json, checks=[check.to_dict() for check in checks])
        if not report_checks(checks, out):
            raise ConfigError("host checks failed; see run.json")
        provenance = _provenance(run_json)
        pin_ok = any(check.name == "harbor_pin" and check.ok for check in checks)
        identity = RunIdentity(model=run.model, executor=run.executor,
                               harness_commit=provenance.commit, harness_dirty=provenance.dirty,
                               harbor_version=provenance.harbor_version,
                               harbor_commit=(doctor.HARBOR_PIN.commit if pin_ok
                                              else provenance.harbor_commit))
        images: dict[str, str] = {}
        with ExitStack() as stack:
            endpoint = None
            if run.meter:
                stage.name = "meter"
                _, endpoint, check = start_meter(Endpoint.of(run), out_dir, run_id, stack)
                if not report_checks([check], out):
                    raise ConfigError("the metering proxy is not reachable from a container")
            stage.name = "tasks"
            for drawn in samples:
                for task in drawn.tasks:
                    row, removed = _matrix_row(run, method, task, identity, out_dir=out_dir,
                                               run_id=run_id, meter=endpoint,
                                               provenance=provenance)
                    append_row(out_dir, row)
                    images.update(removed)
                    print(f"matrix {task.family}/{task.name}: {row.outcome}", file=out)
                    for name, state in sorted(removed.items()):
                        if state.startswith("error"):
                            print(f"warning: image {name} was not removed: {state}", file=out)
                    write_matrix(out_dir, registry=registry, seed=config.seed, samples=samples,
                                 rows=read_rows(out_dir))
        stage.name = "report"
        rows = read_rows(out_dir)
        code = _matrix_exit(rows)
        write_matrix(out_dir, registry=registry, seed=config.seed, samples=samples, rows=rows)
        update_run_json(run_json, outcome={"exit_code": int(code), "rows": len(rows),
                                           "images": images})
        return code


def _matrix_row(run: RunConfig, method: Method, task: registry_fetch.RegistryTask,
                identity: RunIdentity, *, out_dir: Path, run_id: str,
                meter: MeterEndpoint | None,
                provenance: Provenance) -> tuple[MatrixRow, dict[str, str]]:
    """The matrix row of one sampled task, and the outcomes of its image removals."""
    try:
        fetched = registry_fetch.fetch_task(task, out_dir / "_cache")
    except RefusalError as error:
        return MatrixRow.refused(task, identity, error), {}
    except InfraError as error:
        return MatrixRow.infra(task, identity, error), {}
    digest = hashlib.sha256(f"{task.git_url}\n{task.commit}\n{task.path}".encode()).hexdigest()
    name = slug(f"{task.family}--{task.name}").strip("-")[:80]
    task_out = out_dir / "runs" / f"{name}-{digest[:8]}"
    task_out.mkdir(parents=True)
    task_input = TaskInput(task_id=fetched.task_dir.name, task_dir=fetched.task_dir)
    outcome = generate_tasks(run, method, [task_input], None, out_dir=task_out, run_id=run_id,
                             meter=meter, provenance=provenance, validate=True)
    if outcome.refusal_errors:
        return MatrixRow.refused(task, identity, outcome.refusal_errors[task_input.task_id]), {}
    (result,) = outcome.results
    write_report(outcome.results, task_out, task_dirs={
        task_id: written.task_dir for task_id, written in outcome.written.items()})
    images = {} if method.anchor.keep_images else remove_trial_images(task_out / "jobs")
    error = outcome.infra or outcome.task_infra.get(result.task)
    if error is not None:
        return MatrixRow.infra(task, identity, error, paradigm=result.paradigm,
                               identity_sha256=result.identity_sha256), images
    if result.identity_sha256 is None:
        raise ConfigError(f"{task.family}/{task.name}: the generated task has no package "
                          "identity")
    return MatrixRow.result(task, identity, paradigm=result.paradigm,
                            identity_sha256=result.identity_sha256, label=result.label,
                            records=result.anchors), images


def _matrix_exit(rows: Sequence[MatrixRow]) -> ExitCode:
    if any(row.no_result is not None for row in rows):
        return ExitCode.INFRA
    if not rows or any(row.refusal is not None for row in rows):
        return ExitCode.CONFIG
    if any(row.label not in SUCCESS_LABELS for row in rows):
        return ExitCode.NOT_VALIDATED
    return ExitCode.OK


def rerender(out_dir: Path) -> tuple[str, ExitCode]:
    """The summary and exit code of a finished run, from its ``results.jsonl`` (read only)."""
    results_path = out_dir / RESULTS_FILE
    if not results_path.is_file():
        raise ConfigError(f"{out_dir} has no {RESULTS_FILE}; not a finished run directory")
    rows = read_results(results_path)
    refused_path = out_dir / REFUSED_FILE
    refused: Any = {}
    if refused_path.is_file():
        try:
            refused = json.loads(refused_path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ConfigError(f"{refused_path} is not valid JSON: {exc}") from exc
    if not isinstance(refused, dict) or not all(
            isinstance(reason, str) for reason in refused.values()):
        raise ConfigError(f"{refused_path}: expected a JSON object of task id -> reason")
    return render_summary(rows, refused=refused), exit_code(rows, refused=len(refused))


# ------------------------------------------------------------------- helpers


def _start_run(out_dir: Path, config: RunConfig | ValidateConfig | MatrixConfig,
               anchor: AnchorEnvironment, **sections: Any) -> Path:
    """Create the run directory, which must be new or empty, and write ``run.json``."""
    if out_dir.exists() and (not out_dir.is_dir() or any(out_dir.iterdir())):
        raise ConfigError(f"{out_dir} is not empty; choose a fresh output directory")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / RUN_FILE
    endpoint: dict[str, Any] = {}
    run = config.run if isinstance(config, MatrixConfig) else config
    if isinstance(run, RunConfig):
        endpoint = {"api_key_env": run.api_key_env, "provider": provider_block(run)}
    write_run_json(path, config, collect_provenance(), run_id=run.run_id,
                   anchor=asdict(anchor), endpoint=endpoint or None, **sections)
    return path


def _generation_settings(method: Method) -> dict[str, Any]:
    """The ``generation`` section of ``run.json``: the prompt wording and the exec cap."""
    return {"wording": method.plan.wording,
            "agent_exec_cap_sec": method.profile.agent_exec_cap_sec}


def _provenance(run_json: Path) -> Provenance:
    data = json.loads(run_json.read_text(encoding="utf-8"))["provenance"]
    return Provenance(**data)


def _packaged_environment(task_id: str, attempts: Sequence[Mapping[str, Any]]) -> Path:
    shipped = [attempt for attempt in attempts if attempt.get("shipped")] or list(attempts)
    snapshot = shipped[0].get("input_snapshot") or {}
    package_dir = snapshot.get("package_dir") if isinstance(snapshot, Mapping) else None
    environment = Path(package_dir) / "environment" if package_dir else None
    if environment is None or not environment.is_dir():
        raise ConfigError(f"task {task_id}: the anchors run in the packaged image, but the run "
                          "records no package environment for the shipped attempt")
    return environment


def _append_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("a", encoding="utf-8") as sink:
        for row in rows:
            sink.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _finish(out_dir: Path, run_json: Path, outcome: GenOutcome, *, keep_images: bool,
            out: TextIO) -> ExitCode:
    for task_id, error in sorted(outcome.refusal_errors.items()):
        print(f"refused {task_id}: {error}", file=out)
    (out_dir / REFUSED_FILE).write_text(json.dumps(outcome.refused, indent=1, sort_keys=True)
                                        + "\n", encoding="utf-8")
    code = write_report(outcome.results, out_dir, refused=outcome.refused, task_dirs={
        task_id: written.task_dir for task_id, written in outcome.written.items()})
    images = {} if keep_images else remove_trial_images(out_dir / "jobs")
    failed_removals = {name: state for name, state in images.items()
                       if state.startswith("error")}
    labels: dict[str, int] = {}
    for result in outcome.results:
        labels[str(result.label)] = labels.get(str(result.label), 0) + 1
    update_run_json(run_json, outcome={
        "exit_code": int(code), "labels": labels, "refused": len(outcome.refused),
        "infra_error": None if outcome.infra is None else str(outcome.infra),
        "keep_images": keep_images, "images": images})
    if outcome.infra is not None:
        print(f"infrastructure error stopped the run: {outcome.infra}", file=out)
    for task_id, error in sorted(outcome.task_infra.items()):
        print(f"infrastructure error in task {task_id}: {error}", file=out)
    for name, state in sorted(failed_removals.items()):
        print(f"warning: image {name} was not removed: {state}", file=out)
    counts = ", ".join(f"{label} {count}" for label, count in sorted(labels.items()))
    print(f"{len(outcome.results)} task(s) with a result ({counts or 'none'}), "
          f"{len(outcome.refused)} refused; {out_dir / SUMMARY_FILE}; exit code {int(code)}",
          file=out)
    return code
