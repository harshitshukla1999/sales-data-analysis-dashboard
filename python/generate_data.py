"""
generate_data.py
-----------------
Creates a synthetic, realistic e-commerce sales dataset for the project.
Produces two files:
  - data/sales_data_raw.csv        (messy: missing values, bad dates, dupes, case issues)
  - data/sales_data_clean_reference.csv  (the underlying clean ground truth)

Run from the project root:  python python/generate_data.py
"""
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

np.random.seed(42)
random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

categories = {
    "Electronics": ["Wireless Mouse", "Bluetooth Speaker", "USB-C Hub", "Laptop Stand", "Webcam HD", "Power Bank"],
    "Furniture": ["Office Chair", "Standing Desk", "Bookshelf", "Filing Cabinet", "Desk Lamp"],
    "Apparel": ["Cotton T-Shirt", "Denim Jacket", "Running Shoes", "Wool Sweater", "Rain Jacket"],
    "Groceries": ["Organic Coffee", "Green Tea Pack", "Almond Butter", "Olive Oil", "Granola Bars"],
    "Stationery": ["Notebook Set", "Gel Pens Pack", "Sticky Notes", "Whiteboard", "Desk Organizer"],
}

regions = ["North", "South", "East", "West", "Central"]
cities = {
    "North": ["Delhi", "Chandigarh", "Lucknow"],
    "South": ["Bengaluru", "Chennai", "Hyderabad"],
    "East": ["Kolkata", "Patna", "Bhubaneswar"],
    "West": ["Mumbai", "Pune", "Ahmedabad"],
    "Central": ["Bhopal", "Nagpur", "Raipur"],
}
channels = ["Online", "Retail Store", "Distributor"]
payment_modes = ["Credit Card", "UPI", "Net Banking", "Cash on Delivery", "Debit Card"]
customer_segments = ["Individual", "Small Business", "Enterprise"]

start_date = datetime(2024, 1, 1)
end_date = datetime(2025, 12, 31)
days = (end_date - start_date).days

n_rows = 6000
rows = []
order_id_start = 100001

for i in range(n_rows):
    order_id = order_id_start + i
    rand_day = random.randint(0, days)
    order_date = start_date + timedelta(days=rand_day)

    month = order_date.month
    seasonal_multiplier = 1.0
    if month in (11, 12):
        seasonal_multiplier = 1.6
    elif month in (6, 7):
        seasonal_multiplier = 1.25
    elif month in (1, 2):
        seasonal_multiplier = 0.85

    category = random.choice(list(categories.keys()))
    product = random.choice(categories[category])
    region = random.choice(regions)
    city = random.choice(cities[region])
    channel = random.choices(channels, weights=[0.55, 0.30, 0.15])[0]
    payment = random.choice(payment_modes)
    segment = random.choices(customer_segments, weights=[0.6, 0.3, 0.1])[0]

    base_price = {
        "Electronics": random.uniform(800, 6000),
        "Furniture": random.uniform(2000, 15000),
        "Apparel": random.uniform(400, 3000),
        "Groceries": random.uniform(150, 900),
        "Stationery": random.uniform(80, 700),
    }[category]

    unit_price = round(base_price, 2)
    quantity = max(1, int(np.random.poisson(3) * seasonal_multiplier))
    discount_pct = round(random.choice([0, 0, 0, 5, 10, 15, 20]) / 100, 2)
    gross_sales = round(unit_price * quantity, 2)
    discount_amt = round(gross_sales * discount_pct, 2)
    net_sales = round(gross_sales - discount_amt, 2)
    unit_cost = round(unit_price * random.uniform(0.55, 0.75), 2)
    total_cost = round(unit_cost * quantity, 2)
    profit = round(net_sales - total_cost, 2)

    customer_id = f"CUST{random.randint(1000, 4999)}"

    rows.append([
        order_id, order_date.strftime("%Y-%m-%d"), customer_id, segment, region, city,
        channel, category, product, quantity, unit_price, discount_pct, gross_sales,
        discount_amt, net_sales, unit_cost, total_cost, profit, payment
    ])

columns = [
    "OrderID", "OrderDate", "CustomerID", "CustomerSegment", "Region", "City",
    "Channel", "Category", "Product", "Quantity", "UnitPrice", "DiscountPct",
    "GrossSales", "DiscountAmount", "NetSales", "UnitCost", "TotalCost", "Profit",
    "PaymentMode"
]

df = pd.DataFrame(rows, columns=columns)

# ---- Inject realistic messiness for the "raw" version ----
raw = df.copy()

for col, frac in [("City", 0.02), ("PaymentMode", 0.015), ("DiscountPct", 0.01), ("CustomerSegment", 0.01)]:
    idx = raw.sample(frac=frac, random_state=1).index
    raw.loc[idx, col] = np.nan

alt_idx = raw.sample(frac=0.05, random_state=2).index
def messy_date(d):
    dt = datetime.strptime(d, "%Y-%m-%d")
    fmt = random.choice(["%d/%m/%Y", "%m-%d-%Y", "%d-%b-%Y"])
    return dt.strftime(fmt)
raw.loc[alt_idx, "OrderDate"] = raw.loc[alt_idx, "OrderDate"].apply(messy_date)

case_idx = raw.sample(frac=0.04, random_state=3).index
raw.loc[case_idx, "Category"] = raw.loc[case_idx, "Category"].str.upper()
space_idx = raw.sample(frac=0.03, random_state=4).index
raw.loc[space_idx, "Region"] = " " + raw.loc[space_idx, "Region"] + "  "

dupes = raw.sample(n=40, random_state=5)
raw = pd.concat([raw, dupes], ignore_index=True)

bad_idx = raw.sample(n=15, random_state=6).index
raw.loc[bad_idx, "Quantity"] = -1

raw = raw.sample(frac=1, random_state=7).reset_index(drop=True)

raw.to_csv(os.path.join(DATA_DIR, "sales_data_raw.csv"), index=False)
df.to_csv(os.path.join(DATA_DIR, "sales_data_clean_reference.csv"), index=False)

print(f"Raw rows: {len(raw)}")
print(f"Clean reference rows: {len(df)}")
