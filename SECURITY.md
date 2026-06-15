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
