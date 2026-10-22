#!/usr/bin/env python3
"""Collectors — one small object per etype family; the registry pins totality.

Contract per collector:
  - owns a disjoint set of etypes (registry enforces: together they cover all 12,
    no overlap — coverage is total BY CONSTRUCTION, not by convention)
  - for each owned etype: either add records or declare_missing with the concrete
    reason; never silently skip
  - deterministic, read-only w.r.t. the trial's collected files

Phase A operates on what today's collection config already exports. Streams the
config excludes (opencode.txt / trajectory.json) are declared missing WITH the
exclude list as the reason — that declaration is the measured case for Phase B.
"""
from __future__ import annotations

import hashlib
import json
import os

try:
    from .model import ETYPES, EvidenceBundle
    from .trial import TrialView
    from .trace import from_atif
except ImportError:
    from model import ETYPES, EvidenceBundle
    from trial import TrialView
    from trace import from_atif

COLLECTOR_ID = "judge.evidence/0.2"

#: filenames that count as a pre-action snapshot when found among collected files
_BASELINE_NAMES = ("db_before.json", "baseline.json", "base_state.json")

#: process-stream filenames (excluded by today's collection config)
_STREAM_FILES = {"process.action": "trajectory.json",
                 "process.language": "opencode.txt",
                 "process.interaction": "opencode.txt"}


class BaselineCollector:
    etypes = ("baseline.state",)

    def collect(self, t: TrialView, b: EvidenceBundle) -> None:
        hits = [p for n in _BASELINE_NAMES for p in t.find("artifacts", n)]
        if hits:
            for p in hits:
                b.add("baseline.state", p)
            return
        # Only a pre-attempt snapshot can witness t0. Never re-hash the live task
        # package here: a retry or later rebuild may already have changed it.
        reason = "no pre-action artifact or frozen input_snapshot.json; legacy live package is not t0"
        snapshot = t._json("input_snapshot.json")
        if isinstance(snapshot, dict):
            try:
                manifest_path = snapshot["manifest_path"]
                if not os.path.isabs(manifest_path):
                    manifest_path = t.rel(manifest_path)
                with open(manifest_path, "rb") as fh:
                    payload = fh.read()
                if hashlib.sha256(payload).hexdigest() != snapshot.get("sha256"):
                    raise ValueError("snapshot manifest hash mismatch")
                manifest = json.loads(payload)
                if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
                    raise ValueError("snapshot manifest must contain a files array")
            except (OSError, ValueError, KeyError, TypeError) as exc:
                reason = f"frozen input snapshot unavailable or invalid: {exc}"
            else:
                b.add_generated("baseline.state", "initial_state_manifest.json", payload,
                                source="pre-attempt-snapshot", snapshot_sha256=snapshot["sha256"],
                                note="frozen staged package; live in-container runtime state not included")
                return
        b.declare_missing("baseline.state", reason)


