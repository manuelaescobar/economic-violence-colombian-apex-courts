# Tabla de correspondencia — HSSC Submission 9c47b88b-0dd9-4cc6-954d-e4b277f5dbd7

Generado tras la auditoría de integridad de datos solicitada por el editor (revisión menor).
Fuente de verdad: `outputs/` regenerado el 2026-09-22 (`outputs/audit/rerun_20260922_1825.log`,
re-ejecutado con corrección de placebo test) mediante `python 12_reproducibility_report.py`.

Leyenda: **CAMBIA** = valor numérico distinto | **YA ERA INCORRECTO** = ya no coincidía con el
pipeline antes de esta auditoría | **CAMBIO ESTRUCTURAL** = no es solo una cifra, cambia el
diseño del corpus o el marco de interpretación.

## 1. Definición y tamaño del corpus (CAMBIO ESTRUCTURAL)

| Ubicación en manuscrito | Valor publicado | Valor recalculado | Δ | Archivo fuente |
|---|---|---|---|---|
| Abstract, §3.1, Tabla 1 | N = 1,040 "unique Apex Courts decisions" | N = 453 "unique Apex Courts decisions" | −587 (−56.4%) | `data/master_documents.parquet`, `outputs/audit/master_documents_full_catalog.parquet` |
| Abstract, §3.1 | 485,187 oraciones totales | 269,531 oraciones totales | −215,656 | `data/master_sentences.parquet` |
| — (no reportado) | — | 88 artículos académicos, 160 textos ley/decreto/acto administrativo, 1 archivo roto, 332 providencias judiciales de no-Apex-Court excluidos (587 total) | nuevo | `outputs/audit/document_type_review_v2.csv`, `03b_document_type_filter.py` |
| Tabla 1 (composición por corte) | Corte Constitucional 364, CSJ 75, Consejo de Estado 40, "Otras Entidades" 561 (54%) | Corte Constitucional 342, CSJ 73, Consejo de Estado 38, 0 "Otras Entidades" (por diseño, Gate 0.3) | corpus ahora 100% Apex Courts | `data/master_documents.parquet` |
| §3.1 (declaración de composición) | "N = 1,040 unique Apex Courts judicial decisions" | corregir a N = 453, con nota de exclusión del 56.4% del corpus original por contaminación no-judicial y no-apex | — | ídem |

## 2. Flujo de ingesta (SIN CAMBIO salvo lo señalado)

| Etapa | Valor publicado | Valor recalculado | Estado |
|---|---|---|---|
| Archivos crudos | 4,400 | 4,400 | SIN CAMBIO |
| Archivos vacíos (0 bytes) excluidos | 2,914 | 2,914 (66.2%) | SIN CAMBIO |
| Archivos no vacíos válidos | 1,486 | 1,464 | **CAMBIA — resuelto**: hay 2,914 archivos de exactamente 0 bytes y **22 archivos adicionales de 1–99 bytes** que el pipeline excluye por el umbral `min_file_size_bytes: 100` (`config.yaml`). El manuscrito reporta 1,486 (= 4,400 − 2,914), que solo descuenta los de 0 bytes. El valor correcto es **1,464**. La Figura 1 fue actualizada para mostrar ambos pasos de exclusión. |
| Grupos de duplicados MD5 | 292 grupos / 424 redundantes | 1,040 grupos / 424 redundantes | ver nota¹ |
| **Nueva etapa: filtro de tipo documental + Apex Courts** | no existía | 587 excluidos → 453 retenidos | **CAMBIO ESTRUCTURAL (nuevo)** |

¹ Nota: "292 grupos de duplicados" en el texto original parece describir grupos con ≥2 archivos
(i.e., grupos que efectivamente contienen redundancia), mientras que el pipeline reporta 1,040
grupos MD5 totales (incluyendo grupos de tamaño 1). Verificar con las autoras cuál cifra es la
que debe aparecer en el flowchart; ambas son internamente consistentes con datos distintos.

## 3. Operacionalización de tres niveles (CAMBIA — todas las cifras, por reducción del corpus)

| Tier | Manuscrito (N=1040) | Recalculado (N=453) |
|---|---|---|
| STRICT — docs / oraciones | 93 / 233 | **50 / 164** |
| MODERATE — docs / oraciones | 170 / 416 | **89 / 233** |
| BROAD — docs / oraciones | 748 / 7,421 | **351 / 4,634** |
| Prevalencia documental STRICT | 8.9% | 11.04% |
| Prevalencia documental MODERATE | 16.3% | 19.65% |
| Prevalencia documental BROAD | 71.9% | 77.48% |

