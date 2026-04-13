#!/usr/bin/env python3
"""Summarize GitHub pull requests for watched repos."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


API_ROOT = "https://api.github.com"
PR_URL_RE = re.compile(r"^https://github\.com/([^/]+/[^/]+)/pull/(\d+)(?:/.*)?$")
PR_REF_RE = re.compile(r"^([^/\s]+/[^#\s]+)#(\d+)$")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sanitize_text(value: str | None, limit: int = 240) -> str:
    if not value:
        return ""
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def watched_repos_path() -> Path:
    return skill_root() / "watched_repos.txt"


def load_watched_repos() -> list[str]:
    path = watched_repos_path()
    if not path.exists():
        return []
    repos = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        repos.append(line)
    return repos


def parse_pr_target(target: str | None, repo: str | None, number: int | None) -> tuple[str, int]:
    if repo and number is not None:
        return repo, number
    if not target:
        raise ValueError("provide a PR URL, owner/repo#number, or both --repo and --number")

    match = PR_URL_RE.match(target)
    if match:
        return match.group(1), int(match.group(2))

    match = PR_REF_RE.match(target)
    if match:
        return match.group(1), int(match.group(2))

    raise ValueError("could not parse PR target; expected URL or owner/repo#number")


class GitHubClient:
    def __init__(self, token: str) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "openclaw-github-reviewer",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = self.session.get(f"{API_ROOT}{path}", params=params, timeout=60)
        if response.status_code >= 400:
            detail = ""
            try:
                payload = response.json()
                detail = payload.get("message", "")
            except Exception:
                detail = response.text.strip()
            raise RuntimeError(f"GitHub API {response.status_code} for {path}: {detail}")
        return response.json()

    def list_pulls(self, repo: str, limit: int, state: str) -> list[dict[str, Any]]:
        return self.get(
            f"/repos/{repo}/pulls",
            params={
                "state": state,
                "sort": "updated",
                "direction": "desc",
                "per_page": max(1, min(limit, 25)),
            },
        )

    def pull(self, repo: str, number: int) -> dict[str, Any]:
        return self.get(f"/repos/{repo}/pulls/{number}")

    def pull_files(self, repo: str, number: int) -> list[dict[str, Any]]:
        return self.get(
            f"/repos/{repo}/pulls/{number}/files",
            params={"per_page": 100},
        )

    def issue_comments(self, repo: str, number: int) -> list[dict[str, Any]]:
        return self.get(
            f"/repos/{repo}/issues/{number}/comments",
            params={"per_page": 100},
        )

    def review_comments(self, repo: str, number: int) -> list[dict[str, Any]]:
        return self.get(
            f"/repos/{repo}/pulls/{number}/comments",
            params={"per_page": 100},
        )

    def reviews(self, repo: str, number: int) -> list[dict[str, Any]]:
        return self.get(
            f"/repos/{repo}/pulls/{number}/reviews",
            params={"per_page": 100},
        )


def summarize_watch(client: GitHubClient, repos: list[str], limit: int, state: str) -> dict[str, Any]:
    results = []
    for repo in repos:
        pulls = client.list_pulls(repo, limit=limit, state=state)
        items = []
        for pr in pulls:
            items.append(
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "author": (pr.get("user") or {}).get("login"),
                    "state": pr["state"],
                    "draft": pr.get("draft", False),
                    "updated_at": pr.get("updated_at"),
                    "html_url": pr.get("html_url"),
                }
            )
        results.append(
            {
                "repo": repo,
                "returned_count": len(items),
                "items": items,
            }
        )
    return {
        "generated_at": now_iso(),
        "mode": "watch",
        "repos": repos,
        "state": state,
        "limit_per_repo": limit,
        "results": results,
    }


def summarize_commit(client: GitHubClient, repo: str, sha: str, max_sample: int) -> dict[str, Any]:
    """Summarize a single commit with diff and code sample."""
    # Get commit details
    commit = client.get(f"/repos/{repo}/git/commits/{sha}")
    parent_sha = commit["parents"][0]["sha"] if commit.get("parents") else None
    
    # Compare with parent for changes
    files_list = []
    additions = 0
    deletions = 0
    if parent_sha:
        comp = client.get(f"/repos/{repo}/compare/{parent_sha}...{sha}")
        files_list = comp.get("files", [])
        additions = comp.get("additions", 0)
        deletions = comp.get("deletions", 0)
    
    # Group files
    new_files = []
    modified = []
    other = []
    for f in files_list:
        status = f.get("status")
        adds = f.get("additions", 0)
        filename = f.get("filename", "")
        if status == "added" and adds > 50:
            new_files.append(filename)
        elif status == "modified":
            modified.append(filename)
        else:
            other.append(filename)
    
    # Get sample file content
    sample_content = ""
    sample_file = ""
    if new_files:
        sample_file = new_files[0]
        try:
            content_data = client.get(f"/repos/{repo}/contents/{sample_file}?ref={sha}")
            import base64
            sample_content = base64.b64decode(content_data.get("content", "")).decode("utf-8")[:1200]
        except Exception:
            sample_content = "[Could not fetch content]"
    
    return {
        "generated_at": now_iso(),
        "mode": "commit",
        "target": {
            "repo": repo,
            "sha": sha[:7],
            "html_url": f"https://github.com/{repo}/commit/{sha}",
        },
        "commit": {
            "message": commit.get("message", "").strip(),
            "author": (commit.get("author") or {}).get("login"),
            "date": commit.get("committer", {}).get("date", "")[:10] if commit.get("committer") else None,
        },
        "changes": {
            "files_changed": len(files_list),
            "additions": additions,
            "deletions": deletions,
            "new_files": new_files[:15],
            "modified_files": modified[:15],
        },
        "sample": {
            "file": sample_file,
            "content": sample_content,
        },
    }


def summarize_pr(client: GitHubClient, repo: str, number: int, max_files: int, max_comments: int) -> dict[str, Any]:
    pr = client.pull(repo, number)
    files = client.pull_files(repo, number)
    issue_comments = client.issue_comments(repo, number)
    review_comments = client.review_comments(repo, number)
    reviews = client.reviews(repo, number)

    status_counts = Counter((item.get("status") or "unknown") for item in files)
    ext_counts = Counter()
    for item in files:
        suffix = Path(item.get("filename", "")).suffix.lower()
        ext_counts[suffix or "[no_ext]"] += 1

    top_files = sorted(
        files,
        key=lambda item: (
            (item.get("additions") or 0) + (item.get("deletions") or 0),
            item.get("filename") or "",
        ),
        reverse=True,
    )[:max_files]

    review_state_counts = Counter((item.get("state") or "UNKNOWN") for item in reviews)

    comment_items = []
    for item in issue_comments:
        comment_items.append(
            {
                "kind": "issue_comment",
                "author": (item.get("user") or {}).get("login"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "path": None,
                "body": sanitize_text(item.get("body")),
                "html_url": item.get("html_url"),
            }
        )
    for item in review_comments:
        comment_items.append(
            {
                "kind": "review_comment",
                "author": (item.get("user") or {}).get("login"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "path": item.get("path"),
                "body": sanitize_text(item.get("body")),
                "html_url": item.get("html_url"),
            }
        )

    latest_comments = sorted(
        comment_items,
        key=lambda item: item.get("updated_at") or item.get("created_at") or "",
        reverse=True,
    )[:max_comments]

    latest_reviews = []
    for item in sorted(reviews, key=lambda review: review.get("submitted_at") or "", reverse=True)[:max_comments]:
        latest_reviews.append(
            {
                "author": (item.get("user") or {}).get("login"),
                "state": item.get("state"),
                "submitted_at": item.get("submitted_at"),
                "body": sanitize_text(item.get("body")),
                "html_url": item.get("html_url"),
            }
        )

    return {
        "generated_at": now_iso(),
        "mode": "pr",
        "target": {
            "repo": repo,
            "number": number,
            "html_url": pr.get("html_url"),
        },
        "pr": {
            "title": pr.get("title"),
            "state": pr.get("state"),
            "draft": pr.get("draft"),
            "merged": pr.get("merged"),
            "mergeable": pr.get("mergeable"),
            "author": (pr.get("user") or {}).get("login"),
            "created_at": pr.get("created_at"),
            "updated_at": pr.get("updated_at"),
            "base": (pr.get("base") or {}).get("ref"),
            "head": (pr.get("head") or {}).get("ref"),
            "commits": pr.get("commits"),
            "changed_files": pr.get("changed_files"),
            "additions": pr.get("additions"),
            "deletions": pr.get("deletions"),
            "requested_reviewers": [
                reviewer.get("login")
                for reviewer in pr.get("requested_reviewers") or []
                if reviewer.get("login")
            ],
            "labels": [
                label.get("name")
                for label in pr.get("labels") or []
                if label.get("name")
            ],
            "body": sanitize_text(pr.get("body"), limit=600),
        },
        "file_summary": {
            "status_counts": dict(status_counts),
            "extension_counts": dict(ext_counts.most_common(10)),
            "top_files": [
                {
                    "filename": item.get("filename"),
                    "status": item.get("status"),
                    "additions": item.get("additions"),
                    "deletions": item.get("deletions"),
                    "changes": item.get("changes"),
                }
                for item in top_files
            ],
        },
        "review_summary": {
            "review_state_counts": dict(review_state_counts),
            "reviews_count": len(reviews),
            "issue_comments_count": len(issue_comments),
            "review_comments_count": len(review_comments),
            "latest_reviews": latest_reviews,
            "latest_comments": latest_comments,
        },
    }


def parse_commit_target(target: str | None, repo: str | None, sha: str | None) -> tuple[str, str]:
    """Parse commit target: URL, owner/repo@sha, or just sha with repo."""
    if repo and sha:
        return repo, sha
    if not target:
        raise ValueError("provide commit URL, owner/repo@sha, or both --repo and --sha")
    
    # Try URL pattern
    URL_RE = re.compile(r"^https://github\.com/([^/]+/[^/]+)/commit/([a-f0-9]+)")
    match = URL_RE.match(target)
    if match:
        return match.group(1), match.group(2)
    
    # Try owner/repo@sha
    match = re.match(r"^([^/]+/[^@]+)@([a-f0-9]+)$", target)
    if match:
        return match.group(1), match.group(2)
    
    # Assume it's just a sha
    if repo:
        return repo, target
    
    raise ValueError("could not parse commit target; expected URL, owner/repo@sha, or sha with --repo")



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize GitHub PR activity for watched repos.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    watch_parser = subparsers.add_parser("watch", help="List recent pull requests for watched repos.")
    watch_parser.add_argument("--repo", action="append", dest="repos", help="Override watched repos. Repeatable.")
    watch_parser.add_argument("--limit", type=int, default=5, help="Max PRs per repo. Default: 5.")
    watch_parser.add_argument(
        "--state",
        choices=["open", "closed", "all"],
        default="open",
        help="PR state filter. Default: open.",
    )
    watch_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")

    pr_parser = subparsers.add_parser("pr", help="Summarize one pull request.")
    pr_parser.add_argument("target", nargs="?", help="PR URL or owner/repo#number.")
    pr_parser.add_argument("--repo", help="Repository in owner/repo format.")
    pr_parser.add_argument("--number", type=int, help="Pull request number.")
    pr_parser.add_argument("--max-files", type=int, default=12, help="How many changed files to keep.")
    pr_parser.add_argument("--max-comments", type=int, default=8, help="How many recent comments/reviews to keep.")
    pr_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")

    commit_parser = subparsers.add_parser("commit", help="Summarize one commit.")
    commit_parser.add_argument("target", nargs="?", help="Commit URL or owner/repo@sha.")
    commit_parser.add_argument("--repo", help="Repository in owner/repo format.")
    commit_parser.add_argument("--sha", help="Commit SHA (full or 7 chars).")
    commit_parser.add_argument("--latest", action="store_true", help="Use latest commit from default branch.")
    commit_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        env_path = Path("/root/.openclaw/workspace/.env")
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("GITHUB_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                    break

    if not token:
        print("GITHUB_TOKEN is not set in the environment or /root/.openclaw/workspace/.env.", file=sys.stderr)
        return 2

    client = GitHubClient(token)

    try:
        if args.command == "watch":
            repos = args.repos or load_watched_repos()
            if not repos:
                raise RuntimeError("no watched repos configured")
            payload = summarize_watch(client, repos=repos, limit=args.limit, state=args.state)
        elif args.command == "pr":
            repo, number = parse_pr_target(args.target, args.repo, args.number)
            payload = summarize_pr(
                client,
                repo=repo,
                number=number,
                max_files=max(1, args.max_files),
                max_comments=max(1, args.max_comments),
            )
        elif args.command == "commit":
            # Handle commit: parse target or use latest
            if args.latest:
                # Get default branch commits
                commits = client.get(f"/repos/{args.repo or 'doantuyen15/WeaverTestOnline'}/commits", params={"per_page": 1})
                sha = commits[0]["sha"] if commits else None
            elif args.sha:
                sha = args.sha
            elif args.target:
                # Parse owner/repo@sha or just sha
                if "@" in args.target:
                    parts = args.target.split("@")
                    repo = parts[0]
                    sha = parts[1]
                else:
                    sha = args.target
            else:
                raise RuntimeError("provide --latest, --sha, or target")
            
            target_repo = args.repo or "doantuyen15/WeaverTestOnline"
            payload = summarize_commit(client, repo=target_repo, sha=sha, max_sample=1)
        else:
            raise RuntimeError(f"unsupported command: {args.command}")
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
