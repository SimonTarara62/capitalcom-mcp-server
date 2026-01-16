# Capital.com MCP Server

Model Context Protocol (MCP) server for Capital.com Open API - enabling safe, LLM-driven trading operations.

> **⚠️ DISCLAIMER**: This is an **unofficial, community-built** project for educational and study purposes only. It is **NOT** affiliated with, endorsed by, or officially supported by Capital.com. This is an independent implementation of the Capital.com Open API for research and learning purposes.

## ⚠️ Important Safety Notice

**Trading is risky. This software is for engineering/educational purposes and is NOT financial advice.**

- This is an **unofficial community project** - not an official Capital.com product
- Always start with a **Demo account** before considering live trading
- Trading is **disabled by default** and requires explicit configuration
- All trade operations require **two-phase execution** (preview → confirm → execute)
- Built-in risk controls: allowlists, size limits, daily order caps
- **Use at your own risk** - the authors assume no liability for trading losses

## Current Implementation Status

**Overall: 85% Complete** (Phases 1-6 done, Phase 7 testing implemented)

### ✅ Completed (Phases 1-6)

**Foundation & Infrastructure**
- ✅ Project structure with pyproject.toml, dependencies configured
- ✅ Configuration system with environment variable validation
- ✅ Core data models with Pydantic (enums, requests, responses)
- ✅ Error handling (error codes, custom exceptions, secret redaction)
- ✅ Rate limiting (token bucket, async-safe, multi-tier)
- ✅ HTTP client (httpx, retries, timeout handling, logging)
- ✅ Session management (auto-login, token refresh, keep-alive)
- ✅ Risk engine (preview cache, size normalization, trade guards)

**MCP Server & Tools (36 tools implemented)**
- ✅ FastMCP server with STDIO transport
- ✅ Session tools (4) - status, login, ping, logout
- ✅ Market data tools (6) - search, get, prices, sentiment, navigation
- ✅ Account tools (6) - list, preferences, history, demo top-up
- ✅ Trading tools (14) - positions, orders, preview, execute, close, cancel
- ✅ Watchlist tools (6) - list, get, create, add, delete, remove

**MCP Prompts (4 workflow templates implemented)**
- ✅ market_scan - Scan watchlists for trading opportunities
- ✅ trade_proposal - Design trades with risk management
- ✅ execute_trade - Execute previewed trades safely
- ✅ position_review - Analyze portfolio positions and orders

**MCP Resources (4 read-only resources implemented)**
- ✅ cap://status - Server and session status
- ✅ cap://risk-policy - Risk management configuration
- ✅ cap://allowed-epics - Trading allowlist
- ✅ cap://market-cache/{epic} - Market details (dynamic)

### ✅ Testing (Phase 7 - Partial)

**Testing Suite**
- ✅ Test infrastructure (pytest, pytest-asyncio, pytest-mock, pytest-cov)
- ✅ Basic sanity tests (imports, error definitions, MCP server instance)
- ✅ MCP registration tests (33 tools, 5 resources, 4 prompts)
- ✅ Prompt validation tests (descriptions, arguments)
- ⏳ Unit tests for core components (deferred - tight coupling)
- ⏳ Integration tests with mocked API (deferred - tight coupling)

### 📋 Pending

**Optional Features**
- ⏳ WebSocket support (optional, live streaming)
- ⏳ 2 missing tools (update position, update order)

## Quick Start Guide

### Step 1: Get Capital.com API Credentials

