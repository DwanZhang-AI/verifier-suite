"""Bind generated artifacts to the exact public input that produced them."""
import hashlib
import json
from pathlib import Path


def record(bundle, spec, source_spec=None):
    path = Path(bundle) / "manifest.json"
    data = json.loads(path.read_text())
    from spike_bundle.runner_spec import RENDERER_VERSION
    effective = json.dumps(json.loads(spec),ensure_ascii=False,separators=(",", ":"),sort_keys=True)
    data["generation_inputs"] = {"task_spec_sha256": hashlib.sha256((source_spec or spec).encode("utf-8")).hexdigest(),
                                 "effective_spec_sha256": hashlib.sha256(effective.encode("utf-8")).hexdigest(),
                                 "spec_renderer_version": RENDERER_VERSION}
    if data.get("environment_capabilities"):
        from capabilities.registry import RUNTIME_CONTRACT
        data["generation_inputs"]["generation_environment_contract"] = RUNTIME_CONTRACT
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True))


def _revisions():
    from repair_profile import revisions
    return revisions(json.loads(Path(__file__).with_name("input_revisions.json").read_text()))


def required_hash(task_handle):
    data = _revisions()
    return data["required_generation_spec_sha256"].get(task_handle)


def required_runtime(task_handle):
    data = _revisions()
    return data["required_runtime_contract"].get(task_handle)


def required_renderer(task_handle):
    data = _revisions()
    return data.get("required_spec_renderer", {}).get(task_handle)


def required_generation_environment(task_handle):
    data = _revisions()
    return data.get("required_capability_generation_contract", {}).get(task_handle)


def stale_reason(task_handle, manifest):
    from repair_profile import reuse_binding
    provenance = manifest.get("generation_inputs") or {}
    semantic = _revisions().get("required_semantic_generation_spec_sha256", {}).get(task_handle)
    if semantic and provenance.get("task_spec_sha256") != semantic:
        return "Artifact predates a semantic task contract correction"
    if reuse_binding(task_handle, manifest):
        return None
    expected = required_hash(task_handle)
    if expected and provenance.get("task_spec_sha256") != expected:
        return "Artifact was not regenerated for the revised public task spec"
    renderer = required_renderer(task_handle)
    if renderer and provenance.get("spec_renderer_version") != renderer:
        return "Artifact predates the complete runtime prompt renderer"
    environment = required_generation_environment(task_handle)
    if environment:
        axis = manifest.get("harness", {}).get("scaffold_axis")
        capability = manifest.get("environment_capabilities")
        # S0 deliberately has no execution environment. Missing metadata on
        # other/unknown arms is not evidence of a capability-free generation.
        if not capability and axis != "S0":
            return "Missing capability declaration for an environment-bound task"
        if capability and provenance.get("generation_environment_contract") != environment:
            return "Capability verifier was generated against an unpinned SWE repository image"
    return None

# Sensitivity experiment only: source-bound acceptance of the additive observation/client ABI.
_production_stale_reason = stale_reason
def stale_reason(task_handle, manifest):
    reason = _production_stale_reason(task_handle, manifest)
    if reason != "Capability verifier was generated against an unpinned SWE repository image":
        return reason
    import copy
    from repair_profile import fingerprint
    p = Path(__file__).with_name("experimental_environment_bindings.json")
    bindings = json.loads(p.read_text()) if p.exists() else {}
    bound = bindings.get(fingerprint(manifest))
    if not bound or bound["task"] != task_handle:
        return reason
    env = manifest.get("generation_inputs", {}).get("generation_environment_contract")
    expected = required_generation_environment(task_handle)
    if bound["condition"] != "repaired" or env != expected + "+public-observation-pages-20260926-v1":
        return reason
    probe = copy.deepcopy(manifest)
    probe["generation_inputs"]["generation_environment_contract"] = expected
    return _production_stale_reason(task_handle, probe)
