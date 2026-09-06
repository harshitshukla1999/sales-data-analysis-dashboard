"""
data_cleaning.py
-----------------
Week 1 deliverable: Cleans and preprocesses the raw sales dataset.

Steps performed:
  1. Load raw CSV.
  2. Standardize text fields (trim whitespace, fix casing).
  3. Parse inconsistent date formats into a single YYYY-MM-DD format.
  4. Handle missing values (impute / flag, based on column).
  5. Remove duplicate orders.
  6. Remove/flag invalid records (e.g. negative quantities).
  7. Add derived date columns (Year, Month, MonthName, Quarter) used later
     for seasonal-trend analysis.
  8. Save the cleaned dataset to data/sales_data_cleaned.csv.

Run from the project root:  python python/data_cleaning.py
"""
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

RAW_PATH = os.path.join(DATA_DIR, "sales_data_raw.csv")
CLEAN_PATH = os.path.join(DATA_DIR, "sales_data_cleaned.csv")


def parse_mixed_dates(series: pd.Series) -> pd.Series:
    """Parse a column containing multiple date formats into datetime64."""
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%d-%b-%Y"]
    parsed = pd.Series(pd.NaT, index=series.index)
    remaining = series.copy()
    for fmt in formats:
        mask = parsed.isna() & remaining.notna()
        try:
            attempt = pd.to_datetime(remaining[mask], format=fmt, errors="coerce")
        except ValueError:
            continue
        parsed.loc[mask] = attempt
    return parsed


def clean_sales_data(raw_path: str = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(raw_path)
    print(f"Loaded raw data: {df.shape[0]} rows, {df.shape[1]} columns")

    # 1. Standardize text fields --------------------------------------------------
    text_cols = ["CustomerSegment", "Region", "City", "Channel", "Category", "Product", "PaymentMode"]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": pd.NA})
    df["Category"] = df["Category"].str.title()
    df["Region"] = df["Region"].str.title()

    # 2. Parse mixed date formats --------------------------------------------------
    df["OrderDate"] = parse_mixed_dates(df["OrderDate"])
    before = len(df)
    df = df.dropna(subset=["OrderDate"])
    print(f"Dropped {before - len(df)} rows with unparseable dates")

    # 3. Handle missing values -------------------------------------------------------
    # City: fill with "Unknown" (region is still usable for aggregation)
    df["City"] = df["City"].fillna("Unknown")
    # PaymentMode: fill with the most frequent mode
    df["PaymentMode"] = df["PaymentMode"].fillna(df["PaymentMode"].mode()[0])
    # CustomerSegment: fill with "Individual" (majority class)
    df["CustomerSegment"] = df["CustomerSegment"].fillna("Individual")
    # DiscountPct: missing implies no discount was recorded/applied
    df["DiscountPct"] = df["DiscountPct"].fillna(0)

    # 4. Remove duplicate orders -------------------------------------------------------
    before = len(df)
    df = df.drop_duplicates(subset=["OrderID"], keep="first")
    print(f"Removed {before - len(df)} duplicate order rows")

    # 5. Remove invalid records -------------------------------------------------------
    before = len(df)
    df = df[df["Quantity"] > 0]
    print(f"Removed {before - len(df)} rows with invalid (non-positive) quantity")

    # 6. Recompute financial fields to guarantee internal consistency -----------------
    df["GrossSales"] = (df["UnitPrice"] * df["Quantity"]).round(2)
    df["DiscountAmount"] = (df["GrossSales"] * df["DiscountPct"]).round(2)
    df["NetSales"] = (df["GrossSales"] - df["DiscountAmount"]).round(2)
    df["TotalCost"] = (df["UnitCost"] * df["Quantity"]).round(2)
    df["Profit"] = (df["NetSales"] - df["TotalCost"]).round(2)
    df["ProfitMarginPct"] = (df["Profit"] / df["NetSales"]).round(4)

    # 7. Derived date columns for trend analysis ---------------------------------------
    df["Year"] = df["OrderDate"].dt.year
    df["Month"] = df["OrderDate"].dt.month
    df["MonthName"] = df["OrderDate"].dt.strftime("%b")
    df["YearMonth"] = df["OrderDate"].dt.strftime("%Y-%m")
    df["Quarter"] = df["OrderDate"].dt.quarter.map(lambda q: f"Q{q}")
    df["OrderDate"] = df["OrderDate"].dt.strftime("%Y-%m-%d")

    # 8. Final column order -------------------------------------------------------------
    ordered_cols = [
        "OrderID", "OrderDate", "Year", "Quarter", "Month", "MonthName", "YearMonth",
        "CustomerID", "CustomerSegment", "Region", "City", "Channel",
        "Category", "Product", "Quantity", "UnitPrice", "DiscountPct",
        "GrossSales", "DiscountAmount", "NetSales", "UnitCost", "TotalCost",
        "Profit", "ProfitMarginPct", "PaymentMode",
    ]
    df = df[ordered_cols].sort_values("OrderID").reset_index(drop=True)
    return df


if __name__ == "__main__":
    cleaned = clean_sales_data()
    cleaned.to_csv(CLEAN_PATH, index=False)
    print(f"\nSaved cleaned dataset -> {CLEAN_PATH}")
    print(f"Final shape: {cleaned.shape[0]} rows, {cleaned.shape[1]} columns")
    missing = cleaned.isna().sum()
    missing = missing[missing > 0]
    print("\nMissing values per column:")
    print(missing if not missing.empty else "None")
