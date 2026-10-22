"""Host-side metering proxy between generation containers and the model endpoint.

Port of the upstream harness's metering proxy: stdlib only, no
model logic. Each request is forwarded to one configured upstream and recorded
as one ledger row (see :mod:`gavel_harness.meter.ledger`). Streaming (SSE)
responses are passed through as the bytes arrive; usage is parsed from a
rolling 64 KiB tail of the response (chat completions: the ``stream_options``
usage chunk or the final chunk; ``/responses``: the ``response.completed``
event), the last ``"usage": {...}`` object winning.

Kept from upstream: the ``/t/<tag>`` path attribution, the forwarded request
headers (``Accept-Encoding: identity`` keeps usage parseable), the response
framing (the upstream's ``Content-Length``, else chunked; always
``Connection: close``) and the 900 s upstream timeout. Added:

* Any upstream ``scheme://host[:port][/base/path]``. Clients address the
  upstream's own paths behind the tag ``/t/<run_id>/<trial>`` (see
  :func:`tagged_base_url`); the tag is stripped and the rest is forwarded
  unchanged. A request without a tag, or for a path outside the upstream's base
  path, is answered 404 by the proxy and never forwarded.
* Host-side key injection: the client's ``Authorization`` header (a
  placeholder) is replaced by ``Bearer <key>``, the key being the value of the
  environment variable ``api_key_env`` read when the proxy is constructed. The
  key is never written to the ledger, a log record, an error response or an
  exception message.
* Per-request 429 absorption: an upstream 429 is drained and the request is
  re-sent after the wait the ``Retry-After`` header asks for (delay-seconds or
  HTTP-date), or ``15 s * 2**k`` before the k-th retry when there is none; the
  wait is capped at ``max_wait_sec`` and multiplied by a uniform jitter in
  [0.75, 1.25]. After ``max_429_retries`` retries the next 429 reaches the
  client and counts as ``passed_429``. Other statuses (5xx included) pass
  through unretried.
"""

from __future__ import annotations

import email.utils
import http.client
import http.server
import json
import logging
import os
import random
import re
import socketserver
import ssl
import sys
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path
from types import TracebackType
from typing import Any
from urllib.parse import urlsplit

from ..config import DEFAULT_METER_PORT
from ..errors import ConfigError, InfraCategory, InfraError
from .ledger import Ledger, LedgerWriter

RESERVED_PORTS: Mapping[int, str] = {
    8877: "the upstream harness's metering proxy",
    8899: "the LiteLLM bridge",
}
"""Ports the proxy refuses: services of the upstream harness that may share the host."""
HEALTH_PATH = "/_meter/health"
"""``GET`` here answers 200 with the upstream URL; used to check that containers reach the proxy."""
UPSTREAM_TIMEOUT_SEC = 900.0
"""Socket timeout of one upstream exchange (connect, and each read)."""
BACKOFF_BASE_SEC = 15.0
"""Wait before the first retry of a 429 without ``Retry-After``; doubles per retry."""
MAX_WAIT_SEC = 300.0
"""Default cap of one 429 wait, ``Retry-After`` included, before jitter."""
JITTER = 0.25
"""Each 429 wait is multiplied by a uniform draw from [1 - JITTER, 1 + JITTER]."""

_TAIL_BYTES = 65536
_READ_BYTES = 8192
_SHUTDOWN_POLL_SEC = 0.1
_SEGMENT = r"[A-Za-z0-9_:-][A-Za-z0-9_.:-]*"
_SEGMENT_RE = re.compile(_SEGMENT)
_TAG = re.compile(rf"/t/({_SEGMENT})/({_SEGMENT})(/.*)?")
_USAGE_RE = re.compile(rb'"usage"\s*:\s*(\{(?:[^{}]|\{[^{}]*\})*\})')
_MODEL_RE = re.compile(rb'"model"\s*:\s*"([^"]+)"')
_DELAY_SECONDS = re.compile(r"\d+(\.\d+)?")
_ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_KEY = re.compile(r"[\x21-\x7e]+")
_DROPPED_REQUEST_HEADERS = frozenset({
    "host", "content-length", "connection", "accept-encoding", "transfer-encoding",
    "keep-alive", "authorization", "proxy-authorization", "te", "trailer", "upgrade",
})
_PASSED_RESPONSE_HEADERS = frozenset({"content-type", "x-request-id", "retry-after"})
_LOG = logging.getLogger(__name__)


