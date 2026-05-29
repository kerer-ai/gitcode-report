---
name: gitcode-issue-analyzer
description: 分析 GitCode 仓库/社区的 issue，使用 AI 分类识别基础设施类 issue，生成 MD 报告和 Dashboard HTML 页面。支持单仓库、单组织、多目标批量分析。当用户需要分析 issue、查找基础设施问题、生成 issue 分析报告或构建 Dashboard 时使用。
---

# GitCode Issue 分析器

端到端的 GitCode issue 基础设施分析工具：获取 issues → AI 分类 → 生成 MD 报告 → 生成 Dashboard HTML。

三个核心能力均由大模型驱动：
1. **工作流调度** — LLM 编排多目标分析、数据提取、页面渲染的全流程
2. **Issue 分类** — LLM 逐条阅读 issue 标题和描述，基于语义判断是否属于基础设施类
3. **数据理解转换** — LLM 阅读 MD 报告，理解内容，提取结构化数据，生成洞察

## 输入参数

两个参数：
- **target**：仓库名（`owner/repo`）或组织名（如 `Ascend/pytorch`），支持逗号分隔多个目标
- **days**：回溯天数（默认 7 天）

如果用户未提供参数，使用 `AskUserQuestion` 交互式询问——先问 target，再问 days。

## 工作流

按顺序执行。工作目录为当前项目根目录——不要 `cd` 到 skill 目录。

---

### 阶段一：Issue 获取与分类

对每个 target 依次执行。

#### 步骤 1：获取 Issues

```bash
python3 .claude/skills/gitcode-issue-analyzer/scripts/analyze.py <target> --days <N> -r ./issues_raw.json
```

- 原始 issue 数据保存到 `./issues_raw.json`
- 如果 gc 认证失败，提示用户执行 `gc auth login`

#### 步骤 2：AI 分类

**此步骤必须由大模型亲自完成，严禁使用关键词匹配、正则表达式或任何脚本自动分类。**

读取 `./issues_raw.json`。对每条 issue，**仅**提取 `title` 和 `description` 用于分类（丢弃 labels、author、时间戳、state 等元数据，节省 token）。

逐条阅读每个 issue 的标题和描述，基于语义理解判断其是否属于基础设施类问题。

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

超过 20 条 issue 时，分批次分类，每批约 25 条。可使用并行 sub-agents 加速各批次独立分类。

输出格式——每条 issue 一个 JSON 对象：
```json
{"repo":"<仓库名>","number":"<issue号>","is_infra":true/false,"category":"<子分类|null>","reason":"<一句话理由>"}
```

可选子分类：`ci/cd`、`build`、`testing-infra`、`toolchain`、`dev-environment`、`code-quality`、`deployment`、`containerization`、`monitoring`、`logging`、`alerting`、`dependency-management`、`developer-experience`、`other-infra`

将完整 JSON 数组写入 `./classification.json`。

#### 步骤 3：生成 MD 报告

```bash
python3 .claude/skills/gitcode-issue-analyzer/scripts/analyze.py --load-raw ./issues_raw.json --classify ./classification.json
```

报告保存到 `docs/<target>_<timestamp>.md`，包含汇总统计、子分类分布、仓库分布和详情表格。

如果有多 target，对每个 target 重复步骤 1-3。处理完所有 target 后进入阶段二。

---

### 阶段二：Dashboard 生成

所有 target 分析完成后生成综合 Dashboard。

#### 步骤 4：发现最新报告

```bash
python3 .claude/skills/gitcode-issue-analyzer/scripts/generate_index.py list docs/
```

输出 JSON 列出每个 target 的最新报告文件——**不做内容解析**。

#### 步骤 5：LLM 阅读理解报告并提取数据

**此步骤必须由 LLM 完成。严禁使用正则或脚本解析报告内容。**

读取步骤 4 列出的每份 MD 报告，重点关注：
- `## 汇总` — 总 issue 数、基础设施数
- `### 按子分类统计` — 各子分类数量
- `### 按仓库统计` — 各仓库分布
- Header 表格 — `获取 Issue 总数` 作为 total 的 fallback
- `## 详情` 表格 — 具体 issue 条目，用于发现模式

基于语义理解完成三项工作：

1. **提取结构化数据** — 每个社区/仓库输出：
   - `name`、`is_org`、`n_repos`、`total`、`infra`
   - `categories`: 子分类 → 数量映射
   - `report_file`、`report_ts`

2. **计算跨社区汇总** — 合并 `category_totals`、全局 `total`、全局 `infra`、去重 `repos` 数

3. **生成洞察** — 基于对数据的理解，写 3-5 条有深度的分析：
   - 识别集中问题（如"build 类占 CANN 基础设施 issue 的 40%"）
   - 跨社区对比（如"Ascend/pytorch 的 testing-infra 占比显著高于其他社区"）
   - 异常发现（如"BoostKit 19 个 issue 中零基础设施类"）
   - 每条洞察用 HTML 格式：`<strong>标题：</strong>具体分析...`

将提取的数据写入 `./dashboard_data.json`：

```json
{
  "date": "2026-05-29",
  "totals": {"total": 1351, "infra": 161, "repos": 101},
  "communities": [
    {
      "name": "CANN", "is_org": true, "n_repos": 41,
      "total": 837, "infra": 74,
      "categories": {"build": 30, "testing-infra": 10, ...},
      "report_file": "CANN_multi_20260528_1432.md",
      "report_ts": "2026-05-28 14:32 UTC"
    }
  ],
  "category_totals": {"build": 39, "testing-infra": 37, ...},
  "insights": ["<strong>标题：</strong>分析内容...", ...]
}
```

#### 步骤 6：渲染 Dashboard HTML

```bash
python3 .claude/skills/gitcode-issue-analyzer/scripts/generate_index.py render ./dashboard_data.json docs/index.html
```

脚本仅负责 HTML/CSS 样式和布局——所有数据和洞察来自 LLM 产出的 JSON。

#### 步骤 7：清理与总结

```bash
rm -f ./issues_raw.json ./classification.json ./dashboard_data.json
```

输出总结：

```
## 分析完成

| 指标 | 数值 |
|------|------|
| 分析目标数 | <N> |
| 总 Issues | <total> |
| 基础设施类 | <infra> |
| 覆盖仓库数 | <repos> |

📄 MD 报告: docs/
🌐 Dashboard: docs/index.html
```

## 脚本

位于 `.claude/skills/gitcode-issue-analyzer/scripts/` 目录：
- `analyze.py` — CLI 入口（获取 + 报告生成）
- `gc_wrapper.py` — gc 命令封装
- `fetcher.py` — issue 获取编排
- `classifier.py` — 分类数据准备与结果解析
- `reporter.py` — Markdown 报告生成
- `generate_index.py` — Dashboard HTML 渲染（`list` 发现文件，`render` 渲染页面）

无需外部 Python 依赖（仅标准库）。需要安装并认证 `gc` CLI。
