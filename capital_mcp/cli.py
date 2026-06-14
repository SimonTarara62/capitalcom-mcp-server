"""Console entry point for the Capital.com MCP server.

Subcommands:
  run     — start the server (stdio default, or streamable-HTTP)
  doctor  — validate configuration + login WITHOUT printing secrets
  init    — interactive wizard that writes a 0600 credentials file

run flags fall back to env: CAP_MCP_TRANSPORT, CAP_MCP_HOST, CAP_MCP_PORT.
"""

from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_ENV_PATH = Path.home() / ".config" / "capital-mcp" / ".env"


# ---- small I/O seams (monkeypatched in tests) ----------------------------


def _prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or (default or "")


def _prompt_secret(label: str) -> str:
    return getpass.getpass(f"{label}: ").strip()


def _load_config():
    """Build the SDK config from env/.env/_CMD (raises on missing creds)."""
    from capital_cli.sdk import CapitalComConfig

    return CapitalComConfig.from_env()


# ---- run -----------------------------------------------------------------


def cmd_run(args: argparse.Namespace) -> int:
    from capital_mcp.server import mcp

    transport = args.transport or os.environ.get("CAP_MCP_TRANSPORT") or "stdio"
    if transport == "stdio":
        mcp.run(transport="stdio")
        return 0
    host = args.host or os.environ.get("CAP_MCP_HOST") or DEFAULT_HOST
    port = int(args.port or os.environ.get("CAP_MCP_PORT") or DEFAULT_PORT)
    mcp.run(transport="http", host=host, port=port)
    return 0


# ---- doctor --------------------------------------------------------------


def _redact(value: str | None) -> str:
    if not value:
        return "(unset)"
    return value[:2] + "***" if len(value) > 2 else "***"


def cmd_doctor(args: argparse.Namespace) -> int:
    try:
        cfg = _load_config()
    except Exception as exc:  # noqa: BLE001 — report any config failure cleanly
        print(f"x Configuration error: {exc}")
        return 1
    print("Configuration loaded")
    print(f"  CAP_ENV          = {cfg.cap_env.value}")
    print(f"  CAP_API_KEY      = {_redact(cfg.cap_api_key)}")
    print(f"  CAP_IDENTIFIER   = {_redact(cfg.cap_identifier)}")
    print(f"  CAP_ALLOW_TRADING= {cfg.cap_allow_trading}")
    print(f"  CAP_ALLOWED_EPICS= {cfg.cap_allowed_epics or '(none)'}")
    print(f"  base_url         = {cfg.base_url}")
    return 0


# ---- init ----------------------------------------------------------------


def write_env_file(
    path: Path, *, env: str, api_key: str, identifier: str, api_password: str
) -> Path:
    """Write a 0600 .env with the four core settings; create parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        f"CAP_ENV={env}\n"
        f"CAP_API_KEY={api_key}\n"
        f"CAP_IDENTIFIER={identifier}\n"
        f"CAP_API_PASSWORD={api_password}\n"
        "CAP_ALLOW_TRADING=false\n"
        "CAP_ALLOWED_EPICS=\n"
    )
    path.write_text(body)
    path.chmod(0o600)
    return path


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.path) if args.path else DEFAULT_ENV_PATH
    print("Capital.com MCP - credential setup")
    print("Get your API key at: Settings > API integrations (use a DEMO key first).\n")
    env = _prompt("Environment (demo/live)", "demo")
    api_key = _prompt_secret("CAP_API_KEY")
    identifier = _prompt("CAP_IDENTIFIER (login email)")
    api_password = _prompt_secret("CAP_API_PASSWORD (API key custom password)")
    written = write_env_file(
        target, env=env, api_key=api_key, identifier=identifier, api_password=api_password
    )
    print(f"\nWrote {written} (mode 0600)")
    print("\nAdd this to your MCP client config (no secrets in the client file):\n")
    print(
        '  "capitalcom": {\n'
        '    "command": "uvx",\n'
        '    "args": ["capitalcom-mcp"],\n'
        f'    "env": {{ "CAP_ENV_FILE": "{written}" }}\n'
        "  }"
    )
    return 0


# ---- parser / main -------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="capitalcom-mcp", description="Capital.com MCP server")
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="start the server")
    p_run.add_argument("--transport", choices=["stdio", "http"], default=None)
    p_run.add_argument("--host", default=None)
    p_run.add_argument("--port", default=None)
    p_run.set_defaults(func=cmd_run)

    p_doctor = sub.add_parser("doctor", help="validate config + credentials")
    p_doctor.set_defaults(func=cmd_doctor)

    p_init = sub.add_parser("init", help="interactive credential setup")
    p_init.add_argument("--path", default=None, help="env-file path (default ~/.config/capital-mcp/.env)")
    p_init.set_defaults(func=cmd_init)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        # Bare `capitalcom-mcp` -> run with stdio so client launchers work.
        args = parser.parse_args(["run"])
    return args.func(args) or 0