class ProcessStreamCollector:
    etypes = ("process.action", "process.language", "process.interaction",
              "process.checkpoint")

    #: Phase-B in-container digests (ride the verifier channel; see task_transform
    #: EVIDENCE_CAPTURE_SH). Raw streams stay in the container by design.
    _DIGESTS = {"process.action": "verifier/evidence/actions.jsonl",
                "process.language": "verifier/evidence/language.txt",
                "process.interaction": "verifier/evidence/streams.json"}

    @staticmethod
    def _digest_nonempty(t: TrialView, path: str, etype: str) -> bool:
        """an empty digest is NOT evidence — presence requires content."""
        try:
            if path.endswith("streams.json"):
                with open(t.rel(path), encoding="utf-8") as fh:
                    s = json.load(fh)
                if not isinstance(s, dict):
                    return False
                if etype == "process.action":
                    return bool(s.get("tool_calls"))
                return bool(s.get("steps") or s.get("turns") or s.get("entries"))
            if path.endswith("actions.jsonl"):
                with open(t.rel(path), encoding="utf-8") as fh:
                    rows = [json.loads(line) for line in fh if line.strip()]
                return any(isinstance(row, dict) and (row.get("tool") or row.get("name")
                                                      or row.get("function_name")) for row in rows)
            with open(t.rel(path), encoding="utf-8", errors="replace") as fh:
                return bool(fh.read().strip())
        except (OSError, ValueError):
            return False

    #: Harbor's own ATIF trajectory — the standard cross-harness behaviour record.
    #: opencode and codex write logs_dir/trajectory.json via populate_context_post_run;
    #: pi does not (harbor's pi.py has no trajectory writer). Pi keeps its own
    #: native session log instead, picked up below.
    #: Preferred over container-side digests when present.
    _ATIF_NAMES = ("trajectory.json",)

    @staticmethod
    def _lanes(t: TrialView, path: str, pi: bool = False) -> dict[str, int]:
        if not pi:
            with open(t.rel(path), encoding="utf-8") as fh:
                parsed = from_atif(json.load(fh))
            return {"process.action": sum(bool(c.name) for c in parsed.calls),
                    "process.language": len(parsed.user_texts) + len(parsed.agent_texts),
                    "process.interaction": len(parsed.user_texts) + len(parsed.agent_texts)
                    + len(parsed.calls) + len(parsed.observations)}
        actions = language = messages = 0
        with open(t.rel(path), encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise ValueError("Pi event is not an object")
                msg = event.get("message")
                if not isinstance(msg, dict) or not msg.get("role"):
                    continue
                messages += 1
                content = msg.get("content")
                if isinstance(content, str):
                    language += int(bool(content.strip()))
                elif isinstance(content, list):
                    language += sum(isinstance(p, dict) and p.get("type") == "text"
                                    and bool(p.get("text")) for p in content)
                    actions += sum(isinstance(p, dict) and p.get("type") in ("toolCall", "tool_call")
                                   and bool(p.get("name")) for p in content)
        return {"process.action": actions, "process.language": language,
                "process.interaction": messages}

    def collect(self, t: TrialView, b: EvidenceBundle) -> None:
        excludes = t.collection_excludes()
        streams = [(p, False) for n in self._ATIF_NAMES
                   for p in t.find("agent", n) + t.find("artifacts", n)]
        streams += [(p, True) for p in t.walk_files("agent")
                    if "/pi/sessions/" in p and p.endswith(".jsonl")]
        available, diagnostics = {}, []
        for path, pi in streams:
            try:
                lanes = self._lanes(t, path, pi)
            except (OSError, ValueError, TypeError, AttributeError, KeyError) as exc:
                diagnostics.append(f"{path}: invalid stream ({type(exc).__name__})")
                continue
            for lane, count in lanes.items():
                if count:
                    available.setdefault(lane, (path, pi, count))
                else:
                    diagnostics.append(f"{path}: {lane} has no observed records")
        for etype, fname in _STREAM_FILES.items():
            if etype in available:
                path, pi, count = available[etype]
                b.add(etype, path, form="pi_native_session" if pi else "atif_trajectory",
                      source="pi-native" if pi else "harbor-native", observed_records=count)
                continue
            digest = self._DIGESTS.get(etype)
            if digest and t.exists(digest) and self._digest_nonempty(t, digest, etype):
                b.add(etype, digest, form="digest", raw_stream=fname)
                continue
            if etype == "process.language" and t.exists(
                    "verifier/evidence/opencode_tail.txt") and self._digest_nonempty(
                    t, "verifier/evidence/opencode_tail.txt", etype):
                b.add(etype, "verifier/evidence/opencode_tail.txt", form="raw_tail")
                continue
            if digest and t.exists(digest):
                b.declare_missing(etype,
                                  f"digest {digest} exists but is empty "
                                  "(stream source not found in container)")
                continue
            # Raw unstructured text supports language only, not typed tool actions.
            hits = (t.find("agent", fname) + t.find("artifacts", fname)
                    if etype == "process.language" else [])
            hits = [p for p in hits if self._digest_nonempty(t, p, etype)]
            if hits:
                for p in hits:
                    b.add(etype, p, stream_file=fname)
            elif any(fname in e for e in excludes):
                b.declare_missing(etype,
                                  f"{fname} explicitly excluded by collection config "
                                  f"(excludes={excludes}); no in-container digest either")
            else:
                b.declare_missing(etype, f"no usable {etype} records in collected streams",
                                  source_diagnostics=diagnostics)
        b.declare_missing("process.checkpoint",
                          "per-step snapshots are not produced by the runner")


class FinalStateCollector:
    etypes = ("final.artifact", "final.diff", "final.manifest")

    def collect(self, t: TrialView, b: EvidenceBundle) -> None:
        files = t.deliverable_files()
        if files:
            for p in files:
                b.add("final.artifact", p)
        else:
            b.declare_missing("final.artifact", "no declared/recognized verifier deliverable collected")
        diffs = [p for p in files if p.endswith((".patch", ".diff"))]
        if t.exists("verifier/evidence/diff.patch"):
            diffs.append("verifier/evidence/diff.patch")
        if diffs:
            for p in diffs:
                b.add("final.diff", p)
        else:
            b.declare_missing("final.diff",
                              "no change-set artifact collected (workroot not a git "
                              "repo, or capture predates Phase B)")
        # end-state fingerprint: prefer the in-container capture (Phase B), and keep
        # the host-side derivation from Harbor's collection manifest alongside
        has_manifest = t.exists("verifier/evidence/final_manifest.tsv")
        if has_manifest:
            b.add("final.manifest", "verifier/evidence/final_manifest.tsv",
                  form="in_container", partial=True,
                  note="capture is capped/best-effort; empty output does not prove empty state")
        cm = t.collection_manifest()
        if cm is not None:
            listing = sorted(({"source": e.get("source"), "type": e.get("type"),
                               "status": e.get("status")}
                              for e in cm if isinstance(e, dict)),
                             key=lambda r: (str(r["source"]), str(r["type"])))
            b.add_generated("final.manifest", "final_manifest.json",
                            json.dumps({"collected": listing}, indent=1,
                                       ensure_ascii=False),
                            derived_from="artifacts/manifest.json")
        elif not has_manifest:
            b.declare_missing("final.manifest", "Harbor collection manifest absent")
        else:
            # Per-source absence does not make an already present type missing.
            for record in b.records:
                if record.etype == "final.manifest":
                    record.meta["missing_sources"] = ["artifacts/manifest.json"]


class EffectsCollector:
    etypes = ("final.container", "final.deps")

    def collect(self, t: TrialView, b: EvidenceBundle) -> None:
        b.declare_missing("final.container",
                          "container-level effects are not captured by the runner")
        if t.exists("verifier/evidence/deps.txt"):
            b.add("final.deps", "verifier/evidence/deps.txt", form="freeze")
        else:
            b.declare_missing("final.deps",
                              "dependency state not captured (capture predates Phase B)")


class NetworkCollector:
    etypes = ("external.network",)

    def collect(self, t: TrialView, b: EvidenceBundle) -> None:
        # partial capture: the provider's runtime stop
        # hook records container interface traffic TOTALS (rx/tx bytes+packets).
        # Totals witness whether/how much network was used — not which hosts.
        sp = MetricsCollector._spool_final(t)
        if sp and sp.get("net"):
            payload = {"totals": sp["net"], "flows": sp.get("net_flows")}
            note = ("interface totals + conntrack dst-ip:port flows"
                    if sp.get("net_flows") else
                    "interface totals only (no conntrack flows visible at stop)")
            b.add_generated("external.network", "network_totals.json",
                            json.dumps(payload, indent=1, sort_keys=True),
                            source="provider-runtime", note=note)
        else:
            b.declare_missing("external.network",
                              "no traffic totals in the runtime spool (VERITAS_RUNTIME "
                              "off or container gone at stop); per-access log never "
                              "captured (allowlist enforced at the environment layer)")


class MetricsCollector:
    etypes = ("derived.metrics",)

    def collect(self, t: TrialView, b: EvidenceBundle) -> None:
        if t.exists("result.json"):
            b.add("derived.metrics", "result.json", source="harbor")
        for extra in ("verifier/usage.json", "verifier/reward.txt"):
            if t.exists(extra):
                b.add("derived.metrics", extra, source="verifier-phase")
        for ri in ("artifacts/runtime-info.json",          # provider-side (VERITAS_RUNTIME)
                   "artifacts/logs/artifacts/runtime-info.json"):  # container /logs mapping
            if t.exists(ri):
                b.add("derived.metrics", ri,
                      source="provider-runtime", note="E5-5: image digest + container id")
                break
        sp = self._spool_final(t)
        if sp is not None:
            b.add_generated("derived.metrics", "sandbox_final.json",
                            json.dumps(sp, indent=1, ensure_ascii=False, sort_keys=True),
                            source="provider-runtime",
                            note="E5-6: final state incl. OOMKilled + exec counters")
        b.add_generated("derived.metrics", "sandbox_info.json",
                        json.dumps(self._sandbox_info(t), indent=1, ensure_ascii=False,
                                   sort_keys=True),
                        source="host-side best-effort",
                        missing_sources=[] if t.exists("result.json") else ["result.json"],
                        note="no image digest; superseded by runtime-info.json when present")

    @staticmethod
    def _spool_final(t: TrialView) -> dict | None:
        """join the provider's host-side final-state spool by trial/session name."""
        import os as _os
        spool = _os.environ.get(
            "VERITAS_RUNTIME_SPOOL",
            "/opt/gavel/runtime/v2_runtime_spool")
        name = str((t.config() or {}).get("trial_name", "")) or _os.path.basename(t.root)
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in name)
        for cand in (f"{safe}.json", f"{safe}__env.json"):   # provider session = trial__env
            p = _os.path.join(spool, cand)
            if _os.path.exists(p):
                try:
                    with open(p, encoding="utf-8") as fh:
                        value = json.load(fh)
                    return value if isinstance(value, dict) else None
                except (OSError, ValueError):
                    return None
        return None

    @staticmethod
    def _sandbox_info(t: TrialView) -> dict:
        """E5-5/6 placeholder from fields the host already knows (config + result).
        Honest about limits: box via name-normalized box_map match, no image digest,
        death inference = exception presence only."""
        cfg = t.config() or {}
        res = t.result() or {}
        env = cfg.get("environment") or {}
        kw = env.get("kwargs") or {}
        agent = cfg.get("agent") or {}
        task_base = str((cfg.get("task") or {}).get("path", "")).rstrip("/").split("/")[-1]
        norm = lambda x: str(x).replace("-", "_")
        box = None
        for k, v in (kw.get("box_map") or {}).items():
            if norm(k) == norm(task_base):
                box = v
                break
        exc = res.get("exception_info") or {}
        return {"provider": env.get("import_path"),
                "box": box,
                "box_note": None if box else "no normalized box_map match",
                "image": None, "image_note": "digest not recorded by provider",
                "agent": {"import_path": (cfg.get("agent") or {}).get("import_path"),
                          "model": agent.get("model_name"),
                          "timeout_sec": agent.get("override_timeout_sec")},
                "exit": {"has_exception": bool(exc),
                         "exception_type": exc.get("exception_type"),
                         "verifier_environment_mode": res.get("verifier_environment_mode")}}


