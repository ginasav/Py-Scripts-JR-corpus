"""
This script looks for syntactic gemination in text files. It reads the text files, identifies instances of syntactic gemination, and outputs the results to a new file, with their relative timestamps and context.
"""

#-----IMPORTS-----
import re
from pathlib import Path


#-----FUNCTIONS-----

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


#-----TEST ZONE-----
test_file = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/trascrizioni_audio/laureato/240923-JR-Naples-0002-marmo-luca.txt")
result = parse_transcription_file(test_file)

print(f"Parsed {len(result)} lines.")
print("\nFirst 3 lines:")
for line in result[:3]:
    print(line)