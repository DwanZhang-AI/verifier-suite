"""The metering ledger: one JSON row per proxied request, aggregated per trial.

The ledger is a JSONL file written only by :class:`LedgerWriter` (owned by the
metering proxy) and read by :class:`Ledger`. Every row has exactly the keys in
:data:`ROW_KEYS`:

* ``ts`` -- epoch seconds when the request arrived, rounded to milliseconds.
* ``run_id``, ``trial`` -- the attribution tag of the request URL; both None
  for a request that carried no tag (answered by the proxy, never forwarded).
* ``method``, ``path`` -- the HTTP method and the upstream path, without query.
* ``model`` -- the ``"model"`` value found in the first 4 KiB of the request
  body, or None.
* ``status`` -- the HTTP status the client received; 0 when the client went
  away before any answer.
* ``usage`` -- the last ``"usage": {...}`` object of the response tail, verbatim
  as the upstream sent it, or None.
* ``absorbed_429`` -- upstream 429 answers the proxy waited out and retried.
* ``passed_429`` -- 1 when the client received a 429 (retry budget spent), else 0.
* ``req_bytes``, ``resp_bytes`` -- request body bytes, response body bytes
  passed to the client.
* ``ms`` -- wall-clock milliseconds from arrival to the last byte, including
  the 429 waits.
* ``error`` -- None, or why the proxy could not complete the exchange:
  ``untagged``, ``outside_upstream_base``, ``malformed_body``, ``meter_failed``
  (an earlier ledger write failed; not forwarded, the client got 503),
  ``upstream:<exception type>`` (no upstream response; the client got 502),
  ``upstream_stream:<exception type>`` (the upstream broke off mid-response),
  ``client_disconnected``.

A row is appended once its response has been passed to the client. Rows never
hold request or response headers, so the injected API key cannot reach the
ledger.
"""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..errors import InfraCategory, InfraError

ROW_KEYS = (
    "ts", "run_id", "trial", "method", "path", "model", "status", "usage",
    "absorbed_429", "passed_429", "req_bytes", "resp_bytes", "ms", "error",
)
"""The keys of every ledger row, in the order they are written."""


@dataclass(frozen=True)
class TrialUsage:
    """Token usage, rate-limit and failure counts of one trial, summed over its ledger rows.

    Token fields sum the rows whose ``usage`` carries token counts: prompt
    tokens are ``prompt_tokens`` (chat completions) or ``input_tokens``
    (``/responses``); completion tokens are ``completion_tokens`` or
    ``output_tokens``; total tokens are ``total_tokens``, or prompt plus
    completion tokens when the upstream sent no total. ``usage_missing`` counts
    2xx responses without token counts, so a nonzero value means the token
    fields undercount the trial.

    The last three fields classify requests that got no model answer:
    ``upstream_errors`` the upstream did not answer (the proxy could not reach
    it and answered 502 itself, or the answer broke off mid-stream);
    ``client_errors`` the upstream answered with a 4xx other than 401, 403 and
    429, an answer about the request itself (e.g. 400 for an over-long
    context); ``abandoned_429`` the client went away while the proxy was
    waiting out upstream 429 answers for it.
    """

    requests: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    absorbed_429: int
    passed_429: int
    usage_missing: int
    upstream_errors: int = 0
    client_errors: int = 0
    abandoned_429: int = 0


_EMPTY = TrialUsage(0, 0, 0, 0, 0, 0, 0)
_UPSTREAM_ERRORS = ("upstream:", "upstream_stream:")
_NOT_CLIENT_ERRORS = frozenset({401, 403, 429})


def _count(usage: Mapping[str, Any], *names: str) -> int | None:
    for name in names:
        value = usage.get(name)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _add(total: TrialUsage, row: Mapping[str, Any]) -> TrialUsage:
    usage = row["usage"] if isinstance(row["usage"], dict) else {}
    prompt = _count(usage, "prompt_tokens", "input_tokens")
    completion = _count(usage, "completion_tokens", "output_tokens")
    tokens = _count(usage, "total_tokens")
    counted = not (prompt is None and completion is None and tokens is None)
    if counted and tokens is None:
        tokens = (prompt or 0) + (completion or 0)
    status, error = row["status"], row["error"]
    return TrialUsage(
        requests=total.requests + 1,
        prompt_tokens=total.prompt_tokens + (prompt or 0),
        completion_tokens=total.completion_tokens + (completion or 0),
        total_tokens=total.total_tokens + (tokens or 0),
        absorbed_429=total.absorbed_429 + row["absorbed_429"],
        passed_429=total.passed_429 + row["passed_429"],
        usage_missing=total.usage_missing + int(200 <= status < 300 and not counted),
        upstream_errors=total.upstream_errors + int(
            error is not None and error.startswith(_UPSTREAM_ERRORS)),
        client_errors=total.client_errors + int(
            error is None and 400 <= status < 500 and status not in _NOT_CLIENT_ERRORS),
        abandoned_429=total.abandoned_429 + int(
            error == "client_disconnected" and row["absorbed_429"] > 0),
    )


