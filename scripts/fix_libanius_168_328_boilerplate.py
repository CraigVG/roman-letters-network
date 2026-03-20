#!/usr/bin/env python3
"""Fix the 4 boilerplate letters in Libanius 168-328 range."""
import sqlite3, subprocess, json, os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

conn = sqlite3.connect(DB_PATH, timeout=30)
conn.execute("PRAGMA journal_mode=WAL")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, letter_number, modern_english, latin_text FROM letters WHERE collection='libanius' AND id IN (8072, 8073, 8075, 8079)")
letters = [dict(r) for r in cur.fetchall()]

# Extract existing To headers
for l in letters:
    me = l['modern_english'] or ''
    if '\n\n' in me:
        l['to_header'] = me.split('\n\n', 1)[0]
    else:
        l['to_header'] = ''

prompt = """Translate these Libanius letters from Greek to modern English.
Libanius: urbane pagan rhetorician, Antioch, 4th century. Keep his brevity and wit.
Return ONLY a JSON array: [{"id": <id>, "translation": "<body text only>"}]
Body text only - no "To Name. (date)" header line.

"""
for l in letters:
    prompt += f"--- Letter {l['letter_number']} (ID: {l['id']}) ---\n"
    prompt += f"Greek:\n{(l['latin_text'] or '')[:2000]}\n\n"

result = subprocess.run(['claude', '--print'], input=prompt, capture_output=True, text=True, timeout=180)
output = result.stdout.strip()

# Parse JSON
if '```json' in output:
    start = output.index('```json') + 7
    end = output.index('```', start)
    output = output[start:end].strip()
elif '```' in output:
    start = output.index('```') + 3
    end = output.index('```', start)
    output = output[start:end].strip()

bracket_start = output.find('[')
bracket_end = output.rfind(']')
if bracket_start != -1:
    output = output[bracket_start:bracket_end + 1]

translations = json.loads(output)
print(f'Got {len(translations)} translations')

for t in translations:
    lid = t['id']
    matching = next((l for l in letters if l['id'] == lid), None)
    if matching:
        new_text = matching['to_header'] + '\n\n' + t['translation'].strip()
        conn.execute('UPDATE letters SET modern_english = ? WHERE id = ?', (new_text, lid))
        print(f'Saved letter {matching["letter_number"]}')

conn.commit()
conn.close()
print('Done')
