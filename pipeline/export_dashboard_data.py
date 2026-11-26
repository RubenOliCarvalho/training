import json
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "data"

TABLES = {
    "daily": "select * from analytics.mart_daily_training order by calendar_date",
    "weekly": "select * from analytics.mart_weekly_training order by week_start",
    "monthly": "select * from analytics.mart_monthly_training order by month",
    "yearly": "select * from analytics.mart_yearly_training order by year",
    "zones_monthly": "select * from analytics.mart_monthly_zone_times order by month, zone_type, zone",
    "zones_yearly": "select * from analytics.mart_yearly_zone_times order by year, zone_type, zone",
    "activities": "select * from analytics.mart_activity_diary order by start_date_local desc",
    "planned": "select * from analytics.mart_planned_sessions order by event_date, event_id",
    "weekly_plan": "select * from analytics.mart_weekly_plan order by week_start",
    "ride_progress": "select * from analytics.mart_ride_progress order by activity_date",
    "run_progress": "select * from analytics.mart_run_progress order by activity_date",
}


# The dashboard is opened straight from disk (file://), where browsers block
# fetch() of local JSON. dashboard_data.js assigns everything to
# window.DASHBOARD_DATA so docs/index.html can load it with a <script> tag.
JS_BUNDLE = OUTPUT_DIR / "dashboard_data.js"


def export_table(engine, name, query):
    df = pd.read_sql(query, engine)
    output_path = OUTPUT_DIR / f"{name}.json"
    df.to_json(output_path, orient="records", date_format="iso", indent=2)
    print(f"Wrote {len(df)} rows to {output_path}")
    return df.to_json(orient="records", date_format="iso")


# Session time series for the Daily tab, one small script per activity so the
# page loads only the session being viewed (a <script> tag also works from
# file://). Read straight from staging: these are raw display series, not
# modelled metrics. Files are rewritten only when their content changed, so
# unchanged sessions stay out of the data commit; files for activities no
# longer in the table are removed.
STREAMS_DIR = OUTPUT_DIR / "streams"


def export_streams(engine):
    STREAMS_DIR.mkdir(exist_ok=True)
    with engine.connect() as conn:
        rows = conn.execute(text(
            "select activity_id, streams, laps from staging.activity_streams "
            "where streams <> '{}'::jsonb order by activity_id"
        )).fetchall()
    keep, written = set(), 0
    for activity_id, streams, laps in rows:
        path = STREAMS_DIR / f"{activity_id}.js"
        keep.add(path.name)
        payload = json.dumps({**streams, "laps": laps}, separators=(",", ":"))
        content = f"(window.STREAMS = window.STREAMS || {{}})[{json.dumps(activity_id)}] = {payload};\n"
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
            written += 1
    removed = 0
    for path in STREAMS_DIR.glob("*.js"):
        if path.name not in keep:
            path.unlink()
            removed += 1
    print(f"Session streams: {len(rows)} activities, {written} written, {removed} removed")
    return [row[0] for row in rows]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(DB_URL)
    tables_json = {name: export_table(engine, name, query) for name, query in TABLES.items()}
    # Which activities have a session chart, so the page doesn't request missing files.
    tables_json["stream_ids"] = json.dumps(export_streams(engine))
    body = ",\n".join(f'  "{name}": {payload}' for name, payload in tables_json.items())
    JS_BUNDLE.write_text(f"window.DASHBOARD_DATA = {{\n{body}\n}};\n", encoding="utf-8")
    print(f"Wrote {JS_BUNDLE}")


if __name__ == "__main__":
    main()