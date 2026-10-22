"""Package identity: content-addressed build records and immutable attempt inputs.

Port of the upstream ``package_inputs`` module. A sealed generation package
carries ``.veritas_build.json`` with three fields:

* ``identity`` -- what the package was built from, by content only: the file
  manifests of the method kernel (``gavel_harness/method`` and
  ``gavel_harness/paradigms/assets``, under the reserved source names
  ``method`` and ``assets``), the content of every further named input, the
  caller's material references and the explicit build configuration. It holds
  no paths, so the same inputs give the same identity on every host.
* ``identity_sha256`` -- the digest of the canonical JSON of ``identity``.
* ``files`` -- the package's own files in the upstream
  ``.judge_build.json["files"]`` format (see :func:`file_manifest`), so a
  package can be compared file by file with one sealed by the upstream harness.

Upstream left the wording inside ``prompt_compose.py`` out of the comparison;
here every prompt word is a file under ``method/`` and the whole kernel is
compared.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from pathlib import Path, PurePosixPath
from typing import Any

from ..errors import ConfigError
from ..fsguard import escaping_symlinks

BUILD_FILE = ".veritas_build.json"
BUILD_SCHEMA = "gavel-harness/package-build/2"
"""Version 2 of the upstream ``veritas/package-build/1`` identity: content only, no paths."""
SNAPSHOT_SCHEMA = "gavel-harness/input-snapshot/1"

_PACKAGE = resources.files("gavel_harness")
_KERNEL = {"method": ("method",), "assets": ("paradigms", "assets")}
_FEEDBACK_MARKER = ("method", "fragments", "feedback_marker.txt")


class PackageIdentityError(ConfigError):
    """A package cannot be proved to match the requested build, or its bytes changed."""


@dataclass(frozen=True)
class Snapshot:
    """The private input copy of one generation attempt."""

    package_dir: Path
    manifest_path: Path
    manifest_sha256: str
    feedback_path: Path | None
    """The copy's feedback-carrying file, when feedback handling was requested."""


def sha256_file(path: str | Path) -> str:
    """Hex sha256 of a file's bytes, read in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_manifest(root: str | Path, *, exclude: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    """Every file under ``root`` as ``{path, bytes, sha256}``, sorted by path.

    ``path`` is POSIX and relative to ``root``. A symlink (to a file or a
    directory) is recorded as ``{path, symlink}`` with its target and never
    followed. ``__pycache__`` and ``.git`` directories, ``*.pyc``/``*.pyo``
    files and the relative paths in ``exclude`` are skipped. The rows and their
    order are those of upstream ``package_inputs.file_manifest``.
    """
    root = Path(root)
    rows: list[dict[str, Any]] = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", ".git"))
        for name in sorted(names + [d for d in dirs if (Path(directory) / d).is_symlink()]):
            path = Path(directory) / name
            rel = path.relative_to(root).as_posix()
            if rel in exclude or path.suffix in (".pyc", ".pyo"):
                continue
            if path.is_symlink():
                rows.append({"path": rel, "symlink": os.readlink(path)})
            else:
                rows.append({"path": rel, "bytes": path.stat().st_size,
                             "sha256": sha256_file(path)})
    return sorted(rows, key=lambda row: row["path"])


def kernel_fingerprint() -> dict[str, list[dict[str, Any]]]:
    """File manifests of the installed method kernel, by reserved source name."""
    fingerprint = {}
    for name, parts in _KERNEL.items():
        with resources.as_file(_PACKAGE.joinpath(*parts)) as path:
            fingerprint[name] = file_manifest(path)
    return fingerprint


def build_identity(
    *,
    sources: Mapping[str, str | Path] | None = None,
    materials: Mapping[str, Any] | None = None,
    configuration: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The identity of a package built from the given inputs.

    ``sources`` names further local inputs (task instruction, environment
    directory, profile): a directory contributes its file manifest, a file
    ``{sha256}``; where they were read from is not recorded. ``materials`` are
    references to content that is not observed here (task id, on-box material
    version pins). ``configuration`` holds every explicit switch that shapes the
    package. Both must be JSON data; the identity is returned in its JSON form,
    so it compares equal to the copy read back from a sealed package.
    """
    sources = dict(sources or {})
    reserved = sorted(set(sources) & set(_KERNEL))
    if reserved:
        raise ValueError(f"source names {reserved} are reserved for the method kernel")
    fingerprints: dict[str, Any] = dict(kernel_fingerprint())
    for name, value in sorted(sources.items()):
        path = Path(value)
        fingerprints[name] = (file_manifest(path) if path.is_dir() else
                              {"sha256": sha256_file(path)})
    return _canonical({"schema": BUILD_SCHEMA, "sources": fingerprints,
                       "materials": dict(materials or {}),
                       "configuration": dict(configuration or {})})


