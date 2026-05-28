#!/usr/bin/env python3
"""GitCode Issue Analyzer — CLI entry point.

Fetches issues from a GitCode repo or community using gc CLI,
saves raw data, and supports AI-based infrastructure issue classification.

Usage:
    python3 analyze.py <target> [--days N] [--raw-file PATH]
    python3 analyze.py --load-raw PATH [--classify PATH] [--format fmt]

Workflow:
    1. Fetch:   python3 analyze.py owner/repo --days 7
       → Fetches issues, saves to issues_raw.json

    2. AI classify (Claude Code reads issues_raw.json and outputs classification)

    3. Report:  python3 analyze.py --load-raw issues_raw.json --classify result.json
       → Generates markdown table of infrastructure issues
"""

import argparse
import json
import sys

from fetcher import fetch_issues, save_raw_issues, load_raw_issues
from classifier import (
    prepare_classification_input,
    parse_classification_result,
    merge_classification,
)
from reporter import generate_full_report, generate_summary, generate_table


def cmd_fetch(args: argparse.Namespace) -> int:
    """Fetch issues and save raw data."""
    issues = fetch_issues(args.target, days=args.days)
    if not issues:
        print("No issues found.")
        return 1

    save_raw_issues(issues, args.raw_file)

    # Also print the classification prompt for direct use with AI
    prompt = prepare_classification_input(issues)
    print()
    print("=" * 60)
    print("AI Classification Prompt (copy this for the LLM):")
    print("=" * 60)
    print(prompt)

    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Load raw data and generate a report."""
    issues = load_raw_issues(args.load_raw)
    print(f"Loaded {len(issues)} issues from {args.load_raw}")

    if args.classify:
        with open(args.classify, "r", encoding="utf-8") as f:
            classification_raw = f.read()
        classification = parse_classification_result(classification_raw)
        if not classification:
            print(f"[ERROR] Failed to parse classification from {args.classify}")
            return 1
        print(f"Parsed {len(classification)} classification results")
        issues = merge_classification(issues, classification)
    else:
        print("No classification provided, showing all issues as-is")

    filter_infra = args.category == "infra"

    if args.format == "json":
        output = json.dumps(
            [i for i in issues if not filter_infra or i.get("is_infra")],
            ensure_ascii=False,
            indent=2,
        )
    elif args.format == "csv":
        infra = [i for i in issues if not filter_infra or i.get("is_infra")]
        lines = ["repo,number,title,category,is_infra,reason,labels,state,created_at"]
        for i in infra:
            lines.append(
                f"{i['repo']},{i['number']},\"{i['title']}\","
                f"{i.get('category','')},{i.get('is_infra','')},\"{i.get('reason','')}\","
                f"\"{'|'.join(i.get('labels',[]))}\",{i['state']},{i['created_at']}"
            )
        output = "\n".join(lines)
    else:
        output = generate_full_report(issues, filter_infra=filter_infra)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        print(f"Report saved to: {args.output}")
    else:
        print(output)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GitCode Issue Analyzer — fetch and classify issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 analyze.py owner/repo
  python3 analyze.py my-org --days 14
  python3 analyze.py owner/repo --raw-file /tmp/issues.json
  python3 analyze.py --load-raw issues_raw.json --classify result.json
        """,
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Repository (owner/repo) or organization name",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)",
    )
    parser.add_argument(
        "--raw-file", "-r",
        default="./issues_raw.json",
        help="Path to save/load raw issue data (default: ./issues_raw.json)",
    )
    parser.add_argument(
        "--load-raw",
        help="Load raw issues from file instead of fetching",
    )
    parser.add_argument(
        "--classify",
        help="Path to AI classification result JSON",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--category",
        choices=["infra", "all"],
        default="infra",
        help="Filter category (default: infra)",
    )

    args = parser.parse_args()

    if args.load_raw:
        return cmd_report(args)

    if not args.target:
        parser.error("target is required unless --load-raw is specified")

    return cmd_fetch(args)


if __name__ == "__main__":
    sys.exit(main())
