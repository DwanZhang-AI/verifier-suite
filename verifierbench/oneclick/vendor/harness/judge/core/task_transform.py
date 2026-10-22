#!/usr/bin/env python3
"""task_transform: turn any Harbor benchmark task into a judge task, reusing Harbor's
native adapters wherever possible.

Harbor's upstream adapters (80+ benchmarks: swebench, tau3-bench, swebench_multilingual,
bfcl, ...) already convert datasets into the standard task layout:

    instruction.md            <- solver instruction (the bug report / task statement)
    task.toml                 <- environment + timeouts + artifacts
    environment/Dockerfile    <- reproducible task environment
    tests/                    <- OFFICIAL grader (answer side!)
    solution/                 <- reference solution (answer side!)

`judgeify()` converts such a task into a CLOSED-BOOK judge task, reusing the environment
verbatim and stripping every answer-side artifact:

    instruction.md   = our verifier CONTRACT + the original task statement as material
    environment/     = copied unchanged (same image, same repo state)
    tests/test.sh    = the dataset's VALIDITY PROBE (build/direction), never the grader
    solution/        = REMOVED
    task.toml        = name suffixed, artifacts -> the verifier product path

The official tests/solution stay scorer-side: the scorer judges the produced verifier
against them after generation. A dataset adapter therefore reduces to: (upstream Harbor adapter)
+ JudgeifySpec(artifact path, probe script, contract text).
"""
from __future__ import annotations

import os
import re
import shutil
import tomllib
from dataclasses import dataclass, field

ANSWER_SIDE = ("solution",)                       # dirs stripped entirely
ANSWER_TEST_FILES = ("config.json",)              # grader payloads inside tests/

# matched-budget metering (paper item 3): the probe runs in-container after the agent,
# the only point where opencode's session storage still exists — harvest token/tool
# usage into the verifier payload. Schema-tolerant: sums any {"tokens":{input,output}}
# and counts tool parts, so opencode version drift degrades to zeros, never crashes.
USAGE_HARVEST_SH = """
# usage harvest (metering channel)
python3 - <<'PYUSAGE' > "$V/usage.json" 2>/dev/null || echo '{}' > "$V/usage.json"
import json, os, glob
tin = tout = calls = 0
for f in (glob.glob('/logs/agent/opencode/xdg-data/opencode/**/*.json', recursive=True)
          or glob.glob(os.path.expanduser('~/.local/share/opencode/**/*.json'), recursive=True)):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    stack = [d]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            t = o.get('tokens')
            if isinstance(t, dict):
                tin += int(t.get('input') or 0)
                tout += int(t.get('output') or 0)
            if o.get('type') == 'tool':
                calls += 1
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)
print(json.dumps({'tokens_in': tin, 'tokens_out': tout, 'tool_calls': calls}))
PYUSAGE
"""


def add_usage_harvest(test_sh: str) -> str:
    """append the metering block after $V exists; idempotent."""
    if "PYUSAGE" in test_sh:
        return test_sh
    marker = 'mkdir -p "$V"'
    if marker in test_sh:
        return test_sh.replace(marker, marker + "\n" + USAGE_HARVEST_SH.strip(), 1)
    return test_sh.rstrip() + "\n" + USAGE_HARVEST_SH


