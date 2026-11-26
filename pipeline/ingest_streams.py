"""Store each activity's time series (5-second averages) and laps in
staging.activity_streams, for the session chart on the Daily tab.

Only activities without a row are fetched, so after the first run this is two
requests per new activity. Activities with no recorded data (e.g. manual
entries) get an empty row so they aren't requested again.

PRIVACY: only the channels in STREAM_TYPES are requested, so the GPS track
(latlng) is never downloaded. Elevation is stored relative to the start, not as
absolute altitude. Laps keep only the fields in LAP_FIELDS (intervals.icu also
returns weather and wind per lap; those are dropped).

Usage:
    python pipeline/ingest_streams.py                 # new activities only
    python pipeline/ingest_streams.py --refetch i123  # re-download one activity
"""
import argparse
import json
import os
from collections import defaultdict

import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("INTERVALS_API_KEY")
BASE_URL = "https://intervals.icu/api/v1"
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

SAMPLE_SECS = 5
# intervals.icu stream type -> (output key, decimals). No latlng, on purpose.
STREAM_TYPES = {
    "heartrate": ("hr", 0),
    "watts": ("watts", 0),
    "cadence": ("cadence", 0),
    "velocity_smooth": ("speed", 2),   # m/s
    "fixed_altitude": ("elev", 1),     # corrected elevation, preferred
    "altitude": ("elev_raw", 1),       # fallback when fixed_altitude is missing
    "distance": ("dist", 0),           # metres from the start
    "temp": ("temp", 0),               # device sensor
}
# Lap field in intervals.icu -> output key.
LAP_FIELDS = {
    "start_time": "start",
    "end_time": "end",
    "type": "type",
    "label": "label",
    "distance": "dist_m",
    "average_heartrate": "avg_hr",
    "max_heartrate": "max_hr",
    "average_speed": "avg_speed",
    "gap": "gap",
    "average_watts": "avg_watts",
    "weighted_average_watts": "np_watts",
    "average_cadence": "avg_cadence",
    "total_elevation_gain": "gain_m",
}


def get(path, **params):
    response = requests.get(f"{BASE_URL}{path}", auth=("API_KEY", API_KEY), params=params, timeout=60)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def downsample(raw_streams):
    """5-second bucket averages per channel, aligned on one time axis.

    HR of 0 means no reading and is ignored; power, speed and cadence keep zeros
    (coasting, standing still). Distance takes the last value of each bucket.
    A channel with no non-zero data is left out.
    """
    by_type = {s["type"]: s.get("data") or [] for s in raw_streams or []}
    times = by_type.get("time") or []
    if not times:
        return {}

    buckets = sorted({int(t) // SAMPLE_SECS for t in times})
    index = {b: i for i, b in enumerate(buckets)}
    out = {"sample_secs": SAMPLE_SECS, "t": [b * SAMPLE_SECS for b in buckets]}

    for stream_type, (key, digits) in STREAM_TYPES.items():
        values = by_type.get(stream_type)
        if not values or not any(v for v in values if v is not None):
            continue
        sums, counts, last = defaultdict(float), defaultdict(int), {}
        for t, v in zip(times, values):
            if v is None or (stream_type == "heartrate" and v <= 0):
                continue
            b = int(t) // SAMPLE_SECS
            sums[b] += v
            counts[b] += 1
            last[b] = v
        series = [None] * len(buckets)
        for b in counts:
            value = last[b] if stream_type == "distance" else sums[b] / counts[b]
            series[index[b]] = round(value, digits) if digits else int(round(value))
        out[key] = series

    # Elevation relative to the first reading (no absolute altitude published).
    elev = out.pop("elev", None) or out.pop("elev_raw", None)
    out.pop("elev_raw", None)
    if elev:
        start = next(v for v in elev if v is not None)
        out["elev"] = [None if v is None else round(v - start, 1) for v in elev]
    return out


def laps_for(activity_id):
    data = get(f"/activity/{activity_id}/intervals") or {}
    laps = []
    for lap in data.get("icu_intervals") or []:
        row = {}
        for src, key in LAP_FIELDS.items():
            value = lap.get(src)
            if isinstance(value, float):
                value = round(value, 3 if src in ("average_speed", "gap") else 1)
            row[key] = value
        laps.append(row)
    return laps


def store(cur, activity_id):
    raw = get(f"/activity/{activity_id}/streams.json", types=",".join(["time", *STREAM_TYPES]))
    streams = downsample(raw)
    laps = laps_for(activity_id) if streams else []
    cur.execute(
        """
        insert into staging.activity_streams (activity_id, streams, laps)
        values (%s, %s, %s)
        on conflict (activity_id) do update set
            streams = excluded.streams,
            laps = excluded.laps,
            pulled_at = now()
        """,
        (activity_id, json.dumps(streams), json.dumps(laps)),
    )
    return bool(streams)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--refetch", nargs="+", metavar="ACTIVITY_ID", help="re-download these activities")
    args = parser.parse_args()

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            if args.refetch:
                todo = args.refetch
            else:
                cur.execute(
                    """
                    select a.activity_id
                    from staging.intervals_activities_raw a
                    left join staging.activity_streams s using (activity_id)
                    where s.activity_id is null
                    order by a.start_date_local
                    """
                )
                todo = [r[0] for r in cur.fetchall()]
            with_data = 0
            for activity_id in todo:
                with_data += store(cur, activity_id)
                conn.commit()
        print(f"Stored streams for {len(todo)} activity(ies), {with_data} with recorded data.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
