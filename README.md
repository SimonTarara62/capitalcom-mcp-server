# Capital.com MCP Server

Model Context Protocol (MCP) server for Capital.com Open API - enabling safe, LLM-driven trading operations.

## ⚠️ Important Safety Notice

**Trading is risky. This software is for engineering/educational purposes and is NOT financial advice.**

- Always start with a **Demo account** before considering live trading
- Trading is **disabled by default** and requires explicit configuration
- All trade operations require **two-phase execution** (preview → confirm → execute)
- Built-in risk controls: allowlists, size limits, daily order caps

## Current Implementation Status

### ✅ Completed (Phases 1-4)

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

### 📋 Pending (Phase 5-7)

- MCP Resources (cap://status, cap://risk-policy, etc.)
- MCP Prompts (workflow templates for safe trading)
- WebSocket support (optional, live streaming)
- Comprehensive testing suite (unit, integration, acceptance)
- Enhanced documentation & examples

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

## MCP Tools (Planned - 50+ tools)

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

### Run Tests (once implemented)
```bash
pytest
```

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
