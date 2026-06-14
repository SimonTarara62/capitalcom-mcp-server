from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.asyncio


def _tick(epic, bid, offer):
    return SimpleNamespace(
        epic=epic, bid=bid, offer=offer,
        model_dump=lambda: {"epic": epic, "bid": bid, "offer": offer},
    )


async def _aiter(items):
    for it in items:
        yield it


async def test_stream_prices_collects_ticks(client, fake_app):
    fake_app.stream.prices = lambda epics, duration=300.0: _aiter(
        [_tick("GOLD", 2000, 2001), _tick("GOLD", 2002, 2003)]
    )
    result = await client.call_tool(
        "cap_stream_prices", {"epics": ["GOLD"], "duration_s": 1.0, "update_interval_s": 0.0}
    )
    assert result.data["status"] == "completed"
    assert result.data["ticks_received"] == 2


async def test_stream_prices_rejects_too_many_epics(client, fake_app):
    result = await client.call_tool(
        "cap_stream_prices", {"epics": [f"E{i}" for i in range(41)]}
    )
    assert "error" in result.data


async def test_stream_candles_collects_bars(client, fake_app):
    def _bar(epic, close):
        return SimpleNamespace(
            epic=epic, close=close,
            model_dump=lambda: {"epic": epic, "close": close, "resolution": "MINUTE"},
        )

    fake_app.stream.candles = lambda epics, resolutions, bar_type="classic", duration=300.0: _aiter(
        [_bar("GOLD", 2000), _bar("GOLD", 2001)]
    )
    result = await client.call_tool(
        "cap_stream_candles",
        {"epics": ["GOLD"], "resolutions": ["MINUTE"], "duration_s": 1.0, "update_interval_s": 0.0},
    )
    assert result.data["status"] == "completed"
    assert result.data["bars_received"] == 2


async def test_stream_alerts_triggers(client, fake_app):
    fake_app.stream.prices = lambda epics, duration=300.0: _aiter([_tick("GOLD", 2050, 2052)])
    result = await client.call_tool(
        "cap_stream_alerts",
        {"alerts": {"GOLD": {"level": 2049.0, "direction": "ABOVE"}}, "duration_s": 1.0},
    )
    assert result.data["alerts_triggered"] == 1
