"""Explicit, versioned minimum-repair scope; legacy defaults remain available."""
import collections
import copy
import hashlib
import json
import os
from pathlib import Path

_CACHE = {}


def _load(path):
    """按 (路径, mtime) 缓存 —— active() 是逐候选调用的（score.load 每行一次），
    每次重读 JSON 会把计分拖慢一个量级。改了文件 mtime 就变，缓存自动失效。"""
    try:
        key = (str(path), path.stat().st_mtime_ns)
    except FileNotFoundError:
        return None
    if key not in _CACHE:
        _CACHE[key] = json.loads(path.read_text())
    return _CACHE[key]


# 复用豁免登记在 profile 之外的 `ast_reuse.json`，**不写进 profile.json** ——
# `freeze_regeneration.py` 重建 profile 时把 `ast_reuse` 写成空表，登记在那里
# 会被下一次冻结静默抹掉；抹掉不报错，只是这批题重新被闸挡住。
#
# 与 eligible_tasks() / exclusions() 同风格：显式、可数、可关闭。
# `V4V_NO_AST_REUSE=1` 关闭，供审计附录看「不豁免时是什么结果」。
REGISTERED = collections.Counter()   # 登记了多少格
WAIVED = collections.Counter()       # 实际放行了多少行，按题计


def _merge_ast_reuse(name, inline):
    if os.environ.get("V4V_NO_AST_REUSE") == "1":
        return inline
    extra = _load(Path(__file__).parent / "run_profiles" / name / "ast_reuse.json")
    if not extra:
        return inline
    entries = extra.get("ast_reuse") or {}
    merged = {m: dict(v) for m, v in inline.items()}
    for model, cells in entries.items():
        merged.setdefault(model, {}).update(cells)
    REGISTERED[name] = sum(len(v) for v in entries.values())
    return merged


def reuse_stats():
    """出表时随表打印：登记多少格、实际放行多少行、覆盖多少道题。"""
    return {"registered_cells": dict(REGISTERED),
            "waived_rows": sum(WAIVED.values()),
            "waived_tasks": len(WAIVED),
            "disabled": os.environ.get("V4V_NO_AST_REUSE") == "1"}


def active():
    name = os.environ.get("VGB_REPAIR_PROFILE")
    if not name:
        return None
    # min85-v1-w5400 = 同一批 85 道，但墙钟 5400s / maxTokens 32768。
    # **单独一个 profile id，不改 min85-v1** —— 同一个名字指两套预算会让数字不可复现。
    if name not in ("min85-v1", "min85-v1-w5400", "certfix-v1", "authoring-sensitivity-20260926-v1"):
        raise RuntimeError("Unknown repair profile: " + name)
    if os.environ.get("VGB_ALLOW_LEGACY_RESULTS") == "1":
        raise RuntimeError("Repair profiles cannot use legacy-result bypass")
    track = os.environ.get("VGB_REPAIR_TRACK")
    # codex 是第五个臂（S5），与 oc 同构：同一份 85 道题单、同一个判定合同
    # （prompts_codex.json 的 sha256_contract = 3e9f21b02bdee1bb，与
    # π / OpenClaw / mini-swe / Claude Code 逐字相同，臂间可比就靠这个）。
    if track not in ("primary", "oc", "codex"):
        raise RuntimeError("Set VGB_REPAIR_TRACK=primary, oc or codex")
    data = dict(_load(Path(__file__).parent/"run_profiles"/name/"profile.json"))
    data["ast_reuse"] = _merge_ast_reuse(name, data.get("ast_reuse") or {})
    return data, track


def revisions(default):
    selected = active()
    if not selected:
        return default
    data, track = selected
    result = dict(default)
    # Runtime/certification guards for the full pool are deliberately retained.
    result["required_generation_spec_sha256"] = dict(default.get("required_generation_spec_sha256", {}))
    result["required_generation_spec_sha256"].update(data[track]["spec_hashes"])
    result["required_spec_renderer"] = dict(default.get("required_spec_renderer", {}))
    result["required_spec_renderer"].update({t:data["renderer"] for t in data[track]["spec_hashes"]})
    # A frozen historical profile cannot waive later semantic corrections.
    result["required_generation_spec_sha256"] = dict(result["required_generation_spec_sha256"])
    result["required_generation_spec_sha256"].update(default.get("required_semantic_generation_spec_sha256", {}))
    return result


