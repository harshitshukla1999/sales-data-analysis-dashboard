"""
load_to_sqlite.py
------------------
Loads data/sales_data_cleaned.csv into a SQLite database (sql/sales.db)
using the schema defined in schema_and_queries.sql, so all the KPI
queries in that file can be run directly.

Run from the project root:  python sql/load_to_sqlite.py
"""
import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "sales_data_cleaned.csv")
SCHEMA_PATH = os.path.join(BASE_DIR, "sql", "schema_and_queries.sql")
DB_PATH = os.path.join(BASE_DIR, "sql", "sales.db")


def main():
    df = pd.read_csv(DATA_PATH)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)

    # Run just the CREATE TABLE statement from the schema file (first statement)
    with open(SCHEMA_PATH, "r") as f:
        full_sql = f.read()
    create_stmt = full_sql.split("-- Load data")[0]
    conn.executescript(create_stmt)

    df.to_sql("sales", conn, if_exists="append", index=False)
    conn.commit()

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sales")
    print(f"Loaded {cur.fetchone()[0]} rows into {DB_PATH}")

    conn.close()


if __name__ == "__main__":
    main()
