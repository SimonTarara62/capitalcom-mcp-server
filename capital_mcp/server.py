"""MCP Server for Capital.com Open API - FastMCP Implementation."""

import logging
from typing import Any

from fastmcp import FastMCP

from .capital_client import get_client
from .config import get_config
from .models import (
    AccountPreferencesSetRequest,
    ConfirmWaitRequest,
    DemoTopUpRequest,
    ExecutePositionRequest,
    ExecuteWorkingOrderRequest,
    MarketGetRequest,
    MarketSearchRequest,
    PreviewPositionRequest,
    PreviewWorkingOrderRequest,
    PricesRequest,
    WatchlistAddMarketRequest,
    WatchlistCreateRequest,
)
from .risk import get_risk_engine
from .session import get_session_manager
from .utils import poll_until

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Capital.com MCP Server")


# ============================================================
# Session Tools
# ============================================================


@mcp.tool()
async def cap_session_status() -> dict[str, Any]:
    """
    Get current session status.

    Returns session info including login state, account ID, and token expiry estimate.
    No authentication required.
    """
    session = get_session_manager()
    status = session.get_status()
    return status.model_dump()


@mcp.tool()
async def cap_session_login(force: bool = False, account_id: str | None = None) -> dict[str, Any]:
    """
    Create a new session or verify existing session.

    Args:
        force: Force new login even if session is valid (default: false)
        account_id: Account ID to switch to after login (optional)

    Rate limit: 1 request/second (session limit).
    Creates CST and X-SECURITY-TOKEN for subsequent authenticated requests.
    """
    session = get_session_manager()
    data = await session.login(force=force, account_id=account_id)
    return data


@mcp.tool()
async def cap_session_ping() -> dict[str, Any]:
    """
    Keep session alive.

    Extends session timeout by 10 minutes from last activity.
    Call periodically if doing long operations.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()
    data = await session.ping()
    return data


@mcp.tool()
async def cap_session_logout() -> dict[str, str]:
    """
    End session and clear authentication tokens.

    Requires authentication.
    """
    session = get_session_manager()
    await session.logout()
    return {"message": "Logged out successfully"}


# ============================================================
# Market Data Tools
# ============================================================


@mcp.tool()
async def cap_market_search(
    search_term: str | None = None,
    epics: list[str] | None = None,
    limit: int = 50
) -> dict[str, Any]:
    """
    Search for markets by term or EPICs.

    Args:
        search_term: Search term (e.g., "Bitcoin", "BTC") (optional)
        epics: List of EPICs to filter (optional)
        limit: Max results (default: 50, max: 1000)

    Returns list of matching markets with details.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    params: dict[str, Any] = {}
    if search_term:
        params["searchTerm"] = search_term
    if epics:
        params["epics"] = ",".join(epics)

    response = await client.get("/markets", params=params)
    data = response.json()

    # Limit results
    if "markets" in data and len(data["markets"]) > limit:
        data["markets"] = data["markets"][:limit]

    return data


@mcp.tool()
async def cap_market_get(epic: str) -> dict[str, Any]:
    """
    Get detailed market information including dealing rules.

    Args:
        epic: Market EPIC (e.g., "SILVER", "BTCUSD")

    Returns market details, dealing rules (min/max size, increments), and current snapshot.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.get(f"/markets/{epic}")
    return response.json()


@mcp.tool()
async def cap_market_navigation_root() -> dict[str, Any]:
    """
    Get root market navigation tree.

    Returns hierarchical market categories (e.g., Currencies, Indices, Commodities).
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.get("/marketnavigation")
    return response.json()


@mcp.tool()
async def cap_market_navigation_node(node_id: str) -> dict[str, Any]:
    """
    Get market navigation node details.

    Args:
        node_id: Navigation node ID

    Returns child nodes and markets under this category.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.get(f"/marketnavigation/{node_id}")
    return response.json()


@mcp.tool()
async def cap_market_prices(
    epic: str,
    resolution: str = "MINUTE_15",
    max: int = 200,
    from_date: str | None = None,
    to_date: str | None = None
) -> dict[str, Any]:
    """
    Get historical price data (OHLC candles).

    Args:
        epic: Market EPIC
        resolution: Time resolution (MINUTE, MINUTE_5, MINUTE_15, MINUTE_30, HOUR, HOUR_4, DAY, WEEK)
        max: Max candles to return (default: 200, max: 1000)
        from_date: Start date ISO 8601 (optional)
        to_date: End date ISO 8601 (optional)

    Returns historical price data with OHLC values.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    params: dict[str, Any] = {
        "resolution": resolution,
        "max": max,
    }
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date

    response = await client.get(f"/prices/{epic}", params=params)
    return response.json()


