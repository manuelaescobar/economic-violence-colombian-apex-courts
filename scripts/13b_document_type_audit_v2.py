import os
import re
import pandas as pd

# ---- Strong judicial-structure markers (caption / ratio decidendi conventions) ----
JUDICIAL_PATTERNS = [
    re.compile(r"\bMAGISTRAD[OA]\s+(PONENTE|SUSTANCIADOR[A]?)\b", re.IGNORECASE),
    re.compile(r"\bRADICACI[OÓ]N\b", re.IGNORECASE),
    re.compile(r"\bRADICADO\b", re.IGNORECASE),
    re.compile(r"\bEXPEDIENTE\b", re.IGNORECASE),
    re.compile(r"\bACCI[OÓ]N DE TUTELA\b", re.IGNORECASE),
    re.compile(r"\bSentencia\s+(T|C|SU|A)-\d+[/-]\d{2,4}\b", re.IGNORECASE),
    re.compile(r"\b(SC|SP|STC|STL|STP|AC|ATP)\d{2,6}-\d{4}\b"),  # CSJ decision codes
    re.compile(r"\bRAMA JUDICIAL\b", re.IGNORECASE),
    re.compile(r"\bSALA (PLENA|DE CASACI[OÓ]N|JURISDICCIONAL DISCIPLINARIA|DE REVISI[OÓ]N)\b", re.IGNORECASE),
    re.compile(r"\bTRIBUNAL SUPERIOR\b", re.IGNORECASE),
    re.compile(r"\bRECURSO DE CASACI[OÓ]N\b", re.IGNORECASE),
    re.compile(r"\bAuto\s+\d+[/-]\d{2,4}\b"),
    re.compile(r"\b(Auto|Sentencia)\s+[A-Z]*-?\d+\s+de\s+\d{4}\b", re.IGNORECASE),
    re.compile(r"\bCORTE INTERAMERICANA DE DERECHOS HUMANOS\b", re.IGNORECASE),
    re.compile(r"\bConsejer[oa]\s+Ponente\b", re.IGNORECASE),
    re.compile(r"\b(ADICI[OÓ]N|ACLARACI[OÓ]N|SALVAMENTO)\s+DE\s+VOTO\b", re.IGNORECASE),
    # Colombian jurisprudence-digest headnote convention: ALLCAPS TOPIC-descriptor sentence
    re.compile(r"^[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ \-]{8,100}-\s?[A-ZÁÉÍÓÚÑ]"),
    # Consejo de Estado slash-separated descriptor headnote: "PLANTA DE PERSONAL / MODIFICACIÓN..."
    re.compile(r"^[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ \d]{3,60}(\s*/\s*[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ \d]{3,60}){1,}"),
]

BROKEN_PATTERNS = [
    re.compile(r"\bArchivo no encontrado\b", re.IGNORECASE),
    re.compile(r"\bLa Norma o Sentencia Solicitada no se encuentra disponible\b", re.IGNORECASE),
]

ADMIN_ACT_PATTERNS = [
    re.compile(r"\bCOMUNIDAD ANDINA\b", re.IGNORECASE),
    re.compile(r"\bDIRECTIVA (MINISTERIAL|PRESIDENCIAL)\s+\d+\s+DE\s+\d{4}\b", re.IGNORECASE),
    re.compile(r"\bCIRCULAR\s+(EXTERNA\s+)?\d+\s+DE\s+\d{4}\b", re.IGNORECASE),
    re.compile(r"\bG\s?A\s?C\s?E\s?T\s?A\s?(S)?\s?D\s?E\s?L\s?\s?C\s?O\s?N\s?G\s?R\s?E\s?S\s?O\b", re.IGNORECASE),
    re.compile(r"\bTEXTO\s+AL\s+PROYECTO\s+DE\s+LEY\b", re.IGNORECASE),
    re.compile(r"\bCONPES\b", re.IGNORECASE),
    re.compile(r"\bCONSEJO NACIONAL DE POL[IÍ]TICA (ECON[OÓ]MICA Y SOCIAL|SOCIAL)\b", re.IGNORECASE),
]

# ---- Academic-article markers ----
ACADEMIC_PATTERNS = [
    re.compile(r"\bREVISTA\b", re.IGNORECASE),
    re.compile(r"\bISSN\b", re.IGNORECASE),
    re.compile(r"\bART[IÍ]CULO DE INVESTIGACI[OÓ]N\b", re.IGNORECASE),
    re.compile(r"\bUNIVERSIDAD\b.{0,80}\bFACULTAD\b", re.IGNORECASE | re.DOTALL),
    # citation footer style: "Año 4, No. 7" / "Vol. 48 / No. 128" / "pag. 80 a 101" / "pp. 193-217"
    re.compile(r"\bA[ñn]o\s+\d+,?\s+No\.?\s*\d+\b", re.IGNORECASE),
    re.compile(r"\bVol\.?\s*\d+\b.{0,40}\bNo\.?\s*\d+\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\bpp?\.?\s*\d+\s*[-a]\s*\d+\b", re.IGNORECASE),
    # submission-date convention used by academic journals
    re.compile(r"\b(Recibido|Presentado)\b.{0,80}\bAprobado\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\bRese[ñn]a del libro\b", re.IGNORECASE),
]

