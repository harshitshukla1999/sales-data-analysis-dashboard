"""
build_excel.py
---------------
Builds the final Excel deliverable: excel/Sales_Dashboard.xlsx

Sheets created:
  1. ReadMe            - how to use the workbook
  2. RawData           - the cleaned dataset as a formatted Excel Table
  3. Summary_Category  - SUMIFS/COUNTIFS pivot-style summary + chart
  4. Summary_Region    - SUMIFS pivot-style summary + chart
  5. Summary_Monthly   - monthly trend summary + line chart
  6. Summary_Channel   - channel performance summary + chart
  7. Summary_Products  - top 10 products summary + chart
  8. Dashboard         - KPI cards, a Region "slicer" dropdown driving
                         SUMIFS-based KPIs, and all six charts laid out
                         together as the interactive dashboard.

All calculations use live formulas (SUMIFS / COUNTIFS / AVERAGEIFS /
IFERROR) referencing the RawData table, so the workbook recalculates
whenever the underlying data changes — nothing is hardcoded.

Run from the project root:  python python/build_excel.py
"""
import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, NamedStyle
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.chart import LineChart, BarChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import ColorScaleRule

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "sales_data_cleaned.csv")
OUT_PATH = os.path.join(BASE_DIR, "excel", "Sales_Dashboard.xlsx")

FONT_NAME = "Arial"
NAVY = "1F2937"
BLUE = "2563EB"
LIGHT_BLUE = "DBEAFE"
GREEN = "059669"
WHITE = "FFFFFF"
GREY = "F3F4F6"

header_font = Font(name=FONT_NAME, size=10, bold=True, color=WHITE)
header_fill = PatternFill("solid", fgColor=NAVY)
title_font = Font(name=FONT_NAME, size=16, bold=True, color=NAVY)
subtitle_font = Font(name=FONT_NAME, size=10, italic=True, color="6B7280")
kpi_label_font = Font(name=FONT_NAME, size=10, bold=True, color="6B7280")
kpi_value_font = Font(name=FONT_NAME, size=15, bold=True, color=NAVY)
body_font = Font(name=FONT_NAME, size=10)
thin_border = Border(*(Side(style="thin", color="D1D5DB"),) * 4)


