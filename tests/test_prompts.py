import pytest

pytestmark = pytest.mark.asyncio


async def test_prompts_registered(client):
    prompts = await client.list_prompts()
    names = {p.name for p in prompts}
    assert {"market_scan", "trade_proposal", "execute_trade", "position_review"} <= names


async def test_trade_proposal_renders(client):
    result = await client.get_prompt("trade_proposal", {"epic": "GOLD", "direction": "BUY"})
    text = result.messages[0].content.text
    assert "GOLD" in text
