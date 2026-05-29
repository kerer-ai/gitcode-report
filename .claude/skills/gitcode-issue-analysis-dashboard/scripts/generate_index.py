#!/usr/bin/env python3
"""Generate an index.html page from the latest GitCode issue analysis reports.

Scans docs/ for report files named <target>_<timestamp>.md, groups by target,
selects the latest report for each, and renders an HTML index page.
"""

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPORT_PATTERN = re.compile(r"^(.+)_(\d{8}_\d{4})\.md$")
STAT_LINE = re.compile(r"^- (?:总 issues|基础设施类|ci/cd|build|testing-infra|toolchain|dev-environment|code-quality|deployment|containerization|monitoring|logging|alerting|dependency-management|developer-experience|other-infra)[：:]\s*\*?\*?(\d+)\*?\*?")
REPO_LINE = re.compile(r"^- \[(.+?)\]\(.+?\):\s*(\d+)")
REPO_PLAIN_LINE = re.compile(r"^- ([^\[][^:]+?):\s*(\d+)$")


def find_latest_reports(docs_dir: str) -> dict[str, dict]:
    """Find the latest report file for each target in docs_dir.

    Returns dict mapping target -> {path, timestamp, target_display}
    """
    reports: dict[str, dict] = {}

    for fname in os.listdir(docs_dir):
        m = REPORT_PATTERN.match(fname)
        if not m:
            continue
        target = m.group(1)
        ts = m.group(2)

        if target not in reports or ts > reports[target]["timestamp"]:
            # Parse target: Ascend_pytorch -> Ascend/pytorch (single repo)
            #               Ascend_multi   -> Ascend        (org-level)
            if target.endswith("_multi"):
                display = target[:-6]  # strip _multi suffix
                is_org = True
            elif "_" in target:
                display = target.replace("_", "/", 1)
                is_org = False
            else:
                display = target
                is_org = False

            reports[target] = {
                "filename": fname,
                "filepath": os.path.join(docs_dir, fname),
                "timestamp": ts,
                "target": display,
                "is_org": is_org,
            }

    return dict(sorted(reports.items()))


def parse_report_stats(filepath: str) -> dict:
    """Extract summary statistics from a report markdown file."""
    stats: dict[str, int] = {}
    repo_counts: dict[str, int] = {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return {"total": 0, "infra": 0, "categories": {}, "repos": {}}

    in_repo_section = False
    for line in content.split("\n"):
        line = line.strip()

        if "### 按仓库统计" in line:
            in_repo_section = True
            continue
        elif in_repo_section and line.startswith("##"):
            in_repo_section = False

        if in_repo_section:
            m = REPO_LINE.match(line) or REPO_PLAIN_LINE.match(line)
            if m:
                repo_counts[m.group(1)] = int(m.group(2))
            continue

        # Match stat lines like "- ci/cd: 6" or "- 总 issues (获取): **90**"
        if line.startswith("- 总 issues"):
            m = re.search(r"(\d+)", line)
            if m:
                stats["total"] = int(m.group(1))
        elif line.startswith("- 基础设施类"):
            m = re.search(r"(\d+)", line)
            if m:
                stats["infra"] = int(m.group(1))
        elif line.startswith("- ") and ": " in line:
            m = STAT_LINE.match(line)
            if m:
                cat = line.split(":")[0].lstrip("- ").strip()
                if cat not in ("总 issues", "基础设施类"):
                    stats.setdefault("categories", {})[cat] = int(m.group(1))

    stats["repos"] = repo_counts
    return stats


def render_html(reports: list[dict], output_path: str) -> None:
    """Render the index.html page."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build report cards
    cards_html = ""
    for r in reports:
        target = r["target"]
        stats = r.get("stats", {})
        total = stats.get("total", "?")
        infra = stats.get("infra", "?")
        cats = stats.get("categories", {})
        repos = stats.get("repos", {})
        ts = r["timestamp"]

        # Format timestamp
        try:
            dt = datetime.strptime(ts, "%Y%m%d_%H%M")
            ts_display = dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            ts_display = ts

        # Category tags
        cat_tags = ""
        for cat, count in sorted(cats.items()):
            cat_tags += f'<span class="tag">{cat}: {count}</span>'

        # Repo links
        repo_links = ""
        for repo_name, count in repos.items():
            repo_links += f'<a href="https://gitcode.com/{repo_name}/pulls" class="repo-link" target="_blank">{repo_name}: {count}</a>'

        perc = round(infra / total * 100, 1) if isinstance(total, int) and isinstance(infra, int) and total > 0 else 0

        if r.get("is_org"):
            target_url = f"https://gitcode.com/{target}"
        else:
            target_url = f"https://gitcode.com/{target}/pulls"

        cards_html += f"""
        <div class="card">
            <div class="card-header">
                <h2>
                    <a href="{target_url}" target="_blank" class="target-link">{target}</a>
                </h2>
                <span class="badge infra">{infra} infra</span>
                <span class="badge total">{total} total</span>
                <span class="perc">{perc}%</span>
            </div>
            <div class="card-body">
                <div class="report-link">
                    📄 <a href="{r['filename']}">最新报告 ({ts_display})</a>
                </div>"""

        if cat_tags:
            cards_html += f"""
                <div class="tags">{cat_tags}</div>"""

        if repo_links:
            cards_html += f"""
                <div class="repo-links">{repo_links}</div>"""

        cards_html += """
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GitCode Issue 基础设施分析 Dashboard</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f5f7fa;
    color: #333;
    line-height: 1.6;
}}
.container {{ max-width: 960px; margin: 0 auto; padding: 32px 16px; }}
.header {{
    text-align: center; margin-bottom: 40px;
}}
.header h1 {{
    font-size: 28px; color: #1a1a2e; margin-bottom: 8px;
}}
.header .subtitle {{ color: #666; font-size: 14px; }}
.card {{
    background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 20px; overflow: hidden; transition: box-shadow 0.2s;
}}
.card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.12); }}
.card-header {{
    padding: 18px 24px; border-bottom: 1px solid #eee;
    display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}}
