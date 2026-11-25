"""Store best 1/5/20-minute power per ride in staging.activity_power_bests.

Reads each ride's power curve from intervals.icu. Only rides with power and no
row yet are fetched, so after the first run this is one request per new ride.
"""
import os

import psycopg2
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
DURATIONS = {"best_1m_w": 60, "best_5m_w": 300, "best_20m_w": 1200}


def best_efforts(activity_id):
    response = requests.get(
        f"https://intervals.icu/api/v1/activity/{activity_id}/power-curve.json",
        auth=("API_KEY", API_KEY),
        timeout=60,
    )
    response.raise_for_status()
    curve = response.json()
    by_secs = dict(zip(curve.get("secs") or [], curve.get("watts") or []))
    # The curve only has points up to the ride's length, so a missing duration
    # means the ride was too short for it.
    return {col: (round(by_secs[s]) if by_secs.get(s) else None) for col, s in DURATIONS.items()}


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                select a.activity_id
                from staging.intervals_activities_raw a
                left join staging.activity_power_bests p using (activity_id)
                where a.activity_type in ('Ride', 'VirtualRide')
                  and a.avg_watts is not null
                  and p.activity_id is null
                order by a.start_date_local
                """
            )
            todo = [r[0] for r in cur.fetchall()]
            for activity_id in todo:
                bests = best_efforts(activity_id)
                cur.execute(
                    """
                    insert into staging.activity_power_bests (activity_id, best_1m_w, best_5m_w, best_20m_w)
                    values (%(id)s, %(best_1m_w)s, %(best_5m_w)s, %(best_20m_w)s)
                    on conflict (activity_id) do update set
                        best_1m_w = excluded.best_1m_w,
                        best_5m_w = excluded.best_5m_w,
                        best_20m_w = excluded.best_20m_w,
                        pulled_at = now()
                    """,
                    {"id": activity_id, **bests},
                )
                conn.commit()
        print(f"Stored power bests for {len(todo)} ride(s).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
