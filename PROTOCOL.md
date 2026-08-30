# AEP — Verification Protocol

Version 2. Companion to `SPEC.md`. `SPEC.md` defines what the mark looks like.
This document defines what it means, who may display it, and how that is checked.

## 0. What changed from v1

v1 invented a discovery path. That was wrong. Research established that:

- MCP has two competing discovery proposals, both draft: SEP-1649
  (`/.well-known/mcp/server-card.json`, sponsored, open since October 2025) and
  SEP-1960 (`/.well-known/mcp`). Neither is adopted.
- NLWeb defines `/ask` and `/who` but has no discovery file, and explicitly
  defers discovery to MCP.
- The space already holds `llms.txt`, `/.well-known/agents.json`, `/agents.txt`,
  and DNS-based schemes.

Publishing a tenth convention would be worse than useless. This protocol therefore
adopts **SEP-1649's server card** as its discovery document rather than defining
one. If SEP-1649 is superseded, follow it; do not fork.

v1 also permitted vendor-hosted endpoints via a counter-assertion. That is now the
narrow exception rather than the norm. See section 5.

## 1. The claim

Displaying AEP asserts exactly this and nothing more:

> At the time of the most recent successful check, this domain served a valid MCP
> server card at the canonical well-known path, declaring an endpoint on this same
> domain, and that endpoint accepted a connection, advertised at least one
> capability, and returned a well-formed, non-empty response to a minimal
> read-only probe.

Every clause is machine-testable. The narrowness is deliberate and load-bearing.

## 2. Explicit non-goals

The protocol does not check, and AEP does not assert:

- accuracy, completeness, or honesty of anything the endpoint returns
- quality of the endpoint's answers
- uptime, availability guarantees, or any service level
- security posture, authentication strength, or data handling
- the site's conduct toward agents in any respect other than the endpoint

AEP asserts that a door exists and opens. It says nothing about what is
behind it. Any future proposal to check quality or trustworthiness should be
rejected: a claim that cannot be falsified mechanically turns the mark into a
trust seal, and trust seals rot without exception.

## 3. Discovery

The checker fetches:

```
https://<domain>/.well-known/mcp/server-card.json
```

Per SEP-1649. Fixed path, no crawling, no fallbacks, no guessing.

A checker MAY additionally accept `/.well-known/mcp` (SEP-1960) while both drafts
are live, and MUST record which path answered. When one proposal is adopted, the
other is dropped.

The card's `transport.endpoint` is the endpoint under test. Everything else in the
card is informational to this protocol.

Cards MAY carry protocol-specific detail under `_meta`. An NLWeb server, for
example, records its `/ask`, `/who`, and `/info` URLs there. Checkers MUST NOT
require `_meta` and MUST NOT fail a card for its absence.

## 4. Check sequence

Run in order. Any failure stops the sequence and records the failing step.

| # | Check | Pass condition | Timeout |
|---|-------|----------------|---------|
| 1 | Fetch server card | HTTP 200, JSON content type, body under 64 KB | 5 s |
| 2 | Validate card | Required SEP-1649 keys present and well-formed | n/a |
| 3 | Domain binding | See section 5 | n/a |
| 4 | Connect | `transport.endpoint` accepts a connection | 10 s |
| 5 | Capabilities | At least one tool or resource advertised | 10 s |
| 6 | Handshake binding | Any callback URL the transport advertises is same-origin and reachable | 10 s |
| 7 | Probe | Fixed read-only query returns well-formed, non-empty response | 15 s |

Total wall clock budget: 30 s. Exceeding it is a failure of the step in flight,
recorded as a timeout rather than a protocol error.

The probe in step 7 must be published verbatim so operators know what will be sent
and can reproduce it. It must be read-only, must not mutate state, and must not
consume metered credits where the protocol allows that distinction to be
expressed.

### Why step 6 exists

Some transports hand the client a second URL after connecting. MCP's SSE
transport opens with an `endpoint` event naming where to POST messages. If that
URL points off-domain, or 404s, or 403s, the connection is useless no matter how
cleanly step 4 succeeded, and the same-origin guarantee of section 5 is void at
the layer that actually carries traffic.

Checking only the card's declared endpoint passes servers that no real client can
use. This was found by running the check against the first production
implementation, which scored a clean pass while advertising a callback that was
both off-origin and 403.

A checker MUST resolve any advertised callback against the connection URL, and
MUST fail with cause `callback_off_origin` or `callback_unreachable`.
Relative callbacks resolve to the connection URL and therefore always pass.

## 5. Domain binding

**The endpoint must live on the same registrable domain as the site claiming the
mark.** `example.com` and `mcp.example.com` pass. `example.com` and `vendor.io`
does not.

This is the rule, not a preference, and it is the single most important line in
this document. A mark whose endpoints resolve to vendor infrastructure makes that
vendor the registry for the entire standard, no matter how freely the artwork is
licensed. Same-origin binding is what keeps any one company out of the trust path.

Vendors who host agent endpoints for customers must have those customers proxy the
endpoint on their own domain. A CDN rewrite is sufficient. The customer then owns
the URL, which is better product design regardless.

### Narrow exception

A `cross_origin` binding is permitted only where the endpoint host serves
`/.well-known/mcp/authorizes.json` naming the claiming domain in an `authorizes`
array. Checkers MUST record `binding: "cross_origin"` in the public record, and
consumers MAY treat cross-origin bindings as weaker. This exists for genuinely
federated cases, not as a route around section 5.

## 6. Freshness

