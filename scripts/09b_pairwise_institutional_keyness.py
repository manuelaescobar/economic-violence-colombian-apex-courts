"""Diferenciación institucional pareada entre las tres altas cortes.

Motivación (auditoría 2026-09-22): `09_institutional_analysis.py` solo computa
Corte Constitucional vs (Corte Suprema + Consejo de Estado) agrupadas, y solo reporta la cola
POSITIVA (los 15 términos que la CC sobre-utiliza). El manuscrito, sin embargo, afirma que la
jurisdicción ordinaria "remains anchored in procedural and property-dissolution language" —
una afirmación sobre los términos característicos de CSJ/CE que nunca se calculó.

Este script computa los tres contrastes pareados con bootstrap a nivel documento, reportando
AMBAS colas de cada contraste, de modo que la diferenciación institucional quede sustentada
en evidencia simétrica y no solo desde el punto de vista de la CC.
"""
import json
import os

import numpy as np
import pandas as pd
import nltk
from sklearn.feature_extraction.text import CountVectorizer

ALPHA = 0.5
B = 1000
TOP_N = 12
MIN_DF = 5
SEED = 42

spanish_stops = set(nltk.corpus.stopwords.words("spanish"))
custom_stops = {
    'artículo', 'numeral', 'ley', 'decreto', 'resolución', 'fecha', 'bogotá', 'd.c.',
    'corte', 'constitucional', 'suprema', 'justicia', 'consejo', 'estado', 'sala',
    'juez', 'juzgado', 'magistrado', 'ponente', 'expediente', 'demandante', 'demandado',
    'accionante', 'accionado', 'sentencia', 'auto', 'caso'
}
ALL_STOPS = spanish_stops.union(custom_stops)

COURTS = {
    "CC": "Corte Constitucional",
    "CSJ": "Corte Suprema de Justicia",
    "CE": "Consejo de Estado",
}


def monroe_log_odds(k1, n1, k2, n2, n_terms, alpha=ALPHA):
    """Monroe et al. (2008) weighted log-odds with uninformative Dirichlet prior."""
    y1 = k1 + alpha
    y2 = k2 + alpha
    n1_adj = n1 + alpha * n_terms
    n2_adj = n2 + alpha * n_terms
    log_odds = np.log(y1 / (n1_adj - y1)) - np.log(y2 / (n2_adj - y2))
    variance = 1.0 / y1 + 1.0 / y2
    return log_odds, log_odds / np.sqrt(variance)


def build_dtm():
    df_sents = pd.read_parquet("data/master_sentences.parquet")
    df_econ = df_sents[df_sents["is_econ_broad"]]
    doc_texts = (
        df_econ.groupby(["document_id", "court"])
        .agg(doc_text=("sentence_text", lambda x: " ".join(x)))
        .reset_index()
    )
    vec = CountVectorizer(
        ngram_range=(1, 2), min_df=MIN_DF, stop_words=list(ALL_STOPS),
        token_pattern=r'(?u)\b[a-zA-ZáéíóúñÁÉÍÓÚÑ_]{3,}\b',
    )
    dtm = vec.fit_transform(doc_texts["doc_text"]).toarray()
    return doc_texts, dtm, np.array(vec.get_feature_names_out())


def contrast(name_a, name_b, mat_a, mat_b, features, rng):
    n_terms = mat_a.shape[1]
    lo_full, z_full = monroe_log_odds(
        mat_a.sum(axis=0), mat_a.sum(), mat_b.sum(axis=0), mat_b.sum(), n_terms
    )
    df_a = (mat_a > 0).sum(axis=0)
    df_b = (mat_b > 0).sum(axis=0)

    # Candidatos: término presente en >= MIN_DF documentos del grupo donde predomina
    cand_a = np.where((df_a >= MIN_DF) & (z_full > 0))[0]
    cand_b = np.where((df_b >= MIN_DF) & (z_full < 0))[0]
    top_a = cand_a[np.argsort(-z_full[cand_a])][:TOP_N]
    top_b = cand_b[np.argsort(z_full[cand_b])][:TOP_N]
    sel = np.concatenate([top_a, top_b])

    boot = np.zeros((B, len(sel)))
    n_a, n_b = mat_a.shape[0], mat_b.shape[0]
    for i in range(B):
        ia = rng.integers(0, n_a, n_a)
        ib = rng.integers(0, n_b, n_b)
        sa, sb = mat_a[ia], mat_b[ib]
        lo_b, _ = monroe_log_odds(
            sa[:, sel].sum(axis=0), sa.sum(), sb[:, sel].sum(axis=0), sb.sum(), n_terms
        )
        boot[i] = lo_b

    rows = []
    for j, ix in enumerate(sel):
        ci_l, ci_h = np.percentile(boot[:, j], [2.5, 97.5])
        rows.append({
            "contrast": f"{name_a}_vs_{name_b}",
            "favors": name_a if z_full[ix] > 0 else name_b,
            "term": features[ix],
            "doc_freq_a": int(df_a[ix]),
            "doc_freq_b": int(df_b[ix]),
            "log_odds": round(float(lo_full[ix]), 4),
            "z_score": round(float(z_full[ix]), 3),
            "boot_ci_low": round(float(ci_l), 4),
            "boot_ci_high": round(float(ci_h), 4),
            "ci_excludes_zero": bool(ci_l > 0 or ci_h < 0),
        })
    return rows


def main():
    print("=== [09b] Diferenciación institucional pareada (ambas colas, bootstrap documental) ===")
    doc_texts, dtm, features = build_dtm()
    rng = np.random.default_rng(SEED)

    mats = {}
    for code, full_name in COURTS.items():
        mask = (doc_texts["court"] == full_name).values
        mats[code] = dtm[mask]
        print(f"  {code:4} ({full_name:26}): {mask.sum():3d} documentos, {dtm[mask].sum():,} tokens")

    all_rows = []
    for a, b in [("CC", "CSJ"), ("CC", "CE"), ("CSJ", "CE")]:
        if mats[a].shape[0] < 2 or mats[b].shape[0] < 2:
            print(f"\n[!] Contraste {a} vs {b} omitido: documentos insuficientes.")
            continue
        print(f"\n--- {a} vs {b} ---")
        rows = contrast(a, b, mats[a], mats[b], features, rng)
        all_rows.extend(rows)
        for side in (a, b):
            sub = [r for r in rows if r["favors"] == side]
            robust = [r for r in sub if r["ci_excludes_zero"]]
            print(f"  Distintivos de {side}: {len(robust)}/{len(sub)} con IC que excluye 0")
            for r in sub[:6]:
                flag = "*" if r["ci_excludes_zero"] else " "
                print(f"   {flag} {r['term']:22} Z={r['z_score']:8.3f}  "
                      f"CI=[{r['boot_ci_low']:.3f}, {r['boot_ci_high']:.3f}]")

    out = pd.DataFrame(all_rows)
    os.makedirs("outputs/tables", exist_ok=True)
    out.to_csv("outputs/tables/table_institutional_pairwise_keyness.csv", index=False)
    with open("outputs/statistics/institutional_pairwise_keyness.json", "w", encoding="utf-8") as fh:
        json.dump(all_rows, fh, ensure_ascii=False, indent=2)

    print("\nResumen de robustez por contraste:")
    for c, grp in out.groupby("contrast"):
        print(f"  {c:12} {int(grp['ci_excludes_zero'].sum()):2d}/{len(grp):2d} términos robustos")
    print("\nGuardado en outputs/tables/table_institutional_pairwise_keyness.csv")


if __name__ == "__main__":
    main()
