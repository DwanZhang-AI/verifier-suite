# Notice / 来源与许可

## English

This suite is part of the verifier-suite repository and is licensed under the Apache License 2.0, the repository's license (see `LICENSE` at the repository root). That license covers the suite's own code and text: the runner, the VerifierBench runtime, the bootstrap scripts and the vendored Gavel framework code under `vendor/harness/`. Third-party components keep their own licenses, listed below; this suite grants no additional license to third-party code or data.

- **Harbor 0.21.0** (`vendor/harbor/`): its original license is `vendor/harbor/LICENSE`.
- **Rubric library** (`vendor/harness/judge/rubric/library_v1/`): the `finance`, `finance_hard`, `legal` and `legal_hard` domains are derived from the criteria of PRBench (Scale AI), licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). The criteria were reorganized into a domain/category tree with an index; the criterion sentences are kept verbatim. The `airline_ops` domain is derived from the airline task assertions and the `banking_ops` domain from the banking knowledge base of τ²-bench (Sierra Research), licensed under the MIT License, Copyright (c) 2025 Sierra Research.
- **VerifierBench data** comes from the pinned Hugging Face commit of `Catherine1213/VerifierBench`; its dataset card and data license come with the download.
- **AppWorld**: its protected implementation and original data are not in this release; they are prepared by the official install and download commands.
- **AgentDojo, τ²-bench, SWE-bench, Node, OpenCode, CPython and uv** are installed from their official sources, with versions and checksum receipts recorded.

The release contains no model keys, model response history, previously generated verifiers, earlier scores, copies of the original candidates or credentials from any user's machine.

## 中文

本套件属于 verifier-suite 仓库，按仓库的 Apache License 2.0 授权（见仓库根目录的 `LICENSE`）。该许可覆盖套件自身的代码和文本：runner、VerifierBench runtime、引导脚本，以及 `vendor/harness/` 下随包的 Gavel 框架代码。第三方组件沿用各自的许可（见下），本套件不额外授予第三方代码或数据的许可。

- **Harbor 0.21.0**（`vendor/harbor/`）：原许可证位于 `vendor/harbor/LICENSE`。
- **Rubric 库**（`vendor/harness/judge/rubric/library_v1/`）：`finance`、`finance_hard`、`legal`、`legal_hard` 四个领域来自 PRBench（Scale AI）的评分条目，按 CC BY 4.0 授权（https://creativecommons.org/licenses/by/4.0/）；条目被重组为领域/类目树并加了索引，条目原句保持不变。`airline_ops` 领域来自 τ²-bench（Sierra Research）航空任务的判定断言，`banking_ops` 领域来自其银行知识库，按 MIT License 授权，Copyright (c) 2025 Sierra Research。
- **VerifierBench 数据**从 `Catherine1213/VerifierBench` 的固定 Hugging Face 提交获取，数据卡和数据许可随下载保留。
- **AppWorld**：受保护实现与原始数据不打进发行包，由官方安装/下载命令准备。
- **AgentDojo、τ²-bench、SWE-bench、Node、OpenCode、CPython 和 uv** 按各自官方来源安装，分别保留版本与校验收据。

不包含模型密钥、模型响应历史、旧生成 verifier、旧成绩、原始候选副本或用户机器的认证文件。

## τ²-bench license / τ²-bench 许可证文本

```text
MIT License

Copyright (c) 2025 Sierra Research

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