def tagged_base_url(gateway: str, port: int, run_id: str, trial: str, upstream_path: str) -> str:
    """``http://<gateway>:<port>/t/<run_id>/<trial><upstream_path>``: one trial's base URL.

    ``gateway`` is the proxy's address as the client sees it (an IPv6 address
    is bracketed). ``run_id`` and ``trial`` must match
    ``[A-Za-z0-9_:-][A-Za-z0-9_.:-]*`` so the proxy can read them back.
    ``upstream_path`` is the upstream's base path (:attr:`MeterProxy.upstream_path`):
    empty, or absolute without a trailing slash.
    """
    for name, value in (("run_id", run_id), ("trial", trial)):
        if not _SEGMENT_RE.fullmatch(value):
            raise ConfigError(f"{name} {value!r} cannot be a meter tag: use "
                              "[A-Za-z0-9_.:-], not starting with '.'")
    if upstream_path and (not upstream_path.startswith("/") or upstream_path.endswith("/")):
        raise ConfigError("upstream_path must be empty or absolute without a trailing slash, "
                          f"got {upstream_path!r}")
    if not gateway or any(char in gateway for char in "/ \t"):
        raise ConfigError(f"gateway must be a host name or address, got {gateway!r}")
    host = f"[{gateway}]" if ":" in gateway and not gateway.startswith("[") else gateway
    return f"http://{host}:{port}/t/{run_id}/{trial}{upstream_path}"


def retry_after_seconds(value: str | None, *, now: float) -> float | None:
    """Seconds a ``Retry-After`` header value asks to wait, or None when absent or unreadable.

    Reads delay-seconds (digits, optionally with a fraction) and HTTP-dates; a
    date at or before ``now`` (epoch seconds) gives 0.
    """
    if value is None:
        return None
    text = value.strip()
    if _DELAY_SECONDS.fullmatch(text):
        return float(text)
    try:
        when = email.utils.parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return max(0.0, when.timestamp() - now)


@dataclass(frozen=True)
class MeterEndpoint:
    """What the run layer needs to tag trials, read their usage and watch the proxy."""

    gateway: str
    """Address containers use to reach the proxy."""
    port: int
    upstream_path: str
    """The upstream's base path (e.g. ``/api/v3``), following the ``/t/<run>/<trial>`` tag."""
    ledger: Ledger
    check: Callable[[], None]
    """Raises InfraError(METER_UNAVAILABLE) once the proxy stopped metering
    (:meth:`MeterProxy.check`); the run layer calls it while and after every job."""


def _read_key(name: str) -> str:
    if not _ENV_NAME.fullmatch(name):
        raise ConfigError(f"api_key_env must name an environment variable, got {name!r}")
    value = os.environ.get(name)
    if value is None:
        raise ConfigError(f"environment variable {name} is not set; "
                          "the metering proxy injects the API key from it")
    if not _KEY.fullmatch(value):
        raise ConfigError(f"the value of {name} must be non-empty printable ASCII without "
                          "whitespace (the value is not shown)")
    return value


