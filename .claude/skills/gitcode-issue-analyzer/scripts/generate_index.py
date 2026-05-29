#!/usr/bin/env python3
"""Dashboard HTML renderer for GitCode issue analysis reports.

This script does NOT parse markdown reports. Data extraction and insight
generation is done by the LLM, which reads reports and produces structured
JSON. This script only handles:

1. --list    : discover latest report files per target (file I/O only)
2. --render  : take LLM-produced data JSON and render the styled HTML page
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

REPORT_PATTERN = re.compile(r"^(.+)_(\d{8}_\d{4})\.md$")


def cmd_list(docs_dir: str) -> int:
    """Discover latest report file for each target. No content parsing."""
    if not os.path.isdir(docs_dir):
        print(f"Error: directory not found: {docs_dir}", file=sys.stderr)
        return 1

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
                "file": fname,
                "target": display,
                "is_org": is_org,
                "timestamp": ts,
            }

    result = sorted(reports.values(), key=lambda r: r["target"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_render(data_file: str, output_path: str) -> int:
    """Render the HTML dashboard from LLM-extracted structured data.

    Expected JSON schema:
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
        },
        ...
      ],
      "category_totals": {"build": 39, "testing-infra": 37, ...},
      "insights": [
        "<strong>标题：</strong>描述内容...",
        ...
      ]
    }
    """
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error reading data file: {e}", file=sys.stderr)
        return 1

    html = _render_html(data)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Index page generated: {output_path}")
    return 0


# -- Category display config --
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


def _fmt_num(n) -> str:
    if isinstance(n, int) and n >= 1000:
        return f"{n:,}"
    return str(n)


def _pct(part, total) -> str:
    if total > 0:
        return f"{round(part / total * 100, 1)}%"
    return "0%"


def _pct_val(part, total) -> float:
    if total > 0:
        return round(part / total * 100, 1)
    return 0.0


def _render_html(data: dict) -> str:
    date_str = data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    totals = data.get("totals", {})
    communities = data.get("communities", [])
    category_totals = data.get("category_totals", {})
    insights = data.get("insights", [])

    overall_ratio = _pct(totals.get("infra", 0), totals.get("total", 0))

    # -- Summary cards --
    summary_cards = f"""
<div class="summary-grid">
  <div class="summary-card total">
    <div class="value">{_fmt_num(totals.get('total', 0))}</div>
    <div class="label">总 Issues（7天内）</div>
  </div>
  <div class="summary-card infra">
    <div class="value">{totals.get('infra', 0)}</div>
    <div class="label">基础设施类 Issues</div>
  </div>
  <div class="summary-card repos">
    <div class="value">{totals.get('repos', 0)}</div>
    <div class="label">覆盖仓库数</div>
  </div>
  <div class="summary-card ratio">
    <div class="value">{overall_ratio}</div>
    <div class="label">基础设施占比</div>
  </div>
</div>"""

    # -- Community overview table --
    comm_rows = ""
    for c in communities:
        name = c["name"]
        is_org = c.get("is_org", False)
        n_repos = c.get("n_repos", 0)
        t = c.get("total", 0)
        inf = c.get("infra", 0)
        ratio = _pct(inf, t)
        ratio_val = _pct_val(inf, t)
        rtype = "组织" if is_org else "仓库"
        bar_w = min(int(ratio_val * 2.5), 250)

        if is_org:
            tgt_link = f'<a href="https://gitcode.com/{name}" style="color:#0f3460;text-decoration:none;" target="_blank">{name}</a>'
        else:
            tgt_link = f'<a href="https://gitcode.com/{name}/pulls" style="color:#0f3460;text-decoration:none;" target="_blank">{name}</a>'

        comm_rows += f"""
      <tr>
        <td class="community-name">{tgt_link}</td>
        <td>{rtype}</td>
        <td>{n_repos if n_repos > 0 else '—'}</td>
        <td>{t}</td>
        <td>{inf}</td>
        <td>{ratio}</td>
        <td class="bar-cell"><div class="bar" style="width:{bar_w}px"></div></td>
      </tr>"""

    # Total row
    total_bar = min(int(_pct_val(totals.get("infra", 0), totals.get("total", 1)) * 2.5), 250)
    comm_rows += f"""
      <tr style="font-weight:700; background:#fafbfc;">
        <td class="community-name">合计</td>
        <td>—</td>
        <td>{totals.get('repos', 0)}</td>
        <td>{_fmt_num(totals.get('total', 0))}</td>
        <td>{totals.get('infra', 0)}</td>
        <td>{overall_ratio}</td>
        <td class="bar-cell"><div class="bar" style="width:{total_bar}px"></div></td>
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
        <th class="bar-cell">基础设施占比</th>
      </tr>
    </thead>
    <tbody>{comm_rows}
    </tbody>
  </table>
  </div>
