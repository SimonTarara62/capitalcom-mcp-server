# Capital.com MCP Server

[![CI](https://github.com/SimonTarara62/capitalcom-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/SimonTarara62/capitalcom-mcp-server/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Model Context Protocol server for the Capital.com Open API. Built on the tested
[`capitalcom-cli`](https://github.com/SimonTarara62/capitalcom-cli) broker engine
(SDK), it exposes safe, guarded trading + market-data tools to MCP clients.

> ⚠️ **Unofficial & educational.** Not affiliated with Capital.com. Trading is
> risky and this is not financial advice. Trading is **disabled by default**;
> all trades are two-phase (preview → confirm → execute) with allowlists and
> size/rate limits. Start on a **demo** account. Apache-2.0 licensed.

## Install

No clone required — `uvx` runs it in an isolated, throwaway environment and
always fetches the latest tested release:

```bash
uvx capitalcom-mcp --help        # smoke test
```

Or install a persistent command with pipx:

```bash
pipx install capitalcom-mcp
```

## 1. Add your credentials (once)

Get an API key in the Capital.com app: **Settings → API integrations** (make a
**demo** key first). Then run the wizard — it writes a `0600` file and prints
the exact client snippet:

```bash
uvx capitalcom-mcp init
```

This writes `~/.config/capital-mcp/.env`. Verify any time (no secrets printed):

```bash
uvx capitalcom-mcp doctor
```

Prefer a secret manager? Set `CAP_API_KEY_CMD` / `CAP_IDENTIFIER_CMD` /
`CAP_API_PASSWORD_CMD` to a command that prints the secret (e.g.
`op read op://vault/...`, `pass ...`). The secret is fetched at launch and never
written to disk or to your client config.

## 2. Add the server to your client

Every client uses the same `command`/`args`/`env` shape. Pasting
`"CAP_ENV_FILE": "<path from init>"` keeps secrets out of the client file; or
put `CAP_API_KEY`/`CAP_IDENTIFIER`/`CAP_API_PASSWORD` directly in `env`.

### Claude Desktop
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) /
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "capitalcom": {
      "command": "uvx",
      "args": ["capitalcom-mcp"],
      "env": { "CAP_ENV_FILE": "/Users/you/.config/capital-mcp/.env" }
    }
  }
}
```

### Claude Code
```bash
claude mcp add --transport stdio \
  --env CAP_ENV_FILE=/Users/you/.config/capital-mcp/.env \
  capitalcom -- uvx capitalcom-mcp
```

### Cursor
`~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project):

```json
{
  "mcpServers": {
    "capitalcom": {
      "command": "uvx",
      "args": ["capitalcom-mcp"],
      "env": { "CAP_ENV_FILE": "/Users/you/.config/capital-mcp/.env" }
    }
  }
}
```

### VS Code (Copilot)
`.vscode/mcp.json` — note the root key is `servers` and `type: "stdio"`:

```json
{
  "servers": {
    "capitalcom": {
      "type": "stdio",
      "command": "uvx",
      "args": ["capitalcom-mcp"],
      "env": { "CAP_ENV_FILE": "/Users/you/.config/capital-mcp/.env" }
    }
  }
}
```

### Windsurf
`~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "capitalcom": {
      "command": "uvx",
      "args": ["capitalcom-mcp"],
      "env": { "CAP_ENV_FILE": "/Users/you/.config/capital-mcp/.env" }
    }
  }
}
```

### ChatGPT
ChatGPT requires a **remote** server (stdio is not supported) — see
[Remote / VPS hosting](#remote--vps-hosting). Once your server is reachable over
HTTPS, enable **Developer Mode** (Settings → Connectors → Advanced) and add the
server URL ending in `/mcp`. ChatGPT **Deep Research** connectors call two
read-only tools, `search` and `fetch`, which this server implements; full custom
tools require Developer Mode.

## Remote / VPS hosting

Run with streamable-HTTP instead of stdio:

```bash
CAP_ENV_FILE=/home/you/.config/capital-mcp/.env \
  capitalcom-mcp run --transport http --host 0.0.0.0 --port 8000
# endpoint: http://<host>:8000/mcp
```

Or via env (handy in systemd): `CAP_MCP_TRANSPORT=http`, `CAP_MCP_HOST`,
`CAP_MCP_PORT`. Put it behind a TLS-terminating reverse proxy for any public use.

## Safety model
- Trading off unless `CAP_ALLOW_TRADING=true` **and** the EPIC is in
  `CAP_ALLOWED_EPICS` (or `ALL`).
- Two-phase execution; `confirm=true` required for mutations.
- Size, open-position, and daily-order caps; `CAP_DRY_RUN=true` blocks all
  executions. A `TIMEOUT` confirmation is ambiguous — reconcile, don't blindly retry.

## Development
```bash
make install   # editable MCP + capitalcom-cli SDK from PyPI
make check     # ruff + mypy + pytest (offline; no network/credentials)
```

End-to-end tests drive **every** tool through the MCP against the **demo** API
(read, watchlists, account switch, preview/execute/amend/close/cancel, streaming).
They place real demo orders and clean up after themselves, so use a demo `.env`
with trading + streaming enabled:

```bash
# demo .env: CAP_ALLOW_TRADING=true, CAP_ALLOWED_EPICS=GOLD, CAP_WS_ENABLED=true
CAP_MCP_E2E=1 pytest -m e2e -v
```

## License
Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
