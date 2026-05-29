---
name: gitcode-issue-analysis-dashboard
description: Generate an HTML dashboard index page from existing GitCode issue analysis MD reports. The LLM reads reports, understands content, extracts structured data, generates insights, and renders the dashboard. Triggers when user asks to update the dashboard, generate an overview page, build an index, or refresh the analysis summary.
---

# GitCode Issue Analysis Dashboard

Generate a comprehensive HTML dashboard from existing MD reports produced by
`gitcode-issue-analyzer`. The LLM reads and understands report content — the
script only handles HTML/CSS rendering.

This skill consumes MD reports, not raw issue data. Run `gitcode-issue-analyzer`
first if fresh reports are needed.

## Architecture

Two LLM-driven capabilities:

1. **Data understanding** — LLM reads MD reports, comprehends statistics and
   patterns semantically, extracts structured data, generates meaningful insights.
2. **Workflow scheduling** — LLM orchestrates discovery → reading → extraction → rendering.

The `generate_index.py` script only handles:
- File discovery (`list` — find latest report per target)
- HTML/CSS rendering (`render` — from LLM-provided JSON)

## Workflow

### Step 1: Discover Latest Reports

```bash
python3 .claude/skills/gitcode-issue-analysis-dashboard/scripts/generate_index.py list docs/
```

Outputs JSON listing each target's latest report file. **No content parsing.**

If the user also wants fresh analysis first, invoke `gitcode-issue-analyzer`
for each target before this step.

### Step 2: LLM Reads and Understands Reports

**This step MUST be done by the LLM. Do NOT use regex or script-based parsing.**

Read each report file from Step 1. Focus on:
- `## 汇总` — total issues, infrastructure count
- `### 按子分类统计` — category breakdown
- `### 按仓库统计` — per-repository distribution
- Header table — `获取 Issue 总数` as fallback
- `## 详情` table — individual issue entries for pattern discovery

After reading all reports:

1. **Extract structured data** per community:
   - `name`, `is_org`, `n_repos`, `total`, `infra`
   - `categories`: category → count mapping
   - `report_file`, `report_ts`

2. **Compute cross-community totals**:
   - Aggregate `total`, `infra`
   - Count distinct repos
   - Merge `category_totals`

3. **Generate 3-5 insights** based on semantic understanding:
   - Identify concentrated problem areas (e.g. "build is 40% of CANN infra issues")
   - Compare communities
   - Note anomalies
   - Format: `<strong>标题：</strong>具体分析...`

### Step 3: Write Structured Data

Write extracted data to `./dashboard_data.json`:

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

### Step 4: Render HTML Dashboard

```bash
python3 .claude/skills/gitcode-issue-analysis-dashboard/scripts/generate_index.py render ./dashboard_data.json docs/index.html
```

### Step 5: Output Summary

```
## Dashboard Updated

| Metric | Value |
|--------|-------|
| Communities | <N> |
| Total Issues | <total> |
| Infrastructure | <infra> |

Dashboard: docs/index.html
```

Clean up `./dashboard_data.json`.