# T1 Phase B — in-container evidence capture (fixed per-run collection).
# Raw streams stay in the container; this block digests them into small files under
# $V/evidence/ which ride the existing verifier download path. Best-effort by
# contract: every command is timeout-guarded and ||true'd — capture must never
# affect the probe verdict or the reward. Dual-runtime (node first, python3
# fallback): some runner images have node but no python3.
EVIDENCE_CAPTURE_SH = """
# --- evidence capture (T1): final state + materials -> the verifier channel ---
# Behaviour streams are NOT parsed here any more (2026-09-04 ruling): harbor
# natively converts each agent's event stream into an ATIF trajectory.json which
# now rides home with the trial — that is the process-lane record. Only a raw
# tail is kept in-container as a crash-forensics fallback.
EV="${V:-/logs/verifier}/evidence"; mkdir -p "$EV"
WROOT=/app; [ -d /testbed ] && WROOT=/testbed
[ -f /logs/agent/opencode.txt ] && timeout 30 tail -c 131072 /logs/agent/opencode.txt \\
    > "$EV/opencode_tail.txt" 2>/dev/null || true
# final.manifest: end-state fingerprint of the workroot (listing + digests, capped)
timeout 120 sh -c "find '$WROOT' -type f -not -path '*/.git/*' 2>/dev/null | head -5000 \\
    | xargs -r sha256sum 2>/dev/null" > "$EV/final_manifest.tsv" 2>/dev/null || true
# final.diff: change set when the workroot is a git repo (SWE-style testbeds)
if [ -d "$WROOT/.git" ]; then
  timeout 120 sh -c "cd '$WROOT' && git diff HEAD 2>/dev/null | head -c 262144" \\
      > "$EV/diff.patch" 2>/dev/null || true
fi
# final.deps: dependency state (small, best-effort)
{ command -v python3 >/dev/null 2>&1 && timeout 60 python3 -m pip freeze 2>/dev/null | head -300;
  command -v node >/dev/null 2>&1 && node --version 2>/dev/null; } > "$EV/deps.txt" 2>/dev/null || true
# storage diagnosis: where do opencode sessions actually live? (usage.json has been
# silently all-zero since genesis — same wrong-path root cause; listing settles it)
{ for H in "$HOME" /root /home/*; do
    [ -d "$H/.local/share/opencode" ] && find "$H/.local/share/opencode" -type f 2>/dev/null | head -60;
  done
  ls -d /root/.opencode /app/.opencode 2>/dev/null
  env | grep -iE "^HOME=|XDG" ; } > "$EV/storage_listing.txt" 2>/dev/null || true
# T5 declaration + task-material export (host-side certificate needs both)
for MF in /app/declaration.json "$WROOT/declaration.json"; do
  [ -f "$MF" ] && cp -f "$MF" "$EV/gen_declaration.json" 2>/dev/null && break
done
for MAT in /app/task_info.json /testbed/ISSUE.md /app/TASK.md /app/CLAIMS.txt; do
  [ -f "$MAT" ] && cp -f "$MAT" "$EV/material_$(basename "$MAT")" 2>/dev/null || true
done
# --- end evidence capture ---
"""


def add_evidence_capture(test_sh: str) -> str:
    """append the T1 capture block after $V exists; idempotent."""
    if "evidence capture (T1)" in test_sh:
        return test_sh
    marker = 'mkdir -p "$V"'
    if marker in test_sh:
        return test_sh.replace(marker, marker + "\n" + EVIDENCE_CAPTURE_SH.strip(), 1)
    return test_sh.rstrip() + "\n" + EVIDENCE_CAPTURE_SH


@dataclass
class JudgeifySpec:
    contract_text: str                            # the verifier product contract
    probe_test_sh: str                            # tests/test.sh content (validity probe)
    artifact_paths: list[str] = field(default_factory=lambda: ["/app/checker.py"])
    agent_timeout_sec: float = 3600.0
    # 1800, not 600: a probe's build step plus the T1 capture block (find+sha256+git
    # diff on full task repos, each timeout-capped) can exceed 600 s, killing the
    # verifier phase before it writes anything. Timeouts are sized to let work
    # finish; they are not an optimization surface.
    verifier_timeout_sec: float = 1800.0
    materials_header: str = "## 任务材料(与解题 agent 所见一致)\n\n"
    extra_files: dict = field(default_factory=dict)   # relpath -> content (e.g. env fragments)
    # materials-in-container mode: some datasets present the task statement to the judge as
    # a FILE in the workdir (SWE: ./ISSUE.md next to the repo), not as instruction text.
    # env_files land under environment/ and dockerfile_append is added to the Dockerfile
    # (COPY/RUN lines); set include_materials_in_instruction=False to keep the instruction
    # contract-only in that mode.
    env_files: dict = field(default_factory=dict)     # relpath under environment/ -> content
    dockerfile_append: str = ""
    include_materials_in_instruction: bool = True


