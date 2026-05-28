"""Report output formatting — markdown tables and summary statistics."""

from collections import Counter
from datetime import datetime, timezone


def generate_table(
    issues: list[dict],
    filter_infra: bool = True,
) -> str:
    """Generate a Markdown table of classified issues.

    Args:
        issues: List of issue dicts with classification fields (is_infra, category, reason).
        filter_infra: If True, only include infrastructure issues.

    Returns:
        Markdown formatted table string.
    """
    if filter_infra:
        issues = [i for i in issues if i.get("is_infra")]
        if not issues:
            return "未发现基础设施类 issue。"

    # Sort by repo then number
    issues = sorted(issues, key=lambda i: (i.get("repo", ""), i.get("number", 0)))

    headers = ["仓库", "Issue #", "标题", "子分类", "理由", "原始标签", "状态", "创建时间"]
    rows = []

    for iss in issues:
        labels_str = ", ".join(iss.get("labels", [])[:5])
        if len(iss.get("labels", [])) > 5:
            labels_str += f" +{len(iss['labels']) - 5}"

        title = iss.get("title", "")
        # Truncate long titles
        if len(title) > 60:
            title = title[:57] + "..."

        reason = iss.get("reason", "")
        if len(reason) > 40:
            reason = reason[:37] + "..."

        rows.append([
            iss.get("repo", ""),
            str(iss.get("number", "")),
            title,
            iss.get("category", ""),
            reason,
            labels_str,
            iss.get("state", ""),
            iss.get("created_at", "")[:10],
        ])

    # Build markdown table
    col_widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(len(headers))]
    # Cap column widths
    col_widths = [min(w, 30) for w in col_widths]

    def _fmt_row(cells: list[str]) -> str:
        parts = []
        for i, cell in enumerate(cells):
            c = str(cell)
            if len(c) > col_widths[i]:
                c = c[: col_widths[i] - 2] + ".."
            parts.append(c.ljust(col_widths[i]))
        return "| " + " | ".join(parts) + " |"

    lines = []
    lines.append(_fmt_row(headers))
    lines.append("|-" + "-|-".join("-" * w for w in col_widths) + "-|")
    for row in rows:
        lines.append(_fmt_row(row))

    return "\n".join(lines)


def generate_summary(issues: list[dict], filter_infra: bool = True) -> str:
    """Generate a summary of classified issues.

    Args:
        issues: List of issue dicts with classification fields.
        filter_infra: If True, only count infrastructure issues.

    Returns:
        Summary text.
    """
    total = len(issues)

    if filter_infra:
        infra_issues = [i for i in issues if i.get("is_infra")]
    else:
        infra_issues = issues

    if not infra_issues:
        return f"总 issues: {total}, 基础设施类: 0"

    # Count by category
    categories = Counter(i.get("category", "unknown") for i in infra_issues)
    # Count by repo
    repos = Counter(i.get("repo", "unknown") for i in infra_issues)

    lines = [
        f"## 汇总",
        f"",
        f"- 总 issues (获取): **{total}**",
        f"- 基础设施类: **{len(infra_issues)}**",
        f"",
        f"### 按子分类统计",
        f"",
    ]
    for cat, count in categories.most_common():
        lines.append(f"- {cat}: {count}")

    lines.append("")
    lines.append("### 按仓库统计")
    lines.append("")
    for repo, count in repos.most_common():
        lines.append(f"- {repo}: {count}")

    return "\n".join(lines)


def _extract_meta(issues: list[dict]) -> tuple[str, str, str]:
    """Extract target name and date range from issue data."""
    repos = list(set(i.get("repo", "") for i in issues if i.get("repo")))
    target = repos[0] if len(repos) == 1 else ", ".join(sorted(repos))

    dates = [i.get("created_at", "")[:10] for i in issues if i.get("created_at")]
    date_range = f"{min(dates)} ~ {max(dates)}" if dates else "N/A"

    return target, date_range


def generate_header(
    issues: list[dict],
    days: int = 7,
) -> str:
    """Generate a report header with query metadata.

    Args:
        issues: List of issue dicts.
        days: Number of days queried.

    Returns:
        Markdown header string.
    """
    target, date_range = _extract_meta(issues)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# GitCode Issue 分析报告",
        f"",
        f"| 项目 | 内容 |",
        f"|------|------|",
        f"| 查询目标 | **{target}** |",
        f"| 查询天数 | 最近 **{days}** 天 |",
        f"| Issue 时间范围 | {date_range} |",
        f"| 报告生成时间 | {now} |",
        f"| 获取 Issue 总数 | **{len(issues)}** |",
        f"",
    ]
    return "\n".join(lines)


def generate_full_report(
    issues: list[dict],
    filter_infra: bool = True,
    days: int = 7,
) -> str:
    """Generate a complete report with header, summary and detail table.

    Args:
        issues: List of issue dicts with classification fields.
        filter_infra: If True, only report infrastructure issues.
        days: Number of days queried.

    Returns:
        Full report as Markdown text.
    """
    parts = [
        generate_header(issues, days=days),
        generate_summary(issues, filter_infra=filter_infra),
        "",
        "## 详情",
        "",
        generate_table(issues, filter_infra=filter_infra),
    ]
    return "\n".join(parts)
