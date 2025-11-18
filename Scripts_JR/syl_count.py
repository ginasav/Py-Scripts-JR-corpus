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



