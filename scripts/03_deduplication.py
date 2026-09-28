import os
import pandas as pd
import numpy as np

OUTPUT_DATA_DIR = "outputs/data"

def perform_deduplication():
    print("=== [03_deduplication.py] Identificación y Control Riguroso de Duplicados ===")
    df_meta = pd.read_parquet(os.path.join(OUTPUT_DATA_DIR, "documents_with_extracted_metadata.parquet"))
    
    # 1. Exact MD5 Hash Duplication Grouping
    df_meta["duplicate_group"] = df_meta.groupby("md5").ngroup()
    df_meta["is_duplicate"] = df_meta.duplicated(subset=["md5"], keep="first")
    
    # Sort deterministically
    df_meta = df_meta.sort_values(by=["duplicate_group", "raw_filename"]).reset_index(drop=True)
    
    # Generate canonical document_id
    # Format: DOC_{duplicate_group:04d}
    df_meta["document_id"] = df_meta["duplicate_group"].apply(lambda g: f"DOC_{g:04d}")
    
    # Primary representative for each document
    df_unique = df_meta[~df_meta["is_duplicate"]].copy().reset_index(drop=True)
    
    print(f"Total archivos procesados: {len(df_meta):,}")
    print(f"Grupos de duplicados exactos: {df_meta['duplicate_group'].nunique():,}")
    print(f"Archivos redundantes marcados como duplicados (excluidos del maestro): {df_meta['is_duplicate'].sum():,}")
    print(f"Documentos maestros únicos finales: {len(df_unique):,}")
    
    # Save full catalog with duplicate flags
    df_meta.to_parquet(os.path.join(OUTPUT_DATA_DIR, "all_files_deduplication_catalog.parquet"), index=False)
    
    # Save master unique documents
    df_unique.to_parquet("data/master_documents.parquet", index=False)
    print("Dataset maestro guardado en 'data/master_documents.parquet'")
    
    return df_unique

if __name__ == "__main__":
    perform_deduplication()
