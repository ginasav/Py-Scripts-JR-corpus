"""
Script per copiare i file mp3 corrispondenti ai filename presenti nel CSV,
suddividendoli in due cartelle in base al valore della colonna 'istruzione':
  - 'laureato'      -> OUTPUT_LAUREATI
  - 'non-laureato'  -> OUTPUT_NON_LAUREATI

Funzionamento:
- Legge il CSV ed estrae (filename, istruzione)
- Sostituisce l'estensione con .mp3
- Cerca ricorsivamente i file in INPUT_FOLDER (incluse subdirectory)
- Copia i file nella cartella di output corretta (senza duplicati)
- Stampa un report finale di file copiati / mancanti
"""

import csv
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote

# ============================================================
# CONFIG
# ============================================================
CSV_PATH = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/df_professione_istruzione_filtered.csv")
INPUT_FOLDER = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/JR_audio")
OUTPUT_LAUREATI = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/audio/laureato")
OUTPUT_NON_LAUREATI = Path("/Users/ginasaviano/Documents/Gent/PhD Materials/Nuovo paper_Gina/audio/non-laureato")

# Se True, decodifica i caratteri URL-encoded nei filename (es. %E2%80%99 -> ')
DECODE_URL_ENCODED = True
# ============================================================

# Mapping valore di 'istruzione' -> cartella di destinazione
DESTINAZIONI = {
    "laureato": OUTPUT_LAUREATI,
    "non-laureato": OUTPUT_NON_LAUREATI,
}


def estrai_attesi(csv_path: Path) -> dict[Path, set[str]]:
    """
    Legge il CSV e ritorna un dict {cartella_destinazione: {nomi_mp3...}}.
    Gestisce eventuali righe duplicate tramite set.
    Aggiunge anche la versione URL-decoded del nome (se diversa), così lo
    script può trovare il file sia se sul disco ha il nome codificato sia
    se ha quello "vero".
    """
    attesi: dict[Path, set[str]] = {dest: set() for dest in DESTINAZIONI.values()}
    skippati_istruzione_sconosciuta = 0

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for col in ("filename", "istruzione"):
            if col not in reader.fieldnames:
                sys.exit(f"ERRORE: colonna '{col}' non trovata. Colonne: {reader.fieldnames}")

        for row in reader:
            nome = (row["filename"] or "").strip()
            istruzione = (row["istruzione"] or "").strip().lower()
            if not nome:
                continue

            destinazione = DESTINAZIONI.get(istruzione)
            if destinazione is None:
                skippati_istruzione_sconosciuta += 1
                continue

            nome_mp3 = Path(nome).stem + ".mp3"
            attesi[destinazione].add(nome_mp3)
            if DECODE_URL_ENCODED:
                decoded = unquote(nome_mp3)
                if decoded != nome_mp3:
                    attesi[destinazione].add(decoded)

    if skippati_istruzione_sconosciuta:
        print(f"NOTA: {skippati_istruzione_sconosciuta} righe saltate "
              f"(valore 'istruzione' diverso da 'laureato'/'non-laureato').")

    return attesi


def indicizza_mp3_disponibili(input_folder: Path) -> dict[str, Path]:
    """
    Indicizza tutti i file .mp3 sotto input_folder (ricorsivamente).
    Ritorna un dict {nome_file: primo_path_trovato}.
    """
    indice: dict[str, Path] = {}
    duplicati_su_disco = 0
    for path in input_folder.rglob("*.mp3"):
        if path.is_file():
            if path.name in indice:
                duplicati_su_disco += 1
            else:
                indice[path.name] = path
    if duplicati_su_disco:
        print(f"NOTA: trovati {duplicati_su_disco} file mp3 con nomi duplicati "
              f"in subdirectory diverse — copiata solo la prima occorrenza.")
    return indice


def copia_gruppo(nomi: set[str], destinazione: Path,
                 indice_disco: dict[str, Path], etichetta: str) -> None:
    """Copia i file di un gruppo nella cartella di destinazione e stampa il report."""
    destinazione.mkdir(parents=True, exist_ok=True)

    copiati: list[str] = []
    gia_presenti: list[str] = []
    mancanti: list[str] = []
    nomi_gia_copiati: set[str] = set()  # evita di copiare due varianti dello stesso file

    for nome in sorted(nomi):
        # Se la versione decoded di questo nome è già stata copiata, salta
        chiave_canonica = unquote(nome)
        if chiave_canonica in nomi_gia_copiati:
            continue

        sorgente = indice_disco.get(nome)
        if sorgente is None:
            # Prova anche con la versione decodificata, nel caso il disco abbia quella
            sorgente = indice_disco.get(chiave_canonica)
        if sorgente is None:
            mancanti.append(nome)
            continue

        dest_file = destinazione / sorgente.name
        if dest_file.exists():
            gia_presenti.append(sorgente.name)
            nomi_gia_copiati.add(chiave_canonica)
            continue

        shutil.copy2(sorgente, dest_file)
        copiati.append(sorgente.name)
        nomi_gia_copiati.add(chiave_canonica)

    print(f"\n[{etichetta}] -> {destinazione}")
    print(f"  Copiati:      {len(copiati)}")
    print(f"  Già presenti: {len(gia_presenti)} (saltati, output non sovrascritto)")
    print(f"  Mancanti:     {len(mancanti)}")
    if mancanti:
        print(f"  Elenco mancanti:")
        for m in mancanti:
            print(f"    - {m}")


def main() -> None:
    if not CSV_PATH.is_file():
        sys.exit(f"ERRORE: CSV non trovato: {CSV_PATH}")
    if not INPUT_FOLDER.is_dir():
        sys.exit(f"ERRORE: INPUT_FOLDER non esiste o non è una directory: {INPUT_FOLDER}")

    print(f"CSV:    {CSV_PATH}")
    print(f"INPUT:  {INPUT_FOLDER}")
    print(f"OUT laureati:     {OUTPUT_LAUREATI}")
    print(f"OUT non-laureati: {OUTPUT_NON_LAUREATI}")
    print("-" * 60)

    # 1) Estrai i nomi attesi dal CSV, raggruppati per destinazione
    attesi = estrai_attesi(CSV_PATH)
    for dest, nomi in attesi.items():
        print(f"Attesi per {dest.name}: {len(nomi)} nomi (incluse varianti URL-decoded)")

    # 2) Indicizza i file .mp3 disponibili
    print("\nIndicizzazione dei file .mp3 in INPUT_FOLDER (ricorsiva)...")
    indice_disco = indicizza_mp3_disponibili(INPUT_FOLDER)
    print(f"File .mp3 unici trovati su disco: {len(indice_disco)}")

    # 3) Copia per gruppo
    copia_gruppo(attesi[OUTPUT_LAUREATI], OUTPUT_LAUREATI,
                 indice_disco, "LAUREATI")
    copia_gruppo(attesi[OUTPUT_NON_LAUREATI], OUTPUT_NON_LAUREATI,
                 indice_disco, "NON-LAUREATI")


if __name__ == "__main__":
    main()