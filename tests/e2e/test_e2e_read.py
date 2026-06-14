"""E2E (opt-in): read + safe-mutation MCP tools against the demo API."""

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.environ.get("CAP_MCP_E2E"):
    pytest.skip("set CAP_MCP_E2E=1 to run e2e", allow_module_level=True)

EPIC = "GOLD"


async def _call(client, name, args=None):
    result = await client.call_tool(name, args or {})
    return result.data


# ---- session ----


async def test_e2e_session_status(mcp_client):
    data = await _call(mcp_client, "cap_session_status")
    assert "logged_in" in data


async def test_e2e_session_login(mcp_client):
    data = await _call(mcp_client, "cap_session_login", {"force": True})
    assert data.get("active_account_id")


async def test_e2e_session_ping(mcp_client):
    data = await _call(mcp_client, "cap_session_ping")
    assert isinstance(data, dict)


async def test_e2e_session_switch_account(mcp_client):
    accounts = (await _call(mcp_client, "cap_account_list"))["accounts"]
    active_id = next(
        (a["accountId"] for a in accounts if a.get("preferred")), accounts[0]["accountId"]
    )
    others = [a["accountId"] for a in accounts if a["accountId"] != active_id]
    if not others:
        pytest.skip("only one account on this demo login")
    try:
        data = await _call(mcp_client, "cap_session_switch_account", {"account_id": others[0]})
        assert data.get("active_account_id") == others[0]
    finally:
        # restore the original active account
        await _call(mcp_client, "cap_session_switch_account", {"account_id": active_id})


async def test_e2e_session_logout(mcp_client):
    data = await _call(mcp_client, "cap_session_logout")
    assert data == {"message": "Logged out successfully"}


# ---- market ----


async def test_e2e_market_search(mcp_client):
    data = await _call(mcp_client, "cap_market_search", {"search_term": "gold", "limit": 5})
    assert "markets" in data


async def test_e2e_market_get(mcp_client):
    data = await _call(mcp_client, "cap_market_get", {"epic": EPIC})
    assert data.get("instrument", {}).get("epic") == EPIC


async def test_e2e_market_prices(mcp_client):
    data = await _call(
        mcp_client, "cap_market_prices", {"epic": EPIC, "resolution": "HOUR", "max": 5}
    )
    assert data.get("prices")


async def test_e2e_market_sentiment(mcp_client):
    data = await _call(mcp_client, "cap_market_sentiment", {"market_id": EPIC})
    assert isinstance(data, dict)


async def test_e2e_market_navigation(mcp_client):
    root = await _call(mcp_client, "cap_market_navigation_root")
    assert "nodes" in root
    node_id = root["nodes"][0]["id"]
    node = await _call(mcp_client, "cap_market_navigation_node", {"node_id": node_id})
    assert "nodes" in node or "markets" in node


# ---- account ----


async def test_e2e_account_list(mcp_client):
    data = await _call(mcp_client, "cap_account_list")
    assert "accounts" in data
    assert data.get("active_account_id")


async def test_e2e_account_preferences_get(mcp_client):
    data = await _call(mcp_client, "cap_account_preferences_get")
    assert isinstance(data, dict)


async def test_e2e_account_history(mcp_client):
    activity = await _call(mcp_client, "cap_account_history_activity", {"last_period": 600})
    assert isinstance(activity, dict)
    tx = await _call(mcp_client, "cap_account_history_transactions", {"last_period": 600})
    assert isinstance(tx, dict)


async def test_e2e_account_demo_topup(mcp_client):
    # A success OR a broker "account.limit.reached" rejection both prove the tool
    # reached the demo top-up endpoint (the demo balance may already be at its cap).
    try:
        data = await _call(
            mcp_client, "cap_account_demo_topup", {"amount": 1000.0, "confirm": True}
        )
        assert isinstance(data, dict)
    except Exception as exc:  # noqa: BLE001 — limit-reached is a valid broker response
        assert "limit" in str(exc).lower()


# ---- trading read + negative ----


async def test_e2e_positions_list(mcp_client):
    data = await _call(mcp_client, "cap_trade_positions_list")
    assert "positions" in data


async def test_e2e_orders_list(mcp_client):
    data = await _call(mcp_client, "cap_trade_orders_list")
    assert isinstance(data, dict)


async def test_e2e_positions_get_negative(mcp_client):
    with pytest.raises(Exception):  # noqa: B017
        await _call(
            mcp_client,
            "cap_trade_positions_get",
            {"deal_id": "00000000-0000-0000-0000-000000000000"},
        )


async def test_e2e_confirm_get_negative(mcp_client):
    with pytest.raises(Exception):  # noqa: B017
        await _call(mcp_client, "cap_trade_confirm_get", {"deal_reference": "no_such_ref"})


# ---- watchlist lifecycle (safe) ----


async def test_e2e_watchlist_lifecycle(mcp_client):
    created = await _call(
        mcp_client, "cap_watchlists_create", {"name": "capctl-e2e-tmp", "confirm": True}
    )
    wl_id = created.get("watchlistId") or created.get("id")
    assert wl_id
    try:
        listed = await _call(mcp_client, "cap_watchlists_list")
        assert "watchlists" in listed
        await _call(
            mcp_client,
            "cap_watchlists_add_market",
            {"watchlist_id": wl_id, "epic": EPIC, "confirm": True},
        )
        got = await _call(mcp_client, "cap_watchlists_get", {"watchlist_id": wl_id})
        assert isinstance(got, dict)
        await _call(
            mcp_client,
            "cap_watchlists_remove_market",
            {"watchlist_id": wl_id, "epic": EPIC, "confirm": True},
        )
    finally:
        await _call(
            mcp_client, "cap_watchlists_delete", {"watchlist_id": wl_id, "confirm": True}
        )


# ---- ChatGPT Deep Research adapters ----


async def test_e2e_chatgpt_search(mcp_client):
    data = await _call(mcp_client, "search", {"query": "gold"})
    assert isinstance(data["results"], list)


async def test_e2e_chatgpt_fetch(mcp_client):
    data = await _call(mcp_client, "fetch", {"id": EPIC})
    assert data["id"] == EPIC
    assert isinstance(data["text"], str)
