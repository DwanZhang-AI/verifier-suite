# VerifierBench × Gavel one-click suite

[English](#english) | [中文](#中文)

## English

This suite runs Gavel on VerifierBench on one Linux x86_64 host. It prepares the environments from a pinned Hugging Face dataset revision, generates a verifier for every task, replays the candidates and computes the paper's metrics. The default model is `gpt-6-astra`. The benchmark has 222 tasks, 4,993 candidates and 7 categories.

### Requirements

- **Host:** Linux x86_64 with Python 3.9 or newer, Docker Engine, Git and bubblewrap (`bwrap`). The current user must be able to use Docker. No root or sudo is needed, and the host firewall is not modified.
- **Docker version:** Docker Engine 26.x is supported; the suite was tested on 26.1.4. Docker 28 and newer are known not to work. On those versions, an internal network created with `com.docker.network.bridge.inhibit_ipv4` has no IPAM gateway, so the start-time isolation check fails. Other versions are untested.
- **Disk:** at least 100 GiB free on the workspace filesystem and on Docker's data root (`docker info --format '{{.DockerRootDir}}'`, usually `/var/lib/docker`). Setup and the image build refuse to start below that, and the dispatcher launches a new task only while both still have 100 GiB free. SWE task images can take more space.
- **Memory:** the generation image build needs at least 6 GiB `MemAvailable`.
- **Network for setup:** Hugging Face, PyPI, GitHub, npm and the container registries.

### Run with one command

```bash
export OPENAI_API_KEY='your model API key'
./run.sh run --work-dir /path/to/workspace \
  --model gpt-6-astra \
  --api-base-url https://api.openai.com/v1 \
  --api-key-env OPENAI_API_KEY
```

Use a new, dedicated work directory; do not point it at another experiment. The key comes from an environment variable and is never written to the config or the release. The API uses the Responses protocol by default. Generation and scoring both run on this host; the suite does not move work to other machines and creates no scheduled jobs.

`run` verifies the dispatcher's identity, prints `started` and exits; the experiment continues in the background. Use `status` below to follow it. The dispatcher log is `run/controller.log` in the work directory. The model proxy runs in the container `vgb-proxy-<run ID>`; read its log with `docker logs`. Every forwarded model request is recorded in `responses-transport-audit.jsonl` in the work directory (task, status and hashes only, no content).

The model proxy runs as a container. It is attached to this workspace's private network (alias `vgb-proxy`) and to a separate network that only it uses to reach the model endpoint. The key reaches this container through its environment, so users who can run `docker inspect` can see it. The private network is an internal network, and the host has no IPv4 address on its bridge, so generation containers can reach neither the host nor the internet; they can reach only the proxy.

At start, a short-lived health-check container from the pinned generation image calls the proxy's `/healthz` on the private network and proves the isolation: connections from the private network to the host (the network's gateway address) and to the model endpoint must both fail, otherwise the run refuses to start. The container is removed afterwards. It carries no key, mounts or candidates, is not an experiment task and calls no model.

To prepare the environments without calling the model:

```bash
./run.sh prepare --work-dir /path/to/workspace \
  --model gpt-6-astra \
  --api-base-url https://api.openai.com/v1 \
  --api-key-env OPENAI_API_KEY
```

To show the status and metrics of this run:

```bash
./run.sh status --work-dir /path/to/workspace
```

### Where the environment comes from

- **VerifierBench data and reconstruction scripts:** `Catherine1213/VerifierBench` at the pinned commit `8e5d72dfc112aaffca75934a0caaa22067ba8df1`. Each of the 66 files is checked against its SHA in `dataset-lock.json`.
- **Executors and the Gavel framework:** the suite ships the aligned runtime, the generation adapter and the original framework code. The Hugging Face repository does not publish the full runtime or the native environment images, so this bundled code is not a Hugging Face image.
- **Python and toolchain:** CPython 3.12.14 is installed automatically. The generation image copies the same interpreter and the scoring dependencies, and the suite checks the interpreter, the standard library, the dependency inventory, the client and the actual imports. Node 22.23.3 and OpenCode 1.18.3 are pinned.
- **Native environments:** AppWorld 0.1.3.post1 and AgentDojo 0.1.35 are installed from the official PyPI; AppWorld data is downloaded and rebuilt with its official CLI. τ² is built from a pinned commit of its official source. The SWE data comes from a pinned Hugging Face commit, and the 47 task images are pulled by immutable RepoDigest.

