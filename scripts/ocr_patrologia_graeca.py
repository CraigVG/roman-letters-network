#!/usr/bin/env python3
"""OCR Patrologia Graeca pages using Gemini Vision.

Downloads PDF pages from Internet Archive, extracts them as images,
sends to Gemini for Greek text OCR, and updates the database.

Usage:
  # Download PG78 PDF (one-time)
  python scripts/ocr_patrologia_graeca.py --download

  # OCR a range of pages
  python scripts/ocr_patrologia_graeca.py --ocr --start-page 100 --end-page 110

  # OCR and update database
  python scripts/ocr_patrologia_graeca.py --ocr --update-db --start-page 100 --end-page 110

  # Show page mapping (which pages have which letters)
  python scripts/ocr_patrologia_graeca.py --map-pages
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
PG78_DIR = os.path.join(DATA_DIR, 'pg78_ocr')
PDF_PATH = os.path.join(PG78_DIR, 'pg78.pdf')
PAGES_DIR = os.path.join(PG78_DIR, 'pages')
OCR_DIR = os.path.join(PG78_DIR, 'ocr_output')

# Internet Archive URL for PG78
IA_PDF_URL = "https://archive.org/download/bim_early-english-books-1641-1700_patrologiae-cursus-completus-_1860_78/bim_early-english-books-1641-1700_patrologiae-cursus-completus-_1860_78.pdf"

# Isidore's letters span roughly these PDF pages (columns 177-1646 of PG78)
# Each PDF page has 2 columns, and page numbers don't map 1:1 to column numbers
# This will need calibration after downloading
ISIDORE_START_PAGE = 95   # approximate
ISIDORE_END_PAGE = 830    # approximate


GEMINI_OCR_PROMPT = """You are performing OCR on a page from Patrologia Graeca volume 78 (Migne, 1860), containing letters of Isidore of Pelusium.

This page has TWO COLUMNS. The LEFT column contains the GREEK original. The RIGHT column contains a LATIN translation. You must extract ONLY the Greek text from the LEFT column.

YOUR TASK:
1. Extract ONLY the GREEK text from the LEFT column
2. IGNORE the RIGHT column entirely (it is Latin translation)
3. IGNORE footnotes and apparatus criticus at the bottom
4. IGNORE column numbers at the top
5. Preserve letter headings with their numbers (e.g., "ΙΕ΄. – ΠΕΤΡΩ" or "ΕΠΙΣΤΟΛΗ ΛΒ'")
6. Preserve recipient names in Greek
7. Mark unclear/damaged text with [...]

OUTPUT FORMAT:
For each letter on the page, output:
---LETTER [number]---
[Greek heading with recipient]
[Greek text of the letter]

If a letter continues from the previous page, start with:
---CONTINUED---
[Greek text]

If a letter continues onto the next page, end with:
---CONTINUES---

