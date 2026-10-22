#!/usr/bin/env python3
"""Five gates over the whole certifiable tau2 pool, not the four repaired tasks.

tau2_five_gates covered 4 tasks whose obligation is COMMUNICATE, and built its
candidates out of `communicate_info` needles. That construction does not
generalise: most tasks are bound by ACTIONS and the agent-side DB, so a
candidate has to actually CALL the tools -- evaluator_env replays the
candidate's tool calls into a predicted environment and compares its DB hash
against a gold environment replaying `evaluation_criteria.actions`.

So the pool is built from those actions:

  gold        every expected action, in order, with its exact arguments
  base        nothing at all
  near_miss   every action but the last mutating one
  equivalent  the same actions plus an inert assistant utterance
  lies        no calls, but claims the work is done

Adjudication comes from construction, not from the grader. Everything stays on
the deterministic path -- nl_assertions are stripped, because leaving them in
routes the verdict through a remote LLM judge (TAU2-I2) and a gate measured
through a nondeterministic judge is not a measurement.
"""
import collections
import copy
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "tau2-bench", "src"))
from tau2.data_model.simulation import SimulationRun          # noqa: E402
from tau2.evaluator.evaluator import EvaluationType, evaluate_simulation  # noqa: E402
from tau2.registry import registry as R                        # noqa: E402
import tau2_stub_embedder as STUB                              # noqa: E402

# banking_knowledge builds its retrieval pipeline at ENVIRONMENT-CONSTRUCTION
# time. The default `alltools` variant wants an OpenAI embedder (no key here;
# Ark's chat endpoint works with our key but every text-embedding model reports
# InvalidEndpointOrModel.NotFound) and an agentic shell sandbox (`srt`, `rg` not
# installed). `bm25` needs neither and is a variant the benchmark ships.
#
# This is a CONFIGURATION choice, not a stub: retrieval still runs, just
# lexically. It is applied to the gold environment and the candidate
# environment alike -- evaluator_env constructs both through the same
# constructor -- so the DB-hash comparison is unaffected. What it does change is
# what the retrieval TOOL returns, so any task whose obligation is the retrieved
# content is measured under bm25 rather than under the default pipeline. Those
# tasks are marked, not silently counted.
BANKING_VARIANT = os.environ.get("V4V_TAU2_RETRIEVAL", "bm25")
STUB.install()

HERE = os.path.dirname(os.path.abspath(__file__))
READ_ONLY = ("get_", "find_", "list_", "show_", "search_", "calculate_", "look")


def run(task_id, messages):
    return SimulationRun.model_validate({
        "id": "v4v", "task_id": task_id, "timestamp": "2026-08-02T00:00:00",
        "start_time": "2026-08-02T00:00:00", "end_time": "2026-08-02T00:00:01",
        "duration": 1.0, "termination_reason": "agent_stop",
        "messages": messages, "trial": 0, "seed": None})


def calls_for(actions, domain, task):
    """assistant tool_call + the REAL tool result, one pair per action.

    The tool result cannot be faked. Environment.set_state replays each call and
    compares its own response against the recorded ToolMessage; with strict
    replay on (the default, and TAU2-E4 is about what happens when it is off) a
    mismatch raises `Tool call: ... Returned: ... Expected: ...`. A stub "ok"
    therefore blew up 5 of the 6 smoke tasks -- and the exception surfaced as
    "gold does not pass", which is the shape of a benchmark finding rather than
    of a candidate that was never valid.

    So the responses are produced the same way the gold environment produces
    them: build a scratch environment from the task's initial state and execute
    the actions in order.
    """
    from tau2.data_model.message import ToolCall
    env = R.get_env_constructor(domain)()
    init = task.initial_state
    env.set_state(
        initialization_data=(init.initialization_data if init else None),
        initialization_actions=(init.initialization_actions if init else None),
        message_history=[], strict=False)
    msgs = []
    for i, a in enumerate(actions):
        cid = f"v4v_{i}"
        tc = ToolCall(id=cid, name=a.name, arguments=a.arguments or {},
                      requestor=a.requestor or "assistant")
        resp = env.get_response(tc)
        msgs.append({"role": "assistant", "content": None,
                     "tool_calls": [tc.model_dump()]})
        msgs.append({"role": "tool", "id": cid, "content": resp.content,
                     "requestor": a.requestor or "assistant",
                     "error": bool(getattr(resp, "error", False))})
    return msgs


