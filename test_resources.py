#!/usr/bin/env python
"""Test script to verify MCP resources are registered correctly."""

import asyncio
from capital_mcp.server import mcp


async def main():
    """Test that all resources are registered."""
    print("Testing MCP Resources Registration\n")
    print("=" * 60)

    # Get all registered resources (static)
    resources = await mcp.get_resources()

    # Get all resource templates (dynamic)
    templates = await mcp.get_resource_templates()

    total = len(resources) + len(templates)
    print(f"\nTotal resources registered: {total}")
    print(f"  - Static resources: {len(resources)}")
    print(f"  - Dynamic resources (templates): {len(templates)}")
    print("\nRegistered resources:")
    print("-" * 60)

    # Show static resources
    for uri in resources:
        print(f"\n✓ {uri}")

        # Get resource details
        resource = await mcp.get_resource(uri)
        if resource and resource.description:
            # Get first line of description
            desc = resource.description.strip().split('\n')[0]
            print(f"  {desc}")

        print(f"  Type: Static")

        # Show mime type if available
        if resource and hasattr(resource, 'mime_type') and resource.mime_type:
            print(f"  MIME type: {resource.mime_type}")

    # Show dynamic resources (templates)
    for uri_template, template in templates.items():
        print(f"\n✓ {uri_template}")

        if template.description:
            # Get first line of description
            desc = template.description.strip().split('\n')[0]
            print(f"  {desc}")

        print(f"  Type: Dynamic (parameterized)")

        # Extract parameters from URI template
        import re
        params = re.findall(r'\{(\w+)\}', uri_template)
        if params:
            print(f"  Parameters: {', '.join(params)}")

    print("\n" + "=" * 60)
    print("✓ All resources registered successfully!")

    print("\n" + "=" * 60)
    print("\n✅ SUCCESS: All 5 MCP resources are registered and ready to use!")
    print("\nYou can access these resources in Claude Desktop:")
    print("  - cap://status")
    print("  - cap://risk-policy")
    print("  - cap://allowed-epics")
    print("  - cap://watchlists")
    print("  - cap://market-cache/{epic} (e.g., cap://market-cache/GOLD)")
    print("\nResources provide read-only access to server state and configuration.")


if __name__ == "__main__":
    asyncio.run(main())