.card-header h2 {{ font-size: 18px; flex: 1; min-width: 150px; }}
.target-link {{
    color: #1a1a2e; text-decoration: none;
}}
.target-link:hover {{ color: #4a6cf7; text-decoration: underline; }}
.badge {{
    display: inline-block; padding: 3px 10px; border-radius: 12px;
    font-size: 13px; font-weight: 600;
}}
.badge.infra {{ background: #fff3cd; color: #856404; }}
.badge.total {{ background: #e8f0fe; color: #174ea6; }}
.perc {{ font-size: 13px; color: #888; font-weight: 500; }}
.card-body {{ padding: 16px 24px; }}
.report-link {{ margin-bottom: 10px; font-size: 14px; }}
.report-link a {{ color: #4a6cf7; text-decoration: none; }}
.report-link a:hover {{ text-decoration: underline; }}
.tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }}
.tag {{
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    background: #eef1ff; color: #4a6cf7; font-size: 12px;
}}
.repo-links {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.repo-link {{
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    background: #f0f0f0; color: #555; font-size: 12px; text-decoration: none;
}}
.repo-link:hover {{ background: #e0e0e0; color: #333; }}
.footer {{ text-align: center; margin-top: 40px; color: #999; font-size: 13px; }}
.empty {{ text-align: center; padding: 60px 20px; color: #999; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🔍 GitCode Issue 基础设施分析</h1>
        <p class="subtitle">Automated infrastructure issue detection across repositories · Generated at {now}</p>
    </div>

    {cards_html if cards_html else '<div class="empty"><p>暂无分析报告。运行 gitcode-issue-analyzer 生成报告后刷新此页面。</p></div>'}

    <div class="footer">
        <p>Generated by GitCode Issue Analysis Dashboard · <a href="https://gitcode.com" style="color:#999;">GitCode</a></p>
    </div>
</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def main() -> int:
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "docs"
    output = sys.argv[2] if len(sys.argv) > 2 else os.path.join(docs_dir, "index.html")

    if not os.path.isdir(docs_dir):
        print(f"Error: docs directory not found: {docs_dir}")
        return 1

    latest = find_latest_reports(docs_dir)

    if not latest:
        print("No reports found in docs/")
        # Still generate an empty page
        render_html([], output)
        print(f"Empty index page generated: {output}")
        return 0

    print(f"Found {len(latest)} target(s) with reports:")
    reports = []
    for target, info in sorted(latest.items()):
        stats = parse_report_stats(info["filepath"])
        info["stats"] = stats
        reports.append(info)
        print(f"  {info['target']}: {info['filename']} "
              f"(total={stats.get('total','?')}, infra={stats.get('infra','?')})")

    render_html(reports, output)
    print(f"\nIndex page generated: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
