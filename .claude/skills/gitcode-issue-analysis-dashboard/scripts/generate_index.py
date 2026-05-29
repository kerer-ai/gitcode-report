#!/usr/bin/env python3
"""Generate a comprehensive index.html dashboard from the latest GitCode issue analysis reports.

Scans docs/ for report files named <target>_<timestamp>.md, groups by target,
selects the latest report for each, aggregates stats across all communities,
and renders a full-featured HTML dashboard page.
"""

import os
import re
import sys
from datetime import datetime, timezone
from collections import Counter

REPORT_PATTERN = re.compile(r"^(.+)_(\d{8}_\d{4})\.md$")
STAT_LINE = re.compile(
    r"^- (?:ci/cd|build|testing-infra|toolchain|dev-environment|code-quality|"
    r"deployment|containerization|monitoring|logging|alerting|"
    r"dependency-management|developer-experience|other-infra)[：:]\s*\*?\*?(\d+)\*?\*?"
)
REPO_LINK_LINE = re.compile(r"^- \[(.+?)\]\(.+?\):\s*(\d+)")
REPO_PLAIN_LINE = re.compile(r"^- ([^\[][^:]+?):\s*(\d+)$")
TAG_LINE = re.compile(r"infra-tooling.*?(\d+)")

ALL_CATEGORIES = [
    ("testing-infra", "测试基础设施"),
    ("build", "构建系统"),
    ("toolchain", "工具链"),
    ("ci/cd", "持续集成"),
    ("dev-environment", "开发环境"),
    ("code-quality", "代码质量工具"),
    ("developer-experience", "开发体验"),
    ("monitoring", "监控"),
    ("dependency-management", "依赖管理"),
    ("logging", "日志"),
    ("deployment", "部署"),
    ("containerization", "容器化"),
    ("other-infra", "其他"),
]

BAR_COLORS = ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c1", "c2", "c3", "c4", "c5", "c6"]


def find_latest_reports(docs_dir: str) -> dict[str, dict]:
    """Find the latest report file for each target in docs_dir."""
    reports: dict[str, dict] = {}

    for fname in os.listdir(docs_dir):
        if fname == "index.html":
            continue
        m = REPORT_PATTERN.match(fname)
        if not m:
            continue
        target = m.group(1)
        ts = m.group(2)

        if target not in reports or ts > reports[target]["timestamp"]:
            if target.endswith("_multi"):
                display = target[:-6]
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


def parse_report(filepath: str) -> dict:
    """Extract full statistics from a report markdown file.

    Handles both new-format reports (with ## 汇总 and ### 按子分类统计 sections)
    and old-format reports that use a compact single-line summary.
    """
    stats: dict = {
        "total": 0,
        "infra": 0,
        "categories": {},
        "repos": {},
    }

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return stats

    in_repo_section = False
    in_category_section = False

    for line in content.split("\n"):
        line_stripped = line.strip()

        # Track which sub-section we are in
        if "### 按仓库统计" in line_stripped:
            in_repo_section = True
            in_category_section = False
            continue
        elif "### 按子分类统计" in line_stripped:
            in_category_section = True
            in_repo_section = False
            continue
        elif line_stripped.startswith("## "):
            in_repo_section = False
            in_category_section = False

        # Parse repo stats
        if in_repo_section:
            if line_stripped == "- (无)":
                continue
            m = REPO_LINK_LINE.match(line_stripped) or REPO_PLAIN_LINE.match(line_stripped)
            if m:
                stats["repos"][m.group(1)] = int(m.group(2))
            continue

        # Parse category stats
        if in_category_section:
            if line_stripped == "- (无)":
                continue
            m = STAT_LINE.match(line_stripped)
            if m:
                cat = line_stripped.split(":")[0].lstrip("- ").strip()
                stats["categories"][cat] = int(m.group(1))
            continue

        # Parse total / infra count (new format with ** markers)
        if line_stripped.startswith("- 总 issues"):
            m = re.search(r"(\d+)", line_stripped)
            if m:
                stats["total"] = int(m.group(1))
        elif line_stripped.startswith("- 基础设施类"):
            m = re.search(r"(\d+)", line_stripped)
            if m:
                stats["infra"] = int(m.group(1))

        # Fallback: old compact format "总 issues: N, 基础设施类: 0"
        if "总 issues:" in line_stripped and "基础设施类:" in line_stripped and not line_stripped.startswith("-"):
            m_total = re.search(r"总 issues:\s*(\d+)", line_stripped)
            m_infra = re.search(r"基础设施类:\s*(\d+)", line_stripped)
            if m_total:
                stats["total"] = int(m_total.group(1))
            if m_infra:
                stats["infra"] = int(m_infra.group(1))

    # Also try to get total from the header table as fallback
    if stats["total"] == 0:
        m = re.search(r"获取 Issue 总数\s*\|\s*\*?\*?(\d+)\*?\*?", content)
        if m:
            stats["total"] = int(m.group(1))

    return stats


