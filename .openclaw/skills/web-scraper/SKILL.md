---
name: web-scraper
description: Scrape and extract content from websites using playwright or lightweight fetching
---

# Web Scraper Skill

scrape and extract content from websites using playwright or lightweight fetching.

## when to use this skill

use when the user asks to:
- scrape a website or webpage
- extract text/data from a URL
- take a screenshot of a page
- read content behind JavaScript rendering
- interact with a page (click, type, scroll)

do NOT use for:
- simple web searches (use web_fetch instead)
- APIs with proper endpoints (use curl/fetch instead)

## primary tools

### browser tool (playwright)
use for JS-rendered pages, screenshots, interactions:
```
browser(action="open", targetUrl="https://example.com")
browser(action="snapshot")
browser(action="screenshot", targetId="...")
browser(action="act", request={kind: "click", ref: "..."})
```

### web_fetch tool
use for lightweight HTML fetching (no JS):
```
web_fetch(url="https://example.com", maxChars=10000)
```

## legacy (nodriver scraper)

the old scraper at `/root/.openclaw/skills/web-scraper/scripts/scrape.py` is **deprecated** — prefer browser/web_fetch tools above.

if you must use it:
```bash
python3 /root/.openclaw/skills/web-scraper/scripts/scrape.py "https://example.com"
```

## output format

- web_fetch: markdown or text, capped at maxChars
- browser snapshot: structured JSON with page elements
- browser screenshot: binary PNG/JPEG

always summarize scraped content for the user — don't dump raw output.

## tips

- use web_fetch for static pages (fast, no setup)
- use browser for JavaScript-rendered content or when you need to interact
- browser tool handles anti-bot better than plain requests
- screenshots can be sent directly via message tool

## error handling

- if web_fetch fails: try browser tool instead
- if page times out: browser tool may work better for slow pages
- if chromium issues: check browser status with browser(action="status")