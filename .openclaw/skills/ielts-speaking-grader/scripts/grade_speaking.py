#!/usr/bin/env python3
"""
Transcribe and heuristically grade IELTS speaking audio.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
from pathlib import Path

from faster_whisper import WhisperModel


FILLERS = {
    "um",
    "uh",
    "erm",
    "like",
    "you know",
    "i mean",
    "sort of",
    "kind of",
}

COMPLEX_MARKERS = {"because", "although", "while", "which", "that", "if", "when", "unless"}
TOPIC_WORDS = {"experience", "important", "reason", "example", "people", "society", "benefit", "challenge"}


def clamp(value: float, low: float = 4.0, high: float = 8.5) -> float:
    return max(low, min(high, value))


def round_band(value: float) -> float:
    return round(value * 2) / 2


def get_duration_seconds(audio_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def transcribe(audio_path: Path, model_name: str) -> tuple[list[dict[str, float | str]], dict[str, float]]:
    # Optimize download speed using HF_TOKEN and high-speed transfer if available
    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        # These environment variables guide hf_hub_download used by faster-whisper
        os.environ["HF_TOKEN"] = hf_token
        # Enable hf_transfer for much faster downloads (requires hf_transfer package)
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
        try:
            from huggingface_hub import login
            login(token=hf_token)
        except ImportError:
            pass

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(audio_path), vad_filter=True, word_timestamps=True)
    items: list[dict[str, float | str]] = []
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        items.append(
            {
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text,
            }
        )
    meta = {
        "language_probability": round(info.language_probability, 3),
    }
    return items, meta


def analyze(items: list[dict[str, float | str]], duration_seconds: float) -> dict[str, float | int]:
    transcript = " ".join(str(item["text"]) for item in items).strip()
    words = re.findall(r"[A-Za-z']+", transcript.lower())
    word_count = len(words)
    wpm = round((word_count / duration_seconds) * 60, 1) if duration_seconds else 0.0

    pauses = []
    for previous, current in zip(items, items[1:]):
        gap = float(current["start"]) - float(previous["end"])
        if gap > 0:
            pauses.append(gap)

    long_pauses = [gap for gap in pauses if gap >= 1.2]
    filler_hits = sum(transcript.lower().count(filler) for filler in FILLERS)
    sentence_like_units = re.split(r"(?<=[.!?])\s+|\n+", transcript)
    sentence_like_units = [unit.strip() for unit in sentence_like_units if unit.strip()]
    complex_hits = sum(1 for word in COMPLEX_MARKERS if word in words)
    topic_hits = sum(1 for word in TOPIC_WORDS if word in words)

    return {
        "duration_seconds": round(duration_seconds, 1),
        "word_count": word_count,
        "words_per_minute": wpm,
        "segment_count": len(items),
        "average_pause_seconds": round(statistics.mean(pauses), 2) if pauses else 0.0,
        "long_pause_count": len(long_pauses),
        "filler_hits": filler_hits,
        "sentence_unit_count": len(sentence_like_units),
        "complex_marker_hits": complex_hits,
        "topic_word_hits": topic_hits,
    }


def band_fluency(metrics: dict[str, float | int]) -> float:
    score = 5.0
    wpm = float(metrics["words_per_minute"])
    if 105 <= wpm <= 165:
        score += 1.0
    elif 85 <= wpm <= 180:
        score += 0.5
    if int(metrics["long_pause_count"]) <= 3:
        score += 0.5
    if int(metrics["filler_hits"]) <= 3:
        score += 0.5
    if int(metrics["long_pause_count"]) >= 8:
        score -= 0.5
    return round_band(clamp(score))


def band_lexical(metrics: dict[str, float | int], transcript: str) -> float:
    words = re.findall(r"[A-Za-z']+", transcript.lower())
    unique_ratio = (len(set(words)) / len(words)) if words else 0.0
    score = 5.0
    if unique_ratio >= 0.45:
        score += 0.5
    if int(metrics["topic_word_hits"]) >= 3:
        score += 0.5
    if int(metrics["word_count"]) >= 120:
        score += 0.5
    return round_band(clamp(score))


def band_grammar(metrics: dict[str, float | int]) -> float:
    score = 5.0
    if int(metrics["complex_marker_hits"]) >= 3:
        score += 0.5
    if int(metrics["sentence_unit_count"]) >= 5:
        score += 0.5
    if int(metrics["word_count"]) >= 140:
        score += 0.5
    return round_band(clamp(score))


def band_pronunciation(metrics: dict[str, float | int], language_probability: float) -> float:
    score = 5.0
    if language_probability >= 0.8:
        score += 0.5
    if int(metrics["filler_hits"]) <= 2:
        score += 0.5
    if int(metrics["long_pause_count"]) <= 4:
        score += 0.5
    return round_band(clamp(score))


def feedback(overall_band: float, metrics: dict[str, float | int]) -> tuple[list[str], list[str], list[str]]:
    strengths: list[str] = []
    risks: list[str] = []
    drills: list[str] = []

    if 105 <= float(metrics["words_per_minute"]) <= 165:
        strengths.append("The speaking pace is within a healthy conversational range for IELTS practice.")
    if int(metrics["long_pause_count"]) <= 3:
        strengths.append("Pausing looks reasonably controlled instead of constantly breaking the flow.")
    if int(metrics["complex_marker_hits"]) >= 3:
        strengths.append("The transcript shows some evidence of extended and connected sentence structures.")

    if int(metrics["filler_hits"]) >= 4:
        risks.append("Frequent fillers may make the answer sound less controlled and reduce fluency.")
        drills.append("Redo the answer once with a 2-second silent pause rule instead of filling space with 'um' or 'like'.")
    if int(metrics["long_pause_count"]) >= 6:
        risks.append("Long silent gaps suggest hesitation or planning trouble during the answer.")
        drills.append("Practice timed Part 2 answers with a short outline before speaking.")
    if int(metrics["word_count"]) < 90:
        risks.append("The response may be too short to show enough vocabulary and grammatical range.")
        drills.append("Add one example and one reason for each main point to extend your answer naturally.")

    if not drills:
        drills.append("Replace one generic adjective in each answer with a more precise topic-specific word.")
        drills.append("Add one subordinate clause using 'because', 'although', or 'while' in each practice response.")

    if overall_band >= 7.0:
        strengths.append("The answer profile is consistent with a solid, workable speaking performance.")

    return strengths[:3], risks[:3], drills[:4]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Heuristic IELTS speaking grader")
    parser.add_argument("audio_path", help="Path to the audio file")
    parser.add_argument("--output-dir", help="Directory for transcript outputs")
    parser.add_argument("--model", default="turbo", help="Whisper model name, for example tiny, base, small, turbo, large-v3")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audio_path = Path(args.audio_path).expanduser().resolve()
    if not audio_path.exists():
        print(json.dumps({"error": f"Audio file not found: {audio_path}"}))
        return 1

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else Path("/tmp") / f"{audio_path.stem}_speaking_grade"
    output_dir.mkdir(parents=True, exist_ok=True)

    duration_seconds = get_duration_seconds(audio_path)
    items, meta = transcribe(audio_path, args.model)
    transcript = "\n".join(
        f"[{item['start']:>6.2f}-{item['end']:>6.2f}] {item['text']}" for item in items
    )
    transcript_plain = " ".join(str(item["text"]) for item in items).strip()

    transcript_path = output_dir / f"{audio_path.stem}_transcript.txt"
    transcript_path.write_text(transcript, encoding="utf-8")

    metrics = analyze(items, duration_seconds)
    criterion_bands = {
        "fluency_coherence": band_fluency(metrics),
        "lexical_resource": band_lexical(metrics, transcript_plain),
        "grammatical_range_accuracy": band_grammar(metrics),
        "pronunciation": band_pronunciation(metrics, float(meta["language_probability"])),
    }
    overall_band = round_band(sum(criterion_bands.values()) / len(criterion_bands))
    strengths, risks, drills = feedback(overall_band, metrics)

    result = {
        "audio_path": str(audio_path),
        "overall_band": overall_band,
        "criterion_bands": criterion_bands,
        "metrics": metrics,
        "language_probability": meta["language_probability"],
        "transcript_path": str(transcript_path),
        "preview": transcript_plain[:500],
        "strengths": strengths,
        "risks": risks,
        "practice_drills": drills,
        "disclaimer": "This is a heuristic estimate, not an official IELTS examiner score.",
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
