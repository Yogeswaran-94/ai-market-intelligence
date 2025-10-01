# src/report_generator.py
import os
import pandas as pd
import json
import matplotlib.pyplot as plt
from fpdf import FPDF

# Paths
COMBINED_CSV = os.path.join("data", "combined_apps.csv")
INSIGHTS_JSON = os.path.join("outputs", "insights.json")
REPORT_MD = os.path.join("outputs", "executive_report.md")
REPORT_PDF = os.path.join("outputs", "executive_report.pdf")

# Load data
df = pd.read_csv(COMBINED_CSV)
with open(INSIGHTS_JSON, "r") as f:
    insights = json.load(f)

# Create basic charts
os.makedirs("outputs", exist_ok=True)

# 1. Top 10 Categories by App Count
category_counts = df['Category'].value_counts().head(10)
plt.figure(figsize=(8,5))
category_counts.plot(kind='bar')
plt.title("Top 10 App Categories by Count")
plt.ylabel("Number of Apps")
plt.tight_layout()
plt.savefig("outputs/category_chart.png")
plt.close()

# 2. Free vs Paid Apps
type_counts = df['Type'].value_counts()
plt.figure(figsize=(6,4))
type_counts.plot(kind='pie', autopct='%1.1f%%', startangle=90)
plt.title("Free vs Paid Apps")
plt.tight_layout()
plt.savefig("outputs/type_chart.png")
plt.close()

# Generate Markdown Report
with open(REPORT_MD, "w") as f:
    f.write("# AI-Powered Market Intelligence Report\n\n")
    f.write("## Dataset Summary\n")
    f.write(f"- Total Apps: {len(df)}\n")
    f.write(f"- Categories: {df['Category'].nunique()}\n")
    f.write(f"- Platforms: {df['Platform'].unique().tolist()}\n\n")
    f.write("## Charts\n")
    f.write("![Category Chart](category_chart.png)\n")
    f.write("![Free vs Paid](type_chart.png)\n\n")
    f.write("## AI Insights\n")
    for i, item in enumerate(insights, 1):
        f.write(f"### Insight {i}\n")
        f.write(f"- **Insight:** {item['insight']}\n")
        f.write(f"- **Confidence:** {item['confidence']}\n")
        f.write(f"- **Recommendation:** {item['recommendation']}\n\n")

print(f"✅ Markdown report saved at {REPORT_MD}")

# Convert Markdown to PDF (simple)
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("Arial", 'B', 16)
pdf.multi_cell(0, 10, "AI-Powered Market Intelligence Report\n\n")

pdf.set_font("Arial", '', 12)
pdf.multi_cell(0, 8, f"Dataset Summary:\n- Total Apps: {len(df)}\n- Categories: {df['Category'].nunique()}\n- Platforms: {df['Platform'].unique().tolist()}\n\n")

pdf.multi_cell(0, 8, "AI Insights:\n")
for i, item in enumerate(insights, 1):
    pdf.multi_cell(0, 8, f"{i}. Insight: {item['insight']}\n   Confidence: {item['confidence']}\n   Recommendation: {item['recommendation']}\n")

pdf.output(REPORT_PDF)
print(f"✅ PDF report saved at {REPORT_PDF}")
