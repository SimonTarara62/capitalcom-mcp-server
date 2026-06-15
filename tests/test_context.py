"""Tests for the shared CapitalComApp lifecycle."""

import os

from fastmcp import Client

import capital_mcp.context as ctx
from capital_mcp.server import mcp


def test_get_app_is_singleton(monkeypatch):
    """get_app() returns the same instance across calls and builds it lazily."""
    built = []

    class FakeApp:
        def __init__(self):
            built.append(1)

    monkeypatch.setattr(ctx, "CapitalComApp", FakeApp)
    ctx.reset_app()

    a = ctx.get_app()
    b = ctx.get_app()
    assert a is b
    assert len(built) == 1  # constructed exactly once


def test_reset_app_clears_singleton(monkeypatch):
    class FakeApp:
        pass

    monkeypatch.setattr(ctx, "CapitalComApp", FakeApp)
    ctx.reset_app()
    first = ctx.get_app()
    ctx.reset_app()
    second = ctx.get_app()
    assert first is not second


async def test_server_starts_and_lists_tools_without_credentials(monkeypatch):
    # Glama / MCP-directory introspection launches the server with no creds and
    # calls tools/list. That must succeed even though no CAP_* vars are set.
    for key in list(os.environ):
        if key.startswith("CAP_"):
            monkeypatch.delenv(key, raising=False)
    ctx.reset_app()
    async with Client(mcp) as client:          # runs the REAL lifespan
        tools = await client.list_tools()
    assert len(tools) >= 40
    assert ctx._app is None                     # never constructed during introspection
