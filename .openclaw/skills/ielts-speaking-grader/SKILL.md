---
name: ielts-speaking-grader
description: Transcribe and heuristically grade IELTS speaking audio using ffmpeg and faster-whisper. Use when a user asks for speaking-band estimation, transcript generation, fluency feedback, or pronunciation-oriented review from audio.
---

# IELTS Speaking Grader

Turn audio into a transcript, extract timing signals, and estimate IELTS speaking performance with criterion-based feedback.

## when to use this skill

use when the user asks to:

- grade IELTS speaking
- transcribe an answer
- assess fluency from audio
- review a recorded speaking practice file

do NOT use for:

- essays or PDFs
- general audio editing requests that do not involve grading or transcription

## prerequisites

the container should have:

- `ffmpeg`
- `ffprobe`
- python package `faster-whisper`

## workflow

1. run the speaking grader on an audio file
2. read the JSON output
3. use:

- `transcript_path` for the full transcript
- `criterion_bands` for the estimated rubric breakdown
- `metrics` for speaking pace and pause signals

## command patterns

basic usage:

```bash
python3 scripts/grade_speaking.py /path/to/audio.mp3
```

custom output folder:

```bash
python3 scripts/grade_speaking.py /path/to/audio.m4a --output-dir /tmp/speaking_run
```

use a larger model if the container can handle it:

```bash
python3 scripts/grade_speaking.py /path/to/audio.wav --model base
```

## output contract

the script prints JSON with:

- `overall_band`
- `criterion_bands`
- `metrics`
- `transcript_path`
- `preview`

## grading notes

this is a heuristic assistant, not an official examiner.

- pronunciation is inferred only loosely from transcription confidence and pacing signals
- audio quality, accents, and background noise can distort the estimate
- always mention uncertainty if the transcript looks broken

## response pattern

1. report the estimated overall band
2. point out fluency strengths and breakdowns
3. mention lexical and grammar evidence from the transcript
4. give targeted drills:

- filler reduction
- answer expansion
- complex sentence practice
- topic-specific vocabulary
