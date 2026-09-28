import os
import pandas as pd

REVIEW_CSV = "outputs/audit/document_type_review_v2.csv"


def apply_document_type_filter():
    print("=== [03b_document_type_filter.py] Filtro de tipo documental y alcance Apex Courts ===")

    df_docs = pd.read_parquet("data/master_documents.parquet")
    review = pd.read_csv(REVIEW_CSV)[["document_id", "decision_humana", "motivo", "auto_label"]]

    missing = set(df_docs["document_id"]) - set(review["document_id"])
    if missing:
        raise ValueError(
            f"{len(missing)} document_id de master_documents.parquet no están en {REVIEW_CSV}: "
            f"{sorted(missing)[:10]}"
        )

    df_docs = df_docs.merge(review, on="document_id", how="left", validate="one_to_one")

    df_docs["is_judicial_decision"] = df_docs["decision_humana"] == "INCLUIR"
    df_docs["exclusion_reason"] = df_docs["motivo"].where(~df_docs["is_judicial_decision"], "")

    n_total = len(df_docs)
    n_academic = (df_docs["auto_label"] == "ACADEMIC_ARTICLE").sum()
    n_law = (df_docs["auto_label"] == "LAW_OR_DECREE_TEXT").sum()
    n_broken = (df_docs["auto_label"] == "BROKEN_OR_EMPTY").sum()
    n_non_apex_judicial = (
        (df_docs["auto_label"] == "JUDICIAL") & (~df_docs["is_judicial_decision"])
    ).sum()
    n_kept = df_docs["is_judicial_decision"].sum()

    print(f"Total documentos catalogados: {n_total:,}")
    print(f"  Excluidos - artículos académicos:      {n_academic:,}")
    print(f"  Excluidos - textos de ley/decreto/acto administrativo: {n_law:,}")
    print(f"  Excluidos - archivo roto/vacío:         {n_broken:,}")
    print(f"  Excluidos - judicial pero no Apex Court: {n_non_apex_judicial:,}")
    print(f"  RETENIDOS (is_judicial_decision=True, Apex Courts): {n_kept:,}")

    # Preserve the full unfiltered catalog for traceability (nothing is deleted).
    os.makedirs("outputs/audit", exist_ok=True)
    df_docs.to_parquet("outputs/audit/master_documents_full_catalog.parquet", index=False)

    # Canonical corpus used by all downstream pipeline stages: apex-court judicial decisions only.
    df_filtered = df_docs[df_docs["is_judicial_decision"]].drop(
        columns=["decision_humana", "motivo", "auto_label"]
    ).reset_index(drop=True)
    df_filtered.to_parquet("data/master_documents.parquet", index=False)

    print(f"\n'data/master_documents.parquet' sobrescrito con {len(df_filtered):,} documentos "
          f"(is_judicial_decision=True, Apex Courts).")
    print("Catálogo completo con exclusiones preservado en "
          "'outputs/audit/master_documents_full_catalog.parquet'.")

    return df_filtered


if __name__ == "__main__":
    apply_document_type_filter()
