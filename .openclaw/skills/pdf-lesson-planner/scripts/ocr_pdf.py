#!/usr/bin/env python3
"""
OCR PDF Extractor
Converts image-based PDFs to text using Tesseract OCR
"""

import sys
import subprocess
import os
from pathlib import Path

def check_dependencies():
    """Check if required tools are installed"""
    missing = []
    
    # Check poppler-utils
    if subprocess.run(['which', 'pdftoppm'], capture_output=True).returncode != 0:
        missing.append('poppler-utils')
    
    # Check tesseract
    if subprocess.run(['which', 'tesseract'], capture_output=True).returncode != 0:
        missing.append('tesseract-ocr')
    
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Installing...")
        subprocess.run(['apt-get', 'update', '-qq'], check=True)
        subprocess.run(['apt-get', 'install', '-y'] + missing, check=True)
        print("Dependencies installed successfully")

def pdf_to_text(pdf_path, output_path):
    """Extract text from PDF using OCR"""
    pdf_path = Path(pdf_path).resolve()
    output_path = Path(output_path).resolve()
    
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    # Create temp directory for images
    temp_dir = Path('/tmp/pdf_ocr_temp')
    temp_dir.mkdir(exist_ok=True)
    
    print(f"Converting PDF to images...")
    # Convert PDF to PNG images
    subprocess.run([
        'pdftoppm',
        str(pdf_path),
        str(temp_dir / 'page'),
        '-png'
    ], check=True)
    
    # Get all generated images
    images = sorted(temp_dir.glob('page-*.png'))
    
    if not images:
        print("Error: No images generated from PDF")
        sys.exit(1)
    
    print(f"Running OCR on {len(images)} pages...")
    
    # OCR each image
    all_text = []
    for i, img in enumerate(images, 1):
        print(f"  Processing page {i}/{len(images)}...")
        result = subprocess.run([
            'tesseract',
            str(img),
            'stdout'
        ], capture_output=True, text=True, check=True)
        all_text.append(result.stdout)
    
    # Write combined text
    output_path.write_text('\n'.join(all_text))
    
    # Cleanup
    for img in images:
        img.unlink()
    
    print(f"✓ Text extracted to: {output_path}")
    print(f"  Total lines: {len(output_path.read_text().splitlines())}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 ocr_pdf.py <input.pdf> <output.txt>")
        sys.exit(1)
    
    check_dependencies()
    pdf_to_text(sys.argv[1], sys.argv[2])