def style_header_row(ws, row, n_cols):
    for c in range(1, n_cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border


def autofit(ws, widths):
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def kpi_card(ws, cell_row, cell_col, label, formula, number_format="#,##0"):
    label_cell = ws.cell(row=cell_row, column=cell_col, value=label)
    label_cell.font = kpi_label_font
    value_cell = ws.cell(row=cell_row + 1, column=cell_col, value=formula)
    value_cell.font = kpi_value_font
    value_cell.number_format = number_format


def main():
    df = pd.read_csv(DATA_PATH)

    wb = Workbook()

    # =========================================================
    # 1. ReadMe sheet
    # =========================================================
    ws = wb.active
    ws.title = "ReadMe"
    ws["B2"] = "Sales Data Analysis & Dashboard"
    ws["B2"].font = Font(name=FONT_NAME, size=18, bold=True, color=NAVY)
    ws["B3"] = "Project 1 — Excel/Power BI style workbook (Excel-only implementation)"
    ws["B3"].font = subtitle_font

    readme_lines = [
        ("How this workbook is organized", True),
        ("RawData", "The full cleaned dataset (5,985 orders) as an Excel Table named 'SalesTable'."),
        ("Summary_Category", "Revenue/profit/orders by product category — feeds the category chart."),
        ("Summary_Region", "Revenue/profit/orders by region — feeds the region chart."),
        ("Summary_Monthly", "Month-by-month revenue trend — feeds the seasonal trend line chart."),
        ("Summary_Channel", "Revenue by sales channel (Online / Retail Store / Distributor)."),
        ("Summary_Products", "Top 10 products by revenue."),
        ("Dashboard", "The interactive dashboard: KPI cards + all charts + a Region filter dropdown."),
        ("", ""),
        ("How the interactivity works", True),
        ("Region filter", "Cell C5 on the Dashboard sheet is a dropdown (data validation). "
                           "Choose 'All' or a specific region and the KPI cards recalculate "
                           "instantly using SUMIFS formulas against RawData — no macros needed."),
        ("Everything is formula-driven", "Every number in Summary_* and Dashboard sheets is a "
                                          "SUMIFS/COUNTIFS/AVERAGEIFS formula referencing RawData. "
                                          "Update or extend RawData and the whole workbook recalculates."),
        ("", ""),
        ("Source data", True),
        ("Rows", f"{len(df):,} cleaned transactions, Jan 2024 – Dec 2025 (synthetic sample data)."),
        ("Cleaning steps", "See python/data_cleaning.py in the project repo for the full "
                            "reproducible cleaning pipeline (missing values, mixed date formats, "
                            "duplicates, invalid quantities)."),
    ]
    r = 5
    for label, val in readme_lines:
        if val is True:
            ws.cell(row=r, column=2, value=label).font = Font(name=FONT_NAME, size=12, bold=True, color=BLUE)
            r += 1
            continue
        if label == "" and val == "":
            r += 1
            continue
        ws.cell(row=r, column=2, value=label).font = Font(name=FONT_NAME, size=10, bold=True)
        ws.cell(row=r, column=3, value=val).font = body_font
        ws.cell(row=r, column=3).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = 30
        r += 1
    autofit(ws, {"A": 2, "B": 22, "C": 90})

    # =========================================================
    # 2. RawData sheet
    # =========================================================
    ws_raw = wb.create_sheet("RawData")
    cols = list(df.columns)
    ws_raw.append(cols)
    for row in df.itertuples(index=False):
        ws_raw.append(list(row))
    style_header_row(ws_raw, 1, len(cols))
    n_rows = len(df) + 1
    last_col_letter = get_column_letter(len(cols))
    table_ref = f"A1:{last_col_letter}{n_rows}"
    table = Table(displayName="SalesTable", ref=table_ref)
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2", showRowStripes=True, showFirstColumn=False
    )
    ws_raw.add_table(table)
    widths = {get_column_letter(i + 1): max(11, len(c) + 2) for i, c in enumerate(cols)}
    autofit(ws_raw, widths)
    ws_raw.freeze_panes = "A2"

    # column letter lookup for RawData
    col_idx = {name: get_column_letter(i + 1) for i, name in enumerate(cols)}

    # =========================================================
    # 3. Summary_Category
    # =========================================================
    ws_cat = wb.create_sheet("Summary_Category")
    categories = sorted(df["Category"].unique())
    headers = ["Category", "Revenue", "Profit", "Orders", "Avg Order Value", "% of Total Revenue"]
    ws_cat.append(headers)
    style_header_row(ws_cat, 1, len(headers))
    for i, cat in enumerate(categories, start=2):
        ws_cat.cell(row=i, column=1, value=cat)
        rev_formula = f'=SUMIFS(RawData!{col_idx["NetSales"]}:{col_idx["NetSales"]},RawData!{col_idx["Category"]}:{col_idx["Category"]},A{i})'
        profit_formula = f'=SUMIFS(RawData!{col_idx["Profit"]}:{col_idx["Profit"]},RawData!{col_idx["Category"]}:{col_idx["Category"]},A{i})'
        orders_formula = f'=COUNTIFS(RawData!{col_idx["Category"]}:{col_idx["Category"]},A{i})'
        ws_cat.cell(row=i, column=2, value=rev_formula).number_format = "#,##0"
        ws_cat.cell(row=i, column=3, value=profit_formula).number_format = "#,##0"
        ws_cat.cell(row=i, column=4, value=orders_formula).number_format = "#,##0"
        ws_cat.cell(row=i, column=5, value=f"=IFERROR(B{i}/D{i},0)").number_format = "#,##0"
        ws_cat.cell(row=i, column=6, value=f"=IFERROR(B{i}/SUM($B$2:$B${len(categories)+1}),0)").number_format = "0.0%"
    last_row = len(categories) + 1
    ws_cat.append(["Total",
                    f"=SUM(B2:B{last_row})", f"=SUM(C2:C{last_row})", f"=SUM(D2:D{last_row})",
                    f"=IFERROR(B{last_row+1}/D{last_row+1},0)", f"=SUM(F2:F{last_row})"])
    for c in range(1, 7):
        ws_cat.cell(row=last_row + 1, column=c).font = Font(name=FONT_NAME, bold=True)
    autofit(ws_cat, {"A": 16, "B": 14, "C": 14, "D": 10, "E": 16, "F": 18})

    cat_chart = BarChart()
    cat_chart.title = "Revenue by Category"
    cat_chart.style = 10
    cat_chart.y_axis.title = "Net Sales (₹)"
    data = Reference(ws_cat, min_col=2, min_row=1, max_row=last_row)
    cats_ref = Reference(ws_cat, min_col=1, min_row=2, max_row=last_row)
    cat_chart.add_data(data, titles_from_data=True)
    cat_chart.set_categories(cats_ref)
    cat_chart.width, cat_chart.height = 16, 9
    ws_cat.add_chart(cat_chart, "H2")

    # =========================================================
    # 4. Summary_Region
    # =========================================================
    ws_reg = wb.create_sheet("Summary_Region")
    regions = sorted(df["Region"].unique())
    ws_reg.append(["Region", "Revenue", "Profit", "Orders"])
    style_header_row(ws_reg, 1, 4)
    for i, reg in enumerate(regions, start=2):
        ws_reg.cell(row=i, column=1, value=reg)
        ws_reg.cell(row=i, column=2,
                     value=f'=SUMIFS(RawData!{col_idx["NetSales"]}:{col_idx["NetSales"]},RawData!{col_idx["Region"]}:{col_idx["Region"]},A{i})').number_format = "#,##0"
        ws_reg.cell(row=i, column=3,
                     value=f'=SUMIFS(RawData!{col_idx["Profit"]}:{col_idx["Profit"]},RawData!{col_idx["Region"]}:{col_idx["Region"]},A{i})').number_format = "#,##0"
        ws_reg.cell(row=i, column=4,
                     value=f'=COUNTIFS(RawData!{col_idx["Region"]}:{col_idx["Region"]},A{i})').number_format = "#,##0"
    last_row_r = len(regions) + 1
    autofit(ws_reg, {"A": 14, "B": 14, "C": 14, "D": 10})

    reg_chart = PieChart()
    reg_chart.title = "Revenue Share by Region"
    data = Reference(ws_reg, min_col=2, min_row=1, max_row=last_row_r)
    cats_ref = Reference(ws_reg, min_col=1, min_row=2, max_row=last_row_r)
    reg_chart.add_data(data, titles_from_data=True)
    reg_chart.set_categories(cats_ref)
    reg_chart.dataLabels = DataLabelList()
    reg_chart.dataLabels.showPercent = True
    reg_chart.width, reg_chart.height = 14, 9
    ws_reg.add_chart(reg_chart, "F2")

    # =========================================================
    # 5. Summary_Monthly
    # =========================================================
    ws_mon = wb.create_sheet("Summary_Monthly")
    months = sorted(df["YearMonth"].unique())
    ws_mon.append(["YearMonth", "Revenue", "Orders"])
    style_header_row(ws_mon, 1, 3)
    for i, ym in enumerate(months, start=2):
        ws_mon.cell(row=i, column=1, value=ym)
        ws_mon.cell(row=i, column=2,
                     value=f'=SUMIFS(RawData!{col_idx["NetSales"]}:{col_idx["NetSales"]},RawData!{col_idx["YearMonth"]}:{col_idx["YearMonth"]},A{i})').number_format = "#,##0"
        ws_mon.cell(row=i, column=3,
                     value=f'=COUNTIFS(RawData!{col_idx["YearMonth"]}:{col_idx["YearMonth"]},A{i})').number_format = "#,##0"
    last_row_m = len(months) + 1
    autofit(ws_mon, {"A": 14, "B": 14, "C": 10})

    mon_chart = LineChart()
    mon_chart.title = "Monthly Sales Trend"
    mon_chart.style = 12
    mon_chart.y_axis.title = "Net Sales (₹)"
    data = Reference(ws_mon, min_col=2, min_row=1, max_row=last_row_m)
    cats_ref = Reference(ws_mon, min_col=1, min_row=2, max_row=last_row_m)
    mon_chart.add_data(data, titles_from_data=True)
    mon_chart.set_categories(cats_ref)
    for s in mon_chart.series:
        s.smooth = False
    mon_chart.width, mon_chart.height = 20, 9
    ws_mon.add_chart(mon_chart, "E2")

    # =========================================================
    # 6. Summary_Channel
    # =========================================================
    ws_chan = wb.create_sheet("Summary_Channel")
    channels = sorted(df["Channel"].unique())
    ws_chan.append(["Channel", "Revenue", "Orders", "Avg Order Value"])
    style_header_row(ws_chan, 1, 4)
    for i, ch in enumerate(channels, start=2):
        ws_chan.cell(row=i, column=1, value=ch)
        ws_chan.cell(row=i, column=2,
                      value=f'=SUMIFS(RawData!{col_idx["NetSales"]}:{col_idx["NetSales"]},RawData!{col_idx["Channel"]}:{col_idx["Channel"]},A{i})').number_format = "#,##0"
        ws_chan.cell(row=i, column=3,
                      value=f'=COUNTIFS(RawData!{col_idx["Channel"]}:{col_idx["Channel"]},A{i})').number_format = "#,##0"
        ws_chan.cell(row=i, column=4, value=f"=IFERROR(B{i}/C{i},0)").number_format = "#,##0"
    last_row_c = len(channels) + 1
    autofit(ws_chan, {"A": 16, "B": 14, "C": 10, "D": 16})

    chan_chart = BarChart()
    chan_chart.type = "col"
    chan_chart.title = "Revenue by Sales Channel"
    data = Reference(ws_chan, min_col=2, min_row=1, max_row=last_row_c)
    cats_ref = Reference(ws_chan, min_col=1, min_row=2, max_row=last_row_c)
    chan_chart.add_data(data, titles_from_data=True)
    chan_chart.set_categories(cats_ref)
    chan_chart.width, chan_chart.height = 14, 9
    ws_chan.add_chart(chan_chart, "F2")

    # =========================================================
    # 7. Summary_Products (Top 10 by revenue, computed in pandas for ranking
    #    but expressed as live SUMIFS formulas)
    # =========================================================
    ws_prod = wb.create_sheet("Summary_Products")
    top10 = df.groupby("Product")["NetSales"].sum().sort_values(ascending=False).head(10).index.tolist()
    ws_prod.append(["Product", "Revenue", "Units Sold"])
    style_header_row(ws_prod, 1, 3)
    for i, p in enumerate(top10, start=2):
        ws_prod.cell(row=i, column=1, value=p)
        ws_prod.cell(row=i, column=2,
                      value=f'=SUMIFS(RawData!{col_idx["NetSales"]}:{col_idx["NetSales"]},RawData!{col_idx["Product"]}:{col_idx["Product"]},A{i})').number_format = "#,##0"
        ws_prod.cell(row=i, column=3,
                      value=f'=SUMIFS(RawData!{col_idx["Quantity"]}:{col_idx["Quantity"]},RawData!{col_idx["Product"]}:{col_idx["Product"]},A{i})').number_format = "#,##0"
    last_row_p = len(top10) + 1
    autofit(ws_prod, {"A": 20, "B": 14, "C": 12})

    prod_chart = BarChart()
    prod_chart.type = "bar"
    prod_chart.title = "Top 10 Products by Revenue"
    data = Reference(ws_prod, min_col=2, min_row=1, max_row=last_row_p)
    cats_ref = Reference(ws_prod, min_col=1, min_row=2, max_row=last_row_p)
    prod_chart.add_data(data, titles_from_data=True)
    prod_chart.set_categories(cats_ref)
    prod_chart.width, prod_chart.height = 16, 10
    ws_prod.add_chart(prod_chart, "E2")

    # =========================================================
    # 8. Dashboard
    # =========================================================
    ws_dash = wb.create_sheet("Dashboard", 1)
    ws_dash.sheet_view.showGridLines = False
    ws_dash["B2"] = "Sales Performance Dashboard"
    ws_dash["B2"].font = title_font
    ws_dash["B3"] = "Filter by region below — every KPI recalculates live via SUMIFS."
    ws_dash["B3"].font = subtitle_font

    ws_dash["B5"] = "Region Filter:"
    ws_dash["B5"].font = kpi_label_font
    ws_dash["C5"] = "All"
    ws_dash["C5"].font = Font(name=FONT_NAME, bold=True, color=BLUE, size=11)
    ws_dash["C5"].fill = PatternFill("solid", fgColor=LIGHT_BLUE)
    ws_dash["C5"].alignment = Alignment(horizontal="center")
    dv = DataValidation(type="list", formula1='"All,North,South,East,West,Central"', allow_blank=False)
    ws_dash.add_data_validation(dv)
    dv.add(ws_dash["C5"])

    region_col = col_idx["Region"]
    sales_col = col_idx["NetSales"]
    profit_col = col_idx["Profit"]
    orderid_col = col_idx["OrderID"]

    def region_sumif(target_col):
        return (f'=IF($C$5="All",SUM(RawData!{target_col}:{target_col}),'
                f'SUMIFS(RawData!{target_col}:{target_col},RawData!{region_col}:{region_col},$C$5))')

    # KPI cards row
    kpi_card(ws_dash, 8, 2, "TOTAL REVENUE", region_sumif(sales_col), "₹#,##0")
    kpi_card(ws_dash, 8, 4, "TOTAL PROFIT", region_sumif(profit_col), "₹#,##0")
    kpi_card(ws_dash, 8, 6,
              "TOTAL ORDERS",
              f'=IF($C$5="All",COUNT(RawData!{orderid_col}:{orderid_col}),'
              f'COUNTIFS(RawData!{region_col}:{region_col},$C$5))', "#,##0")
    kpi_card(ws_dash, 8, 8, "PROFIT MARGIN",
              f'=IFERROR(D9/B9,0)', "0.0%")
    # Note: D9 = profit value cell, B9 = revenue value cell (row 9 holds the KPI values)

    for col in (2, 4, 6, 8):
        for rr in (8, 9):
            ws_dash.cell(row=rr, column=col).border = Border(bottom=Side(style="medium", color=BLUE))

    # Embed the 5 charts from summary sheets by copying references directly onto the dashboard
    dash_cat_chart = BarChart()
    dash_cat_chart.title = "Revenue by Category"
    data = Reference(ws_cat, min_col=2, min_row=1, max_row=last_row)
    cats_ref = Reference(ws_cat, min_col=1, min_row=2, max_row=last_row)
    dash_cat_chart.add_data(data, titles_from_data=True)
    dash_cat_chart.set_categories(cats_ref)
    dash_cat_chart.width, dash_cat_chart.height = 15, 8.5
    ws_dash.add_chart(dash_cat_chart, "B12")

    dash_reg_chart = PieChart()
    dash_reg_chart.title = "Revenue Share by Region"
    data = Reference(ws_reg, min_col=2, min_row=1, max_row=last_row_r)
    cats_ref = Reference(ws_reg, min_col=1, min_row=2, max_row=last_row_r)
    dash_reg_chart.add_data(data, titles_from_data=True)
    dash_reg_chart.set_categories(cats_ref)
    dash_reg_chart.dataLabels = DataLabelList()
    dash_reg_chart.dataLabels.showPercent = True
    dash_reg_chart.width, dash_reg_chart.height = 15, 8.5
    ws_dash.add_chart(dash_reg_chart, "J12")

    dash_mon_chart = LineChart()
    dash_mon_chart.title = "Monthly Sales Trend"
    data = Reference(ws_mon, min_col=2, min_row=1, max_row=last_row_m)
    cats_ref = Reference(ws_mon, min_col=1, min_row=2, max_row=last_row_m)
    dash_mon_chart.add_data(data, titles_from_data=True)
    dash_mon_chart.set_categories(cats_ref)
    dash_mon_chart.width, dash_mon_chart.height = 15, 8.5
    ws_dash.add_chart(dash_mon_chart, "B29")

    dash_chan_chart = BarChart()
    dash_chan_chart.type = "col"
    dash_chan_chart.title = "Revenue by Channel"
    data = Reference(ws_chan, min_col=2, min_row=1, max_row=last_row_c)
    cats_ref = Reference(ws_chan, min_col=1, min_row=2, max_row=last_row_c)
    dash_chan_chart.add_data(data, titles_from_data=True)
    dash_chan_chart.set_categories(cats_ref)
    dash_chan_chart.width, dash_chan_chart.height = 15, 8.5
    ws_dash.add_chart(dash_chan_chart, "J29")

    dash_prod_chart = BarChart()
    dash_prod_chart.type = "bar"
    dash_prod_chart.title = "Top 10 Products by Revenue"
    data = Reference(ws_prod, min_col=2, min_row=1, max_row=last_row_p)
    cats_ref = Reference(ws_prod, min_col=1, min_row=2, max_row=last_row_p)
    dash_prod_chart.add_data(data, titles_from_data=True)
    dash_prod_chart.set_categories(cats_ref)
    dash_prod_chart.width, dash_prod_chart.height = 15, 8.5
    ws_dash.add_chart(dash_prod_chart, "B46")

    autofit(ws_dash, {"A": 2, "B": 22, "C": 12, "D": 22, "E": 12, "F": 22, "G": 12, "H": 22})

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    wb.save(OUT_PATH)
    print(f"Workbook saved -> {OUT_PATH}")


if __name__ == "__main__":
    main()
