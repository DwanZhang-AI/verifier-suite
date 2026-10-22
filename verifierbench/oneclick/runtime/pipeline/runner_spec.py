"""Shared public-spec renderer. Restricted AppWorld data remains in memory."""
import hashlib
import json
import os
from pathlib import Path

SPEC_CHARS = 48000
RENDERER_VERSION = "public-input-contract-20260917-v2"


def appworld_backfill(spec, task_id, root=None):
    root = root or os.environ.get("APPWORLD_ROOT", "")
    p = Path(root) / "data/tasks" / task_id / "specs.json"
    if not root or not p.is_file():return None
    d = json.loads(p.read_text())
    if not (d.get("instruction") or "").strip():return None
    sup = d.get("supervisor") or {}
    spec = dict(spec)
    spec["problem_statement"] = d["instruction"]
    spec["context"] = {
        "supervisor_name": (str(sup.get("first_name", ""))+" "+str(sup.get("last_name", ""))).strip(),
        "supervisor_email": sup.get("email", ""),
        "supervisor_phone": sup.get("phone_number", ""),
        "datetime": d.get("datetime", "")}
    docs = Path(root)/"data/api_docs/standard"
    allowed = d.get("allowed_apps") or [p.stem for p in sorted(docs.glob("*.json")) if p.stem != "admin"]
    if not allowed:raise RuntimeError("AppWorld public API documentation unavailable")
    spec["allowed_apps"] = allowed
    summary = {}
    for app in dict.fromkeys(["api_docs", *allowed]):
        q = docs/(app+".json")
        if not q.is_file():raise RuntimeError("Missing public API docs for " + app)
        apis = json.loads(q.read_text())
        entries=[]
        for name, doc in apis.items():
            params = doc.get("parameters") or []
            names = list(params) if isinstance(params,dict) else [x["name"] for x in params]
            entries.append(name+"("+", ".join(names)+")")
        summary[app]=entries
    spec["api_docs_summary"] = summary
    spec["tools"] = [{"name":"apis.api_docs.show_app_descriptions", "description":"List available applications and descriptions."},
                     {"name":"apis.api_docs.show_api_descriptions", "description":"Discover APIs of an application."},
                     {"name":"apis.api_docs.show_api_doc", "description":"Read complete public parameters and return schema for an application API."}]
    spec["api_usage"] = "Candidate programs call apis.<app>.<endpoint>(...). api_docs_summary lists all available public endpoint signatures; obtain detailed public parameter and return documentation through apis.api_docs. Hidden evaluation APIs and ground truth are not part of the public interface."
    return spec


