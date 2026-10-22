# Portable Gavel runner

This directory executes one frozen VerifierBench run. Setup is performed by the top-level launcher. The official HF data, public reconstruction, native backend environments, matched Python generation image, and original Gavel harness must be ready before `start.py` runs.

```bash
export VGB_RUN_CONFIG=/absolute/workspace/run-config.json
export OPENAI_API_KEY='your key'  # use the environment name declared in config
python runner/start.py
python runner/runtime.py
python runner/metrics.py
```

Use the configured generation Python for `start.py` and the configured scoring Python for `metrics.py`. The top-level launcher selects these automatically.

`config.py` requires workspace, harness_root, generation_python, scoring_python, model, generation_image, generation_image_id, generation_site_packages_sha256, api_base_url, and api_key_env. Paths are absolute and credentials are never stored in config. The default protocol is Responses and the default model reasoning effort is medium. No model API is called by package preparation or by status/metrics commands.

`prepare.py` verifies the runtime manifest, uses the original Gavel composer, seals 222 public task packages, and freezes source/config bindings. It refuses to import prior experiment state.

`start.py` sets up network isolation without root and without host firewall rules, then starts a single dispatcher:

- It creates a workspace-specific internal Docker network with `com.docker.network.bridge.inhibit_ipv4=true`, so the host has no address on it, and a separate egress network.
- The fixed-upstream model proxy runs as a container attached to both: to the private network under the alias `vgb-proxy`, and to the egress network to reach the model endpoint. The upstream key is only in the proxy container's environment; task containers receive a local proxy token.
- Before dispatch, a health-check container on the private network must reach the proxy's `/healthz` and must fail to connect to the host's gateway address and to the model endpoint; otherwise `start.py` refuses to run.
- Task containers join only the private network and run with `NET_RAW` dropped, so they cannot reach the host or arbitrary network destinations.

This mechanism needs Docker Engine 26.x (tested on 26.1.4). On Docker 28 and newer the internal network has no IPAM gateway and the isolation check fails.

`dispatch.py` retains a six-worker maximum, conservative memory reservations, the 100 GiB start gate / 50 GiB runtime guard, CPU load guard, and persistent adaptive 429 cooldown. Existing live workers are adopted using PID, boot ID, start ticks and argv. Terminal tasks are never repeated. An orphan claim, incomplete startup, upstream protocol denial, or partial replay requires review; it is never silently retried.

`task_worker.py` uses the real Gavel session, collects the declared `checker.py` and `verifier_helpers` files byte-for-byte, and invokes the original suite replay script. AST tasks run one physical round, state/code tasks three. Runtime execution errors remain errors; no failure is fabricated from them. Raw generation/replay outputs stay in this workspace.

`metrics.py` verifies the current run's config, sources, frozen views, artifact hashes, replay receipts and decision audits. It calls original `paper_score.aggregate` on completed tasks only. AST's single result is represented in all three aggregation rounds, one whole median-BA round is selected, and all category metrics use that same round. It never imports earlier experiment scores or fills missing tasks with zero.

