#----------------------------
# liquid_consonant.py
#----------------------------
# This script searches for liquid + consonant clusters in Italian:
#   l + C  (e.g. "Salvatore" -> lv, "alto" -> lt, "calpestare" -> lp)
#   r + C  (e.g. "perché" -> rc, "porta" -> rt, "carbone" -> rb)
#
# Patterns tracked:
#   WITHIN-WORD:
#     - l or r followed by any consonant
#     - EXCLUDING ll, rr  (geminates, not real clusters)
#     - EXCLUDING l+h, r+h  (h is silent and doesn't form a cluster)
#
#   WORD-BOUNDARY:
#     - word ending in l + next word starting with any consonant
#     - word ending in r + next word starting with any consonant
#     - same exclusions (geminates, h)
#
# NOTE: word-initial l/r + consonant is impossible in native Italian
# (no native word starts with "lt-", "rk-", etc.), so position is always
# 'word-internal' for the within-word matches.
#
# Input: WhisperX-style JSON files with word-level timestamps.
# Output: occurrence list with word-level timestamps.
#   - within-word matches: 'word' + its start/end
#   - word-boundary matches: 'word1' + 'word2', start = word1.start, end = word2.end

#--------- IMPORTS ---------
from pathlib import Path
import json

# --------- CONFIG ---------
JSON_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/whisperx_output/laureato")  # <--- CHANGE HERE
OUTPUT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/OUTPUT scripts")
OUTPUT_FILE = OUTPUT_DIR / "liquid_consonant_occurrences_laureato.json"

# --------- CONSTANTS ---------
VOWELS = set("aeiouàèéìòùáíúy")  # y included as semi-vowel just in case
LIQUIDS = {"l", "r"}


def is_consonant(ch):
    """A consonant is any letter that is not a vowel, not an apostrophe,
    and not 'h' (silent in Italian)."""
    if not ch.isalpha():
        return False
    ch = ch.lower()
    if ch in VOWELS:
        return False
    if ch == "h":
        return False
    return True


# --------- FUNCTIONS ---------

def clean_word(word):
    """Strip leading/trailing punctuation."""
    return word.strip(".,!?;:\"()[]{}…—–-").strip()


def find_within_word_matches(word):
    """
    Find l/r + consonant clusters INSIDE a single word.
    Excludes ll, rr (geminates) and l+h, r+h.
    Returns a list of dicts:
        - cluster: 2-letter match (e.g. 'lv', 'rc', 'lt')
        - liquid:  'l' or 'r'
        - index:   where in the word the liquid sits
    """
    cleaned = clean_word(word).lower()
    if len(cleaned) < 2:
        return []

    results = []

    for i, ch in enumerate(cleaned):
        if ch not in LIQUIDS:
            continue

        if i + 1 >= len(cleaned):
            continue
        next_ch = cleaned[i + 1]

        # Exclude geminates: ll, rr
        if next_ch == ch:
            continue

        # Must be a consonant after (this also filters out h)
        if not is_consonant(next_ch):
            continue

        results.append({
            "cluster": ch + next_ch,
            "liquid": ch,
            "index": i,
        })

    return results


def check_word_boundary(word1_text, word2_text):
    """
    Check if word1 ends in l/r and word2 begins with a consonant (not h,
    not the same liquid).
    Returns the 2-letter cluster (e.g. 'lt', 'rc') if a match, else None.
    """
    w1 = clean_word(word1_text).lower()
    w2 = clean_word(word2_text).lower()

    if not w1 or not w2:
        return None

    last_ch = w1[-1]
    first_ch = w2[0]

    if last_ch not in LIQUIDS:
        return None

    # Geminate at boundary (e.g. "il libro" -> ll): exclude
    if first_ch == last_ch:
        return None

    if not is_consonant(first_ch):
        return None

    return last_ch + first_ch


def load_existing_occurrences(json_file):
    """Resume support: load already-saved results."""
    if not json_file.exists():
        return [], set()

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            occurrences = data.get("occurrences", [])
            processed_files = set(data.get("processed_files", []))
            return occurrences, processed_files
    except Exception as e:
        print(f"Warning: Could not read existing JSON: {e}")
        return [], set()


