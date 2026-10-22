#!/usr/bin/env python3
"""Minimal single-shot chat-completions call (stdlib urllib) for pipeline stages that
are a plain LLM call, not an agentic sandbox session (contract extraction). Not used by
the one-click suite. Self-contained: endpoint and key variable are the module constants
below."""
from __future__ import annotations

import json
import os
import urllib.request

ENDPOINT_URL = "https://model-endpoint.example/api/v3/chat/completions"


def chat(model: str, system: str, user: str, temperature: float = 0.2,
         timeout: int = 1800, max_tokens: int = 65536) -> dict:
    """-> {"text", "usage", "finish_reason"}.

    max_tokens defaults to the largest budget the endpoint will take: reasoning models
    spend thousands of completion tokens thinking before the deliverable, so a small cap
    silently truncates the artifact. If the endpoint rejects the cap, halve until
    accepted; a truncated reply is reported via finish_reason == "length", never
    hidden."""
    key = os.environ.get("MODEL_API_KEY", "")
    assert key, "MODEL_API_KEY not in env"
    mt = max_tokens
    while True:
        body = json.dumps({
            "model": model.split("/", 1)[-1],
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": temperature,
            "max_tokens": mt,
        }).encode()
        req = urllib.request.Request(ENDPOINT_URL, data=body, headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.load(r)
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:300]
            if e.code == 400 and "max_tokens" in detail and mt > 4096:
                mt //= 2
                continue
            raise RuntimeError(f"endpoint {e.code}: {detail}") from e
    ch = resp["choices"][0]
    return {"text": ch["message"]["content"], "usage": resp.get("usage", {}),
            "finish_reason": ch.get("finish_reason"), "max_tokens_used": mt}


def chat_json(model: str, system: str, user: str, required_keys: tuple = (),
              retries: int = 1, **kw) -> tuple[dict, dict]:
    """chat() + parse the reply as a JSON object (fenced or bare); one reprompt on
    invalid JSON / missing keys. -> (obj, usage_total). Raises on final failure."""
    usage_total = {"prompt_tokens": 0, "completion_tokens": 0}
    last_err = ""
    for attempt in range(retries + 1):
        u = user if not last_err else (
            user + f"\n\n上一次输出不是合法 JSON 或缺少必需字段({last_err});"
                   "重新输出:只输出一个 JSON 对象,不要任何其他文字。")
        r = chat(model, system, u, **kw)
        for k in ("prompt_tokens", "completion_tokens"):
            usage_total[k] += r["usage"].get(k, 0)
        txt = r["text"].strip()
        if txt.startswith("```"):
            txt = txt.split("```", 2)[1]
            txt = txt.split("\n", 1)[1] if txt.startswith(("json", "JSON")) else txt
        try:
            obj = json.loads(txt.strip())
            missing = [k for k in required_keys if k not in obj]
            if missing:
                last_err = f"missing {missing}"
                continue
            return obj, usage_total
        except json.JSONDecodeError as e:
            last_err = str(e)[:120]
    raise ValueError(f"chat_json failed after {retries + 1} attempts: {last_err}")


if __name__ == "__main__":
    obj, usage = chat_json("endpoint/model", "你是一个 JSON 输出器。",
                           '输出 {"ok": true, "n": 3}', required_keys=("ok",))
    assert obj.get("ok") is True, obj
    print("llm_call selftest OK", usage)
