# Running gavel-harness

## `gavel-harness gen`

```bash
gavel-harness gen <task | directory of tasks | registry:<dataset>@<commit>> ... \
  --model <provider>/<model> --base-url <url> --api-key-env <NAME> \
  [--profile paper/generic] [--paradigm terminal_state|deliverable] [--validate] \
  [--oracle-root DIR] [--tasks-file FILE] [--concurrency 4] --out DIR
```

A run goes through these steps. A step that fails stops the run with its exit
code; from step 2 on, `run.json` records it first (`outcome`: exit code, step,
error).

1. The method resolves: profile, environment profile, paradigm, the package
   plan and the anchor judge environment (`--verifier-network` and
   `--keep-images`/`--no-keep-images` override the profile's settings), and
   `--tasks-file` and `--oracle-root` must exist. `--declare` is refused: this
   build does not collect the declaration yet. Nothing is written before this
   succeeds.
2. Host checks (the same as `gavel-harness doctor`). Any failure exits 2.
3. Intake. A directory holding `task.toml` or `instruction.md` is a task;
   another directory is searched for tasks, and with a single directory input
   task ids are paths relative to it. Registry inputs need `--registry` and
   draw `--sample` tasks with `--seed`. Each task is sniffed with Harbor's task
   model; refused tasks are printed with their reason code, listed in
   `refused.json` and the summary, and get no result row. Every accepted task
   must be writable back before generation starts: its id is a relative path
   of plain names (`[A-Za-z0-9_][A-Za-z0-9_.-]*` per part), its task.toml
   merges, its reference solution has a solve script. A task that is not is
   refused (`not_writable`); the others go on.
4. The metering proxy starts, and a container on the Docker bridge network
   must reach its health route (skipped with `--no-meter`).
5. Generation: one Harbor job for attempt A, one for the feedback retry B of
   tasks whose probe was CRASH or NODIRECTION. Each trial runs the package's
   Dockerfile image alone, started with `sleep infinity` in place of its
   `ENTRYPOINT`, as in the original harness: a package's own
   `environment/docker-compose.yaml` starts no service (this needs Docker
   Compose 2.24.4 or later; the `compose_override` host check refuses an
   earlier one). Under the profile's
   `[run] agent_exec_cap_sec` (3900 s in every shipped profile) every agent
   command ends at that cap; the trial then ships the verifier written so far
   without probing it, as the original harness did. A trial that rate limiting
   reached (a 429 passed to the agent, a request its client abandoned while the
   metering proxy waited out 429s, or an agent that ran out of time or into the
   exec cap after such waits) or with a request the upstream never answered is
   discarded and rerun, at most 3 times. An infrastructure
   failure (stall, Docker daemon, meter, endpoint, Harbor) stops generation;
   every generated task becomes an `infra_error` row and the run exits 3. A
   task whose own environment could not be built or started (twice) is an
   `infra_error` row too, and the other tasks go on.
6. Every delivered verifier is written back into a copy of its task under
   `tasks/<id>/`; the input task is only read.
7. With `--validate`, the null, oracle and swap anchors run as Harbor jobs on
   the written tasks; swap donors are drawn from every accepted task, delivered
   or not. Without it, delivered tasks are labelled `unvalidated`.
8. The report: `results.jsonl`, `summary.md`, and `VERIFIER_REPORT.md` in each
   written task.
9. The images Harbor built for the run's trials are removed by exact name,
   unless the profile's `[anchor] keep_images` keeps them (true for
   `paper/tb4` and `paper/tbsci`) or `--keep-images` is given; the outcome of
   each removal is in `run.json`.

Reference solutions are looked up as `<oracle-root>/<id>/solution`, then
`<task>/solution`.

### Run directory

```
run.json            command, config, provenance, run id, endpoint (key variable name,
                    provider block with placeholder or {env:NAME}), generation (prompt
                    wording, exec cap), anchor settings, host checks, metering proxy
                    address, outcome
packages/           sealed generation packages, _runs.json, refused.jsonl
jobs/               generation Harbor jobs and their input snapshots
meter/ledger.jsonl  one row per model request (metered runs)
generation.jsonl    one generation result per task: probe, attempts, usage, 429 reruns
tasks/<id>/         written-back Harbor tasks with tests/veritas/ and VERIFIER_REPORT.md
anchors/            anchor Harbor jobs
refused.json        {task id: reason}
results.jsonl       one row per generated task
summary.md
```

`run.json` never holds the API key, only the name of its variable.

