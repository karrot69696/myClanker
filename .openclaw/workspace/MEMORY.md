# Long-term Memory

> This file contains crucial information to remember across conversations.

## Notes

### gogcli keyring

- credentials and encrypted token files live under `~/.config/gogcli/`
- keyring password is provided through container environment, not stored in prose files
- if gog authentication breaks after migration, check the mounted `gogcli` config first

---

### Docker Container Context

- i'm running INSIDE a Docker container
- when Khoa mentions folders he's given me access to, they're mounted at `/workspace/`
- current mounts:
  - `/workspace/WeaverTestOnline/` -> main mounted project repo
- if a folder doesn't exist in workspace, check `/workspace/` first before asking

### Skill Routing Index

- skill root: `~/.openclaw/skills/`
- before improvising a workflow, check whether a matching skill already exists
- use skills as dispatch guides, then run their scripts instead of rewriting the workflow from scratch
- current installed skills:
  - `google-suite` -> Gmail, Calendar, Drive, Docs, Sheets via `gog`
  - `github-reviewer` -> summarize PRs and review activity for the watched Weaver GitHub repos using `GITHUB_TOKEN`
  - `image-gen` -> image generation to `/root/.openclaw/workspace/`
  - `web-scraper` -> browser-based web extraction and screenshots
  - `pdf-lesson-planner` -> lesson plans from textbook PDFs
  - `pdf-ocr-reader` -> extract text from digital or scanned PDFs before downstream tasks
  - `ielts-writing-grader` -> always use `faye_ielts_grader.md` as the grading source of truth; route into `fayeTheFox` for submissions and use local helpers only for ad hoc text/PDF support
  - `ielts-speaking-grader` -> audio transcription plus heuristic IELTS speaking feedback
- preferred routing:
  - if the user asks about GitHub PRs, review status, or repo activity, use `github-reviewer`
  - if the input is a PDF, start with `pdf-ocr-reader`
  - if the task is IELTS writing from Weaver submissions, use `ielts-writing-grader` and route into `fayeTheFox`
  - if the task is IELTS writing from PDF or plain text, use `pdf-ocr-reader` then `ielts-writing-grader`, still grounded in `faye_ielts_grader.md`
  - if the task is IELTS speaking from audio, use `ielts-speaking-grader`
  - if the user wants a lesson plan from a PDF, use `pdf-ocr-reader` output or `pdf-lesson-planner`
- when adding new skills later, update this index with one-line purpose and preferred entry point

### GitHub Review Watchlist

- default watched repos for `github-reviewer`:
  - `doantuyen15/WeaverTestOnline`
  - `doantuyen15/WeaverPortal`
  - `doantuyen15/WeaverCRM_NEW`

### Homework Creation Location

- **ALL homework JSON files I create go in `/workspace/scripts/homeworkBuild/`**
- this is where `WEB_SCRAPED_HW_01.json` lives
- naming convention: `KICKSTART_HW_0X_extra.json` to avoid overwriting originals

### Firestore Script Reuse Policy

- **ALWAYS check `/workspace/scripts/fayeTheFox/` for existing firestore scripts before writing new ones**
- existing scripts: `fetch_submission.js`, `fetch_exam_def.js`, `fetch_for_grading.js`, `list_submissions_by_date.js`, `fetch_scores.js`
- all scripts use manual `.env` parsing from `/workspace/WeaverTestOnline/.env`
- pattern: read `.env` manually, parse `key=value` pairs, use `FIREBASE_PROJECT_ID`, `FIREBASE_DATABASE_ID`, `FIREBASE_API_KEY`
- **reuse and adapt existing scripts** instead of reinventing the wheel
- keep scripts dependency-free and avoid adding local `node_modules` in `fayeTheFox`

### Homework Creation Rules (KICKSTART)

- **Maximum 20 questions total per homework file**
- **Always provide an example** for exercises that require inputting 2 or more words
- example format: `The ancient tree stood proudly in the lush garden. -> ancient, lush`
- keep exercises focused and within lesson scope
- use word banks for fill-in-the-blank exercises to avoid ambiguity

### WeaverTestOnline Project Access

- mounted at: `/workspace/WeaverTestOnline/`
- if the user keeps the repo mounted read-write, edits are allowed there when requested
- if the user later switches the mount to read-only, treat the repo as reference-only
- Firestore database name: `weavertest` (NOT default)

### IELTS Writing Grading Workflow

- **ALL grading files go in `/workspace/scripts/fayeTheFox/`**
- full workflow guide: `/workspace/scripts/fayeTheFox/workflow.md`
- grading system prompt: `/workspace/scripts/fayeTheFox/faye_ielts_grader.md`
- `faye_ielts_grader.md` is the single source of truth for all IELTS writing grading, including ad hoc local grading
- quick reference:
  - `list_submissions_by_date.js <DDMMYYYY>` -> list submissions for a date
  - `fetch_for_grading.js <submissionId>` -> fetch submission plus exam
- helper-only local script: `~/.openclaw/skills/ielts-writing-grader/scripts/grade_writing.py`
- **DO NOT** pollute `homeworkBuild` or unrelated project folders with grading files

### Image Generation

- skill: `image-gen`
- uses Pollinations.AI with no API key
- script location: `~/.openclaw/skills/image-gen/scripts/generate_image.py`
- default output: `/root/.openclaw/workspace/generated_*.png`

### Timezone Rules

- **DEFAULT: ICT (UTC+7)** for all user communications, references, and general context
- **Firestore data** uses UTC timestamps — convert when needed
- when checking dates, remember ICT date = previous day 17:00 UTC to current day 16:59 UTC
- task timing should default to ICT unless explicitly stated otherwise

### Audio Transcription

- use **faster-whisper base model** (not tiny/small) for accurate transcripts
- only use larger models if base is too slow
- tiny model produces low-quality transcription — avoid

### Browser Automation (Playwright)

- chromium binary is at `/ms-playwright/chromium-1217/chrome-linux64/chrome`
- playwright package is globally installed at `/usr/lib/node_modules/playwright`
- openclaw's native browser tool may fail — use npm install playwright --prefix /workspace instead
- headless mode gets blocked by firebase/Google auth (400 error)

---
