# src/d2c_phase5.py
import os
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from transformers import pipeline

# ---------- CONFIG ----------
BASE_DIR = Path(__file__).resolve().parents[1]  # project root (one above src/)
DATA_DIR = BASE_DIR / "data"
EXCEL_FILENAME = "Kasparro_Phase5_D2C_Synthetic_Dataset_fixed.xlsx"
EXCEL_PATH = DATA_DIR / EXCEL_FILENAME

OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

CLEANED_CSV = OUTPUTS_DIR / "d2c_phase5_cleaned.csv"
INSIGHTS_JSON = OUTPUTS_DIR / "d2c_insights.json"
CREATIVES_TXT = OUTPUTS_DIR / "d2c_creatives.txt"
REPORT_MD = OUTPUTS_DIR / "executive_report_phase5.md"

# HF model for creatives (free)
HF_MODEL = "google/flan-t5-base"

# ---------- UTIL ----------
def find_col(df, candidates):
    """Return first column name in df.columns that matches any candidate (case-insensitive)."""
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    return None

def safe_div(a, b):
    return a / b if b not in (0, None, np.nan) else np.nan

def z_to_confidence(z):
    """Convert absolute z-score to a confidence measure between 0.5 and 0.99.
       Higher |z| -> higher confidence (more unusual/strong signal)."""
    if np.isnan(z):
        return 0.5
    a = min(6.0, abs(z))  # cap
    # map 0..6 -> 0.5..0.99
    return round(0.5 + (a / 6.0) * 0.49, 2)

# ---------- LOAD ----------
print("Loading D2C dataset...")

if not EXCEL_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {EXCEL_PATH}")

# read sheet1 robustly
try:
    d2c_df = pd.read_excel(EXCEL_PATH, sheet_name="Sheet1")
except Exception:
    # try reading first sheet
    d2c_df = pd.read_excel(EXCEL_PATH, sheet_name=0)

print("Columns in Sheet1:", list(d2c_df.columns))

# normalize column names (trim + lowercase)
d2c_df.columns = [c.strip() for c in d2c_df.columns]
lower_map = {c: c.lower().strip() for c in d2c_df.columns}
d2c_df = d2c_df.rename(columns=lower_map)

# ---------- MAP/VERIFY REQUIRED COLUMNS ----------
# expected logical columns (lowercase)
expected = {
    "spend_usd": ["spend_usd", "spend", "ad_spend", "cost_usd"],
    "impressions": ["impressions", "imps"],
    "clicks": ["clicks"],
    "installs": ["installs"],
    "signups": ["signups"],
    "first_purchase": ["first_purchase", "purchases", "conversions"],
    "repeat_purchase": ["repeat_purchase", "repeat_purchases"],
    "revenue_usd": ["revenue_usd", "revenue", "revenue_usd_total"],
    "seo_category": ["seo_category", "category", "seo_cat"],
    "avg_position": ["avg_position", "average_position", "avg_pos"],
    "monthly_search_volume": ["monthly_search_volume", "search_volume", "monthly_searches"],
    "conversion_rate": ["conversion_rate", "conv_rate"],
    "campaign_id": ["campaign_id", "campaign"],
    "channel": ["channel", "traffic_channel"]
}

col_map = {}
for logical, candidates in expected.items():
    found = None
    for cand in candidates:
        if cand in d2c_df.columns:
            found = cand
            break
    if found:
        col_map[logical] = found

# Ensure minimal set
minimal_needed = ["spend_usd", "clicks", "impressions", "revenue_usd", "first_purchase", "repeat_purchase", "monthly_search_volume", "avg_position", "conversion_rate", "seo_category"]
missing = [m for m in minimal_needed if m not in col_map]
if missing:
    print("Warning: some expected columns not found automatically:", missing)
    # continue but code will handle missing gracefully by filling zeros/nans

# rename to canonical column names
d2c_df = d2c_df.rename(columns={col_map[k]: k for k in col_map})

# Fill missing numeric columns with zeros/nans as appropriate
numeric_cols = ["spend_usd", "impressions", "clicks", "installs", "signups", "first_purchase", "repeat_purchase", "revenue_usd", "avg_position", "monthly_search_volume", "conversion_rate"]
for c in numeric_cols:
    if c in d2c_df.columns:
        # coerce to numeric
        d2c_df[c] = pd.to_numeric(d2c_df[c], errors="coerce")
    else:
        d2c_df[c] = np.nan

