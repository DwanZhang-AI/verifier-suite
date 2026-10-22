"""Lossless, bounded presentation of already-scrubbed public RPC results.

Only tool presentation is paginated. Python verifiers keep the raw ABI.
Pages reference immutable episode-local snapshots; reading them never reruns
candidate code and never refunds a run_public budget.
"""
import hashlib
import json

VERSION = "public-observation-pages-20260926-v1"
MAX_BYTES = 4000


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str).encode()


class ObservationStore:
    def __init__(self):
        self.snapshots = {}

    def present(self, value):
        blob = encoded(value)
        if len(blob) <= MAX_BYTES:
            return value
        key = hashlib.sha256(blob).hexdigest()
        self.snapshots[key] = json.loads(blob)
        return self.page({"response_id": key})

    def page(self, query):
        if set(query) - {"response_id", "path", "offset", "limit"}:
            raise ValueError("Unknown observation query field")
        key = query["response_id"]
        if key not in self.snapshots:
            raise ValueError("Unknown or expired response_id (snapshots last one episode)")
        path = query.get("path", [])
        if not isinstance(path, list) or any(type(k) not in (str, int) for k in path):
            raise ValueError("path must be a list of exact object keys / array indices")
        value = self.snapshots[key]
        for k in path:
            if isinstance(value, list) and (type(k) is not int or k < 0):
                raise ValueError("Array paths require nonnegative integer indices")
            value = value[k]
        offset, limit = query.get("offset", 0), query.get("limit", 20)
        if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("offset >= 0 and 1 <= limit <= 100 required")
        kind = "object" if isinstance(value, dict) else "array" if isinstance(value, list) else "string" if isinstance(value, str) else "scalar"
        out = {"observation_page": VERSION, "response_id": key, "path": path,
               "kind": kind, "offset": offset,
               "read": "inspect({response_id, path, offset, limit}); Python vgb_env returns raw objects"}
        if kind in ("object", "array"):
            entries = list(value.items()) if kind == "object" else list(enumerate(value))
            out.update(total=len(entries), items=[], next_offset=None)
            for k, v in entries[offset:offset + limit]:
                item = {"key": k, "value": v}
                if len(encoded({**out, "items": [*out["items"], item]})) > MAX_BYTES - 100:
                    if out["items"]:
                        break
                    item = {"key": k, "ref": {"response_id": key, "path": [*path, k]},
                            "kind": type(v).__name__}
                    if hasattr(v, "__len__"):
                        item["length"] = len(v)
                if len(encoded({**out, "items": [*out["items"], item]})) > MAX_BYTES - 100:
                    raise ValueError("Observation key/path exceeds page budget")
                out["items"].append(item)
            end = offset + len(out["items"])
            out["next_offset"] = end if end < len(entries) else None
        elif kind == "string":
            # Binary search by encoded bytes: non-ASCII text must not exceed
            # the display limit even when one character occupies many tokens.
            lo, hi = 0, min(len(value) - min(offset, len(value)), MAX_BYTES)
            out.update(total=len(value), text="", next_offset=None)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if len(encoded({**out, "text": value[offset:offset + mid]})) <= MAX_BYTES - 100:
                    lo = mid
                else:
                    hi = mid - 1
            if not lo and offset < len(value):
                raise ValueError("Observation path exceeds page budget")
            out["text"] = value[offset:offset + lo]
            out["next_offset"] = offset + lo if offset + lo < len(value) else None
        else:
            out["value"] = value
        if len(encoded(out)) > MAX_BYTES:
            raise ValueError("Observation metadata exceeds page budget")
        return out
