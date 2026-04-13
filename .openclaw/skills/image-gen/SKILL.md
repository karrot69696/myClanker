---
name: image-gen
description: Generate images from text prompts using Pollinations.AI (free, no API key required). Use when the user asks to create, generate, or render an image, illustration, artwork, or visual content from a description. Supports any creative prompt for lesson materials, social media, presentations, or general image needs.
---

# Image Generation

Generate images from text prompts using Pollinations.AI's FLUX model.

## Quick Start

Run the script with a prompt:

```bash
python3 scripts/generate_image.py "your prompt here"
```

The script outputs the file path to stdout. Default location: `/root/.openclaw/workspace/generated_*.png`

Optional custom output path:

```bash
python3 scripts/generate_image.py "a fox in space" /path/to/output.png
```

## Usage Pattern

1. Run the script with user's prompt
2. Capture the output path from stdout
3. Send the image via message tool with appropriate caption

Example:

```python
result = exec("python3 scripts/generate_image.py 'cyberpunk classroom'")
image_path = result.stdout.strip()
message(action="send", media=image_path, caption="cyberpunk classroom")
```

## Features

- Free, no API key required
- FLUX model with automatic prompt enhancement
- No watermark
- ~5-10 second generation time
- 1024x1024 default resolution

## Technical Details

- API: Pollinations.AI (`https://image.pollinations.ai`)
- Model: FLUX
- Parameters: `nologo=true`, `enhance=true`
- User-Agent spoofing required (handled by script)
- Timeout: 90 seconds
