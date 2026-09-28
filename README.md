# Economic Violence Against Women in Colombian Apex Courts Jurisprudence — data and code

Data and code accompanying the manuscript **"Three Courts, Three Doctrines: Institutional
Channeling of Economic Violence Against Women in Colombian Apex Courts Jurisprudence
(1992–2024)"** by Diana Pacheco-Ortiz, Manuela Escobar-Sierra and Stephanie Rendón Zapata,
under revision at *Humanities and Social Sciences Communications* (submission
9c47b88b-0dd9-4cc6-954d-e4b277f5dbd7).

DOI: `DOI_PENDING`

---

## 1. Contents

| File | Rows × cols | Unit of analysis | Description |
|---|---|---|---|
| `data/documents.parquet` / `.csv` | 453 × 30 | Judicial decision | Canonical corpus: the 453 apex-court decisions retained after deduplication and the document-type/jurisdictional-scope audit |
| `data/sentences_metadata.parquet` | 269,531 × 16 | Sentence | Metadata and classification flags for every valid sentence (≥25 characters) in the 453 decisions; **no sentence text**, only a SHA-256 hash of it |
| `data/flagged_sentences_text.parquet` / `.csv` | 4,634 × 17 | Sentence | Anonymized text of every sentence flagged by any of the three operationalization tiers (strict/moderate/broad) |
| `data/validation_sample.parquet` / `.csv` | 250 × 17 | Sentence | Rule-based validation sample used to benchmark the lexical tiers (Table 2 of the manuscript), with anonymized text |
| `data/kwic_concordances.csv` | 349 × 9 | Sentence (concordance) | KWIC concordance samples for keyness-distinctive terms, with anonymized text |
| `data/document_type_audit.csv` | 1,040 × 12 | Candidate document | Document-type and jurisdictional-scope audit of every candidate document, with the exclusion decision and reason for each |
| `data/candidate_documents_catalog.csv` | 1,040 × 24 | Candidate document | Full metadata catalog of all 1,040 candidate documents (i.e., before the 453-document filter), for tracing every exclusion |
| `data/yearly_temporal_series.csv` | 24 × 16 | Year (1992–2024, non-empty years) | Annual document and sentence counts by tier, used for the temporal/ITS models |
| `config/economic_violence_lexicon.yml` | — | — | The three-tier lexicon (regex patterns) used for classification |
| `scripts/*.py` | — | — | Full processing and analysis pipeline (see §5) |
| `outputs/statistics/*.json` | — | — | Raw statistical outputs (Fisher's exact tests, ITS models, bootstrap keyness, gold-standard evaluation, Word2Vec stability, robustness) |
| `outputs/tables/*.csv` | — | — | Manuscript tables 1–5 in machine-readable form |
| `outputs/figures/*.png` | — | — | Manuscript figures 1–6, 300 DPI |
| `outputs/audit/CORRECTION_LOG.md` | — | — | Every numerical claim in the originally submitted manuscript, its corrected value, and why |

## 2. Variable dictionary

### `data/documents.parquet` (453 × 30) — one row per apex-court decision

| Column | Type | Meaning |
|---|---|---|
| `raw_filename` | str | Original filename in the acquired repository |
| `md5`, `sha256` | str | Content hashes used for deduplication |
| `size_bytes`, `char_count`, `word_count` | int | Raw file size / extracted character and word counts |
| `court` | str | Issuing apex court: Corte Constitucional, Corte Suprema de Justicia, Consejo de Estado |
| `court_confidence` | str | HIGH / MEDIUM / LOW confidence of the automated court-attribution rule |
| `court_source` | str | Which structural marker identified the court (e.g., official header number, text mention) |
| `document_type` | str | Decision type (e.g., Sentencia de Tutela, Providencia) |
| `decision_number` | str | Official case/decision identifier |
| `decision_year`, `decision_month`, `decision_date` | numeric/date | Official decision date, extracted hierarchically |
| `date_confidence`, `date_source` | str | Confidence and source of the date extraction |
| `duplicate_group` | int | ID of the exact-content duplicate group this file belonged to before deduplication |
| `is_duplicate` | bool | Whether this file was a duplicate (all rows here are `False`; duplicates are not in the canonical corpus) |
| `document_id` | str | Canonical document identifier (`DOC_####`) used across all tables |
| `is_judicial_decision` | bool | Result of the document-type/jurisdictional-scope audit (`True` for all 453 rows) |
| `exclusion_reason` | str | Empty for all rows here (populated only in `candidate_documents_catalog.csv` for excluded documents) |
| `total_sentences` | int | Valid sentences (≥25 characters) extracted from this decision |
| `gender_sentences` | int | Sentences flagged as gender-relevant |
| `econ_strict_sentences`, `econ_moderate_sentences`, `econ_broad_sentences` | int | Sentences matching each operationalization tier |
| `has_gender`, `has_econ_strict`, `has_econ_moderate`, `has_econ_broad` | bool | Document-level indicator (≥1 matching sentence) used in the Fisher's-exact and ITS models |

### `data/sentences_metadata.parquet` (269,531 × 16) — one row per valid sentence, no text

| Column | Type | Meaning |
|---|---|---|
| `document_id`, `sentence_id`, `sentence_position` | str/int | Links to `documents.parquet` and position within the decision |
| `char_length`, `word_length` | int | Sentence length |
| `is_gender_relevant` | bool | Gender-relevant sentence flag |
| `court`, `court_confidence`, `decision_year`, `decision_date`, `date_confidence`, `document_type` | — | Copied from the parent document, for convenience |
| `is_econ_strict`, `is_econ_moderate`, `is_econ_broad` | bool | Operationalization-tier match at the sentence level |
| `sentence_sha256` | str | SHA-256 hash of the UTF-8 sentence text (not itself the text); allows checking a sentence's text against the full corpus without redistributing it |

### `data/flagged_sentences_text.parquet` (4,634 × 17) and `data/validation_sample.parquet` (250 × 17)

Same columns as `sentences_metadata.parquet`, plus:

| Column | Type | Meaning |
|---|---|---|
| `sentence_text` | str | **Anonymized** sentence text (identity numbers, phone numbers and email addresses replaced with `[ID REDACTED]`, `[PHONE REDACTED]`, `[EMAIL REDACTED]`) |
| `gold_label` | bool | *(`validation_sample.parquet` only)* Rule-based validation label: whether the sentence was labelled as denoting economic/patrimonial violence by the labelling criteria described in §3 of the manuscript. **This is a rule-based label, not independent human annotation** — see the Limitations note in §6 below |

### `data/kwic_concordances.csv` (349 × 9)

| Column | Meaning |
|---|---|
| `target_term` | The keyness-distinctive term this concordance illustrates |
| `document_id`, `court`, `decision_year`, `sentence_id` | Source sentence identifiers |
| `context_before`, `matched_token`, `context_after` | The KWIC window (anonymized) |
| `full_sentence` | The full sentence (anonymized) |

### `data/document_type_audit.csv` (1,040 × 12)

| Column | Meaning |
|---|---|
| `document_id`, `raw_filename` | Document identifiers |
| `court`, `court_source` | Automated court attribution |
| `decision_year` | Extracted decision year |
| `auto_label` | Heuristic document-type flag: `ACADEMIC_ARTICLE`, `LAW_OR_DECREE_TEXT`, `OTHER`/`UNCERTAIN` (see §4 for the matching rules) |
| `auto_confidence` | Confidence of the heuristic flag |
| `has_econ_strict`, `has_econ_moderate`, `has_econ_broad` | Whether this candidate document matched each tier (before exclusion) |
| `decision_humana` | Human reviewer's decision: `INCLUIR` / `EXCLUIR` |
| `motivo` | Short reason for the human decision (e.g., "artículo de revista", "texto normativo", "no es alta corte", "providencia válida") |

### `data/candidate_documents_catalog.csv` (1,040 × 24)

All columns of `documents.parquet`, computed for the full 1,040-document candidate set
(i.e., before the document-type/jurisdictional-scope filter), plus `decision_humana`,
`motivo` and `auto_label` from the audit. `exclusion_reason` is populated for the 587
excluded documents (academic article, statutory/administrative text, corrupted file, or
non-apex-court decision).

### `data/yearly_temporal_series.csv` (24 × 16)

One row per year with at least one decision (1992–2024): document and sentence counts by
tier, and per-1,000-sentence prevalence rates, as used to fit the interrupted time-series
models (Table 3 / Figures 2–3 of the manuscript).

## 3. Coding scheme — the three operationalization tiers

Copied verbatim from `config/economic_violence_lexicon.yml`:

- **Strict** — explicit, autonomous constructs: `violencia económica`, `violencia
  patrimonial`, `violencia económica y patrimonial`, `despojo económico/patrimonial/de
  bienes`, `control económico de la pareja/machista/coercitivo`, `violencia basada en
  género económica/patrimonial`.
- **Moderate** — a co-occurrence term (`dependencia económica`, `autonomía económica`,
  `coacción económica`, `explotación económica`, `incumplimiento doloso/sistemático/
  reiterado de la cuota alimentaria`, `asfixia económica`, `discriminación económica`,
  `subordinación económica`, `abuso económico/patrimonial`) co-occurring with a
  gender-context term (`mujer(es)`, `género`, `víctima(s)`, `pareja`, `violencia`,
  `feminicidio`, `maltrato`).
- **Broad** — generic economic/family-law stems: `económico(s/as)`, `patrimonio/
  patrimonial(es)`, `alimentos/alimentaria(s)/alimenticios`, `bienes`, `laboral(es)`,
  `ingresos`, `dependencia`, `despojo`, `cuota(s)`, `sociedad conyugal`, `gananciales`.
- Explicit **false-positive exclusions** (e.g., `arancel judicial`, `tasa de interés
  bancario`, `contratación estatal`) are applied on top of all three tiers.

Full regex patterns are in `config/economic_violence_lexicon.yml`.

## 4. Corpus construction

```
4,400 acquired files
  − 2,914 zero-byte acquisition artifacts
  − 22 files below the 100-byte minimum threshold
  − 424 exact-content duplicates (MD5 hashing)
  = 1,040 unique candidate documents
        ↓  document-type & jurisdictional-scope audit
  − 88 academic articles (journal header/ISSN/byline conventions)
  − 160 statutory or administrative texts (Ley/Decreto/Acuerdo/Resolución numbering,
        Congressional gazettes, CONPES, ministerial directives)
  − 1 corrupted file
  − 332 decisions issued by courts other than the three apex courts
  − 6 documents of uncertain classification, excluded conservatively
  = 453 canonical apex-court decisions
    (Corte Constitucional 342, Corte Suprema de Justicia 73, Consejo de Estado 38)
    269,531 valid sentences (≥25 characters)
```

`data/document_type_audit.csv` and `data/candidate_documents_catalog.csv` document every
individual exclusion and its stated reason, so the filter is fully auditable.

## 5. Anonymization and access to the full text

The full text of the 453 underlying decisions is **not redistributed** in this
repository, because it is public jurisprudence that nonetheless contains personal data of
parties in gender-based-violence proceedings — including, in a small number of sentences,
national identity-document numbers — protected under Colombian data-protection law
(Ley 1581 de 2012). Instead:

- `data/sentences_metadata.parquet` publishes the classification metadata of **all**
  269,531 sentences, together with a SHA-256 hash of each sentence's text, so that a
  sentence's classification can be independently checked against the original decision
  without redistributing the decision itself.
- The text is published, **anonymized**, only for the 4,634 sentences flagged by any
  operationalization tier, the 250-sentence validation sample, and the 349 KWIC
  concordances. Identity-document numbers, phone numbers and email addresses are
  replaced with `[ID REDACTED]`, `[PHONE REDACTED]` and `[EMAIL REDACTED]`; monetary
  amounts and case/docket numbers are left untouched.
- The decisions themselves are public: each is cited by its official case number in
  `data/documents.parquet` (`decision_number`) and retrievable from the corresponding
  court's public jurisprudence database (Corte Constitucional, Corte Suprema de Justicia,
  Consejo de Estado).