### Labels

Each task gets the first label whose condition holds:

| Label | Condition |
|---|---|
| `infra_error` | an infrastructure failure hit the task (its environment could not be built or started included); re-run, not counted |
| `undelivered` | no verifier was delivered |
| `unvalidated` | a verifier was delivered; the anchors were not run |
| `null_accepted` | the verifier passes the untouched environment |
| `oracle_rejected` | the verifier fails the reference solution |
| `anchor_inconclusive` | an anchor that ran gave NO_VERDICT |
| `no_oracle` | null FAIL, no reference solution |
| `validated_2way` | null FAIL, oracle PASS, swap PASS (not counted as validated) |
| `validated_strict` | null FAIL, oracle PASS, swap FAIL |
| `validated` | null FAIL, oracle PASS, no swap could be constructed |

A verifier run is NO_VERDICT, never FAIL, when it exits 126, 127 or 137, times
out, could not be staged, or left no readable verdict. Shares in the summary
divide by the result rows minus `infra_error` rows.

Exit codes: 0 every task validated; 1 some task not validated; 2 configuration
error, failed host check or refused task; 3 infrastructure error (re-run the
affected tasks); 4 the harness failed with an unexpected exception (traceback
on stderr). The highest applicable code wins.

## `gavel-harness validate --from-run`

```bash
gavel-harness validate --from-run <run directory> --profile gdpval \
  [--oracle-root DIR] [--concurrency 4] [--keep-images] --out DIR
```

Reads a finished run of the original harness's one-command driver
(`manifest.json`, `tasks.txt`, `refused.json`, `tasks/` links; never its
`results.jsonl`), writes each delivered verifier back onto its original task,
plans swaps by the profile over every task of the run and runs the three
anchors. The run directory is only read and the output directory may not lie
inside it. An empty delivered `verifier.sh` counts as undelivered, and a
delivered verifier whose bytes differ from the sha256 the run recorded is
refused. An undelivered task whose deciding attempt failed on infrastructure is
an `infra_error` row, not `undelivered`: no trial collected, a job that did not
complete or a cancelled trial (`harbor_internal`), a rate-limit exception
(`rate_limited`), an endpoint exception (`endpoint_unavailable`), or another
exception before the agent started (`env_build_failed`).

## `gavel-harness matrix`

```bash
gavel-harness matrix --registry registry.json --per-family 1 --seed 0 \
  --model ... --base-url ... --api-key-env ... --out DIR
```

Samples `--per-family` tasks from every family of the registry (`--family`
restricts it), fetches each at its pinned commit and runs `gen --validate` on
it, one task at a time under `runs/`. Each task appends one row to
`matrix.jsonl`, refusals and infrastructure failures of the task included,
and `SUPPORT_MATRIX.md` is rewritten after every row.

## `gavel-harness doctor`

Checks, each reported as one line and recorded in `run.json` by the commands
that start runs:

| Check | Fails when |
|---|---|
| `ablation_switches` | a `VERITAS_NO_*`, `VERITAS_*_BARE` or `VERITAS_PROMPTS_DIR` variable is set |
| `repo_clean` | the harness has uncommitted changes (`--allow-dirty` accepts them, and says so) |
| `harbor_pin` | the installed Harbor is not 0.21.0 at commit 2fe1615 by file content |
| `docker` | the Docker daemon or the compose plugin does not answer |
| `compose_override` | `docker compose config` merges a package's own compose file into a generation trial's project: Docker Compose before 2.24.4 ignores the `!override` tag of the generation overlay without an error (`gen`, `matrix` and `doctor`; `validate` runs no generation) |
| `verifier_egress` | the verifier phase must be offline but the host cannot enforce it |
| `rubric_mount` | the evidence surface needs the rubric library and it is missing or changed |
| `endpoint` | one minimal request to the endpoint fails |
| `meter_reachable` | a container cannot reach the metering proxy |

## Docker resources

The main container of every trial a run starts carries the label
`veritas.run=<run id>` (`--run-id`, default: the output directory name and a
random suffix). Other containers of a trial (Harbor's egress-control sidecar,
and under the anchors the services of a task's own compose file) carry no run
label; they belong to the trial's compose project `<trial>__env` (lower-cased),
and Harbor removes them with the trial. Trial images are named `<trial>__env-main` by Harbor; a
run removes the ones it built when it ends, as the profile's
`[anchor] keep_images` or `--keep-images`/`--no-keep-images` says. Nothing is
pruned.
