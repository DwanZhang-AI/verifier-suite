"""Single whole-task exclusion policy for generation, judging and scoring."""
import json
import os
from pathlib import Path

VERSION = "full-upstream-exclusion-20260919-v3"


def exclusions():
    if os.environ.get("V4V_NO_UPSTREAM_DEFECT_FILTER") == "1":
        return {}
    path = Path(__file__).with_name("upstream_defects.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["version"] != VERSION:
        raise ValueError("Upstream exclusion registry version mismatch")
    return {row["task_handle"]: row for row in data["tasks"]}


def excluded(task_handle=None, task_id=None):
    entries = exclusions()
    return task_handle in entries or any(
        row["task_id"] == task_id for row in entries.values())


def repair_blockers():
    """Execution/generation blockers are tracked without changing full membership."""
    path = Path(__file__).with_name("blocked_tasks.json")
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {h: row for row in data.get("pending_repairs", []) for h in row["handles"]}


def blocked():
    """Compatibility: our infrastructure failures never exclude a whole task."""
    return {}


def scoring_excluded(task_handle):
    return task_handle in exclusions()
