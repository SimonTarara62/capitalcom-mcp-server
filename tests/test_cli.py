import os
import stat

from capital_mcp import cli


def test_build_parser_defaults():
    args = cli.build_parser().parse_args(["run"])
    assert args.command == "run"
    assert args.transport is None


def test_run_uses_env_transport(monkeypatch):
    monkeypatch.setenv("CAP_MCP_TRANSPORT", "http")
    monkeypatch.setenv("CAP_MCP_PORT", "9000")
    captured = {}

    def fake_run(**kwargs):
        captured.update(kwargs)

    import capital_mcp.server as server
    monkeypatch.setattr(server.mcp, "run", fake_run)
    cli.main(["run"])  # no flags -> env wins
    assert captured["transport"] == "http"
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 9000


def test_run_stdio_passes_only_transport(monkeypatch):
    captured = {}
    import capital_mcp.server as server
    monkeypatch.setattr(server.mcp, "run", lambda **k: captured.update(k))
    cli.main(["run", "--transport", "stdio"])
    assert captured == {"transport": "stdio"}


def test_init_writes_0600_env_file(tmp_path, monkeypatch):
    target = tmp_path / "cfg" / ".env"
    written = cli.write_env_file(
        target, env="demo", api_key="my-key", identifier="me@example.com", api_password="api-pass"
    )
    assert written == target
    content = target.read_text()
    assert "CAP_API_KEY=my-key" in content
    assert "CAP_ENV=demo" in content
    mode = stat.S_IMODE(os.stat(target).st_mode)
    assert mode == 0o600


def test_doctor_reports_missing(monkeypatch, capsys):
    from capital_cli.core.errors import ConfigMissingError

    def boom():
        raise ConfigMissingError("Missing CAP_API_KEY")

    monkeypatch.setattr(cli, "_load_config", boom)
    rc = cli.cmd_doctor(cli.build_parser().parse_args(["doctor"]))
    out = capsys.readouterr().out
    assert rc == 1
    assert "Missing" in out
