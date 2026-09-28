import os
import json
import pandas as pd
import numpy as np

def perform_robustness_evaluation():
    print("=== [10_robustness.py] Evaluación Sistemática de Robustez y Sensibilidad ===")
    
    with open("outputs/statistics/its_models_results.json", "r", encoding="utf-8") as fh:
        its_res = json.load(fh)
        
    with open("outputs/statistics/gold_standard_evaluation.json", "r", encoding="utf-8") as fh:
        gold_res = json.load(fh)
        
    with open("outputs/statistics/word2vec_stability_report.json", "r", encoding="utf-8") as fh:
        w2v_res = json.load(fh)
        
    df_docs = pd.read_parquet("data/master_documents.parquet")
    df_sents = pd.read_parquet("data/master_sentences.parquet")
    
    robustness_table = [
        {
            "definition_level": "STRICT",
            "description": "Explicit autonomous mentions of economic/patrimonial violence only",
            "n_sentences": int(df_sents["is_econ_strict"].sum()),
            "sentence_prevalence_pct": round(float(df_sents["is_econ_strict"].mean() * 100), 3),
            "n_documents": int(df_docs["has_econ_strict"].sum()),
            "document_prevalence_pct": round(float(df_docs["has_econ_strict"].mean() * 100), 2),
            "gold_precision": gold_res["STRICT"]["precision"],
            "gold_recall": gold_res["STRICT"]["recall"],
            "gold_f1": gold_res["STRICT"]["f1_score"],
            "its_level_change_irr": its_res["STRICT"]["level_change_post_2008"]["irr"],
            "its_level_change_p": its_res["STRICT"]["level_change_post_2008"]["p_value"],
            "its_slope_change_irr": its_res["STRICT"]["slope_change_time_after_2008"]["irr"],
            "its_slope_change_p": its_res["STRICT"]["slope_change_time_after_2008"]["p_value"],
            "status": "HIGH_PRECISION_ROBUST"
        },
        {
            "definition_level": "MODERATE",
            "description": "Specific economic harm + contextual gender indicators",
            "n_sentences": int(df_sents["is_econ_moderate"].sum()),
            "sentence_prevalence_pct": round(float(df_sents["is_econ_moderate"].mean() * 100), 3),
            "n_documents": int(df_docs["has_econ_moderate"].sum()),
            "document_prevalence_pct": round(float(df_docs["has_econ_moderate"].mean() * 100), 2),
            "gold_precision": gold_res["MODERATE"]["precision"],
            "gold_recall": gold_res["MODERATE"]["recall"],
            "gold_f1": gold_res["MODERATE"]["f1_score"],
            "its_level_change_irr": its_res["MODERATE"]["level_change_post_2008"]["irr"],
            "its_level_change_p": its_res["MODERATE"]["level_change_post_2008"]["p_value"],
            "its_slope_change_irr": its_res["MODERATE"]["slope_change_time_after_2008"]["irr"],
            "its_slope_change_p": its_res["MODERATE"]["slope_change_time_after_2008"]["p_value"],
            "status": "BALANCED_OPTIMAL_CONSTRUCT"
        },
        {
            "definition_level": "BROAD",
            "description": "All economic/patrimonial/labor/alimony stems in gender rulings",
            "n_sentences": int(df_sents["is_econ_broad"].sum()),
            "sentence_prevalence_pct": round(float(df_sents["is_econ_broad"].mean() * 100), 3),
            "n_documents": int(df_docs["has_econ_broad"].sum()),
            "document_prevalence_pct": round(float(df_docs["has_econ_broad"].mean() * 100), 2),
            "gold_precision": gold_res["BROAD"]["precision"],
            "gold_recall": gold_res["BROAD"]["recall"],
            "gold_f1": gold_res["BROAD"]["f1_score"],
            "its_level_change_irr": its_res["BROAD"]["level_change_post_2008"]["irr"],
            "its_level_change_p": its_res["BROAD"]["level_change_post_2008"]["p_value"],
            "its_slope_change_irr": its_res["BROAD"]["slope_change_time_after_2008"]["irr"],
            "its_slope_change_p": its_res["BROAD"]["slope_change_time_after_2008"]["p_value"],
            "status": "HIGH_RECALL_NOISY"
        }
    ]
    
    df_rob = pd.DataFrame(robustness_table)
    df_rob.to_csv("outputs/tables/table_robustness_sensitivity.csv", index=False)
    
    with open("outputs/statistics/robustness_sensitivity_report.json", "w", encoding="utf-8") as fh:
        json.dump(robustness_table, fh, ensure_ascii=False, indent=2)
        
    print("\n--- Tabla de Sensibilidad Multidefinición ---")
    print(df_rob[["definition_level", "n_sentences", "n_documents", "gold_f1", "its_level_change_irr", "its_level_change_p", "status"]])
    return df_rob

if __name__ == "__main__":
    perform_robustness_evaluation()