# make sure seo_category exists
if "seo_category" not in d2c_df.columns:
    d2c_df["seo_category"] = "Unknown"

# ---------- CLEANING ----------
# Replace obviously wrong values (like percent strings) in conversion_rate
d2c_df["conversion_rate"] = d2c_df["conversion_rate"].apply(lambda x: float(str(x).strip("%"))/100 if isinstance(x, str) and "%" in x else x)
# small sanity: impressions/clicks integers
for c in ["impressions", "clicks", "installs", "first_purchase", "repeat_purchase"]:
    d2c_df[c] = pd.to_numeric(d2c_df[c], errors="coerce").fillna(0).astype(float)

# ---------- METRICS ----------
print("Calculating funnel metrics...")

# CTR, CVR (installs per click), CAC (cost per first_purchase), ROAS, LTV proxy, retention
d2c_df["ctr"] = d2c_df.apply(lambda r: safe_div(r["clicks"], r["impressions"]), axis=1)
d2c_df["cvr_click_to_install"] = d2c_df.apply(lambda r: safe_div(r["installs"], r["clicks"]), axis=1)
# conversions for CAC: use first_purchase (if missing fallback to installs)
d2c_df["conversions_for_cac"] = d2c_df["first_purchase"].where(d2c_df["first_purchase"] > 0, d2c_df["installs"])
d2c_df["cac_usd"] = d2c_df.apply(lambda r: safe_div(r["spend_usd"], r["conversions_for_cac"]), axis=1)
d2c_df["roas"] = d2c_df.apply(lambda r: safe_div(r["revenue_usd"], r["spend_usd"]), axis=1)
d2c_df["ltv_per_install"] = d2c_df.apply(lambda r: safe_div(r["revenue_usd"], r["installs"]), axis=1)
d2c_df["repeat_rate"] = d2c_df.apply(lambda r: safe_div(r["repeat_purchase"], r["first_purchase"]), axis=1)

# ---------- AGGREGATIONS & SEO OPPORTUNITY ----------
print("Calculating SEO opportunity scores...")

# opportunity score: monthly_search_volume * conversion_rate / (avg_position + 1)
d2c_df["opportunity_score"] = d2c_df.apply(
    lambda r: safe_div(r["monthly_search_volume"] * (r["conversion_rate"] if not math.isnan(r["conversion_rate"]) else 0), (r["avg_position"] + 1) if not math.isnan(r["avg_position"]) else 1),
    axis=1
)

seo_agg = d2c_df.groupby("seo_category").agg({
    "monthly_search_volume": "sum",
    "avg_position": "mean",
    "conversion_rate": "mean",
    "opportunity_score": "sum",
    "spend_usd": "sum",
    "revenue_usd": "sum"
}).reset_index().sort_values("opportunity_score", ascending=False)

# ---------- INSIGHTS & CONFIDENCE ----------
print("Deriving insights and confidence scores...")

insights = {"summary": {}, "categories": {}}

# Dataset-level stats
def stats_series(s):
    s = s.dropna()
    return {"mean": float(s.mean()) if len(s) else None, "std": float(s.std(ddof=0)) if len(s) else None}

# compute z-scores per metric for each category to generate confidences
metrics_for_conf = ["opportunity_score", "roas", "cac_usd", "ltv_per_install", "repeat_rate"]
for metric in metrics_for_conf:
    if metric in d2c_df.columns:
        insights["summary"][metric] = stats_series(d2c_df[metric])

# Per-category insights
for _, row in seo_agg.iterrows():
    cat = row["seo_category"]
    cat_rows = d2c_df[d2c_df["seo_category"] == cat]
    # compute category metrics
    cat_metrics = {
        "monthly_search_volume": float(row["monthly_search_volume"]),
        "avg_position": float(row["avg_position"]) if not math.isnan(row["avg_position"]) else None,
        "conversion_rate": float(row["conversion_rate"]) if not math.isnan(row["conversion_rate"]) else None,
        "opportunity_score": float(row["opportunity_score"]),
        "total_spend_usd": float(row["spend_usd"]),
        "total_revenue_usd": float(row["revenue_usd"])
    }
    # confidence scoring via z-scores vs dataset distribution
    cat_conf = {}
    for metric in ["opportunity_score", "roas", "cac_usd", "ltv_per_install", "repeat_rate"]:
        if metric in d2c_df.columns:
            series = d2c_df[metric]
            if series.notna().sum() > 1:
                mean = series.mean()
                std = series.std(ddof=0) if series.std(ddof=0) > 0 else 1.0
                cat_val = cat_rows[metric].mean() if len(cat_rows) else np.nan
                z = (cat_val - mean) / std if not np.isnan(cat_val) else np.nan
                cat_conf[metric] = {"value": float(cat_val) if not np.isnan(cat_val) else None, "z": float(z) if not np.isnan(z) else None, "confidence": z_to_confidence(z)}
            else:
                cat_conf[metric] = {"value": None, "z": None, "confidence": 0.5}
    insights["categories"][cat] = {"metrics": cat_metrics, "confidence": cat_conf}

