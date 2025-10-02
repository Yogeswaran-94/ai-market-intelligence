# src/report_generator.py
import pandas as pd
import matplotlib.pyplot as plt
import os

# ---------------- CONFIG ----------------
UNIFIED_CSV = os.path.join("data", "apps_unified.csv")
OUTPUT_DIR = "outputs"
REPORT_MD = os.path.join(OUTPUT_DIR, "executive_report.md")
REPORT_PDF = os.path.join(OUTPUT_DIR, "executive_report.pdf")

# Ensure outputs folder exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- LOAD DATA ----------------
try:
    df = pd.read_csv(UNIFIED_CSV)
    print(f"✅ Loaded data from {UNIFIED_CSV}, total rows: {len(df)}")
except FileNotFoundError:
    print(f"❌ File not found: {UNIFIED_CSV}. Make sure the CSV exists in the data folder.")
    exit()
except Exception as e:
    print(f"❌ Error reading CSV: {e}")
    exit()

# ---------------- GENERATE SUMMARY ----------------
summary = f"# Executive Report\n\nTotal apps: {len(df)}\n\n"

if 'Category' in df.columns:
    summary += "## Top 10 Category distribution\n\n"
    cat_counts = df['Category'].value_counts().head(10)
    summary += cat_counts.to_markdown() + "\n"
else:
    print("⚠️ Column 'Category' not found in CSV")
    cat_counts = pd.Series(dtype=int)

# ---------------- SAVE MARKDOWN ----------------
try:
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"✅ Markdown report saved at {REPORT_MD}")
except Exception as e:
    print(f"❌ Failed to save markdown report: {e}")

# ---------------- GENERATE PDF PLOT ----------------
if not cat_counts.empty:
    try:
        fig, ax = plt.subplots(figsize=(10,6))
        cat_counts.plot(kind='bar', ax=ax, color='skyblue')
        ax.set_title("Top 10 Categories by App Count")
        ax.set_ylabel("Number of Apps")
        ax.set_xlabel("Category")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(REPORT_PDF)
        plt.close()
        print(f"✅ PDF report saved at {REPORT_PDF}")
    except Exception as e:
        print(f"❌ Failed to generate PDF report: {e}")
else:
    print("⚠️ No category data available to generate PDF plot")
