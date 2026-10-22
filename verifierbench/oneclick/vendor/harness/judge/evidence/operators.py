#!/usr/bin/env python3
"""Evidence operators, batch 1 — deterministic cross-stream reconciliation (T3/T6).

An operator consumes the canonical Trace and returns findings; every finding cites
an evidence pointer. Zero LLM, zero domain knowledge, stdlib only: the same input
always yields the same findings, and each verdict can be walked back to the exact
message/call/observation it rests on — the two properties direct reading cannot give.

  claim_gap  the agent's own text asserts a COMPLETED action whose object is
             grounded nowhere in the action stream or observations (said-not-done).
  cite_gap   a tool call carries argument VALUES that appear nowhere in what the
             agent had seen at that point (user input + prior observations) —
             fabricated arguments.

Both are generic containment checks; no benchmark-specific patterns.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict

try:
    from . import trace as tr
except ImportError:
    import trace as tr


@dataclass
class Finding:
    operator: str
    verdict: str          # flag | ok
    pointer: str          # evidence pointer of the flagged item
    subject: str          # the sentence / argument value in question
    detail: str           # one-line reason

    def as_dict(self):
        return asdict(self)


# ---------------------------------------------------------------- claim_gap
# completed-action assertions: "I have processed…", "I've issued…", "has been
# submitted", "was refunded". Generic auxiliary+participle patterns only.
_ADV = r"(?:also|already|now|just|since|successfully|\w+ly)"
_CLAIM_PAT = re.compile(
    r"\b(?:I(?:'ve| have)|we(?:'ve| have)|(?:has|have)(?:\s+" + _ADV + r")?\s+been"
    r"|was|were|is now|are now)\s+"
    r"(?:" + _ADV + r"\s+){0,2}(\w+(?:ed|en))\b",
    re.I)

_STOP = set("been have has was were will your the this that with from into for and "
            "also then them they their you our are can could would should may might "
            "processed completed done finished confirmed provided received submitted "
            "updated issued".split())


def _content_tokens(s: str) -> list[str]:
    """tokens that identify WHAT was claimed (objects, ids, amounts) — generic
    words and the claim verbs themselves carry no grounding value."""
    toks = re.findall(r"[A-Za-z]{4,}|\d[\d.,-]*", s)
    return [t.lower() for t in toks if t.lower() not in _STOP]


def _verb_stems(verb: str) -> list[str]:
    """'cancelled'->['cancell','cancel'], 'refunded'->['refund'], 'given'->['giv'].
    substring probes against the action stream, so over-stripping is harmless."""
    v = verb.lower()
    outs = []
    if v.endswith("ed"):
        outs.append(v[:-2])
        if len(v) > 4 and v[-3] == v[-4]:
            outs.append(v[:-3])                  # doubled consonant: cancell->cancel
        if v.endswith("ied"):
            outs.append(v[:-3] + "y")            # applied->apply
    elif v.endswith("en"):
        outs.append(v[:-2])
    return [o for o in outs if len(o) >= 3] or [v]


# closed English action-synonym groups — the deterministic bridge between how an
# agent DESCRIBES an action and how the tool NAMES it ("passed to a specialist"
# vs call `escalate`). Fixed table, no benchmark-specific entries; same standing
# as ingest.WEIGHT_MAP.
_VERB_GROUPS = [
    {"pass", "escalat", "transfer", "forward", "handoff", "refer"},
    {"send", "sent", "repli", "messag", "email", "notif", "contact"},
    {"refund", "reimburs", "repay", "repaid", "return"},
    {"cancel", "revok", "terminat", "stop"},
    {"updat", "chang", "modif", "edit", "set", "correct"},
    {"creat", "open", "regist", "add", "apply", "appli", "submit"},
    {"clos", "delet", "remov"},
    {"issu", "grant", "provid", "process"},
    {"check", "verifi", "confirm", "validat", "review", "look"},
    {"block", "freez", "froz", "lock", "suspend"},
]


def _expand_stems(stems: list[str]) -> set[str]:
    out = set(stems)
    for st in stems:
        for grp in _VERB_GROUPS:
            if any(st.startswith(g) or g.startswith(st) for g in grp):
                out |= grp
    return out


def claim_gap(t: "tr.Trace") -> list[Finding]:
    """a COMPLETED-action assertion must reconcile against the ACTION stream:
    the claimed verb has to appear in some call (name or args). Checking the full
    text corpus is wrong — policy/observation text mentions actions that never
    happened (the word 'cancel' existing somewhere doesn't make 'I cancelled'
    true; only a cancel CALL does)."""
    # action corpus = call names + IDENTIFIER-like arg values only. Prose args
    # (reply/message text) are the agent's own speech — including them would let
    # a claim ground itself by having been said inside a send-message call.
    parts = []
    for c in t.calls:
        parts.append(c.name)
        parts.extend(str(v) for v in _arg_values(c.args)
                     if len(str(v).split()) < 4)
    action_corpus = " ".join(parts).lower().replace("_", " ")
    out = []
    agent_all = [(-1, t.final_text)] if t.final_text else []
    agent_all += [(s, x) for s, x in t.agent_texts if x != t.final_text]
    for step, text in agent_all:
        for sent in tr.sentences(text):
            m = _CLAIM_PAT.search(sent)
            if not m:
                continue
            stems = _expand_stems(_verb_stems(m.group(1)))
            ptr = "final_text" if step == -1 else f"agent_texts[{step}]"
            if not any(st in action_corpus for st in stems):
                out.append(Finding("claim_gap", "flag", ptr, sent[:160],
                                   f"完成型断言「{m.group(1)}」在动作流(工具调用)"
                                   f"中无对应动作"))
    return out


# ---------------------------------------------------------------- cite_gap
def _arg_values(args, out=None):
    if out is None:
        out = []
    if isinstance(args, dict):
        for v in args.values():
            _arg_values(v, out)
    elif isinstance(args, (list, tuple)):
        for v in args:
            _arg_values(v, out)
    elif isinstance(args, str):
        if len(args) >= 4 and not args.isdigit() or (args.isdigit() and len(args) >= 4):
            out.append(args)
    elif isinstance(args, (int, float)) and abs(args) >= 1000:
        out.append(str(args))
    return out


def cite_gap(t: "tr.Trace") -> list[Finding]:
    """argument values (specific strings / large numbers) must come from somewhere
    the agent has seen: goal/user text or a PRIOR observation. A value with no
    source is a fabricated argument."""
    out = []
    for c in t.calls:
        # STRICTLY-prior evidence only: the call's own observation echoes its
        # arguments back, which would let a fabricated value ground itself
        seen = t.grounding_corpus(upto_step=c.step).lower()
        for v in _arg_values(c.args):
            vs = str(v).strip().lower()
            if len(vs) < 4:
                continue
            if len(vs.split()) >= 4:
                # prose-length arg = agent speech (reply/message text), not an
                # identifier that needs a source — the language stream owns it
                continue
            if vs in seen:
                continue
            # tolerate case/format drift: try digits-only form for numbers/ids
            digits = re.sub(r"[^\d]", "", vs)
            if digits and len(digits) >= 4 and digits in re.sub(r"[^\d]", "", seen):
                continue
            out.append(Finding("cite_gap", "flag", c.pointer, vs[:120],
                               f"调用 {c.name} 的参数值在此前的用户输入/观察中不存在"))
    return out


# ---------------------------------------------------------------- batch 2
# read-class call prefixes: observing the world, not changing it
_READ_PREFIX = ("get", "lookup", "look_up", "check", "search", "list", "read",
                "find", "query", "fetch", "view", "show")
# communication / delegation calls: speech acts, not state changes
_SPEECH_NAMES = ("reply", "respond", "message", "send_message", "notify", "email")
_HANDOFF = ("escalat", "transfer", "refer", "assign", "handoff")

_ERRISH = re.compile(r"\berror\b|\bfailed\b|\bexception\b|\bnot found\b|\bdenied\b", re.I)
_FUTURE_PAT = re.compile(
    r"\b(I|we)\s+(?:will|'ll|shall|am going to|are going to)\s+"
    r"(?:" + _ADV + r"\s+){0,2}(\w+)\b", re.I)
_FAIL_PAT = re.compile(r"\b(?:cannot|can't|unable to|failed to|won't be able)\b", re.I)


def _is_read(name: str) -> bool:
    n = name.lower()
    return any(n.startswith(p) for p in _READ_PREFIX)


def _is_speech(name: str) -> bool:
    n = name.lower()
    return any(s in n for s in _SPEECH_NAMES)


def _write_calls(t: "tr.Trace") -> list:
    return [c for c in t.calls
            if c.name and not _is_read(c.name) and not _is_speech(c.name)]


def promise_open(t: "tr.Trace") -> list[Finding]:
    """AGENT-subject future promises ("I will refund…") must have either a matching
    action already in the stream or a handoff call carrying them. Third-party
    promises after a handoff are delegated and not checkable here (disclosed
    limitation — they need world knowledge)."""
    action_corpus = " ".join(c.name for c in t.calls).lower().replace("_", " ")
    has_handoff = any(h in c.name.lower() for c in t.calls for h in _HANDOFF)
    out = []
    for sent in tr.sentences(t.final_text):
        m = _FUTURE_PAT.search(sent)
        if not m:
            continue
        stems = _expand_stems(_verb_stems(m.group(2)) + [m.group(2).lower()])
        if any(st in action_corpus for st in stems):
            continue
        if has_handoff:
            continue                       # delegated future work rides the handoff
        out.append(Finding("promise_open", "flag", "final_text", sent[:160],
                           f"未来承诺「{m.group(2)}」既无对应动作也无移交调用"))
    return out


def noop_mask(t: "tr.Trace") -> list[Finding]:
    """a write-class call with EMPTY args and empty/失败 observation, while the
    final text claims completion — the shape of a faked operation."""
    out = []
    claims = bool(_CLAIM_PAT.search(t.final_text or ""))
    for c in _write_calls(t):
        if c.args and any(str(v).strip() for v in c.args.values()):
            continue
        o = tr.observation_for_call(t, c)
        empty_obs = (o is None or not o.text.strip()
                     or o.text.strip() in ("{}", "[]", "null", "none")
                     or bool(_ERRISH.search(o.text)))
        if empty_obs and claims:
            out.append(Finding("noop_mask", "flag", c.pointer, c.name,
                               "空参写操作+空/失败观察,但终答复声称完成"))
    return out


def retry_churn(t: "tr.Trace") -> list[Finding]:
    """>=3 consecutive identical calls whose observations look like errors —
    spinning without progress."""
    out = []
    run_len, prev = 1, None
    for c in t.calls:
        sig = (c.name, tr._jtext(c.args))
        o = tr.observation_for_call(t, c)
        err = bool(o and _ERRISH.search(o.text))
        if sig == prev and err:
            run_len += 1
            if run_len == 3:
                out.append(Finding("retry_churn", "flag", c.pointer, c.name,
                                   "同一调用连续 3 次以上且观察均为错误,无进展"))
        else:
            run_len = 1
        prev = sig if err else None
    return out


def final_consistency(t: "tr.Trace") -> list[Finding]:
    """the final text says FAILURE but a write-class call succeeded (its
    observation is non-empty and not error-ish) — words contradict state."""
    if not _FAIL_PAT.search(t.final_text or ""):
        return []
    out = []
    for c in _write_calls(t):
        o = tr.observation_for_call(t, c)
        if o and o.text.strip() and not _ERRISH.search(o.text):
            out.append(Finding("final_consistency", "flag", c.pointer, c.name,
                               "终答复称失败/无法办理,但该写操作已成功执行"))
    return out


def silent_effect(t: "tr.Trace") -> list[Finding]:
    """a successful write-class call the final text NEVER mentions (verb-group
    check) — a state change the user was not told about."""
    final = (t.final_text or "").lower()
    if not final:
        return []
    out = []
    for c in _write_calls(t):
        o = tr.observation_for_call(t, c)
        if o is None or _ERRISH.search(o.text):
            continue
        name_toks = [w for w in c.name.lower().split("_") if len(w) >= 3]
        stems = _expand_stems(name_toks)
        if not any(st in final for st in stems):
            out.append(Finding("silent_effect", "flag", c.pointer, c.name,
                               "写操作已执行成功,但终答复从未向用户提及"))
    return out


def state_delta_scope(t: "tr.Trace", db_before=None, db_after=None) -> list[Finding]:
    """DB paths that changed but whose leaf value appears in NO call argument —
    a change nothing in the action stream accounts for. No-op without the DB pair."""
    if not isinstance(db_before, dict) or not isinstance(db_after, dict):
        return []
    args_blob = " ".join(tr._jtext(c.args) for c in t.calls).lower()

    def walk(b, a, path):
        out = []
        if isinstance(b, dict) and isinstance(a, dict):
            for k in sorted(set(b) | set(a)):
                out += walk(b.get(k), a.get(k), f"{path}.{k}")
        elif b != a:
            leaf = tr._jtext(a).lower()
            if len(leaf) >= 4 and leaf not in args_blob:
                out.append(Finding("state_delta_scope", "flag", path.lstrip("."),
                                   leaf[:80], "DB 变更值未出现在任何调用参数中"))
        return out
    return walk(db_before, db_after, "")


BATCH1 = {"claim_gap": claim_gap, "cite_gap": cite_gap}
BATCH2 = {"promise_open": promise_open, "noop_mask": noop_mask,
          "retry_churn": retry_churn, "final_consistency": final_consistency,
          "silent_effect": silent_effect}


def run_all(t: "tr.Trace", db_before=None, db_after=None,
            batch2: bool = True) -> dict:
    out = {name: [f.as_dict() for f in op(t)] for name, op in BATCH1.items()}
    if batch2:
        out.update({name: [f.as_dict() for f in op(t)]
                    for name, op in BATCH2.items()})
        out["state_delta_scope"] = [
            f.as_dict() for f in state_delta_scope(t, db_before, db_after)]
    return out


def _selftest():
    steps = [{"index": 0, "thought": "",
              "call": {"name": "get_acct", "arguments": {"acct": "AC-99881"}},
              "observation": {"acct": "AC-99881", "balance": 120}}]
    # fabricated argument: AC-99881 never appeared before the call
    t = tr.from_steps(steps, final_answer="I have refunded your subscription fee.",
                      goal="what is my balance?")
    r = run_all(t)
    assert any(f["operator"] == "cite_gap" for f in r["cite_gap"]), r
    assert any("refunded" in f["subject"] for f in r["claim_gap"]), r
    # grounded case: no flags
    t2 = tr.from_steps(
        [{"index": 0, "thought": "",
          "call": {"name": "get_acct", "arguments": {"acct": "AC-1"}},
          "observation": {"balance": 120}}],
        final_answer="Your balance is 120.", goal="check balance of AC-1")
    r2 = run_all(t2)
    assert not r2["claim_gap"] and not r2["cite_gap"], r2
    print("operators selftest OK")


if __name__ == "__main__":
    _selftest()