1. **Create Account**: Go to [capital.com/trading/signup](https://capital.com/trading/signup)
   - Choose **Demo** account for testing (recommended)
   - Verify your email

2. **Enable 2FA**: Settings > Security > Two-Factor Authentication
   - Required before generating API keys

3. **Generate API Key**: Settings > API integrations > Generate new key
   - Set a label (e.g., "MCP Server")
   - **Set a custom password** (this is NOT your platform password)
   - Save the API key shown (displayed only once!)
   - Note: API keys are trading-capable; Capital.com doesn't offer read-only keys

### Step 2: Install & Configure

```bash
# Navigate to project directory
cd /path/to/capital-mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy and configure environment file
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Required
CAP_ENV=demo
CAP_API_KEY=your_generated_api_key_here
CAP_IDENTIFIER=your_email@example.com
CAP_API_PASSWORD=your_custom_api_password

# Safety (keep trading disabled until ready)
CAP_ALLOW_TRADING=false
CAP_ALLOWED_EPICS=

# Optional: enable later for real trading
# CAP_ALLOW_TRADING=true
# CAP_ALLOWED_EPICS=SILVER,GOLD,BTCUSD
```

### Step 3: Test Server Locally

```bash
# Activate venv if not already
source venv/bin/activate

# Run server directly (for testing)
python -m capital_mcp.server

# You should see:
# INFO - Starting Capital.com MCP Server (env: demo)
# INFO - Trading enabled: False

# Press Ctrl+C to stop
```

### Troubleshooting: Check Logs

If you encounter issues when using the MCP server with Claude Desktop or other clients, check the log files:

**macOS**:
```bash
# View MCP server logs
tail -f ~/Library/Logs/Claude/mcp-server-capital-com.log

# Search for errors
grep -i error ~/Library/Logs/Claude/mcp-server-capital-com.log
```

**Linux**:
```bash
tail -f ~/.config/Claude/logs/mcp-server-capital-com.log
```

**Windows**:
```powershell
Get-Content $env:APPDATA\Claude\logs\mcp-server-capital-com.log -Wait
```

## Integration with Claude Desktop

### macOS/Linux Setup

1. **Find Claude Desktop config location:**
   ```bash
   # macOS
   ~/Library/Application Support/Claude/claude_desktop_config.json

   # Linux
   ~/.config/Claude/claude_desktop_config.json
   ```

2. **Edit `claude_desktop_config.json`:**
   ```json
   {
     "mcpServers": {
       "capital-com": {
         "command": "/path/to/capital-mcp/venv/bin/python",
         "args": ["-m", "capital_mcp.server"],
         "env": {
           "CAP_ENV": "demo",
           "CAP_API_KEY": "your_api_key_here",
           "CAP_IDENTIFIER": "your_email@example.com",
           "CAP_API_PASSWORD": "your_custom_password",
           "CAP_ALLOW_TRADING": "false",
           "CAP_ALLOWED_EPICS": ""
         }
       }
     }
   }
   ```

   **Important**: Replace `/path/to/capital-mcp/venv/bin/python` with your actual virtual environment Python path. Get it by running:
   ```bash
   cd /path/to/capital-mcp
   source venv/bin/activate
   which python
   ```

3. **Restart Claude Desktop**

4. **Verify in Claude Desktop:**
   - Look for the 🔌 icon or "MCP" indicator
   - Type: "What Capital.com tools are available?"
   - Claude should list the 36 available tools

### Windows Setup

1. **Find Claude Desktop config:**
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```

2. **Edit configuration (use Windows paths):**
   ```json
   {
     "mcpServers": {
       "capital-com": {
         "command": "C:\\path\\to\\capital-mcp\\venv\\Scripts\\python.exe",
         "args": ["-m", "capital_mcp.server"],
         "env": {
           "CAP_ENV": "demo",
           "CAP_API_KEY": "your_api_key_here",
           "CAP_IDENTIFIER": "your_email@example.com",
           "CAP_API_PASSWORD": "your_custom_password",
           "CAP_ALLOW_TRADING": "false",
           "CAP_ALLOWED_EPICS": ""
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

## Integration with Cursor IDE

1. **Open Cursor Settings**: `Cmd+,` (Mac) or `Ctrl+,` (Windows/Linux)

2. **Navigate to**: Extensions > MCP > Configure

3. **Add server configuration** (similar to Claude Desktop):
   ```json
   {
     "capital-com": {
       "command": "/path/to/capital-mcp/venv/bin/python",
       "args": ["-m", "capital_mcp.server"],
       "env": {
         "CAP_ENV": "demo",
         "CAP_API_KEY": "your_api_key_here",
         "CAP_IDENTIFIER": "your_email@example.com",
         "CAP_API_PASSWORD": "your_custom_password",
         "CAP_ALLOW_TRADING": "false"
       }
     }
   }
   ```

4. **Restart Cursor**

5. **Test in AI chat**: Ask "List my Capital.com accounts"

## Integration with Windsurf

1. **Create/edit Windsurf MCP config**:
   ```bash
   mkdir -p ~/.windsurf/mcp
   nano ~/.windsurf/mcp/servers.json
   ```

2. **Add configuration**:
   ```json
   {
     "mcpServers": {
       "capital-com": {
         "command": "/path/to/capital-mcp/venv/bin/python",
         "args": ["-m", "capital_mcp.server"],
         "env": {
           "CAP_ENV": "demo",
           "CAP_API_KEY": "your_api_key_here",
           "CAP_IDENTIFIER": "your_email@example.com",
           "CAP_API_PASSWORD": "your_custom_password"
         }
       }
     }
   }
   ```

3. **Restart Windsurf**

## Integration with Custom MCP Clients

If you're building your own MCP client or using a different tool:

```typescript
// Example: Node.js MCP client
import { spawn } from 'child_process';

const server = spawn('/path/to/venv/bin/python', ['-m', 'capital_mcp.server'], {
  env: {
    ...process.env,
    CAP_ENV: 'demo',
    CAP_API_KEY: 'your_key',
    CAP_IDENTIFIER: 'your_email',
    CAP_API_PASSWORD: 'your_password',
    CAP_ALLOW_TRADING: 'false'
  }
});

// Communicate via STDIO (JSON-RPC)
// Read from server.stdout, write to server.stdin
```

## Using the Server

### Example Conversation with Claude Desktop

```
You: "Check my Capital.com session status"

Claude: I'll check your session status.
[Calls cap_session_status]
Response: {"ok": true, "data": {"env": "demo", "logged_in": false, ...}}

You're not currently logged in to the demo environment.

---

You: "Login to my Capital.com account"

Claude: I'll log you in.
[Calls cap_session_login]
Success! Logged in to account ID: ABC123

---

You: "Search for Bitcoin markets"

Claude: Searching for Bitcoin...
[Calls cap_market_search with search_term="Bitcoin"]
Found 5 markets:
- BTCUSD: Bitcoin vs US Dollar
- BTCEUR: Bitcoin vs Euro
- BTCGBP: Bitcoin vs British Pound
...

---

You: "Show me current positions"

Claude: Let me check your positions.
[Calls cap_trade_positions_list]
You have no open positions.

---

You: "Preview buying 1.0 SILVER"

Claude: I'll preview this trade. Note: Trading is currently DISABLED.
[Calls cap_trade_preview_position]
Preview failed: Trading is disabled (CAP_ALLOW_TRADING=false)

To enable trading, update your .env file:
CAP_ALLOW_TRADING=true
CAP_ALLOWED_EPICS=SILVER
```

### Safe Trading Workflow (When Trading Enabled)

```
1. Preview the trade (validates everything, no side effects):
   "Preview buying 2.0 SILVER with stop at 24.50"
   → Returns preview_id

2. Review the preview results:
   - Normalized size (rounded to broker increments)
   - Risk checks (allowlist, size limits, daily limits)
   - Estimated entry price

3. Execute ONLY if all checks pass:
   "Execute position with preview_id [id], confirm=true"
   → Creates real position
   → Returns deal_reference
   → Polls for broker confirmation

4. Monitor:
   "Show my positions"
   "Close position [deal_id] with confirm=true"
```

## Architecture

```
LLM Client (Claude Desktop/Cursor)
  ↕ STDIO (JSON-RPC)
MCP Server (capital_mcp/)
  ├─ server.py          # FastMCP server + tool registrations
  ├─ session.py         # SessionManager (login, refresh, ping)
  ├─ capital_client.py  # HTTP client (httpx, rate limits)
  ├─ risk.py            # RiskEngine (preview, validation)
  ├─ config.py          # Configuration (env vars)
  ├─ models.py          # Pydantic data models
  ├─ errors.py          # Error codes & exceptions
  ├─ rate_limit.py      # Token bucket rate limiter
  └─ utils.py           # Helper functions
```

## Environment Variables Reference

### Required
- `CAP_ENV` - Environment: `demo` or `live` (default: demo)
- `CAP_API_KEY` - API key from Capital.com
- `CAP_IDENTIFIER` - Login email
- `CAP_API_PASSWORD` - API key custom password

### Safety Controls (Recommended)
- `CAP_ALLOW_TRADING` - Enable trading (default: false)
- `CAP_ALLOWED_EPICS` - Comma-separated allowlist (e.g., "SILVER,GOLD,BTCUSD") or "ALL" for unrestricted
- `CAP_MAX_POSITION_SIZE` - Max position size (default: 1.0)
- `CAP_MAX_WORKING_ORDER_SIZE` - Max order size (default: 1.0)
- `CAP_MAX_OPEN_POSITIONS` - Max concurrent positions (default: 3)
- `CAP_MAX_ORDERS_PER_DAY` - Daily order limit (default: 20)
- `CAP_REQUIRE_EXPLICIT_CONFIRM` - Require confirm=true (default: true)
- `CAP_DRY_RUN` - Block all trade executions (default: false)

### Optional
- `CAP_DEFAULT_ACCOUNT_ID` - Default account after login
- `CAP_HTTP_TIMEOUT_S` - HTTP timeout (default: 15)
- `CAP_LOG_LEVEL` - Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)

## MCP Tools (36 implemented)

### Session (4)
- `cap.session.status` - Get session info
- `cap.session.login` - Create session
- `cap.session.ping` - Keep alive
- `cap.session.logout` - End session

### Market Data (6)
- `cap.market.search` - Search markets
- `cap.market.get` - Get market details
- `cap.market.prices` - Historical prices
- `cap.market.sentiment` - Client sentiment
- `cap.market.navigation_root` - Market categories root
- `cap.market.navigation_node` - Market categories node

### Account (6)
- `cap.account.list` - List accounts
- `cap.account.preferences.get` - Get preferences
- `cap.account.preferences.set` - Set preferences
- `cap.account.history.activity` - Activity history
- `cap.account.history.transactions` - Transaction history
- `cap.account.demo.topup` - Top up demo account

### Trading (14)
- **Read-only:**
  - `cap.trade.positions.list` - List positions
  - `cap.trade.positions.get` - Get position details
  - `cap.trade.orders.list` - List working orders
  - `cap.trade.confirm.get` - Get confirmation status
  - `cap.trade.confirm.wait` - Wait for confirmation

- **Preview (safe):**
  - `cap.trade.preview_position` - Preview position
  - `cap.trade.preview_working_order` - Preview order

- **Execute (guarded):**
  - `cap.trade.execute_position` - Execute position
  - `cap.trade.execute_working_order` - Execute order
  - `cap.trade.positions.update` - Update position
  - `cap.trade.positions.close` - Close position
  - `cap.trade.orders.update` - Update order
  - `cap.trade.orders.cancel` - Cancel order

### Watchlists (6)
- `cap.watchlists.list` - List watchlists
- `cap.watchlists.create` - Create watchlist
- `cap.watchlists.get` - Get watchlist
- `cap.watchlists.add_market` - Add market
- `cap.watchlists.delete` - Delete watchlist
- `cap.watchlists.remove_market` - Remove market

## MCP Prompts (Workflow Templates)

MCP prompts are structured workflows that guide Claude through complex multi-step trading operations. They provide step-by-step instructions and best practices for common tasks.

### Available Prompts (4)

#### 1. `market_scan` - Market Analysis Workflow
Guides you through scanning a watchlist for trading opportunities.

**Parameters:**
- `watchlist_id` - Watchlist to scan (leave empty to list watchlists first)
- `timeframe` - Price resolution: MINUTE, MINUTE_5, HOUR, DAY (default: HOUR)
- `lookback_periods` - Number of candles to fetch: 1-1000 (default: 24)

**Workflow:**
1. Get watchlist markets
2. Fetch price data for each market
3. Technical analysis (trends, support/resistance, patterns)
4. Optional sentiment check
5. Generate opportunity summary

**Example Usage:**
- "Use the market_scan prompt to analyze my watchlist"
- "Scan my markets for trading setups"

#### 2. `trade_proposal` - Trade Planning Workflow
Guides you through creating a trade proposal with proper risk management.

**Parameters:**
- `epic` - Market to trade (required, e.g., SILVER, GOLD)
- `direction` - BUY or SELL (default: BUY)
- `thesis` - Your trading reasoning (optional)
- `risk_percent` - Risk as % of balance (default: 1.0%)

**Workflow:**
1. Fetch market details and dealing rules
2. Calculate position size based on risk %
3. Define stop loss and take profit levels
4. Preview the trade (validation only - no execution)
5. Return preview_id for potential execution

**Example Usage:**
- "Create a trade proposal for SILVER"
- "Propose a long trade on GOLD with 2% risk"

**Safety:** This prompt does NOT execute trades - it only creates previews.

#### 3. `execute_trade` - Trade Execution Workflow
Guides you through executing a previewed trade safely.

**Parameters:**
- `preview_id` - Preview ID from trade_proposal (required)

**Workflow:**
1. Verify preview_id is provided and valid
2. Re-check all risk controls
3. Execute position with broker
4. Poll for confirmation (ACCEPTED/REJECTED)
5. Report final status

**Example Usage:**
- "Execute the trade I just previewed"
- "Place the trade with preview ID abc-123"

**Safety:**
- Requires CAP_ALLOW_TRADING=true
- Requires epic in allowlist
- Preview must not be expired (2-minute TTL)
- ⚠️ **This WILL place a real trade**

#### 4. `position_review` - Portfolio Analysis Workflow
Guides you through analyzing your open positions and orders.

**Parameters:** None (analyzes all current positions)

**Workflow:**
1. Fetch all open positions
2. Fetch all working orders
3. Calculate P&L, risk, and exposure metrics
4. Identify concentration and correlation risks
5. Suggest potential adjustments (without executing)

**Example Usage:**
- "Review my current positions"
- "Analyze my portfolio exposure"

**Safety:** This is a read-only workflow - no trades are executed.

### How to Use Prompts

In Claude Desktop or other MCP clients, prompts appear as available interaction patterns. You can invoke them naturally in conversation:

```
User: "I want to scan my watchlist for opportunities"
Claude: [Invokes market_scan prompt, guides through the workflow]

User: "Create a trade plan for SILVER"
Claude: [Invokes trade_proposal prompt, designs trade with risk management]

User: "Execute that trade"
Claude: [Invokes execute_trade prompt, submits to broker]

User: "Show me my open positions"
Claude: [Invokes position_review prompt, analyzes portfolio]
```

Prompts provide structured guidance while maintaining safety controls throughout the workflow.

## MCP Resources (Read-Only Data)

MCP resources provide read-only access to server state and configuration through URI-based resources. Unlike tools (which perform actions), resources expose data that clients can read and monitor.

### Available Resources

#### 1. `cap://status` - Server Status

Real-time server and session information.

**Returns**: JSON with server health, session state, authentication status, rate limits

**Example**:
```json
{
  "server": {
    "name": "Capital.com MCP Server",
    "version": "0.1.0",
    "trading_enabled": true
  },
  "session": {
    "is_logged_in": true,
    "account_id": "ABC123",
    "last_activity": "2026-01-16T10:30:00"
  },
  "risk": {
    "trading_enabled": true,
    "allowed_epics": ["GOLD", "SILVER"],
    "allowlist_mode": "SPECIFIC"
  },
  "rate_limits": {
    "requests_per_second": "10",
    "note": "Capital.com enforces 10 req/s limit"
  }
}
```

**Use Cases**: Monitor server health, check session status, debug authentication issues

---

#### 2. `cap://risk-policy` - Risk Policy

Comprehensive risk management configuration and safety controls.

**Returns**: JSON with all validation layers, safety features, and trading restrictions

**Example**:
```json
{
  "trading_enabled": true,
  "two_phase_execution": true,
  "description": "All trades require preview → explicit execution",
  "allowlist": {
    "mode": "SPECIFIC",
    "epics": ["GOLD", "SILVER"],
    "note": "Only markets on this list can be traded (ALL = wildcard)"
  },
  "validation_layers": [
    "1. Trading enabled check (TRADING_ENABLED env var)",
    "2. Epic allowlist check (must be in ALLOWED_EPICS)",
    "... 10 total layers ..."
  ],
  "safety_features": {
    "preview_required": true,
    "deal_reference_matching": true,
    "authentication_required": true,
    "rate_limiting": true,
    "input_validation": true
  }
}
```

**Use Cases**: Understand active safety controls, audit risk configuration, compliance documentation

---

#### 3. `cap://allowed-epics` - Trading Allowlist

Current trading allowlist configuration showing permitted markets.

**Returns**: JSON with allowlist mode, permitted epics, and configuration instructions

**Example**:
```json
{
  "mode": "SPECIFIC",
  "allowed_epics": ["GOLD", "SILVER", "BTCUSD"],
  "count": 3,
  "trading_enabled": true,
  "description": "Restricted mode: 3 specific markets allowed",
  "configuration": {
    "env_var": "ALLOWED_EPICS",
    "example": "ALLOWED_EPICS=GOLD,SILVER,BTCUSD",
    "wildcard": "ALLOWED_EPICS=ALL (allows all markets)"
  }
}
```

**Use Cases**: Check which markets are tradeable, verify allowlist configuration

---

#### 4. `cap://market-cache/{epic}` - Market Details (Dynamic)

Cached market details for a specific epic (live fetch from broker).

**Parameters**:
- `epic` - Market identifier (e.g., "GOLD", "SILVER", "CS.D.EURUSD.TODAY.IP")

**Returns**: JSON with comprehensive market information

**Authentication**: Required

**Example**: `cap://market-cache/GOLD`

```json
{
  "epic": "GOLD",
  "instrument_name": "Spot Gold",
  "instrument_type": "COMMODITIES",
  "currency": "USD",
  "snapshot": {
    "market_status": "TRADEABLE",
    "bid": 2050.50,
    "offer": 2050.75,
    "update_time": "2026-01-16T10:30:00"
  },
  "dealing": {
    "min_size": 0.1,
    "max_size": 100.0,
    "min_step": 0.1,
    "min_stop_distance": 5.0
  },
  "margin": {
    "factor": 5.0,
    "unit": "PERCENTAGE"
  },
  "opening_hours": {...},
  "cached_at": "2026-01-16T10:30:00"
}
```

**Use Cases**: Get market details, check trading rules, analyze margin requirements

---

### How to Use Resources

In Claude Desktop or other MCP clients, resources can be accessed by URI:

```
User: "Show me the server status"
Claude: [Reads cap://status resource, displays server health]

User: "What's the risk policy?"
Claude: [Reads cap://risk-policy resource, explains safety controls]

User: "Which markets can I trade?"
Claude: [Reads cap://allowed-epics resource, lists permitted epics]

User: "Show all my watchlists"
Claude: [Calls cap_watchlists_list tool, displays watchlist data]

User: "Get details for GOLD market"
Claude: [Reads cap://market-cache/GOLD resource, shows market info]
```

Resources provide a convenient way to inspect server state and configuration without running tools. For watchlist data, use the `cap_watchlists_list` and `cap_watchlists_get` tools.

## Safety Model

### Two-Phase Execution
All side-effect operations use a strict preview → execute flow:

1. **Preview**: Validate trade against broker rules + local risk policy
   - Returns `preview_id` with normalized request + risk checks
   - No side effects, read-only validation

2. **Execute**: Submit trade using `preview_id`
   - Re-runs critical checks
   - Requires `confirm=true` if `CAP_REQUIRE_EXPLICIT_CONFIRM=true`
   - Polls broker confirmation
   - Increments daily order counter

### Risk Guardrails
- **Allowlist**: Only EPICs in `CAP_ALLOWED_EPICS` can be traded
- **Size Limits**: Max position/order size enforced
- **Position Limits**: Max open positions at any time
- **Daily Limits**: Max orders per day
- **Size Normalization**: Rounds to broker min/max/increment
- **Dry-Run Mode**: Blocks all executions when enabled

## Development

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=capital_mcp --cov-report=html

# Run specific test file
pytest tests/test_mcp_registration.py

# Run in verbose mode
pytest -v
```

Current test coverage:
- 13 tests (all passing)
- MCP registration validation (tools, resources, prompts)
- Import and module structure tests
- Prompt schema validation

### Code Quality
```bash
# Format
black capital_mcp/

# Lint
ruff check capital_mcp/

# Type check
mypy capital_mcp/
```

## Documentation

- **Usage Guide**: [USAGE.md](USAGE.md) - Comprehensive usage guide with examples
- **Implementation Summary**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Project overview
- **Capital.com API Reference**: https://open-api.capital.com/
- **Capital.com API Postman Collection**: https://github.com/capital-com-sv/capital-api-postman

## License

MIT

## Disclaimer

This software is provided "as is" for educational and engineering purposes. Trading financial instruments involves risk of loss. The authors assume no responsibility for any financial losses incurred through use of this software. Always test thoroughly on Demo accounts before considering live trading.
