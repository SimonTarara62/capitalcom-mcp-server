"""E2E fixtures. Tests drive the REAL demo API through the MCP server.

Run: CAP_MCP_E2E=1 pytest tests/e2e -m e2e -v

Reads the repo-root .env (real demo credentials). The read + safe-mutation tools
are here; trade mutations + streaming live in test_e2e_trading.py /
test_e2e_stream.py and REQUIRE a trading+WS-enabled demo .env (they fail loudly
if it isn't). SECURITY: never reads or prints .env contents — only sets
CAP_ENV_FILE to its path.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ENV_FILE = REPO / ".env"


@pytest.fixture(autouse=True)
def _use_real_env(monkeypatch):
    """Point the SDK config at the repo-root .env and reset SDK + app singletons."""
    if not ENV_FILE.exists():
        pytest.skip("no repo-root .env with demo credentials")
    monkeypatch.setenv("CAP_ENV_FILE", str(ENV_FILE))
    from capital_cli.core.config import reset_config

    import capital_mcp.context as ctx

    reset_config()
    ctx.reset_app()
    yield
    reset_config()
    ctx.reset_app()


@pytest.fixture
async def mcp_client():
    """In-memory FastMCP client bound to the REAL server (get_app NOT patched)."""
    from fastmcp import Client

    from capital_mcp.server import mcp

    async with Client(mcp) as c:
        yield c
