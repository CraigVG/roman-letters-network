#!/usr/bin/env python3
"""Resumable Gemini-Vision OCR driver for Isidore of Pelusium (PG78).

Extracts each PDF page in the Isidore range and OCRs it to data/pg78_ocr/ocr_output/page-NNNN.txt.
Skips pages already done. Does NOT touch the database — produces clean Greek text for later
matching/import review. Uses gemini-3.1-flash-lite (per project rule).

Run:  GEMINI_API_KEY=... .ocr-venv/bin/python scripts/ocr_isidore_driver.py --start 95 --end 830
"""
import os, sys, argparse, subprocess, time
from pathlib import Path
from google import genai

ROOT = Path(__file__).resolve().parent.parent

PROMPT_TMPL = """You are performing OCR on a page from Patrologia Graeca (Migne, 1860), containing the Greek letters of {author}. The page has two columns of Greek text (ignore the parallel Latin translation if present; transcribe ONLY the Greek).

Transcribe the Greek accurately with correct polytonic accents and breathings. Preserve the letter structure: when a new letter begins it is marked by a number and a recipient name (e.g. ΡΛ΄. ΚΑΛΛΙΟΠΙΩ). Output each new letter as:
---LETTER <number>. – <RECIPIENT>---
<greek text>

If the text at the very top of the page continues a letter from the previous page, begin with:
---CONTINUED---
<greek text>

Output ONLY the transcription with these markers. No commentary, no Latin, no translation."""


def ocr_page(client, img_path):
    with open(img_path, 'rb') as f:
        data = f.read()
    for attempt in range(4):
        try:
            r = client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=[genai.types.Part.from_bytes(data=data, mime_type='image/png'), PROMPT],
            )
            return (r.text or '').strip()
        except Exception as e:
            if attempt == 3:
                print(f'    FAILED {img_path.name}: {e}', flush=True)
                return ''
            time.sleep(5 * (attempt + 1))
    return ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=95)
    ap.add_argument('--end', type=int, default=830)
    ap.add_argument('--dpi', type=int, default=200)
    ap.add_argument('--pdf', default=str(ROOT / 'data/pg78_ocr/pg78.pdf'))
    ap.add_argument('--outdir', default=str(ROOT / 'data/pg78_ocr'))
    ap.add_argument('--author', default='Isidore of Pelusium')
    a = ap.parse_args()
    global PDF, PAGES, OUT, PROMPT
    PDF = Path(a.pdf); OUT = Path(a.outdir) / 'ocr_output'; PAGES = Path(a.outdir) / 'pages'
    PAGES.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
    PROMPT = PROMPT_TMPL.format(author=a.author)
    key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not key:
        sys.exit('no GEMINI_API_KEY')
    client = genai.Client(api_key=key)
    done = total = 0
    for p in range(a.start, a.end + 1):
        outf = OUT / f'page-{p:04d}.txt'
        if outf.exists() and outf.stat().st_size > 0:
            done += 1
            continue
        img = PAGES / f'pg78-{p}.png'
        if not img.exists():
            subprocess.run(['pdftoppm', '-png', '-r', str(a.dpi), '-f', str(p), '-l', str(p),
                            str(PDF), str(PAGES / 'pg78')], check=False)
            # pdftoppm zero-pads to match page count width; find the produced file
            cands = list(PAGES.glob(f'pg78-*{p}.png'))
            img = next((c for c in cands if c.stem.split('-')[-1].lstrip('0') == str(p)), img)
        if not img.exists():
            print(f'  page {p}: no image extracted', flush=True)
            continue
        txt = ocr_page(client, img)
        outf.write_text(txt, encoding='utf-8')
        total += 1
        if total % 10 == 0:
            print(f'  OCRed {total} pages (last={p})', flush=True)
        img.unlink(missing_ok=True)  # free disk as we go
    print(f'DONE: {total} newly OCRed, {done} already present, range {a.start}-{a.end}', flush=True)


if __name__ == '__main__':
    main()
