"""Exception hierarchy and process exit codes.

Every failure the harness can report maps to exactly one exit code. When one run
produces several outcomes, the process exits with the highest code
(INFRA > CONFIG > NOT_VALIDATED > OK). INTERNAL is the exit code of an
exception the harness did not expect (a bug or an unhandled operating-system
error); it is never derived from task outcomes.
"""

from __future__ import annotations

from enum import IntEnum, StrEnum


class ExitCode(IntEnum):
    """Process exit codes of the ``gavel-harness`` command."""

    OK = 0
    """Every task reached the ``validated`` label."""
    NOT_VALIDATED = 1
    """At least one task finished without reaching ``validated``."""
    CONFIG = 2
    """Configuration error, a failed host check, or a refused task."""
    INFRA = 3
    """An infrastructure error hit the run; results are incomplete and the affected tasks
    are re-run."""
    INTERNAL = 4
    """The harness failed with an unexpected exception; results are incomplete."""


class RefusalReason(StrEnum):
    """Why an input task is outside the supported paradigms. Written to ``refused.jsonl``."""

    COMPOSE = "compose"
    """A compose file sits in the task root or in ``environment/``."""
    MULTI_STEP = "multi_step"
    """task.toml declares ``[[steps]]``."""
    MCP_SERVERS = "mcp_servers"
    """task.toml declares MCP servers."""
    REMOTE_ENV = "remote_env"
    """The environment type is a remote provider."""
    NO_INSTRUCTION = "no_instruction"
    """The task has no instruction."""
    NO_ENVIRONMENT = "no_environment"
    """The task has neither a Dockerfile nor a ``docker_image``."""
    TOML_ERROR = "toml_error"
    """task.toml does not parse."""
    GPU_UNAVAILABLE = "gpu_unavailable"
    """The task needs a GPU and the host has none."""
    WINDOWS = "windows"
    """The task needs a Windows container."""
    HAS_TESTS = "has_tests"
    """The task already ships ``tests/`` and the profile does not strip them."""
    NOT_WRITABLE = "not_writable"
    """The generated verifier could not be written back into the task: its id is not a
    relative path of plain names, its task.toml does not merge, or its reference
    solution has no solve script."""
    LFS_CONTENT = "lfs_content"
    """A registry task stores files in Git LFS; the fetch does not retrieve LFS objects."""
    ESCAPING_SYMLINK = "escaping_symlink"
    """A symlink under ``environment/`` points outside it (or cannot be resolved);
    copying the environment would follow it and bring outside files, such as the
    reference solution, into the generation package."""


class InfraCategory(StrEnum):
    """Infrastructure failure classes. None of them is a capability outcome."""

    DOCKER_UNAVAILABLE = "docker_unavailable"
    """The Docker daemon cannot be reached."""
    ENDPOINT_UNAVAILABLE = "endpoint_unavailable"
    """The model endpoint does not answer."""
    METER_UNAVAILABLE = "meter_unavailable"
    """The host-side metering proxy is down."""
    STALLED = "stalled"
    """A job made no progress within the watchdog window."""
    HARBOR_INTERNAL = "harbor_internal"
    """Harbor raised an exception outside any trial."""
    RATE_LIMITED = "rate_limited"
    """A trial stayed rate-limited after its rerun budget was spent."""
    ENV_IMAGE_DRIFT = "env_image_drift"
    """The environment image content changed between anchors of the same task."""
    ENV_BUILD_FAILED = "env_build_failed"
    """A task's environment image could not be built or its container not started."""
    FETCH_FAILED = "fetch_failed"
    """A registry or a task repository could not be fetched (network or git failure)."""


class GavelError(Exception):
    """Base class for every failure the harness reports."""

    exit_code: ExitCode = ExitCode.CONFIG


class ConfigError(GavelError):
    """The run configuration or the host environment is unusable as given."""

    exit_code = ExitCode.CONFIG


class RefusalError(GavelError):
    """An input task is outside the supported paradigms.

    ``reason`` is the machine-readable code; the message explains the case.
    """

    exit_code = ExitCode.CONFIG

    def __init__(self, reason: RefusalReason | str, message: str) -> None:
        self.reason = RefusalReason(reason)
        super().__init__(f"[{self.reason}] {message}")


class InfraError(GavelError):
    """An infrastructure failure; the affected result is not a capability outcome.

    ``category`` is the machine-readable class; the message carries the detail.
    """

    exit_code = ExitCode.INFRA

    def __init__(self, category: InfraCategory | str, message: str) -> None:
        self.category = InfraCategory(category)
        super().__init__(f"[{self.category}] {message}")
