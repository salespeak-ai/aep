# AEP — Agent Entry Point

A site with an AEP can be queried directly by an AI agent instead of crawled.

This repository holds three things, all freely reusable:

- **[PROTOCOL.md](PROTOCOL.md)** — what an AEP claim means and how it is checked.
- **[checker/](checker/)** — a reference checker. Standard library only.
- **The mark** — a visual sign a site displays when its claim currently passes.

Nothing here is owned. The artwork is dedicated under CC0, no trademark is
claimed, and the protocol is published so that anyone, including direct
competitors of its authors, can implement it without asking permission.

## The problem

An agent landing on a website has no way to learn whether that site can answer
questions directly. There is no equivalent of the RSS icon for "you can talk to
this site." The only options today are to crawl every page, or to ask a
vendor-run registry, which makes that vendor the lookup for everyone else's
capability.

## What an AEP claim asserts

Exactly one thing, deliberately narrow:

> At the time of the most recent successful check, this domain served a valid
> MCP server card at the canonical well-known path, declaring an endpoint on
> this same domain, and that endpoint accepted a connection, advertised at least
> one capability, and returned a well-formed, non-empty response to a minimal
> read-only probe.

It says nothing about whether the answers are accurate, complete, or honest. It
asserts that a door exists and opens, not what is behind it. That limit is
load-bearing: a claim that cannot be falsified mechanically becomes a trust
seal, and trust seals rot.

## Discovery

AEP does not define a discovery file. It adopts
[SEP-1649](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1649),
the MCP server card at `/.well-known/mcp/server-card.json`, and accepts
[SEP-1960](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1960)'s
`/.well-known/mcp` while both are draft.

The space already holds `llms.txt`, `/.well-known/agents.json`, `/agents.txt`,
and DNS-based schemes. A tenth convention would be worse than useless.

## Using the checker

```
python3 checker/aep_check.py example.com
python3 checker/aep_check.py example.com --json
```

Exit codes: `0` PASS, `1` FAIL, `2` UNKNOWN.

No dependencies, no account, no registration. A governance model that says
"anyone may run a checker" is worthless if running one requires a build step.

## Governance

The **record format is the standard**, not any particular checker. Multiple
checkers may report on the same domain and may disagree; disagreement is public
information, not an error to be resolved centrally. A checker publishes its
identity, cadence, network origins, and log retention.

The mark links to *a* checker's record, never to *the* checker's record.

The model is SSL Labs: influential as a service, never an authority, useful
without anyone having to trust the operator.

## There is no enforcement

Nothing stops a site displaying the mark while its record says FAIL. The
mechanism is contradiction, not enforcement: the mark links to a public record,
so a site displaying an unearned mark is publishing a link to evidence against
itself. That is the same mechanism that made the RSS icon meaningful.

## Status

Draft. The protocol is at version 2 and has been run against a production
implementation, which it failed for a real defect — see PROTOCOL.md section 4,
step 6, which exists because of that run.

## License

CC0 1.0 Universal. No trademark is claimed. See [LICENSE](LICENSE).
