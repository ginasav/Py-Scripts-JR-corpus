#------------------------------
# intervocalic_bg.py
#------------------------------

'''
This script searches for intervocalic 'b' and 'g' in the JR transcription files.
It fined both word-internal class (e.g., 'abito' or 'progetto') and cross-boundary cases (e.g., 'altro bambino')
'''

'''
Pattern 1: Word-internal intervocalic b/g
Example: "abito" -> finds 'b' between 'a' and 'i'
r'[aeiouàèéìòù][bg][aeiouàèéìòù]'
'''

'''
Pattern 2: Cross-boundary intervocalic b/g
vowel + space(s) + [b or g] + vowel (across word boundary)
r'[aeiouàèéìòù]\s+[bg][aeiouàèéìòù]
'''

#-----IMPORTS-----
from pathlib import Path
import re
import json
from datetime import datetime

#-----CONFIG-----
TXT_DIR = Path ("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/transcriptions_abstract")
OUTPUT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/transcriptions_abstract/OUTPUT_DIR")
OUTPUT_FILE = OUTPUT_DIR / "intervocalic_bg.json"

#-----PARSE TIMESTAMPS-----
def parse_timestamped_line(line):
    """
    Parse a line line: [00:15.2 - 00:18.7] Ciao come va?
    Return: (start_time, end_time, text) or (None, None, None) if not matched
    """
    pattern_time = r'\[(\d{2}:\d{2}\.\d) - (\d{2}:\d{2}\.\d)] (.+)'
    match = re.match(pattern_time, line)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None

#-----FIND INTERVOCALIC B/G-----
def find_intervocalic_bg(text):
    # Vowels included
    vowels = r'[aeiouàèéìòù]'
    
    results = []
    text_lower = text.lower()
    
    # Pattern 1: Word-internal intervocalic
    pattern_internal = vowels + r'[bg]' + vowels
    
    for match in re.finditer(pattern_internal, text_lower):
        matched_text = match.group(0) #ex: "abi"
        letter = matched_text[1] #"b" or "g"
        position = match.start()
        
        # Get surrounding context
        context_start = max(0, position - 20)
        context_end = min(len(text), position + 23)
        context = text[context_start:context_end]
        
        results.append({
            'letter': letter,
            'trigram': matched_text,
            'type': 'internal',
            'position': position,
            'context': context.strip()
        })
        
    # Pattern 2: Cross-boundart intervocalic
    pattern_boundary = vowels + r'\s+[bg]' + vowels
    
    for match in re.finditer(pattern_boundary, text_lower):
        matched_text = match.group(0)
        letter = None
        for char in matched_text:
            if char in 'bg':
                letter = char
                break
            
        position = match.start()
        
    # Surrounding context
    context_start = max(0, position - 20)
    context_end = min(len(text), position + 23)
    context = text[context_start:context_end]
    
    results.append({
        'letter': letter,
        'trigram': matched_text,
        'type': 'boundary',
        'position': position,
        'context': context.strip()
    })
    
    return results

#-----LOAD EXISTING DATA-----
def load_existing_occurrences(json_file):
    if not json_file.exists():
        return [], set()
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data =json.load(f)
            occurrences = data.get('occurrences', [])
            processed_files = set(data.get('processed_files', []))
            return occurrences, processed_files
    except Exception as e:
        print(f"Warning: Could not read existing JSON: {e}")
        return [], set()

#-----MAIN FUNCTION-----
def main():
    print(f"Looking for txt files in: {TXT_DIR}")
    print(f"Searching for intervocalic 'b' and 'g'...\n")
    
    # Loading existing results
    all_occurrences, already_processed = load_existing_occurrences(OUTPUT_FILE)

    if already_processed:
        print(f"\nFound existing results file with {len(already_processed)} already processed files:")    
        for filename in sorted(already_processed):
            print(f"✅ {filename}")
        print(f"\nThese files will be skipped.\n")
        
    if all_occurrences:
        print(f"Loaded {len(all_occurrences)} existing occurrences from previous run.\n")
        
    # Find all txt files
    txt_files =sorted(TXT_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} txt files total\n")
    
    # Filter out already processed files
    files_to_process = [f for f in txt_files if f.name not in already_processed]
    
    if not files_to_process:
        print("All files have already been processed! Yay.")
        print(f"If you want to reprocess, delete or rename: {OUTPUT_FILE}")
        return
    
    print(f"Will process {len(files_to_process)} new files:\n")
    
    # Process each txt file
    for i,txt_file in enumerate(files_to_process, 1):
        print(f"[{i}/{len(files_to_process)}] Processing: {txt_file.name}")
        
        try:
            lines = txt_file.read_text(encoding='utf-8').splitlines()
            file_count = 0
            
            for line in lines:
                start_time, end_time, text = parse_timestamped_line(line)
                
                if text: #so it's successfully parsed
                    bg_results = find_intervocalic_bg(text)
                    
                    if bg_results:
                        for result in bg_results:
                            all_occurrences.append({
                                'filename': txt_file.name,
                                'start': start_time,
                                'end': end_time,
                                'letter': result['letter'],
                                'trigram': result['trigram'],
                                'type': result['type'],
                                'context': result['context']
                            })
                            file_count += 1
                            
            print(f" -> Found {file_count} occurrences")
            already_processed.add(txt_file.name)
        
        except Exception as e:
            print(f"Error processing {txt_file.name}: {e}")
            
    # Calculate statistics
    total = len(all_occurrences)
    internal_count = sum(1 for occ in all_occurrences if occ['type'] == 'internal')
    boundary_count = sum(1 for occ in all_occurrences if occ['type'] == 'boundary')
    b_count = sum(1 for occ in all_occurrences if occ['letter'] == 'b')
    g_count = sum(1 for occ in all_occurrences if occ['letter'] == 'g')
    
    # PRINT SUMMARY
    print("\n" + "=" * 60)
    print("SUMMARY of Intervocalic 'b' and 'g'")
    print("=" * 60)
    print(f"Total files in results: {len(already_processed)}")
    print(f"  - Previously processed: {len(already_processed) - len(files_to_process)}")
    print(f"  - Newly processed: {len(files_to_process)}")
    print(f"\nTotal occurrences: {total}")
    print(f"  - Word-internal: {internal_count}")
    print(f"  - Cross-boundary: {boundary_count}")
    
    # JSON output
    output_data = {
        'total_occurrences': total,
        'internal_occurrences': internal_count,
        'boundary_occurrences': boundary_count,
        'b_occurrences': b_count,
        'g_occurrences': g_count,
        'processed_files': sorted(already_processed),
        'occurrences': sorted(all_occurrences, key=lambda x: (x['filename'], x['start']))
    }
    
    #Output dir if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"\nResults saved to: {OUTPUT_FILE}")
    
    if files_to_process:
        print(f"\nN.B.: Next time you run this script, these {len(files_to_process)} files will be skipped.")
        print(f"To reprocess them, delete or rename: {OUTPUT_FILE}")
        
if __name__ == "__main__":
    main()
    
    
    
