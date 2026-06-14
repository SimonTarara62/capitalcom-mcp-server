"""E2E (opt-in): streaming MCP tools. REQUIRE CAP_WS_ENABLED=true (fail loudly otherwise)."""

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.environ.get("CAP_MCP_E2E"):
    pytest.skip("set CAP_MCP_E2E=1 to run e2e", allow_module_level=True)

EPIC = "GOLD"


async def _call(client, name, args=None):
    result = await client.call_tool(name, args or {})
    return result.data


def _ws_enabled() -> bool:
    import capital_mcp.context as ctx

    return bool(ctx.get_app().config.cap_ws_enabled)


async def test_e2e_stream_prices(mcp_client):
    assert _ws_enabled(), "Full e2e needs streaming: set CAP_WS_ENABLED=true in the demo .env."
    data = await _call(
        mcp_client,
        "cap_stream_prices",
        {"epics": [EPIC], "duration_s": 3.0, "update_interval_s": 0.0},
    )
    assert data["status"] == "completed"
    assert "ticks" in data


async def test_e2e_stream_candles(mcp_client):
    assert _ws_enabled(), "Full e2e needs streaming: set CAP_WS_ENABLED=true in the demo .env."
    data = await _call(
        mcp_client,
        "cap_stream_candles",
        {"epics": [EPIC], "resolutions": ["MINUTE"], "duration_s": 5.0, "update_interval_s": 0.0},
    )
    assert data["status"] == "completed"
    assert "bars" in data


async def test_e2e_stream_alerts(mcp_client):
    assert _ws_enabled(), "Full e2e needs streaming: set CAP_WS_ENABLED=true in the demo .env."
    market = await _call(mcp_client, "cap_market_get", {"epic": EPIC})
    bid = market["snapshot"]["bid"]
    data = await _call(
        mcp_client,
        "cap_stream_alerts",
        {
            "alerts": {EPIC: {"level": bid * 0.5, "direction": "ABOVE"}},
            "duration_s": 5.0,
            "auto_close": True,
        },
    )
    assert data["status"] == "completed"


async def test_e2e_stream_portfolio(mcp_client):
    assert _ws_enabled(), "Full e2e needs streaming: set CAP_WS_ENABLED=true in the demo .env."
    data = await _call(
        mcp_client, "cap_stream_portfolio", {"duration_s": 3.0, "update_interval_s": 0.0}
    )
    assert data["status"] in {"completed", "no_positions"}
