#--------------------
# diphthongs.py
#--------------------
"""
This script searches for diphthongs inside JR transcriptions.
"""

#-----IMPORT-----
from pathlib import Path
import re
import json
from datetime import datetime

#-----CONFIG-----
TXT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/Ampliamento parlanti 20260116/transcriptions")
OUTPUT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/Ampliamento parlanti 20260116/transcriptions/OUTPUT_DIR")
OUTPUT_FILE = OUTPUT_DIR / "diphthongs_occurrences_ampliamento_20260116.json"

#-----PARSE TIMESTAMPS-----
def parse_timestamped_line(line):
    pattern = r'\[(\d{2}:\d{2}\.\d) - (\d{2}:\d{2}\.\d)] (.+)'
    match = re.match(pattern, line)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None

#-----FIND DIPHTHONGS-----
def find_diphtongs(text):
    """
    Args:
        text(str): The text to search in
        
    Returns:
        list: list of tuples (word, diphtong_type)
        
    Pattern = \b\w*(ie|uo)w*\b
    """
    text_lower = text.lower()
    
    pattern = r'\b\w*(ie|uo)\w+\b'
    
    results = []
    for match in re.finditer(pattern, text_lower):
        word = match.group(0) # full word
        diphthong_type = match.group(1) # diphthong ie or uo
        results.append((word, diphthong_type))
        
    return results

#-----LOAD EXISTING DATA-----
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
    
#-----MAIN-----
def main():
    """
    Main function does:
    1. Find all .txt files in TXT_DIR
    2. Loads previously processed files if there are
    3. Processed then only new files
    4. Finds all diphthongs
    5. Saves results in a JSON file
    """
    print(f"Looking for txt files in: {TXT_DIR}")
    
    # Load existing results
    all_occurrences, already_processed = load_existing_occurrences(OUTPUT_FILE)
    
    if already_processed:
        print(f"Found existing results with {len(already_processed)} already processed files:")
        for filename in sorted(already_processed):
            print(f"{filename}")
        print(f"\nThese files will be skipped.\n")
        
    if all_occurrences:
        print(f"Loaded {len(all_occurrences)} existing occurrences from previous runs.\n")
        
    #TXT
    txt_files = sorted(TXT_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} txt files.\n")
    
    # Already processed files
    files_to_process = [f for f in txt_files if f.name not in already_processed]
    
    if not files_to_process:
        print("All files have already been processed!")
        print(f"If you want to reprocess, delete or rename: {OUTPUT_FILE}")
        return
    
    print(f"Will process {len(files_to_process)} new files:\n")
    
    #PRocess each txt file
    for i, txt_file in enumerate(files_to_process,1):
        print(f"[{i}/{len(files_to_process)}] Processing: {txt_file.name}")
        
        try:
            lines = txt_file.read_text(encoding='utf-8').splitlines()
            file_count = 0
            
            for line in lines:
                start_time, end_time, text = parse_timestamped_line(line)
                
                if text:
                    diphthong_results = find_diphtongs(text)
                    
                    if diphthong_results:
                        for word, diphthong_type in diphthong_results:
                            all_occurrences.append({
                                'filename': txt_file.name,
                                'start': start_time,
                                'end': end_time,
                                'word': word,
                                'diphthong_type': diphthong_type,
                                'context': text.strip()
                            })
                            file_count += 1
                            
            print(f" -> Found {file_count} diphthong occurrences")
            already_processed.add(txt_file.name)
        
        except Exception as e:
            print(f"Error processing {txt_file.name}: {e}")
            
    #Statistics
    ie_count = sum(1 for occ in all_occurrences if occ['diphthong_type'] == 'ie')
    uo_count = sum(1 for occ in all_occurrences if occ['diphthong_type'] == 'uo')
    total = len(all_occurrences)
    
    # PRINT SUMMARY
    print("\n" + "=" * 60)
    print("📊 SUMMARY OF ITALIAN DIPHTHONGS")
    print("=" * 60)
    print(f"Total files in results: {len(already_processed)}")
    print(f"  - Previously processed: {len(already_processed) - len(files_to_process)}")
    print(f"  - Newly processed: {len(files_to_process)}")
    print(f"\nTotal diphthong occurrences: {total}")

    # JSON output
    output_data = {
        'total_occurrences': total,
        'ie_forms': ie_count,
        'uo_forms': uo_count,
        'processed_files': sorted(already_processed),
        'occurrences': sorted(all_occurrences, key=lambda x: (x['filename'], x['start']))
    }
    
    # Output dir exists?
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"Results saved in: {OUTPUT_FILE}")
    
    if files_to_process:
        print(f"Next time you run this script, these {len(files_to_process)} files will be skipped.")
        print(f"To reprocess, delete or rename: {OUTPUT_FILE}")
        
        
if __name__ == "__main__":
    main()