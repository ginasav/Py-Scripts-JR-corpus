#------------------------------------------
# transcrive_txt.py
#------------------------------------------
# This script takes a audio file and prints its content to a txt file.

import os
from pathlib import Path
from faster_whisper import WhisperModel

# --------- CONFIG ---------
AUDIO_DIR = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio")  # <--- CAMBIA QUI
LANGUAGE = "it"
ASR_MODEL_SIZE = "medium"

print("Looking in:", AUDIO_DIR.resolve()) #trying to debug path issue

# --------- ASR MODEL (CPU) ---------
try:
    asr_model = WhisperModel(ASR_MODEL_SIZE, device="cpu", compute_type="int8", cpu_threads=8)
except ValueError:
    asr_model = WhisperModel(ASR_MODEL_SIZE, device="cpu", compute_type="float32", cpu_threads=8)
    
print(f"Whisper model loaded: {ASR_MODEL_SIZE} on CPU")

# TIMESTAMP FORMATTING
def format_timestamp(seconds):
    """Convert seconds to MM:SS.S format"""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:04.1f}"

#SAVE TRANSCRIPTION TO TXT
def save_transcription_to_txt(segments, output_path):
    """Save transcription segments to a txt file with timestamps"""
    with open(output_path, "w", encoding="utf-8") as f:
        for seg in segments:
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = seg["text"].strip()
            f.write(f"[{start} - {end}] {text}\n")

# ------------------------------------------------
def main():
    audio_exts = {".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wma", ".alac"}
    files = sorted(p for p in AUDIO_DIR.glob("*") if p.suffix.lower() in audio_exts)
                   
    if not files:
        raise SystemExit(f"Nessun file trovato in {AUDIO_DIR}")
    
    # Create a directory for transcription
    transcriptions_dir = AUDIO_DIR / "transcriptions"
    transcriptions_dir.mkdir(exist_ok=True)
    
    print(f"Trovati {len(files)} file audio to process\n")
    print(f"Output directory: {transcriptions_dir}\n")
    
    for i, audio_path in enumerate(files, 1):
        try:
            print(f"[{i}/{len(files)}] Processing: {audio_path.name}")
            
            #Transcribe audio
            seg_gen, info = asr_model.transcribe(
                str(audio_path),
                language=LANGUAGE,
                vad_filter=True
            )
            
            #Convert Whisper segments to list of dicts
            segments = [
                {
                    "start": float(s.start),
                    "end": float(s.end),
                    "text": s.text
                }
                for s in seg_gen
            ]
            
            #Save to txt file
            output_txt = transcriptions_dir / f"{audio_path.stem}.txt"
            save_transcription_to_txt(segments, output_txt)
            
            print (f" ✅ Trascrizione salvata in: {output_txt.name} ({len(segments)} segmenti)")
        
        except Exception as e:
            print(f" ❌ Errore durante la trascrizione di {audio_path.name}: {e}")
            
if __name__ == "__main__":
    main()