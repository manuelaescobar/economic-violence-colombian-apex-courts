import os
import sys
import subprocess
import json
import time

PIPELINE_MODULES = [
    ("01_ingestion.py", "Ingesta y validación forense de archivos"),
    ("02_metadata_extraction.py", "Extracción estructurada jerárquica de metadata"),
    ("03_deduplication.py", "Control de duplicados y generación de dataset maestro de documentos"),
    ("03b_document_type_filter.py", "Filtro de tipo documental y alcance Apex Courts (auditoría de integridad)"),
    ("04_corpus_validation.py", "Segmentación y validación de oraciones maestras"),
    ("05_economic_violence_detection.py", "Detección multidefinición (Strict, Moderate, Broad)"),
    ("06_gold_standard.py", "Evaluación contra Gold Standard anotado"),
    ("07_temporal_analysis.py", "Modelos ITS, análisis de sobredispersión, autocorrelación y placebos"),
    ("08_semantic_analysis.py", "Word2Vec multi-seed determinista y concordancias KWIC"),
    ("09_institutional_analysis.py", "Diferenciación institucional por Keyness y Bootstrap"),
    ("09b_pairwise_institutional_keyness.py", "Contrastes pareados entre las tres cortes (ambas colas)"),
    ("10_robustness.py", "Evaluación de sensibilidad y robustez"),
    ("11_figures_tables.py", "Generación de figuras de 300 DPI y tablas académicas")
]

def run_full_pipeline():
    print("================================================================================")
    print("RECONSTRUCCIÓN COMPLETA Y AUDITORÍA DEL PIPELINE CUANTITATIVO (Q1 STANDARD)")
    print("================================================================================")
    
    start_time = time.time()
    for script_name, desc in PIPELINE_MODULES:
        print(f"\n---> Ejecutando: [{script_name}] - {desc}")
        ret = subprocess.run([sys.executable, script_name], capture_output=True, text=True)
        if ret.returncode != 0:
            print(f"ERROR en {script_name}:")
            print(ret.stderr)
            sys.exit(1)
        else:
            print(ret.stdout.strip())
            
    elapsed = time.time() - start_time
    print("\n================================================================================")
    print(f"PIPELINE EJECUTADO Y VALIDADO EXITOSAMENTE EN {elapsed:.2f} SEGUNDOS")
    print("================================================================================")

if __name__ == "__main__":
    run_full_pipeline()
