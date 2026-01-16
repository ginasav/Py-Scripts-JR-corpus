#------------------------------
# i_grafica.py
#------------------------------
'''
This script looks for "pronuncia della <i> grafica" pattern - c+i+vowel - separating words that have this pattern inside them and at the beginning position. Examples: "cielo", "società".

Also sc+i+vowel like "scienza"
'''
#-------IMPORTS-------
from pathlib import Path
import re
import json

#-------CONFIG-------
TXT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/Ampliamento parlanti 20260116/transcriptions")
OUTPUT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/Ampliamento parlanti 20260116/transcriptions/OUTPUT_DIR")
OUTPUT_FILE = OUTPUT_DIR / "i_grafica_occurrences_ampliamento_20260116.json"

#-------FUNC to parse time-------
def parse_timestamped_line(line):
    pattern = r'\[(\d{2}:\d{2}\.\d) - (\d{2}:\d{2}\.\d)] (.+)'
    match = re.match(pattern, line)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None

#-------FUNC to find i grafica-------
def find_i_grafica(text):
    text_lower = text.lower()
    results = []
    
    # Pattern 1:ci+vowel
    #all words containing ci+vowel
    ci_word_pattern = r'\b\w*ci[aeiou]\w*\b'
    
    for word_match in re.finditer(ci_word_pattern, text_lower):
        word = word_match.group(0)
        
        #find WHERE it occurs
        ci_pattern = r'ci[aeiou]'
        
        for ci_match in re.finditer(ci_pattern, word):
            ci_position = ci_match.start()
            pattern_found = ci_match.group(0)
            
            #EXLUCE 'CCI' AND 'SCI'
            if ci_position > 0:
                preciding_char = word[ci_position - 1]
                if preciding_char in ['c', 's']:
                    continue #skip!
                
            #Determine position (initial vs internal)
            is_initial = (ci_position == 0)
            position = 'initial' if is_initial else 'internal'
            
            results.append((word, pattern_found, position, 'ci'))
            
    # Pattern 2: sci+vowel
    sci_word_pattern = r'\b\w*sci[aeiou]\w*\b'
    
    for word_match in re.finditer(sci_word_pattern, text_lower):
        word = word_match.group(0)
        
        #Find where tha pattern occurs
        sci_pattern = r'sci[aeiou]'
        
        for sci_match in re.finditer(sci_pattern, word):
            sci_position = sci_match.start()
            pattern_found = sci_match.group(0)
            
            #Determine position (initial vs internal)
            is_initial = (sci_position == 0)
            position = 'initial' if is_initial else 'internal'
            
            results.append((word, pattern_found, position, 'sci'))
            
    return results

#-------LOAD EXISTING DATA-------
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
    
#-------MAIN-------
def main():
    print(f"Looking for txt files in: {TXT_DIR}")
    print(f"Searching for patterns: ci+vowel and sci+vowel\n")
    
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
                    results = find_i_grafica(text)
                    
                    if results:
                        for word, pattern_found, position, pattern_type in results:
                            all_occurrences.append({
                                'filename': txt_file.name,
                                'start': start_time,
                                'end': end_time,
                                'word': word,
                                'pattern': pattern_found,
                                'position': position,
                                'type': pattern_type,
                                'context': text.strip()
                            })
                            file_count += 1
                            
            print(f" -> Found {file_count} occurrences")
            already_processed.add(txt_file.name)
        
        except Exception as e:
            print(f"Error processing {txt_file.name}: {e}")
            
    #-------SEPARATE OCCURRENCES BY TYPE AND POSITION-------
    # CI pattern
    ci_initial = [occ for occ in all_occurrences if occ['type'] == 'ci' and occ['position'] == 'initial']
    ci_internal = [occ for occ in all_occurrences if occ['type'] == 'ci' and occ['position'] == 'internal']
    
    # SCI pattern
    sci_initial = [occ for occ in all_occurrences if occ['type'] == 'sci' and occ['position'] == 'initial']
    sci_internal = [occ for occ in all_occurrences if occ['type'] == 'sci' and occ['position'] == 'internal']
    
    #-----JSON OUTPUT-------
    output_data = {
        'total occurrences': len(all_occurrences),
        'processed_files': sorted(already_processed),
        'ci_vowel': {
            'total': len(ci_initial) + len(ci_internal),
            'initial_forms': len(ci_initial),
            'internal_forms': len(ci_internal),
            'occurrences_initial': sorted(ci_initial, key=lambda x: (x['filename'], x['start'])),
            'occurrences_internal': sorted(ci_internal, key=lambda x: (x['filename'], x['start']))
        },
        'sci_vowel': {
            'total': len(sci_initial) + len(sci_internal),
            'initial_forms': len(sci_initial),
            'internal_forms': len(sci_internal),
            'occurrences_initial': sorted(sci_initial, key=lambda x: (x['filename'], x['start'])),
            'occurrences_internal': sorted(sci_internal, key=lambda x: (x['filename'], x['start']))
        }
    }
    
    #Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n✅ Results saved to: {OUTPUT_FILE}")
    
    
if __name__ == "__main__":
    main()

    
    