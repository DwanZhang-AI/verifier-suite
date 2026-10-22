# Execution and diagnostic revision: suite-fix-20261021-v1

This is a repaired suite, not an unchanged reproduction of the supplied runtime.
Use a new result directory. Never overwrite old artifacts, results, or receipts.
The scoring formula, frozen candidates, labels, task membership and budgets are unchanged.

## AppWorld: probes and candidates are different operations

`vgb_env.run_public({"code": code})` runs an ordinary Python cell. A cell containing
only a function definition does not execute that function. Do not send
`candidate["payload"]["solution"]` through this probe operation.

Use the injected client:

```python
execution = vgb_env.run_appworld_solution(candidate["payload"]["solution"])
```

Equivalently, the backend accepts `run_public({"solution": source})`. It executes
the source in a fresh namespace and explicitly calls `solution(apis, requester)`.
This consumes one existing run_public budget unit; reset does not replenish it.
The call can mutate the current public world. The runner resets before each candidate.
Do not submit both `code` and `solution` keys.

`execution_status="completed"` certifies that invocation returned, not that the
candidate is correct. Independently inspect public state to decide PASS/FAIL.
An execution error must not silently become PASS or FAIL; report ABSTAIN and its
reason when the verifier cannot establish a semantic judgment. Candidate defects
may be judged only from independently established evidence, not a generic error.
The helper does not call official evaluation or expose hidden labels or reference answers.

Generation integration: include this instruction and the updated client/backend
together. A source-only checker lint is available as `scripts/check_delivery.py`.
It warns about direct solution-as-code use and missing literal PASS returns;
these are review hints, never a correctness certificate or an automatic rewrite.

## tau2

No observation expansion or artificial PASS rule is introduced in this repair.
`inspect("state")` exposes a DB fingerprint, not the goal state itself. A changed
hash alone does not prove correctness. A checker that cannot verify the goal
must report that limitation; a verifier with no successful acceptance path needs
review. Do not provide hidden evaluation criteria to make it accept positives.

## Durable diagnosis

Every replay writes `<out>.decisions/` in the trusted evaluator directory. Each
record preserves the untrusted verifier payload (including checks/reasons) and
the runner's execution status/error. The verdict row binds its identity and SHA;
the replay receipt also binds the exact Python runtime source hashes.
Files are private (0600, directory 0700), never mounted into the verifier sandbox,
and must not be sent to model generation. Existing audit files cannot be replaced.
The original verdict/payload hash and scoring interpretation are unchanged.

Existing experiments must not silently switch to this revision. A modified
checker requires a new artifact/hash; a new generation contract must be recorded
as such. This release does not repair historical results or claim a higher score.

## Public execution output repair: suite-output-fix-20261021-v2

AppWorld code-cell and explicit-candidate stdout is returned losslessly.
The previous silent 20,000-character slice corrupted JSON observations.
The complete response still passes the original oracle leakage scan.
Model-facing bounded pages use the existing ObservationStore after scrubbing;
Python checkers receive the original complete output. Budgets are unchanged.
Ordinary code cells still do not implicitly call candidate functions.
No checker, public task, candidate, label, score rule or budget is rewritten.
Historical replays use a separate result directory and runtime SHA receipts.

## Complete public observations: suite-contract-fix-20261021-v3

AppWorld inspect returns complete already-public instructions, supervisor data
and API documentation. tau2 inspect returns complete already-public description
and user scenario; replay returns every nonempty assistant message in order.
All fixed-count/text slices on these public fields are removed. The existing
full oracle scrub and lossless model-facing pages are retained, with unchanged
run/reset semantics and budgets. No hidden goal state, labels or native
evaluation results are exposed. This does not add new goal acceptance logic,
automatically call code-cell functions, or regenerate delivered checkers.

AppWorld reset/state identity now uses a SHA256 of native ModelCollection
model_hashes, not a stringified failed API call. Empty/incomplete native
hashes raise an error instead of producing a constant fingerprint. Native
validation must show stable reads, mutation sensitivity and reset recovery.
Only the opaque digest is exposed; database records and labels remain private.
