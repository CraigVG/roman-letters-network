#!/usr/bin/env python3
"""Parse the Gemini OCR output for Isidore (PG78) into structured letters.

Reads data/pg78_ocr/ocr_output/page-*.txt in page order, stitches ---CONTINUED---
spillover, converts Greek numerals to arabic, and emits data/pg78_ocr/isidore_letters.json
(list of {number, greek_numeral, recipient, greek_text, pages}). Also prints a
source-numbering gate report (sequence sanity, duplicates, gaps). No DB writes.
"""
import re, json, glob, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data/pg78_ocr/ocr_output'

# Greek numeral values
VAL = {
    'Α':1,'Β':2,'Γ':3,'Δ':4,'Ε':5,'Ϛ':6,'ΣΤ':6,'Ζ':7,'Η':8,'Θ':9,
    'Ι':10,'Κ':20,'Λ':30,'Μ':40,'Ν':50,'Ξ':60,'Ο':70,'Π':80,'Ϟ':90,'Ϙ':90,
    'Ρ':100,'Σ':200,'Τ':300,'Υ':400,'Φ':500,'Χ':600,'Ψ':700,'Ω':800,'Ϡ':900,
}

def greek_to_int(s):
    s = s.replace('΄', '').replace("'", '').replace('’', '').strip().upper()
    s = s.replace('ΣΤ', 'Ϛ')
    total = 0
    for ch in s:
        if ch in VAL:
            total += VAL[ch]
        elif ch.strip() == '':
            continue
        else:
            return None  # unrecognized char
    return total if total > 0 else None

HEADER = re.compile(r'^---LETTER\s+(.+?)\.?\s*[–\-]\s*(.*?)---\s*$')

def main():
    pages = sorted(glob.glob(str(OUT / 'page-*.txt')),
                   key=lambda p: int(re.search(r'page-(\d+)', p).group(1)))
    letters = []
    cur = None
    for pf in pages:
        pageno = int(re.search(r'page-(\d+)', pf).group(1))
        text = Path(pf).read_text(encoding='utf-8', errors='replace')
        for line in text.split('\n'):
            h = HEADER.match(line.strip())
            if h:
                if cur:
                    letters.append(cur)
                num_raw = h.group(1).strip()
                cur = {'greek_numeral': num_raw, 'number': greek_to_int(num_raw),
                       'recipient': h.group(2).strip(), 'greek_text': '', 'pages': [pageno]}
                continue
            if line.strip() == '---CONTINUED---':
                # spillover: append to the current letter (continuation of prev page's last letter)
                if cur and pageno not in cur['pages']:
                    cur['pages'].append(pageno)
                continue
            if cur is not None:
                cur['greek_text'] += line + '\n'
    if cur:
        letters.append(cur)
    for L in letters:
        L['greek_text'] = L['greek_text'].strip()

    # write
    json.dump(letters, open(ROOT / 'data/pg78_ocr/isidore_letters.json', 'w'), ensure_ascii=False, indent=1)

    # --- source-numbering gate report ---
    nums = [L['number'] for L in letters if L['number'] is not None]
    unparsed = [L['greek_numeral'] for L in letters if L['number'] is None]
    from collections import Counter
    dup = {n: c for n, c in Counter(nums).items() if c > 1}
    print(f'Parsed letters: {len(letters)}')
    print(f'  with arabic number: {len(nums)} | unparsed numerals: {len(unparsed)}')
    if nums:
        print(f'  number range: {min(nums)}..{max(nums)}')
    print(f'  duplicate numbers: {len(dup)} {dict(list(dup.items())[:10])}')
    print(f'  sample unparsed: {unparsed[:8]}')
    # sequence monotonic check (Migne is per-book; detect resets)
    resets = sum(1 for a, b in zip(nums, nums[1:]) if b < a - 2)
    print(f'  descending jumps (book resets?): {resets}')
    # short/empty bodies
    short = sum(1 for L in letters if len(L['greek_text']) < 40)
    print(f'  letters with <40 chars body: {short}')

if __name__ == '__main__':
    main()
