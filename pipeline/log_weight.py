"""Log a weigh-in: date, weight and body fat %.

Fat mass and fat-free mass are not entered: they are calculated from weight and
body fat (fat mass = weight x body fat %, fat-free mass = weight - fat mass), in
the database by stg_weight_log and here only to show them before saving.
"""
import os
from datetime import date

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


def get_input_date():
    today = date.today()
    while True:
        raw = input(f"Date [default: today, {today.isoformat()}]: ").strip()
        if not raw:
            return today
        try:
            return date.fromisoformat(raw)
        except ValueError:
            print("Enter the date as YYYY-MM-DD, e.g. 2026-11-26, or press Enter for today")


def get_input_weight():
    while True:
        raw = input("Weight (kg): ").strip()
        try:
            weight = float(raw)
        except ValueError:
            print("Enter a number, e.g. 108.4")
            continue
        if 30 <= weight <= 300:
            return weight
        print("That doesn't look like a realistic weight in kg — try again.")


# Optional: press Enter to skip (e.g. on days the scale doesn't report it).
# Accepts a fraction (0.407) or a percentage (40.7); both are stored as 40.7.
def get_input_body_fat():
    while True:
        raw = input("Body fat (e.g. 0.407 or 40.7) [optional, Enter to skip]: ").strip()
        if not raw:
            return None
        try:
            value = float(raw)
        except ValueError:
            print("Enter a number, e.g. 0.407 or 40.7, or leave blank")
            continue
        pct = round(value * 100, 1) if value < 1 else value
        if 1 <= pct <= 90:
            return pct
        print("That doesn't look like a realistic body fat percentage — try again.")


def body_composition(weight_kg, body_fat_pct):
    """Same formulas as stg_weight_log, so the preview matches the dashboard."""
    fat_mass_kg = weight_kg * body_fat_pct / 100
    return fat_mass_kg, weight_kg - fat_mass_kg


# Re-logging a date replaces that day's weight and body fat with the latest entry.
def upsert_weight(conn, log_date, weight_kg, body_fat_pct):
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into staging.weight_log_raw (log_date, weight_kg, body_fat_pct, logged_at)
            values (%s, %s, %s, now())
            on conflict (log_date) do update
                set weight_kg = excluded.weight_kg,
                    body_fat_pct = excluded.body_fat_pct,
                    logged_at = excluded.logged_at
            """,
            (log_date, weight_kg, body_fat_pct),
        )
    conn.commit()


def main():
    log_date = get_input_date()
    weight_kg = get_input_weight()
    body_fat_pct = get_input_body_fat()

    summary = f"{weight_kg} kg"
    if body_fat_pct is not None:
        fat_mass_kg, fat_free_mass_kg = body_composition(weight_kg, body_fat_pct)
        summary += (f" · body fat {body_fat_pct}% · fat mass {fat_mass_kg:.1f} kg"
                    f" · fat-free mass {fat_free_mass_kg:.1f} kg")

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        upsert_weight(conn, log_date, weight_kg, body_fat_pct)
        print(f"Logged {summary} for {log_date.isoformat()}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