def _fmt_num(n) -> str:
    """Format number with commas for thousands."""
    if isinstance(n, int) and n >= 1000:
        return f"{n:,}"
    return str(n)


def _pct(part, total) -> str:
    if total > 0 and isinstance(part, int) and isinstance(total, int):
        return f"{round(part / total * 100, 1)}%"
    return "0%"


def _pct_val(part, total) -> float:
    if total > 0 and isinstance(part, int) and isinstance(total, int):
        return round(part / total * 100, 1)
    return 0.0


def _ts_display(ts: str) -> str:
    try:
        dt = datetime.strptime(ts, "%Y%m%d_%H%M")
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return ts


def _generate_insights(reports: list[dict], totals: dict) -> list[str]:
    """Auto-generate key insights based on data patterns."""
    insights = []

    # Find dominant category per community
    for r in reports:
        cats = r.get("stats", {}).get("categories", {})
        if cats:
            top_cat = max(cats, key=cats.get)
            top_count = cats[top_cat]
            infra = r.get("stats", {}).get("infra", 0)
            if infra > 0 and top_count > 0:
                cat_pct = round(top_count / infra * 100, 1)
                if cat_pct >= 30:
                    cat_label = dict(ALL_CATEGORIES).get(top_cat, top_cat)
                    insights.append(
                        f'<strong>{r["target"]} {cat_label}问题集中：</strong>'
                        f'该社区基础设施 issue 中，<strong>{cat_label}（{top_cat}）</strong>'
                        f'占比达 {cat_pct}%（{top_count}/{infra}）。'
                    )

    # Low infrastructure
    for r in reports:
        infra = r.get("stats", {}).get("infra", 0)
        total = r.get("stats", {}).get("total", 0)
        if total >= 10 and infra == 0:
            insights.append(
                f'<strong>{r["target"]} 规模小但无基础设施关注：</strong>'
                f'{total} 个 issue 中无基础设施类，该社区可能缺乏 CI/测试基础设施方面的投入。'
            )

    # Cross-community common issues
    infra_total = totals["infra"]
    all_cats = Counter()
    for r in reports:
        for cat, count in r.get("stats", {}).get("categories", {}).items():
            all_cats[cat] += count
    if all_cats and infra_total > 0:
        top2 = all_cats.most_common(2)
        if len(top2) >= 2 and (top2[0][1] + top2[1][1]) > 0:
            insights.append(
                f'<strong>{dict(ALL_CATEGORIES).get(top2[0][0], top2[0][0])} 与 '
                f'{dict(ALL_CATEGORIES).get(top2[1][0], top2[1][0])} 是跨社区共性痛点：</strong>'
                f'两者合计占全部基础设施 issue 的 {round((top2[0][1]+top2[1][1])/infra_total*100, 1)}%'
                f'（{top2[0][1]}+{top2[1][1]}/{infra_total}），多个仓库均存在相关问题。'
            )

    return insights[:5]


def render_html(reports: list[dict], output_path: str) -> None:
    """Render the comprehensive dashboard index.html page."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if not reports:
        _write_empty(output_path, now_str)
        return

    # -- Aggregate totals --
    totals = {
        "total": sum(r["stats"]["total"] for r in reports),
        "infra": sum(r["stats"]["infra"] for r in reports),
    }
    # Count distinct repos (from report repo stats)
    all_repos: set = set()
    for r in reports:
        all_repos.update(r["stats"]["repos"].keys())
    totals["repos"] = len(all_repos)

    # Merge categories across all reports
    merged_cats: Counter = Counter()
    for r in reports:
        for cat, count in r["stats"].get("categories", {}).items():
            merged_cats[cat] += count

    overall_ratio = _pct(totals["infra"], totals["total"])

    # -- Summary cards --
    summary_cards = f"""