@mcp.tool()
async def cap_market_sentiment(market_id: str) -> dict[str, Any]:
    """
    Get client sentiment for a market.

    Args:
        market_id: Market ID (usually same as EPIC)

    Returns percentage of long vs short positions from other traders.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.get(f"/clientsentiment/{market_id}")
    return response.json()


# ============================================================
# Account Tools
# ============================================================


@mcp.tool()
async def cap_account_list() -> dict[str, Any]:
    """
    List all trading accounts.

    Returns account details including balance, currency, and account type.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.get("/accounts")
    return response.json()


@mcp.tool()
async def cap_account_preferences_get() -> dict[str, Any]:
    """
    Get account preferences.

    Returns hedging mode setting and leverage configuration per asset class.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.get("/accounts/preferences")
    return response.json()


@mcp.tool()
async def cap_account_preferences_set(
    hedging_mode: bool | None = None,
    leverages: dict[str, int | None] | None = None,
    confirm: bool = False
) -> dict[str, Any]:
    """
    Set account preferences (TRADE-GATED).

    Args:
        hedging_mode: Enable hedging mode (optional)
        leverages: Leverage per asset class - SHARES, CURRENCIES, INDICES, CRYPTOCURRENCIES, COMMODITIES (optional)
        confirm: Explicit confirmation required (default: false)

    IMPORTANT: This is a trade-gated operation.
    - Requires CAP_ALLOW_TRADING=true
    - Requires confirm=true if CAP_REQUIRE_EXPLICIT_CONFIRM=true
    - Changes leverage and hedging mode affect risk exposure

    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    risk = get_risk_engine()
    risk.validate_execution_guards(confirm=confirm)

    # Build request body
    body: dict[str, Any] = {}
    if hedging_mode is not None:
        body["hedgingMode"] = hedging_mode
    if leverages is not None:
        body["leverages"] = leverages

    client = get_client()
    response = await client.put("/accounts/preferences", json=body)
    return response.json()


@mcp.tool()
async def cap_account_history_activity(
    from_date: str | None = None,
    to_date: str | None = None,
    last_period: int = 600
) -> dict[str, Any]:
    """
    Get account activity history.

    Args:
        from_date: Start date ISO 8601 (optional)
        to_date: End date ISO 8601 (optional)
        last_period: Last N seconds (default: 600, max: 86400 for 1 day)

    Returns recent account activity including deals, orders, and updates.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    params: dict[str, Any] = {"lastPeriod": last_period}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date

    client = get_client()
    response = await client.get("/history/activity", params=params)
    return response.json()


@mcp.tool()
async def cap_account_history_transactions(
    from_date: str | None = None,
    to_date: str | None = None,
    last_period: int = 600,
    type: str | None = None
) -> dict[str, Any]:
    """
    Get transaction history.

    Args:
        from_date: Start date ISO 8601 (optional)
        to_date: End date ISO 8601 (optional)
        last_period: Last N seconds (default: 600)
        type: Transaction type filter (optional)

    Returns transaction history including deposits, withdrawals, and P&L.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    params: dict[str, Any] = {"lastPeriod": last_period}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    if type:
        params["type"] = type

    client = get_client()
    response = await client.get("/history/transactions", params=params)
    return response.json()


@mcp.tool()
async def cap_account_demo_topup(amount: float, confirm: bool = False) -> dict[str, Any]:
    """
    Top up demo account balance (DEMO ONLY).

    Args:
        amount: Amount to add to balance
        confirm: Explicit confirmation required (default: false)

    IMPORTANT: Only works in DEMO environment (CAP_ENV=demo).
    Requires confirm=true if CAP_REQUIRE_EXPLICIT_CONFIRM=true.
    Requires authentication.
    """
    config = get_config()

    # Demo-only check
    if config.cap_env.value != "demo":
        raise ValueError("Demo top-up only available in demo environment (CAP_ENV=demo)")

    # Confirmation check
    if config.cap_require_explicit_confirm and not confirm:
        raise ValueError("Explicit confirmation required. Set confirm=true")

    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.post("/accounts/topUp", json={"amount": amount})
    return response.json()


# ============================================================
# Helper Functions
# ============================================================


