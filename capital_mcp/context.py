"""Shared CapitalComApp lifecycle for the MCP server.

The capital_cli SDK uses process-global singletons ("one app per process"),
which fits an MCP server (a single process). We hold one lazily-constructed
CapitalComApp. Construction does NOT log in — login happens lazily per tool via
app.session.ensure_logged_in(). The FastMCP lifespan closes the shared HTTP
client on shutdown.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from capital_cli.sdk import CapitalComApp

if TYPE_CHECKING:
    from fastmcp import FastMCP

_app: CapitalComApp | None = None


def get_app() -> CapitalComApp:
    """Return the process-wide CapitalComApp, building it on first use."""
    global _app
    if _app is None:
        _app = CapitalComApp()
    return _app


def reset_app() -> None:
    """Drop the cached app (tests / re-init)."""
    global _app
    _app = None


@asynccontextmanager
async def lifespan(_server: FastMCP):
    """FastMCP lifespan: lazily build the app, close its HTTP client on exit.

    We deliberately do NOT construct the app eagerly here. Construction calls
    CapitalComConfig.from_env(), which raises ConfigMissingError without CAP_*
    credentials — that would stop the server from starting and break
    credential-free introspection (initialize + tools/list) that MCP
    directories like Glama rely on. The app is built on the first tool call
    that needs the broker (every @mcp.tool() calls get_app() at call time).

    We also do NOT log out on shutdown so the cached session token can be
    reused by the next process (the SDK persists it to a 0600 state file).
    """
    try:
        yield
    finally:
        global _app
        if _app is not None:
            # CapitalComApp.__aexit__ closes the shared httpx client (no logout).
            await _app.__aexit__(None, None, None)
            _app = None
