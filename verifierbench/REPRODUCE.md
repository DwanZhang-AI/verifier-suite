# Reproduce Gavel on VerifierBench

**English** | [中文](REPRODUCE_zh.md)

The one-click suite in [`oneclick/`](oneclick/) runs Gavel on all 222 VerifierBench tasks and scores the result with the original VerifierBench executor. One command does everything; this page explains what it needs, what it does, and how results are scored.

## What the suite does

1. **Data.** Downloads VerifierBench at the pinned Hugging Face revision `8e5d72dfc112aaffca75934a0caaa22067ba8df1` and checks all 66 files against their SHA-256.
2. **Native environments.** Installs a managed CPython 3.12.14; AppWorld 0.1.3.post1 and AgentDojo 0.1.35 from PyPI; AppWorld data through its official CLI; τ²-bench from a pinned upstream commit; SWE-bench data from a pinned Hugging Face revision; and the 47 SWE task images by immutable RepoDigest.
3. **Generation image.** Builds one image with Node 22.23.3, OpenCode 1.18.3 and the same Python interpreter and packages used for scoring.
4. **Generation.** Gavel writes one verifier per task. The generation container gets only the public task and the allowed environment capability; candidates and labels never enter it.
5. **Scoring.** Replays every candidate with the original VerifierBench executor and reports BA_norm, TPR, TNR and FPR_h.

Any mismatch in frozen inputs, native tasks, images or source files stops the run and prints the reason. Nothing is skipped silently.

## Requirements

- Linux x86_64, Python 3.9 or later (only for the bootstrap), Docker Engine, git and bubblewrap (`bwrap`).
- Docker Engine 26.x (tested on 26.1.4). Docker 28 and later do not work: an internal network created with `com.docker.network.bridge.inhibit_ipv4` has no gateway there, and the isolation check fails. Other versions are untested.
- At least **100 GiB free on both** the workspace disk and Docker's data root (`docker info --format '{{.DockerRootDir}}'`). The suite checks both before setup and again before every SWE image pull. The SWE images can take more than that.
- Network access to Hugging Face, PyPI, GitHub, npm and Docker Hub.
- No root or sudo, and no host firewall changes.

> [!TIP]
> No root for bubblewrap? If `unshare --user --map-root-user true` succeeds, unprivileged user namespaces are enabled and an unpacked distribution package works without installing it, for example `apt-get download bubblewrap && dpkg -x bubblewrap_*.deb bwrap-root`, then put `bwrap-root/usr/bin` on `PATH`.

## Commands

Use a new, empty directory for every run. Provide the key only through an environment variable.

```bash
cd verifierbench/oneclick
export OPENAI_API_KEY=...

# Prepare everything, call no model
./run.sh prepare --work-dir /path/to/new-workspace \
  --model gpt-6-astra --api-base-url https://api.openai.com/v1 --api-key-env OPENAI_API_KEY

# Prepare (reusing verified steps) and start the run in the background
./run.sh run --work-dir /path/to/new-workspace \
  --model gpt-6-astra --api-base-url https://api.openai.com/v1 --api-key-env OPENAI_API_KEY

# Progress and metrics
./run.sh status --work-dir /path/to/new-workspace
```

| Option | Default | Meaning |
|---|---|---|
| `--work-dir` | required | A new, empty directory used only by this run |
| `--model` | `gpt-6-astra` | Model name sent to the endpoint |
| `--api-base-url` | required for `prepare` and `run` | HTTPS base URL of an OpenAI-compatible endpoint, without credentials |
| `--api-key-env` | `OPENAI_API_KEY` | Name of the environment variable that holds the key; the key is never written to the configuration or any output |
| `--api-protocol` | `responses` | `responses` or `chat_completions`; use `chat_completions` if the endpoint has no Responses API |
| `--max-workers` | `6` | Tasks generated at the same time, 1 to 6 |

## During a run

