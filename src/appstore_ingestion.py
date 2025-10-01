# src/appstore_ingestion.py
import os
import requests
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

BASE_URL = "https://appstore-scrapper-api.p.rapidapi.com"
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "appstore-scrapper-api.p.rapidapi.com"
}

RAW_JSON = os.path.join("data", "appstore_raw.json")
CLEAN_CSV = os.path.join("data", "appstore_clean.csv")


def get_app_details(app_id):
    url = f"{BASE_URL}/getAppDetail"
    params = {"appId": app_id, "country": "us"}
    r = requests.get(url, headers=HEADERS, params=params)
    return r.json() if r.status_code == 200 else {}


def save_raw_json(data):
    with open(RAW_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Raw App Store JSON saved at {RAW_JSON}")


def clean_appstore_data():
    if not os.path.exists(RAW_JSON):
        print("❌ appstore_raw.json missing!")
        return

    with open(RAW_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data or not isinstance(data, list):
        print("❌ No data found in JSON!")
        return

    df = pd.json_normalize(data)

    # Ensure all expected columns exist
    expected_cols = ["name", "category", "rating", "reviews", "installs", "price"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    # Map columns to match Google schema
    df = df.rename(columns={
        "name": "App",
        "category": "Category",
        "rating": "Rating",
        "reviews": "Reviews",
        "installs": "Installs",
        "price": "Price"
    })

    # Safely convert numeric columns
    for col in ["Rating", "Reviews", "Price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Type column
    df["Type"] = df["Price"].apply(lambda x: "Paid" if x > 0 else "Free")

    df.to_csv(CLEAN_CSV, index=False)
    print(f"✅ Clean App Store CSV saved at {CLEAN_CSV}")


if __name__ == "__main__":
    # Example: fetch one app (replace with multiple in real scenario)
    example_app = get_app_details("284882215")  # Facebook iOS ID
    save_raw_json([example_app])
    clean_appstore_data()