Output ONLY the Greek text. No Latin. No commentary."""


def download_pdf():
    """Download PG78 PDF from Internet Archive."""
    os.makedirs(PG78_DIR, exist_ok=True)

    if os.path.exists(PDF_PATH):
        size_mb = os.path.getsize(PDF_PATH) / 1024 / 1024
        print(f"PDF already exists: {PDF_PATH} ({size_mb:.0f} MB)")
        return

    print(f"Downloading PG78 from Internet Archive (~563 MB)...")
    print(f"URL: {IA_PDF_URL}")
    subprocess.run([
        'curl', '-L', '-o', PDF_PATH, '--progress-bar', IA_PDF_URL
    ], check=True)
    size_mb = os.path.getsize(PDF_PATH) / 1024 / 1024
    print(f"Downloaded: {size_mb:.0f} MB")


def extract_pages(start_page: int, end_page: int, dpi: int = 300):
    """Extract PDF pages as PNG images."""
    os.makedirs(PAGES_DIR, exist_ok=True)

    print(f"Extracting pages {start_page}-{end_page} at {dpi} DPI...")
    subprocess.run([
        'pdftoppm', '-png', '-r', str(dpi),
        '-f', str(start_page), '-l', str(end_page),
        PDF_PATH, os.path.join(PAGES_DIR, 'pg78')
    ], check=True)

    # Count extracted pages
    pages = list(Path(PAGES_DIR).glob('pg78-*.png'))
    print(f"Extracted {len(pages)} page images")
    return sorted(pages)


def ocr_page_with_gemini(image_path: str) -> str:
    """Send a page image to Gemini for OCR using the Python API."""
    from google import genai

    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")

    client = genai.Client(api_key=api_key)

    with open(image_path, 'rb') as f:
        image_data = f.read()

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                genai.types.Part.from_bytes(data=image_data, mime_type='image/png'),
                GEMINI_OCR_PROMPT,
            ]
        )
        return response.text.strip()
    except Exception as e:
        print(f"  Gemini error: {e}")
        return ""


def parse_ocr_output(text: str) -> list[dict]:
    """Parse Gemini OCR output into individual letters."""
    letters = []
    current = None

    for line in text.split('\n'):
        # Check for letter header
        m = re.match(r'---LETTER\s+(\S+)---', line)
        if m:
            if current:
                letters.append(current)
            current = {
                'number': m.group(1),
                'recipient': '',
                'text': '',
                'continued_from_prev': False,
                'continues_to_next': False,
            }
            continue

        if line.strip() == '---CONTINUED---':
            if current:
                letters.append(current)
            current = {
                'number': 'CONTINUED',
                'recipient': '',
                'text': '',
                'continued_from_prev': True,
                'continues_to_next': False,
            }
            continue

        if line.strip() == '---CONTINUES---':
            if current:
                current['continues_to_next'] = True
            continue

        if current:
            current['text'] += line + '\n'

    if current:
        letters.append(current)

    return letters


def ocr_pages(start_page: int, end_page: int, update_db: bool = False):
    """OCR a range of pages and optionally update the database."""
    os.makedirs(OCR_DIR, exist_ok=True)

    # Extract pages first
    pages = extract_pages(start_page, end_page)
    if not pages:
        print("No pages extracted")
        return

    all_letters = []

    for page_path in pages:
        page_num = page_path.stem.split('-')[-1]
        print(f"  OCR page {page_num}...", end=' ', flush=True)

        # Check for cached OCR
        cache_path = os.path.join(OCR_DIR, f'page_{page_num}.txt')
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                ocr_text = f.read()
            print("(cached)")
        else:
            ocr_text = ocr_page_with_gemini(str(page_path))
            if ocr_text:
                with open(cache_path, 'w') as f:
                    f.write(ocr_text)
                print(f"OK ({len(ocr_text)} chars)")
            else:
                print("FAILED")
                continue

            # Rate limit
            time.sleep(2)

        # Parse letters from this page
        page_letters = parse_ocr_output(ocr_text)
        for letter in page_letters:
            letter['page'] = page_num
        all_letters.extend(page_letters)

    # Summary
    letter_count = len([l for l in all_letters if l['number'] != 'CONTINUED'])
    print(f"\nExtracted {letter_count} letter headers from {len(pages)} pages")

    # Save combined output
    output_path = os.path.join(OCR_DIR, f'combined_{start_page}_{end_page}.json')
    with open(output_path, 'w') as f:
        json.dump(all_letters, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")

    if update_db:
        update_database(all_letters)


def update_database(letters: list[dict]):
    """Update latin_text in the database with clean OCR Greek."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    updated = 0
    for letter in letters:
        if letter['number'] == 'CONTINUED':
            continue

        # Try to match letter number to database
        try:
            letter_num = int(re.sub(r'[^0-9]', '', letter['number']))
        except ValueError:
            continue

        # Check if letter exists
        cur.execute(
            "SELECT id, length(latin_text) FROM letters WHERE collection='isidore_pelusium' AND letter_number=?",
            (letter_num,)
        )
        row = cur.fetchone()
        if not row:
            continue

        clean_greek = letter['text'].strip()
        if len(clean_greek) < 20:
            continue

        cur.execute(
            "UPDATE letters SET latin_text = ? WHERE id = ?",
            (clean_greek, row[0])
        )
        updated += 1

    conn.commit()
    print(f"Updated {updated} letters in database with clean Greek")
    conn.close()


def main():
    parser = argparse.ArgumentParser(description='OCR Patrologia Graeca with Gemini')
    parser.add_argument('--download', action='store_true', help='Download PG78 PDF')
    parser.add_argument('--ocr', action='store_true', help='Run OCR on pages')
    parser.add_argument('--update-db', action='store_true', help='Update database with OCR results')
    parser.add_argument('--start-page', type=int, default=ISIDORE_START_PAGE)
    parser.add_argument('--end-page', type=int, default=ISIDORE_END_PAGE)
    parser.add_argument('--map-pages', action='store_true', help='Show page-to-letter mapping')
    args = parser.parse_args()

    if args.download:
        download_pdf()
    elif args.ocr:
        if not os.path.exists(PDF_PATH):
            print("PDF not found. Run with --download first.")
            sys.exit(1)
        ocr_pages(args.start_page, args.end_page, args.update_db)
    elif args.map_pages:
        print("Page mapping requires OCR data. Run --ocr first.")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
