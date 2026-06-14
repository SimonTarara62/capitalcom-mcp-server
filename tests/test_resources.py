import json

import pytest

pytestmark = pytest.mark.asyncio


async def test_risk_policy_resource(client, fake_app):
    result = await client.read_resource("cap://risk-policy")
    payload = json.loads(result[0].text)
    assert payload["trading_enabled"] is False
    assert payload["two_phase_execution"] is True
    assert "GOLD" in payload["allowlist"]["epics"]


async def test_allowed_epics_resource(client, fake_app):
    result = await client.read_resource("cap://allowed-epics")
    payload = json.loads(result[0].text)
    assert payload["count"] == 2
    assert payload["mode"] == "SPECIFIC"
