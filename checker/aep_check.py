#!/usr/bin/env python3
"""AEP reference checker.

Given a domain, runs the seven checks in PROTOCOL.md and emits the record
described in its section 10.

Standard library only, by design. A governance model that says "anyone may run
a checker" is worthless if running one requires a dependency tree, a build step,
or an account. This should work on any machine with Python 3.9+.

  python3 aep_check.py salespeak.ai
  python3 aep_check.py salespeak.ai --json
  python3 aep_check.py example.com --timeout 45

Exit codes: 0 PASS, 1 FAIL, 2 UNKNOWN (opted out or never checkable).
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

PROTOCOL_VERSION = "2"
CARD_PATHS = [
    "/.well-known/mcp/server-card.json",  # SEP-1649
    "/.well-known/mcp",  # SEP-1960, accepted while both drafts are live
]
USER_AGENT = "aep-checker/0.1 (+https://github.com/salespeak-ai/aep)"

MAX_CARD_BYTES = 64 * 1024
TOTAL_BUDGET_S = 30

# Published verbatim so operators know exactly what will be sent. Read-only,
# mutates nothing, and consumes no metered credits on any conforming server.
PROBE = {"jsonrpc": "2.0", "id": "aep-probe", "method": "tools/list", "params": {}}

# Multi-label public suffixes common enough to matter. A full check would use
# the Public Suffix List; bundling it would mean a fetch or a vendored copy, and
# neither belongs in a file meant to be auditable at a glance. Domains outside
# this list fall back to last-two-labels, which over-accepts (treats
# foo.example.co.za and bar.example.co.za as one site) and never under-accepts.
_MULTI_SUFFIXES = {
    "co.uk", "org.uk", "ac.uk", "gov.uk", "co.jp", "or.jp", "ne.jp",
    "com.au", "net.au", "org.au", "co.nz", "com.br", "com.mx", "co.za",
    "co.il", "com.sg", "co.in", "com.tr", "com.cn",
}


def registrable_domain(host: str) -> str:
    """Approximate eTLD+1. See _MULTI_SUFFIXES for the known limitation."""
    labels = host.lower().strip(".").split(".")
    if len(labels) < 2:
        return host.lower()
    if len(labels) >= 3 and ".".join(labels[-2:]) in _MULTI_SUFFIXES:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def same_site(a: str, b: str) -> bool:
    ha = urllib.parse.urlparse(a).hostname or a
    hb = urllib.parse.urlparse(b).hostname or b
    return registrable_domain(ha) == registrable_domain(hb)


def tls_context() -> ssl.SSLContext:
    """A verifying TLS context, or a clear error.

    Certificate verification is never disabled. This tool exists to verify a
    claim about a domain; a check that accepts any certificate verifies nothing
    and would happily pass an attacker.

    Some Python builds ship with an empty trust store (notably the python.org
    macOS installer before its "Install Certificates.command" is run). Fall back
    to certifi if it happens to be installed, then fail loudly.
    """
    ctx = ssl.create_default_context()
    if ctx.get_ca_certs():
        return ctx
    try:
        import certifi

        ctx = ssl.create_default_context(cafile=certifi.where())
        if ctx.get_ca_certs():
            return ctx
    except ImportError:
        pass
    raise SystemExit(
        f"{sys.executable} has no CA certificates loaded, so TLS cannot be "
        "verified.\nOn macOS with a python.org build, run:\n"
        "  /Applications/Python 3.x/Install Certificates.command\n"
        "Or use a different interpreter (/usr/bin/python3 usually works)."
    )


_TLS = None


class Deadline:
    """Wall-clock budget shared across every step, per PROTOCOL.md section 4."""

    def __init__(self, budget: float) -> None:
        self.expires_at = time.monotonic() + budget

    def remaining(self, step_timeout: float) -> float:
        left = self.expires_at - time.monotonic()
        if left <= 0:
            raise TimeoutError("total wall clock budget exhausted")
        return min(step_timeout, left)


def http(
    url: str,
    deadline: Deadline,
    timeout: float,
    method: str = "GET",
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    max_bytes: int = MAX_CARD_BYTES,
) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("User-Agent", USER_AGENT)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    global _TLS
    if _TLS is None:
        _TLS = tls_context()
    with urllib.request.urlopen(
        req, timeout=deadline.remaining(timeout), context=_TLS
    ) as r:
        return r.status, dict(r.headers), r.read(max_bytes)


class Check:
    """Accumulates step results and the first failure cause."""

    def __init__(self) -> None:
        self.steps: list[dict[str, Any]] = []
        self.cause: str | None = None

    def ok(self, step: str, **extra: Any) -> None:
        self.steps.append({"step": step, "result": "pass", **extra})

    def fail(self, step: str, cause: str, detail: str = "") -> None:
        entry = {"step": step, "result": "fail", "cause": cause}
        if detail:
            entry["detail"] = detail[:300]
        self.steps.append(entry)
        self.cause = cause


def _fetch_card(domain: str, c: Check, dl: Deadline) -> tuple[dict | None, str | None]:
    last = ""
    for path in CARD_PATHS:
        url = f"https://{domain}{path}"
        try:
            status, _, raw = http(url, dl, 5.0)
        except TimeoutError:
            c.fail("card_fetch", "timeout")
            return None, None
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
            last = f"{path}: {e}"
            continue
        if status != 200:
            last = f"{path}: HTTP {status}"
            continue
        if len(raw) >= MAX_CARD_BYTES:
            c.fail("card_fetch", "card_too_large", path)
            return None, None
        try:
            card = json.loads(raw)
        except json.JSONDecodeError as e:
            c.fail("card_fetch", "card_malformed", f"{path}: {e}")
            return None, None
        if not isinstance(card, dict):
            c.fail("card_fetch", "card_malformed", f"{path}: not an object")
            return None, None
        c.ok("card_fetch", path=path)
        return card, path
    c.fail("card_fetch", "card_absent", last)
    return None, None


def _validate(card: dict, c: Check) -> str | None:
    transport = card.get("transport")
    if not isinstance(transport, dict) or not transport.get("endpoint"):
        c.fail("card_validate", "card_invalid", "transport.endpoint missing")
        return None
    endpoint = transport["endpoint"]
    if not isinstance(endpoint, str) or not endpoint.startswith("https://"):
        c.fail("card_validate", "card_invalid", "transport.endpoint must be https")
        return None
    c.ok("card_validate", transport=transport.get("type", "unspecified"))
    return endpoint


def _binding(domain: str, endpoint: str, card: dict, c: Check, dl: Deadline) -> str | None:
    if same_site(endpoint, domain):
        c.ok("domain_binding", method="same_etld1")
        return "same_origin"

    host = urllib.parse.urlparse(endpoint).hostname or ""
    url = f"https://{host}/.well-known/mcp/authorizes.json"
    try:
        status, _, raw = http(url, dl, 5.0)
        authorizes = json.loads(raw).get("authorizes", []) if status == 200 else []
    except Exception:
        authorizes = []

    if registrable_domain(domain) in {registrable_domain(a) for a in authorizes}:
        c.ok("domain_binding", method="counter_assertion")
        return "cross_origin"

    c.fail("domain_binding", "binding_failed", f"{endpoint} is not on {domain}")
    return None


def _connect(endpoint: str, c: Check, dl: Deadline) -> str | None:
    """Open the transport. Returns the raw first-response text for step 6."""
    try:
        status, _, raw = http(
            endpoint, dl, 10.0,
            headers={"Accept": "text/event-stream"},
            max_bytes=8192,
        )
    except TimeoutError:
        c.fail("connect", "timeout")
        return None
    except urllib.error.HTTPError as e:
        c.fail("connect", "connection_rejected", f"HTTP {e.code}")
        return None
    except (urllib.error.URLError, OSError) as e:
        c.fail("connect", "connection_refused", str(e))
        return None
    if status != 200:
        c.fail("connect", "connection_rejected", f"HTTP {status}")
        return None
    c.ok("connect")
    return raw.decode("utf-8", "replace")


def _capabilities(card: dict, c: Check) -> bool:
    caps = card.get("capabilities") or {}
    declared = [k for k, v in caps.items() if v] if isinstance(caps, dict) else []
    tools = card.get("tools") or []
    count = len(tools) if isinstance(tools, list) else 0
    if not declared and not count:
        c.fail("capabilities", "no_capabilities", "card declares none")
        return False
    c.ok("capabilities", count=count or len(declared))
    return True


def _handshake_binding(endpoint: str, stream: str, c: Check, dl: Deadline) -> str | None:
    """PROTOCOL.md section 4 step 6.

    A transport may hand back a second URL after connecting. If it points
    off-origin or is unreachable, the connection is useless however cleanly the
    earlier steps passed, and section 5's guarantee is void where traffic
    actually flows.
    """
    advertised = None
    for line in stream.splitlines():
        if line.startswith("data:"):
            try:
                payload = json.loads(line[5:].strip())
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and "url" in payload:
                advertised = payload["url"]
                break

    if advertised is None:
        # Nothing advertised: nothing to verify, and nothing can go wrong here.
        c.ok("handshake_binding", method="none_advertised")
        return endpoint

    resolved = urllib.parse.urljoin(endpoint, advertised)
    method = "relative" if resolved != advertised else "absolute"

    if not same_site(resolved, endpoint):
        c.fail("handshake_binding", "callback_off_origin", f"{advertised} -> {resolved}")
        return None

    try:
        status, _, _ = http(
            resolved, dl, 10.0, method="POST",
            body=b"{}", headers={"Content-Type": "application/json"},
            max_bytes=2048,
        )
        reachable = status < 500
    except urllib.error.HTTPError as e:
        reachable = e.code < 500 and e.code not in (403, 404)
    except Exception:
        reachable = False

    if not reachable:
        c.fail("handshake_binding", "callback_unreachable", resolved)
        return None

    c.ok("handshake_binding", method=method)
    return resolved


def _probe(url: str, c: Check, dl: Deadline) -> bool:
    body = json.dumps(PROBE).encode()
    try:
        status, _, raw = http(
            url, dl, 15.0, method="POST", body=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            max_bytes=256 * 1024,
        )
    except TimeoutError:
        c.fail("probe", "timeout")
        return False
    except urllib.error.HTTPError as e:
        c.fail("probe", "probe_rejected", f"HTTP {e.code}")
        return False
    except Exception as e:
        c.fail("probe", "probe_failed", str(e))
        return False

    if status != 200 or not raw.strip():
        c.fail("probe", "probe_empty", f"HTTP {status}, {len(raw)} bytes")
        return False
    try:
        json.loads(raw)
    except json.JSONDecodeError:
        c.fail("probe", "probe_malformed")
        return False
    c.ok("probe")
    return True


def check(domain: str, budget: float = TOTAL_BUDGET_S) -> dict[str, Any]:
    dl = Deadline(budget)
    c = Check()
    record: dict[str, Any] = {
        "domain": domain,
        "state": "FAIL",
        "protocol_version": PROTOCOL_VERSION,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    card, path = _fetch_card(domain, c, dl)
    if card is None:
        record["state"] = "UNKNOWN" if c.cause == "card_absent" else "FAIL"
        return _finish(record, c, path)

    # Operator opt-out, PROTOCOL.md section 12.
    if (card.get("_meta") or {}).get("checking") == "disabled":
        record["state"] = "UNKNOWN"
        c.cause = "operator_opt_out"
        return _finish(record, c, path)

    record["card_path"] = path
    endpoint = _validate(card, c)
    if endpoint is None:
        return _finish(record, c, path)
    record["endpoint_checked"] = endpoint

    binding = _binding(domain, endpoint, card, c, dl)
    if binding is None:
        return _finish(record, c, path)
    record["binding"] = binding

    stream = _connect(endpoint, c, dl)
    if stream is None:
        return _finish(record, c, path)

    if not _capabilities(card, c):
        return _finish(record, c, path)

    post_url = _handshake_binding(endpoint, stream, c, dl)
    if post_url is None:
        return _finish(record, c, path)

    # PROTOCOL.md section 8: an authenticated endpoint cannot be probed by an
    # anonymous checker. Record the skip rather than failing it or pretending.
    if (card.get("authentication") or {}).get("required"):
        c.steps.append({"step": "probe", "result": "skipped_auth_required"})
        record["state"] = "PASS"
        return _finish(record, c, path)

    if _probe(post_url, c, dl):
        record["state"] = "PASS"
    return _finish(record, c, path)


def _finish(record: dict, c: Check, path: str | None) -> dict:
    record["checks"] = c.steps
    if c.cause:
        record["cause"] = c.cause
    return record


def main() -> int:
    ap = argparse.ArgumentParser(description="AEP reference checker")
    ap.add_argument("domain")
    ap.add_argument("--json", action="store_true", help="emit the record only")
    ap.add_argument("--timeout", type=float, default=TOTAL_BUDGET_S,
                    help=f"total wall clock budget (default {TOTAL_BUDGET_S}s)")
    args = ap.parse_args()

    domain = args.domain.strip().rstrip("/")
    for prefix in ("https://", "http://"):
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.split("/")[0]

    record = check(domain, args.timeout)

    if args.json:
        print(json.dumps(record, indent=2))
    else:
        print(f"{record['state']}  {domain}")
        for s in record["checks"]:
            mark = {"pass": "ok", "fail": "FAIL"}.get(s["result"], s["result"])
            extra = s.get("cause", "") or s.get("method", "") or ""
            detail = f"  {s['detail']}" if s.get("detail") else ""
            print(f"  {mark:>18}  {s['step']}{'  ' + extra if extra else ''}{detail}")

    return {"PASS": 0, "FAIL": 1}.get(record["state"], 2)


if __name__ == "__main__":
    sys.exit(main())
