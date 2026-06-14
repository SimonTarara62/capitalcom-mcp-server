"""Offline integrity test: every registered MCP tool must have an e2e test.

Runs in the normal (non-e2e) suite — no network, no credentials. Lists tools from
the server registry directly (mcp.list_tools) so it does NOT build a real app.
"""

import ast
import asyncio
from pathlib import Path

from tests.e2e.coverage import E2E_COVERAGE, OPTIONAL

E2E_DIR = Path(__file__).parent / "e2e"


def _registered_tool_names() -> set[str]:
    from capital_mcp.server import mcp

    async def _list():
        return {t.name for t in await mcp.list_tools()}

    return asyncio.run(_list())


def _funcs_in(filename: str) -> set[str]:
    tree = ast.parse((E2E_DIR / filename).read_text())
    return {
        n.name
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_every_tool_has_an_e2e_entry():
    registered = _registered_tool_names()
    required = set(E2E_COVERAGE)
    optional = set(OPTIONAL)
    missing_from_registry = required - registered
    uncovered = registered - required - optional
    assert not missing_from_registry, f"registry names not registered: {missing_from_registry}"
    assert not uncovered, f"registered tools with no e2e entry: {uncovered}"


def test_referenced_e2e_tests_exist():
    registered = _registered_tool_names()
    mapping = dict(E2E_COVERAGE)
    for name, node in OPTIONAL.items():
        if name in registered:
            mapping[name] = node
    for tool, node in mapping.items():
        filename, func = node.split("::")
        assert (E2E_DIR / filename).exists(), f"{tool}: missing e2e file {filename}"
        assert func in _funcs_in(filename), f"{tool}: missing e2e test {func} in {filename}"
