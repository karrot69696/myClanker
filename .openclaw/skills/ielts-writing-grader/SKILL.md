---
name: ielts-writing-grader
description: Grade IELTS writing using `faye_ielts_grader.md` from the existing fayeTheFox workflow as the single source of truth for both Weaver submissions and ad hoc text or PDF grading. Use when a user asks for IELTS writing grading, submission review, band estimation, or PDF-to-grading workflows.
---

# IELTS Writing Grader

This skill has two modes:

- `submission workflow` for real Weaver submissions
- `ad hoc grading` for one-off text or PDF jobs

Both modes must use the same grading authority:

```text
/workspace/WeaverTestOnline/scripts/fayeTheFox/faye_ielts_grader.md
```

That file is the single source of truth for grading tone, strictness, band logic, and output style.

## when to use this skill

use when the user asks to:

- grade an IELTS essay
- estimate a writing band
- review a Weaver submission
- fetch and grade writing from Firestore
- grade a PDF or pasted essay

do NOT use for:

- speaking audio
- non-IELTS freeform writing unless the user still wants IELTS-style assessment

## preferred routing

1. if the request is about Weaver submissions or existing grading files:
   use the `fayeTheFox` workflow first
2. if the source is a PDF:
   use `pdf-ocr-reader` first, then continue with ad hoc grading
3. in every grading path, load and follow `faye_ielts_grader.md` before producing the assessment
4. only use `scripts/grade_writing.py` for helper metrics when useful; it is not the grading authority

## primary workflow: fayeTheFox

workflow location:

```text
/workspace/WeaverTestOnline/scripts/fayeTheFox/
```

important files:

```text
/workspace/WeaverTestOnline/scripts/fayeTheFox/WORKFLOW.md
/workspace/WeaverTestOnline/scripts/fayeTheFox/faye_ielts_grader.md
/workspace/WeaverTestOnline/scripts/fayeTheFox/list_submissions_by_date.js
/workspace/WeaverTestOnline/scripts/fayeTheFox/fetch_for_grading.js
```

### full submission flow

1. find submissions for a date:

```bash
cd /workspace/WeaverTestOnline/scripts/fayeTheFox
node list_submissions_by_date.js 05042026
```

1. fetch submission plus exam definition:

```bash
cd /workspace/WeaverTestOnline/scripts/fayeTheFox
node fetch_for_grading.js <submissionId>
```

1. read:

- `submission_<id>.json`
- `exam_<code>.json`
- `faye_ielts_grader.md`

1. produce grading in the established markdown style, usually alongside the existing grading files in the same folder

### workflow rules

- this workflow is the source of truth for real IELTS writing grading in Weaver
- `faye_ielts_grader.md` is the source of truth for all IELTS writing grading, not just Weaver submissions
- keep grading files in `/workspace/WeaverTestOnline/scripts/fayeTheFox/`
- reuse the existing JSON fetch scripts instead of rebuilding fetch logic
- follow the strict tone and scoring rules from `faye_ielts_grader.md`
- use the template when useful, but preserve the established grading style already in that folder

## secondary workflow: ad hoc grading

Use this when the user gives plain text, a standalone file, or a PDF and does not need the Firestore submission workflow.

### ad hoc grading rules

1. load and follow:

```text
/workspace/WeaverTestOnline/scripts/fayeTheFox/faye_ielts_grader.md
```

1. if the input is a PDF, extract text first with `pdf-ocr-reader`
2. if useful, run `scripts/grade_writing.py` only to gather helper signals such as:

- word count
- paragraph count
- connector density
- rough risk flags

1. write the final assessment in the Faye grading style, not the raw JSON helper format

### helper commands

grade from a text file:

```bash
python3 scripts/grade_writing.py --file /path/to/essay.txt
```

grade from raw text:

```bash
python3 scripts/grade_writing.py --text "Some people think..."
```

explicit task type:

```bash
python3 scripts/grade_writing.py --file /path/to/essay.txt --task task2
```

for PDFs:

```bash
python3 /root/.openclaw/skills/pdf-ocr-reader/scripts/extract_pdf.py /path/to/file.pdf
python3 scripts/grade_writing.py --file /tmp/..._extracted.txt
```

## output contract

### fayeTheFox mode

produce a proper grading artifact grounded in:

- the fetched submission
- the exam task definition
- the `faye_ielts_grader.md` prompt

### ad hoc mode

produce the final assessment using `faye_ielts_grader.md` as the grading authority.

if `grade_writing.py` is used, treat its JSON as helper scaffolding only.

## important distinction

- `fayeTheFox` mode is the real workflow
- `faye_ielts_grader.md` is the real rubric and style guide in every mode
- `grade_writing.py` is only a convenience helper

Do not replace `faye_ielts_grader.md` with the heuristic script in any mode.
