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


PROMPT_NAMES = [
    "market_scan",
    "trade_proposal",
    "execute_trade",
    "position_review",
    "live_price_monitor",
    "real_time_alerts",
    "live_portfolio_monitor",
]

TRADE_PROMPTS = ["trade_proposal", "execute_trade", "position_review"]

FOOTER = "_Capital.com MCP — demo account recommended; this is not financial advice._"


async def test_trade_proposal_error_branch_has_footer(client):
    result = await client.get_prompt("trade_proposal", {"epic": "BTCUSD", "direction": "INVALID"})
    text = result.messages[0].content.text
    assert "Invalid direction" in text
    assert FOOTER in text


@pytest.mark.parametrize("name", PROMPT_NAMES)
async def test_prompt_renders_with_footer(client, name):
    args = {}
    if name == "trade_proposal":
        args = {"epic": "BTCUSD"}
    result = await client.get_prompt(name, args)
    text = result.messages[0].content.text
    assert isinstance(text, str) and text.strip()
    assert FOOTER in text, f"{name} is missing the standard footer"


@pytest.mark.parametrize("name", TRADE_PROMPTS)
async def test_trade_prompts_mention_two_phase(client, name):
    args = {"epic": "BTCUSD"} if name == "trade_proposal" else {}
    result = await client.get_prompt(name, args)
    text = result.messages[0].content.text.lower()
    assert "two-phase" in text or "preview" in text
