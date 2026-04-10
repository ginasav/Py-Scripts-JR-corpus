#!/usr/bin/env python3
"""
Measure the duration of all MP3 files in a directory. It requires mutagen.
"""

import os
import sys
import argparse
from pathlib import Path

try:
    from mutagen.mp3 import MP3
except ImportError:
    print("This script requires the mutagen library. Install it with 'pip install mutagen'.")
    sys.exit(1)