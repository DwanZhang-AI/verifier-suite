"""Opaque identity for native AppWorld state; no records or oracle evaluation."""
import hashlib
import json


def fingerprint(model_hashes):
    if not isinstance(model_hashes, dict) or not model_hashes:
        raise RuntimeError("Native AppWorld model hashes unavailable")
    if any(not isinstance(k, str) or type(v) not in (int, str) for k, v in model_hashes.items()):
        raise RuntimeError("Native AppWorld model hashes incomplete")
    return hashlib.sha256(json.dumps(model_hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
