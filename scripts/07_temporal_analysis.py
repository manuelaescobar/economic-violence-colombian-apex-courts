import os
import json
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.stattools import durbin_watson
from scipy.stats import fisher_exact

def perform_temporal_analysis():
    print("=== [07_temporal_analysis.py] Análisis Temporal Descriptivo e Inferencial (ITS & Placebos) ===")
    df_docs = pd.read_parquet("data/master_documents.parquet")
    
    # Filter documents with valid decision year (1992-2024)
    df_valid = df_docs[df_docs["decision_year"].between(1992, 2024)].copy()
    print(f"Documentos con año de decisión válido (1992–2024): {len(df_valid):,} / {len(df_docs):,}")
    
    # Aggregate by decision_year
    yearly = df_valid.groupby("decision_year").agg(
        total_docs=("document_id", "count"),
        gender_docs=("has_gender", "sum"),
        econ_strict_docs=("has_econ_strict", "sum"),
        econ_moderate_docs=("has_econ_moderate", "sum"),
        econ_broad_docs=("has_econ_broad", "sum"),
        total_sentences=("total_sentences", "sum"),
        gender_sentences=("gender_sentences", "sum"),
        econ_strict_sents=("econ_strict_sentences", "sum"),
        econ_moderate_sents=("econ_moderate_sentences", "sum"),
        econ_broad_sents=("econ_broad_sentences", "sum")
    ).reset_index()
    
    # Rates per 1,000 sentences & Document Prevalence
    yearly["prev_strict_doc"] = yearly["econ_strict_docs"] / yearly["total_docs"]
    yearly["prev_mod_doc"] = yearly["econ_moderate_docs"] / yearly["total_docs"]
    yearly["rate_strict_sent_per_1k"] = (yearly["econ_strict_sents"] / yearly["total_sentences"]) * 1000
    yearly["rate_mod_sent_per_1k"] = (yearly["econ_moderate_sents"] / yearly["total_sentences"]) * 1000
    yearly["rate_broad_sent_per_1k"] = (yearly["econ_broad_sents"] / yearly["total_sentences"]) * 1000
    
    yearly.to_parquet("outputs/data/yearly_temporal_series.parquet", index=False)
    yearly.to_csv("outputs/tables/table_temporal_series.csv", index=False)

    # 1b. Descriptive pre/post-2008 document-level prevalence (Fisher's exact test)
    # Reported as the primary pre/post comparison: with only 16 pre-2008 documents in the
    # Apex-Courts-only corpus, the ITS decomposition below is unreliable for sparse/zero-count
    # tiers (see STRICT below) and is reported as exploratory, not primary.
    pre_docs = df_valid[df_valid["decision_year"] <= 2008]
    post_docs = df_valid[df_valid["decision_year"] > 2008]
    descriptive_prepost = {}
    for tier_name, tier_col in [("STRICT", "has_econ_strict"), ("MODERATE", "has_econ_moderate"), ("BROAD", "has_econ_broad")]:
        pre_n = int(pre_docs[tier_col].sum())
        pre_total = len(pre_docs)
        post_n = int(post_docs[tier_col].sum())
        post_total = len(post_docs)
        table = [[pre_n, pre_total - pre_n], [post_n, post_total - post_n]]
        odds_ratio, p_value = fisher_exact(table)
        descriptive_prepost[tier_name] = {
            "pre_2008_docs_with_tier": pre_n,
            "pre_2008_docs_total": pre_total,
            "pre_2008_prevalence_pct": round(100 * pre_n / pre_total, 2) if pre_total else None,
            "post_2008_docs_with_tier": post_n,
            "post_2008_docs_total": post_total,
            "post_2008_prevalence_pct": round(100 * post_n / post_total, 2) if post_total else None,
            "fisher_odds_ratio": round(float(odds_ratio), 4) if np.isfinite(odds_ratio) else None,
            "fisher_p_value": round(float(p_value), 4)
        }
        print(f"\n--- Prevalencia documental pre/post-2008 ({tier_name}, Fisher exacto) ---")
        print(f"Pre-2008: {pre_n}/{pre_total} ({descriptive_prepost[tier_name]['pre_2008_prevalence_pct']}%) | "
              f"Post-2008: {post_n}/{post_total} ({descriptive_prepost[tier_name]['post_2008_prevalence_pct']}%) | "
              f"p = {p_value:.4f}")

    with open("outputs/statistics/descriptive_prepost_2008.json", "w", encoding="utf-8") as fh:
        json.dump(descriptive_prepost, fh, ensure_ascii=False, indent=2)

    # 2. Interrupted Time Series (ITS) for Law 1257 of 2008
    # Variables:
    # time: 0, 1, 2...
    # post_2008: 1 if year > 2008 else 0
    # time_after_2008: (year - 2008) * post_2008
    
    yearly["time"] = yearly["decision_year"] - yearly["decision_year"].min()
    yearly["post_2008"] = (yearly["decision_year"] > 2008).astype(int)
    yearly["time_after_2008"] = np.maximum(0, yearly["decision_year"] - 2008) * yearly["post_2008"]
    
    # Fit Negative Binomial ITS with log(total_sentences) offset
    results_its = {}
    
    for outcome_name, outcome_col in [("STRICT", "econ_strict_sents"), ("MODERATE", "econ_moderate_sents"), ("BROAD", "econ_broad_sents")]:
        formula = f"{outcome_col} ~ time + post_2008 + time_after_2008"
        
        # Check overdispersion: Poisson vs Negative Binomial
        poisson_mod = smf.glm(
            formula=formula,
            data=yearly,
            family=sm.families.Poisson(),
            offset=np.log(yearly["total_sentences"] + 1)
        ).fit()
        
        # Calculate Pearson dispersion
        dispersion = poisson_mod.pearson_chi2 / poisson_mod.df_resid
        
        # Fit Negative Binomial (or robust GLM)
        nb_mod = smf.glm(
            formula=formula,
            data=yearly,
            family=sm.families.NegativeBinomial(alpha=1.0),
            offset=np.log(yearly["total_sentences"] + 1)
        ).fit(cov_type='HC1') # Robust sandwich SE
        
        # Durbin-Watson on residuals
        dw = durbin_watson(nb_mod.resid_response)
        
        # Incident Rate Ratios (IRR)
        params = nb_mod.params
        conf = nb_mod.conf_int()
        irr = np.exp(params)
        irr_low = np.exp(conf[0])
        irr_high = np.exp(conf[1])
        pvals = nb_mod.pvalues
        
        results_its[outcome_name] = {
            "dispersion_pearson": round(float(dispersion), 3),
            "durbin_watson": round(float(dw), 3),
            "intercept": {"coef": round(float(params["Intercept"]), 4), "p": round(float(pvals["Intercept"]), 4)},
            "pre_trend_time": {
                "coef": round(float(params["time"]), 4),
                "irr": round(float(irr["time"]), 4),
                "ci_95": [round(float(irr_low["time"]), 4), round(float(irr_high["time"]), 4)],
                "p_value": round(float(pvals["time"]), 4)
            },
            "level_change_post_2008": {
                "coef": round(float(params["post_2008"]), 4),
                "irr": round(float(irr["post_2008"]), 4),
                "ci_95": [round(float(irr_low["post_2008"]), 4), round(float(irr_high["post_2008"]), 4)],
                "p_value": round(float(pvals["post_2008"]), 4)
            },
            "slope_change_time_after_2008": {
                "coef": round(float(params["time_after_2008"]), 4),
                "irr": round(float(irr["time_after_2008"]), 4),
                "ci_95": [round(float(irr_low["time_after_2008"]), 4), round(float(irr_high["time_after_2008"]), 4)],
                "p_value": round(float(pvals["time_after_2008"]), 4)
            }
        }
        
        print(f"\n--- Modelo ITS ({outcome_name}) ---")
        print(f"Sobredispersión: {dispersion:.2f} | Durbin-Watson: {dw:.2f}")
        print(f"Cambio de Nivel (post_2008): IRR = {irr['post_2008']:.4f} (p = {pvals['post_2008']:.4f})")
        print(f"Cambio de Pendiente (time_after_2008): IRR = {irr['time_after_2008']:.4f} (p = {pvals['time_after_2008']:.4f})")

    # 3. Placebo Inflexion Tests (2005, 2006, 2007, 2009, 2010, 2011)
    # Run on econ_moderate_sents (not econ_strict_sents): with only 16 pre-2008 documents and
    # ZERO econ_strict_sents in every year before 2008, the STRICT NB-GLM does not identify a
    # pre-trend (pre_trend_time IRR order 1e+3 with CI up to 1e+194 in results_its["STRICT"]),
    # and placebo tests on that tier return NaN p-values / degenerate IRRs. MODERATE is the tier
    # that actually converges and is used for all inferential (ITS + placebo) claims; STRICT is
    # reported descriptively only (see descriptive_prepost_2008.json).
    placebo_target_col = "econ_moderate_sents"
    placebos = [2005, 2006, 2007, 2009, 2010, 2011]
    placebo_results = {}

    for pyr in placebos:
        df_p = yearly.copy()
        df_p["post_p"] = (df_p["decision_year"] > pyr).astype(int)
        df_p["time_p"] = np.maximum(0, df_p["decision_year"] - pyr) * df_p["post_p"]

        try:
            m_p = smf.glm(
                formula=f"{placebo_target_col} ~ time + post_p + time_p",
                data=df_p,
                family=sm.families.NegativeBinomial(alpha=1.0),
                offset=np.log(df_p["total_sentences"] + 1)
            ).fit(cov_type='HC1')
            
            placebo_results[str(pyr)] = {
                "level_p": round(float(m_p.pvalues.get("post_p", 1.0)), 4),
                "level_irr": round(float(np.exp(m_p.params.get("post_p", 0.0))), 4),
                "slope_p": round(float(m_p.pvalues.get("time_p", 1.0)), 4),
                "slope_irr": round(float(np.exp(m_p.params.get("time_p", 0.0))), 4)
            }
        except Exception as e:
            placebo_results[str(pyr)] = {"error": str(e)}
            
    with open("outputs/statistics/its_models_results.json", "w", encoding="utf-8") as fh:
        json.dump(results_its, fh, ensure_ascii=False, indent=2)
        
    with open("outputs/statistics/placebo_tests_results.json", "w", encoding="utf-8") as fh:
        json.dump({"outcome_variable": placebo_target_col, "results": placebo_results}, fh, ensure_ascii=False, indent=2)
        
    print("\nAnálisis temporal e inferencial completado exitosamente.")
    return yearly, results_its, placebo_results

if __name__ == "__main__":
    perform_temporal_analysis()
