# 在 VerifierBench 上复现 Gavel

[English](REPRODUCE.md) | **中文**

[`oneclick/`](oneclick/) 里的一键套件在 VerifierBench 全部 222 道题上运行 Gavel，并用 VerifierBench 原执行器计分。一条命令完成全部流程；本页说明它需要什么、做了什么、结果怎么计分。

## 套件做了什么

1. **数据。** 下载固定 Hugging Face 版本 `8e5d72dfc112aaffca75934a0caaa22067ba8df1` 的 VerifierBench，逐个核对 66 个文件的 SHA-256。
2. **原生环境。** 安装受管的 CPython 3.12.14；从 PyPI 安装 AppWorld 0.1.3.post1 和 AgentDojo 0.1.35；用 AppWorld 官方 CLI 下载其数据；从固定的上游提交构建 τ²-bench；从固定 Hugging Face 版本获取 SWE-bench 数据；按不可变的 RepoDigest 拉取 47 个 SWE 任务镜像。
3. **生成镜像。** 构建一个镜像，含 Node 22.23.3、OpenCode 1.18.3，以及与评分侧相同的 Python 解释器和依赖。
4. **生成。** Gavel 为每道题写一个 verifier。生成容器只拿到公开题面和允许的环境能力，候选和标签不会进入生成容器。
5. **计分。** 用 VerifierBench 原执行器回放每个候选，报告 BA_norm、TPR、TNR 和 FPR_h。

冻结输入、原生任务、镜像或源码任何一处校验不一致，都会停止并给出原因，不会静默跳过。

## 主机要求

- Linux x86_64、Python 3.9 及以上（只用于启动脚本）、Docker Engine、git 和 bubblewrap（`bwrap`）。
- Docker Engine 26.x（已在 26.1.4 上测试）。Docker 28 及以上版本不可用：在这些版本里，用 `com.docker.network.bridge.inhibit_ipv4` 创建的 internal 网络没有网关，隔离检查会失败。其他版本未测试。
- 工作目录所在磁盘**和** Docker 数据目录（`docker info --format '{{.DockerRootDir}}'`）都要有至少 **100 GiB** 空闲。套件在准备前、以及每次拉取 SWE 镜像前都会检查这两处。SWE 镜像实际占用可能更多。
- 能访问 Hugging Face、PyPI、GitHub、npm 和 Docker Hub。
- 不需要 root 或 sudo，也不修改主机防火墙。

> [!TIP]
> 没有 root 装不了 bubblewrap？如果 `unshare --user --map-root-user true` 能成功，说明系统允许非特权 user namespace，此时把发行版的包解出来就能用，不必安装。例如 `apt-get download bubblewrap && dpkg -x bubblewrap_*.deb bwrap-root`，再把 `bwrap-root/usr/bin` 加进 `PATH`。

## 命令

每次运行都用一个新的空目录。密钥只通过环境变量提供。

```bash
cd verifierbench/oneclick
export OPENAI_API_KEY=...

# 只准备环境，不调用模型
./run.sh prepare --work-dir /path/to/new-workspace \
  --model gpt-6-astra --api-base-url https://api.openai.com/v1 --api-key-env OPENAI_API_KEY

# 准备（复用已校验的步骤）并在后台启动运行
./run.sh run --work-dir /path/to/new-workspace \
  --model gpt-6-astra --api-base-url https://api.openai.com/v1 --api-key-env OPENAI_API_KEY

# 查看进度和指标
./run.sh status --work-dir /path/to/new-workspace
```

| 参数 | 默认值 | 含义 |
|---|---|---|
| `--work-dir` | 必填 | 只给本次运行用的新空目录 |
| `--model` | `gpt-6-astra` | 发给端点的模型名 |
| `--api-base-url` | `prepare` 和 `run` 必填 | 兼容 OpenAI 接口的 HTTPS 端点，不能带凭据 |
| `--api-key-env` | `OPENAI_API_KEY` | 存放密钥的环境变量名；密钥不会写进配置或任何输出 |
| `--api-protocol` | `responses` | `responses` 或 `chat_completions`；端点不支持 Responses 接口时用 `chat_completions` |
| `--max-workers` | `6` | 同时生成的题数，1 到 6 |

## 运行期间

