"""Tests for WebSocket streaming client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.mark.asyncio
async def test_websocket_client_connect():
    """Test WebSocket client connection."""
    from capital_mcp.websocket_client import WebSocketClient
    from capital_mcp.errors import SessionError

    # Test connection failure when WS is disabled
    with patch("capital_mcp.websocket_client.get_config") as mock_config:
        mock_config.return_value.cap_ws_enabled = False

        client = WebSocketClient()
        with pytest.raises(SessionError, match="WebSocket streaming is disabled"):
            await client.connect()


@pytest.mark.asyncio
async def test_websocket_client_subscribe():
    """Test WebSocket subscription."""
    from capital_mcp.websocket_client import WebSocketClient

    client = WebSocketClient()

    # Test subscribing to too many EPICs
    many_epics = [f"EPIC{i}" for i in range(50)]
    with pytest.raises(ValueError, match="Cannot subscribe to more than 40 EPICs"):
        await client.subscribe(many_epics)


@pytest.mark.asyncio
async def test_price_tick_model():
    """Test PriceTick model validation."""
    from capital_mcp.models import PriceTick

    tick = PriceTick(
        epic="GOLD",
        bid=2048.50,
        offer=2049.00,
        timestamp="2026-01-16T14:30:00Z",
        change_percent=0.5
    )

    assert tick.epic == "GOLD"
    assert tick.bid == 2048.50
    assert tick.offer == 2049.00
    assert tick.change_percent == 0.5


@pytest.mark.asyncio
async def test_stream_alert_model():
    """Test StreamAlert model validation."""
    from capital_mcp.models import StreamAlert

    alert = StreamAlert(
        epic="GOLD",
        condition="LEVEL_ABOVE",
        trigger_price=2050.0,
        current_price=2050.25,
        timestamp="2026-01-16T14:32:18Z"
    )

    assert alert.epic == "GOLD"
    assert alert.condition == "LEVEL_ABOVE"
    assert alert.trigger_price == 2050.0
    assert alert.current_price == 2050.25


@pytest.mark.asyncio
async def test_portfolio_snapshot_model():
    """Test PortfolioSnapshot model validation."""
    from capital_mcp.models import PortfolioSnapshot

    snapshot = PortfolioSnapshot(
        positions=[
            {"deal_id": "123", "epic": "GOLD", "pnl": 125.50},
            {"deal_id": "456", "epic": "SILVER", "pnl": -18.20}
        ],
        total_pnl=107.30,
        timestamp="2026-01-16T14:30:00Z"
    )

    assert len(snapshot.positions) == 2
    assert snapshot.total_pnl == 107.30
    assert snapshot.positions[0]["epic"] == "GOLD"


@pytest.mark.asyncio
async def test_websocket_client_parse_message():
    """Test WebSocket message parsing."""
    from capital_mcp.websocket_client import WebSocketClient
    import json

    client = WebSocketClient()

    # Test valid price update message
    message = json.dumps({
        "destination": "market.GOLD",
        "payload": {
            "bid": 2048.50,
            "offer": 2049.00,
            "changePercent": 0.5
        }
    })

    tick = client._parse_message(message)
    assert tick is not None
    assert tick.epic == "GOLD"
    assert tick.bid == 2048.50
    assert tick.offer == 2049.00

    # Test invalid message
    invalid_message = json.dumps({"invalid": "data"})
    tick = client._parse_message(invalid_message)
    assert tick is None


@pytest.mark.asyncio
async def test_streaming_tools_registered():
    """Test that streaming tools are registered in MCP server."""
    from capital_mcp.server import mcp

    tools = await mcp.get_tools()
    tool_names = list(tools.keys())

    assert "cap_stream_prices" in tool_names
    assert "cap_stream_alerts" in tool_names
    assert "cap_stream_portfolio" in tool_names


@pytest.mark.asyncio
async def test_streaming_prompts_registered():
    """Test that streaming prompts are registered in MCP server."""
    from capital_mcp.server import mcp

    prompts = await mcp.get_prompts()
    prompt_names = list(prompts.keys())

    assert "live_price_monitor" in prompt_names
    assert "real_time_alerts" in prompt_names
    assert "live_portfolio_monitor" in prompt_names
