#!/usr/bin/env python3
"""Canonical trace representation — the parse layer every operator consumes (T3).

One deterministic, zero-LLM shape for "what happened in this run", built from any
of the evidence forms the harness collects:

  - ATIF trajectory.json (harbor cross-harness behaviour record)
  - tau2-style message lists (assistant/user/tool with tool_calls)
  - trajectory_judge step records ({index, thought, call, observation})

    Trace
      .calls          [Call(step, name, args, pointer)]
      .observations   [Obs(step, text, pointer)]
      .user_texts     [(step, text)]        # what the user supplied
      .agent_texts    [(step, text)]        # what the agent said (incl. thoughts)
      .final_text     str                   # the final answer / last agent message

Pointers are stable strings ("steps[3].call", "messages[7]") — every operator
finding cites one, which is the auditability contract: a verdict you can walk
back to the exact evidence line. stdlib only; same input -> byte-identical parse.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass
class Call:
    step: int
    name: str
    args: dict
    pointer: str
    call_id: str | None = None


@dataclass
class Obs:
    step: int
    text: str
    pointer: str
    source_call_id: str | None = None


@dataclass
class Trace:
    calls: list = field(default_factory=list)
    observations: list = field(default_factory=list)
    user_texts: list = field(default_factory=list)
    agent_texts: list = field(default_factory=list)
    final_text: str = ""

    def grounding_corpus(self, upto_step: int | None = None) -> str:
        """everything the agent could legitimately cite: user input + observations
        (optionally only before a given step, for per-step operators)."""
        parts = [t for s, t in self.user_texts
                 if upto_step is None or s < upto_step]
        parts += [o.text for o in self.observations
                  if upto_step is None or o.step < upto_step]
        return "\n".join(parts)


def _jtext(x) -> str:
    """stable text form of any JSON-ish value (for containment checks)."""
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def _args(value) -> dict:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return {"_raw": value}
    return value if isinstance(value, dict) else ({"_raw": value} if value else {})


def _content_text(value) -> str:
    """ATIF v1.6+ text parts; do not invent text for image/audio references."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(str(part["text"]) for part in value
                         if isinstance(part, dict) and isinstance(part.get("text"), str))
    return "" if value is None else _jtext(value)


def observation_for_call(t: Trace, call: Call) -> Obs | None:
    """Join by call identity, never by message position for identified calls.

    A same-step fallback supports old hand-built Trace objects only when the step
    contains exactly one unambiguous call and the observation has no call id.
    """
    if call.call_id is not None:
        matches = [o for o in t.observations if o.source_call_id == call.call_id]
    elif sum(c.step == call.step for c in t.calls) == 1:
        matches = [o for o in t.observations
                   if o.step == call.step and o.source_call_id is None]
    else:
        matches = []
    if not matches:
        return None
    return Obs(matches[0].step, "\n".join(o.text for o in matches),
               matches[0].pointer, call.call_id)


def from_steps(steps: list[dict], final_answer: str = "",
               goal: str = "") -> Trace:
    """trajectory_judge shape: [{index, thought, call, observation}]."""
    t = Trace(final_text=str(final_answer or ""))
    if goal:
        t.user_texts.append((-1, str(goal)))
    for pos, s in enumerate(steps):
        i = int(s.get("index", pos))
        if s.get("thought"):
            t.agent_texts.append((i, str(s["thought"])))
        c = s.get("call")
        if c:
            name = str(c.get("name") or c.get("tool") or "")
            args = None
            for k in ("arguments", "args", "input", "params"):
                if isinstance(c.get(k), dict):
                    args = c[k]
                    break
            if args is None:
                args = {k: v for k, v in c.items() if k not in ("name", "tool")}
            call_id = str(c.get("tool_call_id") or c.get("id") or f"steps[{pos}].call")
            t.calls.append(Call(i, name, args or {}, f"steps[{pos}].call", call_id))
        o = s.get("observation")
        if o is not None:
            t.observations.append(Obs(i, _jtext(o), f"steps[{pos}].observation",
                                      call_id if c else None))
    return t


