import os
import re
import pandas as pd

ACADEMIC_PATTERNS = [
    re.compile(r"\bREVISTA\b", re.IGNORECASE),
    re.compile(r"\bISSN\b", re.IGNORECASE),
    re.compile(r"\bART[IÍ]CULO DE INVESTIGACI[OÓ]N\b", re.IGNORECASE),
    re.compile(r"\bUNIVERSIDAD\b.{0,80}\bFACULTAD\b", re.IGNORECASE | re.DOTALL),
]

LAW_PATTERNS = [
    re.compile(r"\b(LEY|DECRETO|ACUERDO|RESOLUCI[OÓ]N)\s+\d+\s+DE\s+\d{4}\b", re.IGNORECASE),
    re.compile(r"CONGRESO DE LA REP[UÚ]BLICA", re.IGNORECASE),
]

JUDICIAL_EXCLUSION_PATTERNS = [
    re.compile(r"\bMAGISTRAD[OA]\s+PONENTE\b", re.IGNORECASE),
    re.compile(r"\bEXPEDIENTE\b", re.IGNORECASE),
    re.compile(r"\bACCI[OÓ]N DE TUTELA\b", re.IGNORECASE),
    re.compile(r"\bRADICACI[OÓ]N\b", re.IGNORECASE),
]


def classify(head_text: str) -> str:
    is_academic = any(p.search(head_text) for p in ACADEMIC_PATTERNS)
    if is_academic:
        return "ACADEMIC_ARTICLE"

    is_law = any(p.search(head_text) for p in LAW_PATTERNS)
    is_judicial_marker = any(p.search(head_text) for p in JUDICIAL_EXCLUSION_PATTERNS)
    if is_law and not is_judicial_marker:
        return "LAW_OR_DECREE_TEXT"

    return "OTHER"


def clean_head(text: str, n: int = 600) -> str:
    snippet = text[:n]
    return re.sub(r"\s+", " ", snippet).strip()


def main():
    df = pd.read_parquet("data/master_documents.parquet")

    rows = []
    for _, row in df.iterrows():
        filepath = row.get("filepath") or os.path.join("BD_completa", row["raw_filename"])
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                head_raw = fh.read(1500)
        except FileNotFoundError:
            head_raw = ""

        auto_flag = classify(head_raw) if head_raw else "OTHER"

        rows.append({
            "document_id": row["document_id"],
            "raw_filename": row["raw_filename"],
            "court": row["court"],
            "court_source": row["court_source"],
            "decision_year": row["decision_year"],
            "auto_flag": auto_flag,
            "has_econ_strict": row["has_econ_strict"],
            "has_econ_moderate": row["has_econ_moderate"],
            "has_econ_broad": row["has_econ_broad"],
            "head_600": clean_head(head_raw, 600),
            "decision_humana": "",
            "motivo": "",
        })

    out = pd.DataFrame(rows)
    os.makedirs("outputs/audit", exist_ok=True)
    out_path = "outputs/audit/document_type_review.csv"
    out.to_csv(out_path, index=False, encoding="utf-8")

    print(f"Escrito {out_path} con {len(out)} filas.")
    print(out["auto_flag"].value_counts())


if __name__ == "__main__":
    main()
