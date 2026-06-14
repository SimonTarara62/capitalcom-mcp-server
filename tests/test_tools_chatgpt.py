import pytest

pytestmark = pytest.mark.asyncio


async def test_search_returns_results_shape(client, fake_app):
    fake_app.markets.search.return_value = {
        "markets": [{"epic": "GOLD", "instrumentName": "Gold"}]
    }
    result = await client.call_tool("search", {"query": "gold"})
    assert result.data["results"][0]["id"] == "GOLD"
    assert result.data["results"][0]["title"] == "Gold"


async def test_fetch_returns_document_shape(client, fake_app):
    fake_app.markets.get.return_value = {
        "instrument": {"name": "Gold", "epic": "GOLD"},
        "snapshot": {"bid": 2000, "offer": 2001},
    }
    result = await client.call_tool("fetch", {"id": "GOLD"})
    assert result.data["id"] == "GOLD"
    assert "Gold" in result.data["title"]
    assert isinstance(result.data["text"], str)
