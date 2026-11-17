"""Pull daily wellness records (Fitness/Fatigue/ramp rate) from intervals.icu.

ctl/atl here are intervals.icu's own values, i.e. exactly what https://intervals.icu/fitness shows.
Weight and body composition are not loaded from here; they come from the manual
log (pipeline/log_weight.py). The full record is still kept in raw_json.
"""
import os
from datetime import date

import psycopg2
import psycopg2.extras
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("INTERVALS_API_KEY")
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

# Earlier than the first activity in the pipeline (2025-09-08). Wellness records
# before the account had data are simply not returned.
OLDEST_DATE = "2025-01-01"


def fetch_wellness():
    response = requests.get(
        "https://intervals.icu/api/v1/athlete/0/wellness",
        params={"oldest": OLDEST_DATE, "newest": date.today().isoformat()},
        auth=("API_KEY", API_KEY),
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def upsert_wellness(records):
    upsert_sql = """
        INSERT INTO staging.intervals_wellness_raw (
            wellness_date, ctl, atl, ramp_rate, ctl_load, atl_load, raw_json
        )
        VALUES (
            %(id)s, %(ctl)s, %(atl)s, %(ramp)s, %(ctl_load)s, %(atl_load)s, %(raw)s
        )
        ON CONFLICT (wellness_date) DO UPDATE SET
            ctl = EXCLUDED.ctl,
            atl = EXCLUDED.atl,
            ramp_rate = EXCLUDED.ramp_rate,
            ctl_load = EXCLUDED.ctl_load,
            atl_load = EXCLUDED.atl_load,
            raw_json = EXCLUDED.raw_json,
            pulled_at = now();
    """
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            for r in records:
                cur.execute(upsert_sql, {
                    "id": r["id"],  # intervals.icu uses the ISO date as the record id
                    "ctl": r.get("ctl"),
                    "atl": r.get("atl"),
                    "ramp": r.get("rampRate"),
                    "ctl_load": r.get("ctlLoad"),
                    "atl_load": r.get("atlLoad"),
                    "raw": psycopg2.extras.Json(r),
                })
        conn.commit()
    finally:
        conn.close()
    print(f"Upserted {len(records)} wellness records.")


if __name__ == "__main__":
    upsert_wellness(fetch_wellness())
