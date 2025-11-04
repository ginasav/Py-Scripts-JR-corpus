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
TXT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/transcriptions_abstract")
OUTPUT_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio/Abstract AVIS/transcriptions_abstract/OUTPUT_DIR")
OUTPUT_FILE = OUTPUT_DIR / "diphthongs_occurrences.json"

#-----PARSE TIMESTAMPS-----
def parse_timestamped_line(line):
    pattern = r'\[(\d{2}:\d{2}\.\d) - (\d{2}:\d{2}\.\d)] (.+)'
    match = re.match(pattern, line)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None