def fingerprint(manifest):
    """Bind source/file hashes and configuration, allowing interpreter relocation."""
    data = copy.deepcopy(manifest)
    argv = data.get("entrypoint", {}).get("argv", [])
    if argv:
        argv[0] = "<python-interpreter>"
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",", ":"),ensure_ascii=False).encode()).hexdigest()


def reuse_binding(task, manifest):
    selected = active()
    if not selected or selected[1] != "primary":
        return None
    data, _ = selected
    model = manifest.get("harness", {}).get("model")
    entry = data["ast_reuse"].get(model, {}).get(task)
    if entry and fingerprint(manifest) == entry["manifest_fingerprint"]:
        return entry["manifest_fingerprint"]
    return None


def valid_reuse_result(task, row):
    selected = active()
    if not selected or selected[1] != "primary":
        return False
    bound = row.get("generation_reuse_binding")
    ok = bool(bound) and any(entries.get(task, {}).get("manifest_fingerprint") == bound
                             for entries in selected[0]["ast_reuse"].values())
    if ok:
        WAIVED[task] += 1
    return ok


def guard_generation(out, tasks, specs_dir):
    selected = active()
    if not selected:
        return
    data, track = selected
    model = os.environ.get("APP_MODEL")
    lane = os.environ.get("APP_REPAIR_LANE")
    if model not in data["models"] or lane not in data[track]["generation"]:
        raise RuntimeError("Generation model/lane is outside the frozen repair matrix")
    rule = data[track]["generation"][lane]
    expected = rule["tasks_by_model"].get(model, rule.get("tasks", []))
    actual = [t["handle"] for t in tasks]
    if len(actual) != len(set(actual)) or set(actual) != set(expected):
        raise RuntimeError("APP_TASKS differs from the frozen model/lane task list")
    if Path(out).parts[-2:] != (rule["artifact_segment"], model):
        raise RuntimeError("APP_OUT must use the frozen independent segment and model")
    # **`spec_hashes` 按设计只收录「被修订过」的题。** 跨全池的 lane
    # （例如 S6 的 gem，222 道）里大部分题从未修订，登记表里自然没有它们 ——
    # 原来的写法是 `data[track]["spec_hashes"][th]`，直接 KeyError 崩掉，
    # 那是**缺了分支**，不是有意的拒绝。
    #
    # 未登记的题跳过这一项，但**下面那项语义检查照常跑**
    # （`required_semantic_generation_spec_sha256` 来自 input_revisions.json，
    # 对所有题都适用）。而且真正的底线在出表侧：`score.py` 会按
    # `required_generation_spec_sha256` 逐行验，对不上的行拒收。
    # 所以这不是放水，是把「登记表没有」和「登记表对不上」区分开。
    #
    # **显式、可数**：跳过多少道要打印出来。静默跳过和静默通过长得一样。
    unregistered = 0
    for th in actual:
        raw = (Path(specs_dir)/(th+".json")).read_bytes()
        frozen = data[track]["spec_hashes"].get(th)
        if frozen is None:
            unregistered += 1
        elif hashlib.sha256(raw).hexdigest() != frozen:
            raise RuntimeError("Frozen repair spec changed: " + th)
        latest = json.loads(Path(__file__).with_name("input_revisions.json").read_text())
        semantic = latest.get("required_semantic_generation_spec_sha256", {}).get(th)
        if semantic and hashlib.sha256(raw).hexdigest() != semantic:
            raise RuntimeError("Frozen profile predates a semantic task correction: " + th)
    if unregistered:
        print("[guard] %d/%d 道不在 %s 的 spec_hashes 里（未修订题），"
              "已跳过冻结比对；语义检查与出表侧的 hash 闸照常生效"
              % (unregistered, len(actual), track), flush=True)
