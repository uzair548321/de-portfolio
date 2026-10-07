import duckdb, requests, logging, time
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
DB = "data/warehouse.duckdb"
CITIES = {"Delhi": (28.61, 77.21), "Mumbai": (19.07, 72.88), "London": (51.51, -0.13)}
OVERLAP_DAYS = 2
DEFAULT_START = date(2025, 1, 1)

con = duckdb.connect(DB)
con.execute("CREATE SCHEMA IF NOT EXISTS bronze")
con.execute("""
CREATE TABLE IF NOT EXISTS bronze.weather_daily (
  city VARCHAR, obs_date DATE, temp_max DOUBLE, temp_min DOUBLE,
  precipitation DOUBLE, loaded_at TIMESTAMP DEFAULT now(),
  PRIMARY KEY (city, obs_date))""")
con.execute("""
CREATE TABLE IF NOT EXISTS bronze.etl_control (
  source VARCHAR PRIMARY KEY, last_loaded_date DATE)""")

def get_watermark(source):
    r = con.execute("SELECT last_loaded_date FROM bronze.etl_control WHERE source=?", [source]).fetchone()
    return r[0] if r else None

def fetch(city, lat, lon, start, end, retries=3):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {"latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
              "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum", "timezone": "UTC"}
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()["daily"]
        except Exception as e:
            logging.warning(f"{city} attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)
    raise RuntimeError(f"{city} failed after {retries} retries")

def main():
    wm = get_watermark("open_meteo")
    start = (wm - timedelta(days=OVERLAP_DAYS)) if wm else DEFAULT_START
    end = date.today() - timedelta(days=2)   # archive API me latest 1-2 din ka data late aata hai
    if start > end:
        logging.info("Nothing new to load"); return
    logging.info(f"Loading {start} -> {end}")

    for city, (lat, lon) in CITIES.items():
        d = fetch(city, lat, lon, start.isoformat(), end.isoformat())
        rows = list(zip([city]*len(d["time"]), d["time"], d["temperature_2m_max"],
                        d["temperature_2m_min"], d["precipitation_sum"]))
        con.executemany("""
            INSERT INTO bronze.weather_daily (city, obs_date, temp_max, temp_min, precipitation)
            VALUES (?,?,?,?,?)
            ON CONFLICT (city, obs_date) DO UPDATE SET
              temp_max=excluded.temp_max, temp_min=excluded.temp_min,
              precipitation=excluded.precipitation, loaded_at=now()""", rows)
        logging.info(f"{city}: {len(rows)} rows upserted")

    con.execute("""
        INSERT INTO bronze.etl_control VALUES ('open_meteo', ?)
        ON CONFLICT (source) DO UPDATE SET last_loaded_date=excluded.last_loaded_date""", [end])

if __name__ == "__main__":
    main()