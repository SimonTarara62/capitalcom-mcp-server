"""Basic sanity tests to verify test infrastructure."""

import pytest


def test_imports():
    """Test that capital_mcp modules can be imported."""
    import capital_mcp
    from capital_mcp import server
    from capital_mcp import config
    from capital_mcp import session
    from capital_mcp import risk
    from capital_mcp import capital_client
    from capital_mcp import models
    from capital_mcp import errors

    assert capital_mcp is not None
    assert server is not None
    assert config is not None
    assert session is not None
    assert risk is not None
    assert capital_client is not None
    assert models is not None
    assert errors is not None


def test_errors_defined():
    """Test that custom errors are defined."""
    from capital_mcp.errors import (
        TradingDisabledError,
        EpicNotAllowedError,
        PreviewError,
        ConfirmRequiredError,
        DryRunError,
        RiskLimitError
    )

    assert TradingDisabledError is not None
    assert EpicNotAllowedError is not None
    assert PreviewError is not None
    assert ConfirmRequiredError is not None
    assert DryRunError is not None
    assert RiskLimitError is not None


@pytest.mark.asyncio
async def test_mcp_server_instance():
    """Test that MCP server instance exists."""
    from capital_mcp.server import mcp

    assert mcp is not None
    assert hasattr(mcp, 'get_tools')
    assert hasattr(mcp, 'get_resources')
    assert hasattr(mcp, 'get_prompts')