Fuente: `outputs/tables/table_2_operationalization.csv`, `outputs/statistics/robustness_sensitivity_report.json`.

## 4. Gold standard (CAMBIO ESTRUCTURAL — naturaleza del método, no solo cifras)

| Ubicación | Publicado | Corregido |
|---|---|---|
| Abstract, §3.2, Tabla 2 (×2 apariciones) | "an independently annotated gold standard" | Es **100% programático** (reglas de keyword-matching en `06_gold_standard.py`, función `annotate_gold`), no anotación humana. Reescribir como "a rule-based validation sample, constructed via keyword-matching criteria independent of the detector's own three-tier operationalization" |
| STRICT — Precision/Recall/F1 | 0.980 / 0.778 / 0.867 | **0.960 / 0.828 / 0.889** |
| MODERATE — Precision/Recall/F1 | 0.620 / 0.984 / 0.761 | **0.580 / 1.000 / 0.734** |
| BROAD — Precision/Recall/F1 | (perfect recall, bajo F1) | **0.387 / 1.000 / 0.558** |
| FPR strict | 0.54% | recalcular desde matriz de confusión: FP=2/(2+190)=1.04% |

Fuente: `outputs/statistics/gold_standard_evaluation.json`.

## 5. Modelo temporal / hallazgo central del paper (CAMBIO ESTRUCTURAL — el más importante)

| Elemento | Publicado (§4a) | Corregido |
|---|---|---|
| Baseline pre-2008 trend (viñeta 1) | IRR = 1.053 (95% CI [0.812, 1.365], p = 0.697) | **YA ERA INCORRECTO antes de esta auditoría** (desfase 2026-08-13 vs 2026-08-14, ver Hallazgo 3 del plan). Con el corpus corregido, el modelo STRICT es ahora **numéricamente no identificable**: `pre_trend_time` IRR ≈ 1,762 con IC 95% hasta ~10¹⁹⁴ (`outputs/statistics/its_models_results.json`). Mecanismo exacto verificado abajo. |
| ITS STRICT — nivel / pendiente | level 0.564, slope 1.286 | level IRR = 0.394 (p = 0.400); slope IRR = 0.0006 (p = 0.974, **artefacto numérico, no interpretable**) |
| ITS MODERATE — nivel / pendiente | level 0.231, slope 1.127 | level IRR = 0.113 (p = 0.003); slope IRR = 0.484 (p < 0.0001) — converge, pero ver limitación abajo |
| ITS BROAD | (nulo) | level IRR = 0.681 (p = 0.439); slope IRR = 1.028 (p = 0.634) — nulo, consistente con antes |
| **Nuevo: comparación descriptiva pre/post-2008 (Fisher exacto, nivel documento)** | no existía | STRICT: 10.0%→11.16% (p=1.000); MODERATE: 15.0%→19.77% (p=0.777); BROAD: 90.0%→76.74% (p=0.272). **Ninguna diferencia es estadísticamente significativa por Fisher exacto**, lo cual contradice la significancia nominal del ITS-MODERATE (ver limitación) |
| Placebo tests | corridos sobre STRICT | **Corregido**: el script original corría los placebo tests sobre `econ_strict_sents`, que hereda la misma degeneración numérica (varios NaN / IRR en el orden de 10⁹). Se re-parametrizó para correr sobre `econ_moderate_sents` (única serie que converge de forma estable). Ver `07_temporal_analysis.py`, `outputs/statistics/placebo_tests_results.json` |
| N documentos pre-2008 | no se reportaba explícitamente | **20 documentos** (16 antes de aplicar el corte year≤2008 usado en el ITS) en 16 años (1992–2008) — base insuficiente para inferencia de series de tiempo interrumpidas en cualquier tier |

### 5b. Verificación de validez del periodo pre-reforma (auditoría 2026-09-22)

Desglose exacto (documentos con año válido, N=450):

| Periodo | N docs | STRICT | MODERATE | BROAD |
|---|---|---|---|---|
| 1992–2007 | 16 | **0** | 1 | 14 |
| solo 2008 | 4 | 2 | 2 | 4 |
| 1992–2008 (periodo "pre" del modelo ITS, `post_2008 = year > 2008`) | 20 | 2 | 3 | 18 |

**Mecanismo exacto de la no identificabilidad del ITS-STRICT** (corregido respecto a una
descripción previa imprecisa): el periodo pre del modelo *no* es enteramente cero — contiene un
único año con casos (2008, n=2 oraciones) justo en el límite del corte. Ajustar una tendencia
exponencial a una serie 0,0,…,0,2 empuja la pendiente pre hacia infinito. La firma numérica lo
confirma: `pre_trend_time` coef = **+7.4742** y `slope_change` coef = **−7.3473** se cancelan casi
exactamente (suma = 0.127), el patrón clásico de un modelo donde solo la suma de dos parámetros
está determinada y cada uno por separado no lo está. No interpretar ninguno de los dos.

