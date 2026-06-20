# Roadmap

> ⚠️ **Unofficial & educational.** A community project, not affiliated with
> Capital.com. This roadmap shows direction, not promises or dates — priorities
> shift, and community input shapes them. Trading is risky; this is not
> financial advice.

This is a community-owned, open-source MCP server for the Capital.com Open API.
The guiding goals: make it **easy to install**, **safe by default**, and
**pleasant to contribute to**. Here is where it is heading.

## Now — toward 1.0.0

The 1.0.0 line is about being dependable: a stable, documented tool surface and
a frictionless install.

- **Frozen tool API.** The 42 tools / 4 resources / 7 prompts are a stable
  contract, enforced in CI — see [API stability](docs/api-stability.md).
- **One-step local install.** Packaged bundles and a Homebrew formula so adding
  the server to a client is copy-paste, no Python toolchain wrangling.
- **Simpler configuration.** A guided `config` flow, demo/live profiles, and a
  `doctor` that validates your setup before you connect.
- **An audit journal.** An optional, redacted local log of every tool call, so
  agent-driven sessions are reviewable after the fact.
- **A welcoming on-ramp.** This roadmap, an [extension guide](docs/extending.md),
  and [good first issues](docs/good-first-issues.md).

## Next — observe & secure (1.1)

- **Journaling + reports.** Turn the audit journal into activity, trade-journal,
  and performance summaries.
- **Stronger key handling.** OS keychain support and an explicit live-trading
  guardrail.
- **Endpoint authentication.** A token for HTTP transport, refusing unprotected
  non-local binds.

## Later — remote & hosted (1.2)

- **Documented remote deployment.** A safe, TLS-fronted template for running the
  server on your own machine or VPS.
- **Operational health.** Configurable log levels and a health check.

## How to influence it

Open an issue describing your use case, pick up a
[good first issue](docs/good-first-issues.md), or start a discussion. Concrete
needs move items up; this list is a starting point, not a contract.