REGISTRY = (BaselineCollector(), ProcessStreamCollector(), FinalStateCollector(),
            EffectsCollector(), NetworkCollector(), MetricsCollector())


def _check_registry() -> None:
    owned = [t for c in REGISTRY for t in c.etypes]
    dupes = {t for t in owned if owned.count(t) > 1}
    missing = set(ETYPES) - set(owned)
    if dupes or missing:
        raise RuntimeError(f"registry not a partition: dupes={sorted(dupes)} "
                           f"missing={sorted(missing)}")


def collect(trial_dir: str) -> str:
    """Run every registered collector over one trial; write evidence_map.json.
    Returns the map path. Idempotent: prior evidence/ output is regenerated."""
    _check_registry()
    t = TrialView(trial_dir)
    b = EvidenceBundle(trial_dir)
    for c in REGISTRY:
        c.collect(t, b)
    return b.write(COLLECTOR_ID)


def _selftest():
    import os, tempfile
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "artifacts", "app"))
        os.makedirs(os.path.join(d, "verifier"))
        json.dump({"id": "t1", "agent_result": {}}, open(os.path.join(d, "result.json"), "w"))
        json.dump([{"source": "/app/checker.py", "type": "file", "status": "ok"}],
                  open(os.path.join(d, "artifacts", "manifest.json"), "w"))
        open(os.path.join(d, "artifacts", "app", "checker.py"), "w").write("code")
        open(os.path.join(d, "verifier", "reward.txt"), "w").write("1.0")
        open(os.path.join(d, "trial.log"), "w").write(
            "exclude=['opencode.txt', 'opencode/**', 'trajectory.json']\n")
        p1 = collect(d)
        m1 = open(p1).read()
        m = json.loads(m1)
        by = {}
        for r in m["records"]:
            by.setdefault(r["etype"], []).append(r)
        assert by["final.artifact"][0]["path"] == "artifacts/app/checker.py"
        _dm_paths = [r.get("path") for r in by["derived.metrics"]]
        assert "result.json" in _dm_paths
        assert "evidence/sandbox_info.json" in _dm_paths      # E5-5/6 placeholder
        assert "excluded by collection config" in by["process.action"][0]["reason"]
        assert by["final.manifest"][0].get("generated") is True
        assert open(collect(d)).read() == m1        # idempotent + deterministic
        # Phase B: in-container digests flip streams/deps/diff to present
        ev = os.path.join(d, "verifier", "evidence")
        os.makedirs(ev)
        open(os.path.join(ev, "streams.json"), "w").write('{"tool_calls":["bash"],"steps":2}')
        open(os.path.join(ev, "actions.jsonl"), "w").write('{"tool":"bash"}')
        open(os.path.join(ev, "language.txt"), "w").write("hello")
        open(os.path.join(ev, "deps.txt"), "w").write("v22")
        open(os.path.join(ev, "final_manifest.tsv"), "w").write("sha  /app/x.py")
        m2 = json.loads(open(collect(d)).read())
        by2 = {}
        for r in m2["records"]:
            by2.setdefault(r["etype"], []).append(r)
        assert by2["process.action"][0]["availability"] == "present" \
            and by2["process.action"][0]["meta"]["form"] == "digest"
        assert by2["process.language"][0]["availability"] == "present"
        assert by2["final.deps"][0]["availability"] == "present"
        assert any(r["meta"].get("form") == "in_container"
                   for r in by2["final.manifest"] if r.get("meta"))
    print("collectors selftest OK")


if __name__ == "__main__":
    _selftest()