These sources are recorded separately rather than replaced by a single "Hugging Face environment package". Model calls start only after environment preparation passes. Any mismatch in frozen inputs, native tasks, images or source checks stops the run and shows the reason.

### Execution and metrics

- Gavel's original composer and session generate `checker.py` and the declared `verifier_helpers`; replay uses the original VerifierBench executor.
- Generation sees only the public task statement and the permitted environment capabilities; candidates and labels never enter the generation container. Helper modules are delivered byte for byte, and the public environment capabilities match the scoring side.
- At most 6 tasks run concurrently, with adaptive 429 back-off and memory, load and disk gates. Each workspace has its own lock, private network, egress network, proxy container and run identity; generation containers drop the `NET_RAW` capability. Repeating the start command does not add executions: live processes are adopted by identity, and finished tasks are never rerun. Upstream refusals and orphaned or incomplete execution units are kept for review; they are never bypassed or repeated automatically.
- AST categories are replayed once; state and code categories are replayed three times. Overall results weight tasks equally and use the **whole round** with the median BA; the overall table, the per-category table and all four metrics use that same round.
- Outputs are `BA_norm`, `TPR`, `TNR` and `FPR_h`, with `BA_norm = TPR + TNR - 100` (in percent). Execution errors and ABSTAIN are handled as in the original scorer and reported separately; no FAIL is invented and nothing is filled with zero.
- The report reads only this workspace's run. Partial coverage is labelled as an intermediate result; no earlier experiment results, paper scores or pre-made score tables are imported.

### Files and recovery

The workspace contains `runtime/`, `sources/`, `generation-inputs/`, `evaluator-views/`, `run-config.json` and `run/`. `run/` keeps this run's generations, deliveries, replays, errors and SHA receipts. The first preparation freezes the configuration and sources; later calls of the same command check consistency, so the model, inputs, scorer or existing results cannot change silently.

If preparation is interrupted, run it again with the same work directory. Verified steps are reused; if a conflict appears or the suite cannot prove whether an execution unit already ran, it stops and asks for a check instead of repeating blindly. Keep the original artifacts and error records.

### Validation scope

See `validation.json`. Validation covers the pinned Hugging Face download and SHAs, the original framework packaging, dependency and environment boundaries, task isolation and the metric definitions. Validating the release calls no model and is not another full 222-task evaluation.

## 中文

在 Linux x86_64 机器上，从固定的 Hugging Face 数据版本准备环境，生成 verifier，回放候选并计算论文指标。默认模型为 `gpt-6-astra`，共 222 题、4,993 个候选、7 个类别。

### 运行要求

- **主机**：Python 3.9 或更新版本、Docker Engine、Git 和 bubblewrap（`bwrap`），并确认当前用户能使用 Docker。不需要 root 或 sudo，也不修改主机防火墙。
- **Docker 版本**：支持 Docker Engine 26.x，已在 26.1.4 上验证。Docker 28 及以上已知不可用：这些版本中用 `com.docker.network.bridge.inhibit_ipv4` 创建的 internal 网络没有 IPAM 网关，启动时的隔离检查会失败。其他版本未测试。
- **磁盘**：工作目录所在文件系统和 Docker 数据目录（`docker info --format '{{.DockerRootDir}}'`，通常是 `/var/lib/docker`）都需要至少 100 GiB 可用空间。低于该值时环境准备和镜像构建拒绝启动；调度器只在两处都仍有 100 GiB 可用时才启动新任务。SWE 任务镜像可能占用更多空间。
- **内存**：构建生成镜像需要至少 6 GiB `MemAvailable`。
- **准备阶段的网络**：需要访问 Hugging Face、PyPI、GitHub、npm 和镜像仓库。

### 一条命令运行

```bash
export OPENAI_API_KEY='你的模型服务密钥'
./run.sh run --work-dir /path/to/workspace \
  --model gpt-6-astra \
  --api-base-url https://api.openai.com/v1 \
  --api-key-env OPENAI_API_KEY
```

使用一个新的独立工作目录，不能指向已有的其他实验。密钥通过环境变量提供，不写入配置或发行包。API 默认使用 Responses 协议。生成和评分都在指定主机执行；本套件不会迁移到其他机器，也不会创建定时任务。

`run` 核验调度器身份后输出 `started` 并退出，实验继续在后台运行；使用下方 `status` 查看进度。调度日志在工作目录的 `run/controller.log`。代理在容器 `vgb-proxy-<运行 ID>` 中运行，日志用 `docker logs` 查看；每次模型请求的转发记录写在工作目录的 `responses-transport-audit.jsonl`（只记任务、状态和哈希，不记内容）。

