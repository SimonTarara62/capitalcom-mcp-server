# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.2] - 2026-06-15

### Changed
- Clarified the **unofficial** status on disclaimer-less surfaces: the PyPI
  summary and MCP Registry description now lead with "Unofficial", and the
  FastMCP server display name is "Capital.com MCP (unofficial)". No code or
  tool behavior changes. (This project is not affiliated with Capital.com.)

## [0.3.1] - 2026-06-15

### Fixed
- MCP Registry server name now uses the correct GitHub namespace casing
  (`io.github.SimonTarara62/...`) so OIDC-authenticated registry publishing
  succeeds. The README ownership marker and registry badge were aligned to match.

## [0.3.0] - 2026-06-15

### Added
- Official MCP Registry manifest (`server.json`) and automated registry publishing.
- Full README reference for all 42 tools, 4 resources, and 7 prompts.
- Community-health files: CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, issue/PR
  templates, Dependabot config.
- PyPI version/Python/downloads and MCP Registry badges.

### Changed
- Built-in prompts now carry a consistent footer and explicit two-phase safety
  reminders.
- Enriched PyPI metadata (classifiers, keywords, project URLs).

## [0.2.0] - 2026-06-14

### Changed
- Re-platformed onto the published `capitalcom-cli` SDK; removed the vendored
  broker engine.
- Relicensed MIT → Apache-2.0.

### Added
- `capitalcom-mcp` CLI (`run` / `doctor` / `init`), streamable-HTTP transport,
  full end-to-end test suite driving every tool against the demo API, and PyPI
  Trusted Publishing.

[Unreleased]: https://github.com/SimonTarara62/capitalcom-mcp-server/compare/v0.3.2...HEAD
[0.3.2]: https://github.com/SimonTarara62/capitalcom-mcp-server/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/SimonTarara62/capitalcom-mcp-server/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/SimonTarara62/capitalcom-mcp-server/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/SimonTarara62/capitalcom-mcp-server/releases/tag/v0.2.0
