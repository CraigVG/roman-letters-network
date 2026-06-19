#!/usr/bin/env python3
"""Parse Nilus PG79 OCR (Roman numerals) into structured letters + numbering gate."""
import re, json, glob
from pathlib import Path
from collections import Counter
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data/pg79_ocr/ocr_output'
RVAL = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
def roman_to_int(s):
    s = s.strip().upper().replace('.', '')
    if not s or any(c not in RVAL for c in s): return None
    total, prev = 0, 0
    for c in reversed(s):
        v = RVAL[c]
        total += -v if v < prev else v
        prev = max(prev, v)
    return total or None
GVAL={'Α':1,'Β':2,'Γ':3,'Δ':4,'Ε':5,'Ϛ':6,'Ζ':7,'Η':8,'Θ':9,'Ι':10,'Κ':20,'Λ':30,'Μ':40,'Ν':50,'Ξ':60,'Ο':70,'Π':80,'Ϟ':90,'Ρ':100,'Σ':200,'Τ':300,'Υ':400,'Φ':500,'Χ':600,'Ψ':700,'Ω':800}
def greek_to_int(s):
    s=s.replace('΄','').replace("'",'').replace('’','').strip().upper().replace('ΣΤ','Ϛ')
    t=0
    for ch in s:
        if ch in GVAL: t+=GVAL[ch]
        elif ch.strip()=='': continue
        else: return None
    return t or None
def to_int(s):
    return roman_to_int(s) if roman_to_int(s) else greek_to_int(s)
HEADER = re.compile(r'^---LETTER\s+(.+?)\.?\s*[–\-]\s*(.*?)---\s*$')
def main():
    pages = sorted(glob.glob(str(OUT/'page-*.txt')), key=lambda p:int(re.search(r'page-(\d+)',p).group(1)))
    letters=[]; cur=None
    for pf in pages:
        pn=int(re.search(r'page-(\d+)',pf).group(1))
        for line in Path(pf).read_text(encoding='utf-8',errors='replace').split('\n'):
            h=HEADER.match(line.strip())
            if h:
                if cur: letters.append(cur)
                num=h.group(1).strip()
                cur={'roman':num,'number':to_int(num),'recipient':h.group(2).strip(),'greek_text':'','pages':[pn]}
            elif line.strip()=='---CONTINUED---':
                if cur and pn not in cur['pages']: cur['pages'].append(pn)
            elif cur is not None:
                cur['greek_text']+=line+'\n'
    if cur: letters.append(cur)
    for L in letters: L['greek_text']=L['greek_text'].strip()
    json.dump(letters, open(ROOT/'data/pg79_ocr/nilus_letters.json','w'), ensure_ascii=False, indent=1)
    nums=[L['number'] for L in letters if L['number']]
    dup={n:c for n,c in Counter(nums).items() if c>1}
    print(f'parsed: {len(letters)} | numbered: {len(nums)} | range {min(nums)}-{max(nums)}')
    print(f'duplicates: {len(dup)} {dict(list(dup.items())[:8])}')
    print(f'descending jumps: {sum(1 for a,b in zip(nums,nums[1:]) if b<a-2)}')
    short=sum(1 for L in letters if len(L['greek_text'])<40); print('short bodies(<40):',short)
    print('sample:',[(L['roman'],L['number'],L['recipient'][:18]) for L in letters[:3]])
if __name__=='__main__': main()
