#!/usr/bin/env python3
"""
Extract text from a PDF with a practical fallback chain:
1. pdftotext
2. pdfplumber
3. ocrmypdf + pdftotext
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import fitz
import pdfplumber


def run_command(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, check=check)


def clean_text(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\x0c", "\n").splitlines()]
    compact = "\n".join(line for line in lines if line.strip() or line == "")
    return compact.strip() + "\n" if compact.strip() else ""


def count_pages(pdf_path: Path) -> int:
    with fitz.open(pdf_path) as document:
        return document.page_count


def extract_with_pdftotext(pdf_path: Path, output_path: Path) -> str:
    if not shutil.which("pdftotext"):
        return ""
    run_command(["pdftotext", str(pdf_path), str(output_path)], check=True)
    return clean_text(output_path.read_text(encoding="utf-8", errors="ignore"))


def extract_with_pdfplumber(pdf_path: Path, output_path: Path) -> str:
    chunks: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                chunks.append(f"[Page {page_number}]\n{text}")
    cleaned = clean_text("\n\n".join(chunks))
    output_path.write_text(cleaned, encoding="utf-8")
    return cleaned


def ocr_with_ocrmypdf(pdf_path: Path, ocr_pdf_path: Path) -> None:
    if not shutil.which("ocrmypdf"):
        raise FileNotFoundError("ocrmypdf is not installed")
    run_command(
        [
            "ocrmypdf",
            "--skip-text",
            "--force-ocr",
            "--output-type",
            "pdf",
            str(pdf_path),
            str(ocr_pdf_path),
        ],
        check=True,
    )


def write_markdown(markdown_path: Path, pdf_path: Path, mode: str, text: str) -> None:
    markdown = [
        f"# Extracted PDF Text",
        "",
        f"- Source: `{pdf_path}`",
        f"- Mode: `{mode}`",
        "",
        "```text",
        text.strip(),
        "```",
        "",
    ]
    markdown_path.write_text("\n".join(markdown), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract text from a PDF with OCR fallback.")
    parser.add_argument("pdf_path", help="Path to the input PDF")
    parser.add_argument("--output-dir", help="Directory for extracted outputs")
    parser.add_argument("--force-ocr", action="store_true", help="Skip direct extraction and OCR immediately")
    parser.add_argument(
        "--min-chars",
        type=int,
        default=300,
        help="Minimum character count before considering direct extraction good enough",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = Path(args.pdf_path).expanduser().resolve()
    if not pdf_path.exists():
        print(json.dumps({"error": f"PDF not found: {pdf_path}"}))
        return 1

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else Path("/tmp") / f"{pdf_path.stem}_pdf_extract"
    output_dir.mkdir(parents=True, exist_ok=True)

    text_path = output_dir / f"{pdf_path.stem}_extracted.txt"
    markdown_path = output_dir / f"{pdf_path.stem}_extracted.md"
    page_count = count_pages(pdf_path)

    text = ""
    mode = ""

    if not args.force_ocr:
        try:
            text = extract_with_pdftotext(pdf_path, text_path)
            mode = "direct"
        except Exception:
            text = ""
            mode = ""

        if len(text) < args.min_chars:
            try:
                text = extract_with_pdfplumber(pdf_path, text_path)
                mode = "pdfplumber"
            except Exception:
                text = ""
                mode = ""

    if len(text) < args.min_chars:
        ocr_pdf_path = output_dir / f"{pdf_path.stem}_ocr.pdf"
        try:
            ocr_with_ocrmypdf(pdf_path, ocr_pdf_path)
            text = extract_with_pdftotext(ocr_pdf_path, text_path)
            mode = "ocr"
        except Exception as exc:
            print(json.dumps({"error": f"OCR extraction failed: {exc}"}))
            return 1

    text_path.write_text(text, encoding="utf-8")
    write_markdown(markdown_path, pdf_path, mode, text)

    result = {
        "pdf_path": str(pdf_path),
        "mode": mode,
        "page_count": page_count,
        "char_count": len(text),
        "text_path": str(text_path),
        "markdown_path": str(markdown_path),
        "preview": text[:500].strip(),
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