# ---- Law/decree markers ----
LAW_PATTERNS = [
    re.compile(r"\b(LEY|DECRETO|ACUERDO|RESOLUCI[OÓ]N)\s+\d+\s+DE\s+\d{4}\b", re.IGNORECASE),
    re.compile(r"CONGRESO DE LA REP[UÚ]BLICA", re.IGNORECASE),
    re.compile(r"\bPODER P[UÚ]BLICO\s*-\s*RAMA LEGISLATIVA\b", re.IGNORECASE),
] + ADMIN_ACT_PATTERNS


def count_university_bylines(head: str) -> int:
    return len(re.findall(r"\bUniversidad\b", head[:400], re.IGNORECASE))


def classify(head: str) -> tuple[str, str]:
    """Returns (label, confidence). label in {JUDICIAL, ACADEMIC_ARTICLE, LAW_OR_DECREE_TEXT, BROKEN_OR_EMPTY, UNCERTAIN}."""
    if not head.strip() or any(p.search(head) for p in BROKEN_PATTERNS):
        return "BROKEN_OR_EMPTY", "HIGH"

    is_judicial = any(p.search(head) for p in JUDICIAL_PATTERNS)
    is_academic = any(p.search(head) for p in ACADEMIC_PATTERNS) or count_university_bylines(head) >= 2
    is_law = any(p.search(head) for p in LAW_PATTERNS)

    # A genuine judicial caption (Magistrado Ponente / Radicación / Sentencia T-.../ Auto .../
    # CIDH caption / headnote-digest format) is a highly specific convention that academic
    # articles do not reproduce. When both fire, the academic hit is almost always a citation
    # footnote ("Nota LexBase: Citado en la Revista...") appended after the real caption, so
    # judicial wins.
    if is_judicial:
        return "JUDICIAL", "HIGH"

    if is_academic:
        return "ACADEMIC_ARTICLE", "HIGH"

    if is_law:
        return "LAW_OR_DECREE_TEXT", "HIGH"

    return "UNCERTAIN", "LOW"


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

        label, confidence = classify(head_raw)

        # Gate 0.3 already resolved by authors: apex courts only.
        is_apex_court = row["court"] in ("Corte Constitucional", "Corte Suprema de Justicia", "Consejo de Estado")

        if label == "JUDICIAL" and confidence == "HIGH" and is_apex_court:
            decision = "INCLUIR"
            motivo = "auto: marcador judicial de alta confianza + alta corte"
        elif label == "JUDICIAL" and confidence == "HIGH" and not is_apex_court:
            decision = "EXCLUIR"
            motivo = "auto: providencia judicial pero no es alta corte (Gate 0.3)"
        elif label in ("ACADEMIC_ARTICLE", "LAW_OR_DECREE_TEXT", "BROKEN_OR_EMPTY") and confidence == "HIGH":
            decision = "EXCLUIR"
            motivo = f"auto: {label.lower()} de alta confianza"
        else:
            decision = ""
            motivo = ""

        rows.append({
            "document_id": row["document_id"],
            "raw_filename": row["raw_filename"],
            "court": row["court"],
            "court_source": row["court_source"],
            "decision_year": row["decision_year"],
            "auto_label": label,
            "auto_confidence": confidence,
            "has_econ_strict": row["has_econ_strict"],
            "has_econ_moderate": row["has_econ_moderate"],
            "has_econ_broad": row["has_econ_broad"],
            "head_600": clean_head(head_raw, 600),
            "decision_humana": decision,
            "motivo": motivo,
        })

    out = pd.DataFrame(rows)
    os.makedirs("outputs/audit", exist_ok=True)
    out_path = "outputs/audit/document_type_review_v2.csv"
    out.to_csv(out_path, index=False, encoding="utf-8")

    print(f"Escrito {out_path} con {len(out)} filas.")
    print("\nDistribución auto_label x confidence:")
    print(out.groupby(["auto_label", "auto_confidence"]).size())
    print("\nDecisiones auto-resueltas:")
    print(out["decision_humana"].replace("", "SIN_RESOLVER (requiere revisión)").value_counts())


if __name__ == "__main__":
    main()
