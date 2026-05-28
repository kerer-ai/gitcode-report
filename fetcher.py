"""Issue fetching orchestration — single repo or community-wide."""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

from gc_wrapper import GCError, list_issues, list_repos


def _compute_created_after(days: int) -> str:
    """Compute the --created-after date string in ISO 8601 format."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    return since.strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_repo(target: str) -> bool:
    """A target with '/' is treated as a single repo, otherwise an org."""
    return "/" in target


def _normalize_issue(raw: dict, repo: str) -> dict:
    """Normalize a raw issue dict from gc into a consistent format.

    Handles both `gc issue list --json` and `gc issue view --json` formats.
    """
    labels = raw.get("labels", [])
    if isinstance(labels, list):
        label_names = [
            lb["name"] if isinstance(lb, dict) else str(lb) for lb in labels
        ]
    else:
        label_names = []

    # Author field: gc uses "user", fall back to "author"
    user = raw.get("user", raw.get("author", {}))
    if isinstance(user, dict):
        author_name = user.get("login", user.get("username", ""))
    else:
        author_name = str(user) if user else ""

    return {
        "repo": repo,
        "number": raw.get("number", raw.get("iid", "")),
        "title": raw.get("title", ""),
        "description": raw.get("body", raw.get("description", "")),
        "labels": label_names,
        "state": raw.get("state", ""),
        "created_at": raw.get("created_at", ""),
        "updated_at": raw.get("updated_at", ""),
        "author": author_name,
        "url": raw.get("html_url", raw.get("web_url", raw.get("url", ""))),
    }


def _fetch_repo_issues(repo: str, created_after: str) -> list[dict]:
    """Fetch all issues for a single repo, handling pagination."""
    all_issues = []
    page = 1

    while True:
        try:
            batch = list_issues(repo, created_after, limit=100, page=page)
        except GCError as e:
            print(f"  [WARN] Failed to fetch issues for {repo} (page {page}): {e}",
                  file=__import__("sys").stderr)
            break

        if not batch:
            break

        for raw in batch:
            all_issues.append(_normalize_issue(raw, repo))

        if len(batch) < 100:
            break
        page += 1

    return all_issues


def _fetch_org_issues(org: str, created_after: str) -> list[dict]:
    """Fetch issues for all repos in an org, using concurrent fetching."""
    try:
        repos = list_repos(org)
    except GCError as e:
        print(f"[ERROR] Failed to list repos for org '{org}': {e}",
              file=__import__("sys").stderr)
        return []

    if not repos:
        print(f"[WARN] No repositories found for org '{org}'",
              file=__import__("sys").stderr)
        return []

    repo_names = [
        r.get("full_name", r.get("path_with_namespace", "")).replace(" ", "")
        for r in repos
    ]
    repo_names = [r for r in repo_names if r]

    print(f"Found {len(repo_names)} repositories in '{org}'")

    all_issues = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_fetch_repo_issues, repo, created_after): repo
            for repo in repo_names
        }
        for future in as_completed(futures):
            repo = futures[future]
            try:
                issues = future.result()
                if issues:
                    print(f"  {repo}: {len(issues)} issues")
                all_issues.extend(issues)
            except Exception as e:
                print(f"  [WARN] {repo}: {e}", file=__import__("sys").stderr)

    return all_issues


def fetch_issues(target: str, days: int = 7) -> list[dict]:
    """Fetch issues from a repo or community (org).

    Args:
        target: Repo name (owner/repo) or org name.
        days: Number of days to look back.

    Returns:
        List of normalized issue dicts.
    """
    created_after = _compute_created_after(days)
    print(f"Fetching issues since {created_after} ({days} days)")

    if _is_repo(target):
        print(f"Target: repository '{target}'")
        issues = _fetch_repo_issues(target, created_after)
    else:
        print(f"Target: organization '{target}'")
        issues = _fetch_org_issues(target, created_after)

    print(f"Total issues fetched: {len(issues)}")
    return issues


def save_raw_issues(issues: list[dict], path: str) -> None:
    """Save raw issue data as JSON to the given path."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(issues, f, ensure_ascii=False, indent=2)
    print(f"Raw issue data saved to: {path}")


def load_raw_issues(path: str) -> list[dict]:
    """Load raw issue data from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw data file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
