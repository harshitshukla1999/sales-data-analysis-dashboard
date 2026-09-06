"""
sales_analysis.py
------------------
Week 2 deliverable: Exploratory analysis + KPI computation + chart generation.

Reads data/sales_data_cleaned.csv and produces:
  - Printed KPI summary (also saved to docs/kpi_summary.txt)
  - PNG charts saved to screenshots/ for the README and dashboard docs:
        monthly_sales_trend.png
        sales_by_category.png
        sales_by_region.png
        top_products.png
        channel_performance.png
        profit_margin_by_category.png

Run from the project root:  python python/sales_analysis.py
"""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "sales_data_cleaned.csv")
IMG_DIR = os.path.join(BASE_DIR, "screenshots")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 120,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
})

COLORS = ["#2563eb", "#7c3aed", "#059669", "#d97706", "#dc2626", "#0891b2"]


def money(ax_axis="y"):
    fmt = mticker.FuncFormatter(lambda x, _: f"₹{x/1e5:,.1f}L" if x >= 1e5 else f"₹{x:,.0f}")
    return fmt


def main():
    df = pd.read_csv(DATA_PATH)
    df["OrderDate"] = pd.to_datetime(df["OrderDate"])

    lines = []
    def log(msg=""):
        print(msg)
        lines.append(msg)

    log("=" * 60)
    log("SALES DATA — KEY PERFORMANCE INDICATORS")
    log("=" * 60)
    total_revenue = df["NetSales"].sum()
    total_profit = df["Profit"].sum()
    total_orders = df["OrderID"].nunique()
    avg_order_value = total_revenue / total_orders
    margin = total_profit / total_revenue * 100

    log(f"Total Revenue        : ₹{total_revenue:,.2f}")
    log(f"Total Profit          : ₹{total_profit:,.2f}")
    log(f"Total Orders          : {total_orders:,}")
    log(f"Average Order Value   : ₹{avg_order_value:,.2f}")
    log(f"Overall Profit Margin : {margin:.2f}%")
    log("")

    log("-- Revenue by Category --")
    cat = df.groupby("Category")["NetSales"].sum().sort_values(ascending=False)
    for k, v in cat.items():
        log(f"  {k:<15} ₹{v:,.2f}  ({v/total_revenue*100:.1f}%)")
    log("")

    log("-- Revenue by Region --")
    reg = df.groupby("Region")["NetSales"].sum().sort_values(ascending=False)
    for k, v in reg.items():
        log(f"  {k:<15} ₹{v:,.2f}")
    log("")

    log("-- Top 5 Products by Revenue --")
    top_products = df.groupby("Product")["NetSales"].sum().sort_values(ascending=False).head(5)
    for k, v in top_products.items():
        log(f"  {k:<20} ₹{v:,.2f}")

    with open(os.path.join(DOCS_DIR, "kpi_summary.txt"), "w") as f:
        f.write("\n".join(lines))

    # ---------------- Charts ----------------

    # 1. Monthly sales trend
    monthly = df.groupby("YearMonth")["NetSales"].sum().reset_index()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(monthly["YearMonth"], monthly["NetSales"], marker="o", color=COLORS[0], linewidth=2)
    ax.fill_between(monthly["YearMonth"], monthly["NetSales"], alpha=0.08, color=COLORS[0])
    ax.set_title("Monthly Sales Trend", fontsize=13, fontweight="bold")
    ax.set_ylabel("Net Sales")
    ax.yaxis.set_major_formatter(money())
    plt.xticks(rotation=60, fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "monthly_sales_trend.png"))
    plt.close()

    # 2. Sales by category (bar)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    cat.sort_values().plot(kind="barh", ax=ax, color=COLORS[1])
    ax.set_title("Total Sales by Category", fontsize=13, fontweight="bold")
    ax.set_xlabel("Net Sales")
    ax.xaxis.set_major_formatter(money())
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "sales_by_category.png"))
    plt.close()

    # 3. Sales by region (donut)
    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        reg.values, labels=reg.index, autopct="%1.1f%%",
        colors=COLORS, wedgeprops=dict(width=0.4), startangle=90
    )
    ax.set_title("Revenue Share by Region", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "sales_by_region.png"))
    plt.close()

    # 4. Top products
    fig, ax = plt.subplots(figsize=(8, 4.5))
    top_products.sort_values().plot(kind="barh", ax=ax, color=COLORS[2])
    ax.set_title("Top 5 Products by Revenue", fontsize=13, fontweight="bold")
    ax.set_xlabel("Net Sales")
    ax.xaxis.set_major_formatter(money())
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "top_products.png"))
    plt.close()

    # 5. Channel performance
    chan = df.groupby("Channel")["NetSales"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    chan.plot(kind="bar", ax=ax, color=COLORS[3])
    ax.set_title("Revenue by Sales Channel", fontsize=13, fontweight="bold")
    ax.set_ylabel("Net Sales")
    ax.yaxis.set_major_formatter(money())
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "channel_performance.png"))
    plt.close()

    # 6. Profit margin by category
    margin_cat = (df.groupby("Category").apply(lambda g: g["Profit"].sum() / g["NetSales"].sum() * 100)
                  .sort_values(ascending=False))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    margin_cat.plot(kind="bar", ax=ax, color=COLORS[4])
    ax.set_title("Profit Margin % by Category", fontsize=13, fontweight="bold")
    ax.set_ylabel("Profit Margin (%)")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "profit_margin_by_category.png"))
    plt.close()

    print(f"\nCharts saved to: {IMG_DIR}")
    print(f"KPI summary saved to: {os.path.join(DOCS_DIR, 'kpi_summary.txt')}")


if __name__ == "__main__":
    main()
