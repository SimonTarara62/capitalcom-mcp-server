"""Shared fixtures: a fake CapitalComApp and an in-memory FastMCP client.

Tools are exercised through FastMCP's in-memory transport with
capital_mcp.context.get_app monkeypatched to a fake whose services are
AsyncMocks — no network, no credentials.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import capital_mcp.context as ctx


@pytest.fixture
def fake_app():
    """A fake CapitalComApp with AsyncMock services and a sync session.get_status()."""
    session = MagicMock()
    session.ensure_logged_in = AsyncMock(return_value=None)
    session.login = AsyncMock(return_value={"accountId": "TEST123"})
    session.ping = AsyncMock(return_value={"status": "OK"})
    session.logout = AsyncMock(return_value=None)
    session.get_status = MagicMock(
        return_value=SimpleNamespace(
            model_dump=lambda: {"logged_in": True, "account_id": "TEST123"},
            account_id="TEST123",
        )
    )

    app = SimpleNamespace(
        session=session,
        markets=AsyncMock(),
        accounts=AsyncMock(),
        watchlists=AsyncMock(),
        trading=AsyncMock(),
        stream=MagicMock(),  # iterators set per-test
        config=SimpleNamespace(cap_env=SimpleNamespace(value="demo"), cap_ws_enabled=False),
        risk_policy=SimpleNamespace(
            allow_trading=False,
            allowed_epics=["GOLD", "SILVER"],
            max_position_size=1.0,
            max_working_order_size=1.0,
            max_open_positions=3,
            max_orders_per_day=20,
            require_explicit_confirm=True,
            dry_run=False,
        ),
    )
    return app


@pytest.fixture
def patch_app(monkeypatch, fake_app):
    """Patch context.get_app (and the server's imported reference) to the fake."""
    # Clear any process-global app left behind by other tests so the lifespan's
    # shutdown does not try to __aexit__ a stale (non-async-context) instance.
    ctx.reset_app()
    monkeypatch.setattr(ctx, "get_app", lambda: fake_app)
    import capital_mcp.server as server
    monkeypatch.setattr(server, "get_app", lambda: fake_app)
    return fake_app


@pytest.fixture
async def client(patch_app):
    """An in-memory FastMCP client bound to the server, with get_app patched."""
    from fastmcp import Client

    from capital_mcp.server import mcp

    async with Client(mcp) as c:
        yield c
