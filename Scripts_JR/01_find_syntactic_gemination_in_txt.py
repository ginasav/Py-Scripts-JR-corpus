"""
This script looks for syntactic gemination in text files. It reads the text files, identifies instances of syntactic gemination, and outputs the results to a new file, with their relative timestamps and context.
"""

#-----IMPORTS-----
import re
from pathlib import Path
import json

#-----CONSTANTS-----
# Words that trigger Raddoppiamento Fonosintattico
TRIGGER_WORDS = {
    # Verbs (monosyllabic)
    "do", "sto", "fa", "so",
    # Pronouns
    "tu", "me", "te", "che", "chi",
    # Prepositions
    "a", "tra", "fra", "su",
    # Conjunctions
    "e", "o", "ma", "se", "ne",
    # Relatives / indefinites
    "ogni", "qualche", "dove",
    # Numerals
    "tre",
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
def find_rf_candidates():
    """Find potential RF candidates in the parsed transcription. Returns a list of occurrence dicts."""
    


#-----TEST ZONE-----
# Test 1: JSON doesn't exist
test_path = Path("non_existent_file.json")
result = load_existing_results(test_path)
print("empty stucture", result)
#what I should expect: {"total_occurrences": 0, "processed_files": [], "occurrences": []}

# Test 2: JSON exists and is valid
test_path = Path("true_json_test.json")
with open(test_path, "w", encoding="utf-8") as f:
    json.dump({"total_occurrences": 5, "processed_files": ["file1.txt"], "occurrences": [{"file": "file1.txt", "start": "00:00.0", "end": "00:05.0", "text": "example text"}]}, f)
result = load_existing_results(test_path)
print("loaded data", result)

# Test 3: Json corrupted
test_path = Path("corrupted_test.json")
with open(test_path, "w", encoding="utf-8") as f:
    f.write("{ this is not valid JSON }")
try:
    result = load_existing_results(test_path)
except json.JSONDecodeError:
    print("Caught JSONDecodeError as expected for corrupted file.")
    
# Clean up the json test file
Path("true_json_test.json").unlink()
Path("corrupted_test.json").unlink()