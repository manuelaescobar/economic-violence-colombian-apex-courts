import os
import re
import yaml
import pandas as pd
import numpy as np

def detect_economic_violence():
    print("=== [05_economic_violence_detection.py] Operacionalización y Detección Multidefinición ===")
    
    with open("config/economic_violence_lexicon.yml", "r", encoding="utf-8") as fh:
        lexicon = yaml.safe_load(fh)
        
    df_sents = pd.read_parquet("data/master_sentences.parquet")
    print(f"Cargadas {len(df_sents):,} oraciones maestras.")
    
    # Compile regexes
    strict_patterns = [re.compile(item["pattern"], re.IGNORECASE) for item in lexicon["strict"]["patterns"]]
    mod_terms = [re.compile(p, re.IGNORECASE) for p in lexicon["moderate"]["co_occurrence_terms"]]
    mod_gender = [re.compile(p, re.IGNORECASE) for p in lexicon["moderate"]["required_gender_context"]]
    broad_patterns = [re.compile(p, re.IGNORECASE) for p in lexicon["broad"]["patterns"]]
    exclusions = [re.compile(re.escape(p), re.IGNORECASE) for p in lexicon["exclusions_false_positives"]["patterns"]]
    
    def evaluate_sentence(text, is_gender):
        # Check exclusion
        for exc in exclusions:
            if exc.search(text):
                return False, False, False
                
        # 1. STRICT
        is_strict = False
        for sp in strict_patterns:
            if sp.search(text):
                is_strict = True
                break
                
        # 2. MODERATE
        is_moderate = is_strict # strict is subset of moderate
        if not is_moderate:
            has_mod_term = any(mt.search(text) for mt in mod_terms)
            has_mod_gender = is_gender or any(mg.search(text) for mg in mod_gender)
            if has_mod_term and has_mod_gender:
                is_moderate = True
                
        # 3. BROAD
        is_broad = is_moderate # moderate is subset of broad
        if not is_broad and is_gender:
            has_broad_term = any(bp.search(text) for bp in broad_patterns)
            if has_broad_term:
                is_broad = True
                
        return is_strict, is_moderate, is_broad

    strict_flags = []
    moderate_flags = []
    broad_flags = []
    
    for _, row in df_sents.iterrows():
        s_text = row["sentence_text"]
        is_g = row["is_gender_relevant"]
        s_flag, m_flag, b_flag = evaluate_sentence(s_text, is_g)
        strict_flags.append(s_flag)
        moderate_flags.append(m_flag)
        broad_flags.append(b_flag)
        
    df_sents["is_econ_strict"] = strict_flags
    df_sents["is_econ_moderate"] = moderate_flags
    df_sents["is_econ_broad"] = broad_flags
    
    print("\n--- Resultados de Clasificación Oracional ---")
    print(f"STRICT:   {df_sents['is_econ_strict'].sum():,} oraciones ({df_sents['is_econ_strict'].mean()*100:.3f}%)")
    print(f"MODERATE: {df_sents['is_econ_moderate'].sum():,} oraciones ({df_sents['is_econ_moderate'].mean()*100:.3f}%)")
    print(f"BROAD:    {df_sents['is_econ_broad'].sum():,} oraciones ({df_sents['is_econ_broad'].mean()*100:.3f}%)")
    
    # Save enriched sentences
    df_sents.to_parquet("data/master_sentences.parquet", index=False)
    
    # Aggregate to document level
    doc_agg = df_sents.groupby("document_id").agg(
        total_sentences=("sentence_id", "count"),
        gender_sentences=("is_gender_relevant", "sum"),
        econ_strict_sentences=("is_econ_strict", "sum"),
        econ_moderate_sentences=("is_econ_moderate", "sum"),
        econ_broad_sentences=("is_econ_broad", "sum")
    ).reset_index()
    
    doc_agg["has_gender"] = doc_agg["gender_sentences"] > 0
    doc_agg["has_econ_strict"] = doc_agg["econ_strict_sentences"] > 0
    doc_agg["has_econ_moderate"] = doc_agg["econ_moderate_sentences"] > 0
    doc_agg["has_econ_broad"] = doc_agg["econ_broad_sentences"] > 0
    
    df_docs = pd.read_parquet("data/master_documents.parquet")
    df_docs = df_docs.merge(doc_agg, on="document_id", how="left")
    df_docs.to_parquet("data/master_documents.parquet", index=False)
    
    print("\n--- Resultados de Clasificación Documental ---")
    print(f"Documentos con mención de Género/VBG: {df_docs['has_gender'].sum():,} / {len(df_docs):,} ({df_docs['has_gender'].mean()*100:.1f}%)")
    print(f"Documentos con STRICT Econ Violence:   {df_docs['has_econ_strict'].sum():,} ({df_docs['has_econ_strict'].mean()*100:.2f}%)")
    print(f"Documentos con MODERATE Econ Violence: {df_docs['has_econ_moderate'].sum():,} ({df_docs['has_econ_moderate'].mean()*100:.2f}%)")
    print(f"Documentos con BROAD Econ Violence:    {df_docs['has_econ_broad'].sum():,} ({df_docs['has_econ_broad'].mean()*100:.2f}%)")
    
    return df_sents, df_docs

if __name__ == "__main__":
    detect_economic_violence()
