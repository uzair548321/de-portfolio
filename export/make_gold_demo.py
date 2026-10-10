import duckdb

con = duckdb.connect("data/gold_demo.duckdb")
con.execute("ATTACH 'data/warehouse.duckdb' AS src (READ_ONLY)")
con.execute("CREATE SCHEMA IF NOT EXISTS gold")
for t in ["dim_customers", "fact_orders"]:
    con.execute(f"CREATE OR REPLACE TABLE gold.{t} AS SELECT * FROM src.gold.{t}")
    print("copied", t)