import pytest

pytestmark = pytest.mark.asyncio


async def test_watchlist_list(client, fake_app):
    fake_app.watchlists.list.return_value = {"watchlists": []}
    result = await client.call_tool("cap_watchlists_list", {})
    assert result.data == {"watchlists": []}


async def test_watchlist_create_passes_confirm(client, fake_app):
    fake_app.watchlists.create.return_value = {"watchlistId": "w1"}
    await client.call_tool("cap_watchlists_create", {"name": "Metals", "confirm": True})
    fake_app.watchlists.create.assert_awaited_once_with("Metals", confirm=True)


async def test_watchlist_add_market(client, fake_app):
    fake_app.watchlists.add_market.return_value = {"status": "SUCCESS"}
    await client.call_tool(
        "cap_watchlists_add_market", {"watchlist_id": "w1", "epic": "GOLD", "confirm": True}
    )
    fake_app.watchlists.add_market.assert_awaited_once_with("w1", "GOLD", confirm=True)


async def test_watchlist_remove_market(client, fake_app):
    fake_app.watchlists.remove_market.return_value = {"status": "SUCCESS"}
    await client.call_tool(
        "cap_watchlists_remove_market", {"watchlist_id": "w1", "epic": "GOLD", "confirm": True}
    )
    fake_app.watchlists.remove_market.assert_awaited_once_with("w1", "GOLD", confirm=True)