</div>"""

    # -- Category distribution --
    max_cat = max(category_totals.values()) if category_totals else 1
    bar_items = ""
    for i, (cat_key, cat_label) in enumerate(ALL_CATEGORIES):
        count = category_totals.get(cat_key, 0)
        if count == 0:
            continue
        pct = round(count / max_cat * 100)
        color = BAR_COLORS[i % len(BAR_COLORS)]
        bar_items += f"""
        <div class="bar-item">
          <div class="bar-label">{cat_label}</div>
          <div class="bar-track"><div class="bar-fill {color}" style="width:{max(pct, 5)}%">{count}</div></div>
        </div>"""

    short_cats = [c for c, _ in ALL_CATEGORIES[:7]]
    cat_table_header = "<th>社区</th>" + "".join(
        f"<th>{dict(ALL_CATEGORIES).get(c, c).replace('-', '<br>-')}</th>" for c in short_cats
    )
    cat_table_rows = ""
    for c in communities:
        cats = c.get("categories", {})
        cells = "".join(f"<td>{cats.get(cat, 0)}</td>" for cat in short_cats)
        cat_table_rows += f'<tr><td class="community-name">{c["name"]}</td>{cells}</tr>'

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
    insight_html = ""
    for ins in insights:
        insight_html += f'\n  <div class="insight-box">{ins}\n  </div>'

    # -- Detail report links --
    report_links = ""
    for c in communities:
        name = c["name"]
        n_repos = c.get("n_repos", 0)
        desc = name
        if c.get("is_org") and n_repos > 0:
            desc += f" ({n_repos} repos)"
        rf = c.get("report_file", "")
        report_links += f"""
      <tr><td class="community-name">{desc}</td><td><a href="viewer.html?file={rf}">{rf}</a></td><td>{c.get('total', 0)}</td><td>{c.get('infra', 0)}</td><td>{c.get('report_ts', '')}</td></tr>"""

    # -- Full page --
    return f"""<!DOCTYPE html>
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

  .bar-chart .bar-item {{ display: flex; align-items: center; margin-bottom: 8px; }}
  .bar-chart .bar-label {{ width: 140px; font-size: 0.85em; color: #555; text-align: right; padding-right: 12px; flex-shrink: 0; }}
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
    .bar-chart .bar-label {{ width: 100px; font-size: 0.75em; }}
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


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="GitCode Dashboard Renderer")
    sub = parser.add_subparsers(dest="command")

    list_p = sub.add_parser("list", help="Discover latest report files")
    list_p.add_argument("docs_dir", nargs="?", default="docs")

    render_p = sub.add_parser("render", help="Render HTML from LLM data JSON")
    render_p.add_argument("data_file", help="Path to LLM-produced data JSON")
    render_p.add_argument("output", nargs="?", default=None)

    args = parser.parse_args()

    if args.command == "list":
        return cmd_list(args.docs_dir)
    elif args.command == "render":
        output = args.output or os.path.join(
            os.path.dirname(args.data_file), "index.html"
        )
        return cmd_render(args.data_file, output)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
