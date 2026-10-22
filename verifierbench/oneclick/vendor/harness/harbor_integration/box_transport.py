#!/usr/bin/env python3
"""Remote command transport used by the base container provider (box_provider).

box_run sends a shell script to a named remote host through a control script and
returns its merged output; _assert_cmd_size guards the command size limit. The
one-click suite never uses this transport: it runs LocalDockerEnvironment, which
replaces it with local bash. Self-contained: stdlib only.
"""
import os
import subprocess

SCRIPTS = "/opt/gavel/box_control"
SCRATCH = os.environ.get("LOOP_RUNTIME", "/opt/gavel/runtime")
STATE_DIR = os.path.join(SCRATCH, "box_state")                # {box}_state.json per host

# Remote command content cap. The API rejects an oversized command with an opaque 400.
# Heavy assets therefore travel via staged files (gzip+base64, chunked, sha-verified) and
# every launch command stays tiny; _assert_cmd_size fires loudly on the driver host before
# any box_run so an oversize never surfaces as that opaque API error. The real cap is ~24KB;
# 20000 keeps a safety margin.
_CMD_MAX = 20000


class BoxTransportError(RuntimeError):
    """A failed CLI invocation; raw diagnostics survive for provenance/repair."""
    def __init__(self, result, box, name):
        self.returncode = result.returncode
        self.stdout = result.stdout or ""
        self.stderr = result.stderr or ""
        self.box, self.command_name = box, name
        super().__init__(
            f"box transport {name} on {box} failed (rc={self.returncode}): "
            + (self.stdout + "\n" + self.stderr)[-2000:])


class BoxRunOutput(str):
    """String-compatible output with the original successful transport record."""
    def __new__(cls, text, result):
        value = str.__new__(cls, text)
        value.returncode = result.returncode
        value.stdout, value.stderr = result.stdout or "", result.stderr or ""
        return value


def checked_output(result, box, name):
    if result.returncode != 0:
        raise BoxTransportError(result, box, name)
    # Strip only the CLI framing before its explicit output delimiter. Never
    # discard user output merely because it contains 'invocation' or 'Warning'.
    stdout = result.stdout or ""
    before, marker, payload = stdout.partition("[output]\n")
    text = payload if marker else stdout
    if result.stderr and not marker:
        text += ("\n" if text and not text.endswith("\n") else "") + result.stderr
    return BoxRunOutput(text.rstrip("\n"), result)


def _assert_cmd_size(script: str, limit: int = _CMD_MAX, what: str = "remote command") -> int:
    """raise on the driver host if a remote command exceeds the content cap. Returns byte length."""
    n = len(script.encode())
    if n >= limit:
        raise RuntimeError(
            f"{what} is {n} bytes (>= {limit} cap): the remote command content limit "
            f"rejects large commands with an opaque API "
            f"400. Stage heavy assets (worker.py, spec.json, prompt, verifier tarballs) via "
            f"stage_files and keep the launch command to existence-asserts + nohup.")
    return n


def box_run(box, script, timeout=60, name="sw", state_file=None):
    """Run `script` on remote host `box` through the control script, with the per-host
    state file parameterized (default box_state/{box}_state.json). Every command is
    size-guarded first so an oversize fails loudly here, never as an opaque API 400."""
    _assert_cmd_size(script, what=f"remote command({name}) to {box}")
    sf = state_file or os.path.join(STATE_DIR, f"{box}_state.json")
    env = dict(os.environ, BOX_STATE_FILE=sf)
    r = subprocess.run(["python3", "box_control.py", "run", "--timeout", str(timeout),
                        "--name", name],
                       input=script, capture_output=True, text=True, cwd=SCRIPTS, env=env,
                       timeout=timeout + 120)
    return checked_output(r, box, name)
