import duckdb, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
RAW = Path("data/raw/olist")
con = duckdb.connect("data/warehouse.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS bronze")

for f in sorted(RAW.glob("*.csv")):
    table = f.stem.replace("olist_", "").replace("_dataset", "")
    con.execute(f"""
        CREATE OR REPLACE TABLE bronze.olist_{table} AS
        SELECT *, now() AS loaded_at, '{f.name}' AS source_file
        FROM read_csv_auto('{f.as_posix()}', header=true)""")
    n = con.execute(f"SELECT count(*) FROM bronze.olist_{table}").fetchone()[0]
    logging.info(f"{f.name} -> bronze.olist_{table}: {n} rows")