- `run` 核验调度器后输出 `started` 并返回，实验在后台继续运行，用 `status` 查看。
- 调度日志在工作目录的 `run/controller.log`。模型代理在容器 `vgb-proxy-<运行 ID>` 中运行，日志用 `docker logs` 查看。每次模型请求都记录在 `responses-transport-audit.jsonl`（只记任务、状态和哈希，不记内容）。
- 遇到限流（HTTP 429）会自适应退避重试；主机内存、负载或磁盘不足时，暂停启动新题。
- 被模型网关拒绝（HTTP 403）的题，保留第一次拒绝作为证据，不再重试。

## 网络隔离

- 生成容器在一个 internal Docker 网络上，主机在这个网络上没有地址，所以生成容器既访问不到主机，也访问不到外网。
- 唯一能访问的服务是模型代理。它以容器运行，挂在这个网络上（别名 `vgb-proxy`），另接一个只供它出网的网络。密钥以环境变量的形式传给这个容器，所以主机上能执行 `docker inspect` 的人都能看到。
- 每次启动都会在网络内部验证隔离：连接主机和模型端点都必须失败，否则不开跑。
- 生成容器去掉了 `NET_RAW` 能力。

## 计分口径

- 每道题上，TPR 是 verifier 接受的合法候选比例，TNR 是它拒绝的错误候选比例。两者在 222 道题上取平均，BA_norm = TPR + TNR − 100。FPR_h 是被接受的攻击候选比例。
- 工具调用类题回放 1 次，状态类和代码类题回放 3 次；所有指标都用 BA 居中的那一轮完整结果。
- 执行错误和 ABSTAIN 不得分，并单独报告；它们不会被当成 FAIL。
- 报告只读取本工作区的结果。只覆盖部分题时，会标为中间结果。

## 中断后续跑

用同一个工作目录再执行一次同样的命令即可。已校验的步骤会复用，正在运行的进程会被接管，已结束的题不会重跑。如果套件无法确认某个执行单元是否已经运行过，就会停下来要求检查，不会盲目重复。工作目录和创建它的套件版本绑定。

## 工作目录结构

| 路径 | 内容 |
|---|---|
| `runtime/` | 从套件复制的运行时，以及下载的数据集 |
| `sources/` | 原生 benchmark 的源码和数据 |
| `generation-inputs/` | 生成侧的公开题面 |
| `evaluator-views/` | 候选和标签，只有计分器读取 |
| `run-config.json` | 本次运行冻结的配置 |
| `run/` | 生成结果、交付的 verifier、回放、错误记录和 SHA 收据 |

## 出处

主 README 里 GPT-6-astra + Gavel 的结果由本套件的原始版本跑出（压缩包 SHA-256 `13802403127445ff…`）。本仓库附带的是修订版（`SUITE_MANIFEST.json` SHA-256 `a07a4765b62f223a…`），改动如下：生成侧的网络隔离不再需要 root；能力调用的返回结果会泄露 oracle 内容时，生成 agent 收到的是固定的报错信息，不再引用泄露的内容；prepare 中断后从中断处继续；模型代理的连接队列加长，被拒响应少保留一个响应头；打包的框架代码删除了注释里的内部信息，替换了用不到的内部默认值，并给两个模块和部分标识符改了名，逻辑不变；文字和报告中改用 Gavel 这个名字。评测回放和计分都没有改。各版本做过哪些验证，见 [`oneclick/validation.json`](oneclick/validation.json)。

## 常见问题

| 报错 | 处理 |
|---|---|
| `Setup requires at least 100 GiB free disk` | 清理工作目录所在磁盘 |
| `Less than 100 GiB available on workspace or Docker storage before a new SWE image pull` | 同时清理工作目录所在磁盘和 Docker 数据目录 |
| `Missing required host tool: bwrap` | 安装 bubblewrap，或按上面的提示解包使用 |
| `Private network gives the host an address` | Docker 没有应用 `inhibit_ipv4`，请使用 Docker Engine 26.x |
| `Private network is not isolated` | 有路由让私有网络能访问主机或外网，先检查网络再重试 |
| `Proxy container exited` | 查看 `docker logs vgb-proxy-<运行 ID>` |
| 端点返回 HTTP 404 | 端点可能不支持 Responses 接口，改用 `--api-protocol chat_completions` |
