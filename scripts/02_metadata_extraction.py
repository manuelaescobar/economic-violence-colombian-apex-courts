import os
import re
import pandas as pd
import numpy as np

OUTPUT_DATA_DIR = "outputs/data"

def extract_structured_metadata():
    print("=== [02_metadata_extraction.py] Extracción Jerárquica de Metadata Oficial ===")
    df_raw = pd.read_parquet(os.path.join(OUTPUT_DATA_DIR, "raw_ingested_files.parquet"))
    
    # Months map
    months = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }
    
    # Patterns
    p_cc_t = re.compile(r'Sentencia\s+T-?\s*(\d+)[/\-](\d{2,4})', re.IGNORECASE)
    p_cc_c = re.compile(r'Sentencia\s+C-?\s*(\d+)[/\-](\d{2,4})', re.IGNORECASE)
    p_cc_su = re.compile(r'Sentencia\s+SU-?\s*(\d+)[/\-](\d{2,4})', re.IGNORECASE)
    p_cc_auto = re.compile(r'Auto\s+(\d+)[/\-](\d{2,4})', re.IGNORECASE)
    
    p_csj_prov = re.compile(r'(SP|SL|SC|STP|STC|STL)\s*(\d+)[/\-](\d{2,4})', re.IGNORECASE)
    p_csj_rad = re.compile(r'Radicación\s*n°?\s*(\d+)', re.IGNORECASE)
    p_csj_cas = re.compile(r'Casaci[óo]n\s*n°?\s*(\d+)', re.IGNORECASE)
    
    p_ce_rad = re.compile(r'Radicación\s*(?:número|n°)?\s*[:\s]*(\d{10,25})', re.IGNORECASE)
    
    p_date_header = re.compile(r'(?:Bogot[aá],?\s*D\.?\s*C\.?,?\s*)?(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+(19\d\d|20\d\d)', re.IGNORECASE)
    p_date_paren = re.compile(r'\(\s*(?:Bogot[aá],?\s*D\.?\s*C\.?,?\s*)?(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+(19\d\d|20\d\d)\s*\)', re.IGNORECASE)
    p_date_alt = re.compile(r'\b(199\d|20[0-2]\d)[/\-](\d{1,2})[/\-](\d{1,2})\b')
    
    def parse_year(yr_str):
        if not yr_str: return None
        yr = int(yr_str)
        if yr < 100:
            return 1900 + yr if yr > 50 else 2000 + yr
        return yr

    docs_meta = []
    
    for idx, row in df_raw.iterrows():
        fpath = row["filepath"]
        with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
            header_text = fh.read(4000)
            full_text = header_text # start with header
            
        court = None
        court_conf = "LOW"
        court_source = "NONE"
        doc_type = "Providencia"
        prov_num = None
        dec_year = None
        dec_month = None
        dec_date = None
        date_conf = "LOW"
        date_source = "NONE"
        
        # 1. Check Corte Constitucional specific headers
        m_t = p_cc_t.search(header_text)
        m_c = p_cc_c.search(header_text)
        m_su = p_cc_su.search(header_text)
        m_a = p_cc_auto.search(header_text)
        
        if m_t:
            court = "Corte Constitucional"
            doc_type = "Sentencia de Tutela"
            prov_num = f"T-{m_t.group(1)}/{m_t.group(2)}"
            dec_year = parse_year(m_t.group(2))
            court_conf = "HIGH"
            court_source = "OFFICIAL_HEADER_NUMBER"
            date_conf = "HIGH"
            date_source = "SENTENCE_IDENTIFIER"
        elif m_c:
            court = "Corte Constitucional"
            doc_type = "Sentencia de Constitucionalidad"
            prov_num = f"C-{m_c.group(1)}/{m_c.group(2)}"
            dec_year = parse_year(m_c.group(2))
            court_conf = "HIGH"
            court_source = "OFFICIAL_HEADER_NUMBER"
            date_conf = "HIGH"
            date_source = "SENTENCE_IDENTIFIER"
        elif m_su:
            court = "Corte Constitucional"
            doc_type = "Sentencia de Unificación"
            prov_num = f"SU-{m_su.group(1)}/{m_su.group(2)}"
            dec_year = parse_year(m_su.group(2))
            court_conf = "HIGH"
            court_source = "OFFICIAL_HEADER_NUMBER"
            date_conf = "HIGH"
            date_source = "SENTENCE_IDENTIFIER"
        elif m_a:
            court = "Corte Constitucional"
            doc_type = "Auto de Sala Plena/Seguimiento"
            prov_num = f"Auto-{m_a.group(1)}/{m_a.group(2)}"
            dec_year = parse_year(m_a.group(2))
            court_conf = "HIGH"
            court_source = "OFFICIAL_HEADER_NUMBER"
            date_conf = "HIGH"
            date_source = "SENTENCE_IDENTIFIER"
            
        # 2. Check Corte Suprema de Justicia
        m_csj_p = p_csj_prov.search(header_text)
        m_csj_r = p_csj_rad.search(header_text)
        
        if not court:
            if "CORTE SUPREMA DE JUSTICIA" in header_text.upper() or "SALA DE CASACIÓN" in header_text.upper():
                court = "Corte Suprema de Justicia"
                court_conf = "HIGH"
                court_source = "INSTITUTION_HEADER"
                if m_csj_p:
                    doc_type = f"Sentencia Casación {m_csj_p.group(1)}"
                    prov_num = f"{m_csj_p.group(1)}-{m_csj_p.group(2)}/{m_csj_p.group(3)}"
                    if not dec_year:
                        dec_year = parse_year(m_csj_p.group(3))
                        date_conf = "HIGH"
                        date_source = "SENTENCE_IDENTIFIER"
                elif m_csj_r:
                    doc_type = "Sentencia Casación"
                    prov_num = f"Rad-{m_csj_r.group(1)}"
                    
        # 3. Check Consejo de Estado
        if not court:
            if "CONSEJO DE ESTADO" in header_text.upper() or "SALA DE LO CONTENCIOSO ADMINISTRATIVO" in header_text.upper():
                court = "Consejo de Estado"
                court_conf = "HIGH"
                court_source = "INSTITUTION_HEADER"
                doc_type = "Sentencia Contencioso Administrativa"
                m_ce = p_ce_rad.search(header_text)
                if m_ce:
                    prov_num = f"Rad-{m_ce.group(1)}"

        # 4. Check other organs or fallback
        if not court:
            if "CORTE CONSTITUCIONAL" in header_text.upper():
                court = "Corte Constitucional"
                court_conf = "MEDIUM"
                court_source = "TEXT_MENTION_HEADER"
            elif "FISCALÍA" in header_text.upper() or "MINISTERIO" in header_text.upper() or "RESOLUCION" in header_text.upper():
                court = "Otras Entidades"
                court_conf = "MEDIUM"
                court_source = "INSTITUTION_HEADER"
            else:
                court = "Otras Entidades"
                court_conf = "LOW"
                court_source = "FALLBACK"
                
        # Date resolution if not yet found or for full precision
        m_date = p_date_header.search(header_text) or p_date_paren.search(header_text)
        if m_date:
            day = int(m_date.group(1))
            m_str = m_date.group(2).lower()
            month = months.get(m_str, 1)
            yr = int(m_date.group(3))
            
            # If date found in header, it's very reliable
            if not dec_year or date_conf != "HIGH":
                dec_year = yr
                dec_month = month
                dec_date = f"{yr:04d}-{month:02d}-{day:02d}"
                date_conf = "HIGH"
                date_source = "HEADER_EXPLICIT_DATE"
            else:
                dec_month = month
                dec_date = f"{dec_year:04d}-{month:02d}-{day:02d}"
        
        # Additional check if year is still None, look for year in first 500 chars
        if not dec_year:
            m_yr = re.search(r'\b(199\d|20[0-2]\d)\b', header_text[:1000])
            if m_yr:
                dec_year = int(m_yr.group(1))
                date_conf = "MEDIUM"
                date_source = "HEADER_FIRST_YEAR"

        docs_meta.append({
            "raw_filename": row["raw_filename"],
            "filepath": row["filepath"],
            "md5": row["md5"],
            "sha256": row["sha256"],
            "size_bytes": row["size_bytes"],
            "char_count": row["char_count"],
            "word_count": row["word_count"],
            "court": court,
            "court_confidence": court_conf,
            "court_source": court_source,
            "document_type": doc_type,
            "decision_number": prov_num,
            "decision_year": dec_year,
            "decision_month": dec_month,
            "decision_date": dec_date,
            "date_confidence": date_conf,
            "date_source": date_source
        })

    df_meta = pd.DataFrame(docs_meta)
    
    print("\n--- Resumen de Extracción de Metadata ---")
    print("Distribución por Corte:")
    print(df_meta["court"].value_counts(dropna=False))
    print(f"\nConfianza de Corte: {df_meta['court_confidence'].value_counts().to_dict()}")
    print(f"Decisiones con Año Estructurado Válido: {df_meta['decision_year'].notna().sum():,} / {len(df_meta):,} ({df_meta['decision_year'].notna().mean()*100:.1f}%)")
    print(f"Confianza de Fecha: {df_meta['date_confidence'].value_counts().to_dict()}")
    
    out_path = os.path.join(OUTPUT_DATA_DIR, "documents_with_extracted_metadata.parquet")
    df_meta.to_parquet(out_path, index=False)
    print(f"Dataset guardado en '{out_path}'")
    return df_meta

if __name__ == "__main__":
    extract_structured_metadata()
