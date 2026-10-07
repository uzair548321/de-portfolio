import duckdb
from pathlib import Path

out = Path("data/export")
out.mkdir(parents=True, exist_ok=True)
con = duckdb.connect("data/warehouse.duckdb", read_only=True)

for t in ["dim_customers", "fact_orders"]:
    con.execute(f"COPY gold.{t} TO '{(out / (t + '.csv')).as_posix()}' (HEADER, DELIMITER ',')")
    print("exported", t)