#----------------------------
# affricazione_s.py
#----------------------------
# This script searches for words containing 's' immediately after 'l', 'r', or 'n'

#--------- IMPORTS ---------
from pathlib import Path
import re
import json

# --------- CONFIG ---------
TXT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/Ampliamento parlanti 20260116/transcriptions")
OUTPUT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/Ampliamento parlanti 20260116/transcriptions/OUTPUT_DIR")
OUTPUT_FILE = OUTPUT_DIR / "affricazione_s_ampliamento_20260116.json"


# --------- REGEX EXPLANATION ---------
"""
PATTERN: r'\b\w*[lrn]s\w*\b'

\b      = Word boundary (start of word)
\w*     = Zero or more word characters (letters/digits/underscore)
[lrn]   = Character class: matches exactly ONE of these letters: l, r, or n
s       = Literal letter 's' (must come immediately after l/r/n)
\w*     = Zero or more word characters (rest of the word)
\b      = Word boundary (end of word)
"""


def parse_timestamped_line(line):
    pattern = r'\[(\d{2}:\d{2}\.\d) - (\d{2}:\d{2}\.\d)] (.+)'
    match = re.match(pattern, line)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None


def find_s_clusters(text):
    """
    Find all words containing 's' immediately after 'l', 'r', or 'n'.
    
    Returns: list of tuples (word, cluster_type)
        - word: the full word found
        - cluster_type: which cluster was found ('ls', 'rs', or 'ns')
    """
    text_lower = text.lower()
    
    # Pattern explanation:
    # \b     = word boundary (ensures we match whole words)
    # \w*    = zero or more word characters before the cluster
    # [lrn]  = character class: matches l OR r OR n
    # s      = literal 's' immediately after
    # \w*    = zero or more word characters after the cluster
    # \b     = word boundary
    pattern = r'\b\w*[lrn]s\w*\b'
    
    results = []
    
    for match in re.finditer(pattern, text_lower):
        word = match.group(0)  # The full matched word
        
        # Now we need to find WHICH cluster(s) the word contains
        # We use a second pattern to identify the specific cluster
        cluster_pattern = r'[lrn]s'
        cluster_matches = re.findall(cluster_pattern, word)
        
        # A word might contain multiple clusters
        for cluster in cluster_matches:
            results.append((word, cluster))
    
    return results


def load_existing_occurrences(json_file):
    if not json_file.exists():
        return [], set()
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            occurrences = data.get('occurrences', [])
            processed_files = set(data.get('processed_files', []))
            return occurrences, processed_files
    except Exception as e:
        print(f"Warning: Could not read existing JSON: {e}")
        return [], set()


def main():
    print(f"Looking for txt files in: {TXT_DIR}")
    
    # Load any existing results (for incremental processing)
    all_occurrences, already_processed = load_existing_occurrences(OUTPUT_FILE)
    
    if already_processed:
        print(f"\nFound existing results with {len(already_processed)} already processed files.")
        print("These files will be skipped.\n")
    
    if all_occurrences:
        print(f"Loaded {len(all_occurrences)} existing occurrences from previous runs.\n")
    
    # Find all txt files
    txt_files = sorted(TXT_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} txt files\n")
    
    # Filter out already processed files
    files_to_process = [f for f in txt_files if f.name not in already_processed]
    
    if not files_to_process:
        print("All files have already been processed! Nothing to do.")
        print(f"To reprocess, delete or rename: {OUTPUT_FILE}")
        return
    
    print(f"Will process {len(files_to_process)} new files:\n")
    
    # Process each txt file
    for i, txt_file in enumerate(files_to_process, 1):
        print(f"[{i}/{len(files_to_process)}] Processing: {txt_file.name}")
        
        try:
            lines = txt_file.read_text(encoding='utf-8').splitlines()
            file_count = 0
            
            for line in lines:
                # Parse timestamp and text
                start_time, end_time, text = parse_timestamped_line(line)
                
                if text:  # If line was successfully parsed
                    cluster_results = find_s_clusters(text)
                    
                    if cluster_results:
                        for word, cluster_type in cluster_results:
                            all_occurrences.append({
                                'filename': txt_file.name,
                                'start': start_time,
                                'end': end_time,
                                'word': word,
                                'cluster': cluster_type,  # 'ls', 'rs', or 'ns'
                                'context': text.strip()
                            })
                            file_count += 1
            
            print(f"    -> Found {file_count} occurrences")
            already_processed.add(txt_file.name)
            
        except Exception as e:
            print(f"    ✗ Error processing {txt_file.name}: {e}")
    
    
    # Prepare JSON output
    output_data = {
        'total_occurrences': len(all_occurrences),
        'processed_files': sorted(already_processed),
        'occurrences': sorted(all_occurrences, key=lambda x: (x['filename'], x['start']))
    }
    
    # Save to JSON
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
#----------------------------