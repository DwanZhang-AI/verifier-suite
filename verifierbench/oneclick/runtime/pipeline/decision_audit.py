"""Persist untrusted verifier explanations outside its sandbox, never as labels."""
import hashlib
import json
import os
from pathlib import Path


def persist(root, task, candidate, payload, status, error):
    # Hash the identity rather than accepting path components from input files.
    identity = hashlib.sha256(json.dumps([task, candidate]).encode()).hexdigest()
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = root / (identity + '.json')
    raw = (json.dumps({"task": task, "candidate": candidate,
                      "execution_status": status, "execution_error": error,
                      "verifier_payload_untrusted": payload},
                     sort_keys=True, ensure_ascii=False) + '\n').encode()
    # Reject duplicates/symlinks instead of silently replacing an audit record.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
    return {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}
