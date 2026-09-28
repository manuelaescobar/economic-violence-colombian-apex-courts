import os
import re
import json
import pandas as pd
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.corpus import stopwords

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

def calculate_log_odds_ratio(k1, n1, k2, n2, alpha=0.5, n_terms_override=None):
    # Monroe et al. (2008) weighted log-odds with informative/uninformative prior.
    # n_terms_override: vocabulary size for the prior normalization. Required when k1 is a
    # subset of the vocabulary (e.g. bootstrapping only the top terms), since len(k1) would
    # otherwise shrink the prior mass and change the estimand.
    n_terms = len(k1) if n_terms_override is None else n_terms_override
    y1 = k1 + alpha
    y2 = k2 + alpha
    n1_adj = n1 + alpha * n_terms
    n2_adj = n2 + alpha * n_terms
    
    odds1 = y1 / (n1_adj - y1)
    odds2 = y2 / (n2_adj - y2)
    
    log_odds = np.log(odds1) - np.log(odds2)
    variance = 1.0 / y1 + 1.0 / y2
    z_score = log_odds / np.sqrt(variance)
    return log_odds, z_score

def perform_institutional_analysis():
    print("=== [09_institutional_analysis.py] Diferenciación Institucional Rigurosa (Keyness & Bootstrap) ===")
    df_docs = pd.read_parquet("data/master_documents.parquet")
    df_sents = pd.read_parquet("data/master_sentences.parquet")
    
    # Analyze across the 3 main high courts:
    # 1. Corte Constitucional
    # 2. Corte Suprema de Justicia
    # 3. Consejo de Estado
    
    # Document-level texts for gender/economic domain
    df_econ_sents = df_sents[df_sents["is_econ_broad"]].copy()
    
    doc_texts = df_econ_sents.groupby(["document_id", "court"]).agg(
        doc_text=("sentence_text", lambda x: " ".join(x))
    ).reset_index()
    
    # Vectorizer
    c_vec = CountVectorizer(
        ngram_range=(1, 2),
        min_df=5, # Term must appear in at least 5 distinct decisions
        stop_words=list(all_stops),
        token_pattern=r'(?u)\b[a-zA-ZáéíóúñÁÉÍÓÚÑ_]{3,}\b'
    )
    
    dtm = c_vec.fit_transform(doc_texts["doc_text"])
    features = np.array(c_vec.get_feature_names_out())
    
    # Term frequencies by court
    courts = ["Corte Constitucional", "Corte Suprema de Justicia", "Consejo de Estado"]
    court_term_counts = {}
    court_total_words = {}
    court_doc_counts = {}
    
    for c in courts:
        mask = (doc_texts["court"] == c).values
        sub_dtm = dtm[mask]
        counts = np.asarray(sub_dtm.sum(axis=0)).flatten()
        court_term_counts[c] = counts
        court_total_words[c] = counts.sum()
        court_doc_counts[c] = mask.sum()
        
    print(f"Palabras analizadas: CC={court_total_words['Corte Constitucional']:,}, CSJ={court_total_words['Corte Suprema de Justicia']:,}, CE={court_total_words['Consejo de Estado']:,}")
    
    # Calculate Keyness for Corte Constitucional vs (CSJ + CE)
    k1 = court_term_counts["Corte Constitucional"]
    n1 = court_total_words["Corte Constitucional"]
    k2 = court_term_counts["Corte Suprema de Justicia"] + court_term_counts["Consejo de Estado"]
    n2 = court_total_words["Corte Suprema de Justicia"] + court_total_words["Consejo de Estado"]
    
    log_odds, z_scores = calculate_log_odds_ratio(k1, n1, k2, n2)
    
    # Document frequency per term in CC
    cc_mask = (doc_texts["court"] == "Corte Constitucional").values
    cc_sub_dtm = dtm[cc_mask]
    doc_freq_cc = np.asarray((cc_sub_dtm > 0).sum(axis=0)).flatten()
    
    keyness_df = pd.DataFrame({
        "term": features,
        "raw_count_cc": k1,
        "raw_count_others": k2,
        "doc_freq_cc": doc_freq_cc,
        "log_odds_ratio": log_odds,
        "z_score_keyness": z_scores
    })
    
    # Filter valid terms with sufficient document spread (doc_freq >= 5)
    keyness_valid = keyness_df[keyness_df["doc_freq_cc"] >= 5].sort_values(by="z_score_keyness", ascending=False).reset_index(drop=True)
    
    # 2. Document-Level Bootstrap for Top Distinctive Terms (1,000 resamples)
    print("\nEjecutando Bootstrap Documental (B=1,000 resamples) para intervalos de confianza...")
    top_terms = keyness_valid.head(15)["term"].tolist()
    top_indices = [np.where(features == t)[0][0] for t in top_terms]
    
    np.random.seed(42)
    B = 1000
    n_docs_cc = cc_mask.sum()
    n_docs_others = (~cc_mask).sum()
    
    # The bootstrap must resample THE SAME statistic that is reported as the point estimate
    # (Monroe weighted log-odds). A previous version resampled the difference in relative
    # frequencies (rate_cc - rate_oth), which is a different quantity on a different scale:
    # the resulting CIs did not even contain their own point estimates.
    cc_dtm_full = dtm[cc_mask].toarray()
    oth_dtm_full = dtm[~cc_mask].toarray()
    n_terms_total = dtm.shape[1]

    boot_diffs = {t: [] for t in top_terms}

    for _ in range(B):
        idx_cc = np.random.choice(n_docs_cc, size=n_docs_cc, replace=True)
        idx_oth = np.random.choice(n_docs_others, size=n_docs_others, replace=True)

        s_cc = cc_dtm_full[idx_cc]
        s_oth = oth_dtm_full[idx_oth]

        lo_b, _ = calculate_log_odds_ratio(
            s_cc[:, top_indices].sum(axis=0), s_cc.sum(),
            s_oth[:, top_indices].sum(axis=0), s_oth.sum(),
            n_terms_override=n_terms_total
        )

        for j, t in enumerate(top_terms):
            boot_diffs[t].append(lo_b[j])
            
    final_institutional = []
    print("\n---> Top 10 Términos Más Distintivos de la Corte Constitucional (Validación Inferencia Bootstrap):")
    print(f"{'Rango':<5} | {'Término':<28} | {'Doc Freq':<8} | {'Log-Odds (Z)':<12} | {'Bootstrap 95% CI'}")
    print("-" * 80)
    
    for rank, row in keyness_valid.head(15).iterrows():
        term = row["term"]
        if term in boot_diffs:
            ci_low = np.percentile(boot_diffs[term], 2.5)
            ci_high = np.percentile(boot_diffs[term], 97.5)
        else:
            ci_low, ci_high = 0.0, 0.0
            
        final_institutional.append({
            "rank": rank + 1,
            "term": term,
            "raw_count_cc": int(row["raw_count_cc"]),
            "doc_freq_cc": int(row["doc_freq_cc"]),
            "z_score_keyness": round(float(row["z_score_keyness"]), 3),
            "log_odds_ratio": round(float(row["log_odds_ratio"]), 4),
            "bootstrap_ci_95": [round(float(ci_low), 6), round(float(ci_high), 6)]
        })
        if rank < 10:
            print(f"{rank+1:<5} | {term:<28} | {row['doc_freq_cc']:<8} | {row['z_score_keyness']:<12.3f} | [{ci_low:.5f}, {ci_high:.5f}]")

    with open("outputs/statistics/institutional_keyness_bootstrap.json", "w", encoding="utf-8") as fh:
        json.dump(final_institutional, fh, ensure_ascii=False, indent=2)
        
    pd.DataFrame(final_institutional).to_csv("outputs/tables/table_institutional_distinctiveness.csv", index=False)
    return final_institutional

if __name__ == "__main__":
    perform_institutional_analysis()
