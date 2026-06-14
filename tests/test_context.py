"""Tests for the shared CapitalComApp lifecycle."""

import capital_mcp.context as ctx


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