async def _wait_for_confirmation(
    deal_reference: str,
    timeout_s: float = 15.0,
    poll_interval_ms: int = 500
) -> dict[str, Any]:
    """
    Helper function to wait for deal confirmation with polling.

    This is extracted so it can be called by both the tool and internal functions.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()

    async def check_confirm() -> dict[str, Any]:
        response = await client.get(f"/confirms/{deal_reference}")
        return response.json()

    def is_complete(data: dict[str, Any]) -> bool:
        status = data.get("status")
        return status in ("ACCEPTED", "REJECTED")

    result_data = await poll_until(
        check_confirm,
        is_complete,
        timeout_s=timeout_s,
        poll_interval_ms=poll_interval_ms,
    )

    if result_data is None:
        raise TimeoutError(f"Confirmation polling timed out after {timeout_s}s")

    return result_data


# ============================================================
# Trading Tools - Read-only
# ============================================================


@mcp.tool()
async def cap_trade_positions_list() -> dict[str, Any]:
    """
    List all open positions.

    Returns current positions with P&L, direction, size, and attached orders.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.get("/positions")
    return response.json()


@mcp.tool()
async def cap_trade_positions_get(deal_id: str) -> dict[str, Any]:
    """
    Get position details by deal ID.

    Args:
        deal_id: Deal ID of the position

    Returns detailed position information.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.get(f"/positions/{deal_id}")
    return response.json()


@mcp.tool()
async def cap_trade_orders_list() -> dict[str, Any]:
    """
    List all working orders.

    Returns pending LIMIT and STOP orders that haven't triggered yet.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.get("/workingorders")
    return response.json()


