"""Shared test fixtures for Capital.com MCP Server tests."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from capital_mcp.config import Config
from capital_mcp.models import SessionStatus


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv("CAPITAL_API_KEY", "test-api-key")
    monkeypatch.setenv("CAPITAL_PASSWORD", "test-password")
    monkeypatch.setenv("CAPITAL_IDENTIFIER", "test-identifier")
    monkeypatch.setenv("TRADING_ENABLED", "false")
    monkeypatch.setenv("ALLOWED_EPICS", "GOLD,SILVER")


@pytest.fixture
def config(mock_env):
    """Create test config."""
    return Config()


@pytest.fixture
def mock_session():
    """Mock session manager."""
    session = AsyncMock()
    session.ensure_logged_in = AsyncMock()
    session.get_status = MagicMock(return_value=SessionStatus(
        env="demo",
        base_url="https://demo-api-capital.backend-capital.com/api/v1",
        logged_in=True,
        account_id="TEST123",
        last_used_at=datetime.now().isoformat()
    ))
    return session


@pytest.fixture
def mock_client():
    """Mock Capital.com API client."""
    client = AsyncMock()
    response = AsyncMock()
    response.json = AsyncMock(return_value={"status": "ok"})
    response.status_code = 200
    client.get = AsyncMock(return_value=response)
    client.post = AsyncMock(return_value=response)
    client.put = AsyncMock(return_value=response)
    client.delete = AsyncMock(return_value=response)
    return client


@pytest.fixture
def mock_risk():
    """Mock risk engine."""
    risk = MagicMock()
    risk.get_allowed_epics = MagicMock(return_value={"GOLD", "SILVER"})
    risk.validate_execution_guards = MagicMock(return_value=None)
    risk.preview_position = AsyncMock()
    risk.preview_working_order = AsyncMock()
    risk.config = MagicMock()
    risk.config.TRADING_ENABLED = True
    return risk