def identity_digest(identity: Mapping[str, Any]) -> str:
    """Hex sha256 of the canonical JSON of an identity."""
    text = json.dumps(identity, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def seal_build(package_dir: str | Path, identity: Mapping[str, Any]) -> str:
    """Write ``.veritas_build.json`` into a finished package; return the identity digest.

    Refuses a package that is already sealed: a package is built once, into a
    new directory.
    """
    path = Path(package_dir)
    if identity.get("schema") != BUILD_SCHEMA:
        raise ValueError(f"not a {BUILD_SCHEMA} identity; make it with build_identity()")
    if (path / BUILD_FILE).exists():
        raise PackageIdentityError(f"{path} is already sealed; build into a new directory")
    identity = _canonical(identity)
    digest = identity_digest(identity)
    payload = {"identity": identity, "identity_sha256": digest,
               "files": file_manifest(path, exclude=(BUILD_FILE,))}
    (path / BUILD_FILE).write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n",
                                   encoding="utf-8")
    return digest


def validate_cache(package_dir: str | Path, identity: Mapping[str, Any]) -> bool:
    """Return False for a new path, True for a sealed package of exactly this build.

    Raises PackageIdentityError, without editing anything, when the path holds an
    unsealed package, a package of another build, or a package whose files
    changed after sealing.
    """
    path = Path(package_dir)
    if not path.exists():
        return False
    stored = _read_build(path)
    wanted = _canonical(identity)
    if stored["identity"] != wanted:
        differ = _differing(stored["identity"], wanted)
        raise PackageIdentityError(
            f"{path} was built from other inputs ({', '.join(differ)} differ); "
            "use a new output directory"
        )
    _check_files(path, stored["files"])
    return True


def validate_materialized(package_dir: str | Path) -> str:
    """Verify a sealed package consumed without rebuilding it; return its identity digest.

    The package must have been built by the installed method kernel and its files
    must be the sealed bytes.
    """
    path = Path(package_dir)
    stored = _read_build(path)
    kernel = kernel_fingerprint()
    changed = [name for name in kernel if stored["identity"]["sources"].get(name) != kernel[name]]
    if changed:
        raise PackageIdentityError(
            f"{path} was built by another method kernel ({', '.join(changed)} differ); "
            "rebuild it into a new directory"
        )
    _check_files(path, stored["files"])
    return stored["identity_sha256"]