- The complete anonymized full-text corpus is available to editors and peer reviewers of
  the manuscript on request to the corresponding author, Manuela Escobar-Sierra
  (mescobars@unal.edu.co).

## 6. Reproduction

**Quick check (no full text required).** Recomputes the manuscript's headline statistics
(document/sentence counts, pre/post-2008 Fisher's exact tests, and the rule-based
validation Precision/Recall/F1) directly from the published derived data:

```bash
pip install pandas pyarrow scikit-learn scipy
python verify_reported_results.py
```

**Full pipeline (requires the original text corpus, not included here).**

The pipeline scripts were originally developed to run flat, from the same directory as
`config.yaml`, `data/`, `outputs/` and `BD_completa/` (the orchestrator invokes each stage
by bare filename, e.g. `01_ingestion.py`, so all stages must be siblings of one another and
of `config.yaml` on disk). To reproduce end to end:

```bash
pip install -r requirements.txt
python -m spacy download es_core_news_sm
cp scripts/*.py .                 # bring the pipeline stages into the repo root...
mkdir -p BD_completa               # ...and place the original decision text files here
python 12_reproducibility_report.py   # orchestrates 01 -> 11 (incl. 03b, 09b); 13/13b produced the document-type audit
```

The scripts were originally developed against `data/master_documents.parquet`,
`data/master_sentences.parquet` and `data/gold_standard_annotations.parquet`; the files
published here correspond to them as follows:

| Published file | Original pipeline file | Difference |
|---|---|---|
| `data/documents.parquet` | `master_documents.parquet` | `filepath` column removed |
| `data/sentences_metadata.parquet` | `master_sentences.parquet` | `sentence_text` removed, `sentence_sha256` added |
| `data/validation_sample.parquet` | `gold_standard_annotations.parquet` | `sentence_text` anonymized |

## 7. Correction log

`outputs/audit/CORRECTION_LOG.md` documents every numerical claim that changed between the
originally submitted manuscript and the revised version, and the script or output file
that produced each corrected figure.

## 8. License

Code (`scripts/`, `verify_reported_results.py`, `config/`): MIT (see `LICENSE`).
Data (`data/`, `outputs/`): Creative Commons Attribution 4.0 International (CC BY 4.0).

## 9. Citation

See `CITATION.cff`. Archived release: `v1.0-hssc-minor-revision`, DOI `DOI_PENDING`.