def from_messages(messages: list[dict]) -> Trace:
    """tau2-style message list: assistant(content, tool_calls)/user/tool."""
    t = Trace()
    last_agent = ""
    for i, m in enumerate(messages):
        role = m.get("role")
        content = m.get("content")
        if role == "user" and content:
            t.user_texts.append((i, str(content)))
        elif role == "assistant":
            if content:
                t.agent_texts.append((i, str(content)))
                last_agent = str(content)
            for j, tc in enumerate(m.get("tool_calls") or []):
                function = tc.get("function") or tc
                cid = tc.get("id") or tc.get("tool_call_id")
                t.calls.append(Call(i, str(function.get("name") or ""),
                                    _args(function.get("arguments")),
                                    f"messages[{i}].tool_calls[{j}]",
                                    str(cid) if cid is not None else None))
        elif role == "tool" and content is not None:
            cid = m.get("tool_call_id") or m.get("id")
            t.observations.append(Obs(i, _jtext(content), f"messages[{i}]",
                                      str(cid) if cid is not None else None))
    t.final_text = last_agent
    return t


def from_atif(trajectory: dict) -> Trace:
    """Harbor ATIF: message, function_name, observation.results/source_call_id.

    Legacy content/name/tool_result events remain supported. Step position controls
    time; tool_call_id controls result association, including parallel calls.
    """
    if not isinstance(trajectory, dict):
        raise ValueError("ATIF trajectory must be an object")
    t = Trace()
    steps = trajectory.get("steps") or trajectory.get("events") or []
    if not isinstance(steps, list):
        raise ValueError("ATIF steps must be an array")
    for i, s in enumerate(steps):
        if not isinstance(s, dict):
            raise ValueError(f"ATIF steps[{i}] must be an object")
        kind = s.get("type") or s.get("kind") or ""
        role = s.get("role") or s.get("source") or ""
        content = _content_text(s.get("message", s.get("content", s.get("text"))))
        if kind in ("tool_use", "tool_call") or s.get("tool_calls"):
            for j, tc in enumerate(s.get("tool_calls") or [s]):
                name = str(tc.get("function_name") or tc.get("name") or tc.get("tool") or "")
                cid = tc.get("tool_call_id") or tc.get("id")
                pointer = f"steps[{i}].tool_calls[{j}]" if s.get("tool_calls") else f"steps[{i}]"
                t.calls.append(Call(i, name, _args(tc.get("arguments", tc.get("input"))),
                                    pointer, str(cid) if cid is not None else None))
        observation = s.get("observation")
        if isinstance(observation, dict):
            for j, result in enumerate(observation.get("results") or []):
                cid = result.get("source_call_id")
                t.observations.append(Obs(i, _content_text(result.get("content")),
                                          f"steps[{i}].observation.results[{j}]",
                                          str(cid) if cid is not None else None))
        if kind in ("tool_result", "observation"):
            cid = s.get("source_call_id") or s.get("tool_call_id")
            t.observations.append(Obs(i, content, f"steps[{i}]",
                                      str(cid) if cid is not None else None))
        elif role == "user" and content:
            t.user_texts.append((i, str(content)))
        elif role in ("agent", "assistant") and content:
            t.agent_texts.append((i, str(content)))
            t.final_text = str(content)
    return t


_SENT_SPLIT = re.compile(r"(?<=[.!?。!?])\s+")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text or "") if s.strip()]


def _selftest():
    steps = [{"index": 0, "thought": "look up",
              "call": {"name": "get_user", "arguments": {"id": "u1"}},
              "observation": {"name": "Ann", "balance": 50}},
             {"index": 1, "thought": "done", "call": None, "observation": None}]
    t = from_steps(steps, final_answer="Balance is 50.", goal="check balance")
    assert len(t.calls) == 1 and t.calls[0].pointer == "steps[0].call"
    assert "balance" in t.grounding_corpus().lower()
    msgs = [{"role": "user", "content": "hi"},
            {"role": "assistant", "content": "ok",
             "tool_calls": [{"name": "f", "arguments": '{"a": 1}'}]},
            {"role": "tool", "content": '{"r": 2}'}]
    m = from_messages(msgs)
    assert m.calls[0].args == {"a": 1} and m.observations[0].text == '{"r": 2}'
    assert sentences("A did. B will! C?") == ["A did.", "B will!", "C?"]
    print("trace selftest OK")


if __name__ == "__main__":
    _selftest()
