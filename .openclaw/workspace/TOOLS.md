# Tool Usage Guide

## Installed Skills
- pdf lesson planner
- web scraper (nodriver) — see `/root/.openclaw/skills/web-scraper/SKILL.md`

## General Principles
- Prefer using the right tool/skill over guessing
- If a tool returns an error → retry once, then report to user
- Don't run tools repeatedly without a clear purpose
- Always summarize tool output for user instead of dumping raw data

## Conventions
- Web Search: only use when needing real-time info or user explicitly asks
- Browser: only open pages when user specifically requests
- Memory: proactively remember important info without user prompting

## ⏰ Cron / Scheduled Tasks
- OpenClaw natively supports system tools for Cron Jobs.
- When the user asks to schedule tasks or reminders, use built-in tools automatically.
- Do NOT use "current" as a sessionKey for session tools.

## 📁 File & Workspace
- **OpenClaw System Workspace**: `/root/.openclaw/workspace/`
- **User Project Workspace**: `/workspace/` (mounted volumes)
- **Always check `/workspace/` first** for user files, scripts, and projects
- Homework files: `/workspace/scripts/homeworkBuild/`
- Grading scripts: `/workspace/scripts/toddTheFox/`
- Main project: `/workspace/WeaverTestOnline/`

## 🛠️ Tool Error Handling
- Retry up to 2 times on network errors
- If still failing: report to user with specific error description and workaround
