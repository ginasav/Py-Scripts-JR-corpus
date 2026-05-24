"""
This script looks for syntactic gemination in text files. It reads the text files, identifies instances of syntactic gemination, and outputs the results to a new file, with their relative timestamps and context.
"""

#-----IMPORTS-----
import re
from pathlib import Path
import json

#-----CONFIG-----
INPUT_FOLDER = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/trascrizioni_audio/laureato") #CHANGE HERE - txt files
OUTPUT_FOLDER = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/OUTPUT scripts") #CHANGE HERE - results folder
OUTPUT_JSON = OUTPUT_FOLDER / "syntactic_gemination_results_laureato.json"
CONTEXT_WINDOW = 3 # how many words before and after the trigger to include in the context snippet

#-----CONSTANTS-----
# Words that trigger Raddoppiamento Fonosintattico
TRIGGER_WORDS = {
    # Verbs (monosyllabic)
    "do", "sto", "so", "sa", "è", "fu", "ho",
    # Pronouns
    "tu", "me", "te", "che", "chi",
    # Prepositions
    "a", "tra", "fra", "su",
    # Conjunctions
    "e", "se", "ne",
    # Relatives / indefinites
    "ogni", "qualche", "dove",
    # Others
    "tre", "re", "blue"
}


#-----FUNCTIONS-----

# Function that loads existing results from a file
def load_existing_results(json_path):
    """
    Load existing results from JSON if it exists. Return a fresh empty structure if it doesn't. Stop loudly if the file is corrupted.
    """
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"Loaded existing results from {json_path}")
            return data
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {json_path}. The file may be corrupted.")
            raise
    else:
        return {
            "total_occurrences": 0,
            "processed_files": [],
            "occurrences": []
        }
    

# Function to parse the transcription files
def parse_transcription_file(filepath):
    """
    Read a transcription file and returna list of (start, end, text) tuples. Skips empty lines and lines that do not match the expected format.
    """
    pattern = re.compile(r"\[(\d{2}:\d{2}\.\d) - (\d{2}:\d{2}\.\d)\] (.*)")
    parsed_lines = []
    
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            if not line: # skip empty lines
                continue
            
            match = pattern.match(line)
            if match:
                start, end, text = match.groups()
                parsed_lines.append((start, end, text))
            else:
                # Line didn't match the expected format, log it
                print(f"  Warning: Skipped line in {filepath.name}: {line[:50]}")
                
    return parsed_lines

# Function to normalize text
def normalize_word(word):
    """
    Clean up a word so it can be safely compared against the trigger list:
    - lowercase it
    - remove leading/trailing punctuation
    - normalize né/nè/ne variants
    """
    word = word.lower().strip(".,!?;:\"()[]{}")
    if word in ["né", "nè", "ne"]:
        return "ne"
    return word

# Function to check the starting consonant
def starts_with_valid_consonant(word):
    """
    Return True if the word could be a target of RF:
    - it must start with a consonant
    - but with s + C clusters excluded
    
    Assumes that the input is already normalized
    """
    vowels = "aeiou"
    
    if not word:
        return False
    if len(word) == 1:
        return False
    if word[0] in vowels or word[0] == "h":
        return False
    if word.startswith("s") and len(word) > 1 and word[1] not in vowels:
        return False
    
    return True

# Function that find the RF candidates
def find_rf_candidates(parsed_lines, trigger_set, filename):
    """Find potential RF candidates in the parsed transcription. Returns a list of occurrence dicts."""
    # STEP 1: Flatten all lines into one sequence of (word, start, end) tuples
    words_with_timestamps = []
    for start, end, text in parsed_lines:
        for w in text.split():
            words_with_timestamps.append((w, start, end))
            
    occurrences = []
    
    # STEP 2: Walk through the words, looking at each (trigger, next_word) pair
    for i in range(len(words_with_timestamps) - 1):
        word, start, end = words_with_timestamps[i]
        next_word, next_start, next_end = words_with_timestamps[i + 1]
        
        # STEP 3: Normalize the words for comparison
        norm_word = normalize_word(word)
        norm_next = normalize_word(next_word)
        
        # STEP 4: Is this a trigger?
        if norm_word not in trigger_set:
            continue
        
        # STEP 5: Does the next word start with a valid consonant?
        if not starts_with_valid_consonant(norm_next):
            continue
        
        # STEP 6: Build context (up to 3 words begore + trigger + up to 3 after)
        context_start = max(0, i - CONTEXT_WINDOW)
        context_end = min(len(words_with_timestamps), i + CONTEXT_WINDOW + 1)
        context_words = [w for w, _, _ in words_with_timestamps[context_start:context_end]]
        context = " ".join(context_words)
        
        # STEP 7: Record the occurrence
        occurrences.append({
            "filename": filename,
            "start": start,
            "end": next_end,
            "trigger_word": word,
            "following_word": next_word,
            "context": context
        })
    
    return occurrences

# Function to save results to JSON
def save_results(data, json_path):
    """
    Save the results data to a JSON file. Pretty-printed with UTF-8 characters preserved.
    """
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Saved results to {json_path}")
    
#-----MAIN-----
def main():
    #debug
    print(f"DEBUG: INPUT_FOLDER  = {INPUT_FOLDER}")
    print(f"DEBUG: OUTPUT_FOLDER = {OUTPUT_FOLDER}")
    print(f"DEBUG: OUTPUT_JSON   = {OUTPUT_JSON}")
    print(f"DEBUG: OUTPUT_JSON.absolute() = {OUTPUT_JSON.absolute()}")
    print(f"DEBUG: OUTPUT_FOLDER.exists() = {OUTPUT_FOLDER.exists()}")
    
    # before starting, make sure the output folder exists
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # 1. Load existing results
    results = load_existing_results(OUTPUT_JSON)
    processed_set = set(results["processed_files"])
    
    # 2. Lis all .txt files in the input folder
    txt_files = sorted(INPUT_FOLDER.glob("*.txt"))
    print(f"Found {len(txt_files)} .txt files in {INPUT_FOLDER}")
    
    # 3. Process only files not already done
    new_files = [f for f in txt_files if f.name not in processed_set]
    print(f"{len(new_files)} new file to process.\n") 
    
    if not new_files:
        print("Nothing new to process. Exiting.")
        return
    
    for filepath in new_files:
        print(f"Processing: {filepath.name}")
        
        # 3a. Parse
        parsed = parse_transcription_file(filepath)
        
        # 3b. Find candidates
        candidates = find_rf_candidates(parsed, TRIGGER_WORDS, filepath.name)
        print(f"  -> {len(candidates)} candidate(s) found.")
        
        # 3c. Append to results
        results["occurrences"].extend(candidates)
        results["processed_files"].append(filepath.name)
        
        #3d. Update total
        results["total_occurrences"] = len(results["occurrences"])
        
        #4. Save!!!
        save_results(results, OUTPUT_JSON)
        
    # to be sure...
    print(f"\n✅ Done! Total occurrences: {results['totaloccurrences']}")


if __name__ == "__main__":
    main()

#-----TEST ZONE-----
