import pytest

pytestmark = pytest.mark.asyncio


async def test_account_list_adds_active_account(client, fake_app):
    fake_app.accounts.list.return_value = {"accounts": []}
    result = await client.call_tool("cap_account_list", {})
    assert result.data["active_account_id"] == "TEST123"


async def test_preferences_set_maps_hedging_mode(client, fake_app):
    fake_app.accounts.set_preferences.return_value = {"status": "SUCCESS"}
    await client.call_tool(
        "cap_account_preferences_set",
        {"hedging_mode": True, "leverages": {"SHARES": 5}, "confirm": True},
    )
    fake_app.accounts.set_preferences.assert_awaited_once_with(
        hedging=True, leverages={"SHARES": 5}, confirm=True
    )


async def test_demo_topup_passes_confirm(client, fake_app):
    fake_app.accounts.demo_topup.return_value = {"successful": True}
    await client.call_tool("cap_account_demo_topup", {"amount": 1000.0, "confirm": True})
    fake_app.accounts.demo_topup.assert_awaited_once_with(1000.0, confirm=True)


async def test_history_transactions_maps_type(client, fake_app):
    fake_app.accounts.history_transactions.return_value = {"transactions": []}
    await client.call_tool(
        "cap_account_history_transactions", {"last_period": 600, "type": "DEPOSIT"}
    )
    fake_app.accounts.history_transactions.assert_awaited_once_with(
        last_period=600, type_="DEPOSIT", from_date=None, to_date=None
    )
