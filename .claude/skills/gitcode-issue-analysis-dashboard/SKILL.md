---
name: gitcode-issue-analysis-dashboard
description: Orchestrate batch analysis of multiple GitCode repositories/communities using gitcode-issue-analyzer. Interactively asks user for target repos, runs analysis for each sequentially, then generates an HTML index page linking to all latest reports. Triggers when user asks to analyze multiple repos, build a dashboard, generate an overview page, or batch-analyze issues across communities.
---

# GitCode Issue Analysis Dashboard

Orchestrate batch infrastructure-issue analysis across multiple GitCode repositories
or communities, then generate an HTML dashboard linking to all latest reports.

## Workflow

### Step 1: Gather Targets

If the user has not already specified which repositories or communities to analyze,
use `AskUserQuestion` to interactively ask:

1. **Target repos/communities** — comma or space-separated list of `owner/repo`
   or organization names (e.g. `Ascend/pytorch, Ascend/mindspore`)
2. **Days to look back** — default 7, same as gitcode-issue-analyzer

### Step 2: Sequential Analysis

For each target, invoke the `gitcode-issue-analyzer` skill using the `Skill` tool:

```
Skill(skill="gitcode-issue-analyzer")
```

The gitcode-issue-analyzer skill handles fetching issues, AI classification,
and report generation. Each report is saved to `docs/<Target>_<timestamp>.md`.

Process targets **sequentially** — wait for each analysis to fully complete
before starting the next. This avoids API rate limiting and ensures clean
report generation.

### Step 3: Generate Dashboard Index

After all targets are analyzed, generate the HTML dashboard:

```bash
python3 .claude/skills/gitcode-issue-analysis-dashboard/scripts/generate_index.py docs/ docs/index.html
```

The script:

- Scans `docs/` for all report files matching `<target>_<YYYYMMDD_HHMM>.md`
- Groups by target, selects the **latest** report for each
- Extracts summary statistics (total issues, infra count, category breakdown)
- Renders a responsive HTML page with cards for each target

Each card includes:
- Target name linked to its GitCode pulls page
- Infrastructure issue count and percentage
- Category distribution tags
- Repository-level breakdown
- Link to the latest markdown report

### Step 4: Output Summary

Print a summary of what was generated:

```
## Dashboard Generated

| Metric | Value |
|--------|-------|
| Targets analyzed | <N> |
| Reports in docs/ | <count> |

Dashboard: docs/index.html
```

If the project is set up for GitHub/GitCode Pages, the index.html can be
served directly via Pages — inform the user of this option.
