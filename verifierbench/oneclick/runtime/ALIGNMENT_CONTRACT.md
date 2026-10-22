# Integration alignment v4

This independent runtime applies to newly regenerated Veritas + GPT-6-astra
artifacts from the frozen 222-task paper222 set. Original runtimes and results
remain unchanged. Every new artifact pins this MANIFEST.json SHA; replay refuses
a differing manifest. State/code generation and replay use the same modern
public-observation contract, native sources, client, and capability backends.
Generation must set VGB_PUBLIC_OBSERVATION_V2=1 before importing registry/Broker.

Normal candidate judgments are binary PASS/FAIL, following the paper generation
requirement. Runtime/schema/transport errors and native execution failures remain
explicit errors/ABSTAIN where the unmodified original evaluator requires them;
no existing judgment is coerced or filled. This does not change score rules.

AppWorld candidate programs are invoked via run_appworld_solution(source), which
calls solution(apis, requester) exactly once. Plain code probes never implicitly
call defined functions. Completed invocation is not semantic correctness. State
fingerprints are opaque; public API inspection establishes domain assertions.

AgentDojo returns per-tool observations and final_state. That returned final_state
is the terminal evidence; inspect(state) refers to the separate baseline world.
Tau2 DB hashes are opaque identity evidence, not goal predicates. Neither source
provides a hidden oracle, hidden expected state, or labels to the generator.

Exploration remains 20 run_public calls per episode. Replay has one task broker,
serial candidates with reset, and native task-shared total budget (per-candidate
allowance times candidate count). Reset does not refund calls. The frozen views,
labels, task membership, scorer formula, and input/renderer hashes are unchanged.
SWE uses the supplied immutable RepoDigest for all 47 frozen tasks.
