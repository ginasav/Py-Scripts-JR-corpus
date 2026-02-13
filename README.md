# Py-Scripts-JR-corpus

Python scripts for processing and analysing speech data from the JR corpus, developed as part of a PhD project. The pipeline converts audio recordings into timestamped transcripts and extracts segmental phonetic features for linguistic analysis.

## Overview

This repository provides two main components:

1. **Audio-to-transcript conversion** — Scripts at the root level use [WhisperX](https://github.com/m-bain/whisperX) to transcribe audio files into text with word-level timestamps.
2. **Phonetic feature extraction** — Scripts inside the `Scripts_JR/` folder process the generated transcripts to identify and extract segmental features (e.g. vowel quality, consonant realisations, etc.).

The final output is a structured, explorable **JSON file** containing the extracted phonetic data alongside timestamps, making it easy to navigate and query specific portions of the corpus.

## Repository Structure

```
├── transcrive.py          # Audio → transcript conversion (Whisper)
├── transcrive_txt.py      # Audio → plain text transcript
├── Scripts_JR/            # Phonetic feature extraction scripts
│   └── ...                # Various analysis modules
└── venv-whisperx/         # Virtual environment for WhisperX
```

## Getting Started

### Prerequisites

- Python 3.8+
- [WhisperX](https://github.com/m-bain/whisperX) and its dependencies

### Installation

```bash
git clone https://github.com/ginasav/Py-Scripts-JR-corpus.git
cd Py-Scripts-JR-corpus
pip install -r requirements.txt   # if available
```

### Usage

**1. Transcribe audio files:**

```bash
python transcrive.py
```

**2. Run phonetic analysis on transcripts:**

Navigate to the `Scripts_JR/` folder and run the desired analysis script. The output will be saved as a JSON file with timestamps for each extracted feature.

## Output Format

The analysis pipeline produces a JSON file where each entry includes:

- The identified phonetic feature
- Associated timestamp (start/end)
- Contextual information from the transcript

This format allows for easy filtering, visualisation, and further statistical analysis.

## License

This project is part of an academic PhD research effort. Please contact the author for usage permissions.

## Author

[ginasav](https://github.com/ginasav)
