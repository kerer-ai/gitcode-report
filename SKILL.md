---
name: gitcode-issue-analyzer
description: Analyze GitCode repository/community issues to identify infrastructure-related issues using AI classification. Outputs a report.md with categorized table and summary. Use when user wants to analyze issues, find infrastructure issues, classify issues, check repo issues, or generate issue analysis reports.
---

# GitCode Issue Analyzer

Analyze issues from a GitCode repository or community, using AI to identify infrastructure-related issues that are often missed by labels.

## Input

Two parameters:
- **target**: Repository (`owner/repo`) or organization name (e.g. `Ascend/pytorch`, `gitcode-cli`)
- **days**: Number of days to look back (default: 7)

If the user does not provide either parameter, ask interactively using `AskUserQuestion`. Ask for both parameters at once — ask for the target first, then the day count.

## Workflow

Execute these steps sequentially. The working directory is the current project directory — do NOT `cd` to the skill directory.

### Step 1: Fetch Issues

```
bash: python3 <skill_dir>/scripts/analyze.py <target> --days <N> -r ./issues_raw.json
```

- `<skill_dir>` = `~/.claude/skills/gitcode-issue-analyzer`
- Saves raw issue data to `./issues_raw.json`
- If gc auth fails, tell user to run `gc auth login`

### Step 2: AI Classification

Read `./issues_raw.json`. For each issue, extract **only** `title` and `description` for classification (drop labels, author, timestamps, state — they consume tokens without aiding classification).

Classification criteria:

**Infrastructure:**
- CI/CD pipelines, build systems, automation
- Dev environment setup, toolchain config
- Test frameworks, testing infrastructure
- Deployment, containerization, Kubernetes, Docker
- Monitoring, logging, alerting, observability
- Code quality tools (lint, format, static analysis)
- Developer tooling, scripts, automation

**NOT infrastructure:**
- Business features, UI/UX, product requirements
- Documentation feedback
- Operator/model/runtime bug fixes
- CVE / dependency security vulnerabilities
- API compatibility analysis / usage questions
- Feature RFCs for new capabilities

For >20 issues, classify in batches of ~25. Process each batch independently.

Output format — one JSON object per issue:
```json
{"repo":"<repo>","number":"<number>","is_infra":true/false,"category":"<subcategory|null>","reason":"<one-line reason in Chinese>"}
```

Valid categories: `ci/cd`, `build`, `testing-infra`, `toolchain`, `dev-environment`, `code-quality`, `deployment`, `containerization`, `monitoring`, `logging`, `alerting`, `developer-experience`, `other-infra`

Write the complete JSON array to `./classification.json`.

### Step 3: Generate Report

```
bash: python3 <skill_dir>/scripts/analyze.py --load-raw ./issues_raw.json --classify ./classification.json
```

This produces a report in `docs/` named `<community>_<timestamp>.md` with a summary section and a Markdown table.

### Step 4: Print Summary

Print a summary table to the console:

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

## Scripts

Located in `scripts/` under the skill directory:
- `analyze.py` — CLI entry point
- `gc_wrapper.py` — gc CLI wrapper
- `fetcher.py` — issue fetching (single repo or org-wide, with pagination and concurrency)
- `classifier.py` — classification prompt formatting and result parsing
- `reporter.py` — Markdown table and summary generation

No external Python dependencies (stdlib only). Requires `gc` CLI installed and authenticated.
