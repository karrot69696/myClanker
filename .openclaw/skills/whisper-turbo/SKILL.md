---
name: whisper-turbo
description: Transcribe audio files to text using faster-whisper (turbo model by default). Optimized for extremely fast generation and state-of-the-art accuracy. High-speed downloads via Hugging Face. Use when the user needs text from an audio file.
---

# Whisper Transcribe (Turbo)

High-performance audio transcription using `faster-whisper` and the `turbo` model.

## Quick Start

Run the script on any audio file:

```bash
python3 scripts/transcribe.py /path/to/audio.mp3
```

## Features

- Uses the `turbo` model for top-tier accuracy and speed, avoiding the inaccuracy of smaller models.
- Optimized download speed using `HF_TOKEN` and `hf-transfer`.
- Outputs JSON with full transcript, segments, and metadata.
- Automatically handles CPU/GPU detection.

## Implementation Details

- Model: `turbo` (or `large-v3-turbo`)
- Compute Type: `int8` (for high speed on CPU)
- Backend: CTranslate2
- Hugging Face optimization: Enabled
