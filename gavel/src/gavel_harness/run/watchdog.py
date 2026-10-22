"""Stall and health watchdog of one running Harbor job.

A :class:`Watchdog` thread looks at the job every ``interval_sec`` and cancels it
(through the ``cancel`` callback) the first time one of these holds:

* **stall**: for ``stall_sec``, no file or directory under the job's own trial
  directories got a newer mtime and, at every look, the ``busy`` probe reported
  no work Harbor is waiting on. The default probe,
  :func:`docker_children_running`, asks whether this process has a live
  ``docker`` child: an image build, which writes nothing into the trial
  directory, or a command execution such as an agent waiting out rate limits.
  Each of those is bounded by its own Harbor timeout; a scheduler deadlock
  leaves neither file progress nor a docker child.
* **check**: one of the ``checks`` returns a :class:`Trip`. Checks report
  infrastructure failures that make the rest of the job meaningless, e.g. an
  unreachable Docker daemon.

Nothing outside the job directory and this process's children is looked at, so
other jobs on the host can neither mask nor cause a stall. The caller turns
:attr:`Watchdog.trip` into an :class:`~gavel_harness.errors.InfraError`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ..errors import ConfigError, InfraCategory, InfraError

DEFAULT_INTERVAL_SEC = 30.0
DOCKER_INFO_TIMEOUT_SEC = 60.0
DOCKER_FAILURES_TO_TRIP = 3
"""Consecutive failed daemon probes that count as an unreachable daemon."""


@dataclass(frozen=True)
class Trip:
    """Why a watchdog cancelled a job."""

    category: InfraCategory
    message: str


Check = Callable[[], Trip | None]
"""A health check: a Trip when the job must stop, else None. Called from the watchdog thread."""


def latest_progress(job_dir: Path) -> float:
    """The newest mtime of any entry under the trial directories of ``job_dir``.

    Trial directories are the subdirectories of ``job_dir``; files directly in
    ``job_dir`` (Harbor's own job log and result) do not count. Returns 0.0 for
    a job without trial directories. Entries that vanish while being read are
    skipped.
    """
    newest = 0.0
    if not job_dir.is_dir():
        return newest
    for trial in job_dir.iterdir():
        if not trial.is_dir() or trial.is_symlink():
            continue
        for directory, dirs, files in os.walk(trial):
            for name in (directory, *(os.path.join(directory, n) for n in dirs + files)):
                try:
                    newest = max(newest, os.lstat(name).st_mtime)
                except FileNotFoundError:
                    continue
    return newest


def docker_children_running() -> bool:
    """Whether this process has a live child process named ``docker``.

    Harbor runs every image build and container command as a ``docker`` child
    of the process that runs the job. Raises OSError when ``pgrep`` fails.
    """
    result = subprocess.run(["pgrep", "-P", str(os.getpid()), "-x", "docker"],
                            capture_output=True, text=True, timeout=60)
    if result.returncode in (0, 1):
        return result.returncode == 0
    raise OSError(f"pgrep exited {result.returncode}: {result.stderr.strip()}")


class DockerDaemonCheck:
    """Trips with DOCKER_UNAVAILABLE after ``failures`` consecutive failed ``docker info`` calls."""

    def __init__(self, failures: int = DOCKER_FAILURES_TO_TRIP) -> None:
        if failures < 1:
            raise ValueError("failures must be at least 1")
        self._failures = failures
        self._streak = 0

    def __call__(self) -> Trip | None:
        problem = docker_daemon_problem()
        if problem is None:
            self._streak = 0
            return None
        self._streak += 1
        if self._streak < self._failures:
            return None
        return Trip(InfraCategory.DOCKER_UNAVAILABLE,
                    f"the Docker daemon failed {self._streak} probes in a row: {problem}")


def docker_daemon_problem() -> str | None:
    """None when ``docker info`` answers, else why it did not."""
    try:
        result = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"],
                                capture_output=True, text=True, timeout=DOCKER_INFO_TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        return f"docker info did not answer within {DOCKER_INFO_TIMEOUT_SEC:.0f} s"
    except FileNotFoundError:
        return "the docker CLI is not installed"
    if result.returncode != 0:
        return f"docker info exited {result.returncode}: {result.stderr.strip()[:500]}"
    return None


class Watchdog:
    """Cancels a running job that stalls or fails a health check; see the module docstring.

    ``cancel`` is called at most once, from the watchdog thread, and :attr:`trip`
    then says why; it stays None while the watchdog has not cancelled the job. A
    probe or check that raises trips the watchdog: with the category of an
    InfraError, else with HARBOR_INTERNAL; a job that cannot be watched is not
    left running.
    """

    def __init__(self, job_dir: Path, *, stall_sec: float, cancel: Callable[[], None],
                 checks: Sequence[Check] = (), interval_sec: float = DEFAULT_INTERVAL_SEC,
                 busy: Callable[[], bool] = docker_children_running) -> None:
        if stall_sec <= 0 or interval_sec <= 0:
            raise ConfigError("watchdog stall_sec and interval_sec must be positive")
        if busy is docker_children_running and shutil.which("pgrep") is None:
            raise ConfigError("the stall watchdog needs pgrep on PATH")
        self._job_dir = Path(job_dir)
        self._stall_sec = stall_sec
        self._interval = interval_sec
        self._cancel = cancel
        self._checks = tuple(checks)
        self._busy = busy
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._watch, name="veritas-watchdog",
                                        daemon=True)
        self._seen = 0.0
        self._last_progress = 0.0
        self.trip: Trip | None = None

    def start(self) -> None:
        """Start watching; the stall clock starts now."""
        self._thread.start()

    def stop(self) -> None:
        """Stop watching and wait for the thread to end."""
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join()

    def _watch(self) -> None:
        trip = self._guarded(self._begin)
        while trip is None and not self._stop.wait(self._interval):
            trip = self._guarded(self._look)
        if trip is not None:
            self.trip = trip
            self._cancel()

    @staticmethod
    def _guarded(step: Callable[[], Trip | None]) -> Trip | None:
        try:
            return step()
        except InfraError as exc:
            return Trip(exc.category, str(exc))
        except Exception as exc:  # noqa: BLE001 - becomes the trip reason, never swallowed
            return Trip(InfraCategory.HARBOR_INTERNAL,
                        f"the job watchdog failed: {type(exc).__name__}: {exc}")

    def _begin(self) -> Trip | None:
        self._seen = latest_progress(self._job_dir)
        self._last_progress = time.monotonic()
        return None

    def _look(self) -> Trip | None:
        for check in self._checks:
            trip = check()
            if trip is not None:
                return trip
        now = time.monotonic()
        newest = latest_progress(self._job_dir)
        if newest > self._seen or self._busy():
            self._seen = max(self._seen, newest)
            self._last_progress = now
            return None
        idle = now - self._last_progress
        if idle > self._stall_sec:
            return Trip(InfraCategory.STALLED,
                        f"no progress under {self._job_dir} for {idle:.0f} s and no build "
                        "or command running")
        return None
