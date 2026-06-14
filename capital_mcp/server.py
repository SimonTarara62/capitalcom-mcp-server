"""MCP server for the Capital.com Open API — a thin FastMCP layer over the
capital_cli SDK (capital_cli.sdk.CapitalComApp). All broker logic lives in the
SDK; this module only maps MCP tools/resources/prompts onto SDK calls.
"""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import FastMCP

from .context import get_app, lifespan

logger = logging.getLogger(__name__)

# The `instructions` are sent to the client/agent as the server's usage guide:
# how to pick the right tool and the mandatory order of operations.
INSTRUCTIONS = """\
Capital.com trading + market-data server (built on the capitalcom-cli SDK).

WHAT YOU CAN DO
- Markets: cap_market_search (find an EPIC by name) -> cap_market_get (dealing
  rules, min/max size, current bid/offer) -> cap_market_prices (historical OHLC)
  / cap_market_sentiment (long-vs-short %) / cap_market_navigation_root +
  cap_market_navigation_node (browse the category tree).
- Account: cap_account_list, cap_account_preferences_get/set,
  cap_account_history_activity/transactions, cap_account_demo_topup (demo only),
  cap_session_switch_account (change the active account).
- Watchlists: cap_watchlists_list/get/create/add_market/remove_market/delete.
- Positions/orders (read): cap_trade_positions_list/get, cap_trade_orders_list.
- Live data (WebSocket; needs CAP_WS_ENABLED): cap_stream_prices (ticks),
  cap_stream_candles (OHLC bars), cap_stream_alerts (price-level crossings),
  cap_stream_portfolio (open-position ticks).

HOW TO TRADE — ALWAYS TWO PHASES, NEVER SKIP THE PREVIEW
1. PREVIEW (no side effects): cap_trade_preview_position (market order) or
   cap_trade_preview_working_order (pending LIMIT/STOP). Read the returned
   `checks` / `all_checks_passed`. If all_checks_passed is false, DO NOT execute
   — fix size/stops or stop and tell the user why.
2. EXECUTE only a passing preview, by its preview_id: cap_trade_execute_position
   / cap_trade_execute_working_order with confirm=true. Previews expire after
   ~120s — re-preview if stale.
3. MANAGE: cap_trade_positions_amend / cap_trade_orders_amend to change
   stops/limits/level; cap_trade_positions_close / cap_trade_orders_cancel to
   exit. All mutations need confirm=true.
4. CONFIRM: execute/close/cancel can wait for confirmation (wait_for_confirm).
   To poll separately use cap_trade_confirm_get (one-shot) or
   cap_trade_confirm_wait (until ACCEPTED/REJECTED). A {"status":"TIMEOUT"}
   result is AMBIGUOUS — the order may have landed; reconcile with
   cap_trade_positions_list / cap_trade_orders_list before retrying. Never blindly
   re-run an execute/close/cancel on TIMEOUT (there is no broker idempotency key).

SAFETY (enforced server-side by the SDK risk engine — do not try to bypass)
- Trading is OFF unless CAP_ALLOW_TRADING=true AND the EPIC is in
  CAP_ALLOWED_EPICS (or "ALL"). Size, open-position, and daily-order caps apply.
- Inspect the live policy via the resources cap://status, cap://risk-policy,
  cap://allowed-epics before proposing a trade.
- Prefer the demo environment (CAP_ENV=demo) until a workflow is proven.
"""

mcp = FastMCP("Capital.com MCP Server", instructions=INSTRUCTIONS, lifespan=lifespan)


# ============================================================
# Session tools
# ============================================================


@mcp.tool()
async def cap_session_status() -> dict[str, Any]:
    """Get current session status (login state, account, token expiry). No auth required."""
    return get_app().session.get_status().model_dump()


@mcp.tool()
async def cap_session_login(force: bool = False, account_id: str | None = None) -> dict[str, Any]:
    """Create or verify a session. force=true re-logs in; account_id switches account."""
    app = get_app()
    data = await app.session.login(force=force, account_id=account_id)
    data["active_account_id"] = app.session.get_status().account_id
    return data


