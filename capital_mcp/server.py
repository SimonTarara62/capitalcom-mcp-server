"""MCP server for the Capital.com Open API — a thin FastMCP layer over the
capital_cli SDK (capital_cli.sdk.CapitalComApp). All broker logic lives in the
SDK; this module only maps MCP tools/resources/prompts onto SDK calls.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from capital_cli.core.models import (
    Direction,
    PreviewPositionRequest,
    PreviewWorkingOrderRequest,
    WorkingOrderType,
)
from capital_cli.services.confirmations import get_confirmation, wait_for_confirmation
from fastmcp import FastMCP

from .context import get_app, lifespan
from .serialization import preview_to_dict

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


def _version() -> str:
    from capital_mcp import __version__

    return __version__


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


# ============================================================
# Trading tools — read-only + confirmations
# ============================================================


@mcp.tool()
async def cap_trade_positions_list() -> dict[str, Any]:
    """List all open positions (P&L, direction, size, attached orders)."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.trading.list_positions()


@mcp.tool()
async def cap_trade_positions_get(deal_id: str) -> dict[str, Any]:
    """Get a single position's details by deal ID."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.trading.get_position(deal_id)


@mcp.tool()
async def cap_trade_orders_list() -> dict[str, Any]:
    """List all working orders (pending LIMIT/STOP that haven't triggered)."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.trading.list_orders()


@mcp.tool()
async def cap_trade_confirm_get(deal_reference: str) -> dict[str, Any]:
    """Get deal-confirmation status (ACCEPTED/REJECTED/pending) for a deal reference."""
    await get_app().session.ensure_logged_in()
    return await get_confirmation(deal_reference)


@mcp.tool()
async def cap_trade_confirm_wait(
    deal_reference: str,
    timeout_s: float = 15.0,
    poll_interval_ms: int = 500,
) -> dict[str, Any]:
    """Poll the confirmation endpoint until ACCEPTED/REJECTED or timeout."""
    await get_app().session.ensure_logged_in()
    return await wait_for_confirmation(
        deal_reference, timeout_s=timeout_s, poll_interval_ms=poll_interval_ms
    )


# ============================================================
# Trading tools — preview (no side effects)
# ============================================================


@mcp.tool()
async def cap_trade_preview_position(
    epic: str,
    direction: str,
    size: float,
    guaranteed_stop: bool = False,
    trailing_stop: bool = False,
    stop_level: float | None = None,
    stop_distance: float | None = None,
    stop_amount: float | None = None,
    profit_level: float | None = None,
    profit_distance: float | None = None,
    profit_amount: float | None = None,
) -> dict[str, Any]:
    """Preview a position (NO SIDE EFFECTS). Runs the full risk pipeline; returns preview_id."""
    app = get_app()
    await app.session.ensure_logged_in()
    request = PreviewPositionRequest(
        epic=epic,
        direction=Direction(direction.upper()),
        size=size,
        guaranteed_stop=guaranteed_stop,
        trailing_stop=trailing_stop,
        stop_level=stop_level,
        stop_distance=stop_distance,
        stop_amount=stop_amount,
        profit_level=profit_level,
        profit_distance=profit_distance,
        profit_amount=profit_amount,
    )
    preview = await app.trading.preview_position(request)
    return preview_to_dict(preview)


@mcp.tool()
async def cap_trade_preview_working_order(
    epic: str,
    direction: str,
    type: str,
    level: float,
    size: float,
    guaranteed_stop: bool = False,
    trailing_stop: bool = False,
    stop_level: float | None = None,
    stop_distance: float | None = None,
    stop_amount: float | None = None,
    profit_level: float | None = None,
    profit_distance: float | None = None,
    profit_amount: float | None = None,
    good_till_date: str | None = None,
) -> dict[str, Any]:
    """Preview a working order (NO SIDE EFFECTS). type is LIMIT or STOP. Returns preview_id."""
    app = get_app()
    await app.session.ensure_logged_in()
    request = PreviewWorkingOrderRequest(
        epic=epic,
        direction=Direction(direction.upper()),
        type=WorkingOrderType(type.upper()),
        level=level,
        size=size,
        guaranteed_stop=guaranteed_stop,
        trailing_stop=trailing_stop,
        stop_level=stop_level,
        stop_distance=stop_distance,
        stop_amount=stop_amount,
        profit_level=profit_level,
        profit_distance=profit_distance,
        profit_amount=profit_amount,
        good_till_date=good_till_date,
    )
    preview = await app.trading.preview_working_order(request)
    return preview_to_dict(preview)


# ============================================================
# Trading tools — execute / close / cancel (side effects, guarded by the SDK)
# ============================================================


@mcp.tool()
async def cap_trade_execute_position(
    preview_id: str,
    confirm: bool = False,
    wait_for_confirm: bool = True,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    """Execute a previewed position (CREATES A REAL TRADE). SDK enforces all safety gates."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.trading.execute_position(
        preview_id, confirm=confirm, wait=wait_for_confirm, timeout_s=timeout_s
    )


@mcp.tool()
async def cap_trade_execute_working_order(
    preview_id: str,
    confirm: bool = False,
    wait_for_confirm: bool = True,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    """Execute a previewed working order (CREATES A REAL ORDER). SDK enforces all safety gates."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.trading.execute_working_order(
        preview_id, confirm=confirm, wait=wait_for_confirm, timeout_s=timeout_s
    )


@mcp.tool()
async def cap_trade_positions_close(
    deal_id: str,
    confirm: bool = False,
    wait_for_confirm: bool = True,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    """Close an open position (SIDE EFFECT). Requires confirm + trading enabled."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.trading.close_position(
        deal_id, confirm=confirm, wait=wait_for_confirm, timeout_s=timeout_s
    )


@mcp.tool()
async def cap_trade_orders_cancel(
    deal_id: str,
    confirm: bool = False,
    wait_for_confirm: bool = True,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    """Cancel a working order (SIDE EFFECT). Requires confirm + trading enabled."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.trading.cancel_order(
        deal_id, confirm=confirm, wait=wait_for_confirm, timeout_s=timeout_s
    )


# ============================================================
# Trading tools — amend (side effects, guarded by the SDK)
# ============================================================


@mcp.tool()
async def cap_trade_positions_amend(
    deal_id: str,
    stop_level: float | None = None,
    stop_distance: float | None = None,
    profit_level: float | None = None,
    profit_distance: float | None = None,
    guaranteed_stop: bool | None = None,
    trailing_stop: bool | None = None,
    confirm: bool = False,
    wait_for_confirm: bool = True,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    """Amend stop-loss / take-profit on an open position (SIDE EFFECT). Requires confirm."""
    app = get_app()
    await app.session.ensure_logged_in()
    body: dict[str, Any] = {}
    if stop_level is not None:
        body["stopLevel"] = stop_level
    if stop_distance is not None:
        body["stopDistance"] = stop_distance
    if profit_level is not None:
        body["profitLevel"] = profit_level
    if profit_distance is not None:
        body["profitDistance"] = profit_distance
    if guaranteed_stop is not None:
        body["guaranteedStop"] = guaranteed_stop
    if trailing_stop is not None:
        body["trailingStop"] = trailing_stop
    return await app.trading.amend_position(
        deal_id, body=body, confirm=confirm, wait=wait_for_confirm, timeout_s=timeout_s
    )


@mcp.tool()
async def cap_trade_orders_amend(
    deal_id: str,
    level: float | None = None,
    stop_level: float | None = None,
    stop_distance: float | None = None,
    profit_level: float | None = None,
    profit_distance: float | None = None,
    good_till_date: str | None = None,
    confirm: bool = False,
    wait_for_confirm: bool = True,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    """Amend a working order's level/expiry/stops-limits (SIDE EFFECT). Requires confirm."""
    app = get_app()
    await app.session.ensure_logged_in()
    body: dict[str, Any] = {}
    if level is not None:
        body["level"] = level
    if stop_level is not None:
        body["stopLevel"] = stop_level
    if stop_distance is not None:
        body["stopDistance"] = stop_distance
    if profit_level is not None:
        body["profitLevel"] = profit_level
    if profit_distance is not None:
        body["profitDistance"] = profit_distance
    if good_till_date is not None:
        body["goodTillDate"] = good_till_date
    return await app.trading.amend_order(
        deal_id, body=body, confirm=confirm, wait=wait_for_confirm, timeout_s=timeout_s
    )


# ============================================================
# Watchlist tools
# ============================================================


@mcp.tool()
async def cap_watchlists_list() -> dict[str, Any]:
    """List all watchlists (IDs and names)."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.watchlists.list()


@mcp.tool()
async def cap_watchlists_get(watchlist_id: str) -> dict[str, Any]:
    """Get a watchlist's details including its markets."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.watchlists.get(watchlist_id)


@mcp.tool()
async def cap_watchlists_create(name: str, confirm: bool = False) -> dict[str, Any]:
    """Create a new watchlist (1-100 chars). Requires confirm when configured."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.watchlists.create(name, confirm=confirm)


@mcp.tool()
async def cap_watchlists_add_market(
    watchlist_id: str, epic: str, confirm: bool = False
) -> dict[str, Any]:
    """Add a market (EPIC) to a watchlist. Requires confirm when configured."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.watchlists.add_market(watchlist_id, epic, confirm=confirm)


@mcp.tool()
async def cap_watchlists_remove_market(
    watchlist_id: str, epic: str, confirm: bool = False
) -> dict[str, Any]:
    """Remove a market (EPIC) from a watchlist. Requires confirm when configured."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.watchlists.remove_market(watchlist_id, epic, confirm=confirm)


@mcp.tool()
async def cap_watchlists_delete(watchlist_id: str, confirm: bool = False) -> dict[str, Any]:
    """Delete a watchlist. Requires confirm when configured."""
    app = get_app()
    await app.session.ensure_logged_in()
    return await app.watchlists.delete(watchlist_id, confirm=confirm)


# ============================================================
# Streaming tools (WebSocket; engine via app.stream)
# ============================================================


@mcp.tool()
async def cap_stream_prices(
    epics: list[str],
    duration_s: float = 300.0,
    update_interval_s: float = 1.0,
) -> dict[str, Any]:
    """Stream live bid/offer for up to 40 EPICs for duration_s seconds (WebSocket)."""
    if not epics:
        return {"error": "No EPICs provided", "message": "Specify at least one EPIC."}
    if len(epics) > 40:
        return {
            "error": "Too many EPICs",
            "message": f"Max 40 concurrent subscriptions (requested: {len(epics)}).",
            "max_allowed": 40,
        }
    app = get_app()
    await app.session.ensure_logged_in()
    ticks: list[dict[str, Any]] = []
    last = datetime.now(timezone.utc)
    try:
        async for tick in app.stream.prices(epics, duration=duration_s):
            now = datetime.now(timezone.utc)
            if (now - last).total_seconds() >= update_interval_s:
                ticks.append(tick.model_dump())
                last = now
        return {
            "status": "completed",
            "epics_monitored": epics,
            "duration_s": duration_s,
            "ticks_received": len(ticks),
            "ticks": ticks[-100:],
        }
    except Exception as e:  # surface streaming errors as data
        return {"error": "Streaming failed", "message": str(e), "ticks_before_error": len(ticks)}


@mcp.tool()
async def cap_stream_candles(
    epics: list[str],
    resolutions: list[str],
    bar_type: str = "classic",
    duration_s: float = 300.0,
    update_interval_s: float = 1.0,
) -> dict[str, Any]:
    """Stream live OHLC bars for up to 40 EPICs at the given resolutions (WebSocket).

    resolutions e.g. ["MINUTE", "HOUR"]; bar_type "classic" or "heikin-ashi".
    """
    if not epics:
        return {"error": "No EPICs provided", "message": "Specify at least one EPIC."}
    if len(epics) > 40:
        return {
            "error": "Too many EPICs",
            "message": f"Max 40 concurrent subscriptions (requested: {len(epics)}).",
            "max_allowed": 40,
        }
    if not resolutions:
        return {"error": "No resolutions provided", "message": "Specify at least one resolution."}
    app = get_app()
    await app.session.ensure_logged_in()
    bars: list[dict[str, Any]] = []
    last = datetime.now(timezone.utc)
    try:
        async for bar in app.stream.candles(
            epics, resolutions, bar_type=bar_type, duration=duration_s
        ):
            now = datetime.now(timezone.utc)
            if (now - last).total_seconds() >= update_interval_s:
                bars.append(bar.model_dump())
                last = now
        return {
            "status": "completed",
            "epics_monitored": epics,
            "resolutions": resolutions,
            "bars_received": len(bars),
            "bars": bars[-100:],
        }
    except Exception as e:  # noqa: BLE001
        return {"error": "Streaming failed", "message": str(e), "bars_before_error": len(bars)}


@mcp.tool()
async def cap_stream_alerts(
    alerts: dict[str, dict[str, Any]],
    duration_s: float = 300.0,
    auto_close: bool = False,
) -> dict[str, Any]:
    """Monitor EPICs for price-level crossings. alerts: {EPIC: {level, direction: ABOVE|BELOW}}."""
    if not alerts:
        return {"error": "No alerts configured", "message": "Specify at least one alert."}
    epics = list(alerts.keys())
    if len(epics) > 40:
        return {"error": "Too many alerts", "message": f"Max 40 (requested: {len(epics)})."}
    app = get_app()
    await app.session.ensure_logged_in()
    triggered: list[dict[str, Any]] = []
    triggered_epics: set[str] = set()
    try:
        async for tick in app.stream.prices(epics, duration=duration_s):
            if auto_close and tick.epic in triggered_epics:
                continue
            cfg = alerts.get(tick.epic)
            if not cfg:
                continue
            level = float(cfg["level"])
            direction = str(cfg["direction"]).upper()
            mid = (tick.bid + tick.offer) / 2
            hit = (direction == "ABOVE" and mid >= level) or (direction == "BELOW" and mid <= level)
            if hit:
                triggered.append(
                    {
                        "epic": tick.epic,
                        "condition": f"LEVEL_{direction}",
                        "trigger_price": level,
                        "current_price": mid,
                    }
                )
                triggered_epics.add(tick.epic)
                if auto_close and len(triggered_epics) == len(epics):
                    break
        return {
            "status": "completed",
            "alerts_configured": len(alerts),
            "alerts_triggered": len(triggered),
            "triggered_alerts": triggered,
            "auto_close": auto_close,
        }
    except Exception as e:  # noqa: BLE001
        return {
            "error": "Alert monitoring failed",
            "message": str(e),
            "triggered_alerts": triggered,
        }


@mcp.tool()
async def cap_stream_portfolio(
    duration_s: float = 300.0,
    update_interval_s: float = 5.0,
) -> dict[str, Any]:
    """Stream live portfolio snapshots for open positions for duration_s seconds (WebSocket)."""
    app = get_app()
    await app.session.ensure_logged_in()
    try:
        positions = (await app.trading.list_positions()).get("positions", [])
        if not positions:
            return {"status": "no_positions", "message": "No open positions.", "positions": []}
        epics = [p.get("market", {}).get("epic") or p.get("epic") for p in positions]
        epics = [e for e in epics if e]
        snapshots: list[dict[str, Any]] = []
        last = datetime.now(timezone.utc)
        async for _tick in app.stream.portfolio(epics, duration=duration_s):
            now = datetime.now(timezone.utc)
            if (now - last).total_seconds() < update_interval_s:
                continue
            last = now
            snapshots.append(
                {
                    "positions": [
                        {
                            "deal_id": p.get("position", {}).get("dealId") or p.get("dealId"),
                            "epic": p.get("market", {}).get("epic") or p.get("epic"),
                        }
                        for p in positions
                    ],
                    "timestamp": now.isoformat(),
                }
            )
        return {
            "status": "completed",
            "duration_s": duration_s,
            "positions_monitored": len(positions),
            "snapshots_collected": len(snapshots),
            "snapshots": snapshots[-20:],
        }
    except Exception as e:  # noqa: BLE001
        return {"error": "Portfolio streaming failed", "message": str(e)}


# ============================================================
# Resources (read-only)
# ============================================================


@mcp.resource("cap://status")
async def cap_status_resource() -> dict[str, Any]:
    """Server + session status snapshot."""
    app = get_app()
    status = app.session.get_status()
    policy = app.risk_policy
    return {
        "server": {"name": "Capital.com MCP Server", "version": _version()},
        "session": status.model_dump(),
        "risk": {
            "trading_enabled": policy.allow_trading,
            "allowed_epics": list(policy.allowed_epics),
            "allowlist_mode": "ALL" if "ALL" in policy.allowed_epics else "SPECIFIC",
        },
    }


@mcp.resource("cap://risk-policy")
async def cap_risk_policy_resource() -> dict[str, Any]:
    """Active risk-management policy."""
    policy = get_app().risk_policy
    return {
        "trading_enabled": policy.allow_trading,
        "two_phase_execution": True,
        "description": "All trades require preview -> explicit execution",
        "allowlist": {
            "mode": "ALL" if "ALL" in policy.allowed_epics else "SPECIFIC",
            "epics": list(policy.allowed_epics),
        },
        "limits": {
            "max_position_size": policy.max_position_size,
            "max_working_order_size": policy.max_working_order_size,
            "max_open_positions": policy.max_open_positions,
            "max_orders_per_day": policy.max_orders_per_day,
        },
        "require_explicit_confirm": policy.require_explicit_confirm,
        "dry_run": policy.dry_run,
    }


@mcp.resource("cap://allowed-epics")
async def cap_allowed_epics_resource() -> dict[str, Any]:
    """Trading allowlist."""
    policy = get_app().risk_policy
    epics = list(policy.allowed_epics)
    has_wildcard = "ALL" in epics
    return {
        "mode": "WILDCARD" if has_wildcard else "SPECIFIC",
        "allowed_epics": epics,
        "count": len(epics),
        "trading_enabled": policy.allow_trading,
    }


@mcp.resource("cap://market-cache/{epic}")
async def cap_market_cache_resource(epic: str) -> dict[str, Any]:
    """Live market details for an EPIC (no real cache)."""
    app = get_app()
    await app.session.ensure_logged_in()
    data = await app.markets.get(epic)
    snapshot = data.get("snapshot", {})
    instrument = data.get("instrument", {})
    dealing = instrument.get("dealingRules", {})
    return {
        "epic": epic,
        "instrument_name": instrument.get("name"),
        "instrument_type": instrument.get("type"),
        "snapshot": {
            "market_status": snapshot.get("marketStatus"),
            "bid": snapshot.get("bid"),
            "offer": snapshot.get("offer"),
            "update_time": snapshot.get("updateTime"),
        },
        "dealing": {
            "min_size": dealing.get("minDealSize", {}).get("value"),
            "max_size": dealing.get("maxDealSize", {}).get("value"),
            "min_step": dealing.get("minStepDistance", {}).get("value"),
        },
    }


# ============================================================
# Prompts (workflow guidance; return plain strings for FastMCP 3.x)
# ============================================================


@mcp.prompt()
async def market_scan(
    watchlist_id: str = "",
    timeframe: str = "HOUR",
    lookback_periods: int = 24,
) -> str:
    """
    Market scan workflow - Analyze markets in a watchlist.

    This prompt guides you through scanning markets for trading opportunities.
    It fetches a watchlist, retrieves price data for each market, and prompts
    you to analyze the data for patterns and opportunities.

    Args:
        watchlist_id: ID of watchlist to scan (leave empty to list all watchlists first)
        timeframe: Price resolution (MINUTE, MINUTE_5, HOUR, DAY) - default: HOUR
        lookback_periods: Number of candles to fetch (1-1000) - default: 24

    Workflow:
    1. If watchlist_id is empty, first call cap_watchlists_list to choose one
    2. Call cap_watchlists_get to get markets in the watchlist
    3. For each market, call cap_market_prices to get historical data
    4. Analyze the price data for trading opportunities
    5. Optionally check cap_market_sentiment for client positioning

    Example usage:
    - "Scan my watchlist for trading setups"
    - "Analyze markets in watchlist abc123 over the last day"
    """
    if not watchlist_id:
        return (
            "# Market Scan Workflow\n\n"
            "Let's scan your watchlist for trading opportunities.\n\n"
            "**Step 1: Select Watchlist**\n"
            "First, let's get your watchlists. Call the `cap_watchlists_list` tool "
            "to see all available watchlists, then provide the watchlist ID you want to scan.\n\n"
            "**Parameters for next steps:**\n"
            f"- Timeframe: {timeframe}\n"
            f"- Lookback periods: {lookback_periods}\n\n"
            "After you have a watchlist ID, use this prompt again with the watchlist_id parameter."
            "\n\n---\n"
            "_Capital.com MCP — demo account recommended; this is not financial advice._"
        )

    return (
        "# Market Scan Workflow\n\n"
        f"Scanning watchlist: **{watchlist_id}**\n"
        f"Timeframe: **{timeframe}** | Lookback: **{lookback_periods} periods**\n\n"
        "**Step 2: Get Watchlist Markets**\n"
        f"Call `cap_watchlists_get` with watchlist_id='{watchlist_id}' "
        "to get the list of markets.\n\n"
        "**Step 3: Fetch Price Data**\n"
        "For each market (EPIC) in the watchlist:\n"
        f"- Call `cap_market_prices` with resolution='{timeframe}' and max={lookback_periods}\n"
        "- Collect OHLC data for analysis\n\n"
        "**Step 4: Technical Analysis**\n"
        "Analyze the price data for each market:\n"
        "- Identify trends (uptrend, downtrend, ranging)\n"
        "- Check for support/resistance levels\n"
        "- Look for chart patterns (breakouts, reversals)\n"
        "- Calculate key metrics (volatility, momentum)\n\n"
        "**Step 5: Sentiment Check (Optional)**\n"
        "For interesting markets, call `cap_market_sentiment` to see "
        "how other clients are positioned (long vs short %).\n\n"
        "**Output Format:**\n"
        "Provide a summary table with:\n"
        "- Market name & EPIC\n"
        "- Current price & trend direction\n"
        "- Key levels (support/resistance)\n"
        "- Trading opportunity rating (Low/Medium/High)\n"
        "- Brief rationale\n\n"
        "Focus on actionable insights and clear opportunity identification."
        "\n\n---\n"
        "_Capital.com MCP — demo account recommended; this is not financial advice._"
    )


@mcp.prompt()
async def trade_proposal(
    epic: str,
    direction: str = "BUY",
    thesis: str = "",
    risk_percent: float = 1.0,
) -> str:
    """
    Trade proposal workflow - Design a trade with proper risk management.

    This prompt guides you through creating a trade proposal with entry,
    stop loss, and take profit levels. It uses preview to validate the trade
    WITHOUT executing it.

    Args:
        epic: Market EPIC to trade (e.g., SILVER, GOLD, BTCUSD)
        direction: Trade direction (BUY or SELL) - default: BUY
        thesis: Your trading thesis/reasoning
        risk_percent: Risk as % of account balance (default: 1.0%)

    Workflow:
    1. Call cap_market_get to fetch market details and dealing rules
    2. Calculate position size based on risk_percent and stop loss distance
    3. Call cap_trade_preview_position to validate the trade
    4. Return the preview_id for potential execution (DO NOT execute yet)

    Example usage:
    - "Propose a trade for SILVER"
    - "Create a trade proposal for buying GOLD with 2% risk"
    """
    direction_upper = direction.upper()
    if direction_upper not in ["BUY", "SELL"]:
        return (
            f"# Trade Proposal Error\n\n"
            f"Invalid direction: '{direction}'. Must be 'BUY' or 'SELL'."
        )

    thesis_section = f"\n**Trading Thesis:**\n{thesis}\n" if thesis else ""

    return (
        "# Trade Proposal Workflow\n\n"
        "\n> **Safety:** trades are **two-phase** — `preview` validates, then "
        "`execute` with `confirm=true` places the order. Never skip the preview.\n"
        f"**Market:** {epic}\n"
        f"**Direction:** {direction_upper}\n"
        f"**Risk:** {risk_percent}% of account balance\n"
        f"{thesis_section}\n"
        "---\n\n"
        "**Step 1: Fetch Market Details**\n"
        f"Call `cap_market_get` with epic='{epic}' to get:\n"
        "- Current bid/offer prices\n"
        "- Dealing rules (min/max size, increments)\n"
        "- Market status (open/closed)\n"
        "- Margin requirements\n\n"
        "**Step 2: Calculate Position Size**\n"
        "Based on your risk management:\n"
        f"1. Account balance × {risk_percent}% = risk amount in currency\n"
        "2. Determine stop loss distance (e.g., support/resistance level)\n"
        "3. Position size = risk amount ÷ stop loss distance\n"
        "4. Round size to market's minSizeIncrement\n"
        "5. Ensure size is between minDealSize and maxDealSize\n\n"
        "**Step 3: Define Stop Loss & Take Profit**\n"
        "- **Stop Loss:** Technical level or fixed distance\n"
        "  - For BUY: below current price (e.g., support level)\n"
        "  - For SELL: above current price (e.g., resistance level)\n"
        "- **Take Profit:** Risk/reward ratio (e.g., 2:1 or 3:1)\n"
        "  - Target = Entry ± (Stop distance × reward ratio)\n\n"
        "**Step 4: Preview the Trade**\n"
        f"Call `cap_trade_preview_position` with:\n"
        f"- epic: '{epic}'\n"
        f"- direction: '{direction_upper}'\n"
        "- size: calculated size\n"
        "- stop_level: your stop loss price\n"
        "- profit_level: your take profit price\n\n"
        "**Step 5: Review Preview Results**\n"
        "The preview will return:\n"
        "- ✅ All risk checks (must pass)\n"
        "- Estimated entry price\n"
        "- Margin requirement\n"
        "- Potential profit/loss at targets\n"
        "- **preview_id** (save this for execution)\n\n"
        "**Important Safety Notes:**\n"
        "- This workflow does NOT execute the trade\n"
        "- The preview_id is valid for 2 minutes\n"
        "- Review all details before considering execution\n"
        "- Use the 'execute_trade' prompt with the preview_id to execute\n\n"
        "**Output Format:**\n"
        "Present the trade proposal as:\n"
        "```\n"
        f"Market: {epic}\n"
        f"Direction: {direction_upper}\n"
        "Entry: [estimated price]\n"
        "Stop Loss: [price] ([distance] points, [risk %]%)\n"
        "Take Profit: [price] ([distance] points, [reward:risk ratio])\n"
        "Position Size: [size] units\n"
        "Margin Required: [amount]\n"
        "Risk: [currency amount]\n"
        "Potential Reward: [currency amount]\n"
        "Preview ID: [uuid]\n"
        "Risk Checks: [✅/❌ status]\n"
        "```"
        "\n\n---\n"
        "_Capital.com MCP — demo account recommended; this is not financial advice._"
    )


@mcp.prompt()
async def execute_trade(preview_id: str = "") -> str:
    """
    Execute trade workflow - Execute a previewed trade safely.

    This prompt guides you through executing a trade that was previously
    previewed. It includes confirmation polling and proper error handling.

    Args:
        preview_id: Preview ID from trade_proposal workflow (required)

    Workflow:
    1. Verify preview_id is provided
    2. Call cap_trade_execute_position with the preview_id and confirm=true
    3. Poll for confirmation using cap_trade_confirm_wait or cap_trade_confirm_get
    4. Report final status (ACCEPTED or REJECTED with reason)

    Safety notes:
    - Requires CAP_ALLOW_TRADING=true
    - Requires epic in CAP_ALLOWED_EPICS allowlist
    - Preview must not be expired (2-minute TTL)
    - This WILL place a real trade with the broker

    Example usage:
    - "Execute the previewed trade"
    - "Place the trade with preview ID abc-123-def"
    """
    if not preview_id:
        return (
            "# Execute Trade Workflow - Missing Preview ID\n\n"
            "⚠️ **Error:** preview_id is required.\n\n"
            "**How to get a preview_id:**\n"
            "1. Use the `trade_proposal` prompt to create a trade proposal\n"
            "2. That workflow will call `cap_trade_preview_position`\n"
            "3. The preview returns a preview_id (valid for 2 minutes)\n"
            "4. Use that preview_id with this prompt to execute\n\n"
            "**Example workflow:**\n"
            "```\n"
            "User: Propose a trade for SILVER\n"
            "Assistant: [uses trade_proposal prompt, gets preview_id: 'abc-123']\n"
            "User: Execute that trade\n"
            "Assistant: [uses execute_trade prompt with preview_id='abc-123']\n"
            "```"
            "\n\n---\n"
            "_Capital.com MCP — demo account recommended; this is not financial advice._"
        )

    return (
        "# Execute Trade Workflow\n\n"
        "\n> **Safety:** trades are **two-phase** — `preview` validates, then "
        "`execute` with `confirm=true` places the order. Never skip the preview.\n"
        f"**Preview ID:** {preview_id}\n\n"
        "⚠️ **DANGER: This workflow will place a REAL trade with the broker.**\n\n"
        "**Pre-Execution Checklist:**\n"
        "- [ ] Trading is enabled (CAP_ALLOW_TRADING=true)\n"
        "- [ ] Market EPIC is in allowlist (CAP_ALLOWED_EPICS)\n"
        "- [ ] Preview is not expired (generated < 2 minutes ago)\n"
        "- [ ] Trade details were reviewed and approved by user\n"
        "- [ ] Risk management is appropriate\n\n"
        "**Step 1: Execute Position**\n"
        f"Call `cap_trade_execute_position` with:\n"
        f"- preview_id: '{preview_id}'\n"
        "- confirm: true\n"
        "- wait_for_confirm: true (recommended)\n\n"
        "This will:\n"
        "1. Validate the preview_id is still valid\n"
        "2. Re-check all risk controls\n"
        "3. Submit the order to Capital.com broker\n"
        "4. Return a deal_reference\n"
        "5. Automatically poll for confirmation (if wait_for_confirm=true)\n\n"
        "**Step 2: Confirmation Status**\n"
        "The broker will respond with:\n"
        "- **ACCEPTED:** Trade executed successfully\n"
        "  - deal_id: Position identifier\n"
        "  - level: Actual fill price\n"
        "  - size: Actual position size\n"
        "  - direction: BUY or SELL\n"
        "- **REJECTED:** Trade rejected by broker\n"
        "  - reason: Why it was rejected (e.g., insufficient margin, market closed)\n\n"
        "**Step 3: Post-Execution Actions**\n"
        "If ACCEPTED:\n"
        "- Call `cap_trade_positions_get` with the deal_id to see position details\n"
        "- Verify stop loss and take profit were set correctly\n"
        "- Record the trade in your trading journal\n\n"
        "If REJECTED:\n"
        "- Review the rejection reason\n"
        "- Check account balance and margin\n"
        "- Verify market is open\n"
        "- Create a new preview if you want to try again\n\n"
        "**Error Handling:**\n"
        "Possible errors:\n"
        "- `TRADING_DISABLED`: CAP_ALLOW_TRADING is false\n"
        "- `EPIC_NOT_ALLOWED`: Market not in allowlist\n"
        "- `PREVIEW_EXPIRED`: Preview is older than 2 minutes\n"
        "- `PREVIEW_NOT_FOUND`: Invalid preview_id\n"
        "- `UPSTREAM_ERROR`: Broker API error\n\n"
        "**Output Format:**\n"
        "Report execution result clearly:\n"
        "```\n"
        "✅ TRADE EXECUTED SUCCESSFULLY\n"
        "Deal ID: [deal_id]\n"
        "Market: [epic]\n"
        "Direction: [BUY/SELL]\n"
        "Size: [size] units\n"
        "Entry Price: [level]\n"
        "Stop Loss: [stop_level]\n"
        "Take Profit: [profit_level]\n"
        "Status: ACCEPTED\n"
        "```\n\n"
        "OR:\n\n"
        "```\n"
        "❌ TRADE REJECTED\n"
        "Reason: [broker rejection reason]\n"
        "Status: REJECTED\n"
        "```"
        "\n\n---\n"
        "_Capital.com MCP — demo account recommended; this is not financial advice._"
    )


@mcp.prompt()
async def position_review() -> str:
    """
    Position review workflow - Analyze current positions and orders.

    This prompt guides you through reviewing open positions and working orders,
    identifying exposures, and suggesting adjustments. It does NOT execute
    any trades - it's purely analytical.

    No arguments required - reviews all current positions and orders.

    Workflow:
    1. Call cap_trade_positions_list to get all open positions
    2. Call cap_trade_orders_list to get all working orders
    3. For each position, calculate P&L, risk, and exposure
    4. Identify correlations and concentration risks
    5. Suggest potential adjustments (WITHOUT executing them)

    Example usage:
    - "Review my current positions"
    - "Analyze my portfolio exposure"
    - "Show me my open trades and their status"
    """
    return (
        "# Position Review Workflow\n\n"
        "\n> **Safety:** this is read-only. Any follow-up trade must go through "
        "the two-phase `preview` → `execute` flow.\n"
        "Let's analyze your current trading positions and orders.\n\n"
        "**Step 1: Fetch Open Positions**\n"
        "Call `cap_trade_positions_list` to get all open positions.\n\n"
        "For each position, extract:\n"
        "- deal_id & market (EPIC)\n"
        "- Direction (BUY/SELL)\n"
        "- Size & entry level (price)\n"
        "- Current market price\n"
        "- Unrealized P&L\n"
        "- Stop loss & take profit levels\n\n"
        "**Step 2: Fetch Working Orders**\n"
        "Call `cap_trade_orders_list` to get all pending orders.\n\n"
        "For each order, extract:\n"
        "- order_id & market (EPIC)\n"
        "- Direction (BUY/SELL)\n"
        "- Size & trigger level\n"
        "- Order type (LIMIT/STOP)\n"
        "- Good till date\n\n"
        "**Step 3: Calculate Key Metrics**\n\n"
        "*Per Position:*\n"
        "- P&L (currency and %)\n"
        "- Risk (distance to stop loss in currency)\n"
        "- Reward (distance to take profit in currency)\n"
        "- Days held\n"
        "- Status (winning/losing, at risk/safe)\n\n"
        "*Portfolio Level:*\n"
        "- Total unrealized P&L\n"
        "- Total capital at risk (sum of all stop loss distances)\n"
        "- Largest winning position\n"
        "- Largest losing position\n"
        "- Net directional exposure (net long/short across all positions)\n\n"
        "**Step 4: Risk Analysis**\n\n"
        "*Check for:*\n"
        "- **Concentration Risk:** Too much exposure to one market\n"
        "- **Correlation Risk:** Multiple positions in correlated markets\n"
        "  - (e.g., GOLD and SILVER often move together)\n"
        "- **Directional Bias:** Are you heavily long or short overall?\n"
        "- **Stop Loss Coverage:** Are all positions protected?\n"
        "- **Profit Target Coverage:** Do all positions have take profits?\n\n"
        "**Step 5: Position Health Check**\n\n"
        "For each position, assess:\n"
        "- ✅ **Healthy:** In profit, stop loss at breakeven or better\n"
        "- ⚠️ **At Risk:** Near stop loss, or stop too wide\n"
        "- 🔍 **Needs Attention:** No stop loss, or profit target hit\n"
        "- ❌ **Losing:** Underwater, stop loss not adjusted\n\n"
        "**Step 6: Adjustment Suggestions**\n\n"
        "*Potential actions (DO NOT execute):*\n"
        "- Move stop loss to breakeven on winning positions\n"
        "- Tighten stop loss if trade is going your way\n"
        "- Close losing positions if thesis invalidated\n"
        "- Take partial profits on large winners\n"
        "- Cancel stale working orders\n"
        "- Reduce exposure in correlated markets\n\n"
        "**Step 7: Market Context (Optional)**\n\n"
        "For key positions:\n"
        "- Call `cap_market_sentiment` to see client positioning\n"
        "- Call `cap_market_prices` to check recent price action\n"
        "- Consider if stop loss is at a logical level\n\n"
        "**Output Format:**\n\n"
        "```\n"
        "# Portfolio Summary\n"
        "Total Open Positions: [count]\n"
        "Total Working Orders: [count]\n"
        "Total Unrealized P&L: [amount] ([%])\n"
        "Capital at Risk: [amount]\n"
        "Net Exposure: [net long/short description]\n\n"
        "# Position Details\n\n"
        "## Position 1: [EPIC] [BUY/SELL] [size]\n"
        "Entry: [price] | Current: [price] | P&L: [amount] ([%])\n"
        "Stop: [price] (Risk: [amount]) | Target: [price] (Reward: [amount])\n"
        "Status: [✅/⚠️/🔍/❌] [description]\n"
        "Suggestion: [specific action recommendation]\n\n"
        "[... repeat for each position ...]\n\n"
        "# Working Orders\n\n"
        "## Order 1: [EPIC] [type] [direction] @ [trigger_price]\n"
        "Size: [size] | Expires: [date]\n"
        "Status: [active/stale]\n"
        "Suggestion: [keep/cancel/adjust]\n\n"
        "[... repeat for each order ...]\n\n"
        "# Risk Assessment\n"
        "Concentration: [assessment]\n"
        "Correlation: [assessment]\n"
        "Directional Bias: [assessment]\n"
        "Stop Loss Coverage: [% of positions protected]\n\n"
        "# Recommended Actions\n"
        "1. [Priority action 1]\n"
        "2. [Priority action 2]\n"
        "3. [Priority action 3]\n"
        "```\n\n"
        "**Important Notes:**\n"
        "- This workflow is READ-ONLY and analytical\n"
        "- No trades will be executed automatically\n"
        "- All suggestions require user approval before execution\n"
        "- Use appropriate tools (cap_trade_positions_close, etc.) to act on suggestions"
        "\n\n---\n"
        "_Capital.com MCP — demo account recommended; this is not financial advice._"
    )


@mcp.prompt()
async def live_price_monitor(
    epics: list[str] | None = None,
    duration_minutes: float = 5.0,
    threshold_percent: float = 1.0,
) -> str:
    """
    Live price monitor - Real-time price tracking with movement alerts (WebSocket streaming).

    Monitor live market prices with instant alerts when prices move beyond threshold.
    Uses WebSocket streaming for real-time updates with sub-second latency.

    Args:
        epics: List of market EPICs to monitor (leave empty to search/select, max 40)
        duration_minutes: How long to monitor (default: 5 minutes, max: 10 minutes)
        threshold_percent: Alert when price moves > this % (default: 1.0%)

    Workflow:
    1. Select markets to monitor (or provide EPICs directly)
    2. Fetch initial prices to establish baseline
    3. [STREAM] Subscribe to real-time WebSocket price updates
    4. Display live price board with continuous updates
    5. Alert when any market moves > threshold_percent
    6. Auto-stop after duration_minutes

    Note: Requires CAP_WS_ENABLED=true in configuration.
    Capital.com WebSocket sessions last 10 minutes maximum.

    Example usage:
    - "Monitor GOLD and SILVER prices for 2 minutes"
    - "Watch BTC for next 5 minutes, alert on 2% moves"
    - "Track my watchlist in real-time"
    """
    if epics is None:
        epics = []
    if not epics:
        return (
            "# 📊 Live Price Monitor Workflow\n\n"
            "**Real-time price tracking with WebSocket streaming**\n\n"
            "---\n\n"
            "**Step 1: Select Markets**\n"
            "First, choose which markets you want to monitor:\n"
            "- Call `cap_market_search` to find markets by name/category\n"
            "- Or call `cap_watchlists_list` to see your watchlists\n"
            "- Or call `cap_watchlists_get` to get markets from a specific watchlist\n"
            "- Maximum: 40 markets simultaneously\n\n"
            "**Parameters for next steps:**\n"
            f"- Duration: {duration_minutes} minutes\n"
            f"- Alert threshold: {threshold_percent}% price movement\n\n"
            "After you have your EPICs list, use this prompt again with the epics parameter.\n"
            'Example: `live_price_monitor(epics=["GOLD", "SILVER"], duration_minutes=2.0)`'
            "\n\n---\n"
            "_Capital.com MCP — demo account recommended; this is not financial advice._"
        )

    return (
        "# 📊 Live Price Monitor\n\n"
        f"**Monitoring:** {', '.join(epics[:5])}"
        + (f" (+{len(epics) - 5} more)" if len(epics) > 5 else "")
        + "\n"
        f"**Duration:** {duration_minutes} minutes | "
        f"**Alert threshold:** {threshold_percent}%\n\n"
        "---\n\n"
        "**Step 2: Fetch Initial Prices**\n"
        "Get baseline prices for comparison:\n"
        "- For each EPIC, call `cap_market_prices` with resolution=MINUTE and max=1\n"
        "- Record current bid/offer/mid prices\n"
        "- This establishes the starting point for threshold alerts\n\n"
        "**Step 3: [STREAM] Start Real-Time Monitoring**\n"
        f"Call `cap_stream_prices` to start WebSocket streaming:\n"
        f"- epics: {epics}\n"
        f"- duration_s: {duration_minutes * 60}\n"
        "- update_interval_s: 1.0 (updates every second)\n\n"
        "⚡ **While streaming:**\n"
        "- Display live price board (update continuously as ticks arrive)\n"
        "- Calculate % change from baseline for each market\n"
        f"- **Alert** when any market moves > {threshold_percent}%\n"
        "- Show timestamp for each update\n\n"
        "**Step 4: Present Live Dashboard**\n"
        "Format the output as a continuously updating table:\n"
        "```\n"
        "📊 LIVE PRICES (auto-updating)\n"
        "───────────────────────────────────────\n"
        "EPIC     | Bid      | Offer    | Change\n"
        "───────────────────────────────────────\n"
        "GOLD     | 2,048.50 | 2,049.00 | +0.5% ⚡\n"
        "SILVER   | 27.80    | 27.82    | -0.2%\n"
        "───────────────────────────────────────\n"
        "Last update: HH:MM:SS\n"
        "```\n\n"
        f"⚠️ **Alert format** (when change > {threshold_percent}%):\n"
        "```\n"
        "⚡ PRICE ALERT: GOLD\n"
        f"   Moved {threshold_percent}%+ from baseline\n"
        "   Current: $2,048.50 (was $2,038.00)\n"
        "   Change: +$10.50 (+0.52%)\n"
        "   Time: 14:32:18\n"
        "```\n\n"
        "**Important Notes:**\n"
        "- ✅ WebSocket provides sub-second updates\n"
        f"- ⏱️ Stream auto-stops after {duration_minutes} minutes\n"
        "- 🔄 Auto-reconnects if connection drops (up to 3 attempts)\n"
        "- 🚫 Requires CAP_WS_ENABLED=true in config\n"
        "- 📊 Capital.com sends updates when prices change (not on fixed interval)\n"
        "\n\n---\n"
        "_Capital.com MCP — demo account recommended; this is not financial advice._"
    )


@mcp.prompt()
async def real_time_alerts(
    alert_config: dict[str, float] | None = None,
    duration_minutes: float = 5.0,
    auto_stop: bool = True,
) -> str:
    """
    Real-time alerts - Conditional alerts for trading opportunities (WebSocket streaming).

    Set price level alerts and get instant notifications when markets hit your targets.
    Uses WebSocket for real-time monitoring with immediate alert triggers.

    Args:
        alert_config: Alert levels per EPIC (e.g., {"GOLD": 2050.0, "SILVER": 28.5})
        duration_minutes: Maximum monitoring duration (default: 5 minutes)
        auto_stop: Stop monitoring after first alert? (default: true)

    Workflow:
    1. Configure alert conditions (price levels for each market)
    2. [STREAM] Subscribe to WebSocket price updates
    3. Monitor continuously for alert triggers
    4. Emit instant alert when condition met
    5. Optionally continue monitoring or stop after first alert

    Note: Requires CAP_WS_ENABLED=true in configuration.

    Example usage:
    - "Alert me when GOLD reaches 2050"
    - "Notify when SILVER drops below 28"
    - "Watch breakout levels for BTC and ETH"
    """
    if alert_config is None:
        alert_config = {}
    if not alert_config:
        return (
            "# ⚡ Real-Time Alerts Setup\n\n"
            "**Instant notifications when markets hit your target levels**\n\n"
            "---\n\n"
            "**Step 1: Identify Target Markets & Levels**\n"
            "Determine which markets you want to monitor and at what price levels:\n\n"
            "1. **Find markets:**\n"
            "   - Call `cap_market_search` to search by name\n"
            "   - Call `cap_market_get` to check current prices\n\n"
            "2. **Define alert levels:**\n"
            "   - Support/resistance levels (technical analysis)\n"
            "   - Psychological levels (round numbers)\n"
            "   - Breakout points\n"
            "   - Previous highs/lows\n\n"
            "**Step 2: Configure Alert Parameters**\n"
            "Decide:\n"
            f"- **Duration:** How long to monitor (default: {duration_minutes} min, max: 10 min)\n"
            f"- **Auto-stop:** Stop after first alert? (default: {auto_stop})\n\n"
            "**Step 3: Format Alert Configuration**\n"
            "Create alert_config dictionary:\n"
            "```python\n"
            "{\n"
            '  "GOLD": 2050.0,    # Alert when GOLD hits 2050\n'
            '  "SILVER": 28.5,    # Alert when SILVER hits 28.5\n'
            '  "BTCUSD": 45000.0  # Alert when BTC hits 45000\n'
            "}\n"
            "```\n\n"
            "Then call this prompt again with alert_config parameter.\n"
            'Example: `real_time_alerts(alert_config={"GOLD": 2050.0}, duration_minutes=5.0)`'
            "\n\n---\n"
            "_Capital.com MCP — demo account recommended; this is not financial advice._"
        )

    return (
        "# ⚡ Real-Time Alert Monitoring\n\n"
        f"**Configured alerts:** {len(alert_config)} markets\n"
        f"**Duration:** {duration_minutes} minutes | "
        f"**Auto-stop after alert:** {'Yes' if auto_stop else 'No'}\n\n"
        "---\n\n"
        "**Alert Configuration:**\n"
        + "\n".join(
            [f"- {epic}: {level:,.2f}" for epic, level in list(alert_config.items())[:10]]
        )
        + ("\n- ..." if len(alert_config) > 10 else "")
        + "\n\n"
        "**Step 2: Fetch Current Prices**\n"
        "Get current market prices to determine direction:\n"
        "- For each EPIC in alert_config, call `cap_market_get`\n"
        "- Check if current price is above or below alert level\n"
        "- Determine alert direction (ABOVE if currently below, BELOW if currently above)\n\n"
        "**Step 3: [STREAM] Start Alert Monitoring**\n"
        "Call `cap_stream_alerts` with formatted configuration:\n"
        "```python\n"
        "alerts = {\n"
        + "\n".join(
            [
                f'  "{epic}": {{"level": {level}, "direction": "ABOVE"}}  # Adjust direction based on current price'
                for epic, level in list(alert_config.items())[:3]
            ]
        )
        + "\n}\n"
        "```\n\n"
        f"- duration_s: {duration_minutes * 60}\n"
        f"- auto_close: {auto_stop}\n\n"
        "⚡ **While monitoring:**\n"
        "- WebSocket streams live price updates\n"
        "- Each tick is checked against alert conditions\n"
        "- Instant notification when level crossed\n"
        + (
            "- Monitoring stops after first alert\n"
            if auto_stop
            else "- Continues monitoring all markets\n"
        )
        + "\n"
        "**Step 4: Handle Alert Triggers**\n"
        "When an alert fires, display:\n"
        "```\n"
        "🚨 ALERT TRIGGERED! 🚨\n"
        "───────────────────────────────────────\n"
        "Market: GOLD\n"
        "Condition: Price ABOVE 2050.00\n"
        "Trigger Price: 2050.00\n"
        "Current Price: 2050.25\n"
        "Timestamp: 2026-01-16T14:32:18Z\n"
        "───────────────────────────────────────\n"
        "```\n\n"
        "**Optional Next Actions:**\n"
        "After alert triggers:\n"
        "1. ✅ Call `cap_market_get` to get full market details\n"
        "2. ✅ Use `trade_proposal` prompt to design trade entry\n"
        "3. ✅ Check `cap_market_sentiment` for positioning data\n"
        "4. ✅ Review technical levels with `cap_market_prices`\n\n"
        "**Important Notes:**\n"
        "- ⚡ Alerts trigger within milliseconds of level breach\n"
        "- 🔄 Auto-reconnects on WebSocket disconnection\n"
        "- 📊 Checks mid-price: (bid + offer) / 2\n"
        "- 🚫 Requires CAP_WS_ENABLED=true\n"
        f"- ⏱️ Max duration: {duration_minutes} minutes (Capital.com limit: 10 min)\n"
        "\n\n---\n"
        "_Capital.com MCP — demo account recommended; this is not financial advice._"
    )


@mcp.prompt()
async def live_portfolio_monitor(
    duration_minutes: float = 5.0,
    alert_pnl_threshold: float = 100.0,
) -> str:
    """
    Live portfolio monitor - Real-time P&L tracking for open positions (WebSocket streaming).

    Watch your portfolio P&L update in real-time as market prices move.
    Get instant alerts when total P&L crosses thresholds.

    Args:
        duration_minutes: Monitoring duration (default: 5 minutes, max: 10 minutes)
        alert_pnl_threshold: Alert when total P&L exceeds this amount (default: $100)

    Workflow:
    1. Fetch current open positions
    2. [STREAM] Subscribe to price updates for position markets
    3. Calculate live P&L as prices change
    4. Display real-time portfolio dashboard
    5. Alert when P&L crosses threshold

    Note: Requires CAP_WS_ENABLED=true and active positions.

    Example usage:
    - "Monitor my portfolio P&L for 5 minutes"
    - "Watch positions in real-time, alert at $500 P&L"
    - "Track live portfolio performance"
    """
    return (
        "# 💼 Live Portfolio Monitor\n\n"
        f"**Duration:** {duration_minutes} minutes | "
        f"**P&L alert threshold:** ${alert_pnl_threshold:,.2f}\n\n"
        "---\n\n"
        "**Step 1: Fetch Open Positions**\n"
        "Get your current portfolio:\n"
        "- Call `cap_trade_positions_list` to get all open positions\n"
        "- Extract: deal IDs, EPICs, directions, sizes, current P&L\n"
        "- If no positions: Cannot monitor empty portfolio\n\n"
        "**Step 2: Extract Position EPICs**\n"
        "Identify which markets to monitor:\n"
        "- Get unique EPICs from all positions\n"
        "- Note: Max 40 markets (Capital.com WebSocket limit)\n"
        "- If > 40 positions, prioritize largest positions\n\n"
        "**Step 3: [STREAM] Monitor Portfolio in Real-Time**\n"
        f"Call `cap_stream_portfolio`:\n"
        f"- duration_s: {duration_minutes * 60}\n"
        "- update_interval_s: 5.0 (updates every 5 seconds)\n\n"
        "📊 **While streaming:**\n"
        "- WebSocket streams price updates for all position markets\n"
        "- Recalculates P&L every 5 seconds\n"
        "- Displays live portfolio dashboard\n"
        f"- **Alerts** when total P&L crosses ${alert_pnl_threshold:,.2f}\n\n"
        "**Step 4: Display Live Dashboard**\n"
        "Format as continuously updating portfolio summary:\n"
        "```\n"
        "💼 LIVE PORTFOLIO DASHBOARD\n"
        "═══════════════════════════════════════════════════════\n"
        "Position     | Direction | Size  | P&L       | Status\n"
        "───────────────────────────────────────────────────────\n"
        "GOLD         | BUY       | 0.5   | +$125.50  | ✅\n"
        "SILVER       | SELL      | 2.0   | -$18.20   | 📊\n"
        "BTCUSD       | BUY       | 0.1   | +$230.00  | ⚡\n"
        "───────────────────────────────────────────────────────\n"
        "TOTAL P&L:                         +$337.30  | 🎯\n"
        "═══════════════════════════════════════════════════════\n"
        "Last update: 14:32:18 | Updates every 5s\n"
        "```\n\n"
        "**Status Indicators:**\n"
        "- ✅ Winning (P&L > 0)\n"
        "- 📊 Flat (P&L ≈ 0)\n"
        "- ⚠️ Losing but within risk tolerance\n"
        "- 🔴 Significant loss\n\n"
        f"**Alert Format** (when total P&L crosses ${alert_pnl_threshold:,.2f}):\n"
        "```\n"
        "🎯 P&L THRESHOLD ALERT!\n"
        f"   Total P&L crossed ${alert_pnl_threshold:,.2f}\n"
        "   Current P&L: +$337.30\n"
        "   Time: 14:32:18\n"
        "   Action: Review positions, consider taking profits\n"
        "```\n\n"
        "**Optional Follow-Up Actions:**\n"
        "Based on live P&L:\n"
        "1. 💰 **Taking Profits:** Use `cap_trade_positions_close` to close winning positions\n"
        "2. 🛑 **Cutting Losses:** Close losing positions before they worsen\n"
        "3. 📊 **Position Details:** Call `cap_trade_positions_get` for specific position\n"
        "4. 🎯 **Adjust Stops:** Update stop losses on running positions\n\n"
        "**Important Notes:**\n"
        "- ⚡ P&L updates as prices change (real-time)\n"
        "- 🔄 Updates every 5 seconds (configurable)\n"
        "- 📊 Includes all open positions automatically\n"
        "- 🚫 Requires CAP_WS_ENABLED=true and active positions\n"
        f"- ⏱️ Auto-stops after {duration_minutes} minutes\n"
        "- 💡 Simplified P&L calculation (demo purposes - real calc needs more data)\n"
        "\n\n---\n"
        "_Capital.com MCP — demo account recommended; this is not financial advice._"
    )


# ============================================================
# ChatGPT Deep Research adapters (search / fetch)
# ============================================================


@mcp.tool()
async def search(query: str) -> dict[str, Any]:
    """ChatGPT Deep Research: search Capital.com markets. Returns {results:[{id,title,url}]}."""
    app = get_app()
    await app.session.ensure_logged_in()
    data = await app.markets.search(query, limit=20)
    results = [
        {
            "id": m.get("epic"),
            "title": m.get("instrumentName") or m.get("epic"),
            "url": f"capitalcom://market/{m.get('epic')}",
        }
        for m in data.get("markets", [])
        if m.get("epic")
    ]
    return {"results": results}


@mcp.tool()
async def fetch(id: str) -> dict[str, Any]:
    """ChatGPT Deep Research: fetch a market's details. Returns {id,title,text,url,metadata}."""
    app = get_app()
    await app.session.ensure_logged_in()
    data = await app.markets.get(id)
    instrument = data.get("instrument", {})
    title = instrument.get("name") or id
    return {
        "id": id,
        "title": title,
        "text": json.dumps(data),
        "url": f"capitalcom://market/{id}",
        "metadata": {"type": instrument.get("type")},
    }
