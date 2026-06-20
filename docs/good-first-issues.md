# Good first issues

> ⚠️ **Unofficial & educational.** Community project, not affiliated with
> Capital.com. New here? These are small, well-scoped tasks to make a first
> contribution. Read [CONTRIBUTING.md](../CONTRIBUTING.md) and
> [docs/extending.md](extending.md) first, and develop against a **demo**
> account.

Comment on the matching issue (or open one referencing the item) before you
start, so we don't double up.

## Documentation

- **Add a "Troubleshooting" section to the README** covering the three most
  common setup errors (missing credentials, trading disabled, streaming off).
  *Acceptance:* a short table of symptom → fix.
- **Improve tool docstrings** where the first line is terse. The docstring is
  what MCP clients show users. *Files:* `capital_mcp/server.py`.

## Tests

- **Add a unit test for an untested error path** — e.g. a tool called without a
  required argument, or an SDK error surfaced as a clean message. *Files:*
  `tests/test_tools_*.py` using the `client`/`fake_app` fixtures.
- **Tighten an assertion** in an existing `tests/test_tools_*.py` to check the
  exact SDK call arguments (`assert_awaited_once_with(...)`), not just the
  return value.

## Small features (read-only, low risk)

- **Add a read-only market tool** that surfaces an existing `capital_cli`
  endpoint not yet exposed. Follow [docs/extending.md](extending.md): tool +
  unit test + e2e coverage entry + `make snapshot` + README table + CHANGELOG.
- **Improve an error message** when credentials are missing so it names the
  exact env vars and points to `uvx capitalcom-mcp init`. *Files:*
  `capital_mcp/context.py`, `capital_mcp/cli.py`.

## Quality

- **Add a `make` target or pre-commit hook** that runs `ruff` + `mypy` on
  staged files, and document it in CONTRIBUTING. *Files:* `Makefile`,
  `CONTRIBUTING.md`.

Each task should stay small enough to review in one sitting. If one grows,
split it and say so in the PR.
