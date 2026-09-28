"""Recomputes headline statistics of the manuscript from the published derived data."""
import pandas as pd
from scipy.stats import fisher_exact
from sklearn.metrics import precision_score, recall_score, f1_score
d = pd.read_parquet("data/documents.parquet")
print("Documents by court:", d.court.value_counts().to_dict(), "| total", len(d))
print("Sentences:", len(pd.read_parquet("data/sentences_metadata.parquet")))
d = d[d.decision_year.notna()]; pre = d.decision_year <= 2008
print("\nPre/post-2008 document prevalence (Fisher's exact test)")
for t in ["strict", "moderate", "broad"]:
    c = f"has_econ_{t}"; a, b = int(d[pre][c].sum()), int(pre.sum()); e, f = int(d[~pre][c].sum()), int((~pre).sum())
    print(f"  {t:9s} pre {a}/{b}  post {e}/{f}  p = {fisher_exact([[a, b - a], [e, f - e]])[1]:.3f}")
g = pd.read_parquet("data/validation_sample.parquet")
print("\nRule-based validation sample (N = %d)" % len(g))
for t in ["strict", "moderate", "broad"]:
    y, p = g.gold_label, g[f"is_econ_{t}"].astype(int)
    print(f"  {t:9s} P = {precision_score(y, p):.3f}  R = {recall_score(y, p):.3f}  F1 = {f1_score(y, p):.3f}")