def pool_for(task, domain):
    """Gold has to satisfy EVERY component in reward_basis, not just the DB.

    The first version emitted the expected tool calls and said nothing. On
    airline/3 that scored DB=1.0, COMMUNICATE=0.0 -> reward 0.0, and all six
    smoke tasks reported "gold fails". Read as a benchmark result that is a
    six-task finding; read correctly it is a candidate that never did half the
    task. `communicate_info` is part of the obligation and gold must say it.
    """
    ec = task.evaluation_criteria
    acts = list(ec.actions or [])
    needles = list(ec.communicate_info or [])
    if not acts and not needles:
        return None
    say = [{"role": "assistant", "content": " ".join(needles)}] if needles else []
    gold = calls_for(acts, domain, task) + say
    # equivalent: same actions, the same facts said differently
    eq_say = ([{"role": "assistant",
                "content": "Certainly — " + ", ".join(needles) + ". Anything else?"}]
              if needles else [{"role": "assistant", "content": "All set."}])
    eq = calls_for(acts, domain, task) + eq_say
    pool = [("gold", gold, "PASS"), ("base", [], "FAIL"),
            ("equivalent", eq, "PASS"),
            # says the work is done, does none of it
            ("lies", [{"role": "assistant",
                       "content": "Done, I've taken care of that."}], "FAIL")]
    # A candidate must fail at EXACTLY ONE component or the G3 hole for that
    # component stays masked: `base` and `lies` miss the DB too, so making
    # COMMUNICATE always-true left their verdicts unchanged and the hole read as
    # undetected (26_ 3 is the same story in AppWorld).
    if needles:
        # COMMUNICATE asks "did you tell the user this", and it matches by
        # containment -- deliberately, because extra words in an utterance are
        # fine. So APPENDING to a needle is not a near-miss at all: '1628_v4v'
        # still contains '1628' and passed, which looked like grader leniency
        # and was a bad candidate. A near-miss has to say a DIFFERENT value.
        def _perturb(x):
            s = str(x)
            if s.isdigit():
                return str(int(s) + 1)
            return "".join(chr(ord(c) + 1) if c.isalnum() else c for c in s)
        wrong = list(needles[:-1]) if len(needles) > 1 else [_perturb(needles[0])]
        pool.append(("near_miss_communicate",
                     calls_for(acts, domain, task)
                     + [{"role": "assistant", "content": " ".join(wrong)}],
                     "FAIL"))
    mutating = [i for i, a in enumerate(acts)
                if not a.name.startswith(READ_ONLY)]
    if mutating:
        keep = [a for i, a in enumerate(acts) if i != mutating[-1]]
        # near-miss: everything right except one state change, and it still
        # reports correctly -- so only the DB component may differ
        pool.append(("near_miss", calls_for(keep, domain, task) + say, "FAIL"))
    elif needles and len(needles) > 1:
        pool.append(("near_miss", calls_for(acts, domain, task)
                     + [{"role": "assistant", "content": " ".join(needles[:-1])}],
                     "FAIL"))
    return pool


def grade(task, domain, messages):
    t = copy.deepcopy(task)
    t.evaluation_criteria.nl_assertions = None
    try:
        ri = evaluate_simulation(simulation=run(t.id, messages), task=t,
                                 evaluation_type=EvaluationType.ALL,
                                 solo_mode=False, domain=domain)
        return "PASS" if ri.reward == 1.0 else "FAIL"
    except Exception as e:
        return f"ERROR:{type(e).__name__}"


