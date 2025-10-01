import pandas as pd
import os

RAW_PATH = os.path.join("data", "googleplaystore.csv")
CLEAN_PATH = os.path.join("data", "googleplaystore_clean.csv")

def load_kaggle_data():
    df = pd.read_csv(RAW_PATH)
    print(f"✅ Loaded raw Google Play data: {df.shape} rows")

    # Remove commas, plus signs, and non-numeric installs
    df["Installs"] = (
        df["Installs"]
        .astype(str)  # ensure it's string first
        .str.replace(",", "", regex=False)
        .str.replace("+", "", regex=False)
        .str.extract(r"(\d+)")  # keep only digits
    )

    # Convert to int, ignoring errors
    df["Installs"] = pd.to_numeric(df["Installs"], errors="coerce")

    # Clean Price column
    df["Price"] = df["Price"].astype(str).str.replace("$", "", regex=False)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0)

    # Fill missing Ratings with 0
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(0)

    # Save cleaned CSV
    df.to_csv(CLEAN_PATH, index=False)
    print(f"✅ Cleaned CSV saved at {CLEAN_PATH}")

if __name__ == "__main__":
    load_kaggle_data()
