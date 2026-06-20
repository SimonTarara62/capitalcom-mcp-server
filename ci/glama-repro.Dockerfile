# Faithful replica of Glama's auto-generated build image for capitalcom-mcp-server.
# Purpose: reproduce Glama's sandbox in CI to find the working Build step + CMD.
# NOTE: kept faithful on purpose (incl. `uv python clean`, python-only symlink)
# so any Glama-template bug we cannot edit via the form is surfaced here.
FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive \
    GLAMA_VERSION="1.0.0" \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git \
    && curl -fsSL https://deb.nodesource.com/setup_26.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g mcp-proxy@6.4.3 pnpm@10.14.0 \
    && node --version \
    && curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin/ sh \
    && uv python install 3.12 --default --preview \
    && ln -s "$(uv python find)" /usr/local/bin/python \
    && python --version \
    && uv python clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app
ENV PATH="/app/node_modules/.bin:$PATH"

# The Build step Glama runs. Use `uv pip install --system` because Glama's image
# has `uv` but its uv-managed python may ship WITHOUT pip, so `pip` / `python -m
# pip` can fail; `uv pip install --system` installs into the default python reliably.
RUN uv pip install --system capitalcom-mcp==0.3.4

# No ENTRYPOINT/CMD: the CI probes exec the candidate commands explicitly.
