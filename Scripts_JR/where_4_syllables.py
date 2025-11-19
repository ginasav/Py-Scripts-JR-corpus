#----------------------------
# where_4_syllables.py
#----------------------------
# This script analyzes the syllable_3_4_occurrences.json file
# and tells you which txt files have 4-syllable word occurrences

#----------- IMPORTS -----------
import json
from pathlib import Path

#---------- CONFIG -----------
OUTPUT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/transcriptions_abstract/OUTPUT_DIR")
JSON_FILE = OUTPUT_DIR / "syllable_3_4.json"

#---------- MAIN FUNC ----------
def main():
    print("="*60)
    print("WHERE ARE THE 4-SYLLABLE WORD OCCURRENCES?")
    print("="*60)
    print(f"\nReading JSON file: {JSON_FILE}\n")
    
    # Check if the json file exists
    if not JSON_FILE.exists():
        print(f"Error: File not found!")
        return
    
    # Load the JSON data
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return
    
    # Get all occurrences
    occurrences = data.get('occurrences', [])
    
    if not occurrences:
        print("No occurrences found.")
        return
    
    # Find files with 4-syllable words
    files_with_4_syllables = {}
    
    for occ in occurrences:
        if occ['syllables'] == 4:
            filename = occ['filename']
            word = occ['word']
            
            if filename not in files_with_4_syllables:
                files_with_4_syllables[filename] = []
                
            files_with_4_syllables[filename].append(word)
            
            
    # Print results
    if not files_with_4_syllables:
        print("No files contain 4-syllable word occurrences.")
        return
    
    for filename in sorted(files_with_4_syllables.keys()):
        words = files_with_4_syllables[filename]
        print(f"{filename}")
        print(f" Words: {','.join(words)}\n")

if __name__ == "__main__":
    main()
    
        