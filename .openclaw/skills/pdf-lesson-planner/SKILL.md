---
name: pdf-lesson-planner
description: Extract content from PDF textbooks (text or image-based) and generate structured lesson plans for English teaching. Use when a user asks to create lesson plans from PDF materials, process textbook PDFs, or build teaching materials from scanned/digital textbooks. Handles both text-extractable and image-only PDFs via OCR.
---

# PDF Lesson Planner

## Overview

This skill extracts content from PDF textbooks (both text-based and image-based) and generates comprehensive lesson plans for English teaching. It handles OCR when needed and structures content into ready-to-use teaching materials.

## Workflow

### Step 1: Analyze the PDF

First, determine if the PDF has extractable text:

```bash
pdftotext "file.pdf" /tmp/test.txt
wc -l /tmp/test.txt
```

- If output > 0 lines: PDF has text layer, proceed to Step 2
- If output = 0 lines: PDF is image-based, proceed to OCR workflow

### Step 2a: Extract Text (for text-based PDFs)

```bash
pdftotext "file.pdf" /tmp/extracted.txt
cat /tmp/extracted.txt
```

### Step 2b: OCR Workflow (for image-based PDFs)

Use the OCR script to extract text from image-based PDFs:

```bash
python3 scripts/ocr_pdf.py "path/to/file.pdf" /tmp/output.txt
```

The script handles:

- Converting PDF pages to images
- Running Tesseract OCR on each page
- Combining results into a single text file

### Step 3: Analyze Content Structure

Read the extracted text and identify:

- **Unit/chapter title** and learning outcomes
- **Reading passages** and vocabulary
- **Grammar points** being taught
- **Exercises** and activities
- **Discussion questions**

### Step 4: Generate Lesson Plan

Create a structured lesson plan with:

1. **Learning Outcomes** - What students will be able to do
2. **Warm-up** (5-10 mins) - Engaging activity to activate prior knowledge
3. **Reading/Input** (15-20 mins) - Pre-reading, while-reading, post-reading
4. **Grammar Presentation** (20-25 mins) - Clear explanation with examples
5. **Controlled Practice** (15-20 mins) - Exercises from textbook
6. **Freer Practice** (20-25 mins) - Communicative activities
7. **Wrap-up & Homework** (5-10 mins) - Review and assignment

Include:

- **Common mistakes** students make with this grammar/topic
- **Differentiation tips** for different levels
- **Materials needed**
- **Teacher notes** for tricky points

Save the lesson plan as a markdown file in the same directory as the PDF.

## Resources

### scripts/

**ocr_pdf.py** - Converts image-based PDFs to text using Tesseract OCR

Usage:

```bash
python3 scripts/ocr_pdf.py input.pdf output.txt
```

Requires: poppler-utils, tesseract-ocr (auto-installed if missing)

### references/

**lesson_plan_template.md** - Standard lesson plan structure for reference when generating plans
