"""Report output formatting — markdown tables and summary statistics."""

import unicodedata
from collections import Counter
from datetime import datetime, timezone

# Category code → Chinese display name
CATEGORY_NAMES = {
    "ci/cd": "持续集成",
    "build": "构建系统",
    "testing-infra": "测试基础设施",
    "toolchain": "工具链",
    "dev-environment": "开发环境",
    "code-quality": "代码质量工具",
    "deployment": "部署",
    "containerization": "容器化",
    "monitoring": "监控",
    "logging": "日志",
    "alerting": "告警",
    "dependency-management": "依赖管理",
    "developer-experience": "开发体验",
    "other-infra": "其他基础设施",
    "unknown": "未知",
}


def _display_width(text: str) -> int:
    """Return display width accounting for CJK characters (2-wide)."""
    w = 0
    for ch in text:
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            w += 2
        else:
            w += 1
    return w


def _truncate_display(text: str, max_width: int) -> str:
    """Truncate text to fit within max_width display columns, adding '..'."""
    w = 0
    result = []
    for ch in text:
        cw = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        if w + cw > max_width - 2:
            result.append("..")
            break
        w += cw
        result.append(ch)
    return "".join(result)


def _visible_text(cell: str) -> str:
    """Extract visible portion of a markdown link."""
    if cell.startswith("[") and "](" in cell:
        return cell[1 : cell.index("](")]
    return cell


def _pad_cell(cell: str, target_width: int) -> str:
    """Pad cell to target display width, handling CJK and markdown links."""
    text = _visible_text(cell)
    current_w = _display_width(text)
    pad_needed = target_width - current_w
    if pad_needed > 0:
        return cell + " " * pad_needed
    return cell


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
    issues = sorted(issues, key=lambda i: (i.get("repo", ""), int(i.get("number", 0))))

    headers = ["仓库", "Issue #", "标题", "子分类", "理由", "原始标签", "状态", "创建时间"]
    rows = []

    for iss in issues:
        labels = iss.get("labels", []) or []
        labels_str = ", ".join(labels[:5])
        if len(labels) > 5:
            labels_str += f" +{len(labels) - 5}"

        title = iss.get("title", "")
        # Truncate long titles to ~50 display width
        if _display_width(title) > 50:
            title = _truncate_display(title, 50)

        reason = iss.get("reason", "")
        if _display_width(reason) > 36:
            reason = _truncate_display(reason, 36)

        repo = iss.get("repo", "")
        number = iss.get("number", "")
        repo_link = f"[{repo}](https://gitcode.com/{repo}/pulls)"
        issue_link = f"[#{number}](https://gitcode.com/{repo}/issues/{number})"

        cat_code = iss.get("category", "") or ""
        cat_display = CATEGORY_NAMES.get(cat_code, cat_code)

        rows.append([
            repo_link,
            issue_link,
            title,
            cat_display,
            reason,
            labels_str,
            iss.get("state", ""),
            iss.get("created_at", "")[:10],
        ])

    # Column widths target (display widths, CJK char = 2)
    COL_MAX = {"仓库": 30, "Issue #": 10, "标题": 50, "子分类": 12,
               "理由": 32, "原始标签": 24, "状态": 8, "创建时间": 10}

    def _fmt_row(cells: list[str]) -> str:
        parts = []
        for i, cell in enumerate(cells):
            header_key = headers[i]
            target = COL_MAX.get(header_key, 20)
            text = _visible_text(cell)
            # Truncate if needed
            if _display_width(text) > target:
                if cell.startswith("[") and "](" in cell:
                    link_start = cell.index("](")
                    keep = _truncate_display(text, target)
                    cell = f"[{keep}]{cell[link_start:]}"
                    text = keep
                else:
                    cell = _truncate_display(text, target)
                    text = cell
            parts.append(_pad_cell(cell, target))
        return "| " + " | ".join(parts) + " |"

    lines = []
    lines.append(_fmt_row(headers))
    lines.append("|-" + "-|-".join("-" * COL_MAX[h] for h in headers) + "-|")
    for row in rows:
        lines.append(_fmt_row(row))

    return "\n".join(lines)


def generate_summary(issues: list[dict], filter_infra: bool = True) -> str:
    """Generate a summary of classified issues.

    Args:
        issues: List of issue dicts with classification fields.
        filter_infra: If True, only count infrastructure issues.

    Returns:
        Summary text. Always includes full structure so downstream parsers
        can reliably extract statistics from any report.
    """
    total = len(issues)

    if filter_infra:
        infra_issues = [i for i in issues if i.get("is_infra")]
    else:
        infra_issues = issues

    # Count by category
    categories = Counter(i.get("category", "unknown") for i in infra_issues if i.get("is_infra"))
    # Count by repo
    repos = Counter(i.get("repo", "unknown") for i in infra_issues if i.get("is_infra"))

    lines = [
        f"## 汇总",
        f"",
        f"- 总 issues (获取): **{total}**",
        f"- 基础设施类: **{len(infra_issues)}**",
        f"",
        f"### 按子分类统计",
        f"",
    ]
    if categories:
        for cat, count in categories.most_common():
            cat_display = CATEGORY_NAMES.get(cat, cat)
            lines.append(f"- {cat_display}: {count}")
    else:
        lines.append("- (无)")

    lines.append("")
    lines.append("### 按仓库统计")
    lines.append("")
    if repos:
        for repo, count in repos.most_common():
            lines.append(f"- [{repo}](https://gitcode.com/{repo}/pulls): {count}")
    else:
        lines.append("- (无)")

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