class MeterProxy:
    """The metering proxy: a stdlib HTTP server on a background thread, one thread per connection.

    ``upstream`` is ``http(s)://host[:port][/base/path]`` without credentials,
    query or fragment. ``ledger`` is the JSONL file rows are appended to.
    ``host``/``port`` is the listening address; port 0 picks a free port, and
    ports in :data:`RESERVED_PORTS` are refused. ``max_429_retries`` is the
    per-request retry budget for upstream 429s, ``max_wait_sec`` caps one wait.
    ``sleep`` and ``rng`` perform the waits and draw the jitter (injectable for
    tests). Construction fails with ConfigError when the key variable is unset
    or unusable. :meth:`stop` does not wait for in-flight requests.

    Whoever reaches the listening address can spend the injected key: on a host
    reachable from untrusted networks, bind ``host`` to the address containers
    use, or firewall the port.
    """

    def __init__(
        self,
        *,
        upstream: str,
        api_key_env: str,
        ledger: Path,
        host: str = "0.0.0.0",
        port: int = DEFAULT_METER_PORT,
        max_429_retries: int = 12,
        max_wait_sec: float = MAX_WAIT_SEC,
        upstream_timeout_sec: float = UPSTREAM_TIMEOUT_SEC,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
    ) -> None:
        if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
            raise ConfigError(f"port must be an integer in 0..65535, got {port!r}")
        if port in RESERVED_PORTS:
            raise ConfigError(f"port {port} is reserved for {RESERVED_PORTS[port]}; choose another")
        retries = max_429_retries
        if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
            raise ConfigError(f"max_429_retries must be a non-negative integer, got {retries!r}")
        for name, value in (("max_wait_sec", max_wait_sec),
                            ("upstream_timeout_sec", upstream_timeout_sec)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                raise ConfigError(f"{name} must be a positive number of seconds, got {value!r}")
        parts = urlsplit(upstream)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ConfigError(f"upstream must be an http(s) URL with a host, got {upstream!r}")
        if parts.username is not None or parts.password is not None:
            raise ConfigError("upstream must not carry credentials; the key comes from api_key_env")
        if parts.query or parts.fragment:
            raise ConfigError(f"upstream must not carry a query or fragment, got {upstream!r}")
        try:
            upstream_port = parts.port
        except ValueError as exc:
            raise ConfigError(f"upstream has an invalid port: {upstream!r}") from exc
        self._authorization = f"Bearer {_read_key(api_key_env)}"
        self._upstream_host = parts.hostname
        self._upstream_port = upstream_port
        self._upstream_path = parts.path.rstrip("/")
        self._upstream = f"{parts.scheme}://{parts.netloc}{self._upstream_path}"
        self._ssl = ssl.create_default_context() if parts.scheme == "https" else None
        self._ledger_path = Path(ledger)
        self._host = host
        self._port = port
        self._max_429_retries = max_429_retries
        self._max_wait = float(max_wait_sec)
        self._timeout = float(upstream_timeout_sec)
        self._sleep = sleep
        self._rng = rng if rng is not None else random.Random()
        self._server: _Server | None = None
        self._thread: threading.Thread | None = None
        self._writer: LedgerWriter | None = None
        self._failure: str | None = None

    @property
    def port(self) -> int:
        """The listening port: the bound one while running, else the requested one (0 = any)."""
        if self._server is not None:
            return self._server.server_address[1]
        return self._port

    @property
    def upstream(self) -> str:
        """The upstream as ``scheme://host[:port]/base/path``, without a trailing slash."""
        return self._upstream

    @property
    def upstream_path(self) -> str:
        """The upstream's base path, empty or absolute without a trailing slash."""
        return self._upstream_path

    @property
    def ledger_path(self) -> Path:
        """The ledger file this proxy appends to."""
        return self._ledger_path

    def endpoint(self, gateway: str) -> MeterEndpoint:
        """The run layer's handle on this proxy, for clients that reach it at ``gateway``."""
        return MeterEndpoint(gateway=gateway, port=self.port, upstream_path=self._upstream_path,
                             ledger=Ledger(self._ledger_path), check=self.check)

    def start(self) -> None:
        """Open the ledger, bind the listening socket and serve on a daemon thread.

        Raises ConfigError when already running or when the address cannot be bound.
        """
        if self._server is not None:
            raise ConfigError("the metering proxy is already running")
        try:
            writer = LedgerWriter(self._ledger_path)
        except OSError as exc:
            raise ConfigError(
                f"cannot open the ledger {self._ledger_path}: {exc.strerror}"
            ) from exc
        try:
            server = _Server((self._host, self._port), _Handler)
        except OSError as exc:
            writer.close()
            raise ConfigError(
                f"the metering proxy cannot listen on {self._host}:{self._port}: {exc.strerror}"
            ) from exc
        server.meter = self
        self._writer, self._server, self._failure = writer, server, None
        self._thread = threading.Thread(
            target=server.serve_forever, kwargs={"poll_interval": _SHUTDOWN_POLL_SEC},
            name=f"veritas-meter:{self.port}", daemon=True,
        )
        self._thread.start()
        _LOG.info("metering proxy listening on %s:%d -> %s, ledger %s",
                  self._host, self.port, self._upstream, self._ledger_path)

    def stop(self) -> None:
        """Stop serving and close the ledger. Idempotent."""
        server, thread, writer = self._server, self._thread, self._writer
        self._server = self._thread = self._writer = None
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join()
        if writer is not None:
            writer.close()

    def check(self) -> None:
        """Raise InfraError(METER_UNAVAILABLE) when the proxy stopped metering.

        That is the case after a ledger write failed (from then on every
        request is answered 503 and not forwarded, so nothing goes unmetered)
        or when the serving thread is gone while the proxy should be running.
        """
        if self._failure is not None:
            raise InfraError(InfraCategory.METER_UNAVAILABLE, self._failure)
        if self._server is None or self._thread is None or not self._thread.is_alive():
            raise InfraError(InfraCategory.METER_UNAVAILABLE, "the metering proxy is not running")

    def __enter__(self) -> MeterProxy:
        self.start()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None,
                 tb: TracebackType | None) -> None:
        self.stop()

    def _record(self, row: dict[str, Any]) -> None:
        writer = self._writer
        try:
            if writer is None:
                raise OSError("the ledger is closed")
            writer.write(row)
        except OSError as exc:
            self._failure = (
                f"ledger {self._ledger_path} is not writable: {type(exc).__name__}: {exc}"
            )
            _LOG.error("metering proxy stopped forwarding: %s", self._failure)

    def _connect(self) -> http.client.HTTPConnection:
        if self._ssl is not None:
            return http.client.HTTPSConnection(self._upstream_host, self._upstream_port,
                                               timeout=self._timeout, context=self._ssl)
        return http.client.HTTPConnection(self._upstream_host, self._upstream_port,
                                          timeout=self._timeout)

    def _under_base(self, path: str) -> bool:
        base = self._upstream_path
        return not base or path == base or path.startswith(base + "/")

    def _wait_429(self, retry_after: str | None, retry: int) -> float:
        wait = retry_after_seconds(retry_after, now=time.time())
        if wait is None:
            wait = BACKOFF_BASE_SEC * 2 ** retry
        return min(wait, self._max_wait) * self._rng.uniform(1 - JITTER, 1 + JITTER)