<div class="summary-grid">
  <div class="summary-card total">
    <div class="value">{_fmt_num(totals['total'])}</div>
    <div class="label">总 Issues（7天内）</div>
  </div>
  <div class="summary-card infra">
    <div class="value">{totals['infra']}</div>
    <div class="label">基础设施类 Issues</div>
  </div>
  <div class="summary-card repos">
    <div class="value">{totals['repos']}</div>
    <div class="label">覆盖仓库数</div>
  </div>
  <div class="summary-card ratio">
    <div class="value">{overall_ratio}</div>
    <div class="label">基础设施占比</div>
  </div>
</div>"""

    # -- Community overview table --
    comm_rows = ""
    for r in reports:
        s = r["stats"]
        t = s["total"]
        inf = s["infra"]
        ratio = _pct(inf, t)
        ratio_val = _pct_val(inf, t)
        n_repos = len(s["repos"])
        rtype = "组织" if r["is_org"] else "仓库"
        # Tag counts are not extractable from reports; show placeholder
        tag_count_display = "—"
        tag_cov = "—"
        tag_cls = "low"
        bar_w = min(int(ratio_val * 2.5), 250)

        # Build target link
        if r["is_org"]:
            tgt_link = f'<a href="https://gitcode.com/{r["target"]}" style="color:#0f3460;text-decoration:none;" target="_blank">{r["target"]}</a>'
        else:
            tgt_link = f'<a href="https://gitcode.com/{r["target"]}/pulls" style="color:#0f3460;text-decoration:none;" target="_blank">{r["target"]}</a>'

        comm_rows += f"""
      <tr>
        <td class="community-name">{tgt_link}</td>
        <td>{rtype}</td>
        <td>{n_repos if n_repos > 0 else '—'}</td>
        <td>{t}</td>
        <td>{inf}</td>
        <td>{ratio}</td>
        <td>{tag_count_display}</td>
        <td><span class="tag {tag_cls}">{tag_cov}</span></td>
        <td class="bar-cell"><div class="bar" style="width:{bar_w}px"></div></td>
      </tr>"""

    # Total row
    comm_rows += f"""
      <tr style="font-weight:700; background:#fafbfc;">
        <td class="community-name">合计</td>
        <td>—</td>
        <td>{totals['repos']}</td>
        <td>{_fmt_num(totals['total'])}</td>
        <td>{totals['infra']}</td>
        <td>{overall_ratio}</td>
        <td>—</td>
        <td><span class="tag low">—</span></td>
        <td class="bar-cell"><div class="bar" style="width:{min(int(_pct_val(totals['infra'], totals['total']) * 2.5), 250)}px"></div></td>
      </tr>"""

    community_table = f"""
<div class="section">
  <h2>各社区基础设施 Issue 概况</h2>
  <div class="table-wrap">
  <table class="community-table">
    <thead>
      <tr>
        <th>社区/组织</th>
        <th>类型</th>
        <th>仓库数</th>
        <th>总 Issues</th>
        <th>基础设施类</th>
        <th>占比</th>
        <th>infra-tooling 标签数</th>
        <th>标签覆盖率</th>
        <th class="bar-cell">基础设施占比</th>
      </tr>
    </thead>
    <tbody>{comm_rows}
    </tbody>
  </table>
  </div>
</div>"""

    # -- Category distribution --
    # Bar chart (all communities merged)
    max_cat = max(merged_cats.values()) if merged_cats else 1
    bar_items = ""
    for i, (cat_key, cat_label) in enumerate(ALL_CATEGORIES):
        count = merged_cats.get(cat_key, 0)
        if count == 0:
            continue
        pct = round(count / max_cat * 100)
        color = BAR_COLORS[i % len(BAR_COLORS)]
        bar_items += f"""
        <div class="bar-item">
          <div class="bar-label">{cat_label} ({cat_key})</div>
          <div class="bar-track"><div class="bar-fill {color}" style="width:{max(pct, 5)}%">{count}</div></div>
        </div>"""

    # Cross-community category table
    short_cats = [c for c, _ in ALL_CATEGORIES[:7]]  # first 7 categories
    cat_table_header = "<th>社区</th>" + "".join(f"<th>{dict(ALL_CATEGORIES).get(c, c).replace('-', '<br>-')}</th>" for c in short_cats)
    cat_table_rows = ""
    for r in reports:
        cats = r["stats"].get("categories", {})
        cells = "".join(f"<td>{cats.get(c, 0)}</td>" for c in short_cats)
        cat_table_rows += f'<tr><td class="community-name">{r["target"]}</td>{cells}</tr>'

    category_section = f"""
