# AI-Powered Market Intelligence

## Author
Yogeswaran S
(yogeswaran00794@gmail.com)

## Project Overview
This project implements an **AI-powered market intelligence system** for analyzing mobile apps and D2C eCommerce performance. It ingests data from multiple sources, cleans and structures it, generates actionable insights using AI/LLM models, and produces comprehensive reports. The system also includes Phase 5 D2C analysis with funnel insights, SEO opportunities, and AI-generated creatives.

## Key Features
- **App Insights**
  - Combines Google Play Store and App Store data
  - Cleans and normalizes app metadata
  - Generates top 10 app rankings, confidence-scored insights, and downloadable reports
- **Phase 5: D2C Insights**
  - Funnel analysis (impressions → clicks → installs → revenue)
  - SEO opportunity detection
  - AI-generated creatives (ad headlines, meta descriptions, PDP text)
- **Interactive Streamlit Interface**
  - Select apps to view insights
  - Explore D2C funnel metrics, SEO, and creatives
  - Download reports in CSV, Markdown, or text formats

## Project Structure
├── data/
│ ├── googleplaystore.csv
│ ├── googleplaystore_clean.csv
│ ├── appstore_clean.csv
│ ├── apps_unified.csv
│ └── Kasparro_Phase5_D2C_Synthetic_Dataset_fixed.xlsx
│
├── outputs/
│ ├── d2c_creatives.txt
│ ├── d2c_insights.json
│ ├── d2c_phase5_cleaned.csv
│ ├── executive_report.md
│ ├── executive_report.pdf
│ ├── executive_report_phase5.md
│ └── insights.json
│
├── notebooks/
│ └── exploration.ipynb
│
├── src/
│ ├── appstore_ingestion.py
│ ├── cleaning.py
│ ├── d2c_phase5.py
│ ├── insights_local.py
│ ├── integration.py
│ ├── interface.py
│ ├── kaggle_ingestion.py
│ └── report_generator.py
│
├── main.py
├── requirements.txt
└── README.md

## Installation

1. Clone the repository:
git clone <https://github.com/Yogeswaran-94/ai-market-intelligence.git>
cd ai_market_intelligence

2. Create and activate a Python virtual environment:
python -m venv venv
venv\Scripts\activate

3. Install dependencies:
pip install -r requirements.txt

4. How to Run
# Step 1: Ingest and clean data
python src/kaggle_ingestion.py
python src/appstore_ingestion.py
python src/cleaning.py

# Step 2: Integrate datasets and generate insights
python src/integration.py
python src/insights_local.py

# Step 3: Phase 5 D2C dataset processing
python src/d2c_phase5.py

# Step 4: Generate reports
python src/report_generator.py

# Step 5: Launch Streamlit dashboard
streamlit run src/interface.py

Navigate through sidebar options:
App Insights – Explore app-level insights and top 10 rankings
Phase 5: D2C Insights – View funnel metrics, SEO opportunities, and AI-generated creatives
Download reports directly from the interface (CSV, Markdown, TXT)

## Data Sources
Google Play Store Dataset (Kaggle) – Metadata for ~10,000 Android apps
App Store Scraper API (RapidAPI) – Real-time App Store data
Synthetic D2C Dataset – Funnel metrics, ad campaign performance, and SEO data

## Outputs
Cleaned datasets (outputs/d2c_phase5_cleaned.csv, outputs/insights.json)
Reports (executive_report.md, executive_report.pdf, executive_report_phase5.md)
AI Creatives (outputs/d2c_creatives.txt)

## Notes
Phase 5 creative outputs are automatically parsed and displayed in the Streamlit interface.
Confidence scores are included with all generated insights.
The system is modular: new datasets or APIs can be integrated easily.

## Requirements
Python 3.10+
Packages listed in requirements.txt (Streamlit, pandas, numpy, requests, etc.)

## License
This project is for educational and assessment purposes.