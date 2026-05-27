#----------------------------
# s_palatalization.py
#----------------------------
# This script searches for Neapolitan s-palatalization contexts in Italian:
# /s/ becomes [ʃ] when followed by a non-dental consonant.
#
# Two groups of clusters are tracked: (De Blasi & Fanciullo, 2002)
#   - "stop"      -> s + p, s + b, s + c, s + g    (sp, sb, sc, sg)
#   - "fricative" -> s + f, s + v                  (sf, sv)
#
# Positions kept:
#   - "word-initial"  -> s is the first letter of the word    (e.g. "spagnolo", "sfortuna")
#   - "word-internal" -> s is anywhere else in the word       (e.g. "rispondere", "asfalto")
#
# Input: WhisperX-style JSON files with word-level timestamps.
# Output: occurrence list where start/end are the timestamps of the TARGET WORD.

#--------- IMPORTS ---------
from pathlib import Path
import json

# --------- CONFIG ---------
JSON_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/whisperx_output/non-laureato")  # <--- CHANGE HERE
OUTPUT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/OUTPUT scripts")
OUTPUT_FILE = OUTPUT_DIR / "s_palatalization_occurrences_non_laureato.json"

# --------- CONSTANTS ---------
# Map each second consonant to its group label.
STOP_CONSONANTS = {"p", "b", "c", "g"}
FRICATIVE_CONSONANTS = {"f", "v"}


# --------- FUNCTIONS ---------

def clean_word(word):
    """Strip leading/trailing punctuation."""
    return word.strip(".,!?;:\"()[]{}…—–-").strip()


def find_s_palatalization_positions(word):
    """
    Find all s + (p/b/c/g/f/v) clusters inside a single word.
    Excludes 'sc' followed by 'e' or 'i' (that's the /ʃ/ digraph, not s+stop).

    Returns a list of dicts:
        - position: 'word-initial' or 'word-internal'
        - cluster: 2-letter match ('sp', 'sb', 'sc', 'sg', 'sf', 'sv')
        - group:   'stop' or 'fricative'
        - index:   where in the word the 's' sits
    """
    cleaned = clean_word(word).lower()
    if not cleaned:
        return []

    results = []

    for i, ch in enumerate(cleaned):
        if ch != "s":
            continue

        # Need at least one char after the 's'
        if i + 1 >= len(cleaned):
            continue
        next_ch = cleaned[i + 1]

        # Decide the group
        if next_ch in STOP_CONSONANTS:
            group = "stop"
        elif next_ch in FRICATIVE_CONSONANTS:
            group = "fricative"
        else:
            continue  # not one of our target consonants

        # --- EXCLUSION: 'sc' + 'e'/'i' is the digraph /ʃ/, skip it ---
        if next_ch == "c" and i + 2 < len(cleaned) and cleaned[i + 2] in ("e", "i"):
            continue

        # --- POSITION ---
        position = "word-initial" if i == 0 else "word-internal"

        results.append({
            "position": position,
            "cluster": cleaned[i:i + 2],
            "group": group,
            "index": i,
        })

    return results


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
    Open one WhisperX JSON file, walk through every segment & word,
    and return a list of s-palatalization occurrences.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    file_occurrences = []
    segments = data.get("segments", [])

    for segment in segments:
        words = segment.get("words", [])
        context = segment.get("text", "").strip()

        for word_obj in words:
            word_text = word_obj.get("word", "")
            start = word_obj.get("start")
            end = word_obj.get("end")
            score = word_obj.get("score")

            hits = find_s_palatalization_positions(word_text)

            for hit in hits:
                file_occurrences.append({
                    "filename": json_file.name,
                    "start": start,
                    "end": end,
                    "word": clean_word(word_text),
                    "cluster": hit["cluster"],     # sp, sb, sc, sg, sf, sv
                    "group": hit["group"],          # 'stop' or 'fricative'
                    "position": hit["position"],    # 'word-initial' or 'word-internal'
                    "char_index": hit["index"],
                    "score": score,
                    "context": context,
                })

    return file_occurrences


def main():
    print(f"Looking for JSON files in: {JSON_DIR}")

    # Load existing results (resume support)
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
    initial_count = sum(1 for o in all_occurrences if o["position"] == "word-initial")
    internal_count = sum(1 for o in all_occurrences if o["position"] == "word-internal")
    stop_count = sum(1 for o in all_occurrences if o["group"] == "stop")
    fric_count = sum(1 for o in all_occurrences if o["group"] == "fricative")

    # Per-cluster breakdown
    cluster_counts = {}
    for o in all_occurrences:
        cluster_counts[o["cluster"]] = cluster_counts.get(o["cluster"], 0) + 1

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY: s-palatalization (s + non-dental consonant)")
    print("=" * 60)
    print(f"Total files processed: {len(already_processed)}")
    print(f"Total occurrences: {len(all_occurrences)}")
    print(f"  - Word-initial:  {initial_count}")
    print(f"  - Word-internal: {internal_count}")
    print(f"  - Stop group (sp/sb/sc/sg):     {stop_count}")
    print(f"  - Fricative group (sf/sv):       {fric_count}")
    print("\n  Per-cluster:")
    for cluster in sorted(cluster_counts):
        print(f"    {cluster}: {cluster_counts[cluster]}")

    # Save JSON
    output_data = {
        "total_occurrences": len(all_occurrences),
        "word_initial_count": initial_count,
        "word_internal_count": internal_count,
        "stop_group_count": stop_count,
        "fricative_group_count": fric_count,
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