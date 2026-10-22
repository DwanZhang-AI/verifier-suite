#!/usr/bin/env python3
"""G1a/G1c/G2 for AgentDojo, using the benchmark's own ground-truth pipeline.

AgentDojo grades with per-task Python predicates -- `utility(model_output,
pre_env, post_env)` for the user task and `security(...)` for the injection --
and ships `GroundTruthPipeline`, which executes `task.ground_truth(env)`. So the
anchors need no model:

  gold        run GroundTruthPipeline            utility must be True
  base        run nothing                        utility must be False
  near_miss   ground truth minus its last call   utility must be False
  equivalent  ground truth plus a read-only call  utility must be True

`base -> True` means the task is already satisfied before the agent acts, i.e.
there is no anchor at all -- the same `base_candidate_passes` shape that removed
29 tau2 tasks from the certifiable pool. `near_miss -> True` means the last call
is not actually required by the predicate.
"""
import json
import sys
import traceback

from agentdojo.agent_pipeline.ground_truth_pipeline import GroundTruthPipeline
from agentdojo.task_suite.load_suites import get_suites


def gold_text(suite, task, env):
    """What a correct agent would SAY, harvested from the ground-truth calls.

    43 of 97 tasks reported "gold fails" with an empty model_output, and the
    reason is in the predicate: query tasks such as workspace/user_task_0 check
    `list_is_in_string_or_set(self._EMAIL_ADDRESSES, model_output)` -- the
    obligation is the ANSWER TEXT, not the environment. A candidate that runs the
    right tools and says nothing has done half the task, exactly as in tau2 where
    the same omission scored DB=1.0 COMMUNICATE=0.0.

    The tool outputs are the answer material, so the text is built from them
    rather than from the task's private expected values -- using those would be
    grading the candidate against itself.
    """
    from agentdojo.functions_runtime import FunctionsRuntime
    runtime = FunctionsRuntime(suite.tools)
    parts = []
    for c in task.ground_truth(env):
        try:
            out, _err = runtime.run_function(env, c.function, dict(c.args),
                                             raise_on_error=False)
            parts.append(str(out))
        except Exception:
            continue
    return "\n".join(parts)


def run_calls(suite, task, calls):
    """Execute a list of FunctionCalls against a fresh environment."""
    env = suite.load_and_inject_default_environment({})
    from agentdojo.functions_runtime import FunctionsRuntime
    runtime = FunctionsRuntime(suite.tools)
    for c in calls:
        try:
            runtime.run_function(env, c.function, dict(c.args), raise_on_error=False)
        except Exception:
            pass
    return env


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "v1.2"
    suites = get_suites(version)
    rows = []
    for sname, suite in suites.items():
        for tid, task in suite.user_tasks.items():
            rec = {"suite": sname, "task_id": tid, "kind": "user"}
            try:
                pre = suite.load_and_inject_default_environment({})
                gt = task.ground_truth(pre)
                rec["n_calls"] = len(gt)
                text = gold_text(suite, task, suite.load_and_inject_default_environment({}))
                post_gold = run_calls(suite, task, gt)
                rec["gold"] = bool(task.utility(text, pre, post_gold))
                post_base = suite.load_and_inject_default_environment({})
                rec["base"] = bool(task.utility("", pre, post_base))
                rec["base_with_text"] = bool(task.utility(text, pre, post_base))
                if gt:
                    post_nm = run_calls(suite, task, gt[:-1])
                    rec["near_miss"] = bool(task.utility(text, pre, post_nm))
                rec["g1a"] = rec["gold"] and not rec["base"]
                rec["g2_negative"] = (not rec.get("near_miss", True))
            except Exception as e:
                rec["error"] = f"{type(e).__name__}: {str(e)[:90]}"
            rows.append(rec)
            flag = ("✓" if rec.get("g1a") else "✗") if "error" not in rec else "!"
            print(f"{sname}/{tid:<28}{flag} gold={rec.get('gold')} "
                  f"base={rec.get('base')} near_miss={rec.get('near_miss')}"
                  f"{'  ' + rec['error'] if 'error' in rec else ''}", flush=True)
    ok = sum(1 for r in rows if r.get("g1a"))
    nm = sum(1 for r in rows if r.get("g2_negative"))
    err = sum(1 for r in rows if "error" in r)
    print(f"\nAgentDojo {version}: {len(rows)} 道 user_task")
    print(f"   G1a（gold 过 且 base 不过）: {ok}")
    print(f"   近错解被抓（G2 负向侧）:      {nm}")
    print(f"   执行异常:                    {err}")
    json.dump(rows, open("ad_gates.json", "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
