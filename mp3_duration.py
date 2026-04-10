#!/usr/bin/env python3
"""
Measure the duration of all MP3 files in a directory. It requires mutagen.

Pass the folder path as an argument when running the script in the terminal. If no folder is specified, it will use the current directory. Use the -r or --recursive flag to include subfolders.
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
    
#Convert seconds to hours, minutes, and seconds
def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

#Measuring mp3 duration
def measure_mp3_duration(folder: str, recursive: bool = False) -> None:
    folder_path = Path(folder)
    
    if not folder_path.is_dir():
        print(f"Error: '{folder}' is not a valid directory.")
        return
    
    #Find mp3 files
    pattern = "**/*.mp3" if recursive else "*.mp3"
    mp3_files = sorted(folder_path.glob(pattern))
    
    if not mp3_files:
        print(f"No MP3 files found in '{folder}'.")
        return
    
    print(f"\n{'File':<50} {'Duration':>10}")
    print("-" * 62)
    
    total_seconds = 0.0
    errors = []
    
    for mp3_path in mp3_files:
        try:
            audio = MP3(mp3_path)
            duration = audio.info.length
            total_seconds += duration
            # Path relative to the folder
            rel_path = mp3_path.relative_to(folder_path)
            print(f"{str(rel_path):<50} {format_duration(duration):>10}")
        except Exception as e:
            errors.append((mp3_path.name, str(e)))
            print(f"{mp3_path.name:<50} {'Error':>10}")
            
    print("-" * 62)
    print(f"{'Total - ' + str(len(mp3_files)) + ' file(s)':<50} {format_duration(total_seconds):>10}")
    print()
    
    if errors:
        print("Files that could not be read:")
        for name, msg in errors:
            print(f"  {name}: {msg}")
            
#MAIN
def main():
    parser = argparse.ArgumentParser(
        description="Measure the duration of MP3 files in a directory."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Path to the folder containing MP3 files (default: current directory)."
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Search subfolders recursively."
    )
    args = parser.parse_args()
    
    measure_mp3_duration(args.folder, args.recursive)
    
if __name__ == "__main__":
    main()