def snapshot_package(
    package_dir: str | Path,
    destination: str | Path,
    manifest_path: str | Path,
    *,
    feedback_file: str | None = None,
    feedback: str | None = None,
    injected_files: Mapping[str, Any] | None = None,
) -> Snapshot:
    """Copy a sealed package into a private attempt directory and freeze its digest.

    ``destination`` must not exist and must lie outside the package. The base
    package never changes. ``feedback_file`` is a package-relative path, usually
    ``instruction.md``: in the copy, any earlier validity feedback is cut at the
    feedback marker, and ``feedback`` (when given) is appended after the marker.
    ``injected_files`` records references to material injected into the
    container; their bytes are not part of the snapshot. The manifest at
    ``manifest_path`` holds the source identity digest and the copy's files.
    """
    source = Path(package_dir).resolve()
    dest = Path(destination).resolve()
    if source == dest or source in dest.parents:
        raise ValueError("attempt inputs must be outside the source package")
    source_identity = _read_build(source)["identity_sha256"]
    escaping = escaping_symlinks(source)
    if escaping:
        raise ConfigError(
            f"{source}: symlinks point outside the package: " + ", ".join(escaping[:5])
        )
    feedback_rel = None
    if feedback_file is not None:
        feedback_rel = PurePosixPath(feedback_file)
        if feedback_rel.is_absolute() or ".." in feedback_rel.parts or not feedback_rel.parts:
            raise ValueError(
                f"feedback file must be a path inside the package, got {feedback_file!r}"
            )
        if not (source / feedback_rel).is_file():
            raise FileNotFoundError(f"feedback file {feedback_file} is not in {source}")
    shutil.copytree(source, dest, symlinks=False,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    feedback_path = None
    if feedback_rel is not None:
        marker = _PACKAGE.joinpath(*_FEEDBACK_MARKER).read_text(encoding="utf-8")
        feedback_path = dest / feedback_rel
        text = feedback_path.read_text(encoding="utf-8").split(marker)[0]
        if feedback is not None:
            text += marker + feedback + "\n"
        feedback_path.write_text(text, encoding="utf-8")
    manifest = Path(manifest_path).resolve()
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "schema": SNAPSHOT_SCHEMA, "source_identity_sha256": source_identity,
        "files": file_manifest(dest), "injected_files": dict(injected_files or {}),
        "injected_content_status": "external references; bytes not captured by local snapshot",
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return Snapshot(package_dir=dest, manifest_path=manifest,
                    manifest_sha256=sha256_file(manifest), feedback_path=feedback_path)


def _canonical(value: Mapping[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(json.dumps(value, sort_keys=True, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"package identity must be JSON data: {exc}") from exc


def _read_build(path: Path) -> dict[str, Any]:
    """Load and self-check the build record of a sealed package."""
    try:
        stored = json.loads((path / BUILD_FILE).read_text(encoding="utf-8"))
        identity = stored["identity"]
        valid = (identity["schema"] == BUILD_SCHEMA and isinstance(identity["sources"], dict)
                 and isinstance(stored["files"], list))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise PackageIdentityError(
            f"no readable {BUILD_FILE} at {path}; build into a new output directory") from exc
    if not valid:
        raise PackageIdentityError(f"{path / BUILD_FILE} is not a {BUILD_SCHEMA} record")
    if stored.get("identity_sha256") != identity_digest(identity):
        raise PackageIdentityError(
            f"{path / BUILD_FILE}: identity_sha256 does not match its identity"
        )
    return stored


def _check_files(path: Path, sealed: list[dict[str, Any]]) -> None:
    current = file_manifest(path, exclude=(BUILD_FILE,))
    if current == sealed:
        return
    before = {row["path"]: row for row in sealed}
    after = {row["path"]: row for row in current}
    changes = ([f"+{p}" for p in sorted(after.keys() - before.keys())]
               + [f"-{p}" for p in sorted(before.keys() - after.keys())]
               + [f"~{p}" for p in sorted(before.keys() & after.keys()) if before[p] != after[p]])
    more = f" and {len(changes) - 10} more" if len(changes) > 10 else ""
    shown = ", ".join(changes[:10]) + more
    raise PackageIdentityError(
        f"{path} changed after sealing ({shown}); preserve it and build a fresh version")


def _differing(stored: Mapping[str, Any], wanted: Mapping[str, Any]) -> list[str]:
    """Names of the identity parts that differ, down to individual sources."""
    out = []
    for key in sorted(stored.keys() | wanted.keys()):
        a, b = stored.get(key), wanted.get(key)
        if a == b:
            continue
        if key == "sources" and isinstance(a, dict) and isinstance(b, dict):
            out += [f"sources.{name}" for name in sorted(a.keys() | b.keys())
                    if a.get(name) != b.get(name)]
        else:
            out.append(key)
    return out
