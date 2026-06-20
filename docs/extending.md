# Extending the server

> ⚠️ **Unofficial & educational.** Community project, not affiliated with
> Capital.com. Use a **demo** account for all development.

This server is a thin [FastMCP](https://github.com/jlowin/fastmcp) layer over the
[`capitalcom-cli`](https://github.com/SimonTarara62/capitalcom-cli) SDK. If you
can call the SDK, you can add a tool.

## Architecture in one picture

```
MCP client ──▶ capital_mcp/server.py        @mcp.tool() async functions
                     │                       (the surface MCP clients see)
                     ▼
              capital_mcp/context.py         get_app() → one lazy CapitalComApp
                     │                       (no login until first call)
                     ▼
              capital_cli SDK facade         app.markets / accounts / trading /
                     │                       watchlists / stream / session
                     ▼
              capital_mcp/serialization.py   *_to_dict helpers → JSON-safe dicts
```

- **`server.py`** holds every tool, resource, and prompt. Tools never talk to
  the network directly; they call the SDK facade.
- **`context.py`** owns the single `CapitalComApp`. It is built lazily so the
  server can start and be introspected **without credentials**. Always go
  through `get_app()`.
- **`serialization.py`** converts SDK models into plain `dict[str, Any]` so
  every tool returns JSON-safe data.

## Add a read-only tool (the common case)

1. **Write the tool** in `capital_mcp/server.py`:

   ```python
   @mcp.tool()
   async def cap_market_example(epic: str) -> dict[str, Any]:
       """One-line description shown to MCP clients."""
       app = get_app()
       await app.session.ensure_logged_in()   # guard: all user-facing tools log in lazily
       result = await app.markets.example(epic)   # call the SDK facade
       return market_to_dict(result)              # serialize to a JSON-safe dict
   ```

   Real examples to copy from: `cap_market_get` (`server.py`), `cap_market_sentiment`,
   `cap_account_list`.

2. **Mutations require confirmation.** Any tool with a side effect takes
   `confirm: bool = False` and the SDK enforces the gate. See
   `cap_watchlists_create` (simple) and the two-phase trade flow
   `cap_trade_preview_position` → `cap_trade_execute_position` (the canonical
   "preview then confirm then execute" pattern).

3. **Write a unit test** in the matching `tests/test_tools_*.py` using the
   in-memory fixtures from `tests/conftest.py`:

   ```python
   async def test_market_example(client, fake_app):
       fake_app.markets.example.return_value = {"epic": "GOLD"}
       result = await client.call_tool("cap_market_example", {"epic": "GOLD"})
       fake_app.markets.example.assert_awaited_once_with("GOLD")
       assert result.data == {"epic": "GOLD"}
   ```

   - `client` is an in-memory FastMCP client (no network, no credentials).
   - `fake_app` is a `CapitalComApp` whose services are `AsyncMock`s — set
     `return_value`/`side_effect` and assert the call.
   - Both live in `tests/conftest.py`. The `client` fixture already depends on
     `patch_app`, which wires `fake_app` into the server — so just request both
     `client` and `fake_app` by name and pytest resolves the dependency chain.

4. **Register e2e coverage.** Add an e2e test under `tests/e2e/` and map the
   tool in `tests/e2e/coverage.py`. The offline test `tests/test_e2e_coverage.py`
   fails if any registered tool is missing from that registry.

5. **Re-freeze the surface.** Adding a tool is additive and expected:
   `make snapshot` regenerates the frozen API golden, and a CHANGELOG entry
   records it. (Renames/removals are breaking — see
   [API stability](api-stability.md).)

6. **Document it** in the README "What's inside" tables.

## Add a resource or a prompt

- **Resource:** `@mcp.resource("cap://your-uri")` (or templated,
  `cap://thing/{id}`) returning `dict[str, Any]`. See `cap://status` and the
  templated `cap://market-cache/{epic}` in `server.py`.
- **Prompt:** `@mcp.prompt()` returning a `str` of step-by-step guidance.
  Prompts orchestrate tools but never trade on their own. See `market_scan`
  and `trade_proposal`.

Both are part of the frozen surface — run `make snapshot` after adding one.

## Before you open a PR

```bash
make check        # ruff + mypy + pytest (offline; no network/credentials)
```

Update `CHANGELOG.md` under `## [Unreleased]`, keep the PR focused, and prefer
Conventional Commit messages (`feat:`, `fix:`, `docs:`). See
[CONTRIBUTING.md](../CONTRIBUTING.md) for the full checklist.
