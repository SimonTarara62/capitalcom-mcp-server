<!-- mcp-name: io.github.simontarara62/capitalcom-mcp-server -->

# Capital.com MCP Server

[![PyPI version](https://img.shields.io/pypi/v/capitalcom-mcp.svg)](https://pypi.org/project/capitalcom-mcp/)
[![Python versions](https://img.shields.io/pypi/pyversions/capitalcom-mcp.svg)](https://pypi.org/project/capitalcom-mcp/)
[![CI](https://github.com/SimonTarara62/capitalcom-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/SimonTarara62/capitalcom-mcp-server/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-listed-0098FF)](https://registry.modelcontextprotocol.io/?search=io.github.simontarara62/capitalcom-mcp-server)
[![PyPI downloads](https://img.shields.io/pypi/dm/capitalcom-mcp.svg)](https://pypi.org/project/capitalcom-mcp/)

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

## What's inside — tools, resources & prompts

This server exposes **42 tools**, **4 resources**, and **7 guided prompts**. All
tool names are prefixed `cap_` except the two ChatGPT Deep Research adapters
(`search`, `fetch`). Mutating tools require `confirm=true`; trades are two-phase.

### Session & account

| Tool | What it does |
| --- | --- |
| `cap_session_status` | Current login/session state. |
| `cap_session_login` | Authenticate (optionally `force=true`). |
| `cap_session_ping` | Keep-alive / liveness check. |
| `cap_session_logout` | End the session. |
| `cap_session_switch_account` | Switch the active trading account. |
| `cap_account_list` | List accounts and the active account id. |
| `cap_account_preferences_get` | Read account preferences (e.g. hedging mode). |
| `cap_account_preferences_set` | Update preferences (`confirm` required). |
| `cap_account_history_activity` | Account activity history. |
| `cap_account_history_transactions` | Transaction history. |
| `cap_account_demo_topup` | Top up a **demo** balance (`confirm` required). |

### Market data

| Tool | What it does |
| --- | --- |
| `cap_market_search` | Search instruments by term. |
| `cap_market_get` | Full market details + snapshot for an EPIC. |
| `cap_market_navigation_root` | Top-level market navigation nodes. |
| `cap_market_navigation_node` | Drill into a navigation node. |
| `cap_market_prices` | Historical OHLC candles. |
| `cap_market_sentiment` | Client long/short positioning. |

### Trading (read → preview → execute → manage)

| Tool | What it does |
| --- | --- |
| `cap_trade_positions_list` | Open positions. |
| `cap_trade_positions_get` | One position by deal id. |
| `cap_trade_orders_list` | Working (pending) orders. |
| `cap_trade_confirm_get` | Fetch a deal confirmation by reference. |
| `cap_trade_confirm_wait` | Poll until a deal confirms (or times out). |
| `cap_trade_preview_position` | **Phase 1**: validate a market position (no execution). |
| `cap_trade_preview_working_order` | **Phase 1**: validate a working order. |
| `cap_trade_execute_position` | **Phase 2**: execute a previewed position (`confirm`). |
| `cap_trade_execute_working_order` | **Phase 2**: place a previewed working order (`confirm`). |
| `cap_trade_positions_close` | Close a position (`confirm`). |
| `cap_trade_orders_cancel` | Cancel a working order (`confirm`). |
| `cap_trade_positions_amend` | Amend stop/limit on a position (`confirm`). |
| `cap_trade_orders_amend` | Amend a working order (`confirm`). |

### Watchlists

| Tool | What it does |
| --- | --- |
| `cap_watchlists_list` | List watchlists. |
| `cap_watchlists_get` | Get one watchlist's markets. |
| `cap_watchlists_create` | Create a watchlist (`confirm`). |
| `cap_watchlists_add_market` | Add an EPIC (`confirm`). |
| `cap_watchlists_remove_market` | Remove an EPIC (`confirm`). |
| `cap_watchlists_delete` | Delete a watchlist (`confirm`). |

### Streaming (WebSocket; requires `CAP_WS_ENABLED=true`)

| Tool | What it does |
| --- | --- |
| `cap_stream_prices` | Live bid/ask updates for EPICs. |
| `cap_stream_candles` | Live OHLC candle updates. |
| `cap_stream_alerts` | Threshold price alerts. |
| `cap_stream_portfolio` | Live position/P&L updates. |

### ChatGPT Deep Research adapters

| Tool | What it does |
| --- | --- |
| `search` | Read-only instrument search (ChatGPT connector contract). |
| `fetch` | Read-only instrument fetch by id (ChatGPT connector contract). |

### Resources

| URI | What it returns |
| --- | --- |
| `cap://status` | Session/connection status snapshot. |
| `cap://risk-policy` | Active risk policy (trading flag, caps). |
| `cap://allowed-epics` | The trading EPIC allowlist. |
| `cap://market-cache/{epic}` | Cached market snapshot for an EPIC. |

### Guided prompts

Prompts are reusable workflows your client can launch by name. They emit
step-by-step guidance that orchestrates the tools above — they never trade on
their own.

| Prompt | Purpose |
| --- | --- |
| `market_scan` | Scan a watchlist for opportunities (prices + sentiment). |
| `trade_proposal` | Design a risk-sized trade and validate it via preview. |
| `execute_trade` | Safely execute a previously previewed trade. |
| `position_review` | Review open positions and working orders. |
| `live_price_monitor` | Stream prices and flag threshold moves. |
| `real_time_alerts` | Configure and watch live price alerts. |
| `live_portfolio_monitor` | Stream live portfolio P&L with a threshold. |

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
