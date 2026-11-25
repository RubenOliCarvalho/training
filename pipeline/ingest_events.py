"""Pull calendar events (planned workouts) from intervals.icu into staging.intervals_events_raw.

The window [OLDEST_DATE, today + LOOKAHEAD_DAYS] is reloaded on every run: events
in it are upserted and rows for events no longer on the calendar (deleted or
moved out of the window) are removed, so the table mirrors the calendar.
"""
import os
from datetime import date, timedelta

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

# Planned workouts start with the training plans (Nov 2026); earlier events are
# not used by any report.
OLDEST_DATE = date(2026, 11, 1)
LOOKAHEAD_DAYS = 42


def fetch_events(oldest, newest):
    response = requests.get(
        "https://intervals.icu/api/v1/athlete/0/events",
        params={"oldest": oldest.isoformat(), "newest": newest.isoformat()},
        auth=("API_KEY", API_KEY),
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def sync_events(events, oldest, newest):
    upsert_sql = """
        insert into staging.intervals_events_raw (
            event_id, event_date, category, event_type, name, planned_secs,
            paired_activity_id, external_id, raw_json
        )
        values (
            %(event_id)s, %(event_date)s, %(category)s, %(event_type)s, %(name)s, %(planned_secs)s,
            %(paired_activity_id)s, %(external_id)s, %(raw)s
        )
        on conflict (event_id) do update set
            event_date = excluded.event_date,
            category = excluded.category,
            event_type = excluded.event_type,
            name = excluded.name,
            planned_secs = excluded.planned_secs,
            paired_activity_id = excluded.paired_activity_id,
            external_id = excluded.external_id,
            raw_json = excluded.raw_json,
            pulled_at = now();
    """
    ids = [e["id"] for e in events]
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            for e in events:
                cur.execute(upsert_sql, {
                    "event_id": e["id"],
                    "event_date": e["start_date_local"][:10],
                    "category": e.get("category"),
                    "event_type": e.get("type"),
                    "name": e.get("name"),
                    "planned_secs": e.get("moving_time"),
                    "paired_activity_id": e.get("paired_activity_id"),
                    "external_id": e.get("external_id"),
                    "raw": psycopg2.extras.Json(e),
                })
            # Same transaction as the upserts: a failed run leaves the table untouched.
            cur.execute(
                """
                delete from staging.intervals_events_raw
                where event_date between %s and %s
                  and not (event_id = any(%s))
                """,
                (oldest, newest, ids),
            )
            removed = cur.rowcount
        conn.commit()
    finally:
        conn.close()
    print(f"Upserted {len(events)} events, removed {removed} no longer on the calendar.")


if __name__ == "__main__":
    newest = date.today() + timedelta(days=LOOKAHEAD_DAYS)
    sync_events(fetch_events(OLDEST_DATE, newest), OLDEST_DATE, newest)