@mcp.tool()
async def cap_session_ping() -> dict[str, Any]:
    """Keep the session alive (extends timeout). Requires authentication."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.session.ping()


@mcp.tool()
async def cap_session_logout() -> dict[str, str]:
    """End the session and clear tokens. Requires authentication."""
    await get_app().session.logout()
    return {"message": "Logged out successfully"}


@mcp.tool()
async def cap_session_switch_account(account_id: str) -> dict[str, Any]:
    """Switch the active trading account by ID. Requires authentication."""
    app = get_app()
    await app.session.ensure_logged_in()
    data = await app.session.switch_account(account_id)
    data["active_account_id"] = app.session.get_status().account_id
    return data


# ============================================================
# Market data tools
# ============================================================


@mcp.tool()
async def cap_market_search(
    search_term: str | None = None,
    epics: list[str] | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search markets by term or EPIC list. limit truncates results client-side."""
    app = get_app()
    await app.session.ensure_logged_in()
    epics_param = ",".join(epics) if epics else None
    return await app.markets.search(search_term, epics=epics_param, limit=limit)


@mcp.tool()
async def cap_market_get(epic: str) -> dict[str, Any]:
    """Get full market details and dealing rules for an EPIC."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.markets.get(epic)


@mcp.tool()
async def cap_market_navigation_root() -> dict[str, Any]:
    """Get the root market-navigation tree (categories)."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.markets.navigation_root()


@mcp.tool()
async def cap_market_navigation_node(node_id: str) -> dict[str, Any]:
    """Get child nodes/markets under a navigation node."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.markets.navigation_node(node_id)


@mcp.tool()
async def cap_market_prices(
    epic: str,
    resolution: str = "MINUTE_15",
    max: int = 200,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, Any]:
    """Get historical OHLC candles. resolution e.g. MINUTE_15, HOUR, DAY."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.markets.prices(
        epic, resolution=resolution, max_candles=max, from_date=from_date, to_date=to_date
    )


@mcp.tool()
async def cap_market_sentiment(market_id: str) -> dict[str, Any]:
    """Get client sentiment (long vs short %) for a market."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.markets.sentiment([market_id])


# ============================================================
# Account tools
# ============================================================


@mcp.tool()
async def cap_account_list() -> dict[str, Any]:
    """List all trading accounts (balance, currency, type). Requires authentication."""
    app = get_app()
    await app.session.ensure_logged_in()
    data = await app.accounts.list()
    data["active_account_id"] = app.session.get_status().account_id
    return data


@mcp.tool()
async def cap_account_preferences_get() -> dict[str, Any]:
    """Get account preferences (hedging mode, per-asset-class leverage)."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.accounts.get_preferences()


@mcp.tool()
async def cap_account_preferences_set(
    hedging_mode: bool | None = None,
    leverages: dict[str, int] | None = None,
    confirm: bool = False,
) -> dict[str, Any]:
    """Set account preferences (TRADE-GATED). Requires confirm=true when configured."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.accounts.set_preferences(
        hedging=hedging_mode, leverages=leverages, confirm=confirm
    )


@mcp.tool()
async def cap_account_history_activity(
    from_date: str | None = None,
    to_date: str | None = None,
    last_period: int = 600,
    detailed: bool = False,
    deal_id: str | None = None,
) -> dict[str, Any]:
    """Get account activity history (deals, orders, updates). detailed adds fields; deal_id filters."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.accounts.history_activity(
        last_period=last_period,
        from_date=from_date,
        to_date=to_date,
        detailed=detailed,
        deal_id=deal_id,
    )


@mcp.tool()
async def cap_account_history_transactions(
    from_date: str | None = None,
    to_date: str | None = None,
    last_period: int = 600,
    type: str | None = None,
) -> dict[str, Any]:
    """Get transaction history (deposits, withdrawals, P&L). Optional type filter."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.accounts.history_transactions(
        last_period=last_period, type_=type, from_date=from_date, to_date=to_date
    )


@mcp.tool()
async def cap_account_demo_topup(amount: float, confirm: bool = False) -> dict[str, Any]:
    """Top up the demo account balance (DEMO ONLY). The SDK enforces demo + confirm."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.accounts.demo_topup(amount, confirm=confirm)
