# gavel-harness

gavel-harness generates a closed-book verifier for each [Harbor](https://github.com/harbor-framework/harbor)
task, writes it back into the task as `tests/`, and checks it with three anchors
(null, oracle, swap) that each end in a three-state verdict: PASS, FAIL or NO_VERDICT.

Status: pre-release. Implemented paradigms: `terminal_state` and `deliverable`;
executor: `opencode`. Not in this build: declare mode (`--declare` is refused
because the declaration and its certificate are not collected yet) and the
in-image import check of a deliverable task's parser libraries.

## Install

Requires Python 3.12+, Linux and Docker with the compose plugin, Docker Compose
2.24.4 or later: generation leaves a task's own compose file out with compose's
`!override` tag, which earlier versions ignore without an error (`gavel-harness
doctor` checks it). Harbor is pinned to commit 2fe1615 (version 0.21.0),
installed from its git repository.

```bash
pip install -e .
gavel-harness --help
```

## Usage

```bash
export OPENAI_API_KEY=...
gavel-harness doctor --model openai/gpt-6-astra \
  --base-url https://api.openai.com/v1 --api-key-env OPENAI_API_KEY
gavel-harness gen examples/hello-terminal --model openai/gpt-6-astra \
  --base-url https://api.openai.com/v1 --api-key-env OPENAI_API_KEY \
  --validate --out ./out/hello-terminal
gavel-harness gen examples/deliverable-mini --paradigm deliverable \
  --model openai/gpt-6-astra \
  --base-url https://api.openai.com/v1 --api-key-env OPENAI_API_KEY \
  --validate --out ./out/deliverable-mini
```

`--model` is `<provider id>/<model id>`; the endpoint must serve the
OpenAI-compatible chat completions API. `--api-key-env` names the environment
variable that holds the key; the key itself is never written to `run.json` or
any other output. By default every model request goes through a metering proxy
on the host (port 8878, listening on the Docker bridge gateway) that adds the
key, records tokens per trial and absorbs rate limiting; containers only see a
placeholder key. `--no-meter` sends requests directly and passes the key into
the containers.

| Command | Purpose |
|---|---|
| `gavel-harness doctor` | Check that the host can run `gavel-harness gen` |
| `gavel-harness gen` | Generate verifiers, write them back, validate with `--validate` |
| `gavel-harness validate --from-run` | Run the three anchors on the verifiers of an earlier run of the original harness's one-command driver |
| `gavel-harness matrix` | Build the support matrix over registry families |
| `gavel-harness report` | Print the summary of a finished run |

Exit codes: 0 every task validated; 1 some task not validated; 2 configuration
error, failed host check or refused task; 3 infrastructure error (results are
incomplete; re-run the affected tasks); 4 unexpected internal error.
`docs/running.md` describes the run directory, the labels and the host checks.

Harbor's anonymous usage telemetry is off for every `gavel-harness` command unless
`HARBOR_TELEMETRY` is already set.

## Paradigms

Every supported task belongs to one of five paradigms: `terminal_state`,
`deliverable`, `repo_patch`, `dialog_state`, `pairwise_text`. Differences
between benchmarks within a paradigm are TOML profiles under
`src/gavel_harness/profiles/`.

## Prompt wording

The generation prompt opens with an evidence header in one of two wordings,
selected by the profile's `wording` key. New tasks use `state_gate`: when the
task's end state can be checked against its starting state, that comparison
decides the requirement, and process or conversation evidence cannot overturn a
failed comparison. The `paper/generic` and `gdpval` profiles use it.
`frozen_evh1` is the earlier wording: it asks for state assertions written as
code comparisons when state evidence exists and for process assertions
otherwise, without making the state comparison decide. The `paper/tb4` and
`paper/tbsci` profiles use it, as the original harness did for those benchmarks.

## Fidelity to the original harness

Prompt texts, contracts, probe scripts, install blocks and task.toml templates are
copied or extracted byte for byte from the original harness, and `UPSTREAM.lock`
records each with its origin. Seven Python modules carry the upstream code with
rewritten comments and docstrings (`verbatim-code` in the lock); ported code is
held to the upstream output.
`DEVIATIONS.toml` lists every behaviour difference and its category. The rubric library ships with the tool that builds it;
`docs/rubric_library.md` rebuilds it from public inputs.

## Layout

```
src/gavel_harness/   package (method, paradigms, profiles, intake, build, run, meter,
                       verify, export, rubric; cli and pipeline)
examples/              hello-terminal (terminal_state), deliverable-mini (deliverable)
docs/  tools/  images/
```

## License

Apache-2.0. See `LICENSE` and `NOTICE` for third-party material.
