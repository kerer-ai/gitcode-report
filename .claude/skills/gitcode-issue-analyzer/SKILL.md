---
name: gitcode-issue-analyzer
description: 分析 GitCode 仓库/社区的 issue，使用 AI 分类识别基础设施类 issue，生成 MD 报告。支持单仓库、单组织、多目标批量分析。当用户需要分析 issue、查找基础设施问题、分类 issue、检查仓库 issue 或生成 issue 分析报告时使用。Dashboard 生成请使用 gitcode-issue-analysis-dashboard。
---

# GitCode Issue 分析器

使用 AI 分析 GitCode 仓库或社区的 issue，识别常被标签遗漏的基础设施类问题。
输出标准化的 Markdown 报告到 `docs/` 目录，可被 `gitcode-issue-analysis-dashboard`
消费生成 HTML Dashboard。

## 架构

两个核心能力均由大模型驱动：

1. **工作流调度** — LLM 编排多目标分析：获取 → 分类 → 报告生成
2. **Issue 分类** — LLM 逐条阅读 issue 标题和描述，基于语义判断是否属于基础设施类

脚本负责机械性工作：GC API 调用、数据存取、Markdown 格式化。

## 输入参数

- **target**：仓库名（`owner/repo`）或组织名（如 `Ascend/pytorch`），支持逗号分隔多个目标
- **days**：回溯天数（默认 7 天）

如果用户未提供参数，使用 `AskUserQuestion` 交互式询问——先问 target，再问 days。

## 工作流

按顺序执行。工作目录为当前项目根目录。

### 步骤 1：获取 Issues

```bash
python3 .claude/skills/gitcode-issue-analyzer/scripts/analyze.py <target> --days <N> -r ./issues_raw.json
```

- 原始 issue 数据保存到 `./issues_raw.json`
- 如果 gc 认证失败，提示用户执行 `gc auth login`

### 步骤 2：AI 分类

**此步骤必须由大模型亲自完成，严禁使用关键词匹配、正则表达式或任何脚本自动分类。**

读取 `./issues_raw.json`。对每条 issue，**仅**提取 `title` 和 `description` 用于分类（丢弃 labels、author、时间戳、state 等不辅助分类的元数据，节省 token）。

逐条阅读每个 issue 的标题和描述，基于语义理解判断其是否属于基础设施类问题。

**属于基础设施：**
- CI/CD 流水线、构建系统、自动化
- 开发环境搭建、工具链配置
- 测试框架、测试基础设施
- 部署、容器化、Kubernetes、Docker
- 监控、日志、告警、可观测性
- 代码质量工具（lint、format、静态分析工具的引入/配置/维护）
- 开发者工具、脚本、自动化

**不属于基础设施：**
- 业务功能、UI/UX、产品需求
- 文档反馈
- 算子/模型/runtime bug 修复
- CVE/依赖安全漏洞
- API 一致性分析/使用问题
- 新功能 RFC
- 代码重构/清理（如模块重构、拼写修正、减少重复代码）
- 编译器/工具链的新功能增强（如新增 costmodel 后端）

超过 20 条 issue 时，分批次分类，每批约 25 条。可使用并行 sub-agents 加速各批次独立分类。

输出格式——每条 issue 一个 JSON 对象：
```json
{"repo":"<仓库名>","number":"<issue号>","is_infra":true/false,"category":"<子分类|null>","reason":"<一句话理由>"}
```

可选子分类：`ci/cd`、`build`、`testing-infra`、`toolchain`、`dev-environment`、`code-quality`、`deployment`、`containerization`、`monitoring`、`logging`、`alerting`、`dependency-management`、`developer-experience`、`other-infra`

将完整 JSON 数组写入 `./classification.json`。

### 步骤 3：生成 MD 报告

```bash
python3 .claude/skills/gitcode-issue-analyzer/scripts/analyze.py --load-raw ./issues_raw.json --classify ./classification.json
```

报告保存到 `docs/<target>_<timestamp>.md`，包含：
- 查询元数据（目标、天数、时间范围）
- 汇总统计（总 issues、基础设施数）
- 按子分类统计
- 按仓库统计（含超链接）
- 详情表格（仓库、Issue #、标题、子分类、理由、标签、状态、创建时间）

多个 target 时对每个依次执行步骤 1-3。

### 步骤 4：清理与总结

```bash
rm -f ./issues_raw.json ./classification.json
```

```
## 分析结果

| 指标 | 数值 |
|------|------|
| 仓库/组织 | <target> |
| 时间范围 | 最近 <N> 天 |
| 总 issues | <total> |
| 基础设施类 | <infra_count> |

### 子分类分布
- <category>: <count>
...

📄 完整报告: docs/<target>_<timestamp>.md
```

## 与 Dashboard 的协作

MD 报告是 `gitcode-issue-analyzer` 和 `gitcode-issue-analysis-dashboard` 之间的标准接口。
分析完成后，用户可运行 dashboard skill 基于现有报告生成/更新 HTML 综合页面。

## 脚本

位于 `.claude/skills/gitcode-issue-analyzer/scripts/`：
- `analyze.py` — CLI 入口（获取 + 报告生成）
- `gc_wrapper.py` — gc 命令封装
- `fetcher.py` — issue 获取编排
- `classifier.py` — 分类数据准备与结果解析
- `reporter.py` — Markdown 报告生成

无需外部 Python 依赖（仅标准库）。需要安装并认证 `gc` CLI。
