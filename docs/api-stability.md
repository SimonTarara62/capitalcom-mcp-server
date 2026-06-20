# API stability

> ⚠️ **Unofficial & educational.** This is a community project, not affiliated
> with Capital.com. This page is a promise about how the **MCP tool surface**
> evolves so you can build on it safely.

This server exposes a fixed surface: **42 tools**, **4 resources**, and **7
guided prompts**. That surface is the contract.

## What "stable" guarantees

Within a given **major** version (e.g. all of `1.x`):

- **Tool names do not change** and are not removed.
- **Tool semantics do not silently change** — what a tool does stays what it did.
- **Existing parameters** keep their name, type, and meaning. Defaults are not
  changed in a way that alters behavior.
- **Resource URIs and prompt names** are likewise stable.

Allowed **without** a major bump (additive, backward-compatible):

- Adding a **new** tool, resource, or prompt.
- Adding a **new optional** parameter (with a default) to an existing tool.

Requires a **major** bump:

- Renaming or removing a tool/resource/prompt, renaming a parameter, or
  changing a parameter's type or a default's behavior. Such a change ships with
  a **deprecation alias** where feasible (the old name keeps working for one
  major and emits a deprecation note) and is always recorded in
  [CHANGELOG.md](../CHANGELOG.md).

## How it is enforced

The surface is locked by an automated snapshot
(`tests/snapshots/api_surface.json`, checked by
`tests/test_api_surface_snapshot.py`) that runs in the offline test suite. Any
accidental change to a tool schema, resource URI, or prompt argument **fails
CI** until either reverted or explicitly re-frozen with a CHANGELOG entry.

## The one naming exception

Every tool is prefixed `cap_` **except** `search` and `fetch`. Those two
implement the ChatGPT Deep Research connector contract, which requires those
exact names; they are intentionally unprefixed and read-only.

## Pinning

Stability is a promise about *major* versions. To pin against *any* change at
all (including additive ones), pin the exact package version — see the README's
"Pinning for production / real-money use".