def render(spec, task_id, benchmark, note):
    if benchmark == "AppWorld":
        spec = appworld_backfill(spec, task_id)
        if spec is None:raise RuntimeError("AppWorld runtime public task data missing; refusing placeholder generation")
    text = (spec.get("problem_statement") or "").strip()
    if not text or text.startswith("Judge whether a candidate solution"):
        raise RuntimeError(str(task_id)+": placeholder problem statement; refusing generation")
    # Compact JSON keeps every public field within the prompt budget. Never cut
    # JSON at a character boundary: a half schema silently changes the task.
    s = json.dumps(spec, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    note.update(spec_chars=len(s), spec_truncated=False, spec_renderer_version=RENDERER_VERSION,
                effective_spec_sha256=hashlib.sha256(s.encode()).hexdigest())
    if len(s)>SPEC_CHARS:
        raise RuntimeError(f"Public task spec has {len(s)} chars, exceeds {SPEC_CHARS}; explicit schema compaction required")
    return s


def spec_text(specs_dir, th, task_id, benchmark, note):
    raw = (Path(specs_dir)/(th+".json")).read_bytes()
    note["task_spec_sha256"] = hashlib.sha256(raw).hexdigest()
    return render(json.loads(raw),task_id,benchmark,note)


def record_manifest(work, note):
    path=Path(work)/"manifest.json"
    data=json.loads(path.read_text())
    data["generation_inputs"]={k:note[k] for k in ("task_spec_sha256","effective_spec_sha256","spec_renderer_version") if k in note}
    if note.get("authoring_runtime") or note.get("public_observation_v2"):
        data["generation_inputs"]["experimental_runtime"] = {k: note[k] for k in
            ("authoring_runtime", "authoring_client_sha256", "public_observation_v2",
             "authoring_instructions_sha256") if k in note}
    if data.get("environment_capabilities"):
        from capabilities.registry import RUNTIME_CONTRACT
        data["generation_inputs"]["generation_environment_contract"] = RUNTIME_CONTRACT
    path.write_text(json.dumps(data,ensure_ascii=False,indent=1,sort_keys=True))


def assert_generation_allowed():
    root=Path(__file__).resolve().parent
    if root.name == "spike_bundle":root=root.parent
    policy=root/"execution_policy.json"
    import os as _os
    pol=json.loads(policy.read_text()) if policy.exists() else {}
    if pol.get("generation_allowed"):
        sc=pol.get("generation_scope") or {}
        if sc:
            prof=_os.environ.get("VGB_REPAIR_PROFILE")
            lane=_os.environ.get("APP_REPAIR_LANE")
            mod=_os.environ.get("APP_MODEL")
            if (prof!=sc.get("profile") or lane not in sc.get("lanes",[])
                    or mod not in sc.get("models",[])):
                raise RuntimeError("GENERATION_OUT_OF_SCOPE: %s/%s/%s"%(prof,lane,mod))
        return
    paused=(root/"PAUSE_REPAIR_RUNS").exists()
    if policy.exists():paused=paused or pol.get("mode")=="repair_only"
    if paused:
        raise RuntimeError("PAUSED_BY_USER: repair only; generation is disabled")


def validate_frozen_inputs(tasks, specs_dir):
    root=Path(__file__).resolve().parent
    if root.name == "spike_bundle":root=root.parent
    freeze=root/"generation_input_freeze.json"
    if not freeze.exists():
        raise RuntimeError("Audited public input freeze missing: " + str(freeze))
    members=json.loads(freeze.read_text())["tasks"]
    for task in tasks:
        th=task["handle"]
        expected=members.get(th)
        if expected is None:
            raise RuntimeError("Task outside the audited generation pool: " + th)
        if task["instance_id"]!=expected["task_id"] or task["benchmark"]!=expected["benchmark"]:
            raise RuntimeError("Task identity differs from the audited input: " + th)
        note={}
        spec_text(specs_dir, th, task["instance_id"], task["benchmark"], note)
        for field in ("task_spec_sha256", "effective_spec_sha256"):
            if note[field]!=expected[field]:
                raise RuntimeError("Public input differs from the audited freeze: " + th + ": " + field)


def guard_output_directory(out, tasks, specs_dir):
    """Do not overwrite or silently resume artifacts generated from stale inputs."""
    assert_generation_allowed()
    from repair_profile import guard_generation
    guard_generation(out, tasks, specs_dir)
    validate_frozen_inputs(tasks, specs_dir)
    from pool_policy import excluded
    from generation_provenance import stale_reason
    for task in tasks:
        th=task["handle"]
        if excluded(th,task.get("instance_id")):continue
        mf=Path(out)/th/"manifest.json"
        if not mf.exists():continue
        manifest=json.loads(mf.read_text())
        provenance=manifest.get("generation_inputs") or {}
        expected=hashlib.sha256((Path(specs_dir)/(th+".json")).read_bytes()).hexdigest()
        if provenance.get("task_spec_sha256")!=expected or provenance.get("spec_renderer_version")!=RENDERER_VERSION:
            raise RuntimeError("APP_OUT contains historical artifacts; choose a new repair-v2 segment instead of overwriting: " + str(out))
        # Runtime-only AppWorld task/API data can change without changing the
        # placeholder file. Compare the actual rendered input before resuming.
        note={}
        spec_text(specs_dir, th, task["instance_id"], task["benchmark"], note)
        if provenance.get("effective_spec_sha256") != note["effective_spec_sha256"]:
            raise RuntimeError("APP_OUT effective public input changed: " + th)
        reason=stale_reason(th, manifest)
        if reason:
            raise RuntimeError("APP_OUT artifact is stale: " + th + ": " + reason)


# Claude Code discovers CLAUDE.md / AGENTS.md by walking up from its cwd, and
# the driver runs it with `cwd=APP_OUT/<handle>`.  Measured 2026-09-22 with an
# identical 2-token prompt and `--tools ""`:
#
#     cwd=/tmp                          cache_creation =    531
#     cwd=<repo>/vgb_container/work/…   cache_creation = 29,620   ($0.2973)
#
# The 29k difference is this project's own CLAUDE.md -- which carries the
# scoring口径, the four gate conditions and the upstream-defect task ids --
# being pushed into the *generating* model's context.  On a benchmark about
# writing verifiers that is answer leakage, not a budget line.
#
# Fail closed, same direction as cc_gate: a contaminated run writes artifacts
# that look entirely normal and score wrong.  The escape hatch exists so the
# audit appendix can reproduce a contaminated run on purpose, never so a real
# run can get past this.
AMBIENT_CONTEXT_NAMES = ("CLAUDE.md", "AGENTS.md")


def ambient_context_files(out):
    """Every CLAUDE.md / AGENTS.md Claude Code would pick up for cwd=out/<handle>."""
    found = []
    for d in [Path(out).resolve(), *Path(out).resolve().parents]:
        for name in AMBIENT_CONTEXT_NAMES:
            p = d / name
            if p.is_file():
                found.append(p)
    return found


def guard_no_ambient_context(out):
    """Refuse to generate from a work root that leaks project context into the model."""
    if os.environ.get("VGB_ALLOW_AMBIENT_CONTEXT") == "1":
        print("[ambient-context] WAIVED by VGB_ALLOW_AMBIENT_CONTEXT=1 -- "
              "artifacts from this run carry project context and are audit-only")
        return []
    found = ambient_context_files(out)
    if found:
        raise RuntimeError(
            "APP_OUT sits under project context files that Claude Code will read "
            "into every task's system prompt (answer leakage, ~29k tokens/call). "
            "Move the work root outside them, e.g. APP_OUT=/opt/vgb_run/... : "
            + ", ".join(str(p) for p in found))
    print("[ambient-context] clean: no CLAUDE.md/AGENTS.md above " + str(out))
    return []
