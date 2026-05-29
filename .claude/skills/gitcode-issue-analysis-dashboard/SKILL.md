---
name: gitcode-issue-analysis-dashboard
description: Orchestrate batch analysis of multiple GitCode repositories/communities using gitcode-issue-analyzer. Interactively asks user for target repos, runs analysis for each sequentially, then generates an HTML index page linking to all latest reports. Triggers when user asks to analyze multiple repos, build a dashboard, generate an overview page, or batch-analyze issues across communities.
---

# GitCode Issue Analysis Dashboard

Orchestrate batch infrastructure-issue analysis across multiple GitCode repositories
or communities, then generate an HTML dashboard from the latest reports.

## Architecture

This skill leverages the LLM for three critical functions:

1. **Workflow scheduling** — the LLM orchestrates the entire pipeline: gather targets,
   invoke analysis skill sequentially, extract data, and trigger rendering.
2. **Issue classification** — delegated to `gitcode-issue-analyzer`, which uses AI
   to classify each issue (not keyword matching).
3. **Data understanding and insight generation** — the LLM reads MD reports directly,
   comprehends the statistics and patterns semantically, extracts structured data, and
   generates meaningful insights. The script only handles HTML/CSS rendering.

## Workflow

### Step 1: Discover Latest Reports

Run the file-discovery command to list the latest report for each target:

```bash
python3 .claude/skills/gitcode-issue-analysis-dashboard/scripts/generate_index.py list docs/
```

This outputs JSON listing each target's latest report file — **no content parsing**.

If the user also wants to run fresh analyses first, gather targets interactively
with `AskUserQuestion`, then invoke `gitcode-issue-analyzer` sequentially for each
target before proceeding.

### Step 2: LLM Reads and Understands Reports

**This step MUST be done by the LLM. Do NOT use regex or script-based parsing.**

Read each report file discovered in Step 1. Focus on these sections:

- `## 汇总` — total issues, infrastructure count
- `### 按子分类统计` — category breakdown (ci/cd, build, testing-infra, etc.)
- `### 按仓库统计` — per-repository distribution
- Header table — `获取 Issue 总数` as fallback for total count
- `## 详情` table — individual issue entries for pattern discovery

After reading all reports, the LLM must:

1. **Extract structured data** — for each community/repo:
   - `name`: display name (e.g. "CANN", "Ascend/pytorch")
   - `is_org`: true for org-level analysis, false for single repo
   - `n_repos`: number of distinct repos in the report
   - `total`: total issues fetched
   - `infra`: infrastructure issue count
   - `categories`: dict of category → count
   - `report_file`: filename of the MD report
   - `report_ts`: human-readable timestamp

2. **Compute cross-community totals**:
   - Aggregate `total`, `infra` across all communities
   - Count distinct repos across all communities
   - Merge category counts into `category_totals`

3. **Generate insights** — based on semantic understanding of the data:
   - Identify patterns (e.g. "build issues dominate CANN at 40%")
   - Compare communities (e.g. "Ascend/pytorch has high testing-infra ratio")
   - Note anomalies (e.g. "BoostKit has zero infra issues across 19 total")
   - Highlight cross-community common pain points
   - Each insight as HTML string: `<strong>标题：</strong>具体分析...`
   - Write 3-5 substantive, data-grounded insights

### Step 3: Write Structured Data

Write the extracted data as JSON to `./dashboard_data.json`:

```json
{
  "date": "2026-05-29",
  "totals": {
    "total": 1351,
    "infra": 161,
    "repos": 101
  },
  "communities": [
    {
      "name": "CANN",
      "is_org": true,
      "n_repos": 41,
      "total": 837,
      "infra": 74,
      "categories": {"build": 30, "testing-infra": 10, "toolchain": 10, "ci/cd": 5, "dev-environment": 13, "code-quality": 5, "developer-experience": 1},
      "report_file": "CANN_multi_20260528_1432.md",
      "report_ts": "2026-05-28 14:32 UTC"
    }
  ],
  "category_totals": {
    "build": 39,
    "testing-infra": 37,
    "toolchain": 27,
    "ci/cd": 23,
    "dev-environment": 21,
    "code-quality": 10,
    "developer-experience": 4
  },
  "insights": [
    "<strong>构建系统问题跨社区突出：</strong>build 类 issue 共 39 个，占全部基础设施问题的 24.2%，主要集中在 CANN 和 Ascend 组织...",
    "<strong>Ascend/pytorch 测试基础设施压力显著：</strong>testing-infra 占比达 41.9%，主要表现为社区用例同步和 NPU 适配 patch 覆盖不足..."
  ]
}
```

### Step 4: Render HTML Dashboard

Pass the structured data to the rendering script:

```bash
python3 .claude/skills/gitcode-issue-analysis-dashboard/scripts/generate_index.py render ./dashboard_data.json docs/index.html
```

The script purely handles HTML/CSS styling and layout — all data and insights
come from the LLM-produced JSON.

### Step 5: Output Summary

Print a summary:

```
## Dashboard Generated

| Metric | Value |
|--------|-------|
| Communities | <N> |
| Total Issues | <total> |
| Infrastructure | <infra> |
| Repos Covered | <repos> |

Dashboard: docs/index.html
```

Clean up `./dashboard_data.json` if desired.
