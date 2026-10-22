"""Content identities and immutable per-attempt task inputs (stdlib only)."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil

BUILD_FILE = ".judge_build.json"
BUILD_SCHEMA = "veritas/package-build/1"
SNAPSHOT_SCHEMA = "veritas/input-snapshot/1"
FEEDBACK_MARKER = "\n\n## IMPORTANT - VALIDITY FEEDBACK (previous attempt)\n"


class PackageIdentityError(ValueError):
    """An existing package cannot be proved to match the requested build."""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_manifest(root: str | Path, *, exclude: tuple[str, ...] = ()) -> list[dict]:
    """Sorted, chunk-hashed files. Symlinks are recorded as links, never followed."""
    root = Path(root)
    rows = []
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


def build_identity(adapter_file: str, *, sources: dict[str, str] | None = None,
                   materials: dict | None = None, configuration: dict | None = None) -> dict:
    """Bind adapter/helper source, caller-supplied material, and explicit switches.

    On-box injected material and rubric contents are not locally observable: record
    their references/version pins, never claim their bytes were measured here.
    """
    core = Path(__file__).resolve().parent
    paths = {"adapter": adapter_file, "package_inputs": __file__,
             **{name: str(core / (name + ".py")) for name in
                ("probe_core", "prompt_compose", "task_transform")}, **(sources or {})}
    fingerprints = {}
    for name, value in sorted(paths.items()):
        path = Path(value)
        fingerprints[name] = (file_manifest(path) if path.is_dir() else
                              {"sha256": sha256_file(path)})
    return {"schema": BUILD_SCHEMA, "sources": fingerprints,
            "source_paths": {name: str(Path(value).resolve()) for name, value in paths.items()},
            "materials": materials or {}, "configuration": configuration or {},
            "switches": {key: os.environ.get(key) for key in (
                "VERITAS_BATTERY", "VERITAS_DECLARE", "VERITAS_BARE_CONTRACT", "VERITAS_RUNNER_BASE",
                "VERITAS_RUBRIC_VERSION", "VERITAS_MATERIAL_VERSION",
                "VERITAS_NO_EVIDENCE", "VERITAS_NO_RUBRIC", "VERITAS_NO_CORE")}}


def validate_cache(package_dir: str, identity: dict) -> bool:
    """Return False for a new path; reject stale/unversioned caches without editing."""
    path = Path(package_dir)
    if not path.exists():
        return False
    try:
        previous = json.loads((path / BUILD_FILE).read_text())
    except (OSError, ValueError) as exc:
        raise PackageIdentityError(
            f"Unversioned or incomplete package {path}; build into a new output directory") from exc
    def without_paths(value):
        out = {key: val for key, val in value.items() if key != "source_paths"}
        # normalize switches: a None-valued (unset) switch is equivalent to the key
        # being absent — otherwise ADDING a new switch to the schema invalidates every
        # previously sealed package.
        if isinstance(out.get("switches"), dict):
            out["switches"] = {k: v for k, v in out["switches"].items() if v is not None}
        # plumbing source hashes are excluded from comparison (still recorded for
        # provenance): comparing them makes ANY code fix invalidate every sealed
        # package. package_inputs is the comparator itself; prompt_compose is pure
        # composition plumbing: all its wording lives in the
        # prompts dir as per-file-hashed data (evidence_header.txt included), so
        # wording drift is still caught, by the file hashes. Adapter + probe/
        # transform sources remain compared.
        if isinstance(out.get("sources"), dict):
            out["sources"] = {k: v for k, v in out["sources"].items()
                              if k not in ("package_inputs", "prompt_compose")}
        # legacy prompts narrowing: packages sealed before identity_sources() carried a
        # manifest of the whole prompts dir, so adding any other dataset's contract
        # file invalidated them. Reduce that manifest to the two files the
        # current identity actually depends on; sha comparison stays strict.
        src = out.get("sources")
        if isinstance(src, dict) and isinstance(src.get("prompts"), list):
            contract = identity.get("source_paths", {}).get("prompts_contract")
            man = {e.get("path"): e.get("sha256") for e in src.pop("prompts")}
            if "core_manual.txt" in man:
                src["prompts_core"] = {"sha256": man["core_manual.txt"]}
            rel = "contracts/" + os.path.basename(contract) if contract else None
            if rel in man:
                src["prompts_contract"] = {"sha256": man[rel]}
        return out
    if not isinstance(previous.get("identity"), dict) or \
            without_paths(previous["identity"]) != without_paths(identity):
        raise PackageIdentityError(
            f"Package configuration/source/material mismatch at {path}; use a new output directory")
    if previous.get("files") != file_manifest(path, exclude=(BUILD_FILE,)):
        raise PackageIdentityError(
            f"Package contents changed at {path}; preserve it and build a fresh version")
    return True


def seal_build(package_dir: str, identity: dict) -> None:
    # runner-base override for multi-executor packages (unused by the one-click suite,
    # whose Dockerfiles start FROM its own generation image): template Dockerfiles of
    # the original harness name an opencode-only base image; other executors need a
    # fuller base. Env-gated; the flag participates in build identity, so frozen
    # package trees are untouched.
    rb = os.environ.get("VERITAS_RUNNER_BASE")
    if rb:
        dfp = os.path.join(package_dir, "environment", "Dockerfile")
        if os.path.exists(dfp):
            txt = open(dfp).read()
            if "FROM opencode-runner:local" in txt or "FROM opencode-runner-py:local" in txt:
                txt = txt.replace("FROM opencode-runner:local", f"FROM {rb}")
                txt = txt.replace("FROM opencode-runner-py:local", f"FROM {rb}")
                open(dfp, "w").write(txt)
    path = Path(package_dir)
    payload = {"identity": identity, "files": file_manifest(path, exclude=(BUILD_FILE,))}
    (path / BUILD_FILE).write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")


def validate_materialized(package_dir: str, *, allow_unversioned: bool = False) -> str:
    """Verify a sealed package when consumed without calling its adapter again.

    Legacy task packages require an explicit compatibility opt-in and are labelled
    unversioned in the attempt ledger, never promoted to verified cache identities.
    """
    path = Path(package_dir)
    if not (path / BUILD_FILE).exists():
        if allow_unversioned:
            return "unversioned"
        raise PackageIdentityError(
            f"No build manifest at {path}; rebuild with its adapter into a NEW output directory. "
            "Legacy replay only: allow_unversioned_packages=True or VERITAS_ALLOW_UNVERSIONED=disclosed")
    try:
        stored = json.loads((path / BUILD_FILE).read_text())["identity"]
        source_paths = dict(stored["source_paths"])
        if "prompts" in source_paths and os.environ.get("VERITAS_PROMPTS_DIR"):
            source_paths["prompts"] = os.environ["VERITAS_PROMPTS_DIR"]
        current = build_identity(source_paths["adapter"], sources=source_paths,
                                 materials=stored["materials"], configuration=stored["configuration"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise PackageIdentityError(f"Cannot verify package build identity at {path}; rebuild into a new directory") from exc
    validate_cache(package_dir, current)
    return "verified"


def snapshot_package(package_dir: str, destination: str, manifest_path: str,
                     *, feedback_file: str | None = None, feedback: str | None = None,
                     injected_files: dict | None = None) -> tuple[str | None, dict]:
    """Copy inputs before an attempt and freeze a digest manifest outside the package.

    destination must not exist. Base inputs never change. Legacy feedback is removed
    only in the private attempt copy, so it cannot contaminate a fresh first attempt.
    """
    source = Path(package_dir).resolve()
    dest = Path(destination).resolve()
    if source == dest or source in dest.parents:
        raise ValueError("attempt inputs must be outside the source package")
    shutil.copytree(source, dest, symlinks=False,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    private_feedback = None
    if feedback_file:
        original = Path(feedback_file).resolve()
        try:
            relative = original.relative_to(source)
        except ValueError as exc:
            raise ValueError("feedback file must belong to its task package") from exc
        target = dest / relative
        if target.exists():
            text = target.read_text(encoding="utf-8", errors="replace").split(FEEDBACK_MARKER)[0]
            if feedback is not None:
                text += FEEDBACK_MARKER + feedback + "\n"
            target.write_text(text)
            private_feedback = str(target)
    manifest = Path(manifest_path).resolve()
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "schema": SNAPSHOT_SCHEMA, "source_package_dir": str(source),
        "package_dir": str(dest), "files": file_manifest(dest),
        "injected_files": dict(injected_files or {}),
        "injected_content_status": "external references; bytes not captured by local snapshot",
    }, sort_keys=True, indent=2) + "\n")
    return private_feedback, {"package_dir": str(dest), "manifest_path": str(manifest),
                              "sha256": sha256_file(manifest)}