<div class="chart-row">
  <div class="chart-box">
    <div class="section" style="padding:20px;">
      <h2>基础设施子分类分布（全社区）</h2>
      <div class="bar-chart">{bar_items}
      </div>
    </div>
  </div>

  <div class="chart-box">
    <div class="section" style="padding:20px;">
      <h2>各社区分类构成</h2>
      <div class="table-wrap">
      <table class="community-table category-table">
        <thead><tr>{cat_table_header}</tr></thead>
        <tbody>{cat_table_rows}
        </tbody>
      </table>
      </div>
    </div>
  </div>
</div>"""

    # -- Insights --
    insights = _generate_insights(reports, totals)
    insight_html = ""
    for ins in insights:
        insight_html += f'\n  <div class="insight-box">{ins}\n  </div>'

    # -- Detail report links --
    report_links = ""
    for r in reports:
        s = r["stats"]
        n_repos = len(s["repos"])
        desc = f"{r['target']}"
        if r["is_org"] and n_repos > 0:
            desc += f" ({n_repos} repos)"
        report_links += f"""
      <tr><td class="community-name">{desc}</td><td><a href="viewer.html?file={r['filename']}">{r['filename']}</a></td><td>{s['total']}</td><td>{s['infra']}</td><td>{_ts_display(r['timestamp'])}</td></tr>"""

    # -- Final HTML --
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>社区基础设施 VOC 分析报告</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; color: #333; line-height: 1.6; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}

  .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: #fff; padding: 48px 0; text-align: center; margin-bottom: 32px; border-radius: 0 0 24px 24px; }}
  .header h1 {{ font-size: 2.2em; margin-bottom: 8px; }}
  .header p {{ font-size: 1.1em; opacity: 0.8; }}

  .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 32px; }}
  .summary-card {{ background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); text-align: center; }}
  .summary-card .value {{ font-size: 2.4em; font-weight: 700; }}
  .summary-card .label {{ color: #666; font-size: 0.95em; margin-top: 4px; }}
  .summary-card.total .value {{ color: #0f3460; }}
  .summary-card.infra .value {{ color: #e94560; }}
  .summary-card.repos .value {{ color: #533483; }}
  .summary-card.ratio .value {{ color: #0d7377; }}

  .section {{ background: #fff; border-radius: 12px; padding: 28px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
  .section h2 {{ font-size: 1.4em; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #e94560; color: #1a1a2e; }}

  .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  .community-table {{ width: 100%; border-collapse: collapse; white-space: nowrap; }}
  .community-table th {{ background: #f0f2f5; text-align: left; padding: 10px 12px; font-weight: 600; color: #555; border-bottom: 2px solid #ddd; font-size: 0.9em; }}
  .community-table td {{ padding: 10px 12px; border-bottom: 1px solid #eee; font-size: 0.9em; }}
  .community-table tr:hover {{ background: #fafbfc; }}
  .community-table .community-name {{ font-weight: 600; color: #0f3460; }}
  .bar-cell {{ width: 100px; }}
  .bar {{ height: 8px; border-radius: 4px; background: #e94560; }}
  .category-table td, .category-table th {{ text-align: center; }}

  .chart-row {{ display: flex; gap: 24px; margin-bottom: 24px; flex-wrap: wrap; }}
  .chart-box {{ flex: 1; min-width: 280px; max-width: 100%; }}
  .chart-box h3 {{ font-size: 1.05em; color: #555; margin-bottom: 12px; }}

  .bar-chart .bar-item {{ display: flex; align-items: center; margin-bottom: 8px; }}
  .bar-chart .bar-label {{ width: 160px; font-size: 0.9em; color: #555; text-align: right; padding-right: 12px; flex-shrink: 0; }}
  .bar-chart .bar-track {{ flex: 1; background: #f0f2f5; border-radius: 4px; height: 22px; position: relative; overflow: hidden; }}
  .bar-chart .bar-fill {{ height: 100%; border-radius: 4px; display: flex; align-items: center; padding-left: 8px; font-size: 0.8em; color: #fff; font-weight: 600; }}
  .bar-chart .bar-fill.c1 {{ background: #e94560; }}
  .bar-chart .bar-fill.c2 {{ background: #533483; }}
  .bar-chart .bar-fill.c3 {{ background: #0d7377; }}
  .bar-chart .bar-fill.c4 {{ background: #f39c12; }}
  .bar-chart .bar-fill.c5 {{ background: #2980b9; }}
  .bar-chart .bar-fill.c6 {{ background: #27ae60; }}
  .bar-chart .bar-fill.c7 {{ background: #8e44ad; }}

  .insight-box {{ background: #fff8e1; border-left: 4px solid #f39c12; padding: 16px 20px; margin: 16px 0; border-radius: 0 8px 8px 0; }}
  .insight-box strong {{ color: #e67e22; }}

  .footer {{ text-align: center; color: #999; padding: 24px 0; font-size: 0.85em; }}

  .tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 600; }}
  .tag.high {{ background: #ffeaea; color: #e94560; }}
  .tag.mid {{ background: #fff3e0; color: #f39c12; }}
  .tag.low {{ background: #e8f5e9; color: #27ae60; }}

  @media (max-width: 768px) {{
    .chart-row {{ flex-direction: column; }}
    .bar-chart .bar-label {{ width: 120px; font-size: 0.8em; }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>社区基础设施 VOC 分析报告</h1>
  <p>基于 AI 分类的 GitCode 社区 Issue 基础设施类问题识别 | {date_str}</p>
</div>

<div class="container">

{summary_cards}

{community_table}

{category_section}

<div class="section">
  <h2>关键洞察</h2>{insight_html}
</div>

<div class="section">
  <h2>各社区详细报告</h2>
  <table class="community-table">
    <thead><tr><th>社区</th><th>报告文件</th><th>总 Issues</th><th>基础设施类</th><th>生成时间</th></tr></thead>
    <tbody>{report_links}
    </tbody>
  </table>
</div>

<div class="section">
  <h2>分析方法说明</h2>
  <p style="color:#666; font-size:0.95em;">
    本报告基于 <strong>GitCode Issue Analyzer</strong> 工具自动生成，通过 <code>gc</code> CLI 获取指定社区/仓库最近 7 天的全部 issues，
    再由 AI（大模型）根据标题和正文内容逐一判断是否属于基础设施类问题。
  </p>
  <p style="color:#666; font-size:0.95em; margin-top:8px;">
    <strong>基础设施类判定标准：</strong>CI/CD 流水线、构建系统、测试框架/基础设施、开发环境、工具链配置、代码质量工具、部署与容器化、监控与日志、开发者工具与脚本。
  </p>
  <p style="color:#666; font-size:0.95em; margin-top:8px;">
    <strong>排除范围：</strong>业务功能、文档反馈、算子/模型 bug、CVE 安全漏洞、API 一致性分析、功能 RFC、代码重构/清理、编译器新功能增强。
  </p>
</div>

<div class="footer">
  Generated by GitCode Issue Analyzer &mdash; {date_str}
</div>

</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def _write_empty(output_path: str, now_str: str) -> None:
    """Generate an empty placeholder page."""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>社区基础设施 VOC 分析报告</title></head>
<body style="font-family:sans-serif;text-align:center;padding:80px 20px;color:#999;">
  <h1>社区基础设施 VOC 分析报告</h1>
  <p>暂无分析报告。运行 gitcode-issue-analyzer 生成报告后刷新此页面。</p>
  <p style="font-size:0.85em;">{now_str}</p>
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
        _write_empty(output, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
        print(f"Empty index page generated: {output}")
        return 0

    print(f"Found {len(latest)} target(s) with reports:")
    reports = []
    for target, info in sorted(latest.items()):
        stats = parse_report(info["filepath"])
        info["stats"] = stats
        reports.append(info)
        n_repos = len(stats["repos"])
        print(f"  {info['target']}: {info['filename']} "
              f"(total={stats['total']}, infra={stats['infra']}, repos={n_repos})")

    render_html(reports, output)
    print(f"\nIndex page generated: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
