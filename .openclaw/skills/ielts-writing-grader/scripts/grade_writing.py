#!/usr/bin/env python3
"""
Heuristic IELTS writing grader.
This is a structured assistant, not an official examiner substitute.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path


CONNECTORS = {
    "however",
    "therefore",
    "moreover",
    "furthermore",
    "although",
    "because",
    "while",
    "whereas",
    "for example",
    "for instance",
    "in addition",
    "on the other hand",
    "as a result",
    "in conclusion",
}
ACADEMIC_WORDS = {
    "significant",
    "increase",
    "decrease",
    "trend",
    "proportion",
    "percentage",
    "overall",
    "consequence",
    "development",
    "evidence",
    "issue",
    "benefit",
    "drawback",
    "policy",
    "analysis",
}


def clamp(value: float, low: float = 4.0, high: float = 8.5) -> float:
    return max(low, min(high, value))


def round_band(value: float) -> float:
    return round(value * 2) / 2


def sentence_split(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def word_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z']+", text.lower())


def detect_task(text: str, explicit_task: str | None) -> str:
    if explicit_task:
        return explicit_task
    task1_markers = ["chart", "graph", "table", "diagram", "map", "percent", "figure"]
    lowered = text.lower()
    return "task1" if sum(marker in lowered for marker in task1_markers) >= 2 else "task2"


def grammar_error_signals(text: str) -> int:
    patterns = [
        r"\bi\s+[a-z]+s\b",
        r"\bpeople\s+is\b",
        r"\bthere (?:have|has) many\b",
        r"\ba\s+[aeiou][a-z]+",
        r"\ban\s+[^aeiou\s][a-z]+",
        r"\bmore better\b",
        r"\bmost easiest\b",
    ]
    return sum(len(re.findall(pattern, text.lower())) for pattern in patterns)


def band_for_task_response(word_count: int, paragraph_count: int, connector_hits: int, task: str) -> float:
    minimum = 150 if task == "task1" else 250
    score = 5.0
    if word_count >= minimum:
        score += 1.0
    if word_count >= minimum + 40:
        score += 0.5
    if paragraph_count >= (3 if task == "task1" else 4):
        score += 0.5
    if connector_hits >= 4:
        score += 0.5
    return round_band(clamp(score))


def band_for_coherence(sentences: list[str], paragraph_count: int, connector_hits: int) -> float:
    lengths = [len(word_tokens(sentence)) for sentence in sentences] or [0]
    avg_len = statistics.mean(lengths)
    score = 5.0
    if paragraph_count >= 4:
        score += 0.5
    if 10 <= avg_len <= 28:
        score += 1.0
    if connector_hits >= 5:
        score += 0.5
    if max(lengths) > 45:
        score -= 0.5
    return round_band(clamp(score))


def band_for_lexical(words: list[str], academic_hits: int) -> float:
    unique_ratio = (len(set(words)) / len(words)) if words else 0
    score = 5.0
    if unique_ratio >= 0.45:
        score += 0.5
    if unique_ratio >= 0.55:
        score += 0.5
    if academic_hits >= 4:
        score += 0.5
    if len(words) >= 220:
        score += 0.5
    return round_band(clamp(score))


def band_for_grammar(sentences: list[str], error_signals: int) -> float:
    score = 5.5
    if len(sentences) >= 8:
        score += 0.5
    if any("," in sentence and any(word in sentence.lower() for word in ["which", "that", "while", "although"]) for sentence in sentences):
        score += 0.5
    if error_signals >= 3:
        score -= 0.5
    if error_signals >= 6:
        score -= 0.5
    return round_band(clamp(score))


def build_feedback(task: str, overall_band: float, criterion_bands: dict[str, float], metrics: dict[str, float | int]) -> tuple[list[str], list[str], list[str]]:
    strengths: list[str] = []
    risks: list[str] = []
    priorities: list[str] = []

    if metrics["word_count"] >= (150 if task == "task1" else 250):
        strengths.append("The response is long enough to address the task without being obviously underdeveloped.")
    if criterion_bands["lexical_resource"] >= 6.5:
        strengths.append("Vocabulary variety is reasonably strong for a heuristic first-pass band estimate.")
    if criterion_bands["coherence_cohesion"] >= 6.5:
        strengths.append("The response shows a usable paragraph structure and some linking language.")

    if metrics["word_count"] < (150 if task == "task1" else 250):
        risks.append("The response is under length, which usually drags down task response sharply.")
        priorities.append("Add one more well-developed body paragraph or expand the existing explanation with evidence and examples.")
    if metrics["grammar_error_signals"] >= 3:
        risks.append("There are noticeable grammar-pattern signals that may lower grammatical accuracy.")
        priorities.append("Proofread subject-verb agreement, article use, and comparative forms before submitting.")
    if metrics["connector_hits"] < 4:
        risks.append("Linking devices are limited, so the essay may read more like separate statements than a controlled argument.")
        priorities.append("Use clearer transitions between claims, examples, and conclusions.")
    if metrics["unique_word_ratio"] < 0.45:
        risks.append("Vocabulary repetition is fairly high, which can cap lexical resource.")
        priorities.append("Replace repeated high-frequency words with more precise alternatives and collocations.")

    if not priorities:
        priorities.append("Tighten topic sentences and make each paragraph do one clear job.")
        priorities.append("Add one or two more specific examples or comparisons to deepen development.")

    if overall_band >= 7.0:
        strengths.append("The essay has the profile of a competent response, even if it still needs polishing.")

    return strengths[:3], risks[:3], priorities[:4]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Heuristic IELTS writing grader")
    parser.add_argument("--file", help="Path to a text file containing the essay")
    parser.add_argument("--text", help="Raw essay text")
    parser.add_argument("--task", choices=["task1", "task2"], help="Explicit IELTS task type")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.file and not args.text:
        print(json.dumps({"error": "Provide --file or --text"}))
        return 1

    if args.file:
        text = Path(args.file).expanduser().read_text(encoding="utf-8", errors="ignore")
        source = str(Path(args.file).expanduser().resolve())
    else:
        text = args.text or ""
        source = "inline-text"

    text = text.strip()
    if not text:
        print(json.dumps({"error": "Input text is empty"}))
        return 1

    task = detect_task(text, args.task)
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    sentences = sentence_split(text)
    words = word_tokens(text)
    connector_hits = sum(1 for connector in CONNECTORS if connector in text.lower())
    academic_hits = sum(1 for word in ACADEMIC_WORDS if word in words)
    unique_ratio = round((len(set(words)) / len(words)) if words else 0, 3)
    error_signals = grammar_error_signals(text)

    criterion_bands = {
        "task_response": band_for_task_response(len(words), len(paragraphs), connector_hits, task),
        "coherence_cohesion": band_for_coherence(sentences, len(paragraphs), connector_hits),
        "lexical_resource": band_for_lexical(words, academic_hits),
        "grammatical_range_accuracy": band_for_grammar(sentences, error_signals),
    }
    overall_band = round_band(sum(criterion_bands.values()) / len(criterion_bands))

    metrics = {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "connector_hits": connector_hits,
        "academic_word_hits": academic_hits,
        "unique_word_ratio": unique_ratio,
        "grammar_error_signals": error_signals,
    }
    strengths, risks, priorities = build_feedback(task, overall_band, criterion_bands, metrics)

    result = {
        "source": source,
        "task": task,
        "overall_band": overall_band,
        "criterion_bands": criterion_bands,
        "metrics": metrics,
        "strengths": strengths,
        "risks": risks,
        "revision_priorities": priorities,
        "disclaimer": "This is a heuristic estimate, not an official IELTS examiner score.",
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
