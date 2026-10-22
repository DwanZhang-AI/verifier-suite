"""judge.evidence — the T1 fixed evidence-collection protocol (harness-side).

After every agent run the harness produces evidence_map.json: a TOTAL account of
the run's observable record over the 12 evidence types — each either present
(verifiable file references) or missing_declared (concrete reason). Collectors are
registered per etype family; the registry is pinned to be a partition of all 12,
so coverage is total by construction.

Public API:
    collect(trial_dir)   -> path of the written evidence_map.json
    load_map(trial_dir)  -> the parsed map
    coverage(maps)       -> per-etype aggregate table
"""
from .model import ETYPES, PROTOCOL_VERSION, EvidenceBundle, load_map, coverage  # noqa: F401
from .collectors import collect, REGISTRY, COLLECTOR_ID                           # noqa: F401
