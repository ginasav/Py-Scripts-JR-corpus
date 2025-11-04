

import os
import re
from pathlib import Path
import torch
from faster_whisper import WhisperModel
import whisperx
from praatio import textgrid as tg

# --------- CONFIG ---------
AUDIO_DIR = Path("/Users/ginasaviano/Documents/Gent/JR_audio")  # <--- CAMBIA QUI
LANGUAGE = "it"
ASR_MODEL_SIZE = "medium"
EPS = 1e-3
MIN_DUR = 1e-4

print("Looking in:", AUDIO_DIR.resolve()) #trying to debug path issue


# --------- DEVICE ---------    
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
ALIGN_DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"ALIGN device: {ALIGN_DEVICE} (ASR: faster-whisper su CPU)")

# --------- ASR MODEL (CPU) ---------
try:
    asr_model = WhisperModel(ASR_MODEL_SIZE, device="cpu", compute_type="int8", cpu_threads=8)
except ValueError:
    asr_model = WhisperModel(ASR_MODEL_SIZE, device="cpu", compute_type="float32", cpu_threads=8)

# --------- ALIGN MODEL ---------
align_model, align_meta = whisperx.load_align_model(language_code=LANGUAGE, device=ALIGN_DEVICE)


try:
    import epitran
    epi = epitran.Epitran("ita-Latn")
    def g2p_words(words):
        outs = []
        for w in words:
            phon_str = epi.transliterate(w or "")

            tokens = [ch for ch in phon_str if not ch.isspace()]
            outs.append(tokens)
        return outs
    G2P_OK = True
    print("[G2P] Epitran attivo (ita-Latn)")
except Exception as e:
    print(f"[G2P] Epitran non disponibile ({e}); il tier g2p_lex verrà omesso.")
    G2P_OK = False
    def g2p_words(words):  # fallback vuoto
        return [[] for _ in words]

# --------- UTIL ---------
_word_re = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ’']+", re.UNICODE)
def normalize_word(w: str) -> str:
    w = (w or "").strip().lower().replace("’", "'")
    m = _word_re.findall(w)
    return "".join(m) if m else ""

def iter_word_phones_safe(word_dict):
    phones = word_dict.get("phones") or []
    out = []
    for it in phones:
        if isinstance(it, dict):
            lab = str(it.get("phone") or "").strip(); dur = it.get("duration")
        else:
            lab = str(it).strip(); dur = None
        if lab: out.append((lab, dur))
    return out

def fix_overlaps(entries, max_end=None, eps=EPS, min_dur=MIN_DUR):
    if not entries: return []
    entries = sorted(entries, key=lambda x: (float(x[0]), float(x[1])))
    fixed = []
    for s, e, lab in entries:
        s = float(s); e = float(e)
        if max_end is not None:
            s = max(0.0, min(s, max_end)); e = max(0.0, min(e, max_end))
        if e <= s + min_dur/10: continue
        if not fixed:
            fixed.append([s, e, lab]); continue
        ps, pe, pl = fixed[-1]
        if s < pe - eps:
            new_pe = max(ps, min(s, pe))
            if new_pe - ps >= min_dur: fixed[-1][1] = new_pe
            else: fixed.pop()
        if fixed:
            ps, pe, pl = fixed[-1]
            s = max(s, pe)
        if e - s >= min_dur: fixed.append([s, e, lab])
    fixed = [(float(s), float(e), lab) for s, e, lab in fixed]
    if max_end is not None:
        fixed = [(s, min(e, max_end), lab) for (s,e,lab) in fixed if min(e, max_end)-s >= min_dur]
    return fixed

# --------- TEXTGRID ---------
def to_textgrid(aligned, out_path: Path):
    words, phones, g2p = [], [], []
    max_end = 0.0

    for seg in aligned.get("segments", []):
        for w in seg.get("words", []):
            lab = (w.get("word") or "").strip()
            ws, we = w.get("start"), w.get("end")
            if ws is None or we is None or we <= ws: continue
            ws, we = float(ws), float(we)
            words.append((ws, we, lab)); max_end = max(max_end, we)


            plist = iter_word_phones_safe(w)
            if plist:
                any_dur = any(d is not None for _, d in plist)
                t = ws
                if any_dur:
                    total = sum((d or 0.0) for _, d in plist) or (we-ws)
                    scale = (we-ws)/total if total>0 else 0.0
                    for ph, d in plist:
                        dur = ((d or 0.0)*scale) if total>0 else (we-ws)/len(plist)
                        ps, pe = t, min(we, t+dur)
                        if pe>ps+MIN_DUR/10: phones.append((ps, pe, ph))
                        t = pe
                else:
                    step = (we-ws)/len(plist)
                    for ph,_ in plist:
                        ps, pe = t, min(we, t+step)
                        if pe>ps+MIN_DUR/10: phones.append((ps, pe, ph))
                        t = pe
                if phones and phones[-1][1] < we:
                    ps, _, labp = phones[-1]; phones[-1] = (ps, we, labp)

            # g2p lessicale (Epitran)
            base = normalize_word(lab)
            if base and G2P_OK:
                g_list = g2p_words([base])[0]  # lista di simboli IPA
                if g_list:
                    step = (we - ws) / len(g_list)
                    t = ws
                    for ph in g_list:
                        ps, pe = t, min(we, t + step)
                        if pe > ps + MIN_DUR/10: g2p.append((ps, pe, ph))
                        t = pe
                    if g2p and g2p[-1][1] < we:
                        ps, _, labg = g2p[-1]; g2p[-1] = (ps, we, labg)

    # fix overlap
    words = fix_overlaps(words, max_end)
    phones = fix_overlaps(phones, max_end)
    g2p = fix_overlaps(g2p, max_end)

    tg_obj = tg.Textgrid()
    tg_obj.addTier(tg.IntervalTier("words",  words, 0, max_end))
    tg_obj.addTier(tg.IntervalTier("phones", phones, 0, max_end))
    tg_obj.addTier(tg.IntervalTier("g2p_lex", g2p, 0, max_end))
    tg_obj.save(str(out_path), format="short_textgrid", includeBlankSpaces=True)



def main():
    audio_exts = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
    files = sorted(p for p in AUDIO_DIR.glob("*") if p.suffix.lower() in audio_exts)
    if not files:
        raise SystemExit(f"Nessun file audio in {AUDIO_DIR}")


    for ap in files:
        try:
            print(f"\n[ASR] {ap.name}")
            seg_gen, info = asr_model.transcribe(str(ap), language=LANGUAGE, vad_filter=True)
            segments = [{"start": float(s.start), "end": float(s.end), "text": s.text} for s in seg_gen]
            print("[ALIGN] parola+fono…")
            aligned = whisperx.align(segments, align_model, align_meta, str(ap), ALIGN_DEVICE)
            to_textgrid(aligned, ap.with_suffix(".TextGrid"))
        except Exception as e:
            print(f"[ERR] {ap.name}: {e}")



if __name__ == "__main__":
    main()