- `run` verifies the scheduler, prints `started` and returns; the experiment continues in the background. Check it with `status`.
- The scheduler log is `run/controller.log` in the workspace. The model proxy runs in the container `vgb-proxy-<run id>`; read its log with `docker logs`. Every model request is recorded in `responses-transport-audit.jsonl` (task, status and hashes only, no content).
- Rate limits (HTTP 429) are retried with adaptive back-off. Memory, load and disk gates hold new tasks when the host is short.
- A task that the model gateway refuses (HTTP 403) keeps the first refusal as evidence and is never retried.

## Network isolation

- Generation containers sit on an internal Docker network on which the host has no address, so they can reach neither the host nor the internet.
- The only reachable service is the model proxy, a container attached to that network (alias `vgb-proxy`) and to a separate egress network. The key is passed to this container as an environment variable, so anyone who can run `docker inspect` on the host can read it.
- Every start proves the isolation from inside the network: connecting to the host and to the model endpoint must fail, or the run does not start.
- Generation containers run without the `NET_RAW` capability.

## How results are scored

- For each task, TPR is the share of valid candidates the verifier accepts and TNR the share of invalid ones it rejects. Both are averaged over the 222 tasks, and BA_norm = TPR + TNR − 100. FPR_h is the share of attack candidates accepted.
- Tool-call tasks are replayed once; state and code tasks are replayed three times. The complete round with the median BA is used for every reported metric.
- Execution errors and ABSTAIN earn no credit and are reported separately; they are never turned into FAIL.
- The report reads only this workspace's results. Partial coverage is labelled as an interim result.

## Resuming

Run the same command with the same workspace. Verified steps are reused, running processes are adopted, and finished tasks are not run again. If the suite cannot prove whether a unit of work already ran, it stops and asks for inspection instead of repeating it. A workspace is bound to the suite version that created it.

## Workspace layout

| Path | Contents |
|---|---|
| `runtime/` | The runtime copied from the suite, plus the downloaded dataset |
| `sources/` | Native benchmark sources and data |
| `generation-inputs/` | Public task inputs for generation |
| `evaluator-views/` | Candidates and labels, read only by the scorer |
| `run-config.json` | The frozen configuration of this run |
| `run/` | Generation results, delivered verifiers, replays, errors and SHA receipts |

## Provenance

The GPT-6-astra + Gavel numbers in the main README were produced with the original release of this suite (archive SHA-256 `13802403127445ff…`). This repository ships a revision (`SUITE_MANIFEST.json` SHA-256 `a07a4765b62f223a…`). Its changes: generation-side network isolation no longer needs root; when a capability call's result would reveal oracle content, the generating agent gets a fixed error message instead of one that quotes it; an interrupted prepare resumes where it stopped; the model proxy accepts a longer connection queue and keeps one header fewer from refused responses; in the vendored harness, internal references were removed from comments, unused internal default values were replaced, and two modules and some identifiers were renamed without changing the logic; text and reports use the name Gavel. Scoring replay and the metrics are unchanged. [`oneclick/validation.json`](oneclick/validation.json) lists what was verified for each version.

## Troubleshooting

| Message | What to do |
|---|---|
| `Setup requires at least 100 GiB free disk` | Free space on the workspace disk |
| `Less than 100 GiB available on workspace or Docker storage before a new SWE image pull` | Free space on the workspace disk and on Docker's data root |
| `Missing required host tool: bwrap` | Install bubblewrap or unpack it as in the tip above |
| `Private network gives the host an address` | Docker does not apply `inhibit_ipv4`; use Docker Engine 26.x |
| `Private network is not isolated` | Something routes the private network to the host or the internet; inspect the network before retrying |
| `Proxy container exited` | Read `docker logs vgb-proxy-<run id>` |
| HTTP 404 from the endpoint | The endpoint likely lacks the Responses API; use `--api-protocol chat_completions` |