def _malformed(path: Path, lineno: int, why: str) -> InfraError:
    return InfraError(InfraCategory.METER_UNAVAILABLE,
                      f"{path}:{lineno}: malformed ledger row ({why})")


def _parse_row(path: Path, lineno: int, line: bytes) -> dict[str, Any]:
    try:
        row = json.loads(line)
    except ValueError as exc:
        raise _malformed(path, lineno, "not JSON") from exc
    if not isinstance(row, dict) or set(row) != set(ROW_KEYS):
        raise _malformed(path, lineno, f"expected the keys {', '.join(ROW_KEYS)}")
    for name in ("status", "absorbed_429", "passed_429"):
        if not isinstance(row[name], int) or isinstance(row[name], bool):
            raise _malformed(path, lineno, f"{name} is not an integer")
    if row["error"] is not None and not isinstance(row["error"], str):
        raise _malformed(path, lineno, "error is neither null nor a string")
    if (row["run_id"] is None) != (row["trial"] is None):
        raise _malformed(path, lineno, "run_id and trial must both be set or both be null")
    return row


class Ledger:
    """Reads a ledger file and aggregates it per ``(run_id, trial)``.

    Safe to use while the proxy is still appending: each call reads only the
    bytes added since the previous call, and a trailing line without its
    newline (a row being written) is left for the next call. Any complete line
    that is not a well-formed row, a missing file or a file that shrank raises
    InfraError(METER_UNAVAILABLE): the token accounting is then unusable, never
    silently partial. One instance may be shared between threads.
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        self._offset = 0
        self._lineno = 0
        self._totals: dict[tuple[str, str], TrialUsage] = {}

    @property
    def path(self) -> Path:
        """The ledger file."""
        return self._path

    def trial(self, run_id: str, trial: str) -> TrialUsage:
        """The usage of one trial so far; all zeros when it made no request."""
        with self._lock:
            self._catch_up()
            return self._totals.get((run_id, trial), _EMPTY)

    def _catch_up(self) -> None:
        try:
            with self._path.open("rb") as stream:
                size = os.fstat(stream.fileno()).st_size
                if size < self._offset:
                    raise InfraError(
                        InfraCategory.METER_UNAVAILABLE,
                        f"{self._path} shrank from {self._offset} to {size} bytes while being read",
                    )
                stream.seek(self._offset)
                data = stream.read(size - self._offset)
        except FileNotFoundError as exc:
            raise InfraError(
                InfraCategory.METER_UNAVAILABLE,
                f"no ledger at {self._path}; the metering proxy writing it never started",
            ) from exc
        complete = data.rfind(b"\n") + 1
        for line in data[:complete].split(b"\n")[:-1]:
            self._lineno += 1
            row = _parse_row(self._path, self._lineno, line)
            if row["run_id"] is None:
                continue
            key = (row["run_id"], row["trial"])
            self._totals[key] = _add(self._totals.get(key, _EMPTY), row)
        self._offset += complete


class LedgerWriter:
    """Appends rows to a ledger file; the metering proxy's only way to write it.

    Creates the file and its parent directories. Each row is one ``write``
    call on a descriptor opened with ``O_APPEND``, under a lock, so concurrent
    rows never interleave and a reader sees whole lines.
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(self._path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        self._lock = threading.Lock()

    def write(self, row: Mapping[str, Any]) -> None:
        """Append one row, whose keys must be exactly :data:`ROW_KEYS`; OSError on I/O failure."""
        if set(row) != set(ROW_KEYS):
            raise ValueError(f"a ledger row has exactly the keys {', '.join(ROW_KEYS)}")
        data = (json.dumps({key: row[key] for key in ROW_KEYS}, ensure_ascii=False) + "\n").encode()
        with self._lock:
            view = memoryview(data)
            while view:
                view = view[os.write(self._fd, view):]

    def close(self) -> None:
        """Close the file; later writes raise OSError."""
        with self._lock:
            if self._fd >= 0:
                os.close(self._fd)
                self._fd = -1
