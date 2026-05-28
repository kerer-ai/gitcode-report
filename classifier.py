"""AI classification data preparation.

Extracts minimal issue data (title + description only) to save tokens,
and parses AI classification results.
"""

import json

INFRA_CATEGORIES = [
    "ci/cd",
    "build",
    "dev-environment",
    "toolchain",
    "testing-infra",
    "deployment",
    "containerization",
    "monitoring",
    "logging",
    "alerting",
    "code-quality",
    "dependency-management",
    "developer-experience",
    "other-infra",
]

CLASSIFICATION_PROMPT_TEMPLATE = """你是一个 issue 分类助手。请分析以下 GitCode issues，判断每个 issue 是否属于"基础设施/工具链"类别。

基础设施类包括：
- CI/CD 流水线、构建系统、自动化
- 开发环境搭建、工具链配置
- 测试框架、测试基础设施
- 部署、容器化、Kubernetes、Docker
- 监控、日志、告警、可观测性
- 代码质量工具 (lint, format, static analysis)
- 开发辅助工具、脚本、自动化

不属于基础设施的：业务功能、UI/UX、产品需求、文档、常规 bug 修复、CVE/依赖安全漏洞等。

对每个 issue 输出一行 JSON：
{"repo": "<仓库名>", "number": <issue号>, "is_infra": true/false, "category": "<子分类|null>", "reason": "<一句话理由>"}

只输出 JSON 数组，不要其他内容。

以下是待分类的 issues：

"""


def prepare_classification_input(issues: list[dict]) -> str:
    """Extract only title + description from each issue and format as
    a compact text block for AI classification.

    Strips labels, state, author, timestamps, and other metadata to
    minimize token consumption.
    """
    lines = [CLASSIFICATION_PROMPT_TEMPLATE]

    for i, issue in enumerate(issues):
        lines.append(f"--- Issue #{i + 1} ---")
        lines.append(f"repo: {issue.get('repo', '')}")
        lines.append(f"number: {issue.get('number', '')}")
        lines.append(f"title: {issue.get('title', '')}")
        desc = issue.get("description", "") or ""
        if desc:
            lines.append(f"description: {desc[:500]}")
        lines.append("")

    return "\n".join(lines)


def parse_classification_result(raw: str) -> list[dict]:
    """Parse the AI classification result JSON into a list of dicts.

    Expected format: a JSON array of objects with fields:
    repo, number, is_infra, category, reason
    """
    raw = raw.strip()

    # Try to extract JSON array from markdown code blocks
    if "```" in raw:
        blocks = []
        in_block = False
        for line in raw.split("\n"):
            if line.startswith("```"):
                if in_block:
                    break
                in_block = True
                continue
            if in_block:
                blocks.append(line)
        if blocks:
            raw = "\n".join(blocks)

    # Try to find JSON array boundaries
    raw = raw.strip()
    if not raw.startswith("["):
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            raw = raw[start : end + 1]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: try to parse line by line
        results = []
        for line in raw.split("\n"):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return results


def merge_classification(
    raw_issues: list[dict], classification: list[dict]
) -> list[dict]:
    """Merge classification results back into raw issue data.

    Matches by (repo, number) from classification to raw issues.
    """
    class_map = {}
    for c in classification:
        key = (c.get("repo", ""), c.get("number"))
        class_map[key] = c

    merged = []
    for issue in raw_issues:
        key = (issue.get("repo", ""), issue.get("number"))
        if key in class_map:
            c = class_map[key]
            issue["is_infra"] = c.get("is_infra", False)
            issue["category"] = c.get("category", "")
            issue["reason"] = c.get("reason", "")
        else:
            issue["is_infra"] = False
            issue["category"] = ""
            issue["reason"] = ""
        merged.append(issue)

    return merged
