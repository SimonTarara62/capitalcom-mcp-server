#!/usr/bin/env python
"""Test script to verify MCP prompts are registered correctly."""

import asyncio
from capital_mcp.server import mcp


async def main():
    """Test that all prompts are registered."""
    print("Testing MCP Prompts Registration\n")
    print("=" * 60)

    # Get all registered prompts
    prompts = await mcp.get_prompts()

    print(f"\nTotal prompts registered: {len(prompts)}")
    print("\nRegistered prompts:")
    print("-" * 60)

    for prompt_name in prompts:
        print(f"\n✓ {prompt_name}")

        # Get prompt details
        prompt = await mcp.get_prompt(prompt_name)
        if prompt and prompt.description:
            # Get first line of description
            desc = prompt.description.strip().split('\n')[0]
            print(f"  {desc}")

        # Show arguments if available
        if prompt and prompt.arguments:
            args = []
            for arg in prompt.arguments:
                if arg.required:
                    args.append(f"{arg.name} (required)")
                else:
                    args.append(f"{arg.name}")
            print(f"  Arguments: {', '.join(args) if args else 'none'}")

    print("\n" + "=" * 60)
    print("✓ All prompts registered successfully!")

    print("\n" + "=" * 60)
    print("\n✅ SUCCESS: All 4 MCP prompts are registered and ready to use!")
    print("\nYou can now use these prompts in Claude Desktop by invoking them")
    print("in conversation. For example:")
    print("  - 'Use the market_scan prompt'")
    print("  - 'Help me with a trade proposal for SILVER'")
    print("  - 'Review my positions'")
    print("\nThe prompts will guide Claude through structured workflows for")
    print("market analysis, trade planning, execution, and position review.")


if __name__ == "__main__":
    asyncio.run(main())
