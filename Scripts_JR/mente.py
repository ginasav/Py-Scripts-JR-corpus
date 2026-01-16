#----------------------------
# mente.py
#----------------------------
# This script is for searching for 'mente' in text files, managing them based on audio file and timestamps, and counting occurrences.

#--------- IMPORTS ---------
from pathlib import Path
import re
import json
from datetime import datetime

# --------- CONFIG ---------
TXT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/Ampliamento parlanti 20260116/transcriptions") # <--- CHANGE HERE
OUTPUT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/Ampliamento parlanti 20260116/transcriptions/OUTPUT_DIR")
OUTPUT_FILE = OUTPUT_DIR / "mente_occurrences_ampliamento_20260116.json"

# FUNCTION FOR PARSE TIMESTAMPS
"""
Parse a line like: [00:15.2 - 00:18.7] Ciao come va?
Return: (start_time, end_time, text) or (None, None, None) if not matched
"""
def parse_timestamped_line(line):
    pattern = r'\[(\d{2}:\d{2}\.\d) - (\d{2}:\d{2}\.\d)] (.+)'
    match = re.match(pattern, line)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None

# MAIN FUNCTION TO LOOK FOR MENTE
"""
Find all words ending with mente in text.
Return list of matched words.
"""
def find_mente_in_txt(text):
    text_lower = text.lower()
    # Pattern that catches 'mente' or 'ment'
    pattern = r'\b\w*(mente?)\b'
    results = []
    for match in re.finditer(pattern, text_lower):
        word = match.group(0) #full word
        ending = match.group(1) #caduta finale
        is_caduta = ending == "ment"
        results.append((word, is_caduta))
        
    return results

# LOAD ALREADY PROCESSED FILES
def load_already_processed_files(output_file):
    """
    Load existing JSON data if file exists.
    """
    if not output_file.exists():
        return set()
    
    processed_files = set ()
    try:
        content = output_file.read_text(encoding='utf-8')
        # Look for lines like "FILE: filename.txt"
        pattern = r'^FILE: (.+\.txt)$'
        for line in content.splitlines():
            match = re.match(pattern, line)
            if match:
                processed_files.add(match.group(1))
    except Exception as e:
        print(f"Warning: Could not read existing output file: {e}")
        return set()
    
    return processed_files

# LOAD EXISTING OCCURRENCES
def load_existing_occurrences(json_file):
    """
    Load occurrences from existing output file to combine with new results.
    Returns: (list of occurrences, set of processed files)
    """
    if not json_file.exists():
        return [], set()
    
    existing_occurrences = []
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            occurrences = data.get('occurrences', [])
            processed_files = set(data.get('processed_files', []))
            return occurrences, processed_files
    except Exception as e:
        print(f"Warning: Could not read existing JSON: {e}")
        return [], set()

# FUNCTION THAT RETURNS THE ANALYSIS
def main():
    print(f"Looking for txt files in :{TXT_DIR}")
    
    # Check which files were already processed
    all_occurrences, already_processed = load_existing_occurrences(OUTPUT_FILE)
    
    if already_processed:
        print(f"\nFound existing results file with {len(already_processed)} already processed files:")
        for filename in sorted(already_processed):
            print(f"  ✓ {filename}")
        print(f"\nThese files will be skipped.\n")
    
    if all_occurrences:
        print(f"Loaded {len(all_occurrences)} existing occurrences from previous runs.\n")
    
    #Find all txt files
    txt_files = sorted(TXT_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} txt files\n")
    
    # Filter out already processed files
    files_to_process = [f for f in txt_files if f.name not in already_processed]
    
    if not files_to_process:
        print("All files have already been processed! Nothing to do.")
        print(f"If you want to reprocess, delete or rename: {OUTPUT_FILE}")
        return
    
    print(f"Will process {len(files_to_process)} new files:\n")
    
    
    #Track all occurrences with timestamp and audiofile info
    # all_occurrences = []
    
    # Process each txt file
    for i, txt_file in enumerate(files_to_process, 1):
        print(f"[{i}/{len(files_to_process)}] Processing: {txt_file.name}")
        
        try:
            lines = txt_file.read_text(encoding='utf-8').splitlines()
            file_count = 0
            
            for line in lines:
                #Parse timestamp and txt
                start_time, end_time, text = parse_timestamped_line(line)
                
                if text: #if successfully the line was parsed
                    mente_results = find_mente_in_txt(text)
                    
                    if mente_results:
                        for word, is_caduta in mente_results:
                            all_occurrences.append({
                                'filename': txt_file.name,
                                'start': start_time,
                                'end': end_time,
                                'word': word,
                                'caduta': is_caduta,
                                'context': text.strip()
                            })
                            file_count += 1
                            
            print(f" -> Found {file_count} occurrences")
            already_processed.add(txt_file.name)
            
        except Exception as e:
            print(f" ❌ Error processing {txt_file.name}: {e}")
            
    #Count caduta vs full forms + statistics
    caduta_count = sum(1 for occ in all_occurrences if occ['caduta'])
    full_count = len(all_occurrences) - caduta_count
    caduta_rate = round(caduta_count/len(all_occurrences)*100, 1) if all_occurrences else 0.0
            
    # PRINT SUMMARY
    print("\n" + "="*60) #separator
    print("SUMMARY of '-mente'")
    print("="*60)
    print(f"Total files in results: {len(already_processed)}")
    print(f"  - Previously processed: {len(already_processed) - len(files_to_process)}")
    print(f"  - Newly processed: {len(files_to_process)}")
    print(f"Total occurrences: {len(all_occurrences)}")
    print(f"  - Full forms (-mente): {full_count}")
    print(f"  - Truncated forms (-ment): {caduta_count}")
    print(f" - Caduta rate: {caduta_rate}%")

    
    # JSON output
    output_data = {
        'total_occurrences': len(all_occurrences),
        'full_forms': full_count,
        'caduta_forms': caduta_count,
        'caduta_rate': caduta_rate,
        'processed_files': sorted(already_processed),
        'occurrences': sorted(all_occurrences, key=lambda x: (x['filename'], x['start']))
    }
    
    #Save to JSON
    with open (OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n✅ Results saved to: {OUTPUT_FILE}")
    
    if files_to_process:
        print(f"\nN.B.: Next time you run this script, these {len(files_to_process)} files will be skipped.")
        print(f"To reprocess them, delete or rename: {OUTPUT_FILE}")
        
if __name__ == "__main__":
    main()
#----------------------------