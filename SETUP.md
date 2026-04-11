# OpenClaw Clanker Setup

> This guide is for recreating this specific clanker on another machine. It reflects the current Docker, 9router, `gogcli`, skill, and workspace setup in this repo.

## What This Setup Contains

- `ai-bot` container running OpenClaw
- `9router` sidecar container that powers model routing
- mounted OpenClaw runtime data at `/root/.openclaw`
- mounted `gogcli` config at `/root/.config/gogcli`
- mounted Weaver project at `/workspace/WeaverTestOnline`
- custom skills for PDF OCR, IELTS writing grading, IELTS speaking grading, scraping, Google tools, and image generation

## What You Need On The Host

- Docker Desktop or Docker Engine with Compose
- a copy of this `openclaw-setup/` folder
- a `gogcli` config folder containing:
  - `credentials.json`
  - `keyring/`
- access to the Weaver repo if you want the same project mount

## Important Files

- [Dockerfile](C:/Users/minhk/OneDrive/Desktop/myClanker/openclaw-setup/docker/openclaw/Dockerfile)
- [docker-compose.yml](C:/Users/minhk/OneDrive/Desktop/myClanker/openclaw-setup/docker/openclaw/docker-compose.yml)
- [.env](C:/Users/minhk/OneDrive/Desktop/myClanker/openclaw-setup/docker/openclaw/.env)
- [MEMORY.md](C:/Users/minhk/OneDrive/Desktop/myClanker/openclaw-setup/.openclaw/workspace/MEMORY.md)
- [skills](C:/Users/minhk/OneDrive/Desktop/myClanker/openclaw-setup/.openclaw/skills)

## Host Folder Expectations

Before starting, decide where these live on the target machine:

- `WEAVER_ROOT`
  The host path to the Weaver repo
- `GOGCLI_CONFIG`
  The host path to the `gogcli` config folder

Current examples on this machine:

```env
WEAVER_ROOT=C:/Users/minhk/OneDrive/Desktop/WEAVER/WeaverTestOnline
GOGCLI_CONFIG=C:/Users/minhk/.config/gogcli
```

## OpenClaw State: What Actually Matters

To recreate the clanker elsewhere, preserve these:

- `docker/openclaw/.env`
- `.openclaw/`
- host `gogcli` config folder

Weaver is a separate mounted project and should be copied or cloned independently.

## Install Steps

### 1. Copy the setup folder

Copy the whole `openclaw-setup/` directory to the new machine.

### 2. Restore or copy `gogcli` config

Make sure the target machine has a `gogcli` config folder with:

```text
<gogcli-config>/
├── credentials.json
└── keyring/
```

If this folder is missing or incomplete, Google-integrated skills will not work until you re-authenticate.

### 3. Edit `docker/openclaw/.env`

Set the target-machine values for:

```env
TELEGRAM_BOT_TOKEN=...
GOG_KEYRING_PASSWORD=...
WEAVER_ROOT=...
GOGCLI_CONFIG=...
```

Notes:

- `WEAVER_ROOT` should point to the host copy of Weaver
- `GOGCLI_CONFIG` should point to the host `gogcli` folder
- do not hardcode those paths into `docker-compose.yml`; keep them in `.env`

### 4. Review container mounts

The Compose file intentionally mounts only:

- OpenClaw runtime data
- Weaver
- `gogcli` config

Current config:

```yaml
volumes:
  - openclaw-data:/root/.openclaw
  - ${WEAVER_ROOT}:/workspace/WeaverTestOnline
  - ${GOGCLI_CONFIG}:/root/.config/gogcli:ro
```

If you want the clanker to edit Weaver, keep the Weaver mount writable.
If you want reference-only access, change the Weaver mount to `:ro`.

### 5. Build

From `docker/openclaw/`:

```bash
docker compose build --pull --no-cache
```

Notes:

- the Dockerfile installs `openclaw@latest`
- npm fetches can be flaky, so the Dockerfile includes retry logic
- a clean build is the easiest way to ensure you are actually resolving the current `latest`

### 6. Start

```bash
docker compose up -d
```

### 7. Check logs

```bash
docker logs -f openclaw
docker logs -f 9router
```

You want to see:

- OpenClaw gateway starts successfully
- 9router comes up on port `20128`
- auto-approval loop does not spam fatal errors

## How This Stack Works

### `ai-bot`

The main container:

- runs OpenClaw gateway on port `18791`
- patches OpenClaw config at startup to enable full tool profile and gateway settings
- auto-approves pending devices in a loop
- contains Playwright, Python, OCR, audio, PDF, and code-analysis tooling

### `9router`

The sidecar:

- runs on port `20128`
- installs `9router`
- builds and maintains the `smart-route` combo in `/root/.9router/db.json`
- is required by the current compose stack because `ai-bot` depends on it

## Skills Included

This setup includes these custom skills under `.openclaw/skills/`:

- `google-suite`
- `image-gen`
- `web-scraper`
- `pdf-lesson-planner`
- `pdf-ocr-reader`
- `ielts-writing-grader`
- `ielts-speaking-grader`

The clanker also keeps a compact skill routing index in [MEMORY.md](C:/Users/minhk/OneDrive/Desktop/myClanker/openclaw-setup/.openclaw/workspace/MEMORY.md).

## Migration Checklist

- copy `openclaw-setup/`
- copy or restore the `gogcli` config folder
- clone or copy Weaver to the target machine
- update `WEAVER_ROOT` in `.env`
- update `GOGCLI_CONFIG` in `.env`
- verify `GOG_KEYRING_PASSWORD`
- build and start with Docker Compose

## Troubleshooting

### Build fails during `npm install -g openclaw@latest`

This is usually a flaky npm registry fetch. The current Dockerfile already retries. Re-run:

```bash
docker compose build --pull --no-cache
```

### OpenClaw starts but Google tools fail

Check:

- `GOGCLI_CONFIG` points to the right host folder
- the folder contains both `credentials.json` and `keyring/`
- `GOG_KEYRING_PASSWORD` is correct

### Weaver files are missing in the container

Check:

- `WEAVER_ROOT` in `.env`
- that the host path actually exists
- the mount appears under `/workspace/WeaverTestOnline`

### 9router does not come up

Check:

- `docker logs 9router`
- whether port `20128` is already taken
- whether outbound npm/network access is available during container startup

### Device pairing errors appear

The container already auto-approves devices, but you can force it manually:

```bash
docker exec -it openclaw openclaw devices approve --latest
```

## Security Notes

- do not put plaintext secrets in prose docs or memory files
- `.env` contains real secrets and should be handled like a secret file
- `gogcli` config is sensitive because it contains OAuth credentials and token material
- do not mount broad host directories unless you explicitly want the clanker to see them

## Minimal Reinstall Summary

If you need the short version on a new machine:

1. Copy `openclaw-setup/`
2. Copy the `gogcli` config folder
3. Put Weaver somewhere on disk
4. Edit `docker/openclaw/.env`
5. Run:

```bash
cd docker/openclaw
docker compose build --pull --no-cache
docker compose up -d
```
