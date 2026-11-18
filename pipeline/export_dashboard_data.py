import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
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


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(DB_URL)
    tables_json = {name: export_table(engine, name, query) for name, query in TABLES.items()}
    body = ",\n".join(f'  "{name}": {payload}' for name, payload in tables_json.items())
    JS_BUNDLE.write_text(f"window.DASHBOARD_DATA = {{\n{body}\n}};\n", encoding="utf-8")
    print(f"Wrote {JS_BUNDLE}")


if __name__ == "__main__":
    main()