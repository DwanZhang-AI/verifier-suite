"""Command-line entry point ``gavel-harness``.

Commands: ``doctor`` (host checks), ``gen`` (generate, write back and
optionally validate verifiers), ``validate --from-run`` (the anchors on the
verifiers of an earlier upstream run), ``matrix`` (support matrix over registry
families) and ``report`` (re-render a finished run's summary). The runs
themselves are in :mod:`gavel_harness.pipeline`.

Harbor's anonymous usage telemetry is switched off (``HARBOR_TELEMETRY=0``)
unless the environment already sets the variable.

Every failure ends in an exit code (:class:`gavel_harness.errors.ExitCode`): a
reported failure in its own code, any other exception in ``INTERNAL`` with its
traceback on stderr, so a crash never reads as a finished run.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import tempfile
import traceback
from collections.abc import Callable, Sequence
from contextlib import ExitStack
from pathlib import Path

from . import __version__
from .config import (
    DEFAULT_METER_PORT,
    PARADIGMS,
    VERIFIER_NETWORK_MODES,
    MatrixConfig,
    RunConfig,
    ValidateConfig,
)
from .errors import ConfigError, ExitCode, GavelError
from .run.executors import executor_names

Handler = Callable[[argparse.Namespace], int]

TELEMETRY_ENV = "HARBOR_TELEMETRY"


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _add_endpoint_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group(
        "model endpoint and executor",
        "gen and matrix require --model, --base-url and --api-key-env; doctor checks the "
        "endpoint when they are given")
    group.add_argument("--model", help="<provider id>/<model id>, e.g. openai/gpt-5")
    group.add_argument("--base-url", help="endpoint base URL, e.g. https://api.example.com/v1")
    group.add_argument(
        "--api-key-env", metavar="NAME",
        help="name of the environment variable that holds the API key (never the key itself)")
    group.add_argument("--executor", default="opencode", choices=executor_names(),
                       help="agent executor that writes the verifier (default: opencode)")


def _add_meter_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("metering proxy")
    group.add_argument(
        "--no-meter", dest="meter", action="store_false",
        help="send model requests directly to the endpoint: no per-trial token ledger, no 429 "
        "handling, and the key is passed into the containers")
    group.add_argument("--meter-port", type=int, default=DEFAULT_METER_PORT,
                       help=f"port of the metering proxy (default: {DEFAULT_METER_PORT})")
    group.add_argument("--meter-gateway", metavar="HOST",
                       help="address containers reach the host at (default: the Docker bridge "
                       "gateway)")
    group.add_argument("--meter-bind", metavar="HOST",
                       help="address the proxy listens on (default: the gateway address)")


def _add_verifier_network_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--verifier-network",
        choices=VERIFIER_NETWORK_MODES,
        help="network policy of the verification phase (default: the profile's anchor "
        "network, no-network unless the profile declares otherwise)",
    )


def _add_method_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("method")
    group.add_argument(
        "--profile", default="paper/generic", help="benchmark profile (default: paper/generic)"
    )
    group.add_argument(
        "--env",
        help="environment profile for package Dockerfiles (default: the profile's env, "
        "plain for every shipped profile)",
    )
    group.add_argument("--paradigm", choices=PARADIGMS, help="force one paradigm for every input")
    group.add_argument(
        "--declare",
        action="store_true",
        help="ask the agent to declare checked and unchecked requirements (default: off; "
        "refused by this build, which does not collect the declaration)",
    )
    group.add_argument(
        "--deliverable-dir",
        metavar="CONTAINER_PATH",
        help="absolute in-container directory that holds a deliverable task's output",
    )
    _add_verifier_network_arg(parser)


def _add_run_args(parser: argparse.ArgumentParser) -> argparse._ArgumentGroup:
    run = parser.add_argument_group("run")
    run.add_argument("--out", required=True, type=_path, help="output directory of this run")
    run.add_argument("--concurrency", type=int, default=4,
                     help="concurrent trials (default: 4)")
    run.add_argument("--run-id", help="run id labelling containers and jobs "
                     "(default: the output directory name and a random suffix)")
    run.add_argument("--keep-images", action=argparse.BooleanOptionalAction,
                     help="keep (or remove) the images Harbor built for this run's trials "
                     "(default: the profile's [anchor] keep_images)")
    run.add_argument("--allow-dirty", action="store_true",
                     help="accept a checkout with uncommitted changes")
    run.add_argument("--watchdog-sec", type=int, default=1200,
                     help="cancel a generation job after this long without progress (default: "
                     "1200)")
    return run


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gavel-harness",
        description="Generate, write back and validate closed-book verifiers for Harbor tasks.",
    )
    parser.add_argument("--version", action="version", version=f"gavel-harness {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    doctor = sub.add_parser("doctor", help="check that this host can run gavel-harness gen")
    _add_endpoint_args(doctor)
    doctor.add_argument("--profile", default="paper/generic", help="benchmark profile to check")
    _add_verifier_network_arg(doctor)
    _add_meter_args(doctor)
    doctor.add_argument(
        "--allow-dirty", action="store_true", help="accept a checkout with uncommitted changes"
    )
    doctor.set_defaults(handler=_doctor)

    gen = sub.add_parser("gen", help="generate verifiers for tasks and write them back")
    gen.add_argument(
        "inputs",
        nargs="+",
        metavar="INPUT",
        help="task directory, directory of tasks, or registry:<dataset>@<commit>",
    )
    _add_endpoint_args(gen)
    _add_method_args(gen)
    run = _add_run_args(gen)
    run.add_argument(
        "--validate", action="store_true", help="run the null/oracle/swap anchors after write-back"
    )
    run.add_argument("--tasks-file", type=_path, help="file listing the task IDs to run")
    run.add_argument(
        "--oracle-root", type=_path,
        help="directory of reference solutions kept outside the tasks (<root>/<id>/solution)"
    )
    run.add_argument(
        "--replace-tests", action="store_true", help="accept input tasks that already ship tests/"
    )
    run.add_argument("--registry", help="registry.json path or URL for registry: inputs")
    run.add_argument("--sample", type=int, metavar="K",
                     help="tasks drawn from each registry: input (default: all)")
    run.add_argument("--seed", type=int, default=0, help="sampling seed (default: 0)")
    _add_meter_args(gen)
    gen.set_defaults(handler=_gen)

    validate = sub.add_parser(
        "validate", help="run the three anchors on the verifiers of an earlier run")
    validate.add_argument(
        "--from-run",
        required=True,
        type=_path,
        metavar="RUN_DIR",
        help="run directory of the upstream one-command driver; only read",
    )
    validate.add_argument("--profile", required=True,
                          help="benchmark profile giving the paradigm and anchor environment")
    validate.add_argument(
        "--oracle-root", type=_path,
        help="directory of reference solutions kept outside the tasks (<root>/<id>/solution)"
    )
    validate.add_argument(
        "--out", required=True, type=_path, help="output directory for anchor results"
    )
    validate.add_argument(
        "--concurrency", type=int, default=4, help="tasks validated at once (default: 4)"
    )
    validate.add_argument("--keep-images", action=argparse.BooleanOptionalAction,
                          help="keep (or remove) the images built for the anchors "
                          "(default: the profile's [anchor] keep_images)")
    validate.add_argument("--run-id", help="run id labelling containers and jobs")
    validate.add_argument(
        "--allow-dirty", action="store_true", help="accept a checkout with uncommitted changes"
    )
    _add_verifier_network_arg(validate)
    validate.set_defaults(handler=_validate)

    matrix = sub.add_parser("matrix", help="build the support matrix over registry families")
    matrix.add_argument("--registry", required=True, help="registry.json path or URL")
    matrix.add_argument(
        "--per-family", required=True, type=int, metavar="N", help="tasks sampled per family"
    )
    matrix.add_argument("--seed", required=True, type=int, help="sampling seed")
    matrix.add_argument("--family", action="append", default=[], metavar="NAME",
                        help="restrict the matrix to this family (repeatable)")
    _add_endpoint_args(matrix)
    _add_method_args(matrix)
    _add_run_args(matrix)
    _add_meter_args(matrix)
    matrix.set_defaults(handler=_matrix)

    report = sub.add_parser("report", help="print the summary of a finished run")
    report.add_argument("run_dir", type=_path, metavar="RUN_DIR", help="output directory of a run")
    report.set_defaults(handler=_report)

    return parser


def _endpoint(args: argparse.Namespace) -> tuple[str, str, str]:
    """``(model, base URL, key variable)`` from the endpoint arguments.

    Raises ConfigError when one of them is not given.
    """
    if args.model is None or args.base_url is None or args.api_key_env is None:
        raise ConfigError("--model, --base-url and --api-key-env are required")
    return args.model, args.base_url, args.api_key_env


def _run_config(args: argparse.Namespace, inputs: tuple[str, ...], **extra: object) -> RunConfig:
    model, base_url, key_env = _endpoint(args)
    return RunConfig(
        inputs=inputs, model=model, base_url=base_url, api_key_env=key_env, out_dir=args.out,
        executor=args.executor, profile=args.profile, env=args.env, paradigm=args.paradigm,
        concurrency=args.concurrency, declare=args.declare,
        verifier_network=args.verifier_network, deliverable_dir=args.deliverable_dir,
        allow_dirty=args.allow_dirty, run_id=args.run_id, meter=args.meter,
        meter_port=args.meter_port, meter_gateway=args.meter_gateway,
        meter_bind=args.meter_bind, keep_images=args.keep_images,
        watchdog_sec=args.watchdog_sec, **extra,  # type: ignore[arg-type]
    )


def _gen(args: argparse.Namespace) -> int:
    from .pipeline import run_gen

    config = _run_config(
        args, tuple(args.inputs), validate=args.validate, tasks_file=args.tasks_file,
        oracle_root=args.oracle_root, replace_tests=args.replace_tests,
        registry=args.registry, sample=args.sample, seed=args.seed)
    return run_gen(config, out=sys.stdout)


def _validate(args: argparse.Namespace) -> int:
    from .pipeline import run_validate

    config = ValidateConfig(
        from_run=args.from_run, profile=args.profile, out_dir=args.out,
        oracle_root=args.oracle_root, concurrency=args.concurrency,
        keep_images=args.keep_images, verifier_network=args.verifier_network,
        run_id=args.run_id, allow_dirty=args.allow_dirty)
    return run_validate(config, out=sys.stdout)


def _matrix(args: argparse.Namespace) -> int:
    from .pipeline import run_matrix

    config = MatrixConfig(registry=args.registry, per_family=args.per_family, seed=args.seed,
                          run=_run_config(args, (args.registry,), validate=True),
                          families=tuple(args.family))
    return run_matrix(config, out=sys.stdout)


def _doctor(args: argparse.Namespace) -> int:
    from . import pipeline

    method = pipeline.resolve_method(profile=args.profile, env=None, paradigm=None,
                                     declare=False, deliverable_dir=None,
                                     verifier_network=args.verifier_network)
    endpoint = None
    if args.model or args.base_url or args.api_key_env:
        model, base_url, key_env = _endpoint(args)
        endpoint = pipeline.Endpoint(
            model=model, base_url=base_url, api_key_env=key_env, executor=args.executor,
            meter=args.meter, meter_port=args.meter_port, meter_gateway=args.meter_gateway,
            meter_bind=args.meter_bind)
    run_id = pipeline.resolve_run_id(None, Path("doctor"))
    checks = pipeline.host_checks(allow_dirty=args.allow_dirty, network=method.anchor.network,
                                  run_id=run_id, generation=True, endpoint=endpoint,
                                  judge_evidence=method.plan.judge_evidence,
                                  rubric=method.plan.switches.rubric)
    ok = pipeline.report_checks(checks, sys.stdout)
    if ok and endpoint is not None and endpoint.meter:
        with tempfile.TemporaryDirectory(prefix="veritas-doctor-") as scratch, \
                ExitStack() as stack:
            _, _, check = pipeline.start_meter(endpoint, Path(scratch), run_id, stack)
        ok = pipeline.report_checks([check], sys.stdout)
    return ExitCode.OK if ok else ExitCode.CONFIG


def _report(args: argparse.Namespace) -> int:
    from .pipeline import rerender

    text, code = rerender(args.run_dir)
    sys.stdout.write(text)
    return code


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help(sys.stderr)
        return ExitCode.CONFIG
    os.environ.setdefault(TELEMETRY_ENV, "0")
    logger = logging.getLogger("gavel_harness")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(asctime)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    command: Handler = args.handler
    try:
        return command(args)
    except GavelError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # noqa: BLE001 - reported with its traceback, never swallowed
        traceback.print_exc(file=sys.stderr)
        print(f"internal error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return ExitCode.INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
