# src/cleaning.py
import pandas as pd
import os

RAW_PATH = os.path.join("data", "googleplaystore.csv")
CLEAN_PATH = os.path.join("data", "cleaned_googleplaystore.csv")

def clean_kaggle_data():
    df = pd.read_csv(RAW_PATH)
    print("Initial shape:", df.shape)

    # Drop duplicates
    df = df.drop_duplicates()

    # Lenient dropna (only critical columns)
    df = df.dropna(subset=["App", "Category"])

    # Clean 'Installs'
    df["Installs"] = df["Installs"].str.replace("+","",regex=False).str.replace(",","",regex=False)
    df["Installs"] = pd.to_numeric(df["Installs"], errors="coerce").fillna(0).astype(int)

    # Clean 'Size'
    def size_to_mb(x):
        try:
            x = str(x)
            if "M" in x: return float(x.replace("M",""))
            if "k" in x: return float(x.replace("k",""))/1024
            return None
        except: return None
    df["Size"] = df["Size"].apply(size_to_mb)

    # Clean 'Price'
    df["Price"] = df["Price"].str.replace("$","",regex=False)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0.0)

    # Reviews numeric
    df["Reviews"] = pd.to_numeric(df["Reviews"], errors="coerce").fillna(0).astype(int)

    # Type column
    df["Type"] = df["Price"].apply(lambda x: "Paid" if x>0 else "Free")

    print("Final shape:", df.shape)

    df.to_csv(CLEAN_PATH, index=False)
    print(f"✅ Cleaned dataset saved at {CLEAN_PATH}")

if __name__ == "__main__":
    clean_kaggle_data()