# ---------- SAVE CLEANED DATA ----------
print("Saving cleaned dataset and insights...")

# cleaned CSV
d2c_df.to_csv(CLEANED_CSV, index=False)

# insights JSON
with open(INSIGHTS_JSON, "w", encoding="utf-8") as f:
    json.dump(insights, f, ensure_ascii=False, indent=2)

# ---------- GENERATE CREATIVES (HF Flan-T5) ----------
print("Generating AI-powered creatives... (HuggingFace model:", HF_MODEL, ")")
# Use text2text pipeline for Flan-T5:
gen = pipeline("text2text-generation", model=HF_MODEL)

top_categories = list(seo_agg["seo_category"].head(3).astype(str).values)
creatives = []

for cat in top_categories:
    prompt = (
        f"You are a marketing copywriter. Produce 3 short, distinct ad headlines (<= 12 words), "
        f"1 SEO meta description (max 160 chars), and 1 product page benefit sentence for a D2C brand in the category: {cat}. "
        "Keep language action-oriented and customer-focused. Return JSON with fields: headlines (list), meta, pdp."
    )
    out = gen(prompt, max_length=180)[0]["generated_text"]
    # best-effort: keep text as-is and store; we do not parse strict JSON from the model.
    creatives.append({"category": cat, "raw_output": out})

# write creatives file
with open(CREATIVES_TXT, "w", encoding="utf-8") as f:
    for item in creatives:
        f.write(f"=== Category: {item['category']} ===\n")
        f.write(item["raw_output"].strip() + "\n\n")

# ---------- EXECUTIVE REPORT (Markdown) ----------
print("Writing executive report (markdown)...")
report_lines = []
report_lines.append("# Executive Report — Phase 5: D2C Funnel & SEO Insights\n")
report_lines.append("## Summary\n")
report_lines.append(f"- Rows processed: {len(d2c_df):,}\n")
report_lines.append(f"- Top SEO opportunities (by computed opportunity_score):\n")

for _, r in seo_agg.head(10).reset_index(drop=True).iterrows():
    report_lines.append(f"- **{r['seo_category']}** — opportunity_score: {r['opportunity_score']:.1f}, monthly_search_volume: {r['monthly_search_volume']:.0f}, avg_position: {r['avg_position']:.2f}\n")

report_lines.append("\n## Top category recommendations\n")
for cat in top_categories:
    cat_ins = insights["categories"].get(cat, {})
    report_lines.append(f"### {cat}\n")
    report_lines.append(f"- Opportunity score: {cat_ins.get('metrics',{}).get('opportunity_score', 'N/A')}\n")
    # include confidence for opportunity_score if present
    conf_obj = cat_ins.get("confidence", {}).get("opportunity_score", {})
    if conf_obj:
        report_lines.append(f"- Confidence (opportunity_score): {conf_obj.get('confidence')}\n")
    report_lines.append("\n")

report_lines.append("## Creatives (generated)\n")
for item in creatives:
    report_lines.append(f"### {item['category']}\n```\n{item['raw_output'].strip()}\n```\n")

report_lines.append("\n## Files produced\n")
report_lines.append(f"- Cleaned CSV: `{CLEANED_CSV}`\n")
report_lines.append(f"- Insights JSON: `{INSIGHTS_JSON}`\n")
report_lines.append(f"- Creatives TXT: `{CREATIVES_TXT}`\n")

with open(REPORT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

# ---------- PRINT SUMMARY ----------
print("\n--- Done ---")
print(f"Cleaned data saved: {CLEANED_CSV}")
print(f"Insights JSON saved: {INSIGHTS_JSON}")
print(f"Creatives saved: {CREATIVES_TXT}")
print(f"Executive report (markdown): {REPORT_MD}")

# show top seo table snippet
print("\nTop 5 SEO opportunities:")
print(seo_agg[["seo_category", "monthly_search_volume", "avg_position", "conversion_rate", "opportunity_score"]].head(5).to_string(index=False))
