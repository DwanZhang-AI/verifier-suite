"""Harbor registry datasets: load a registry, pin and sample its tasks, fetch them.

A Harbor registry (``registry.json``, parsed with Harbor's own ``DatasetSpec``)
lists datasets; every dataset task names a git repository, a commit and a path.
A *family* is one dataset name. :func:`families` lists every family,
:func:`sample` draws tasks from one with a seed, and :func:`fetch_task`
materializes a task directory at its pinned commit by a partial fetch that
downloads only that commit's trees and the files under the task's path (hosts
without partial-clone support, such as the Hugging Face hub, send the whole
commit). The registry file and the remote repositories are only read.

Pins. A task is pinned when its registry ``git_commit_id`` is a full hex
object name (40 or 64 digits). Tasks pinned to anything else (``HEAD``, a
branch name) and tasks without a ``git_url`` are never fetched; a
:class:`Family` counts them in ``excluded``, and a :class:`FamilySample` says
when it holds fewer tasks than requested, so a sample never shrinks silently.
A ``registry:<name>@<commit>`` reference (:func:`parse_ref`) supplies the
commit for the dataset's unpinned tasks and must equal the pin of every pinned
one. When a registry lists one name with several versions, the first entry in
registry order is the family (the chosen version is recorded on every task).

Cache layout under ``cache_dir`` (the caller's ``out/_cache``)::

    repos/<repo>.git              bare partial clone of one repository
    tasks/<repo>/<commit>/<path>  task directories, moved into place only when complete
    locks/<repo>.lock             serializes git work on one repository across threads
                                  and processes

``<repo>`` is a readable slug of the git URL plus a digest of the full URL. A
task directory already in the cache is reused as is.

Errors. A network or git failure raises
:class:`~gavel_harness.errors.InfraError` (``fetch_failed``) once the retry
budget is spent. A malformed registry, a malformed reference, or a task path
that is not a directory at the pinned commit raises ConfigError. A task that
contains Git LFS pointer files raises RefusalError (``lfs_content``): LFS
objects are not fetched, and a pointer in place of its file is not the task.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal
from urllib.parse import urlsplit

import httpx
from harbor.models.registry import DatasetSpec
from pydantic import ValidationError

from ..config import slug
from ..errors import ConfigError, InfraCategory, InfraError, RefusalError, RefusalReason

REF_PREFIX = "registry:"
"""Prefix of a registry reference among ``gavel-harness gen`` inputs."""

UNPINNED = "unpinned"
"""``excluded`` key: the registry pins the task to no full commit id."""
NOT_GIT = "not_git"
"""``excluded`` key: the registry gives the task no git URL."""

_COMMIT = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
_LFS_POINTER_PREFIXES = (
    b"version https://git-lfs.github.com/spec/v1\n",
    b"version https://hawser.github.com/spec/v1\n",
)
_LFS_POINTER_MAX_BYTES = 1024
# Git LFS pointer files are small text files that start with a version line
# (LFS specification); a file larger than this cap is not a pointer.
_NO_BLOB_FILTER_HOSTS = frozenset({"huggingface.co"})
# The Hugging Face git server does not serve partial clones (Harbor's task
# client makes the same exception); there the commit is fetched whole.


@dataclass(frozen=True)
class Registry:
    """A parsed registry file."""

    source: str
    """The path or URL the registry was read from."""
    sha256: str
    """sha256 of the registry bytes."""
    datasets: tuple[DatasetSpec, ...]
    """The registry rows in file order."""


@dataclass(frozen=True)
class RegistryTask:
    """One task of a family, pinned to a commit.

    ``pinned_by`` is ``registry`` when the registry pins the commit and ``ref``
    when a ``registry:<name>@<commit>`` reference supplied it. ``path`` is the
    task directory inside the repository, a relative POSIX path.
    """

    family: str
    version: str
    name: str
    git_url: str
    commit: str
    path: str
    pinned_by: Literal["registry", "ref"]

    def __post_init__(self) -> None:
        if self.pinned_by not in ("registry", "ref"):
            raise ConfigError(f"task {self.name!r}: pinned_by must be 'registry' or 'ref', "
                              f"got {self.pinned_by!r}")
        if not _COMMIT.fullmatch(self.commit):
            raise ConfigError(
                f"task {self.name!r}: commit must be a full hex id, got {self.commit!r}"
            )
        path = PurePosixPath(self.path)
        if (path.is_absolute() or not path.parts or ".." in path.parts
                or path.as_posix() != self.path):
            raise ConfigError(
                f"task {self.name!r}: path must be a normalized relative POSIX path, "
                f"got {self.path!r}"
            )


@dataclass(frozen=True)
class Family:
    """The fetchable tasks of one dataset, sorted by ``(name, path)``."""

    name: str
    version: str
    tasks: tuple[RegistryTask, ...]
    excluded: Mapping[str, int]
    """Tasks that cannot be fetched, counted by reason (:data:`UNPINNED`, :data:`NOT_GIT`)."""


@dataclass(frozen=True)
class FamilySample:
    """The tasks drawn from one family; fewer than ``requested`` when the family has fewer."""

    family: Family
    requested: int
    tasks: tuple[RegistryTask, ...]

    @property
    def short(self) -> bool:
        """True when the family could not supply ``requested`` tasks."""
        return len(self.tasks) < self.requested


@dataclass(frozen=True)
class RegistryRef:
    """A parsed ``registry:<name>@<commit>`` input."""

    name: str
    commit: str


@dataclass(frozen=True)
class FetchedTask:
    """A task directory materialized at its pinned commit."""

    task: RegistryTask
    task_dir: Path
    cached: bool
    """True when the directory was already in the cache."""


def is_ref(text: str) -> bool:
    """Whether a ``gavel-harness gen`` input is a registry reference."""
    return text.startswith(REF_PREFIX)


def parse_ref(text: str) -> RegistryRef:
    """Parse ``registry:<name>@<commit>``; the commit must be a full hex id.

    Raises ConfigError for any other form.
    """
    if not is_ref(text):
        raise ConfigError(f"{text!r} is not a registry reference ({REF_PREFIX}<name>@<commit>)")
    name, sep, commit = text.removeprefix(REF_PREFIX).rpartition("@")
    if not sep or not name:
        raise ConfigError(f"{text!r}: expected {REF_PREFIX}<name>@<commit>")
    commit = commit.lower()
    if not _COMMIT.fullmatch(commit):
        raise ConfigError(f"{text!r}: the commit must be a full hex commit id, got {commit!r}")
    return RegistryRef(name=name, commit=commit)


def load_registry(source: str | Path, *, client: httpx.Client | None = None) -> Registry:
    """Read and parse a registry from a file path or an http(s) URL.

    ``client`` serves URL sources (default: a fresh ``httpx.Client``). A
    transport failure, HTTP 429 or a 5xx answer raises InfraError
    (``fetch_failed``); any other non-200 answer, a missing file and a registry
    that does not match Harbor's dataset schema raise ConfigError.
    """
    text = str(source)
    if text.startswith(("http://", "https://")):
        data = _download(text, client)
    else:
        try:
            data = Path(text).read_bytes()
        except OSError as exc:
            raise ConfigError(f"cannot read registry {text}: {exc}") from exc
    try:
        rows = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"registry {text} is not JSON: {exc}") from exc
    if not isinstance(rows, list):
        raise ConfigError(f"registry {text} must be a JSON list of datasets")
    try:
        datasets = tuple(DatasetSpec.model_validate(row) for row in rows)
    except ValidationError as exc:
        raise ConfigError(f"registry {text} does not match Harbor's dataset schema: {exc}") from exc
    return Registry(source=text, sha256=hashlib.sha256(data).hexdigest(), datasets=datasets)


def families(registry: Registry) -> tuple[Family, ...]:
    """Every family of ``registry``, sorted by name; the first entry of a name wins."""
    names = sorted({dataset.name for dataset in registry.datasets})
    return tuple(family(registry, name) for name in names)


def family(registry: Registry, name: str, *, commit: str | None = None) -> Family:
    """The family ``name`` of ``registry`` (its first entry in registry order).

    ``commit`` pins the tasks the registry leaves unpinned, and every task the
    registry does pin must be pinned to it. Raises ConfigError when no dataset
    has that name or a registry pin differs from ``commit``.
    """
    dataset = next((entry for entry in registry.datasets if entry.name == name), None)
    if dataset is None:
        raise ConfigError(f"registry {registry.source} has no dataset named {name!r}")
    if commit is not None and not _COMMIT.fullmatch(commit):
        raise ConfigError(f"commit must be a full lower-case hex id, got {commit!r}")
    tasks: list[RegistryTask] = []
    excluded: Counter[str] = Counter()
    conflicts: list[str] = []
    for entry in dataset.tasks:
        if entry.git_url is None:
            excluded[NOT_GIT] += 1
            continue
        pin = (entry.git_commit_id or "").lower()
        if _COMMIT.fullmatch(pin):
            if commit is not None and pin != commit:
                conflicts.append(f"{entry.name} at {pin}")
                continue
            pinned_by: Literal["registry", "ref"] = "registry"
        elif commit is not None:
            pin, pinned_by = commit, "ref"
        else:
            excluded[UNPINNED] += 1
            continue
        tasks.append(RegistryTask(
            family=dataset.name, version=dataset.version, name=entry.name,
            git_url=entry.git_url, commit=pin, path=entry.path.as_posix(), pinned_by=pinned_by,
        ))
    if conflicts:
        raise ConfigError(
            f"dataset {name!r}: {len(conflicts)} task(s) are pinned to another commit than "
            f"{commit}: {', '.join(conflicts[:3])}"
        )
    tasks.sort(key=lambda task: (task.name, task.path))
    return Family(name=dataset.name, version=dataset.version, tasks=tuple(tasks),
                  excluded=dict(sorted(excluded.items())))


def sample(source: Family, k: int, seed: int) -> FamilySample:
    """Draw ``k`` tasks from ``source`` (all of them when it has fewer).

    The draw uses its own ``random.Random`` seeded with ``"<seed>:<family name>"``,
    so a family's sample depends only on the seed, the family name and its task
    list, never on which other families are sampled. Tasks are returned sorted
    by ``(name, path)``. Raises ConfigError when ``k`` is below 1.
    """
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ConfigError(f"the sample size must be a positive integer, got {k!r}")
    rng = random.Random(f"{seed}:{source.name}")
    drawn = rng.sample(source.tasks, min(k, len(source.tasks)))
    drawn.sort(key=lambda task: (task.name, task.path))
    return FamilySample(family=source, requested=k, tasks=tuple(drawn))


def fetch_tasks(
    tasks: Sequence[RegistryTask],
    cache_dir: Path,
    *,
    attempts: int = 3,
    retry_delay_sec: float = 20.0,
    git_timeout_sec: float = 1200.0,
) -> list[FetchedTask]:
    """Fetch every task with :func:`fetch_task`, in order; the first failure raises."""
    return [
        fetch_task(task, cache_dir, attempts=attempts, retry_delay_sec=retry_delay_sec,
                   git_timeout_sec=git_timeout_sec)
        for task in tasks
    ]


def fetch_task(
    task: RegistryTask,
    cache_dir: Path,
    *,
    attempts: int = 3,
    retry_delay_sec: float = 20.0,
    git_timeout_sec: float = 1200.0,
) -> FetchedTask:
    """Materialize ``task`` at its pinned commit under ``cache_dir``; see the module docstring.

    Every git command that talks to the remote is tried up to ``attempts``
    times, waiting ``retry_delay_sec`` times the attempt number in between, and
    is killed after ``git_timeout_sec``. Raises InfraError (``fetch_failed``)
    when they all fail, ConfigError when git is missing or the path is not a
    directory at the commit, RefusalError (``lfs_content``) for Git LFS
    pointers.
    """
    if attempts < 1:
        raise ConfigError(f"attempts must be at least 1, got {attempts}")
    git = _Git(timeout_sec=git_timeout_sec)
    slug = _repo_slug(task.git_url)
    cache = Path(cache_dir).absolute()
    repo = cache / "repos" / f"{slug}.git"
    dest = cache / "tasks" / slug / task.commit / task.path
    with _locked(cache / "locks" / f"{slug}.lock"):
        if dest.is_dir():
            return FetchedTask(task=task, task_dir=dest, cached=True)
        if not repo.is_dir():
            _init_repo(git, repo, task.git_url)
        pin_ref = f"refs/pins/{task.commit}"
        if not git.ok("-C", str(repo), "show-ref", "--verify", "--quiet", pin_ref):
            fetch = ["-C", str(repo), "fetch", "--quiet", "--no-tags", "--depth", "1"]
            if _blob_filter(task.git_url):
                fetch.append("--filter=blob:none")
            _retry(lambda: git.run(*fetch, "origin", f"{task.commit}:{pin_ref}"),
                   f"git fetch of {task.commit} from {task.git_url}", attempts, retry_delay_sec)
        _require_tree(git, repo, task)
        staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=_mkdir(cache / "tasks")))
        try:
            tree = staging / "tree"
            index = staging / "index"

            def checkout() -> subprocess.CompletedProcess[str]:
                if tree.exists():
                    shutil.rmtree(tree)
                index.unlink(missing_ok=True)
                tree.mkdir()
                return git.run(
                    "-c", "core.autocrlf=false", f"--git-dir={repo}", f"--work-tree={tree}",
                    "checkout", "--quiet", task.commit, "--", task.path,
                    index_file=index,
                )

            _retry(checkout, f"git checkout of {task.path} at {task.commit} from {task.git_url}",
                   attempts, retry_delay_sec)
            materialized = tree / task.path
            pointers = _lfs_pointers(materialized)
            if pointers:
                raise RefusalError(
                    RefusalReason.LFS_CONTENT,
                    f"{task.family}/{task.name} stores {len(pointers)} file(s) in Git LFS "
                    f"(e.g. {pointers[0]}); LFS objects are not fetched",
                )
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.rename(materialized, dest)
        finally:
            shutil.rmtree(staging)
    return FetchedTask(task=task, task_dir=dest, cached=False)


class _Git:
    """Runs git without a terminal prompt and with literal pathspecs.

    A missing git binary is a ConfigError.
    """

    def __init__(self, *, timeout_sec: float) -> None:
        self._timeout = timeout_sec

    def run(self, *args: str, index_file: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_LITERAL_PATHSPECS="1")
        if index_file is not None:
            env["GIT_INDEX_FILE"] = str(index_file)
        try:
            return subprocess.run(["git", *args], capture_output=True, text=True, env=env,
                                  timeout=self._timeout, check=False)
        except FileNotFoundError as exc:
            raise ConfigError("git is required to fetch registry tasks") from exc

    def ok(self, *args: str) -> bool:
        """Run a local query; True on exit 0, False on exit 1, InfraError otherwise."""
        result = self.run(*args)
        if result.returncode not in (0, 1):
            raise InfraError(InfraCategory.FETCH_FAILED,
                             f"git {' '.join(args)}: exit {result.returncode}: "
                             f"{_tail(result.stderr)}")
        return result.returncode == 0

    def check(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run a local command; any non-zero exit raises InfraError."""
        result = self.run(*args)
        if result.returncode != 0:
            raise InfraError(InfraCategory.FETCH_FAILED,
                             f"git {' '.join(args)}: exit {result.returncode}: "
                             f"{_tail(result.stderr)}")
        return result


