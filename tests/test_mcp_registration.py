"""Tests for MCP tools, resources, and prompts registration."""

import pytest


@pytest.mark.asyncio
async def test_all_tools_registered():
    """Test that all MCP tools are registered."""
    from capital_mcp.server import mcp

    tools = await mcp.get_tools()
    tool_names = list(tools.keys())

    # Session tools (4)
    assert "cap_session_login" in tool_names
    assert "cap_session_logout" in tool_names
    assert "cap_session_status" in tool_names
    assert "cap_session_ping" in tool_names

    # Market data tools
    assert "cap_market_search" in tool_names
    assert "cap_market_get" in tool_names
    assert "cap_market_navigation_root" in tool_names
    assert "cap_market_navigation_node" in tool_names
    assert "cap_market_prices" in tool_names
    assert "cap_market_sentiment" in tool_names

    # Account tools
    assert "cap_account_list" in tool_names
    assert "cap_account_preferences_get" in tool_names
    assert "cap_account_preferences_set" in tool_names
    assert "cap_account_history_activity" in tool_names
    assert "cap_account_history_transactions" in tool_names
    assert "cap_account_demo_topup" in tool_names

    # Trading tools
    assert "cap_trade_positions_list" in tool_names
    assert "cap_trade_positions_get" in tool_names
    assert "cap_trade_orders_list" in tool_names
    assert "cap_trade_preview_position" in tool_names
    assert "cap_trade_execute_position" in tool_names
    assert "cap_trade_positions_close" in tool_names
    assert "cap_trade_orders_cancel" in tool_names
    assert "cap_trade_confirm_wait" in tool_names
    assert "cap_trade_preview_working_order" in tool_names
    assert "cap_trade_execute_working_order" in tool_names
    assert "cap_trade_confirm_get" in tool_names

    # Watchlist tools
    assert "cap_watchlists_list" in tool_names
    assert "cap_watchlists_get" in tool_names
    assert "cap_watchlists_create" in tool_names
    assert "cap_watchlists_delete" in tool_names
    assert "cap_watchlists_add_market" in tool_names
    assert "cap_watchlists_remove_market" in tool_names

    # Total should be 33+ tools
    assert len(tool_names) >= 33


@pytest.mark.asyncio
async def test_all_resources_registered():
    """Test that all MCP resources are registered."""
    from capital_mcp.server import mcp

    # Get static resources
    resources = await mcp.get_resources()
    # Get dynamic resources (templates)
    templates = await mcp.get_resource_templates()

    total = len(resources) + len(templates)

    # Should have 5 resources (4 static + 1 dynamic)
    assert total == 5

    # Check static resources
    assert "cap://status" in resources
    assert "cap://risk-policy" in resources
    assert "cap://allowed-epics" in resources
    assert "cap://watchlists" in resources

    # Check dynamic resource template
    assert "cap://market-cache/{epic}" in templates


@pytest.mark.asyncio
async def test_all_prompts_registered():
    """Test that all MCP prompts are registered."""
    from capital_mcp.server import mcp

    prompts = await mcp.get_prompts()
    prompt_names = list(prompts.keys())

    # Should have 4 prompts
    assert len(prompt_names) == 4

    assert "market_scan" in prompt_names
    assert "trade_proposal" in prompt_names
    assert "execute_trade" in prompt_names
    assert "position_review" in prompt_names


@pytest.mark.asyncio
async def test_tools_have_descriptions():
    """Test that all tools have descriptions."""
    from capital_mcp.server import mcp

    tools = await mcp.get_tools()

    for tool_name, tool in tools.items():
        assert tool.description is not None, f"{tool_name} missing description"
        assert len(tool.description) > 10, f"{tool_name} description too short"


@pytest.mark.asyncio
async def test_prompts_have_descriptions():
    """Test that all prompts have descriptions."""
    from capital_mcp.server import mcp

    prompts = await mcp.get_prompts()

    for prompt_name in prompts:
        prompt = await mcp.get_prompt(prompt_name)
        assert prompt.description is not None, f"{prompt_name} missing description"
        assert len(prompt.description) > 10, f"{prompt_name} description too short"
