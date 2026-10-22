#!/usr/bin/env python3
"""TrialView — the ONE place that knows the Harbor trial-directory layout.

Collectors never touch raw paths; they ask the view. When the layout changes
(new Harbor version, new collection config), this file is the whole blast radius.

Layout (as collected by the generation harness):
    <trial>/config.json      job config (dataset, task, model, budgets)
    <trial>/result.json      Harbor trial result (agent/verifier outcomes, usage)
    <trial>/trial.log        orchestration log (incl. collection notes)
    <trial>/agent/           agent-side collected files (often only setup/)
    <trial>/verifier/        verifier-phase outputs (reward.txt, test-stdout.txt, ...)
    <trial>/artifacts/       collected container files + Harbor collection manifest
"""
from __future__ import annotations

import json
import os
import fnmatch


class TrialView:
    def __init__(self, trial_dir: str):
        self.root = os.path.abspath(trial_dir)
        if not os.path.isdir(self.root):
            raise FileNotFoundError(trial_dir)

    # ------------------------------------------------------------- structured
    def _json(self, name: str) -> dict | None:
        p = os.path.join(self.root, name)
        try:
            with open(p, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return None

    def result(self) -> dict | None:
        value = self._json("result.json")
        return value if isinstance(value, dict) else None

    def config(self) -> dict | None:
        value = self._json("config.json")
        return value if isinstance(value, dict) else None

    def dataset(self) -> str | None:
        for src in (self.config() or {}, self.result() or {}):
            for key in ("dataset", "task_name"):
                v = src.get(key)
                if isinstance(v, str) and v:
                    return v.split("/")[-1].split("-")[0] if key == "task_name" else v
        return None

    def collection_manifest(self) -> list | None:
        """Harbor's own record of what it copied out (artifacts/manifest.json)."""
        m = self._json(os.path.join("artifacts", "manifest.json"))
        return m if isinstance(m, list) else None

    # ------------------------------------------------------------- files
    def rel(self, *parts: str) -> str:
        return os.path.join(self.root, *parts)

    def exists(self, *parts: str) -> bool:
        return os.path.exists(self.rel(*parts))

    def walk_files(self, subdir: str) -> list[str]:
        """All files under <trial>/<subdir>, trial-relative, sorted (deterministic)."""
        base = self.rel(subdir)
        out = []
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames.sort()
            for f in sorted(filenames):
                out.append(os.path.relpath(os.path.join(dirpath, f), self.root))
        return out

    def find(self, subdir: str, basename: str) -> list[str]:
        return [p for p in self.walk_files(subdir)
                if os.path.basename(p) == basename]

    def deliverable_files(self) -> list[str]:
        """Collected task artifacts, excluding telemetry and process logs.

        Prefer Harbor's successful artifact destinations. Old trials without a
        usable manifest retain a conservative fallback for known verifier products.
        A verifier stdout/reward file alone is never a delivered verifier.
        """
        out = set()
        for entry in self.collection_manifest() or []:
            if not isinstance(entry, dict) or entry.get("status") != "ok":
                continue
            source = str(entry.get("source") or "")
            if source.startswith(("/logs/agent", "/logs/verifier")) or source.endswith("runtime-info.json"):
                continue
            dest = entry.get("destination")
            if not isinstance(dest, str) or not dest:
                dest = source.lstrip("/")
            target = os.path.realpath(self.rel("artifacts", dest))
            base = os.path.realpath(self.rel("artifacts"))
            if os.path.commonpath((base, target)) != base:
                continue
            if os.path.isfile(target):
                out.add(os.path.relpath(target, self.root))
            elif os.path.isdir(target):
                out.update(self.walk_files(os.path.relpath(target, self.root)))
        # Probe copies of these products are supported for older transport layouts.
        known = ("checker.py", "verifier.py", "judge_prompt.txt", "test_*.py")
        for subdir in ("artifacts", "verifier"):
            for path in self.walk_files(subdir):
                if "/evidence/" not in path and any(
                        fnmatch.fnmatch(os.path.basename(path), name) for name in known):
                    out.add(path)
        return sorted(p for p in out if not p.endswith("manifest.json")
                      and "/evidence/" not in p
                      and os.path.basename(p) not in {"reward.txt", "reward.json", "usage.json",
                                                     "runtime-info.json", "test-stdout.txt", "test-stderr.txt"})

    def collection_excludes(self) -> list[str]:
        """Parse the collection-exclude note from trial.log — the honest source
        for WHY process streams are absent (they were excluded, not never made)."""
        p = self.rel("trial.log")
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if "exclude=[" in line:
                        seg = line.split("exclude=[", 1)[1].split("]", 1)[0]
                        return [s.strip().strip("'\"") for s in seg.split(",") if s.strip()]
        except OSError:
            pass
        return []


def _selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "artifacts", "app"))
        json.dump({"dataset": "tau2"}, open(os.path.join(d, "config.json"), "w"))
        json.dump([{"source": "/app/x", "status": "ok"}],
                  open(os.path.join(d, "artifacts", "manifest.json"), "w"))
        open(os.path.join(d, "artifacts", "app", "checker.py"), "w").write("x")
        open(os.path.join(d, "trial.log"), "w").write(
            "No files in '/logs/agent' matched include=None "
            "exclude=['opencode.txt', 'opencode/**', 'trajectory.json']; down\n")
        t = TrialView(d)
        assert t.dataset() == "tau2"
        assert t.collection_manifest()[0]["status"] == "ok"
        assert t.find("artifacts", "checker.py") == [os.path.join("artifacts", "app", "checker.py")]
        assert "trajectory.json" in t.collection_excludes()
    print("trial selftest OK")


if __name__ == "__main__":
    _selftest()
