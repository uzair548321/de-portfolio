import subprocess
import sys

import duckdb


def row_count() -> int:
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    n = con.execute("select count(*) from bronze.weather_daily").fetchone()[0]
    con.close()
    return n


subprocess.run([sys.executable, "ingestion/load_weather.py"], check=True)
first = row_count()
subprocess.run([sys.executable, "ingestion/load_weather.py"], check=True)
second = row_count()

print(f"rows after run 1: {first}, after run 2: {second}")
assert first > 0, "no rows loaded"
assert first == second, "rerun changed the row count, load is not idempotent"