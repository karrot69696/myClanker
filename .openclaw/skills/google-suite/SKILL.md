# Google Suite Skill

interact with Gmail, Calendar, Drive, Docs, Sheets, and more via gogcli.

## when to use this skill

use when the user asks to:
- check/search/send emails
- view/create/update calendar events
- upload/download/search Drive files
- create/edit Docs or Sheets
- manage contacts or tasks

## prerequisites

gogcli must be installed and authenticated. if not found, guide the user through setup.

## installation check

```bash
which gog || echo "not installed"
```

## setup flow

if gogcli is missing:

1. install via homebrew (macOS/Linux):
   ```bash
   brew install gogcli
   ```

2. or build from source:
   ```bash
   git clone https://github.com/steipete/gogcli.git
   cd gogcli
   make
   sudo cp bin/gog /usr/local/bin/
   ```

3. setup OAuth credentials:
   - user creates OAuth client in Google Cloud Console
   - downloads client JSON
   - runs: `gog auth credentials ~/Downloads/client_secret_....json`
   - runs: `gog auth add user@gmail.com`

## common operations

### gmail

**search emails:**
```bash
gog gmail search 'newer_than:7d' --json --max 10
```

**send email:**
```bash
gog gmail send \
  --to recipient@example.com \
  --subject "Subject" \
  --body "Message body"
```

**get thread:**
```bash
gog gmail thread get <threadId> --json
```

### calendar

**today's events:**
```bash
gog calendar events primary --today --json
```

**create event:**
```bash
gog calendar create primary \
  --summary "Meeting" \
  --from "2026-04-05T10:00:00Z" \
  --to "2026-04-05T11:00:00Z" \
  --json
```

**search events:**
```bash
gog calendar search "standup" --today --json
```

### drive

**list files:**
```bash
gog drive ls --max 20 --json
```

**search files:**
```bash
gog drive search "invoice" --json
```

**upload file:**
```bash
gog drive upload /path/to/file --json
```

**download file:**
```bash
gog drive download <fileId> --out /path/to/save
```

### docs

**create doc:**
```bash
gog docs create "My Document" --json
```

**export as markdown:**
```bash
gog docs export <docId> --format markdown
```

### sheets

**read sheet:**
```bash
gog sheets read <spreadsheetId> --range "Sheet1!A1:D10" --json
```

**write to sheet:**
```bash
gog sheets write <spreadsheetId> --range "Sheet1!A1" --values "[[\"Name\",\"Email\"]]" --json
```

### contacts

**search contacts:**
```bash
gog contacts search "john" --json
```

### tasks

**list tasks:**
```bash
gog tasks list <tasklistId> --json
```

**create task:**
```bash
gog tasks add <tasklistId> "Task title" --json
```

## output format

always use `--json` flag for machine-readable output. parse the JSON response and present it conversationally to the user.

## error handling

- if `gog` command not found → guide user through installation
- if auth error (401/403) → suggest running `gog auth list --check`
- if quota exceeded → inform user and suggest trying again later
- if invalid parameters → explain what went wrong and suggest correction

## account selection

if user has multiple Google accounts configured:
```bash
gog --account work@company.com gmail search 'newer_than:1d'
```

or set default:
```bash
export GOG_ACCOUNT=work@company.com
```

## security notes

- OAuth tokens stored securely in system keyring
- never log or display access tokens
- respect user's Google account permissions
- inform user when performing write operations (send email, create event, etc.)

## examples

**user:** "check my emails from today"
**action:** run `gog gmail search 'newer_than:1d' --json --max 10`, parse results, summarize

**user:** "what's on my calendar tomorrow?"
**action:** run `gog calendar events primary --tomorrow --json`, format nicely

**user:** "send an email to alice@example.com saying hi"
**action:** run `gog gmail send --to alice@example.com --subject "Hi" --body "Hi Alice!"`, confirm sent

**user:** "upload report.pdf to Drive"
**action:** run `gog drive upload ./report.pdf --json`, return Drive link

## tips

- use relative time flags: `--today`, `--tomorrow`, `--week`, `--days 7`
- calendar events include timezone info in JSON output
- Drive operations support `--all` to search across shared drives
- Gmail supports rich queries: `from:boss@company.com is:unread`