def main():
    targets = json.load(open(f"{HERE}/tau2_certifiable.json"))
    by_dom = collections.defaultdict(list)
    for d, t in targets:
        by_dom[d].append(t)
    out, tally = [], collections.Counter()
    def flush():
        json.dump(out, open(f"{HERE}/tau2_all_gates.json", "w"),
                  indent=1, ensure_ascii=False)

    for domain, ids in by_dom.items():
        # One domain that cannot even be constructed must not discard the
        # domains already measured. banking_knowledge builds an embedder that
        # calls OpenAI, and the OpenAIError propagated out of the loop after 95
        # airline+retail tasks had already been graded -- all of them lost,
        # because results were only written at the end.
        if domain == "banking_knowledge":
            # registry._domains[domain] IS the environment constructor, and it
            # is what evaluator_env calls for BOTH the gold and the candidate
            # environment -- replacing it here keeps the two sides identical,
            # which is the only reason a non-default retrieval variant is safe.
            from tau2.domains.banking_knowledge.environment import (
                get_environment as _ge)

            def fixed(*a, **k):
                k.pop("retrieval_variant", None)
                return _ge(*a, retrieval_variant=BANKING_VARIANT, **k)

            R._domains[domain] = fixed
            assert R.get_env_constructor(domain) is fixed, "检索变体没换上"
        try:
            tasks = {t.id: t for t in R.get_tasks_loader(domain)()}
        except Exception as e:
            tally[f"{domain}: 域无法构造 ({type(e).__name__})"] += len(ids)
            for tid in ids:
                out.append({"domain": domain, "task_id": tid,
                            "blocked": "domain_unavailable",
                            "detail": f"{type(e).__name__}: {str(e)[:120]}"})
            flush()
            continue
        for tid in ids:
            task = tasks.get(tid)
            if task is None:
                tally["任务不存在"] += 1
                continue
            try:
                pool = pool_for(task, domain)
            except Exception as e:
                tally[f"造池异常 {type(e).__name__}"] += 1
                out.append({"domain": domain, "task_id": tid,
                            "blocked": "pool_error",
                            "detail": f"{type(e).__name__}: {str(e)[:120]}"})
                continue
            if not pool:
                tally["无 actions，造不出池"] += 1
                continue
            v, dis = {}, []
            for cid, msgs, adj in pool:
                got = grade(task, domain, msgs)
                v[cid] = got
                if got != adj:
                    dis.append(cid)
            if v.get("gold") != "PASS":
                tally["gold 不过（先怀疑自己）"] += 1
                out.append({"domain": domain, "task_id": tid, "verdicts": v,
                            "blocked": "gold_gate"})
                continue
            g1a = v["gold"] == "PASS" and v["base"] == "FAIL"
            g1c = not dis
            g2 = (v.get("near_miss") == "FAIL" and v.get("equivalent") == "PASS")
            flips = 0
            for _ in range(2):
                for cid, msgs, _adj in pool:
                    if grade(task, domain, msgs) != v[cid]:
                        flips += 1
            ok = g1a and g1c and g2 and flips == 0
            tally["G1+G2+G5 全过" if ok else "有缺口"] += 1
            out.append({"domain": domain, "task_id": tid, "verdicts": v,
                        "g1a": g1a, "g1c_kappa_is_1": g1c, "g2": g2,
                        "g5_flips": flips, "disagreements": dis})
            print(f"{domain}/{tid:<8}{'✓' if ok else '✗'}  "
                  + " ".join(f"{k}={x}" for k, x in v.items()), flush=True)
            if len(out) % 20 == 0:
                flush()
    print()
    print(f"   embedder 桩被调用 {STUB.CALLS['n']} 次（{STUB.CALLS['texts']} 段文本）"
          f"{'——检索确实参与了，这些题需另行核实' if STUB.CALLS['n'] else '——从未被调用，桩不影响任何判决'}")
    for k, n in tally.most_common():
        print(f"   {k}: {n}")
    flush()


if __name__ == "__main__":
    main()