@mcp.tool()
async def cap_trade_confirm_get(deal_reference: str) -> dict[str, Any]:
    """
    Get deal confirmation status.

    Args:
        deal_reference: Deal reference from trade operation (format: o_...)

    Returns confirmation status: ACCEPTED, REJECTED, or pending.
    Includes affected deal IDs if accepted.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.get(f"/confirms/{deal_reference}")
    return response.json()


@mcp.tool()
async def cap_trade_confirm_wait(
    deal_reference: str,
    timeout_s: float = 15.0,
    poll_interval_ms: int = 500
) -> dict[str, Any]:
    """
    Wait for deal confirmation with polling.

    Args:
        deal_reference: Deal reference from trade operation
        timeout_s: Timeout in seconds (default: 15.0)
        poll_interval_ms: Poll interval in milliseconds (default: 500)

    Polls confirmation endpoint until ACCEPTED/REJECTED or timeout.
    Returns final confirmation status.
    Requires authentication.
    """
    return await _wait_for_confirmation(deal_reference, timeout_s, poll_interval_ms)


# ============================================================
# Trading Tools - Preview (Safe, No Side Effects)
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
    profit_amount: float | None = None
) -> dict[str, Any]:
    """
    Preview a position before execution (NO SIDE EFFECTS).

    Args:
        epic: Market EPIC
        direction: BUY or SELL
        size: Position size
        guaranteed_stop: Use guaranteed stop (default: false)
        trailing_stop: Use trailing stop (default: false)
        stop_level: Stop loss price level (optional)
        stop_distance: Stop loss distance from entry (optional)
        stop_amount: Stop loss amount (optional)
        profit_level: Take profit price level (optional)
        profit_distance: Take profit distance from entry (optional)
        profit_amount: Take profit amount (optional)

    Validates against:
    - Trading enabled (CAP_ALLOW_TRADING)
    - Epic allowlist (CAP_ALLOWED_EPICS) - use 'ALL' to allow all instruments
    - Broker dealing rules (min/max size, increments)
    - Local risk policy (max position size)
    - Daily order limits

    Returns preview_id for use with cap_trade_execute_position.
    This is a READ-ONLY validation, no position is created.

    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    request = PreviewPositionRequest(
        epic=epic,
        direction=direction,
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

    risk = get_risk_engine()
    preview = await risk.preview_position(request)

    return {
        "preview_id": preview.preview_id,
        "normalized_request": preview.normalized_request,
        "checks": [c.model_dump() for c in preview.checks],
        "all_checks_passed": preview.all_checks_passed,
        "estimated_entry": preview.estimated_entry,
        "estimated_risk_notes": preview.estimated_risk_notes,
        "expires_in_seconds": 120,
    }


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
    good_till_date: str | None = None
) -> dict[str, Any]:
    """
    Preview a working order before execution (NO SIDE EFFECTS).

    Args:
        epic: Market EPIC
        direction: BUY or SELL
        type: LIMIT or STOP
        level: Order trigger price level
        size: Order size
        guaranteed_stop: Use guaranteed stop (default: false)
        trailing_stop: Use trailing stop (default: false)
        stop_level: Stop loss price level (optional)
        stop_distance: Stop loss distance from entry (optional)
        stop_amount: Stop loss amount (optional)
        profit_level: Take profit price level (optional)
        profit_distance: Take profit distance from entry (optional)
        profit_amount: Take profit amount (optional)
        good_till_date: Expiry date ISO 8601 (optional)

    Similar validation to preview_position plus order-specific checks.
    Returns preview_id for use with cap_trade_execute_working_order.

    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    request = PreviewWorkingOrderRequest(
        epic=epic,
        direction=direction,
        type=type,
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

    risk = get_risk_engine()
    preview = await risk.preview_working_order(request)

    return {
        "preview_id": preview.preview_id,
        "normalized_request": preview.normalized_request,
        "checks": [c.model_dump() for c in preview.checks],
        "all_checks_passed": preview.all_checks_passed,
        "estimated_entry": preview.estimated_entry,
        "estimated_risk_notes": preview.estimated_risk_notes,
        "expires_in_seconds": 120,
    }


# ============================================================
# Trading Tools - Execute (Side Effects, Heavily Guarded)
# ============================================================


@mcp.tool()
async def cap_trade_execute_position(
    preview_id: str,
    confirm: bool = False,
    wait_for_confirm: bool = True,
    timeout_s: float = 15.0
) -> dict[str, Any]:
    """
    Execute a position (SIDE EFFECT - CREATES REAL TRADE).

    Args:
        preview_id: Preview ID from cap_trade_preview_position
        confirm: Explicit confirmation (default: false)
        wait_for_confirm: Wait for broker confirmation (default: true)
        timeout_s: Confirmation timeout (default: 15.0)

    CRITICAL SAFETY CHECKS:
    - Requires CAP_ALLOW_TRADING=true
    - Refuses if CAP_DRY_RUN=true
    - Requires confirm=true if CAP_REQUIRE_EXPLICIT_CONFIRM=true
    - Preview must exist and all checks must have passed
    - Re-validates epic is still allowed (or 'ALL' is set)

    On success:
    - Creates position on broker
    - Returns deal_reference
    - Optionally waits for confirmation (ACCEPTED/REJECTED)
    - Increments daily order counter

    Rate limit: 1 request per 0.1 seconds (trading limit).
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    risk = get_risk_engine()
    risk.validate_execution_guards(confirm=confirm, preview_id=preview_id)

    preview = risk.get_preview(preview_id)
    normalized = preview.normalized_request

    # Build broker request
    broker_request: dict[str, Any] = {
        "epic": normalized["epic"],
        "direction": normalized["direction"],
        "size": normalized["size"],
    }

    # Add optional fields
    if normalized.get("guaranteed_stop"):
        broker_request["guaranteedStop"] = True
    if normalized.get("trailing_stop"):
        broker_request["trailingStop"] = True
    if normalized.get("stop_level"):
        broker_request["stopLevel"] = normalized["stop_level"]
    if normalized.get("stop_distance"):
        broker_request["stopDistance"] = normalized["stop_distance"]
    if normalized.get("stop_amount"):
        broker_request["stopAmount"] = normalized["stop_amount"]
    if normalized.get("profit_level"):
        broker_request["profitLevel"] = normalized["profit_level"]
    if normalized.get("profit_distance"):
        broker_request["profitDistance"] = normalized["profit_distance"]
    if normalized.get("profit_amount"):
        broker_request["profitAmount"] = normalized["profit_amount"]

    # Execute trade
    client = get_client()
    response = await client.post("/positions", json=broker_request, rate_limit_type="trading")
    data = response.json()

    # Increment order counter
    risk.increment_order_count()

    # Wait for confirmation if requested
    if wait_for_confirm and "dealReference" in data:
        try:
            confirm_data = await _wait_for_confirmation(
                deal_reference=data["dealReference"],
                timeout_s=timeout_s,
            )
            data["confirmation"] = confirm_data
        except TimeoutError:
            data["confirmation"] = {"status": "TIMEOUT", "message": "Confirmation timed out"}

    return data


