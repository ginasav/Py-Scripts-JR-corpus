#----------------------------
# syllable_3_4.py
#----------------------------
# This script searches for words with exactly 3 or 4 syllables in transcription files,
# managing them based on audio file and timestamps, and counting occurrences.

#---------- IMPORTS ------------
from pathlib import Path
import re
import json
from datetime import datetime
import pyphen

#---------- CONFIGS ------------
TXT_DIR = Path("") #CHANGE HERE to directory with transcription txt files
OUTPUT_DIR = Path("") #CHANGE HERE to directory for output files
OUTPUT_FILE = OUTPUT_DIR / "syllable_3_4.json"

# Initialization of Italian hyphenation dictionary
ITALIAN_HYPHENATOR = pyphen.Pyhpen(lang='it_IT')

# FUNCTION TO PARSE TIMESTAMPS
def parse_timestamped_line(line):
    pattern = r'\[(\d{2}:\d{2}\.\d) - (\d{2}:\d{2}\.\d)] (.+)'
    match = re.match(pattern, line)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None

# FUNCTION TO COUNT SYLLABLES
"""
Return: number of syllables as int
"""
def count_syllables(word):
    # Clean the word from lowecase and punctuation
    word_clean = word.lower().strip()
    word_clean = re.sub(r'[,.!?;:"]', '', word_clean)
    
    # If empty after cleaning, return 0
    if not word_clean:
        return 0
    
    # Use pyphen
    hyphenated = ITALIAN_HYPHENATOR.inserted(word_clean)
    
    # Split by hyphen and count syllables
    syllables = hyphenated.split('-')
    
    return len(syllables)

# MAIN FUNCTION TO FIND 3-4 SYLLABLE WORDS
"""
Return: list of matched words with their syllable count
"""
def find_3_4_syllable_words(text):
    words = re.findall(r'\w+', text.lower())
    
    results = []
    for word in words:
        syllable_count = count_syllables(word)
        
        # Only 3 4 syllables
        if syllable_count == 3 or syllable_count == 4:
            results.append((word, syllable_count))
    
    return results

# LOAD EXISTING OCCURENCES 
def load_existing_occurrences(json_file):
    """
    DOn't want to overload the script, so read previous output file to add new results
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
    print(f"Looking for txt files in: {TXT_DIR}")
    
    # OUTPUT DIR IF IT DOESNT EXIST
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check already processed files
    all_occurrences, already_processed = load_existing_occurrences(OUTPUT_FILE)
    
    if already_processed:
        print(f"Skipping already processed files: {already_processed}")
        for filename in sorted(already_processed):
            print(f" - {filename}")
        print(f"\nThese files will be skipped.")
        
    if all_occurrences:
        print(f"Loaded {len(all_occurrences)} existing occurrences.")
        
    # Find txt files
    txt_files = sorted(TXT_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} txt files.")
    
    # Filter our already processed files
    files_to_process = [f for f in txt_files if f.name not in already_processed]
    
    if not files_to_process:
        print("All files have already been processed! yay!")
        print(f"If you want to reprocess, rename or delete: {OUTPUT_FILE}")
        return
    
    print(f"Processing {len(files_to_process)} new files...\n")
    
    # Process each txt file
    for i, txt_file in enumerate(files_to_process, 1):
        print(f"[{i}/{len(files_to_process)}] Processing: {txt_file.name}")
        
        try:
            lines = txt_file.read_text(encoding='utf-8').splitlines()
            file_count = 0
            
            for line in lines:
                # Parse timestamp and text
                start_time, end_time, text = parse_timestamped_line(line)
                
                if text:  # if successfully the line was parsed
                    syllable_results = find_3_4_syllable_words(text)
                    
                    if syllable_results:
                        for word, syllable_count in syllable_results:
                            all_occurrences.append({
                                'filename': txt_file.name,
                                'start': start_time,
                                'end': end_time,
                                'word': word,
                                'syllables': syllable_count,
                                'context': text.strip()
                            })
                            file_count += 1
            
            print(f" -> Found {file_count} occurrences")
            already_processed.add(txt_file.name)
            
        except Exception as e:
            print(f"Error processing {txt_file.name}: {e}")
    
    
# Count 3-syllable vs 4-syllable words + statistics
    three_syllable_count = sum(1 for occ in all_occurrences if occ['syllables'] == 3)
    four_syllable_count = sum(1 for occ in all_occurrences if occ['syllables'] == 4)
    three_syllable_rate = round(three_syllable_count/len(all_occurrences)*100, 1) if all_occurrences else 0.0
    four_syllable_rate = round(four_syllable_count/len(all_occurrences)*100, 1) if all_occurrences else 0.0
    
    # PRINT SUMMARY
    print("\n" + "="*60)  # separator
    print("SUMMARY of 3 & 4-SYLLABLE WORDS")
    print("="*60)
    print(f"Total files in results: {len(already_processed)}")
    print(f"  - Previously processed: {len(already_processed) - len(files_to_process)}")
    print(f"  - Newly processed: {len(files_to_process)}")
    print(f"Total occurrences: {len(all_occurrences)}")
    print(f"  - 3-syllable words: {three_syllable_count} ({three_syllable_rate}%)")
    print(f"  - 4-syllable words: {four_syllable_count} ({four_syllable_rate}%)")
    
    # JSON output
    output_data = {
        'processed_files': sorted(already_processed),
        'occurrences': sorted(all_occurrences, key=lambda x: (x['filename'], x['start']))
    }
    
    # Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Results saved to: {OUTPUT_FILE}")
    
    if files_to_process:
        print(f"\nN.B.: Next time you run this script, these {len(files_to_process)} files will be skipped.")
        print(f"To reprocess them, delete or rename: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
#----------------------------