def _download(url: str, client: httpx.Client | None) -> bytes:
    own = client is None
    http = httpx.Client(timeout=60.0, follow_redirects=True) if client is None else client
    try:
        response = http.get(url)
    except httpx.HTTPError as exc:
        raise InfraError(InfraCategory.FETCH_FAILED,
                         f"registry {url}: {type(exc).__name__}: {exc}") from exc
    finally:
        if own:
            http.close()
    if response.status_code == 429 or response.status_code >= 500:
        raise InfraError(InfraCategory.FETCH_FAILED, f"registry {url}: HTTP {response.status_code}")
    if response.status_code != 200:
        raise ConfigError(f"registry {url}: HTTP {response.status_code}")
    return response.content


def _repo_slug(git_url: str) -> str:
    parts = urlsplit(git_url)
    readable = slug(f"{parts.netloc}{parts.path}").strip("-")[-48:]
    digest = hashlib.sha256(git_url.encode()).hexdigest()[:12]
    return f"{readable}-{digest}" if readable else digest


def _blob_filter(git_url: str) -> bool:
    return (urlsplit(git_url).hostname or "") not in _NO_BLOB_FILTER_HOSTS


def _init_repo(git: _Git, repo: Path, git_url: str) -> None:
    """Create the bare cache repository for ``git_url``; it appears at ``repo`` only when ready."""
    staging = Path(tempfile.mkdtemp(prefix=f".{repo.name}.", dir=_mkdir(repo.parent)))
    try:
        built = staging / repo.name
        git.check("init", "--quiet", "--bare", str(built))
        git.check("-C", str(built), "config", "remote.origin.url", git_url)
        if _blob_filter(git_url):
            for key, value in (("core.repositoryformatversion", "1"),
                               ("extensions.partialClone", "origin"),
                               ("remote.origin.promisor", "true")):
                git.check("-C", str(built), "config", key, value)
        os.rename(built, repo)
    finally:
        shutil.rmtree(staging)


