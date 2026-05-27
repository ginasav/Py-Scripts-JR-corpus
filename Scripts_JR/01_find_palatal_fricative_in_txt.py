#----------------------------
# fricative_c_ce_ci.py
#----------------------------
# This script searches for the fricative-c pattern [c]+e / [c]+i in Italian
# (e.g. "pace", "Lucia", "cuoce", "cibo", "cera", "piace").
#
# It reads WhisperX-style JSON transcriptions with WORD-LEVEL timestamps,
# so the start/end of each occurrence is the timestamp of the target word
# itself.
#
# Position is classified as:
#   - "word-initial"  -> c is the first letter of the word          (e.g. "cera", "città")
#   - "intervocalic"  -> c is between two vowels                    (e.g. "pace", "Lucia")
#
# Excluded patterns:
#   - che / chi   -> hard /k/    (the 'h' kills the affricate)
#   - sce / sci   -> /ʃ/         ("sh" sound)
#   - cce / cci   -> geminate    (consonant cluster before c, not intervocalic)

#--------- IMPORTS ---------
from pathlib import Path
import re
import json

# --------- CONFIG ---------
JSON_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/trascrizioni_audio/non-laureato")  # <--- CHANGE HERE: folder with word-level JSON files
OUTPUT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/OUTPUT scripts")
OUTPUT_FILE = OUTPUT_DIR / "soft_c_occurrences_non_laureato.json"

# --------- CONSTANTS ---------
VOWELS = "aeiouàèéìòùáíúAEIOUÀÈÉÌÒÙÁÍÚ"


# --------- FUNCTIONS ---------

def clean_word(word):
    """
    Strip punctuation from start/end of a word so we can analyse the
    letter sequence cleanly. We keep apostrophes inside the word but
    nothing else.
    """
    return word.strip(".,!?;:\"()[]{}…—–-").strip()


def find_soft_c_positions(word):
    """
    Find all palatal-c occurrences inside a single word.
    Returns a list of dicts, one per occurrence, with:
        - position: 'word-initial', 'intervocalic', or 'other'
        - pattern: the 2-letter match ('ce' or 'ci')
        - index: where in the word the 'c' is
    Already filters out che/chi, sce/sci, cce/cci.
    """
    cleaned = clean_word(word).lower()
    if not cleaned:
        return []

    results = []

    # Walk through the word looking for 'c' followed by 'e' or 'i'
    for i, ch in enumerate(cleaned):
        if ch != "c":
            continue

        # Need a next character
        if i + 1 >= len(cleaned):
            continue
        next_ch = cleaned[i + 1]

        # Must be c+e or c+i
        if next_ch not in ("e", "i"):
            continue

        # --- EXCLUSIONS ---
        # Look-ahead: if the char after e/i is 'h', that's not what we want
        # (this is just safety; "ceh"/"cih" don't really exist in Italian,
        # but it costs nothing). The real "ch" exclusion is below.

        # Exclude sce / sci  -> previous char is 's'
        if i >= 1 and cleaned[i - 1] == "s":
            continue

        # Exclude cce / cci  -> previous char is 'c' (geminate)
        if i >= 1 and cleaned[i - 1] == "c":
            continue

        # NOTE: "che" / "chi" can't fire here because the pattern is c+e/c+i,
        # not c+h. The 'h' would sit between c and e/i, so c+h would never
        # match c+e or c+i in the first place. Good.

        # --- POSITION CLASSIFICATION ---
        if i == 0:
            position = "word-initial"
        else:
            prev_ch = cleaned[i - 1]
            if prev_ch in VOWELS.lower():
                position = "intervocalic"
            else:
                position = "other"  # consonant before c (e.g. dolce, pancia)

        results.append({
            "position": position,
            "pattern": cleaned[i:i + 2],  # 'ce' or 'ci'
            "index": i,
        })

    return results


def load_existing_occurrences(json_file):
    """Resume support: load already-saved results, like your other scripts."""
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


def get_context_for_word(segment, word_index):
    """
    Return the segment text as context. The segment is the line the word
    belongs to, so it already gives a few words of surrounding context.
    """
    return segment.get("text", "").strip()


def process_json_file(json_file):
    """
    Open one WhisperX JSON file, walk through every segment & every word,
    and return a list of soft-c occurrences (word-initial + intervocalic only).
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    file_occurrences = []
    segments = data.get("segments", [])

    for segment in segments:
        words = segment.get("words", [])
        context = segment.get("text", "").strip()

        for w_idx, word_obj in enumerate(words):
            word_text = word_obj.get("word", "")
            start = word_obj.get("start")
            end = word_obj.get("end")
            score = word_obj.get("score")  # whisper confidence, useful to keep

            # Find all soft-c hits inside this word
            hits = find_soft_c_positions(word_text)

            for hit in hits:
                # Only keep word-initial and intervocalic
                if hit["position"] not in ("word-initial", "intervocalic"):
                    continue

                file_occurrences.append({
                    "filename": json_file.name,
                    "start": start,
                    "end": end,
                    "word": clean_word(word_text),
                    "pattern": hit["pattern"],          # 'ce' or 'ci'
                    "position": hit["position"],         # 'word-initial' or 'intervocalic'
                    "char_index": hit["index"],          # where the 'c' is in the word
                    "score": score,                      # whisper alignment confidence
                    "context": context,                  # the whole segment text
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

    # Find all JSON files
    json_files = sorted(JSON_DIR.glob("*.json"))
    print(f"Found {len(json_files)} JSON files\n")

    # Filter out already processed files
    files_to_process = [f for f in json_files if f.name not in already_processed]

    if not files_to_process:
        print("All files have already been processed!")
        print(f"To reprocess, delete: {OUTPUT_FILE}")
        return

    print(f"Will process {len(files_to_process)} new files:\n")

    # Process each file
    for i, json_file in enumerate(files_to_process, 1):
        print(f"[{i}/{len(files_to_process)}] Processing: {json_file.name}")

        try:
            file_occurrences = process_json_file(json_file)

            # Commit only if no exception
            all_occurrences.extend(file_occurrences)
            already_processed.add(json_file.name)
            print(f"   → Found {len(file_occurrences)} occurrences")

        except Exception as e:
            print(f"   ✗ Error processing {json_file.name}: {e}")

    # Statistics
    initial_count = sum(1 for o in all_occurrences if o["position"] == "word-initial")
    intervocalic_count = sum(1 for o in all_occurrences if o["position"] == "intervocalic")
    ce_count = sum(1 for o in all_occurrences if o["pattern"] == "ce")
    ci_count = sum(1 for o in all_occurrences if o["pattern"] == "ci")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY: Soft-c (ce/ci)")
    print("=" * 60)
    print(f"Total files processed: {len(already_processed)}")
    print(f"Total occurrences: {len(all_occurrences)}")
    print(f"  - Word-initial: {initial_count}")
    print(f"  - Intervocalic: {intervocalic_count}")
    print(f"  - Pattern 'ce': {ce_count}")
    print(f"  - Pattern 'ci': {ci_count}")

    # Save JSON
    output_data = {
        "total_occurrences": len(all_occurrences),
        "word_initial_count": initial_count,
        "intervocalic_count": intervocalic_count,
        "ce_count": ce_count,
        "ci_count": ci_count,
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