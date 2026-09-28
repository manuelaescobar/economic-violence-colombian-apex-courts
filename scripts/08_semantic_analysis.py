import os
import re
import json
import pandas as pd
import numpy as np
from gensim.models import Word2Vec
import nltk
from nltk.corpus import stopwords

# Ensure stopwords
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

spanish_stops = set(stopwords.words('spanish'))
custom_stops = {
    'entonces', 'aquí', 'así', 'pues', 'ser', 'él', 'cómo', 'creer', 'como', 'haber',
    'tema', 'poder', 'tener', 'ir', 'decir', 'hacer', 'cosa', 'ahí', 'ver', 'si', 'año',
    'artículo', 'numeral', 'ley', 'decreto', 'resolución', 'fecha', 'bogotá', 'd.c.',
    'corte', 'constitucional', 'suprema', 'justicia', 'consejo', 'estado', 'sala',
    'juez', 'juzgado', 'magistrado', 'ponente', 'expediente', 'demandante', 'demandado',
    'accionante', 'accionado', 'sentencia', 'auto', 'caso'
}
all_stops = spanish_stops.union(custom_stops)

def tokenize_corpus(sentences):
    tokenized = []
    for text in sentences:
        text_mod = re.sub(r'violencia\s+económica', 'violencia_economica', text, flags=re.IGNORECASE)
        text_mod = re.sub(r'violencia\s+patrimonial', 'violencia_patrimonial', text_mod, flags=re.IGNORECASE)
        text_mod = re.sub(r'dependencia\s+económica', 'dependencia_economica', text_mod, flags=re.IGNORECASE)
        text_mod = re.sub(r'cuota\s+alimentaria', 'cuota_alimentaria', text_mod, flags=re.IGNORECASE)
        tokens = re.findall(r'\b[a-zA-ZáéíóúñÁÉÍÓÚÑ_]{3,}\b', text_mod.lower())
        valid = [t for t in tokens if t not in all_stops]
        if len(valid) > 2:
            tokenized.append(valid)
    return tokenized

def perform_semantic_analysis():
    print("=== [08_semantic_analysis.py] Análisis Semántico con Word2Vec Multi-Seed y Concordancias ===")
    df_sents = pd.read_parquet("data/master_sentences.parquet")
    
    # Train on moderate corpus (validated semantic ground)
    df_econ = df_sents[df_sents["is_econ_moderate"]].copy()
    print(f"Oraciones en sub-corpus semántico: {len(df_econ):,}")
    
    tokenized_docs = tokenize_corpus(df_econ["sentence_text"])
    
    seeds = [1, 7, 21, 42, 100]
    target_terms = ['violencia_economica', 'patrimonio', 'dependencia', 'violencia_patrimonial']
    
    multi_seed_results = {term: {} for term in target_terms}
    
    for seed in seeds:
        # Strictly workers=1 for reproducibility across runs
        w2v = Word2Vec(
            sentences=tokenized_docs,
            vector_size=150,
            window=5,
            min_count=3,
            workers=1,
            sg=1,
            epochs=20,
            seed=seed
        )
        
        for term in target_terms:
            if term in w2v.wv:
                sims = w2v.wv.most_similar(term, topn=10)
                multi_seed_results[term][seed] = sims
            else:
                multi_seed_results[term][seed] = []
                
    # Calculate stability metrics (Jaccard@10 across seeds and Mean Cosine Sim)
    stability_summary = {}
    
    for term in target_terms:
        all_top_words = []
        jaccard_pairs = []
        seed_list = list(multi_seed_results[term].keys())
        
        for s in seed_list:
            words = [w for w, score in multi_seed_results[term][s]]
            if words:
                all_top_words.append(set(words))
                
        if len(all_top_words) > 1:
            for i in range(len(all_top_words)):
                for j in range(i+1, len(all_top_words)):
                    s1 = all_top_words[i]
                    s2 = all_top_words[j]
                    jacc = len(s1.intersection(s2)) / len(s1.union(s2)) if len(s1.union(s2)) > 0 else 0
                    jaccard_pairs.append(jacc)
                    
            mean_jaccard = float(np.mean(jaccard_pairs))
        else:
            mean_jaccard = 0.0
            
        # Aggregate consensus neighbors
        word_counts = {}
        word_sims = {}
        for s in seed_list:
            for w, score in multi_seed_results[term][s]:
                word_counts[w] = word_counts.get(w, 0) + 1
                word_sims[w] = word_sims.get(w, []) + [score]
                
        consensus_neighbors = []
        for w, cnt in sorted(word_counts.items(), key=lambda x: (x[1], np.mean(word_sims[x[0]])), reverse=True)[:10]:
            consensus_neighbors.append({
                "term": w,
                "seed_agreement": f"{cnt}/{len(seeds)}",
                "mean_cosine_similarity": round(float(np.mean(word_sims[w])), 4),
                "std_cosine_similarity": round(float(np.std(word_sims[w])), 4)
            })
            
        stability_summary[term] = {
            "mean_jaccard_at_10": round(mean_jaccard, 4),
            "stability_status": "STABLE" if mean_jaccard >= 0.60 else ("MODERATELY_STABLE" if mean_jaccard >= 0.40 else "UNSTABLE"),
            "consensus_neighbors": consensus_neighbors
        }
        
        print(f"\n--- Estabilidad de Vecinos para '{term}' ---")
        print(f"Jaccard@10 promedio entre semillas: {mean_jaccard:.4f} ({stability_summary[term]['stability_status']})")
        print("Top 5 vecinos de consenso:")
        for n in consensus_neighbors[:5]:
            print(f"  * {n['term']:<25} | Similitud: {n['mean_cosine_similarity']:.4f} (Acuerdo: {n['seed_agreement']})")

    with open("outputs/statistics/word2vec_stability_report.json", "w", encoding="utf-8") as fh:
        json.dump(stability_summary, fh, ensure_ascii=False, indent=2)
        
    # 2. Concordance Analysis (KWIC) for Target Terms
    kwic_terms = ['violencia_economica', 'viena', 'cairo', 'femicidio', 'patrimonio', 'dependencia']
    concordance_records = []
    
    for _, row in df_sents[df_sents["is_gender_relevant"]].iterrows():
        text = row["sentence_text"]
        text_lower = text.lower()
        for kt in kwic_terms:
            pattern = r'\b' + kt.replace('_', r'\s+') + r'\b'
            m = re.search(pattern, text_lower)
            if m:
                start = max(0, m.start() - 80)
                end = min(len(text), m.end() + 80)
                concordance_records.append({
                    "target_term": kt,
                    "document_id": row["document_id"],
                    "court": row["court"],
                    "decision_year": row["decision_year"],
                    "sentence_id": row["sentence_id"],
                    "context_before": text[start:m.start()].strip(),
                    "matched_token": text[m.start():m.end()],
                    "context_after": text[m.end():end].strip(),
                    "full_sentence": text
                })
                
    df_kwic = pd.DataFrame(concordance_records)
    print(f"\nTotal concordancias contextuales extraídas: {len(df_kwic):,}")
    print(df_kwic["target_term"].value_counts())
    
    df_kwic.to_parquet("outputs/data/concordance_kwic_table.parquet", index=False)
    df_kwic.to_csv("outputs/tables/table_concordance_samples.csv", index=False)
    
    return stability_summary, df_kwic

if __name__ == "__main__":
    perform_semantic_analysis()
