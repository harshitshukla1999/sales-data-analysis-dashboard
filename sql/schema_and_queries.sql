-- =====================================================================
--  Sales Data Analysis — SQL Schema & KPI Queries
--  Compatible with SQLite / MySQL / PostgreSQL (minor dialect tweaks
--  noted inline where relevant). Built for the sales_data_cleaned table.
-- =====================================================================

-- -----------------------------------------------------------------
-- 1. SCHEMA
-- -----------------------------------------------------------------
DROP TABLE IF EXISTS sales;

CREATE TABLE sales (
    OrderID          INTEGER PRIMARY KEY,
    OrderDate        TEXT NOT NULL,          -- YYYY-MM-DD
    Year             INTEGER,
    Quarter          TEXT,
    Month            INTEGER,
    MonthName        TEXT,
    YearMonth        TEXT,
    CustomerID       TEXT,
    CustomerSegment  TEXT,
    Region           TEXT,
    City             TEXT,
    Channel          TEXT,
    Category         TEXT,
    Product          TEXT,
    Quantity         INTEGER,
    UnitPrice        REAL,
    DiscountPct      REAL,
    GrossSales       REAL,
    DiscountAmount   REAL,
    NetSales         REAL,
    UnitCost         REAL,
    TotalCost        REAL,
    Profit           REAL,
    ProfitMarginPct  REAL,
    PaymentMode      TEXT
);

-- Load data (SQLite CLI example):
-- .mode csv
-- .import data/sales_data_cleaned.csv sales --skip 1

-- -----------------------------------------------------------------
-- 2. KEY PERFORMANCE INDICATORS (KPIs)
-- -----------------------------------------------------------------

-- 2.1 Total Revenue, Profit, Orders, Avg Order Value
SELECT
    ROUND(SUM(NetSales), 2)                        AS TotalRevenue,
    ROUND(SUM(Profit), 2)                          AS TotalProfit,
    COUNT(DISTINCT OrderID)                        AS TotalOrders,
    ROUND(SUM(NetSales) * 1.0 / COUNT(DISTINCT OrderID), 2) AS AvgOrderValue,
    ROUND(SUM(Profit) * 100.0 / SUM(NetSales), 2)  AS OverallProfitMarginPct
FROM sales;

-- 2.2 Sales by Category (revenue driver identification)
SELECT
    Category,
    ROUND(SUM(NetSales), 2)   AS Revenue,
    ROUND(SUM(Profit), 2)     AS Profit,
    COUNT(DISTINCT OrderID)   AS Orders,
    ROUND(SUM(NetSales) * 100.0 / (SELECT SUM(NetSales) FROM sales), 2) AS PctOfTotalRevenue
FROM sales
GROUP BY Category
ORDER BY Revenue DESC;

-- 2.3 Monthly Sales Trend (seasonality)
SELECT
    YearMonth,
    ROUND(SUM(NetSales), 2) AS Revenue,
    COUNT(DISTINCT OrderID) AS Orders
FROM sales
GROUP BY YearMonth
ORDER BY YearMonth;

-- 2.4 Sales by Region
SELECT
    Region,
    ROUND(SUM(NetSales), 2) AS Revenue,
    ROUND(SUM(Profit), 2)   AS Profit,
    COUNT(DISTINCT OrderID) AS Orders
FROM sales
GROUP BY Region
ORDER BY Revenue DESC;

-- 2.5 Top 10 Products by Revenue
SELECT
    Product,
    Category,
    ROUND(SUM(NetSales), 2)   AS Revenue,
    SUM(Quantity)             AS UnitsSold
FROM sales
GROUP BY Product, Category
ORDER BY Revenue DESC
LIMIT 10;

-- 2.6 Sales Channel Performance
SELECT
    Channel,
    ROUND(SUM(NetSales), 2)  AS Revenue,
    ROUND(AVG(NetSales), 2)  AS AvgOrderValue,
    COUNT(DISTINCT OrderID)  AS Orders
FROM sales
GROUP BY Channel
ORDER BY Revenue DESC;

-- 2.7 Customer Segment Contribution
SELECT
    CustomerSegment,
    ROUND(SUM(NetSales), 2) AS Revenue,
    COUNT(DISTINCT CustomerID) AS UniqueCustomers,
    ROUND(SUM(NetSales) * 1.0 / COUNT(DISTINCT CustomerID), 2) AS RevenuePerCustomer
FROM sales
GROUP BY CustomerSegment
ORDER BY Revenue DESC;

-- 2.8 Quarter-over-Quarter growth
SELECT
    Year,
    Quarter,
    ROUND(SUM(NetSales), 2) AS Revenue
FROM sales
GROUP BY Year, Quarter
ORDER BY Year, Quarter;

-- 2.9 Discount Impact Analysis — does discounting correlate with larger baskets?
SELECT
    CASE
        WHEN DiscountPct = 0 THEN 'No Discount'
        WHEN DiscountPct <= 0.10 THEN 'Low (<=10%)'
        ELSE 'High (>10%)'
    END AS DiscountBand,
    ROUND(AVG(Quantity), 2)          AS AvgUnitsPerOrder,
    ROUND(AVG(NetSales), 2)          AS AvgOrderValue,
    ROUND(AVG(ProfitMarginPct) * 100, 2) AS AvgProfitMarginPct
FROM sales
GROUP BY DiscountBand
ORDER BY AvgOrderValue DESC;

-- 2.10 Top 5 Cities by Revenue per Region (window function)
SELECT Region, City, Revenue, CityRank
FROM (
    SELECT
        Region,
        City,
        ROUND(SUM(NetSales), 2) AS Revenue,
        RANK() OVER (PARTITION BY Region ORDER BY SUM(NetSales) DESC) AS CityRank
    FROM sales
    GROUP BY Region, City
) ranked
WHERE CityRank <= 3
ORDER BY Region, CityRank;

-- 2.11 Month-over-Month growth rate (window function)
SELECT
    YearMonth,
    Revenue,
    ROUND(
        (Revenue - LAG(Revenue) OVER (ORDER BY YearMonth)) * 100.0
        / LAG(Revenue) OVER (ORDER BY YearMonth), 2
    ) AS MoM_GrowthPct
FROM (
    SELECT YearMonth, ROUND(SUM(NetSales), 2) AS Revenue
    FROM sales
    GROUP BY YearMonth
) monthly
ORDER BY YearMonth;

-- 2.12 Payment Mode Preference by Channel
SELECT
    Channel,
    PaymentMode,
    COUNT(*) AS OrderCount,
    ROUND(SUM(NetSales), 2) AS Revenue
FROM sales
GROUP BY Channel, PaymentMode
ORDER BY Channel, Revenue DESC;
