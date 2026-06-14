import pytest

pytestmark = pytest.mark.asyncio


async def test_market_search_joins_epics(client, fake_app):
    fake_app.markets.search.return_value = {"markets": [{"epic": "GOLD"}]}
    result = await client.call_tool(
        "cap_market_search", {"search_term": "gold", "epics": ["GOLD", "SILVER"], "limit": 10}
    )
    fake_app.markets.search.assert_awaited_once_with("gold", epics="GOLD,SILVER", limit=10)
    assert result.data == {"markets": [{"epic": "GOLD"}]}


async def test_market_prices_maps_max_to_max_candles(client, fake_app):
    fake_app.markets.prices.return_value = {"prices": []}
    await client.call_tool("cap_market_prices", {"epic": "GOLD", "max": 50})
    fake_app.markets.prices.assert_awaited_once_with(
        "GOLD", resolution="MINUTE_15", max_candles=50, from_date=None, to_date=None
    )


async def test_market_sentiment_wraps_single_id(client, fake_app):
    fake_app.markets.sentiment.return_value = {"longPositionPercentage": 60}
    await client.call_tool("cap_market_sentiment", {"market_id": "GOLD"})
    fake_app.markets.sentiment.assert_awaited_once_with(["GOLD"])