class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    # Concurrent trials connect in bursts; the default listen backlog of 5 resets
    # connections on hosts that do not round it up.
    request_queue_size = 128
    meter: MeterProxy

    def handle_error(self, request: Any, client_address: Any) -> None:
        # Only the exception type is logged: a message could quote a header value.
        _LOG.error("metering proxy: %s while serving %s",
                   type(sys.exception()).__name__, client_address)


class _Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server: _Server

    def log_message(self, format: str, *args: Any) -> None:
        """Silenced: the ledger is the record of every request."""

    def do_GET(self) -> None:
        self._proxy()

    def do_POST(self) -> None:
        self._proxy()

    def _read_body(self) -> bytes:
        if "chunked" in self.headers.get("Transfer-Encoding", "").lower():
            parts = []
            while size := int(self.rfile.readline().split(b";", 1)[0], 16):
                parts.append(self.rfile.read(size))
                self.rfile.readline()
            while self.rfile.readline() not in (b"\r\n", b"\n", b""):
                pass
            return b"".join(parts)
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def _answer(self, status: int, payload: Mapping[str, Any]) -> int:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)
        return len(data)

    def _refuse(self, status: int, message: str) -> int:
        return self._answer(status, {"error": {"message": message, "type": "veritas_meter"}})

    def _proxy(self) -> None:
        meter = self.server.meter
        t0 = time.time()
        path, sep, query = self.path.partition("?")
        if self.command == "GET" and path == HEALTH_PATH:
            self._answer(200, {"service": "veritas-meter", "upstream": meter.upstream})
            return
        row: dict[str, Any] = {
            "ts": round(t0, 3), "run_id": None, "trial": None, "method": self.command,
            "path": path, "model": None, "status": 0, "usage": None, "absorbed_429": 0,
            "passed_429": 0, "req_bytes": 0, "resp_bytes": 0, "ms": 0, "error": None,
        }
        tag = _TAG.fullmatch(path)
        if tag is not None:
            row.update(run_id=tag.group(1), trial=tag.group(2), path=tag.group(3) or "/")
        try:
            try:
                body = self._read_body()
            except ValueError:
                row.update(status=400, error="malformed_body")
                row["resp_bytes"] = self._refuse(400, "malformed request body")
                return
            row["req_bytes"] = len(body)
            model = _MODEL_RE.search(body[:4096])
            if model:
                row["model"] = model.group(1).decode(errors="replace")
            if meter._failure is not None:
                row.update(status=503, error="meter_failed")
                row["resp_bytes"] = self._refuse(503, "the metering proxy cannot write its ledger")
            elif tag is None:
                row.update(status=404, error="untagged")
                row["resp_bytes"] = self._refuse(
                    404, "request path carries no /t/<run_id>/<trial> tag")
            elif not meter._under_base(row["path"]):
                row.update(status=404, error="outside_upstream_base")
                row["resp_bytes"] = self._refuse(
                    404, f"path is outside the upstream base {meter.upstream_path}")
            else:
                self._forward(meter, row, row["path"] + sep + query, body)
        except OSError:
            row["error"] = row["error"] or "client_disconnected"
        finally:
            row["ms"] = round((time.time() - t0) * 1000)
            meter._record(row)

    def _forward(self, meter: MeterProxy, row: dict[str, Any], target: str, body: bytes) -> None:
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in _DROPPED_REQUEST_HEADERS}
        headers["Accept-Encoding"] = "identity"     # keep usage parseable
        headers["Authorization"] = meter._authorization
        absorbed = 0
        while True:
            conn = meter._connect()
            try:
                conn.request(self.command, target, body=body or None, headers=headers)
                resp = conn.getresponse()
                if resp.status != 429 or absorbed >= meter._max_429_retries:
                    break
                retry_after = resp.getheader("Retry-After")
                resp.read()
            except (OSError, http.client.HTTPException) as exc:
                conn.close()
                row.update(status=502, absorbed_429=absorbed,
                           error=f"upstream:{type(exc).__name__}")
                row["resp_bytes"] = self._refuse(502, f"upstream: {type(exc).__name__}")
                return
            conn.close()
            meter._sleep(meter._wait_429(retry_after, absorbed))
            absorbed += 1
        row.update(status=resp.status, absorbed_429=absorbed, passed_429=int(resp.status == 429))
        try:
            self._relay(resp, row)
        finally:
            conn.close()

    def _relay(self, resp: http.client.HTTPResponse, row: dict[str, Any]) -> None:
        self.send_response(resp.status)
        for k, v in resp.getheaders():
            if k.lower() in _PASSED_RESPONSE_HEADERS:
                self.send_header(k, v)
        # the body is re-framed: chunked when the upstream sent no length
        up_len = resp.getheader("Content-Length")
        chunked = up_len is None
        if chunked:
            self.send_header("Transfer-Encoding", "chunked")
        else:
            self.send_header("Content-Length", up_len)
        self.send_header("Connection", "close")
        tail = bytearray()
        total = 0
        try:
            self.end_headers()
            while True:
                try:
                    chunk = resp.read1(_READ_BYTES)
                except (OSError, http.client.HTTPException) as exc:
                    row["error"] = f"upstream_stream:{type(exc).__name__}"
                    break
                if not chunk:
                    break
                total += len(chunk)
                tail += chunk
                if len(tail) > 2 * _TAIL_BYTES:
                    del tail[:-_TAIL_BYTES]
                if chunked:
                    self.wfile.write(b"%x\r\n" % len(chunk) + chunk + b"\r\n")
                else:
                    self.wfile.write(chunk)
                self.wfile.flush()
            if chunked and row["error"] is None:
                self.wfile.write(b"0\r\n\r\n")
        except OSError:
            row["error"] = "client_disconnected"     # usage is still recorded
        row["resp_bytes"] = total
        hits = _USAGE_RE.findall(bytes(tail[-_TAIL_BYTES:]))
        if hits:                                     # last usage blob wins (stream final chunk)
            try:
                row["usage"] = json.loads(hits[-1])
            except ValueError:
                row["usage"] = None