@mcp.tool()
async def cap_trade_execute_working_order(
    preview_id: str,
    confirm: bool = False,
    wait_for_confirm: bool = True,
    timeout_s: float = 15.0
) -> dict[str, Any]:
    """
    Execute a working order (SIDE EFFECT - CREATES REAL ORDER).

    Args:
        preview_id: Preview ID from cap_trade_preview_working_order
        confirm: Explicit confirmation (default: false)
        wait_for_confirm: Wait for broker confirmation (default: true)
        timeout_s: Confirmation timeout (default: 15.0)

    Same safety checks as execute_position.
    Creates a pending LIMIT or STOP order.

    Rate limit: 1 request per 0.1 seconds (trading limit).
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    risk = get_risk_engine()
    risk.validate_execution_guards(confirm=confirm, preview_id=preview_id)

    preview = risk.get_preview(preview_id)
    normalized = preview.normalized_request

    # Build broker request
    broker_request: dict[str, Any] = {
        "epic": normalized["epic"],
        "direction": normalized["direction"],
        "type": normalized["type"],
        "level": normalized["level"],
        "size": normalized["size"],
    }

    # Add optional fields
    if normalized.get("guaranteed_stop"):
        broker_request["guaranteedStop"] = True
    if normalized.get("trailing_stop"):
        broker_request["trailingStop"] = True
    if normalized.get("stop_level"):
        broker_request["stopLevel"] = normalized["stop_level"]
    if normalized.get("stop_distance"):
        broker_request["stopDistance"] = normalized["stop_distance"]
    if normalized.get("stop_amount"):
        broker_request["stopAmount"] = normalized["stop_amount"]
    if normalized.get("profit_level"):
        broker_request["profitLevel"] = normalized["profit_level"]
    if normalized.get("profit_distance"):
        broker_request["profitDistance"] = normalized["profit_distance"]
    if normalized.get("profit_amount"):
        broker_request["profitAmount"] = normalized["profit_amount"]
    if normalized.get("good_till_date"):
        broker_request["goodTillDate"] = normalized["good_till_date"]

    # Execute order
    client = get_client()
    response = await client.post("/workingorders", json=broker_request, rate_limit_type="trading")
    data = response.json()

    # Increment order counter
    risk.increment_order_count()

    # Wait for confirmation if requested
    if wait_for_confirm and "dealReference" in data:
        try:
            confirm_data = await _wait_for_confirmation(
                deal_reference=data["dealReference"],
                timeout_s=timeout_s,
            )
            data["confirmation"] = confirm_data
        except TimeoutError:
            data["confirmation"] = {"status": "TIMEOUT", "message": "Confirmation timed out"}

    return data


@mcp.tool()
async def cap_trade_positions_close(
    deal_id: str,
    confirm: bool = False,
    wait_for_confirm: bool = True,
    timeout_s: float = 15.0
) -> dict[str, Any]:
    """
    Close an open position (SIDE EFFECT - CLOSES TRADE).

    Args:
        deal_id: Deal ID of position to close
        confirm: Explicit confirmation (default: false)
        wait_for_confirm: Wait for broker confirmation (default: true)
        timeout_s: Confirmation timeout (default: 15.0)

    CRITICAL: Requires CAP_ALLOW_TRADING=true and confirmation.
    Refuses if CAP_DRY_RUN=true.

    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    risk = get_risk_engine()
    risk.validate_execution_guards(confirm=confirm)

    client = get_client()
    response = await client.delete(f"/positions/{deal_id}")
    data = response.json()

    # Wait for confirmation if requested
    if wait_for_confirm and "dealReference" in data:
        try:
            confirm_data = await _wait_for_confirmation(
                deal_reference=data["dealReference"],
                timeout_s=timeout_s,
            )
            data["confirmation"] = confirm_data
        except TimeoutError:
            data["confirmation"] = {"status": "TIMEOUT", "message": "Confirmation timed out"}

    return data


@mcp.tool()
async def cap_trade_orders_cancel(
    deal_id: str,
    confirm: bool = False,
    wait_for_confirm: bool = True,
    timeout_s: float = 15.0
) -> dict[str, Any]:
    """
    Cancel a working order (SIDE EFFECT - CANCELS ORDER).

    Args:
        deal_id: Deal ID of order to cancel
        confirm: Explicit confirmation (default: false)
        wait_for_confirm: Wait for broker confirmation (default: true)
        timeout_s: Confirmation timeout (default: 15.0)

    CRITICAL: Requires CAP_ALLOW_TRADING=true and confirmation.
    Refuses if CAP_DRY_RUN=true.

    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    risk = get_risk_engine()
    risk.validate_execution_guards(confirm=confirm)

    client = get_client()
    response = await client.delete(f"/workingorders/{deal_id}")
    data = response.json()

    # Wait for confirmation if requested
    if wait_for_confirm and "dealReference" in data:
        try:
            confirm_data = await _wait_for_confirmation(
                deal_reference=data["dealReference"],
                timeout_s=timeout_s,
            )
            data["confirmation"] = confirm_data
        except TimeoutError:
            data["confirmation"] = {"status": "TIMEOUT", "message": "Confirmation timed out"}

    return data


# ============================================================
# Watchlist Tools
# ============================================================


@mcp.tool()
async def cap_watchlists_list() -> dict[str, Any]:
    """
    List all watchlists.

    Returns user's watchlists with IDs and names.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.get("/watchlists")
    return response.json()


