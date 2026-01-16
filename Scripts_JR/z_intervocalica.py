#----------------------------
# z_intervocalica.py
#----------------------------
# This script searches for intervocalic 's' (pronounced as [z]) in Italian text files.
# Pattern: Vowel-s-Vowel inside a word (e.g., "francese", "casa")

#--------- IMPORTS ---------
from pathlib import Path
import re
import json

# --------- CONFIG ---------
TXT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/Ampliamento parlanti 20260116/transcriptions")
OUTPUT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/Ampliamento parlanti 20260116/transcriptions/OUTPUT_DIR")
OUTPUT_FILE = OUTPUT_DIR / "z_intervocalica_occurrences_ampliamento_20260116.json"

# --------- CONSTANTS ---------
VOWELS = "aeiouàèéìòù"


# --------- FUNCTIONS ---------

def parse_timestamped_line(line):
    pattern = r'\[(\d{2}:\d{2}\.\d) - (\d{2}:\d{2}\.\d)\] (.+)'
    match = re.match(pattern, line)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None


def find_intervocalic_s(text):
    text_lower = text.lower()
    pattern = rf'\b\w*[{VOWELS}]s(?!s)[{VOWELS}]\w*\b'
    
    # findall returns a list of all matching words
    return re.findall(pattern, text_lower)


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
    
    # Load existing results
    all_occurrences, already_processed = load_existing_occurrences(OUTPUT_FILE)
    
    if already_processed:
        print(f"\nFound {len(already_processed)} already processed files. Skipping them.\n")
    
    if all_occurrences:
        print(f"Loaded {len(all_occurrences)} existing occurrences.\n")
    
    # Find all txt files
    txt_files = sorted(TXT_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} txt files\n")
    
    # Filter out already processed files
    files_to_process = [f for f in txt_files if f.name not in already_processed]
    
    if not files_to_process:
        print("All files have already been processed!")
        print(f"To reprocess, delete: {OUTPUT_FILE}")
        return
    
    print(f"Will process {len(files_to_process)} new files:\n")
    
    # Process each file
    for i, txt_file in enumerate(files_to_process, 1):
        print(f"[{i}/{len(files_to_process)}] Processing: {txt_file.name}")
        
        try:
            lines = txt_file.read_text(encoding='utf-8').splitlines()
            file_count = 0
            
            for line in lines:
                start_time, end_time, text = parse_timestamped_line(line)
                
                if text:
                    words = find_intervocalic_s(text)
                    
                    for word in words:
                        all_occurrences.append({
                            'filename': txt_file.name,
                            'start': start_time,
                            'end': end_time,
                            'word': word,
                            'context': text.strip()
                        })
                        file_count += 1
            
            print(f"   → Found {file_count} occurrences")
            already_processed.add(txt_file.name)
            
        except Exception as e:
            print(f"   ✗ Error processing {txt_file.name}: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY: Intervocalic 's' [z]")
    print("=" * 60)
    print(f"Total files processed: {len(already_processed)}")
    print(f"Total occurrences: {len(all_occurrences)}")
    
    # Save JSON
    output_data = {
        'total_occurrences': len(all_occurrences),
        'processed_files': sorted(already_processed),
        'occurrences': sorted(all_occurrences, key=lambda x: (x['filename'], x['start']))
    }
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()