**⚠ La "ausencia pre-2008" NO es estadísticamente sorprendente.** Tasa base STRICT post-2008 =
11.16%. Si esa misma tasa hubiera regido en 1992–2007, la probabilidad de observar **cero** casos
en las 16 decisiones disponibles de ese periodo es **0.150** (binomial exacto, one-sided
p = 0.1505). Es decir: los datos son compatibles con una tasa constante durante todo el periodo,
y la ausencia de casos pre-2008 se explica suficientemente por el tamaño minúsculo de la muestra
pre-reforma. **Consecuencia directa: ni siquiera el encuadre descriptivo de "emergencia doctrinal"
puede afirmarse como un patrón que requiera explicación.** El manuscrito debe decir que el corpus
no tiene poder estadístico para distinguir emergencia de tasa constante en el periodo pre-reforma.

**Conclusión metodológica recomendada:** el paper no puede sostener, con el corpus corregido, la
afirmación de un efecto discontinuo causal/cuasi-causal de la Ley 1257 de 2008 sobre el
tratamiento jurisprudencial de la violencia económica. El patrón descriptivo (ausencia casi total
pre-2008, presencia gradual post-2008) es real y reportable, pero el N pre-reforma (20 documentos)
es insuficiente para las pruebas inferenciales que el diseño original pretendía. Recomendado:
degradar la sección "Interrupted Time-Series" de resultado central a análisis exploratorio,
con la comparación de prevalencia (Fisher exacto) como resultado descriptivo principal.

## 6. Diagnósticos del modelo (recalculado, mismo patrón cualitativo)

| Métrica | Publicado | Corregido |
|---|---|---|
| Pearson dispersion STRICT / MODERATE / BROAD | 15.83 (no se especificaba por tier) | 5.68 / 5.53 / 36.13 |
| Durbin-Watson STRICT / MODERATE / BROAD | 1.88 | 2.06 / 2.03 / 2.30 |

Fuente: `outputs/statistics/its_models_results.json`.

## 7. Keyness institucional — **BUG DE CÓDIGO CORREGIDO; el hallazgo SOBREVIVE**

| Término | Publicado (Z) | Recalculado (Z) | IC bootstrap **corregido** |
|---|---|---|---|
| mujeres | 12.21 | 10.768 | [0.559, 1.413] |
| laboral | 8.19 | 7.241 | [0.375, 1.456] |
| acoso | 6.47 | 6.037 | [0.889, 3.363] |

**Bug detectado y corregido en `09_institutional_analysis.py`.** El bootstrap remuestreaba
`rate_cc - rate_oth` (diferencia de frecuencias relativas, escala 0–1) pero el IC resultante se
reportaba junto al `log_odds_ratio` (escala logarítmica, valores 0.4–2.3). Eran **dos estadísticos
distintos**. Síntoma diagnóstico: los 15 términos tenían su estimación puntual **fuera** de su
propio IC (p. ej. "mujeres": punto 0.962, IC reportado [−0.063, 0.083]), lo que es imposible en un
bootstrap correcto. Además los IC erróneos incluían el cero, de modo que un revisor habría
concluido —incorrectamente— que la diferenciación institucional no era significativa.

Corrección aplicada: el bootstrap ahora remuestrea el mismo estadístico que se reporta (log-odds
de Monroe), a nivel documento, con la normalización del prior sobre el vocabulario completo
(parámetro `n_terms_override`, necesario porque `len(k1)` se encogía al pasar solo los 15 términos
top y alteraba el estimando).

**Resultado sustantivo: el hallazgo de diferenciación institucional es VÁLIDO y ROBUSTO.** Con el
bootstrap correcto, **15/15** términos tienen IC 95% que excluye el cero y que contiene su
estimación puntual. Es decir, la distintividad discursiva de la Corte Constitucional resiste el
remuestreo a nivel documento (que sí tiene en cuenta el clustering documental que la fórmula de
varianza de Monroe ignora). Este es ahora el hallazgo empírico **más sólido** del paper y no debe
debilitarse en la reescritura — solo hay que corregir los IC reportados y moderar el lenguaje por
el desbalance de N entre cortes (CC n=287 docs vs CSJ+CE n=64 en el sub-corpus BROAD).