@mcp.tool()
async def cap_watchlists_get(watchlist_id: str) -> dict[str, Any]:
    """
    Get watchlist details including markets.

    Args:
        watchlist_id: Watchlist ID

    Returns watchlist with list of EPICs.
    Requires authentication.
    """
    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.get(f"/watchlists/{watchlist_id}")
    return response.json()


@mcp.tool()
async def cap_watchlists_create(name: str, confirm: bool = False) -> dict[str, Any]:
    """
    Create a new watchlist.

    Args:
        name: Watchlist name (1-100 characters)
        confirm: Explicit confirmation (default: false)

    Requires confirm=true if CAP_REQUIRE_EXPLICIT_CONFIRM=true.
    Requires authentication.
    """
    config = get_config()
    if config.cap_require_explicit_confirm and not confirm:
        raise ValueError("Explicit confirmation required. Set confirm=true")

    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.post("/watchlists", json={"name": name})
    return response.json()


@mcp.tool()
async def cap_watchlists_add_market(
    watchlist_id: str,
    epic: str,
    confirm: bool = False
) -> dict[str, Any]:
    """
    Add market to watchlist.

    Args:
        watchlist_id: Watchlist ID
        epic: Market EPIC to add
        confirm: Explicit confirmation (default: false)

    Requires confirm=true if CAP_REQUIRE_EXPLICIT_CONFIRM=true.
    Requires authentication.
    """
    config = get_config()
    if config.cap_require_explicit_confirm and not confirm:
        raise ValueError("Explicit confirmation required. Set confirm=true")

    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.put(f"/watchlists/{watchlist_id}", json={"epic": epic})
    return response.json()


@mcp.tool()
async def cap_watchlists_delete(watchlist_id: str, confirm: bool = False) -> dict[str, Any]:
    """
    Delete a watchlist.

    Args:
        watchlist_id: Watchlist ID
        confirm: Explicit confirmation (default: false)

    Requires confirm=true if CAP_REQUIRE_EXPLICIT_CONFIRM=true.
    Requires authentication.
    """
    config = get_config()
    if config.cap_require_explicit_confirm and not confirm:
        raise ValueError("Explicit confirmation required. Set confirm=true")

    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.delete(f"/watchlists/{watchlist_id}")
    return response.json() if response.text else {"status": "deleted"}


@mcp.tool()
async def cap_watchlists_remove_market(
    watchlist_id: str,
    epic: str,
    confirm: bool = False
) -> dict[str, Any]:
    """
    Remove market from watchlist.

    Args:
        watchlist_id: Watchlist ID
        epic: Market EPIC to remove
        confirm: Explicit confirmation (default: false)

    Requires confirm=true if CAP_REQUIRE_EXPLICIT_CONFIRM=true.
    Requires authentication.
    """
    config = get_config()
    if config.cap_require_explicit_confirm and not confirm:
        raise ValueError("Explicit confirmation required. Set confirm=true")

    session = get_session_manager()
    await session.ensure_logged_in()

    client = get_client()
    response = await client.delete(f"/watchlists/{watchlist_id}/{epic}")
    return response.json() if response.text else {"status": "removed"}


# ============================================================
# Server Lifecycle
# ============================================================


if __name__ == "__main__":
    config = get_config()
    logger.info(f"Starting Capital.com MCP Server (env: {config.cap_env.value})")
    logger.info(f"Trading enabled: {config.cap_allow_trading}")

    if config.cap_allow_trading:
        allowed = config.allowed_epics_list
        if allowed and allowed[0].upper() == 'ALL':
            logger.info("Allowed EPICs: ALL (no restrictions)")
        else:
            logger.info(f"Allowed EPICs: {allowed}")

    # Run FastMCP server (handles STDIO automatically)
    mcp.run()