模型代理以容器运行：它挂在本工作区的私有网络上（别名 `vgb-proxy`），另接一个只供它出网的网络；密钥通过环境变量传入这个容器，因此能执行 `docker inspect` 的用户可以看到。私有网络是 internal 网络，且主机在其网桥上没有 IPv4 地址，生成容器既访问不到主机，也访问不到外网，只能访问代理。

启动时用固定生成镜像创建一个短暂的健康检查容器，在本工作区私有网络访问代理的 `/healthz`，并证明隔离：从私有网络连接主机（网络网关地址）和模型服务地址都必须失败，否则拒绝启动；随后自动删除。它不携带密钥、挂载或候选，不属于实验任务，也不调用模型。

若只准备环境、不调用模型：

```bash
./run.sh prepare --work-dir /path/to/workspace \
  --model gpt-6-astra \
  --api-base-url https://api.openai.com/v1 \
  --api-key-env OPENAI_API_KEY
```

查看这次运行的状态和指标：

```bash
./run.sh status --work-dir /path/to/workspace
```

### 环境来源

- **VerifierBench 数据与重建脚本**：`Catherine1213/VerifierBench`，固定提交 `8e5d72dfc112aaffca75934a0caaa22067ba8df1`；66 个文件逐一校验 `dataset-lock.json` 中的 SHA。
- **执行器和 Gavel 框架**：套件包含本次对齐后的 runtime、生成适配器和原框架代码。HF 这个仓库没有发布完整 runtime 或原生环境镜像，不能把这些本地随包代码称为 HF 镜像。
- **Python / 工具链**：自动安装 CPython 3.12.14；生成镜像复制同一解释器及评分依赖，核验解释器、标准库、依赖 inventory、客户端和实际导入。Node 22.23.3、OpenCode 1.18.3 固定版本。
- **原生环境**：AppWorld 0.1.3.post1 和 AgentDojo 0.1.35 从官方 PyPI 安装；AppWorld 数据使用其官方 CLI 下载和重建。τ² 从官方源的固定提交构建；SWE 原数据来自固定 HF 提交，47 套任务镜像按不可变 RepoDigest 获取。

这些来源分开记录，不用一个虚构的“HF 环境包”替代。环境准备通过后，才会启动模型调用。任何冻结输入、原生任务、镜像或源码校验不一致都会停止并显示原因。

### 执行和结果口径

- 使用 Gavel 原 composer/session 生成 `checker.py` 及声明的 `verifier_helpers`，评分回放使用原 VerifierBench 执行器。
- 生成阶段只拿公共题面和允许的环境能力；候选及标签不放入生成容器。辅助模块按原字节交付，公开环境能力与评分侧一致。
- 最大并发 6，保留自适应 429 退避、内存/负载/磁盘门。工作区有独立锁、私有网络、出网网络、代理容器和运行身份；生成容器去掉 NET_RAW 能力。执行次数不随重复调用启动命令增加：已有活跃进程按身份接续，终态任务不重跑。上游拒绝及孤立/不完整执行单元保留为需复核，不自动绕过或重复。
- AST 类别实际回放一次，状态和代码类别实际回放三次。总体按题等权，取 BA 居中的**完整一轮**；总体、分类表以及四项指标都使用同一轮。
- 输出 `BA_norm`、`TPR`、`TNR`、`FPR_h`。`BA_norm = TPR + TNR - 100`（百分数）。执行异常/ABSTAIN 按原评分器处理，单独报告，不伪造 FAIL 或补零。
- 报告只读取该工作区本次运行结果。部分覆盖会明确标为中间结果；没有导入旧实验结果、论文分数或预制成绩表。

### 文件与恢复

工作区包含 `runtime/`、`sources/`、`generation-inputs/`、`evaluator-views/`、`run-config.json` 和 `run/`。`run/` 保存当前运行的生成、交付、回放、错误及 SHA 收据。首次准备冻结配置与源码；以后调用同一命令会检查一致性，不能偷偷改变模型、输入、评分器或已有结果。

准备中断后可用同一工作目录再次运行。已校验步骤复用；若发现冲突或无法证明执行单元是否已经运行，会停止要求检查，而不盲目重复。请保留原始产物和错误记录。

### 验证范围

详见 `validation.json`。验证包括固定 HF 数据下载与 SHA、原框架封包、依赖/环境边界、任务隔离和结果口径测试。发行包验证本身不另外调用模型，不代表又完成了一遍 222 题评测。
