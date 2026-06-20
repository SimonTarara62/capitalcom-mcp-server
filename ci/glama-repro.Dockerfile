# Faithful replica of Glama's CURRENT auto-generated build image (2026-06-20:
# Glama replaced the broken `uv python clean` with `apt-get clean`). Now tests the
# build-step fix `uv pip install --system` — the form's `python -m pip install`
# fails with externally-managed-environment on the uv-managed python.
FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive \
    GLAMA_VERSION="1.0.0" \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g mcp-proxy@6.4.3 pnpm@10.14.0 \
    && node --version \
    && curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR="/usr/local/bin" sh \
    && uv python install 3.12 --default --preview \
    && ln -s "$(uv python find)" /usr/local/bin/python \
    && python --version \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app
ENV PATH="/app/node_modules/.bin:$PATH"

# The fix: install into a fresh uv venv (NOT externally-managed). `--system`
# resolved to Debian's locked /usr python; a venv sidesteps PEP 668 entirely.
RUN uv venv /opt/capvenv \
    && uv pip install --python /opt/capvenv/bin/python capitalcom-mcp==0.3.4

# No ENTRYPOINT/CMD: the CI probes exec the candidate commands explicitly.
