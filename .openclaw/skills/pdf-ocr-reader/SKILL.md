---
name: pdf-ocr-reader
description: Extract text from digital or scanned PDFs and return structured output for downstream tasks like IELTS grading, lesson planning, and summarization. Use when a user asks to read, OCR, summarize, or grade a PDF. Prefer this before any PDF-specific downstream skill.
---

# PDF OCR Reader

Extract text from PDFs using a fallback chain that works for both normal and scanned files.

## when to use this skill

use when the user asks to:
- read a PDF
- extract text from a PDF
- OCR a scanned PDF
- summarize or grade content that starts as a PDF

do NOT use for:
- image files that are not PDFs
- handwritten photos without a PDF container

## prerequisites

the container should have:
- `pdftotext`
- `ocrmypdf`
- `python3`
- python packages: `pymupdf`, `pdfplumber`

## workflow

1. run the extractor:
```bash
python3 scripts/extract_pdf.py "/path/to/file.pdf"
```

2. inspect the JSON output:
- `mode` tells you whether direct extraction or OCR was used
- `text_path` points to the extracted text file
- `markdown_path` points to a markdown-friendly version
- `preview` gives a short sample for quick inspection

3. read the extracted text file and continue with the downstream task

## command patterns

basic extraction:
```bash
python3 scripts/extract_pdf.py "/path/to/file.pdf"
```

custom output folder:
```bash
python3 scripts/extract_pdf.py "/path/to/file.pdf" --output-dir /tmp/pdf_job
```

force OCR:
```bash
python3 scripts/extract_pdf.py "/path/to/file.pdf" --force-ocr
```

## output contract

the script prints JSON to stdout in this shape:

```json
{
  "pdf_path": "/path/to/file.pdf",
  "mode": "direct|pdfplumber|ocr",
  "page_count": 8,
  "char_count": 4210,
  "text_path": "/tmp/file_extracted.txt",
  "markdown_path": "/tmp/file_extracted.md",
  "preview": "first few hundred characters..."
}
```

always summarize extracted content for the user instead of dumping the full text directly into chat.

## error handling

- if `char_count` is very low, assume the PDF may be mostly images or low quality
- if extraction fails, try `--force-ocr`
- if OCR still fails, report that the file may be corrupted or require better scan quality

## downstream usage

- for essays and reports: pass `text_path` into the IELTS writing grader
- for textbook materials: feed the extracted text into lesson-planning or summarization workflows
- for scanned worksheets: quote uncertain OCR passages carefully and mention uncertainty
