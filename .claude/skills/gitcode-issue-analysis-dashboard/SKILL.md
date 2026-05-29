---
name: gitcode-issue-analysis-dashboard
description: 基于已有的 GitCode issue 分析 MD 报告生成 HTML Dashboard 综合页面。LLM 阅读报告、理解内容、提取结构化数据、生成洞察，脚本仅负责 HTML/CSS 渲染。当用户要更新 Dashboard、生成总览页面、构建索引或刷新分析汇总时触发。
---

# GitCode Issue 分析 Dashboard

基于 `gitcode-issue-analyzer` 产出的 MD 报告生成综合 HTML Dashboard。
LLM 负责阅读和理解报告内容——脚本仅处理 HTML/CSS 渲染。

此 Skill 消费 MD 报告，不处理原始 issue 数据。如需最新报告，先运行
`gitcode-issue-analyzer`。

## 架构

两个核心能力均由大模型驱动：

1. **数据理解** — LLM 直接阅读 MD 报告，语义层面理解统计数据和模式，
   提取结构化数据，生成有深度的洞察。
2. **工作流调度** — LLM 编排发现 → 阅读 → 提取 → 渲染的全流程。

`generate_index.py` 脚本仅处理：
- 文件发现（`list` — 找出每个 target 的最新报告）
- HTML/CSS 渲染（`render` — 基于 LLM 产出的 JSON）

## 工作流

### 步骤 1：发现最新报告

```bash
python3 .claude/skills/gitcode-issue-analysis-dashboard/scripts/generate_index.py list docs/
```

输出 JSON 列出每个 target 的最新报告文件。**不做内容解析。**

如用户需要最新的分析数据，先调用 `gitcode-issue-analyzer` 对各 target
完成分析后再执行此步骤。

### 步骤 2：LLM 阅读理解报告

**此步骤必须由 LLM 完成。严禁使用正则或脚本解析报告内容。**

依次读取步骤 1 列出的每份 MD 报告，重点关注：
- `## 汇总` — 总 issue 数、基础设施数
- `### 按子分类统计` — 各子分类数量分布
- `### 按仓库统计` — 各仓库分布
- Header 表格 — `获取 Issue 总数` 作为 total 的 fallback
- `## 详情` 表格 — 具体 issue 条目，用于发现模式

阅读完所有报告后完成三项工作：

1. **提取结构化数据** — 每个社区/仓库：
   - `name`、`is_org`、`n_repos`、`total`、`infra`
   - `categories`：子分类 → 数量映射
   - `report_file`、`report_ts`

2. **计算跨社区汇总**：
   - 汇总 `total`、`infra`
   - 去重统计仓库数
   - 合并 `category_totals`

3. **生成 3-5 条洞察** — 基于对数据的语义理解：
   - 识别集中问题（如"build 类占 CANN 基础设施 issue 的 40%"）
   - 跨社区对比（如"Ascend/pytorch 的 testing-infra 占比显著高于其他社区"）
   - 异常发现（如"BoostKit 19 个 issue 中零基础设施类"）
   - 格式：`<strong>标题：</strong>具体分析...`

### 步骤 3：写入结构化数据

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

### 步骤 4：渲染 HTML Dashboard

```bash
python3 .claude/skills/gitcode-issue-analysis-dashboard/scripts/generate_index.py render ./dashboard_data.json docs/index.html
```

脚本仅负责 HTML/CSS 样式和布局——所有数据和洞察来自 LLM 产出的 JSON。

### 步骤 5：输出总结

```
## Dashboard 已更新

| 指标 | 数值 |
|------|------|
| 社区数 | <N> |
| 总 Issues | <total> |
| 基础设施类 | <infra> |

Dashboard: docs/index.html
```

清理 `./dashboard_data.json`。
