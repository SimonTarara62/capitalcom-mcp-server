# Minimal image that runs the (unofficial) Capital.com MCP server over stdio.
#
# Credentials are provided at RUNTIME (env vars, or a mounted file referenced by
# CAP_ENV_FILE). The server intentionally starts WITHOUT credentials so MCP
# directories (e.g. Glama) can introspect it (initialize + tools/list). Broker
# calls require CAP_API_KEY / CAP_IDENTIFIER / CAP_API_PASSWORD at call time.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install from source so the image always matches this repo (readme is required
# by pyproject's `readme = "README.md"`).
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY capital_mcp ./capital_mcp
RUN pip install .

# Default to stdio (what MCP clients and Glama introspection use). For remote/
# HTTP hosting, override: `docker run ... capitalcom-mcp run --transport http
# --host 0.0.0.0 --port 8000` and publish the port.
ENTRYPOINT ["capitalcom-mcp"]
CMD ["run", "--transport", "stdio"]
