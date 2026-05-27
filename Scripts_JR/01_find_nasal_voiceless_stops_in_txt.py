#----------------------------
# nasal_voiceless_stop.py
#----------------------------
# This script searches for voiceless stops after nasal consonants — a Neapolitan
# phenomenon where /p t k/ become voiced [b d g] after a nasal:
#     monte    -> mo[nd]e
#     tempo    -> te[mb]o
#     pa[nc]a  -> pa[ng]a
#
# Patterns tracked:
#   WITHIN-WORD:
#     - n + t       (e.g. "montagna", "praticamente", "tanto")
#     - n + p       (e.g. "input"? rare)
#                    actually n+p is rare in Italian: "input" loanword.
#                    Kept for completeness in case of loanwords/foreign names.
#     - n + c       EXCLUDING n+c+e/i  (because c+e/i is /tʃ/, affricate)
#                   (e.g. "panca", "banca", "anche")
#     - m + p       (e.g. "tempo", "campo", "comprare")
#
#   WORD-BOUNDARY:
#     - word ending in 'n' + next word starting with t/p/c
#       (c excluded if next char is e/i)
#       (e.g. "non tutti", "non può", "con tanto")
#     - word ending in 'm' + next word starting with p
#       (rare but possible)
#
# Excluded:
#   - n + c + e/i  (affricate /tʃ/, not a stop)
#   - m + anything except p  (only 'mp' is a possible Italian pattern)
#
# Input: WhisperX-style JSON files with word-level timestamps.
# Output: occurrence list with word-level timestamps.
#   - within-word matches: 'word' + its start/end
#   - word-boundary matches: 'word1' + 'word2', start = word1.start, end = word2.end

#--------- IMPORTS ---------
from pathlib import Path
import json

# --------- CONFIG ---------
JSON_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/whisperx_output/non-laureato")  # <--- CHANGE HERE
OUTPUT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/OUTPUT scripts")
OUTPUT_FILE = OUTPUT_DIR / "nasal_voiceless_stop_occurrences_non_laureato.json"

# --------- CONSTANTS ---------
# Voiceless stops that can follow 'n'
N_STOPS = {"t", "p", "c"}
# Voiceless stops that can follow 'm' (per spec: only 'p')
M_STOPS = {"p"}


# --------- FUNCTIONS ---------

def clean_word(word):
    """Strip leading/trailing punctuation."""
    return word.strip(".,!?;:\"()[]{}…—–-").strip()


def find_within_word_matches(word):
    """
    Find nasal + voiceless stop clusters INSIDE a single word.
    Returns a list of dicts:
        - cluster: 2-letter match (e.g. 'nt', 'mp', 'nc')
        - index:   where in the word the nasal sits
    """
    cleaned = clean_word(word).lower()
    if len(cleaned) < 2:
        return []

    results = []

    for i, ch in enumerate(cleaned):
        # We need a character after this one
        if i + 1 >= len(cleaned):
            continue
        next_ch = cleaned[i + 1]

        if ch == "n" and next_ch in N_STOPS:
            # Exclude nc + e/i (affricate)
            if next_ch == "c" and i + 2 < len(cleaned) and cleaned[i + 2] in ("e", "i"):
                continue
            results.append({"cluster": ch + next_ch, "index": i})

        elif ch == "m" and next_ch in M_STOPS:
            results.append({"cluster": ch + next_ch, "index": i})

    return results


def check_word_boundary(word1_text, word2_text):
    """
    Check whether word1 ending + word2 beginning forms a nasal + voiceless stop
    cluster across the word boundary.
    Returns the 2-letter cluster (e.g. 'nt') if a match, else None.
    """
    w1 = clean_word(word1_text).lower()
    w2 = clean_word(word2_text).lower()

    if not w1 or not w2:
        return None

    last_ch = w1[-1]
    first_ch = w2[0]

    if last_ch == "n" and first_ch in N_STOPS:
        # Exclude n + c + e/i
        if first_ch == "c" and len(w2) >= 2 and w2[1] in ("e", "i"):
            return None
        return last_ch + first_ch

    if last_ch == "m" and first_ch in M_STOPS:
        return last_ch + first_ch

    return None


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
    AND check the boundary with the next word (within the same segment, since
    cross-segment boundaries are unreliable timing-wise).
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
                    "word2": None,            # not applicable
                    "cluster": hit["cluster"],
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
                "start": w1.get("start"),       # start of word1
                "end": w2.get("end"),           # end of word2
                "word": clean_word(w1.get("word", "")),
                "word2": clean_word(w2.get("word", "")),
                "cluster": cluster,
                "char_index": None,             # not meaningful across boundary
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

    cluster_counts = {}
    for o in all_occurrences:
        cluster_counts[o["cluster"]] = cluster_counts.get(o["cluster"], 0) + 1

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY: Voiceless stops after nasals")
    print("=" * 60)
    print(f"Total files processed: {len(already_processed)}")
    print(f"Total occurrences: {len(all_occurrences)}")
    print(f"  - Within-word:    {within_count}")
    print(f"  - Word-boundary:  {boundary_count}")
    print("\n  Per-cluster:")
    for cluster in sorted(cluster_counts):
        print(f"    {cluster}: {cluster_counts[cluster]}")

    # Save JSON
    output_data = {
        "total_occurrences": len(all_occurrences),
        "within_word_count": within_count,
        "word_boundary_count": boundary_count,
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