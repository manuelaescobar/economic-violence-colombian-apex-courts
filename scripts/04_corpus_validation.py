import os
import re
import pandas as pd
import numpy as np

OUTPUT_DATA_DIR = "outputs/data"

def split_and_validate_sentences():
    print("=== [04_corpus_validation.py] Segmentación Oracional y Construcción de Dataset Maestro ===")
    df_docs = pd.read_parquet("data/master_documents.parquet")
    
    # Regex split on sentence boundaries
    sentence_split_regex = re.compile(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ"“])')
    
    # Gender relevance filter
    gender_kw = re.compile(r'\b(mujer(?:es)?|g[eé]nero|v[ií]ctima(?:s)?|acoso|feminicidio|femicidio|agresi[oó]n|maltrato|equidad|discriminaci[oó]n)\b', re.IGNORECASE)
    
    sentences_records = []
    
    for _, doc in df_docs.iterrows():
        doc_id = doc["document_id"]
        court = doc["court"]
        court_conf = doc["court_confidence"]
        year = doc["decision_year"]
        date = doc["decision_date"]
        date_conf = doc["date_confidence"]
        doc_type = doc["document_type"]
        fpath = doc["filepath"]
        
        with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
            
        raw_sents = sentence_split_regex.split(text)
        
        sent_pos = 0
        for s in raw_sents:
            s_clean = " ".join(s.strip().split())
            if len(s_clean) >= 25: # minimum valid sentence length
                is_gender = bool(gender_kw.search(s_clean))
                sent_id = f"{doc_id}_S{sent_pos:05d}"
                
                sentences_records.append({
                    "document_id": doc_id,
                    "sentence_id": sent_id,
                    "sentence_position": sent_pos,
                    "sentence_text": s_clean,
                    "char_length": len(s_clean),
                    "word_length": len(s_clean.split()),
                    "is_gender_relevant": is_gender,
                    "court": court,
                    "court_confidence": court_conf,
                    "decision_year": year,
                    "decision_date": date,
                    "date_confidence": date_conf,
                    "document_type": doc_type
                })
                sent_pos += 1

    df_sentences = pd.DataFrame(sentences_records)
    print(f"Total oraciones extraídas de documentos únicos: {len(df_sentences):,}")
    print(f"Oraciones con contenido de género/VBG: {df_sentences['is_gender_relevant'].sum():,} ({df_sentences['is_gender_relevant'].mean()*100:.2f}%)")
    
    df_sentences.to_parquet("data/master_sentences.parquet", index=False)
    print("Dataset maestro de oraciones guardado en 'data/master_sentences.parquet'")
    return df_sentences

if __name__ == "__main__":
    split_and_validate_sentences()