Fuente: `outputs/statistics/institutional_keyness_bootstrap.json`,
`outputs/tables/table_institutional_distinctiveness.csv` (regenerados).

## 8. Word2Vec — estabilidad de vecinos (CAMBIA, degradación notable)

| Constructo | Jaccard@10 publicado | Jaccard@10 recalculado | Estado |
|---|---|---|---|
| violencia_económica | 0.873 | **0.474** | STABLE → **MODERATELY_STABLE** |
| patrimonio | 0.821 | 0.858 | STABLE → STABLE |
| dependencia | 0.520 | **0.349** | ? → **UNSTABLE** |
| violencia_patrimonial | 0.712 | 0.603 | STABLE → STABLE |

**⚠ PROBLEMA DE VALIDEZ, no solo de cifras.** El sub-corpus semántico sobre el que se entrena
Word2Vec tiene **233 oraciones ≈ 20,764 tokens, vocabulario de 4,122 tipos**. Eso está órdenes de
magnitud por debajo de lo necesario para entrenar embeddings distribucionales interpretables
(la mayoría de los tipos aparecen 1–5 veces). La evidencia empírica de que los vectores son ruido
está en los propios "vecinos de consenso" de `violencia_economica`, que son palabras funcionales y
genérico-jurídicas sin relación semántica con el constructo: **"cuanto", "sometida", "señor",
"norma", "tutela"**. Un vecindario semántico válido contendría términos como *patrimonial*,
*alimentos*, *despojo*, *dependencia*.

**Recomendación:** eliminar el análisis Word2Vec del manuscrito, o reportarlo explícitamente como
no concluyente por insuficiencia de datos. Presentar Jaccard@10 = 0.474 como "MODERATELY_STABLE"
sugiere una validación semántica que los datos no soportan, y es precisamente el tipo de
afirmación que el editor pidió revisar. La etiqueta `stability_status` del script es un umbral
arbitrario, no una prueba de validez.

Fuente: `outputs/statistics/word2vec_stability_report.json`.

## 7b. Diferenciación institucional pareada — análisis FALTANTE, ahora computado

**Problema detectado.** El manuscrito (§6) afirma: *"the ordinary jurisdiction (Supreme Court and
Council of State) exhibits significant discursive inertia, remaining anchored in procedural and
property-dissolution language"*. Esa afirmación **nunca se computó**: `09_institutional_analysis.py`
calcula un único contraste (CC vs CSJ+CE agrupadas) y ordena por Z descendente tomando
`head(15)`, de modo que solo se examinó la cola positiva (términos que la CC sobre-utiliza). La
cola negativa —la que caracterizaría a CSJ/CE— nunca se inspeccionó, y no existe ningún cálculo
de keyness propio para la Corte Suprema ni para el Consejo de Estado por separado, pese a que el
abstract promete caracterizar la diferenciación *"across the Constitutional Court, the Supreme
Court of Justice, and the Council of State"*.

**Solución.** Nuevo script `09b_pairwise_institutional_keyness.py`: los tres contrastes pareados,
reportando **ambas colas** de cada uno, con bootstrap a nivel documento (B=1,000) del mismo
estadístico log-odds. Salidas: `outputs/tables/table_institutional_pairwise_keyness.csv`,
`outputs/statistics/institutional_pairwise_keyness.json`.

Robustez: CC vs CE 24/24 términos con IC que excluye 0; CC vs CSJ 19/24; CSJ vs CE 17/24.

**Resultado — cada corte canaliza la violencia económica por su propio aparato doctrinal:**

| Corte | Términos distintivos (IC excluye 0) | Marco doctrinal |
|---|---|---|
| Corte Constitucional | mujeres, derechos, sexual, laboral, discriminación, género, violencia, víctimas | Derechos fundamentales, no discriminación, enfoque de género |
| Corte Suprema de Justicia | dependencia económica, alimentos, liquidación, violencia intrafamiliar, intrafamiliar, económica | Derecho de familia: cuota alimentaria, liquidación de sociedad conyugal, violencia intrafamiliar |
| Consejo de Estado | responsabilidad, responsabilidad patrimonial, culpa, privación, patrimonial, víctima, libertad | Responsabilidad patrimonial del Estado, culpa, privación injusta de la libertad |

**⚠ Esto REFUTA la afirmación de "discursive inertia" del manuscrito.** Los términos distintivos de
la Corte Suprema incluyen **"dependencia económica"**, **"violencia intrafamiliar"** y
**"económica"** — vocabulario sustantivo de violencia económica, no lenguaje meramente procesal.
En el contraste CSJ vs CE, la CSJ se distingue precisamente por *económica* (Z = 3.906, IC
[0.426, 1.617]) y *violencia intrafamiliar* (Z = 3.439, IC [1.023, 4.147]). La jurisdicción
ordinaria **sí** aborda la violencia económica; lo hace desde el derecho de familia y la
responsabilidad estatal en lugar del discurso constitucional de derechos.

