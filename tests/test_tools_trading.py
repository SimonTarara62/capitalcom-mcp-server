import pytest

import capital_mcp.server as server

pytestmark = pytest.mark.asyncio


async def test_positions_list(client, fake_app):
    fake_app.trading.list_positions.return_value = {"positions": []}
    result = await client.call_tool("cap_trade_positions_list", {})
    fake_app.trading.list_positions.assert_awaited_once()
    assert result.data == {"positions": []}


async def test_confirm_get_calls_module_fn(client, fake_app, monkeypatch):
    from unittest.mock import AsyncMock
    fn = AsyncMock(return_value={"status": "ACCEPTED"})
    monkeypatch.setattr(server, "get_confirmation", fn)
    result = await client.call_tool("cap_trade_confirm_get", {"deal_reference": "o_123"})
    fn.assert_awaited_once_with("o_123")
    assert result.data == {"status": "ACCEPTED"}


async def test_confirm_wait_passes_args(client, fake_app, monkeypatch):
    from unittest.mock import AsyncMock
    fn = AsyncMock(return_value={"status": "ACCEPTED"})
    monkeypatch.setattr(server, "wait_for_confirmation", fn)
    await client.call_tool(
        "cap_trade_confirm_wait",
        {"deal_reference": "o_123", "timeout_s": 5.0, "poll_interval_ms": 250},
    )
    fn.assert_awaited_once_with("o_123", timeout_s=5.0, poll_interval_ms=250)


async def test_preview_position_builds_request_and_serializes(client, fake_app):
    from types import SimpleNamespace

    captured = {}

    async def fake_preview(req):
        captured["req"] = req
        return SimpleNamespace(
            preview_id="pv-1",
            normalized_request={"epic": "GOLD"},
            checks=[SimpleNamespace(model_dump=lambda: {"check": "size", "passed": True, "message": "ok"})],
            all_checks_passed=True,
            estimated_entry=2000.0,
            estimated_risk_notes=None,
        )

    fake_app.trading.preview_position = fake_preview
    result = await client.call_tool(
        "cap_trade_preview_position",
        {"epic": "GOLD", "direction": "buy", "size": 0.5, "stop_distance": 15},
    )
    assert result.data["preview_id"] == "pv-1"
    assert result.data["all_checks_passed"] is True
    assert result.data["expires_in_seconds"] == 120
    assert str(captured["req"].direction).upper().endswith("BUY")
    assert captured["req"].size == 0.5


async def test_execute_position_maps_wait_flag(client, fake_app):
    fake_app.trading.execute_position.return_value = {"dealReference": "o_1"}
    await client.call_tool(
        "cap_trade_execute_position",
        {"preview_id": "pv-1", "confirm": True, "wait_for_confirm": False, "timeout_s": 5.0},
    )
    fake_app.trading.execute_position.assert_awaited_once_with(
        "pv-1", confirm=True, wait=False, timeout_s=5.0
    )


async def test_close_position_maps_args(client, fake_app):
    fake_app.trading.close_position.return_value = {"dealReference": "o_2"}
    await client.call_tool("cap_trade_positions_close", {"deal_id": "d1", "confirm": True})
    fake_app.trading.close_position.assert_awaited_once_with(
        "d1", confirm=True, wait=True, timeout_s=15.0
    )


async def test_cancel_order_maps_args(client, fake_app):
    fake_app.trading.cancel_order.return_value = {"dealReference": "o_3"}
    await client.call_tool("cap_trade_orders_cancel", {"deal_id": "o1", "confirm": True})
    fake_app.trading.cancel_order.assert_awaited_once_with(
        "o1", confirm=True, wait=True, timeout_s=15.0
    )


async def test_amend_position_builds_body(client, fake_app):
    fake_app.trading.amend_position.return_value = {"dealReference": "o_4"}
    await client.call_tool(
        "cap_trade_positions_amend",
        {"deal_id": "d1", "stop_level": 1990.0, "profit_level": 2100.0, "confirm": True},
    )
    fake_app.trading.amend_position.assert_awaited_once_with(
        "d1",
        body={"stopLevel": 1990.0, "profitLevel": 2100.0},
        confirm=True,
        wait=True,
        timeout_s=15.0,
    )


async def test_amend_order_builds_body(client, fake_app):
    fake_app.trading.amend_order.return_value = {"dealReference": "o_5"}
    await client.call_tool(
        "cap_trade_orders_amend",
        {"deal_id": "o1", "level": 2050.0, "good_till_date": "2026-12-31T00:00:00", "confirm": True},
    )
    fake_app.trading.amend_order.assert_awaited_once_with(
        "o1",
        body={"level": 2050.0, "goodTillDate": "2026-12-31T00:00:00"},
        confirm=True,
        wait=True,
        timeout_s=15.0,
    )
