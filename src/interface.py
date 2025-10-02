# src/interface.py
import streamlit as st
import pandas as pd
import json
import os
import altair as alt

# -----------------------------
# Helper Functions
# -----------------------------
def parse_number(x):
    """Convert strings like '3.0M' or '5K' to integers."""
    try:
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
            return int(float(x))
    except:
        return 0

def load_insights(json_path="outputs/insights.json"):
    """Load insights JSON safely."""
    if not os.path.exists(json_path):
        st.warning(f"Insights JSON not found: {json_path}")
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for app, info in data.items():
            info['category'] = str(info.get('category', 'Unknown'))
            try:
                info['rating'] = min(float(info.get('rating', 0.0)), 5.0)
            except:
                info['rating'] = 0.0
            info['reviews'] = parse_number(info.get('reviews', 0))
            info['installs'] = parse_number(info.get('installs', 0))
            try:
                info['price'] = float(info.get('price', 0.0))
            except:
                info['price'] = 0.0
        return data
    except Exception as e:
        st.error(f"Failed to load insights JSON: {e}")
        return {}

def generate_markdown_report(top_apps):
    """Generate markdown report for top apps."""
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

def load_creatives(file_path="outputs/d2c_creatives.txt"):
    """Load AI-generated creatives safely."""
    if not os.path.exists(file_path):
        st.warning(f"Creatives file not found: {file_path}")
        return []

    try:
        creatives = []
        with open(file_path, "r", encoding="utf-8") as f:
            blocks = f.read().split("=== Category:")

        for block in blocks[1:]:
            parts = block.split("===")
            category = parts[0].strip()
            content = parts[1].strip() if len(parts) > 1 else ""
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            headlines, meta, pdp = "", "", ""
            for line in lines:
                if line.lower().startswith("headlines:"):
                    headlines = line[len("headlines:"):].strip()
                elif line.lower().startswith("meta:"):
                    meta = line[len("meta:"):].strip()
                elif line.lower().startswith("pdp:"):
                    pdp = line[len("pdp:"):].strip()
            creatives.append({
                "category": category,
                "headlines": headlines,
                "meta": meta,
                "pdp": pdp
            })
        return creatives
    except Exception as e:
        st.error(f"Failed to load AI creatives: {e}")
        return []

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="AI-Powered Market Intelligence", layout="wide")
st.title("📊 AI-Powered Market Intelligence")

# Sidebar
section = st.sidebar.selectbox("Select Section", ["App Insights", "Phase 5: D2C Insights"])

# -----------------------------
# App Insights
# -----------------------------
if section == "App Insights":
    st.subheader("Select an app to see key insights")
    insights_data = load_insights("outputs/insights.json")
    if not insights_data:
        st.warning("No insights data available.")
    else:
        app_list = sorted(insights_data.keys())
        selected_app = st.selectbox("Select an App", app_list)
        if selected_app:
            try:
                info = insights_data[selected_app]
                st.markdown(f"**App Name:** {selected_app}")
                st.markdown(f"**Category:** {info.get('category','Unknown')}")
                st.markdown(f"**Rating:** {info.get('rating',0):.1f}")
                st.markdown(f"**Reviews:** {info.get('reviews',0):,}")
                st.markdown(f"**Installs:** {info.get('installs',0):,}")
                st.markdown(f"**Price:** ${info.get('price',0):.2f}")

                st.subheader("Generated Market Insights")
                for line in info.get("insights", ["No insights available."]):
                    st.write(f"• {line}")

                st.markdown(f"**Confidence:** {int(info.get('confidence',0)*100)}%")
            except Exception as e:
                st.error(f"Error displaying app info: {e}")

        # Display Top 10 Apps Table
        try:
            st.subheader("🌟 Top 10 Apps by Rating")
            top_10 = dict(sorted(insights_data.items(), key=lambda x: x[1]['rating'], reverse=True)[:10])
            df_top = pd.DataFrame([{
                "App Name": app,
                "Category": info['category'],
                "Rating": info['rating'],
                "Reviews": info['reviews'],
                "Installs": info['installs'],
                "Price": info['price']
            } for app, info in top_10.items()])
            st.dataframe(df_top.style.format({
                "Reviews": "{:,}",
                "Installs": "{:,}",
                "Price": "${:.2f}"
            }))
            md_report = generate_markdown_report(top_10)
            st.download_button("📥 Download Markdown Report", md_report, "executive_report.md", "text/markdown")
        except Exception as e:
            st.error(f"Error displaying Top 10 Apps: {e}")

