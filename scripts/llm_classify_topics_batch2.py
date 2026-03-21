#!/usr/bin/env python3
"""
LLM-based topic classification for letters missing topics — BATCH 2 (second half).

Skips the first 850 letters (already done in batch 1) and classifies the rest.
Uses claude-sonnet-4-20250514 via the Anthropic API.
"""

import sqlite3
import json
import time
import anthropic

DB_PATH = "/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db"
BATCH_SIZE = 25
SKIP = 850
MODEL = "claude-sonnet-4-20250514"

CATEGORIES = (
    "arianism, barbarian_invasion, christology, church_state_conflict, conversion, "
    "diplomatic, donatism, education_books, famine_plague, friendship, grief_death, "
    "humor, illness, imperial_politics, monasticism, papal_authority, pelagianism, "
    "property_economics, slavery_captivity, travel_mobility, women"
)

SYSTEM_PROMPT = f"""Classify each letter into one or more topic categories. Return ONLY a JSON array of objects with "id" and "topics" (comma-separated string).

Categories: {CATEGORIES}

If a letter doesn't clearly fit any category, use "friendship" as default (most ancient letters are fundamentally about maintaining social bonds).

Return ONLY valid JSON like: [{{"id": 123, "topics": "friendship,travel_mobility"}}, ...]"""


def classify_batch(client: anthropic.Anthropic, batch: list[dict]) -> list[dict] | None:
    """Call the API for a batch of letters. Returns list of {id, topics} dicts or None on failure."""
    letters_text = ""
    for letter in batch:
        text = (letter["modern_english"] or "")[:300]
        letters_text += f"ID:{letter['id']} | {letter['collection']} | {text}\n---\n"

    prompt = f"{SYSTEM_PROMPT}\n\nLetters:\n{letters_text}"

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            # Remove first line (```json or ```) and last line (```)
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  [ERROR] JSON parse failed: {e}")
        print(f"  Raw response (first 500 chars): {raw[:500]}")
        return None
    except anthropic.APIError as e:
        print(f"  [ERROR] API error: {e}")
        return None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Fetch all letters missing topics, ordered by id, skip first 850
    rows = conn.execute(
        "SELECT id, collection, modern_english FROM letters "
        "WHERE topics IS NULL OR length(topics) = 0 "
        "ORDER BY id"
    ).fetchall()

    total_missing = len(rows)
    print(f"Total letters missing topics: {total_missing}")

    batch2_rows = rows[SKIP:]
    print(f"Skipping first {SKIP}, processing remaining {len(batch2_rows)} letters.")
    print(f"ID range: {batch2_rows[0]['id']} — {batch2_rows[-1]['id']}\n")

    if not batch2_rows:
        print("Nothing to process.")
        conn.close()
        return

    # Split into batches of BATCH_SIZE
    batches = [batch2_rows[i:i + BATCH_SIZE] for i in range(0, len(batch2_rows), BATCH_SIZE)]
    print(f"Processing {len(batches)} batches of up to {BATCH_SIZE} letters each.\n")

    client = anthropic.Anthropic()

    total_classified = 0
    total_errors = 0
    sample_results = []

    for batch_num, batch in enumerate(batches, start=1):
        batch_list = [dict(row) for row in batch]
        ids = [r["id"] for r in batch_list]
        print(f"Batch {batch_num}/{len(batches)} — IDs {ids[0]}–{ids[-1]} ({len(batch_list)} letters)...", end=" ", flush=True)

        result = classify_batch(client, batch_list)

        # Retry once on failure
        if result is None:
            print("retrying in 5s...", end=" ", flush=True)
            time.sleep(5)
            result = classify_batch(client, batch_list)

        if result is None:
            print(f"FAILED — skipping batch {batch_num}")
            total_errors += 1
            time.sleep(0.5)
            continue

        # Update database
        updates = []
        for item in result:
            try:
                letter_id = int(item["id"])
                topics = str(item["topics"]).strip()
                if topics:
                    updates.append((topics, letter_id))
            except (KeyError, ValueError, TypeError) as e:
                print(f"\n  [WARN] Bad item in response: {item} — {e}")

        if updates:
            conn.executemany(
                "UPDATE letters SET topics = ? WHERE id = ? AND (topics IS NULL OR length(topics) = 0)",
                updates
            )
            conn.commit()
            total_classified += len(updates)

            # Collect a few samples from early batches
            if len(sample_results) < 6:
                for topics_val, lid in updates[:2]:
                    sample_results.append({"id": lid, "topics": topics_val})

        print(f"done ({len(updates)} updated)")

        # Throttle between batches
        time.sleep(0.5)

    # Final stats
    remaining = conn.execute(
        "SELECT COUNT(*) FROM letters WHERE topics IS NULL OR length(topics) = 0"
    ).fetchone()[0]
    total_letters = conn.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
    with_topics = conn.execute("SELECT COUNT(*) FROM letters WHERE topics IS NOT NULL AND length(topics) > 0").fetchone()[0]

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total letters in DB:           {total_letters}")
    print(f"Letters now with topics:       {with_topics}")
    print(f"Still missing topics:          {remaining}")
    print(f"Classified this run:           {total_classified}")
    print(f"Batches with errors (skipped): {total_errors}")

    print("\nSample results:")
    for s in sample_results:
        print(f"  ID {s['id']:>6}: {s['topics']}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
