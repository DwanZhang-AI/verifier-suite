#!/usr/bin/env python3
"""Hermes judge agent: probe-skip install + custom-provider routing.

Not used by the one-click suite (VERITAS_HARNESS=hermes only).

Install: a pre-baked hermes is used when present; the stock adapter's github-raw
install pipe is the fallback.

Routing: the hermes CLI's base_url resolution chain is CLI-arg > startup override >
model config > OPENROUTER_BASE_URL; it never reads OPENAI_BASE_URL, so the stock
agent's env forwarding silently sends requests to the default host. The working
path is a named entry in config.yaml `custom_providers` (base_url + key_env)
selected via --provider. run() below replaces the stock provider resolution
wholesale with that wiring; the session layer passes the (possibly metered) base
URL via agent kwargs.
"""
from __future__ import annotations

import os
import shlex
from typing import override

import yaml

from harbor.agents.installed.hermes import Hermes
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

_DEFAULT_ENDPOINT = "https://model-endpoint.example/api/v3"


class JudgeHermes(Hermes):
    def __init__(self, *args, endpoint_base: str | None = None, **kwargs):
        self._endpoint_base = endpoint_base or _DEFAULT_ENDPOINT
        super().__init__(*args, **kwargs)

    @override
    def get_version_command(self) -> str | None:
        # hermes >=0.21 dropped the `version` subcommand harbor still probes with
        # (`--version` is the surviving flag); harbor's install tail `hermes version`
        # would otherwise hard-fail agent setup.
        return 'export PATH="/usr/local/bin:$HOME/.local/bin:$PATH"; hermes --version'

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        probe = await environment.exec(
            command=self.get_version_command(), timeout_sec=120)
        if probe.return_code == 0 and (probe.stdout or "").strip():
            self._version = probe.stdout.strip()
            return
        # harbor's install body verbatim EXCEPT the trailing validation, which
        # must use --version (see get_version_command).
        await self.ensure_system_dependencies(
            environment, ("curl", "git", "ripgrep", "xz"))
        await self.exec_as_agent(
            environment,
            command=(
                "set -euo pipefail; "
                "curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash -s -- --skip-setup && "
                'export PATH="/usr/local/bin:$HOME/.local/bin:$PATH" && '
                'export HERMES_HOME="${HERMES_HOME:-/tmp/hermes}" && '
                'mkdir -p "$HERMES_HOME" "$HERMES_HOME/sessions" "$HERMES_HOME/skills" "$HERMES_HOME/memories" && '
                "hermes --version"
            ),
        )

    def _endpoint_config_yaml(self, model: str) -> str:
        config = {
            "model": model,
            "provider": "endpoint",
            "toolsets": ["hermes-cli"],
            "agent": {"max_turns": 90},
            "memory": {"memory_enabled": False, "user_profile_enabled": False},
            "compression": {"enabled": True, "threshold": 0.85},
            "terminal": {"backend": "local", "timeout": 180},
            "delegation": {"max_iterations": 50},
            "checkpoints": {"enabled": False},
            "custom_providers": [{
                "name": "endpoint",
                "base_url": self._endpoint_base,
                "key_env": "MODEL_API_KEY",
                "api_mode": "chat_completions",
                "model": model,
            }],
        }
        return yaml.dump(config, default_flow_style=False)

    @override
    async def run(self, instruction: str, environment: BaseEnvironment,
                  context: AgentContext) -> None:
        # model_name arrives as "<anything>/<slug>"; only the slug matters: the
        # custom provider entry carries routing and credentials.
        model = self.model_name.split("/", 1)[-1]
        env = {
            "HERMES_HOME": "/tmp/hermes",
            "TERMINAL_ENV": "local",
            "MODEL_API_KEY": os.environ.get("MODEL_API_KEY", ""),
            "HARBOR_INSTRUCTION": instruction,
        }
        config_yaml = self._endpoint_config_yaml(model)
        await self.exec_as_agent(
            environment,
            command=("mkdir -p /tmp/hermes && "
                     f"cat > /tmp/hermes/config.yaml << 'EOF'\n{config_yaml}EOF"),
            env=env, timeout_sec=10)
        mcp_command = self._build_register_mcp_servers_command()
        if mcp_command:
            await self.exec_as_agent(environment, command=mcp_command, env=env,
                                     timeout_sec=10)
        run_cmd = (
            'export PATH="/usr/local/bin:$HOME/.local/bin:$PATH" && '
            'hermes --yolo chat -q "$HARBOR_INSTRUCTION" -Q '
            f"--model {shlex.quote(model)} --provider endpoint "
            "2>&1 | stdbuf -oL tee /logs/agent/hermes.txt"
        )
        try:
            await self.exec_as_agent(environment, command=run_cmd, env=env)
        finally:
            try:
                await self.exec_as_agent(
                    environment,
                    command=('export PATH="/usr/local/bin:$HOME/.local/bin:$PATH" && '
                             "hermes sessions export /logs/agent/hermes-session.jsonl "
                             "--source cli 2>/dev/null || true"),
                    env={"HERMES_HOME": "/tmp/hermes"}, timeout_sec=30)
            except Exception:
                pass