# -----------------------------
# Phase 5: D2C Insights
# -----------------------------
elif section == "Phase 5: D2C Insights":
    d2c_view = st.selectbox("Phase 5 Views", ["Funnel Insights", "SEO Opportunities", "AI Creatives", "Raw D2C Data"])
    csv_path = "outputs/d2c_phase5_cleaned.csv"
    try:
        d2c_data = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to load D2C CSV: {e}")
        d2c_data = pd.DataFrame()

    # Funnel Insights
    if d2c_view == "Funnel Insights":
        st.subheader("📈 D2C Funnel Metrics")
        try:
            if not d2c_data.empty:
                metrics = {k: d2c_data[k].sum() for k in ["impressions","clicks","installs","signups","first_purchase","repeat_purchase","spend_usd","revenue_usd"]}
                for k,v in metrics.items():
                    st.metric(k, f"{v:,.0f}")
                funnel_df = pd.DataFrame({
                    "Stage": ["Impressions","Clicks","Installs","Signups","First Purchase","Repeat Purchase"],
                    "Value": [metrics["impressions"], metrics["clicks"], metrics["installs"], metrics["signups"], metrics["first_purchase"], metrics["repeat_purchase"]]
                })
                st.altair_chart(alt.Chart(funnel_df).mark_bar().encode(x='Stage', y='Value'), use_container_width=True)
                st.download_button("📥 Download Phase 5 D2C Report", d2c_data.to_csv(index=False), "phase5_d2c_report.csv", "text/csv")
            else:
                st.info("No D2C data available.")
        except Exception as e:
            st.error(f"Error displaying Funnel Insights: {e}")

    # SEO Opportunities
    elif d2c_view == "SEO Opportunities":
        st.subheader("🔍 SEO Opportunities")
        try:
            if not d2c_data.empty:
                seo_cols = ["seo_category", "avg_position", "monthly_search_volume"]
                st.dataframe(d2c_data[seo_cols])
                seo_chart = alt.Chart(d2c_data).mark_bar().encode(
                    x=alt.X('seo_category', sort='-y'), y='monthly_search_volume'
                )
                st.altair_chart(seo_chart, use_container_width=True)
                st.download_button("📥 Download SEO Opportunities", d2c_data[seo_cols].to_csv(index=False), "seo_opportunities.csv", "text/csv")
            else:
                st.info("No SEO data available.")
        except Exception as e:
            st.error(f"Error displaying SEO Opportunities: {e}")

    # AI Creatives
    elif d2c_view == "AI Creatives":
        st.subheader("💡 AI-Generated Creative Outputs")
        try:
            creatives = load_creatives("outputs/d2c_creatives.txt")
            if creatives:
                for i, c in enumerate(creatives, 1):
                    st.markdown(f"**Creative #{i} — Category: {c['category']}**")
                    st.markdown(f"- **Headlines:** {c['headlines']}")
                    st.markdown(f"- **Meta:** {c['meta']}")
                    st.markdown(f"- **PDP:** {c['pdp']}")
                with open("outputs/d2c_creatives.txt", "r", encoding="utf-8") as f:
                    st.download_button("📥 Download AI Creatives", f.read(), "d2c_creatives.txt", "text/plain")
            else:
                st.info("No AI creatives available.")
        except Exception as e:
            st.error(f"Error displaying AI Creatives: {e}")

    # Raw D2C Data
    elif d2c_view == "Raw D2C Data":
        st.subheader("📊 Cleaned D2C Dataset")
        try:
            if not d2c_data.empty:
                st.dataframe(d2c_data)
                st.download_button("📥 Download Raw D2C Data", d2c_data.to_csv(index=False), "d2c_phase5_cleaned.csv", "text/csv")
            else:
                st.info("No raw D2C data available.")
        except Exception as e:
            st.error(f"Error displaying raw D2C data: {e}")
