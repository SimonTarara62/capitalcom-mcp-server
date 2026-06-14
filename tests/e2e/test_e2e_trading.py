"""E2E (opt-in): preview + trade-mutation MCP tools against the demo API.

Mutation tests place REAL demo orders and REQUIRE the demo .env to enable trading
for the target EPIC (CAP_ALLOW_TRADING=true + CAP_ALLOWED_EPICS). They fail with
a clear message if it isn't enabled, and always clean up (close/cancel) what they
open. Run on a DEMO account only.
"""

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.environ.get("CAP_MCP_E2E"):
    pytest.skip("set CAP_MCP_E2E=1 to run e2e", allow_module_level=True)

# Use a 24/7 market so executions run regardless of the hour (GOLD etc. close
# outside exchange hours, which would reject market-order execution).
EPIC = "BTCUSD"
SIZE = 0.01


async def _call(client, name, args=None):
    result = await client.call_tool(name, args or {})
    return result.data


def _trading_enabled_for(epic: str) -> bool:
    import capital_mcp.context as ctx

    policy = ctx.get_app().risk_policy
    if not policy.allow_trading:
        return False
    allowed = [e.upper() for e in policy.allowed_epics]
    return "ALL" in allowed or epic.upper() in allowed


async def test_e2e_preview_position(mcp_client):
    data = await _call(
        mcp_client,
        "cap_trade_preview_position",
        {"epic": EPIC, "direction": "BUY", "size": SIZE},
    )
    assert data["preview_id"]
    assert isinstance(data["all_checks_passed"], bool)


async def test_e2e_preview_working_order(mcp_client):
    market = await _call(mcp_client, "cap_market_get", {"epic": EPIC})
    bid = market["snapshot"]["bid"]
    data = await _call(
        mcp_client,
        "cap_trade_preview_working_order",
        {"epic": EPIC, "direction": "BUY", "type": "LIMIT", "level": bid * 0.5, "size": SIZE},
    )
    assert data["preview_id"]


async def test_e2e_preferences_set(mcp_client):
    assert _trading_enabled_for(EPIC), (
        "Full e2e places real DEMO orders: set CAP_ALLOW_TRADING=true and add "
        f"{EPIC} (or ALL) to CAP_ALLOWED_EPICS in the demo .env."
    )
    current = await _call(mcp_client, "cap_account_preferences_get")
    hedging = bool(current.get("hedgingMode", False))
    data = await _call(
        mcp_client,
        "cap_account_preferences_set",
        {"hedging_mode": hedging, "confirm": True},
    )
    assert isinstance(data, dict)


async def test_e2e_execute_close_position(mcp_client):
    assert _trading_enabled_for(EPIC), (
        "Full e2e places real DEMO orders: set CAP_ALLOW_TRADING=true and add "
        f"{EPIC} (or ALL) to CAP_ALLOWED_EPICS in the demo .env."
    )
    preview = await _call(
        mcp_client,
        "cap_trade_preview_position",
        {"epic": EPIC, "direction": "BUY", "size": SIZE},
    )
    assert preview["all_checks_passed"], preview["checks"]
    executed = await _call(
        mcp_client,
        "cap_trade_execute_position",
        {"preview_id": preview["preview_id"], "confirm": True, "wait_for_confirm": True},
    )
    deal_ref = executed.get("dealReference")
    assert deal_ref
    confirm = await _call(
        mcp_client, "cap_trade_confirm_wait", {"deal_reference": deal_ref, "timeout_s": 15.0}
    )
    assert confirm.get("status") in {"ACCEPTED", "REJECTED", "TIMEOUT"}
    positions = (await _call(mcp_client, "cap_trade_positions_list")).get("positions", [])
    deal_id = next(
        (
            p.get("position", {}).get("dealId")
            for p in positions
            if p.get("market", {}).get("epic") == EPIC
        ),
        None,
    )
    assert deal_id, "could not resolve the opened position's dealId"
    try:
        market = await _call(mcp_client, "cap_market_get", {"epic": EPIC})
        stop_level = round(market["snapshot"]["bid"] * 0.9, 1)  # valid stop below a BUY
        amended = await _call(
            mcp_client,
            "cap_trade_positions_amend",
            {"deal_id": deal_id, "stop_level": stop_level, "confirm": True},
        )
        assert isinstance(amended, dict)
    finally:
        closed = await _call(
            mcp_client, "cap_trade_positions_close", {"deal_id": deal_id, "confirm": True}
        )
        assert isinstance(closed, dict)


async def test_e2e_execute_cancel_order(mcp_client):
    assert _trading_enabled_for(EPIC), (
        "Full e2e places real DEMO orders: set CAP_ALLOW_TRADING=true and add "
        f"{EPIC} (or ALL) to CAP_ALLOWED_EPICS in the demo .env."
    )
    market = await _call(mcp_client, "cap_market_get", {"epic": EPIC})
    bid = market["snapshot"]["bid"]
    level = round(bid * 0.5, 2)
    preview = await _call(
        mcp_client,
        "cap_trade_preview_working_order",
        {"epic": EPIC, "direction": "BUY", "type": "LIMIT", "level": level, "size": SIZE},
    )
    assert preview["all_checks_passed"], preview["checks"]
    executed = await _call(
        mcp_client,
        "cap_trade_execute_working_order",
        {"preview_id": preview["preview_id"], "confirm": True, "wait_for_confirm": True},
    )
    assert executed.get("dealReference")
    orders = (await _call(mcp_client, "cap_trade_orders_list")).get("workingOrders", [])
    deal_id = next(
        (
            o["workingOrderData"]["dealId"]
            for o in orders
            if o.get("marketData", {}).get("epic") == EPIC
        ),
        None,
    )
    assert deal_id, "could not resolve the working order's dealId"
    try:
        amended = await _call(
            mcp_client,
            "cap_trade_orders_amend",
            {"deal_id": deal_id, "level": round(bid * 0.55, 2), "confirm": True},
        )
        assert isinstance(amended, dict)
    finally:
        cancelled = await _call(
            mcp_client, "cap_trade_orders_cancel", {"deal_id": deal_id, "confirm": True}
        )
        assert isinstance(cancelled, dict)
