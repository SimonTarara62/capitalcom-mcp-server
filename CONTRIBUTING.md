# Contributing

Thanks for your interest in improving the Capital.com MCP server! This project is
a thin [FastMCP](https://github.com/jlowin/fastmcp) layer over the
[`capitalcom-cli`](https://github.com/SimonTarara62/capitalcom-cli) SDK.

## Ground rules

- Be respectful — see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- Never commit secrets. `.env` and credential files are gitignored; only
  `.env.example` is tracked.
- Use a **demo** Capital.com account for all development and testing.

## Dev setup

```bash
git clone https://github.com/SimonTarara62/capitalcom-mcp-server
cd capitalcom-mcp-server
make install        # editable install + the capitalcom-cli SDK from PyPI
make check          # ruff + mypy + pytest (offline; no network/credentials)
```

## Running end-to-end tests (optional, demo only)

E2E tests drive every tool through the MCP against the live **demo** API and
place real demo orders (cleaning up after themselves). They need a demo `.env`:

```bash
# .env: CAP_ALLOW_TRADING=true, CAP_ALLOWED_EPICS=BTCUSD, CAP_WS_ENABLED=true
CAP_MCP_E2E=1 pytest -m e2e -v
```

## Adding a new tool

1. Add an `@mcp.tool()` async function in `capital_mcp/server.py` that delegates
   to the SDK facade (`get_app().<service>...`). Mutations must require
   `confirm=true`.
2. Add a unit test under `tests/test_tools_*.py` using the in-memory client.
3. Add an e2e test under `tests/e2e/` and register the tool in
   `tests/e2e/coverage.py` (the coverage-registry test enforces 100% tool
   coverage).
4. Document the tool in the README "What's inside" tables.

## Pull requests

- Keep PRs focused; update `CHANGELOG.md` under `## [Unreleased]`.
- Ensure `make check` passes and `ruff`/`mypy` are clean.
- Conventional Commit messages are appreciated (e.g. `feat:`, `fix:`, `docs:`).
