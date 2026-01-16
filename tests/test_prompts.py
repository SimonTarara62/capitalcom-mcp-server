"""Tests for MCP prompts."""

import pytest


@pytest.mark.asyncio
async def test_prompts_registered():
    """Test that all prompts are registered."""
    from capital_mcp.server import mcp

    prompts = await mcp.get_prompts()

    # Should have 4 prompts
    assert len(prompts) == 4

    # Check prompt names
    prompt_names = list(prompts.keys())
    assert "market_scan" in prompt_names
    assert "trade_proposal" in prompt_names
    assert "execute_trade" in prompt_names
    assert "position_review" in prompt_names


@pytest.mark.asyncio
async def test_market_scan_prompt():
    """Test market_scan prompt details."""
    from capital_mcp.server import mcp

    prompt = await mcp.get_prompt("market_scan")

    assert prompt is not None
    assert prompt.name == "market_scan"
    assert "scan" in prompt.description.lower() or "market" in prompt.description.lower()

    # Check arguments exist
    assert prompt.arguments is not None
    arg_names = [arg.name for arg in prompt.arguments]
    # Verify at least one argument exists
    assert len(arg_names) > 0


@pytest.mark.asyncio
async def test_trade_proposal_prompt():
    """Test trade_proposal prompt details."""
    from capital_mcp.server import mcp

    prompt = await mcp.get_prompt("trade_proposal")

    assert prompt is not None
    assert prompt.name == "trade_proposal"
    assert "trade" in prompt.description.lower() or "proposal" in prompt.description.lower()

    # Check arguments
    assert prompt.arguments is not None
    arg_names = [arg.name for arg in prompt.arguments]
    assert "epic" in arg_names


@pytest.mark.asyncio
async def test_execute_trade_prompt():
    """Test execute_trade prompt details."""
    from capital_mcp.server import mcp

    prompt = await mcp.get_prompt("execute_trade")

    assert prompt is not None
    assert prompt.name == "execute_trade"
    assert "execute" in prompt.description.lower() or "trade" in prompt.description.lower()

    # Check arguments exist
    assert prompt.arguments is not None
    arg_names = [arg.name for arg in prompt.arguments]
    # Verify at least one argument exists
    assert len(arg_names) > 0


@pytest.mark.asyncio
async def test_position_review_prompt():
    """Test position_review prompt details."""
    from capital_mcp.server import mcp

    prompt = await mcp.get_prompt("position_review")

    assert prompt is not None
    assert prompt.name == "position_review"
    assert "position" in prompt.description.lower() or "review" in prompt.description.lower()

    # Should have no required arguments (reviews all positions)
    if prompt.arguments:
        required_args = [arg for arg in prompt.arguments if arg.required]
        assert len(required_args) == 0
