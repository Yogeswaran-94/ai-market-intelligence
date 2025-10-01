# src/interface.py
import streamlit as st
import pandas as pd
import json

# -----------------------------
# Helper Functions
# -----------------------------

def parse_number(x):
    """Convert strings like '3.0M' or '5K' to integers."""
    if isinstance(x, (int, float)):
        return int(x)
    x = str(x).upper().replace(',', '').strip()
    if x.endswith('M'):
        return int(float(x[:-1]) * 1_000_000)
    elif x.endswith('K'):
        return int(float(x[:-1]) * 1_000)
    elif x == '' or x == 'N/A':
        return 0
    else:
        try:
            return int(float(x))
        except:
            return 0

def load_insights(json_path="outputs/insights.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for app, info in data.items():
        info['reviews'] = parse_number(info.get('reviews', 0))
        info['installs'] = parse_number(info.get('installs', 0))
        info['price'] = float(info.get('price', 0.0))
        info['rating'] = float(info.get('rating', 0.0))
    return data

def generate_markdown_report(top_apps):
    md = "# AI-Powered Market Insights Report\n\n"
    md += "## Top Apps by Rating\n\n"
    md += "| App Name | Category | Rating | Reviews | Installs | Price |\n"
    md += "|----------|---------|-------|--------|---------|-------|\n"
    for app, info in top_apps.items():
        md += f"| {app} | {info['category']} | {info['rating']} | {info['reviews']:,} | {info['installs']:,} | ${info['price']:.2f} |\n"
    md += "\n## Detailed Insights\n\n"
    for app, info in top_apps.items():
        md += f"### {app}\n"
        md += "\n".join(f"- {line}" for line in info.get('insights', [])) + "\n"
        md += f"- Confidence: {int(info.get('confidence',0)*100)}%\n\n"
    return md

def load_creatives(file_path="d2c.creatives.txt"):
    creatives = []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().split("=== Category:")
    for block in lines[1:]:
        parts = block.split("===")
        category = parts[0].strip()
        content = parts[1].strip() if len(parts) > 1 else ""
        content_parts = [x.strip() for x in content.split(",")]
        creative = {
            "category": category,
            "headlines": content_parts[0] if len(content_parts) > 0 else "",
            "meta": content_parts[1] if len(content_parts) > 1 else "",
            "pdp": content_parts[2] if len(content_parts) > 2 else ""
        }
        creatives.append(creative)
    return creatives

# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(page_title="AI-Powered Market Intelligence", layout="wide")
st.title("📊 AI-Powered Market Intelligence")

# Sidebar for navigation
section = st.sidebar.selectbox("Select Section", ["App Insights", "Phase 5: D2C Insights"])

if section == "App Insights":
    st.subheader("Select an app to see key insights")
    insights_data = load_insights("outputs/insights.json")
    app_list = sorted(insights_data.keys())
    selected_app = st.selectbox("Select an App", app_list)
    
    if selected_app:
        app_info = insights_data[selected_app]
        st.markdown(f"**App Name:** {selected_app}")
        st.markdown(f"**Category:** {app_info['category']}")
        st.markdown(f"**Rating:** {app_info['rating']}")
        st.markdown(f"**Reviews:** {app_info['reviews']:,}")
        st.markdown(f"**Installs:** {app_info['installs']:,}")
        st.markdown(f"**Price:** ${app_info['price']:.2f}")
        
        st.subheader("Generated Market Insights")
        for line in app_info.get("insights", []):
            st.write(f"• {line}")
        st.markdown(f"**Confidence:** {int(app_info.get('confidence',0)*100)}%")
    
    # Top 10 apps table
    st.subheader("🌟 Top 10 Apps by Rating")
    top_10_apps = dict(sorted(insights_data.items(), key=lambda x: x[1]['rating'], reverse=True)[:10])
    top_table = pd.DataFrame([
        {
            "App Name": app,
            "Category": info['category'],
            "Rating": info['rating'],
            "Reviews": info['reviews'],
            "Installs": info['installs'],
            "Price": info['price']
        } for app, info in top_10_apps.items()
    ])
    st.dataframe(top_table.style.format({
        "Reviews": "{:,}",
        "Installs": "{:,}",
        "Price": "${:.2f}"
    }))
    md_report = generate_markdown_report(top_10_apps)
    st.download_button("📥 Download Markdown Report", md_report, "executive_report.md", "text/markdown")

elif section == "Phase 5: D2C Insights":
    d2c_view = st.selectbox("Phase 5 Views", ["Funnel Insights", "SEO Opportunities", "AI Creatives", "Raw D2C Data"])
    d2c_data = pd.read_csv("d2c_phase5_cleaned.csv")
    
    if d2c_view == "Funnel Insights":
        st.subheader("📈 D2C Funnel Metrics")
        metrics = {
            "spend_usd": d2c_data['spend_usd'].sum(),
            "impressions": d2c_data['impressions'].sum(),
            "clicks": d2c_data['clicks'].sum(),
            "installs": d2c_data['installs'].sum(),
            "signups": d2c_data['signups'].sum(),
            "first_purchase": d2c_data['first_purchase'].sum(),
            "repeat_purchase": d2c_data['repeat_purchase'].sum(),
            "revenue_usd": d2c_data['revenue_usd'].sum()
        }
        for k, v in metrics.items():
            st.metric(k.replace("_"," ").title(), f"{v:,.0f}")
        st.download_button("📥 Download Phase 5 D2C Report", d2c_data.to_csv(index=False), "phase5_d2c_report.csv", "text/csv")
    
    elif d2c_view == "SEO Opportunities":
        st.subheader("🔍 SEO Opportunities")
        seo_cols = ["seo_category", "avg_position", "monthly_search_volume"]
        st.dataframe(d2c_data[seo_cols])
        st.download_button("📥 Download SEO Opportunities", d2c_data[seo_cols].to_csv(index=False), "seo_opportunities.csv", "text/csv")
    
    elif d2c_view == "AI Creatives":
        st.subheader("💡 AI-Generated Creative Outputs")
        creatives = load_creatives("d2c.creatives.txt")
        for i, creative in enumerate(creatives, 1):
            st.markdown(f"**Creative #{i}**")
            st.markdown(f"=== Category: {creative['category']} ===")
            st.write("Headlines:", creative['headlines'])
            st.write("Meta:", creative['meta'])
            st.write("PDP:", creative['pdp'])
        st.download_button("📥 Download AI Creatives", open("d2c.creatives.txt","r").read(), "d2c_creatives.txt", "text/plain")
    
    elif d2c_view == "Raw D2C Data":
        st.subheader("📊 Cleaned D2C Dataset")
        st.dataframe(d2c_data)
        st.download_button("📥 Download Raw D2C Data", d2c_data.to_csv(index=False), "d2c_phase5_cleaned.csv", "text/csv")
