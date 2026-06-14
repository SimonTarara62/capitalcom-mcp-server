import pytest

pytestmark = pytest.mark.asyncio


async def test_session_status(client, fake_app):
    result = await client.call_tool("cap_session_status", {})
    assert result.data == {"logged_in": True, "account_id": "TEST123"}


async def test_session_login_adds_active_account(client, fake_app):
    result = await client.call_tool("cap_session_login", {"force": True})
    fake_app.session.login.assert_awaited_once_with(force=True, account_id=None)
    assert result.data["active_account_id"] == "TEST123"


async def test_session_logout(client, fake_app):
    result = await client.call_tool("cap_session_logout", {})
    fake_app.session.logout.assert_awaited_once()
    assert result.data == {"message": "Logged out successfully"}


async def test_session_switch_account(client, fake_app):
    fake_app.session.switch_account = __import__("unittest").mock.AsyncMock(
        return_value={"trailingStopsEnabled": False}
    )
    result = await client.call_tool("cap_session_switch_account", {"account_id": "ACC2"})
    fake_app.session.switch_account.assert_awaited_once_with("ACC2")
    assert result.data["active_account_id"] == "TEST123"
