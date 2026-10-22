
# --- veritas judge-arm CLI install (appended by tb4 adapter; local builds have egress)
USER root
RUN (command -v curl >/dev/null || (apt-get update -qq && apt-get install -y -qq curl ca-certificates >/dev/null)) \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - >/dev/null 2>&1 \
    && apt-get install -y -qq nodejs >/dev/null \
    && npm i -g opencode-ai@1.18.3 @openai/codex@0.154.0 >/dev/null 2>&1 \
    && opencode --version && codex --version
ENV HOME=/root OPENCODE_DISABLE_AUTOUPDATE=1 OPENCODE_DISABLE_LSP_DOWNLOAD=1