def _require_tree(git: _Git, repo: Path, task: RegistryTask) -> None:
    listing = git.check("-C", str(repo), "ls-tree", task.commit, "--", task.path).stdout
    entries = [line.split("\t", 1) for line in listing.splitlines() if line]
    match = [meta.split() for meta, path in entries if path == task.path]
    if not match:
        raise ConfigError(
            f"{task.family}/{task.name}: {task.path} does not exist at {task.commit} "
            f"in {task.git_url}"
        )
    if match[0][1] != "tree":
        raise ConfigError(
            f"{task.family}/{task.name}: {task.path} is a {match[0][1]}, not a task directory, "
            f"at {task.commit} in {task.git_url}"
        )


def _retry(
    action: Callable[[], subprocess.CompletedProcess[str]],
    what: str,
    attempts: int,
    delay_sec: float,
) -> subprocess.CompletedProcess[str]:
    failure = ""
    for attempt in range(1, attempts + 1):
        try:
            result = action()
        except subprocess.TimeoutExpired as exc:
            failure = f"timed out after {exc.timeout} s"
        else:
            if result.returncode == 0:
                return result
            failure = f"exit {result.returncode}: {_tail(result.stderr)}"
        if attempt < attempts:
            time.sleep(delay_sec * attempt)
    raise InfraError(InfraCategory.FETCH_FAILED,
                     f"{what} failed after {attempts} attempt(s); last: {failure}")


def _lfs_pointers(root: Path) -> list[str]:
    """Relative POSIX paths of the Git LFS pointer files under ``root``, sorted."""
    found = []
    for directory, _dirs, files in os.walk(root):
        for name in files:
            path = Path(directory) / name
            if path.is_symlink() or path.stat().st_size > _LFS_POINTER_MAX_BYTES:
                continue
            head = path.read_bytes()
            if head.startswith(_LFS_POINTER_PREFIXES):
                found.append(path.relative_to(root).as_posix())
    return sorted(found)


@contextmanager
def _locked(lock_path: Path) -> Iterator[None]:
    _mkdir(lock_path.parent)
    with lock_path.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _mkdir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _tail(text: str, limit: int = 400) -> str:
    text = text.strip()
    return text if len(text) <= limit else "..." + text[-limit:]