El hallazgo correcto no es una jerarquía de compromiso institucional (CC avanzada vs. ordinaria
inerte), sino **canalización doctrinal diferenciada**: tres competencias, tres vocabularios, tres
puertas de entrada al mismo fenómeno. Debe reescribirse §6 en estos términos.

*Nota:* algunos términos distintivos de la CSJ son artefactos de transcripción, no sustantivos
("señor", "sic", "meses" —este último probablemente de cálculos de cuota alimentaria). Excluirlos
de la interpretación y señalarlo en el texto.

## 7c. Las sentencias emblemáticas del análisis cualitativo y el corpus cuantitativo

El manuscrito analiza cualitativamente siete providencias (3 CC, 3 CSJ, 1 CE). Verificación
cruzada contra el corpus:

| Providencia | Estado en el corpus |
|---|---|
| T-967/14 | presente y retenida (`DOC_0577`) |
| SU-201/21 | presente y retenida (`DOC_0916`) |
| T-012/16 | presente y retenida (`DOC_0643`) |
| T-219/23 | presente y retenida (`DOC_0702`) |
| **STC14035-2018** (Corte Suprema) | **AUSENTE del corpus crudo** — 0 coincidencias en los 4,400 archivos |
| **STC16182-2018** (Corte Suprema) | **AUSENTE del corpus crudo** — 0 coincidencias en los 4,400 archivos |

Dos de las tres providencias emblemáticas de la Corte Suprema no están en el corpus cuantitativo.
Esto no invalida la selección cualitativa (fue intencional y basada en la experiencia profesional
de las autoras, según §3), pero **el manuscrito presenta el diseño como secuencial**
—cuantitativo y luego cualitativo—, lo que sugiere que las providencias cualitativas provienen del
corpus. Debe declararse explícitamente que la muestra cualitativa se seleccionó de forma
independiente del corpus computacional, y que dos de sus casos no figuran en él. Esto es
especialmente relevante ahora que la diferenciación institucional pasa a ser el hallazgo central y
la representación de la CSJ en el corpus es limitada.

## 9. Concordancias KWIC (CAMBIA, y resuelve el problema de PII)

| | Publicado | Recalculado |
|---|---|---|
| Viena | n = 47 | recalcular de `outputs/tables/table_concordance_samples.csv` (target_term='viena'), n = 20 |
| Cairo | n = 43 | n = 21 |
| **PII en `table_concordance_samples.csv`** | 4 filas con nombres/cédulas reales (`DOC_0408`, `DOC_0603`, `DOC_0678`) | **0 filas con PII** — los 3 documentos fuente del problema fueron excluidos por el filtro de tipo documental (no eran providencias judiciales). Verificado con regex `\d{1,2}\.\d{3}\.\d{3}` sobre las 349 filas actuales: 0 coincidencias |

## 10. Declaración de datos (CAMBIO ESTRUCTURAL)

| Elemento | Publicado | Corregido |
|---|---|---|
| Declaración de ética/datos | "no new primary data were generated or analyzed; all sources used are available in publicly accessible legal databases" | Inexacto: se construyó un corpus derivado (documentos y oraciones anotadas, clasificación de tipo documental, validación gold). Reemplazar por declaración real de disponibilidad de datos con enlace al repositorio (pendiente Fase 5) |

---

## Resumen ejecutivo para la carta al editor

1. El corpus se redujo de 1,040 a **453** decisiones tras excluir 587 documentos no-judiciales
   o no-Apex-Court (artículos académicos, textos legales/administrativos, 1 archivo roto,
   providencias de tribunales inferiores).
2. El "gold standard" es programático, no anotado independientemente; se reescribe la
   descripción metodológica en consecuencia.
3. El hallazgo central del ITS no es sostenible como estaba planteado: el tier STRICT es
   numéricamente inestable (separación cuasi-perfecta por 0 casos pre-2008) y ni siquiera el
   tier MODERATE resiste una prueba descriptiva simple (Fisher exacto, p=0.777). Se recomienda
   reformular la conclusión central como patrón descriptivo, no como efecto inferencial robusto.
4. El PII detectado en la tabla de concordancias se resolvió automáticamente al excluir sus
   documentos fuente por el filtro de tipo documental.
5. La declaración de datos debe reescribirse para reflejar con precisión el corpus derivado
   construido y su disponibilidad.
