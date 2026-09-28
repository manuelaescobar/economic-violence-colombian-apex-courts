import os
import glob
import hashlib
import json
import re
import pandas as pd
import yaml

with open("config.yaml", "r", encoding="utf-8") as fh:
    config = yaml.safe_load(fh)

RAW_DIR = config["corpus"]["raw_dir"]
MIN_SIZE = config["corpus"]["min_file_size_bytes"]
OUTPUT_DATA_DIR = "outputs/data"
os.makedirs(OUTPUT_DATA_DIR, exist_ok=True)

def ingest_corpus():
    print("=== [01_ingestion.py] Ingesta y Validación Forense Inicial del Corpus ===")
    all_files = sorted(glob.glob(os.path.join(RAW_DIR, "*.txt")))
    print(f"Total archivos detectados en '{RAW_DIR}': {len(all_files):,}")
    
    records = []
    for fpath in all_files:
        fname = os.path.basename(fpath)
        size = os.path.getsize(fpath)
        
        if size < MIN_SIZE:
            continue
            
        with open(fpath, "rb") as fh:
            raw_bytes = fh.read()
            
        md5_hash = hashlib.md5(raw_bytes).hexdigest()
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
        
        try:
            text = raw_bytes.decode("utf-8")
            enc = "utf-8"
        except UnicodeDecodeError:
            text = raw_bytes.decode("latin-1", errors="replace")
            enc = "latin-1_fallback"
            
        char_count = len(text)
        word_count = len(text.split())
        
        records.append({
            "raw_filename": fname,
            "filepath": fpath,
            "size_bytes": size,
            "char_count": char_count,
            "word_count": word_count,
            "md5": md5_hash,
            "sha256": sha256_hash,
            "encoding": enc
        })
        
    df_raw = pd.DataFrame(records)
    print(f"Archivos no vacíos procesados válidamente: {len(df_raw):,}")
    print(f"MD5 únicos identificados: {df_raw['md5'].nunique():,}")
    
    out_path = os.path.join(OUTPUT_DATA_DIR, "raw_ingested_files.parquet")
    df_raw.to_parquet(out_path, index=False)
    print(f"Dataset de ingesta guardado en '{out_path}'")
    return df_raw

if __name__ == "__main__":
    ingest_corpus()
