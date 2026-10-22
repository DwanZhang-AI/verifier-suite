<div align="center">

<img src="assets/banner.svg" alt="verifier-suite：谁来验证 verifier？" width="100%">

### 公正评判 agent 的工作

[📄 **论文**](https://arxiv.org/abs/2610.28679) &nbsp;·&nbsp;
[🌐 **项目主页**](https://verifierbench.github.io/) &nbsp;·&nbsp;
[🤗 **数据集**](https://huggingface.co/datasets/Catherine1213/VerifierBench) &nbsp;·&nbsp;
[🛠️ **Gavel**](gavel/) &nbsp;·&nbsp;
[📊 **结果**](#-verifierbench-上的结果) &nbsp;·&nbsp;
[🚀 **快速开始**](#-快速开始)

[![arXiv](https://img.shields.io/badge/arXiv-2610.28679-b31b1b?style=flat-square)](https://arxiv.org/abs/2610.28679)
[![Dataset](https://img.shields.io/badge/%F0%9F%A4%97%20HF-Dataset-ffcc4d?style=flat-square)](https://huggingface.co/datasets/Catherine1213/VerifierBench)
[![Python](https://img.shields.io/badge/Python-3.12%2B-0F4D92?style=flat-square&logo=python&logoColor=white)](gavel/pyproject.toml)
[![License](https://img.shields.io/badge/License-Apache--2.0-16776F?style=flat-square)](LICENSE)

[English](README.md) | **中文**

</div>

---

## 🔥 最新动态

- **[2026 年 10 月]** 📊 **GPT-6-astra + Gavel 在 VerifierBench 上达到 68.3 BA_norm**，在所有配置中排名第一，高于论文中的每一种 harness。[查看结果](#-verifierbench-上的结果)
- **[2026 年 10 月]** 🧪 **一键套件**：一条命令在 VerifierBench 上复现 Gavel，不需要 root。[使用指南](verifierbench/REPRODUCE_zh.md)
- **[2026 年 10 月]** 🛠️ **Gavel** harness 在本仓库发布：一条命令为 Harbor 任务生成、写回并验证 verifier。
- **[2026 年 10 月]** 📄 **VerifierBench** 发布：[论文](https://arxiv.org/abs/2610.28679)、[数据集](https://huggingface.co/datasets/Catherine1213/VerifierBench)和[项目主页](https://verifierbench.github.io/)。

## 💡 一句话概括

能自我改进的 agent 会自己出题、自己解题，**还会自己写给答案发奖励的 verifier**。verifier 一旦写错，它经手的每一次奖励、每一条训练数据都会跟着错。

- **VerifierBench** 测量 agent 写的 verifier 到底有多可靠。结论是：太严了。它们拒掉正确解的次数，远多于放过错误解的次数。
- **Gavel** 是一套 harness，让 verifier 从它判定时真正能看到的证据出发来写检查：任务要求什么就查什么，不多加条件。

<div align="center">
<table>
  <tr>
    <td align="center" width="25%"><h3>222</h3>道题，来自 6 个 agent benchmark</td>
    <td align="center" width="25%"><h3>4,993</h3>个隐藏用例，含 798 个攻击</td>
    <td align="center" width="25%"><h3>36</h3>个模型 × harness 组合</td>
    <td align="center" width="25%"><h3>68.3 / 100</h3>VerifierBench 第一名：<br>GPT-6-astra + Gavel</td>
  </tr>
</table>
</div>

## 🔍 VerifierBench

<p align="center">
  <img src="assets/verifierbench_overview.png" alt="VerifierBench 总览：源任务、构造的正负候选、V4V 筛查、verifier 生成与评测" width="100%">
</p>

VerifierBench 只给 agent 解题者能拿到的东西：任务说明和环境，让它写一个可执行的 verifier。然后用这个 verifier 从没见过的隐藏用例来检验它。

- 🧩 **222 道题**，来自 BFCL v4、ACEBench、τ²-bench、AppWorld、AgentDojo 和 SWE-bench Verified，覆盖工具调用、环境状态和代码修改三类验证。
- 🧪 **4,993 个隐藏用例**：参考解、1,344 个合法变体、2,629 个普通错误，以及 798 个利用检查漏洞或伪造成功信号的攻击。
- 🛡️ **V4V（Verifier4Verifier）**：用重放、可重复性、来源追溯、输入与标签一致性、平凡基线和变异测试六项检查，筛查每个源 verifier 和用例集，之后才信任它的标签。
- 🤖 **36 个组合**：19 个模型跑在同一个通用 harness 上，另有 Claude Code、Codex、Gemini CLI、OpenClaw 和 mini-swe-agent。

## 🛠️ Gavel：从证据出发生成 verifier

既然模型外面的 harness 能让分数相差二十多分，harness 就值得专门设计。**Gavel** 是面向 [Harbor](https://github.com/harbor-framework/harbor) 任务的 verifier 生成 harness：一条命令为每道题闭卷生成 verifier，把它作为 `tests/` 写回任务，再做验证。在 VerifierBench 上，GPT-6-astra 用 Gavel 得到 **68.3**，用 Pi 是 62.1，用 Codex 是 58.0，在所有配置中排名第一（[查看结果](#-verifierbench-上的结果)）。

<table>
  <tr>
    <td width="50%" valign="top"><b>🔎 证据优先</b><br>在写任何检查之前，agent 先弄清楚 verifier 判定时能看到什么：终态、起始快照、对话记录。它只检查这些证据能见证的事情；见证不了的要求直接跳过，不去猜。</td>
    <td width="50%" valign="top"><b>🎯 不多加条件</b><br>每个 verifier 都遵守 9 条核心准则：判结果，不判实现方式；用仍能区分对错的最弱比较；不因措辞、顺序或格式这类差别拒掉实质正确的解。另有一个收录 19,603 条带出处领域规则的库，补上任务里没写明的要求。</td>
  </tr>
  <tr>
    <td width="50%" valign="top"><b>✅ 先确认能跑</b><br>生成结束后，harness 会实际运行这个 verifier。如果它运行崩溃，或者在没做任何修改的起始状态上也判通过，agent 会拿到诊断信息，有一次修正机会。</td>
    <td width="50%" valign="top"><b>⚖️ 判不了就直说</b><br>判决分 PASS、FAIL、NO_VERDICT 三种，运行出错永远不会被当成“要求没满足”。</td>
  </tr>
</table>

### ⚔️ 同一道题的对照

同一道题，同一个 agent（OpenCode），同一个模型（GLM-5.2），唯一的区别是有没有 Gavel。

**题目：** 信用分 540 的 Bob 想办一张信用卡，要求外币交易手续费不超过 1.5%、最低还款比例不超过 1.5%，并且支持虚拟卡管理。符合条件的是 EcoCard，正确的结果是 Bob 申请了这张卡。

<table>
  <tr>
    <th width="50%">❌ 没有 Gavel</th>
    <th width="50%">✅ 使用 Gavel</th>
  </tr>
  <tr>
    <td valign="top">

```python
if not used_kb_search:
    return False
if not communicated:
    return False
if db_before != db_after:
    return False
return True
```

要求**数据库不能有任何变化**，这是任务里根本没有的条件。结果 Bob 合法的 EcoCard 申请被拒，空对话也被拒：它什么都拒。

</td>
    <td valign="top">

```python
for app_id in new_ids:
    ...
    name_ok = ("nakamoto" in name) or ("bob" in name)
    card_ok = "eco" in card_type
    status_ok = status in ("APPROVED", "PENDING")
    if name_ok and card_ok and status_ok:
        return True
return False
```

先从银行知识库推出符合条件的是 EcoCard，再检查终态里有没有 **Bob 新提交的 EcoCard 申请**，两种申请状态都接受。正确解通过，空对话被拒。

</td>
  </tr>
</table>

<sub>以上是 τ²-bench 银行任务 006 生成的 verifier 摘录，来自 Gavel 的开发实验。</sub>

### 📊 VerifierBench 上的结果

| 模型 | Harness | BA_norm ↑ | TPR ↑ | TNR ↑ | FPR_h ↓ |
|---|---|---:|---:|---:|---:|
| **GPT-6-astra** | **Gavel** | **68.3** | **84.1** | 84.2 | 18.2 |
| Claude Opus 4.8 | Claude Code | 66.2 | 75.8 | 90.4 | 7.8 |
| GPT-6-astra | Pi | 62.1 | 67.4 | 94.6 | 7.4 |
| GPT-6-astra | Codex | 58.0 | 66.2 | 91.8 | 9.2 |
| Claude Opus 4.8 | Pi | 54.0 | 67.7 | 86.3 | 13.5 |
| Kimi K3 | Pi | 53.4 | 70.2 | 83.2 | 13.4 |
| GPT-5.6-sol | Pi | 52.9 | 56.8 | 96.0 | **0.8** |
| GPT-5.6-terra | Pi | 52.9 | 56.5 | **96.3** | 3.6 |
| Gemini 3.5 Flash | Gemini CLI | 50.7 | 59.2 | 91.5 | 7.7 |
| GLM-5.2 | Pi | 48.8 | 68.1 | 80.8 | 12.1 |
| Doubao Seed 2.1 Pro | Pi | 46.8 | 57.0 | 89.9 | 11.4 |
| GPT-5.5 | Pi | 46.6 | 61.6 | 85.1 | 9.9 |
| DeepSeek V4 Pro | Pi | 44.8 | 65.5 | 79.2 | 10.1 |
| DeepSeek V4 Flash | Pi | 40.5 | 60.7 | 79.8 | 8.0 |
| Qwen3.7 Plus | Pi | 40.2 | 57.6 | 82.6 | 13.6 |
| Gemini 3.5 Flash | Pi | 35.7 | 52.4 | 83.3 | 13.2 |
| Kimi K2.6 | Pi | 35.2 | 52.5 | 82.7 | 4.6 |
| GPT-5.6-terra | Codex | 31.0 | 39.2 | 91.8 | 4.7 |
| GPT-5.5 | Codex | 30.3 | 41.2 | 89.1 | 6.2 |
| Doubao Seed 2.0 Code | Pi | 29.7 | 45.0 | 84.8 | 12.3 |
| Doubao Seed 2.0 Lite | Pi | 26.8 | 41.1 | 85.7 | 10.5 |
| GPT-5.6-sol | Codex | 26.2 | 32.3 | 93.9 | 1.0 |
| Doubao Seed 2.0 Pro | Pi | 22.8 | 27.4 | 95.4 | 6.8 |
| GPT-5.1 | Pi | 22.2 | 35.2 | 87.1 | 9.7 |
| Gemini 2.5 Pro | Pi | 14.2 | 31.7 | 82.5 | 4.0 |
| Doubao Seed 2.0 Mini | Pi | 10.6 | 21.1 | 89.5 | 3.7 |
| Gemini 2.5 Pro | Gemini CLI | 5.0 | 23.7 | 81.3 | 3.5 |
| 恒定 / 随机 | — | 0.0 | — | — | — |

各行都在 VerifierBench 的 222 道题上评测，按 BA_norm = TPR + TNR − 100 排序。除 Gavel 外，其余各行来自 VerifierBench 论文：Table 2 的 19 个 Pi harness 配置，以及 Table 3 的 7 个原生 harness 配置（其 TPR、TNR 和 FPR_h 取自 Table 12）。加粗表示表中这些行里每列最好的值（FPR_h 取最低）。

> [!NOTE]
> 对同一个模型，Gavel 把 TPR 从 67.4 提高到 84.1（+16.7），这正是 VerifierBench 在每个模型上都发现的弱点；代价是拒错能力有所下降：TNR 84.2 对 94.6，FPR_h 18.2 对 7.4。

### 🧪 在 VerifierBench 上复现

一条命令完成全部流程：下载冻结的 VerifierBench 数据（固定 Hugging Face 版本），搭建原生环境（τ²-bench、AgentDojo、AppWorld，以及按 digest 固定的 47 个 SWE 镜像），用 Gavel 为每道题生成 verifier，用 VerifierBench 原执行器回放全部 4,993 个候选，并报告 BA_norm、TPR、TNR 和 FPR_h。

```bash
cd verifierbench/oneclick
export OPENAI_API_KEY=...
./run.sh run --work-dir /path/to/new-workspace \
  --model gpt-6-astra --api-base-url https://api.openai.com/v1 --api-key-env OPENAI_API_KEY
./run.sh status --work-dir /path/to/new-workspace
```

> [!IMPORTANT]
> 需要 Linux x86_64、Python 3.9 及以上、Docker Engine 26.x（28 及以上版本不可用）、git 和 bubblewrap；工作目录所在磁盘**和** Docker 数据目录都要有至少 100 GiB 空闲；需要能访问 Hugging Face、PyPI、GitHub、npm 和 Docker Hub。不需要 root 或 sudo。端点不支持 Responses 接口时，加 `--api-protocol chat_completions`。完整说明见 [verifierbench/REPRODUCE_zh.md](verifierbench/REPRODUCE_zh.md)。

### 🚀 快速开始

Gavel 需要 Linux、Python 3.12 及以上，以及 Docker 和 Compose 2.24.4 及以上版本。

```bash
cd gavel
pip install -e .

export OPENAI_API_KEY=...
gavel-harness doctor --model openai/gpt-6-astra \
  --base-url https://api.openai.com/v1 --api-key-env OPENAI_API_KEY
gavel-harness gen examples/hello-terminal --model openai/gpt-6-astra \
  --base-url https://api.openai.com/v1 --api-key-env OPENAI_API_KEY \
  --validate --out ./out/r1
```

> [!TIP]
> 任何兼容 OpenAI chat 接口的端点都可以用；换用其他服务商时，改 `--model` 和 `--base-url` 即可。API key 从你指定的环境变量读取，不会写进任何输出文件。当前版本支持终态类和交付物类任务，执行器为 OpenCode；范式、配置文件和运行目录的说明见 [gavel/README.md](gavel/README.md) 和 [gavel/docs](gavel/docs/)。

## 📁 仓库内容

| 路径 | 内容 |
|---|---|
| [`verifierbench/`](verifierbench/) | VerifierBench 论文（[arXiv](https://arxiv.org/abs/2610.28679)、[PDF](verifierbench/VerifierBench.pdf)）和摘要 |
| [`verifierbench/oneclick/`](verifierbench/oneclick/) | 一键套件：在 VerifierBench 上运行 Gavel，用原执行器计分 |
| [`verifierbench/REPRODUCE_zh.md`](verifierbench/REPRODUCE_zh.md) | 套件的使用方法、检查内容和计分口径 |
| [`gavel/`](gavel/) | Gavel harness：源码、示例和文档 |
| [`assets/`](assets/) | 本页用到的图 |

## ✍️ 引用

如果这项工作对你有帮助，请引用：

```bibtex
@article{yin2026verifierbench,
  title   = {VerifierBench: Benchmarking the Generation of Executable Verifiers for LLM Agents},
  author  = {Yin, Jianing and Chen, Ziyi and Wang, Hao and Sun, Yiyou and Jin, Zijian and Song, Dawn and Zhang, Daoan},
  journal = {arXiv preprint arXiv:2610.28679},
  year    = {2026},
  url     = {https://arxiv.org/abs/2610.28679}
}
```

## 📜 许可证

本仓库以 [Apache License 2.0](LICENSE) 发布。第三方内容沿用各自的许可，列在 [`gavel/NOTICE`](gavel/NOTICE) 和 [`verifierbench/oneclick/NOTICE.md`](verifierbench/oneclick/NOTICE.md) 中。
