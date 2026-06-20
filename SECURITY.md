# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.3.x   | ✅        |
| < 0.3   | ❌        |

## Reporting a vulnerability

**Please do not open public issues for security problems.** This project brokers
trading API credentials, so responsible disclosure matters.

- Use GitHub's **Report a vulnerability** button (Security → Advisories →
  Report a vulnerability) on this repository, **or**
- email the maintainer listed on the GitHub profile.

Please include reproduction steps and the affected version. We aim to acknowledge
reports within **5 business days** and to ship a fix or mitigation as quickly as
the severity warrants.

## Handling credentials safely

- This server never logs secrets and writes credential files with `0600`
  permissions.
- Always start on a **demo** account. Trading is disabled unless
  `CAP_ALLOW_TRADING=true` **and** the EPIC is allowlisted.
- Prefer the `CAP_*_CMD` secret-exec helpers or `CAP_ENV_FILE` over inline
  secrets in client configs.

## Tool stability

Tool **names** and their **semantics** are stable within a major version. An
existing tool's behavior will not silently change between releases: a change
that alters what a tool does ships as a **new tool name** or a documented
deprecation, and every such change is recorded in [CHANGELOG.md](CHANGELOG.md).
This protects MCP clients from "rug-pull" surprises where a trusted tool quietly
starts doing something different.

To pin against any change at all, pin the exact package version (see the
README's "Pinning for production / real-money use" note).

The full policy — what is guaranteed within a major version, what is additive,
and how deprecations work — is documented in
[docs/api-stability.md](docs/api-stability.md) and enforced by an automated
API-surface snapshot test.