def judgeify(src_task_dir: str, dst_task_dir: str, spec: JudgeifySpec) -> str:
    """Build the judge task at dst from the upstream Harbor task at src. Returns dst.
    Fails loudly if any answer-side artifact would survive (leak guard)."""
    if os.path.exists(dst_task_dir):
        shutil.rmtree(dst_task_dir)
    os.makedirs(dst_task_dir)

    # environment: verbatim reuse (the whole point of riding upstream adapters)
    env_src = os.path.join(src_task_dir, "environment")
    if os.path.isdir(env_src):
        shutil.copytree(env_src, os.path.join(dst_task_dir, "environment"))

    # instruction: contract + original statement as material (unless the statement rides
    # inside the container as a file — SWE's ./ISSUE.md — in which case contract-only)
    orig = ""
    ip = os.path.join(src_task_dir, "instruction.md")
    if os.path.exists(ip):
        orig = open(ip, encoding="utf-8", errors="replace").read()
    if spec.include_materials_in_instruction:
        inst = spec.contract_text.rstrip() + "\n\n" + spec.materials_header + orig.strip() + "\n"
    else:
        inst = spec.contract_text.rstrip() + "\n"
    open(os.path.join(dst_task_dir, "instruction.md"), "w").write(inst)

    # materials-in-container: files under environment/ + Dockerfile additions
    env_dst = os.path.join(dst_task_dir, "environment")
    if spec.env_files or spec.dockerfile_append:
        os.makedirs(env_dst, exist_ok=True)
    for rel, content in spec.env_files.items():
        p = os.path.join(env_dst, rel)
        os.makedirs(os.path.dirname(p) or env_dst, exist_ok=True)
        open(p, "w").write(content)
    if spec.dockerfile_append:
        with open(os.path.join(env_dst, "Dockerfile"), "a") as fh:
            fh.write("\n" + spec.dockerfile_append.strip() + "\n")

    # task.toml: keep environment/timeout knobs, override artifacts + name + verifier budget
    tp = os.path.join(src_task_dir, "task.toml")
    toml = open(tp, encoding="utf-8", errors="replace").read() if os.path.exists(tp) else ""
    toml = re.sub(r'(?m)^name *= *"([^"]+)"', lambda m: f'name = "{m.group(1)}-judge"', toml)
    toml = re.sub(r"(?ms)^artifacts *= *\[.*?\]", "", toml)
    arts = "artifacts = [" + ", ".join(f'"{a}"' for a in spec.artifact_paths) + "]\n"
    toml = arts + toml
    if re.search(r"(?m)^\[agent\]", toml):
        toml = re.sub(r"(?ms)(^\[agent\][^\[]*?^timeout_sec *= *)[0-9.]+",
                      lambda m: m.group(1) + str(spec.agent_timeout_sec), toml)
    # verifier budget: the spec value must actually land in task.toml (otherwise the
    # upstream 600 passes through)
    if re.search(r"(?ms)^\[verifier\][^\[]*?^timeout_sec *= *[0-9.]+", toml):
        toml = re.sub(r"(?ms)(^\[verifier\][^\[]*?^timeout_sec *= *)[0-9.]+",
                      lambda m: m.group(1) + str(spec.verifier_timeout_sec), toml)
    elif re.search(r"(?m)^\[verifier\]\s*(?:#.*)?$", toml):
        toml = re.sub(r"(?m)^(\[verifier\]\s*(?:#.*)?)$",
                      lambda m: m.group(1) + f"\ntimeout_sec = {spec.verifier_timeout_sec}",
                      toml, count=1)
    else:
        toml += f"\n[verifier]\ntimeout_sec = {spec.verifier_timeout_sec}\n"
    tomllib.loads(toml)  # fail before publishing an invalid generated configuration
    open(os.path.join(dst_task_dir, "task.toml"), "w").write(toml)

    # tests/: ONLY the probe (+ the metering harvest, which is measurement not judging)
    td = os.path.join(dst_task_dir, "tests")
    os.makedirs(td)
    open(os.path.join(td, "test.sh"), "w").write(
        add_evidence_capture(add_usage_harvest(spec.probe_test_sh)))
    os.chmod(os.path.join(td, "test.sh"), 0o755)

    for rel, content in spec.extra_files.items():
        p = os.path.join(dst_task_dir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(content)

    # LEAK GUARD: nothing answer-side may exist in the judge task
    for bad in ANSWER_SIDE:
        assert not os.path.exists(os.path.join(dst_task_dir, bad)), f"leak: {bad}/ survived"
    for f in ANSWER_TEST_FILES:
        assert not os.path.exists(os.path.join(dst_task_dir, "tests", f)), f"leak: tests/{f}"
    low = spec.contract_text.lower()
    assert "solve.sh" not in low, "contract text references the reference solution"
    return dst_task_dir


def variant(base_pkg_dir: str, dst_dir: str, instruction_text: str,
            artifact_paths: list[str], probe_test_sh: str) -> str:
    """Stage-variant of an existing judge package: same environment, different
    instruction/artifacts/probe. The staged pipeline uses this to run its exploration
    and synthesis sessions in the byte-identical task environment."""
    if os.path.exists(dst_dir):
        shutil.rmtree(dst_dir)
    shutil.copytree(base_pkg_dir, dst_dir)
    open(os.path.join(dst_dir, "instruction.md"), "w").write(instruction_text)
    tp = os.path.join(dst_dir, "task.toml")
    toml = open(tp, encoding="utf-8", errors="replace").read()
    toml = re.sub(r"(?ms)^artifacts *= *\[.*?\]\n?", "", toml)
    toml = "artifacts = [" + ", ".join(f'"{a}"' for a in artifact_paths) + "]\n" + toml
    open(tp, "w").write(toml)
    ts = os.path.join(dst_dir, "tests", "test.sh")
    open(ts, "w").write(add_evidence_capture(add_usage_harvest(probe_test_sh)))
    os.chmod(ts, 0o755)
    return dst_dir


def _selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "up")
        os.makedirs(os.path.join(src, "environment"))
        os.makedirs(os.path.join(src, "tests"))
        os.makedirs(os.path.join(src, "solution"))
        open(os.path.join(src, "instruction.md"), "w").write("Fix the bug in frobnicate().")
        open(os.path.join(src, "task.toml"), "w").write(
            'schema_version = "1.4"\nartifacts = ["/x"]\n[task]\nname = "bench/t1"\n'
            "[agent]\ntimeout_sec = 999.0\n")
        open(os.path.join(src, "environment", "Dockerfile"), "w").write("FROM x\n")
        open(os.path.join(src, "tests", "test.sh"), "w").write("official grader\n")
        open(os.path.join(src, "tests", "config.json"), "w").write("{}")
        open(os.path.join(src, "solution", "solve.sh"), "w").write("answer\n")
        spec = JudgeifySpec(contract_text="CONTRACT: produce ./checker.py",
                            probe_test_sh="#!/bin/bash\necho probe\n",
                            agent_timeout_sec=3600.0)
        dst = judgeify(src, os.path.join(d, "jt"), spec)
        assert not os.path.exists(os.path.join(dst, "solution"))
        assert not os.path.exists(os.path.join(dst, "tests", "config.json"))
        body = open(os.path.join(dst, "tests", "test.sh")).read()
        assert body.startswith("#!/bin/bash") and "echo probe" in body
        assert "PYUSAGE" in body                      # metering harvest injected
        inst = open(os.path.join(dst, "instruction.md")).read()
        assert "CONTRACT" in inst and "frobnicate" in inst
        toml = open(os.path.join(dst, "task.toml")).read()
        assert 'name = "bench/t1-judge"' in toml
        assert 'artifacts = ["/app/checker.py"]' in toml and '"/x"' not in toml
        assert "timeout_sec = 3600.0" in toml
        assert os.path.exists(os.path.join(dst, "environment", "Dockerfile"))
        # materials-in-container mode
        spec2 = JudgeifySpec(contract_text="CONTRACT ONLY", probe_test_sh="#!/bin/bash\n",
                             env_files={"ISSUE.md": "Fix the bug in frobnicate()."},
                             dockerfile_append="COPY ISSUE.md /testbed/ISSUE.md\nRUN rm -rf /testbed/.git",
                             include_materials_in_instruction=False)
        dst2 = judgeify(src, os.path.join(d, "jt2"), spec2)
        inst2 = open(os.path.join(dst2, "instruction.md")).read()
        assert "frobnicate" not in inst2 and inst2.startswith("CONTRACT ONLY")
        assert open(os.path.join(dst2, "environment", "ISSUE.md")).read().startswith("Fix the bug")
        dk = open(os.path.join(dst2, "environment", "Dockerfile")).read()
        assert dk.endswith("RUN rm -rf /testbed/.git\n") and "COPY ISSUE.md" in dk
    print("task_transform selftest OK")


if __name__ == "__main__":
    _selftest()
