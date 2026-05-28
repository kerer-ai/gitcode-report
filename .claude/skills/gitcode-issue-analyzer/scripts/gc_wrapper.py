"""Wrapper around gc CLI for GitCode operations."""

import json
import subprocess
import sys

GC_CMD = "gc"


class GCError(Exception):
    """Raised when a gc command fails."""

    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr


def run_gc(args: list[str]) -> dict | list:
    """Execute a gc command and return parsed JSON output."""
    cmd = [GC_CMD] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        raise GCError(
            f"'{GC_CMD}' command not found. Is gitcode-cli installed?\n"
            f"Install: pip install gitcode-cli"
        )
    except subprocess.TimeoutExpired:
        raise GCError(f"Command timed out: {' '.join(cmd)}")

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "401" in stderr or "authentication" in stderr.lower():
            raise GCError(
                f"Authentication required. Run: {GC_CMD} auth login", stderr
            )
        if "404" in stderr or "not found" in stderr.lower():
            raise GCError(f"Resource not found. Check the repository name.", stderr)
        raise GCError(f"gc command failed: {stderr}", stderr)

    raw = result.stdout.strip()
    if not raw:
        return []

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise GCError(f"Failed to parse gc output as JSON: {e}\nOutput: {raw[:500]}")


def list_issues(
    repo: str,
    created_after: str,
    limit: int = 100,
    page: int = 1,
) -> list[dict]:
    """List issues in a repo created after a given date.

    Args:
        repo: Repository in owner/repo format.
        created_after: ISO 8601 date string (e.g. "2024-01-01").
        limit: Max issues per page (default 100).
        page: Page number starting from 1.
    """
    args = [
        "issue", "list",
        "-R", repo,
        "--state", "all",
        "--created-after", created_after,
        "--sort", "created",
        "--direction", "desc",
        "--limit", str(limit),
        "--page", str(page),
        "--json",
    ]
    return run_gc(args)


def list_repos(owner: str, limit: int = 100) -> list[dict]:
    """List repositories for an organization/user.

    Args:
        owner: Organization or user name.
        limit: Max repos to list.
    """
    args = [
        "repo", "list",
        "--owner", owner,
        "--limit", str(limit),
        "--json",
    ]
    return run_gc(args)


def get_issue_detail(repo: str, number: int) -> dict:
    """Get detailed info for a single issue.

    Args:
        repo: Repository in owner/repo format.
        number: Issue number.
    """
    args = [
        "issue", "view", str(number),
        "-R", repo,
        "--json",
    ]
    return run_gc(args)


def check_auth() -> bool:
    """Check if gc is authenticated."""
    try:
        run_gc(["auth", "status"])
        return True
    except GCError:
        return False
