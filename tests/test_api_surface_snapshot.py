"""Freeze test: the public MCP surface (tool schemas, resources, prompts).

The e2e coverage registry already locks the *set* of tool names; this test
additionally locks every tool's input schema, all resource URIs (static +
templated), and every prompt's argument list. Any drift fails the offline
suite. Regenerate intentionally with: `UPDATE_SNAPSHOT=1 pytest
tests/test_api_surface_snapshot.py` (or `make snapshot`).
"""

import json
import os
import pathlib

SNAPSHOT = pathlib.Path(__file__).parent / "snapshots" / "api_surface.json"


async def build_surface(client) -> dict:
    """Capture the live MCP surface as a JSON-serializable dict."""
    tools = await client.list_tools()
    resources = await client.list_resources()
    templates = await client.list_resource_templates()
    prompts = await client.list_prompts()
    return {
        "tools": {t.name: t.inputSchema for t in sorted(tools, key=lambda x: x.name)},
        "resources": sorted(str(r.uri) for r in resources),
        "resource_templates": sorted(t.uriTemplate for t in templates),
        "prompts": {
            p.name: sorted(
                (
                    {"name": a.name, "required": bool(getattr(a, "required", False))}
                    for a in (p.arguments or [])
                ),
                key=lambda a: a["name"],
            )
            for p in sorted(prompts, key=lambda x: x.name)
        },
    }


async def test_surface_counts(client):
    surface = await build_surface(client)
    assert len(surface["tools"]) == 42
    assert len(surface["resources"]) == 3
    assert len(surface["resource_templates"]) == 1
    assert len(surface["prompts"]) == 7


async def test_api_surface_snapshot(client):
    live = await build_surface(client)
    if os.getenv("UPDATE_SNAPSHOT"):
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.write_text(json.dumps(live, indent=2, sort_keys=True) + "\n")
    assert SNAPSHOT.exists(), (
        "Missing golden snapshot. Generate it once with: "
        "UPDATE_SNAPSHOT=1 pytest tests/test_api_surface_snapshot.py"
    )
    expected = json.loads(SNAPSHOT.read_text())
    assert live == expected, (
        "MCP API surface changed vs the frozen contract. If this change is "
        "INTENTIONAL: regenerate with `make snapshot`, record it in "
        "CHANGELOG.md, and update docs/api-stability.md. If UNINTENTIONAL: "
        "revert the change — the surface is frozen."
    )