Freshness is the parameter that decides whether this survives. Every dead badge
died by being checked once and displayed forever.

- **Check interval:** every 24 hours, at a randomized time within the window.
- **Staleness threshold:** a PASS expires 72 hours after the last successful
  check. This tolerates two consecutive missed or failed checks and no more.
- **On expiry:** the record moves to `FAIL`. The site is expected to stop
  displaying the mark. Absence is the negative state.

24 hours rather than hourly because endpoints change rarely, and hourly checking
at adoption scale is a distributed denial of service run against your own
adopters.

## 7. States

| State | Meaning |
|-------|---------|
| `UNKNOWN` | Never checked. |
| `PASS` | Last check succeeded, within staleness window. |
| `DEGRADED` | One or two consecutive failures, still within staleness window. |
| `FAIL` | Three or more consecutive failures, or past the staleness threshold. |
| `NOT_CHECKED` | The checker itself failed to run. |

`DEGRADED` keeps the record honest without flapping on a brief blip. Only `PASS`
qualifies a site to display the mark.

`NOT_CHECKED` must never increment the consecutive-failure counter. A checker
outage is the checker's fault and must not revoke anyone.

Record failure causes distinctly: DNS failure, connection refused, TLS error, HTTP
error, card invalid, binding failed, connection rejected, empty capabilities,
probe empty, timeout. Aggregating these into "failed" destroys the operator's
ability to fix the problem.

## 8. Authentication

An endpoint whose card declares `authentication.required: true` cannot be probed
by an anonymous checker, and the protocol will not hold credentials.

Such an endpoint receives `state: PASS` with `probe: "skipped_auth_required"`
provided steps 1 through 4 pass and the card declares at least one capability. The
public record must show the probe was skipped. A consumer that requires a proven
probe can filter on it.

The alternative, failing every authenticated endpoint, would exclude enterprise
deployments for no gain in the claim's truthfulness. The alternative of pretending
the probe ran would be a lie. Recording the skip is the honest third option.

## 9. Cloaking

A site could serve a working endpoint to a known checker and nothing to real
agents. Cloaking voids the assertion.

The tension: an open protocol requires a documented, identifiable checker, and a
documented checker is trivially detectable.

Resolution:

- The checker publishes its user agent string and network origins.
- The checker additionally performs an unannounced check from a generic user agent
  and an unpublished origin, at least once per staleness window.
- If the announced and unannounced checks disagree, the record moves to `FAIL`
  with cause `differential_response`, recorded publicly.

This does not make cloaking impossible. It makes it detectable and expensive,
which is the realistic bar.

## 10. The public record

Every checker publishes a machine-readable record per domain at a stable URL, plus
a human-readable page. The mark links to the record.

```json
{
  "domain": "example.com",
  "state": "PASS",
  "protocol_version": "2",
  "checker_id": "example-checker.org",
  "card_path": "/.well-known/mcp/server-card.json",
  "endpoint_checked": "https://example.com/agent/sse",
  "binding": "same_origin",
  "last_check_at": "2026-08-29T04:12:07Z",
  "last_pass_at": "2026-08-29T04:12:07Z",
  "consecutive_failures": 0,
  "checks": [
    {"step": "card_fetch", "result": "pass"},
    {"step": "card_validate", "result": "pass"},
    {"step": "domain_binding", "result": "pass", "method": "same_etld1"},
    {"step": "connect", "result": "pass", "ms": 240},
    {"step": "capabilities", "result": "pass", "count": 4},
    {"step": "handshake_binding", "result": "pass", "method": "relative"},
    {"step": "probe", "result": "pass", "ms": 810}
  ]
}
```

A badge whose claim cannot be independently inspected is the failure mode that
killed the security seals. The record is not optional.

## 11. Governance

If one organization runs the only checker, the mark is gated by that organization
regardless of how freely the artwork is licensed.

Therefore:

- This protocol is published openly. Anyone may implement it.
- The **record format is the standard**, not any particular checker.
- A checker must publish its identity, cadence, origins, and log retention policy.
- The mark links to *a* checker's record. Never to *the* checker's record.
- Multiple checkers may report on the same domain and may disagree. Disagreement
  is public information, not an error to be resolved centrally.

The model is SSL Labs: influential as a service, never an authority, useful
without anyone having to trust the operator.

## 12. Operator protections

- **Rate limit.** No more than one full check sequence per domain per hour from
  any single checker, regardless of retries.
- **Identification.** The announced check sends a documented user agent and a
  contact URL.
- **Opt out.** A domain may set `_meta.checking: "disabled"` in its server card.
  The record then reads `UNKNOWN` with cause `operator_opt_out`. A domain that
  opts out is not eligible to display the mark, and that is its choice to make.
- **Correction.** A published contact route for disputing a record, with the
  dispute and its resolution recorded publicly.

## 13. Enforcement

There is none, and the protocol should not pretend otherwise. Nothing stops a site
displaying the mark while its record says `FAIL`.

The mechanism is contradiction, not enforcement: the mark links to a record, and
the record is public. A site displaying an unearned mark is publishing a link to
evidence against itself. That is the entire enforcement model, and it is the same
one that made the RSS icon meaningful.

## 14. Open parameters

Decide before v1 release:

- Probe query wording, published verbatim.
- Whether `DEGRADED` is exposed in the public record or kept internal.
- Log retention period for check history.
- Whether records are queryable in bulk, and under what rate limit.
- Whether to accept SEP-1960's path during the draft period, or bet on SEP-1649
  alone.
