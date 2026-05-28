---
name: gitcode-issue-analyzer
description: 分析 GitCode 仓库/社区的 issue，使用 AI 分类识别基础设施类 issue。输出包含分类表格和汇总的 Markdown 报告。当用户需要分析 issue、查找基础设施问题、分类 issue、检查仓库 issue 或生成 issue 分析报告时使用。
---

# GitCode Issue 分析器

使用 AI 分析 GitCode 仓库或社区的 issue，识别常被标签遗漏的基础设施类问题。

## 输入参数

两个参数：
- **target**：仓库名（`owner/repo`）或组织名（如 `Ascend/pytorch`、`gitcode-cli`）
- **days**：回溯天数（默认 7 天）

如果用户未提供参数，使用 `AskUserQuestion` 交互式询问。一次同时问两个参数——先问 target，再问 days。

## 工作流

按顺序执行以下步骤。工作目录为当前项目根目录——不要 `cd` 到 skill 目录。

### 步骤 1：获取 Issues

在项目根目录运行：

```
bash: python3 .claude/skills/gitcode-issue-analyzer/scripts/analyze.py <target> --days <N> -r ./issues_raw.json
```

- 原始 issue 数据保存到 `./issues_raw.json`
- 如果 gc 认证失败，提示用户执行 `gc auth login`

### 步骤 2：AI 分类

读取 `./issues_raw.json`。对每条 issue，**仅**提取 `title` 和 `description` 用于分类（丢弃 labels、author、时间戳、state 等不辅助分类的元数据，节省 token）。

分类标准：

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
- 新功能 RFC

超过 20 条 issue 时，分批次分类，每批约 25 条。各批次独立处理。

输出格式——每条 issue 一个 JSON 对象：
```json
{"repo":"<仓库名>","number":"<issue号>","is_infra":true/false,"category":"<子分类|null>","reason":"<一句话理由>"}
```

可选子分类：`ci/cd`、`build`、`testing-infra`、`toolchain`、`dev-environment`、`code-quality`、`deployment`、`containerization`、`monitoring`、`logging`、`alerting`、`developer-experience`、`other-infra`

将完整 JSON 数组写入 `./classification.json`。

### 步骤 3：生成报告

```
bash: python3 .claude/skills/gitcode-issue-analyzer/scripts/analyze.py --load-raw ./issues_raw.json --classify ./classification.json
```

报告自动保存到 `docs/` 目录，文件名为 `<社区>_<时间戳>.md`，包含汇总统计和 Markdown 详情表格。

### 步骤 4：输出总结

在控制台打印总结：

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

## 脚本

位于项目 `.claude/skills/gitcode-issue-analyzer/scripts/` 目录：
- `analyze.py` — CLI 入口
- `gc_wrapper.py` — gc 命令封装
- `fetcher.py` — issue 获取编排（单仓库或组织级，支持分页和并发）
- `classifier.py` — 分类数据准备与结果解析
- `reporter.py` — Markdown 表格和汇总生成

无需外部 Python 依赖（仅标准库）。需要安装并认证 `gc` CLI。