def process_json_file(json_file):
    """
    Walk through every segment & word. For each word, find within-word matches
    AND check the boundary with the next word (within the same segment).
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    file_occurrences = []
    segments = data.get("segments", [])

    for segment in segments:
        words = segment.get("words", [])
        context = segment.get("text", "").strip()

        # --- WITHIN-WORD matches ---
        for word_obj in words:
            word_text = word_obj.get("word", "")
            start = word_obj.get("start")
            end = word_obj.get("end")
            score = word_obj.get("score")

            hits = find_within_word_matches(word_text)

            for hit in hits:
                file_occurrences.append({
                    "filename": json_file.name,
                    "type": "within-word",
                    "start": start,
                    "end": end,
                    "word": clean_word(word_text),
                    "word2": None,
                    "cluster": hit["cluster"],
                    "liquid": hit["liquid"],
                    "char_index": hit["index"],
                    "score": score,
                    "score2": None,
                    "context": context,
                })

        # --- WORD-BOUNDARY matches ---
        for i in range(len(words) - 1):
            w1 = words[i]
            w2 = words[i + 1]

            cluster = check_word_boundary(w1.get("word", ""), w2.get("word", ""))
            if cluster is None:
                continue

            file_occurrences.append({
                "filename": json_file.name,
                "type": "word-boundary",
                "start": w1.get("start"),
                "end": w2.get("end"),
                "word": clean_word(w1.get("word", "")),
                "word2": clean_word(w2.get("word", "")),
                "cluster": cluster,
                "liquid": cluster[0],
                "char_index": None,
                "score": w1.get("score"),
                "score2": w2.get("score"),
                "context": context,
            })

    return file_occurrences


def main():
    print(f"Looking for JSON files in: {JSON_DIR}")

    all_occurrences, already_processed = load_existing_occurrences(OUTPUT_FILE)

    if already_processed:
        print(f"\nFound {len(already_processed)} already processed files. Skipping them.\n")

    if all_occurrences:
        print(f"Loaded {len(all_occurrences)} existing occurrences.\n")

    json_files = sorted(JSON_DIR.glob("*.json"))
    print(f"Found {len(json_files)} JSON files\n")

    files_to_process = [f for f in json_files if f.name not in already_processed]

    if not files_to_process:
        print("All files have already been processed!")
        print(f"To reprocess, delete: {OUTPUT_FILE}")
        return

    print(f"Will process {len(files_to_process)} new files:\n")

    for i, json_file in enumerate(files_to_process, 1):
        print(f"[{i}/{len(files_to_process)}] Processing: {json_file.name}")

        try:
            file_occurrences = process_json_file(json_file)
            all_occurrences.extend(file_occurrences)
            already_processed.add(json_file.name)
            print(f"   → Found {len(file_occurrences)} occurrences")
        except Exception as e:
            print(f"   ✗ Error processing {json_file.name}: {e}")

    # Statistics
    within_count = sum(1 for o in all_occurrences if o["type"] == "within-word")
    boundary_count = sum(1 for o in all_occurrences if o["type"] == "word-boundary")
    l_count = sum(1 for o in all_occurrences if o["liquid"] == "l")
    r_count = sum(1 for o in all_occurrences if o["liquid"] == "r")

    cluster_counts = {}
    for o in all_occurrences:
        cluster_counts[o["cluster"]] = cluster_counts.get(o["cluster"], 0) + 1

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY: Liquid + consonant (l/r + C)")
    print("=" * 60)
    print(f"Total files processed: {len(already_processed)}")
    print(f"Total occurrences: {len(all_occurrences)}")
    print(f"  - Within-word:    {within_count}")
    print(f"  - Word-boundary:  {boundary_count}")
    print(f"  - 'l' clusters:   {l_count}")
    print(f"  - 'r' clusters:   {r_count}")
    print("\n  Per-cluster (top 20):")
    for cluster, count in sorted(cluster_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"    {cluster}: {count}")

    # Save JSON
    output_data = {
        "total_occurrences": len(all_occurrences),
        "within_word_count": within_count,
        "word_boundary_count": boundary_count,
        "l_count": l_count,
        "r_count": r_count,
        "per_cluster_count": cluster_counts,
        "processed_files": sorted(already_processed),
        "occurrences": sorted(
            all_occurrences,
            key=lambda x: (x["filename"], x["start"] if x["start"] is not None else 0.0),
        ),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()