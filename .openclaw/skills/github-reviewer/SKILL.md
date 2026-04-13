---
name: github-reviewer
description: Review and summarize GitHub pull requests across the watched Weaver repositories using the container's GITHUB_TOKEN. Use when the user asks for PR summaries, review status, changed-file overviews, or a quick scan of recent repo activity.
---

# GitHub Reviewer

summarize GitHub pull requests and recent PR activity using the `GITHUB_TOKEN` already present in the container environment.

## when to use this skill

use when the user asks to:

- summarize a pull request
- review code changes in a GitHub PR
- check review status or requested changes
- scan recent PR activity in the watched Weaver repos
- compare which repos have active PRs needing attention

do NOT use for:

- editing repository code directly in a local clone
- full issue management workflows unrelated to code review

## watched repos

default repo watch list lives in:

```text
/root/.openclaw/skills/github-reviewer/watched_repos.txt
```

currently tracked:

- `doantuyen15/WeaverTestOnline`
- `doantuyen15/WeaverPortal`
- `doantuyen15/WeaverCRM_NEW`

## prerequisites

- `GITHUB_TOKEN` must exist in the environment OR in `/root/.openclaw/workspace/.env`
- token should have read access to the target repos and PR metadata

## primary entry points

watch recent PR activity across the watched repos:

```bash
python3 /root/.openclaw/skills/github-reviewer/scripts/github_review.py watch --json
```

summarize one PR from a URL:

```bash
python3 /root/.openclaw/skills/github-reviewer/scripts/github_review.py pr "https://github.com/doantuyen15/WeaverPortal/pull/123" --json
```

summarize one PR from repo plus number:

```bash
python3 /root/.openclaw/skills/github-reviewer/scripts/github_review.py pr --repo doantuyen15/WeaverPortal --number 123 --json
```

summarize the latest commit on default branch:

```bash
python3 /root/.openclaw/skills/github-reviewer/scripts/github_review.py commit --repo doantuyen15/WeaverTestOnline --latest --json
```

summarize a specific commit by SHA:

```bash
python3 /root/.openclaw/skills/github-reviewer/scripts/github_review.py commit doantuyen15/WeaverTestOnline@0cee8e3 --json
```

override the watch list for an ad hoc repo scan:

```bash
python3 /root/.openclaw/skills/github-reviewer/scripts/github_review.py watch --repo owner/repo --repo owner/other --json
```

## output contract

prefer `--json` so the agent can parse reliably.

`watch` returns:

- watched repos
- open PR counts
- recent PR titles, numbers, authors, draft state, and update timestamps

`pr` returns:

- PR metadata and branch info
- additions, deletions, commit count, changed-file count
- top changed files
- review state summary
- latest review and comment excerpts

## review workflow

1. if the user asks generally what needs attention, start with `watch`
2. pick the most relevant PR
3. run `pr ... --json`
4. summarize:
   - what changed
   - review state and blockers
   - risky files or hotspots
   - anything that obviously needs follow-up

## limitations

- REST review comments do not expose full thread resolution state
- if the token lacks repo access, GitHub will return `403` or `404`
- this helper summarizes changed files and comments; it does not replace deep manual code review when the user wants line-by-line analysis

## security rules

- never print or echo `GITHUB_TOKEN`
- never paste raw auth headers into chat
- summarize PR content instead of dumping huge API payloads
