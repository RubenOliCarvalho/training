"""Push planned workouts from a plan file to the intervals.icu calendar.

intervals.icu then uploads them to Garmin Connect (requires "Upload planned
workouts" in intervals.icu Settings -> Garmin Connect), and Garmin Connect
syncs them to the watch.

Usage:
    python pipeline/push_workouts.py plans/<plan>.yaml            # create or update
    python pipeline/push_workouts.py plans/<plan>.yaml --dry-run  # show, send nothing
    python pipeline/push_workouts.py plans/<plan>.yaml --delete   # remove from calendar

Plan file format (YAML):

    plan: base-block-1            # id; tags every workout so re-pushing updates them
    workouts:
      - date: 2026-11-24
        name: Easy run/walk 25'
        type: Run                 # optional, default Run
        description: |            # intervals.icu workout text
          Warmup
          - 5m Z1 HR
          Main set 6x
          - 2m Z2 HR
          - 1m Z1 HR
          Cooldown
          - 2m Z1 HR

Each workout is identified by external_id "<plan>-<date>-<n>" (n = order within
that date), so pushing the same file again updates the existing calendar entries
instead of duplicating them. Workouts that were removed from the file are NOT
deleted automatically; use --delete to clear a whole plan, then push again.
"""
import argparse
import os
import sys
from datetime import date
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_KEY = os.getenv("INTERVALS_API_KEY")
BASE_URL = "https://intervals.icu/api/v1/athlete/0"
AUTH = ("API_KEY", API_KEY)


def load_plan(path):
    plan = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    plan_id = plan.get("plan")
    if not plan_id or not isinstance(plan.get("workouts"), list) or not plan["workouts"]:
        sys.exit("Plan file needs a 'plan' id and a non-empty 'workouts' list.")

    events, per_date = [], {}
    for w in plan["workouts"]:
        missing = [k for k in ("date", "name", "description") if not w.get(k)]
        if missing:
            sys.exit(f"Workout {w!r} is missing: {', '.join(missing)}")
        d = w["date"] if isinstance(w["date"], date) else date.fromisoformat(str(w["date"]))
        per_date[d] = per_date.get(d, 0) + 1
        events.append({
            "category": "WORKOUT",
            "type": w.get("type", "Run"),
            "start_date_local": f"{d.isoformat()}T00:00:00",
            "name": w["name"],
            "description": w["description"].strip(),
            "external_id": f"{plan_id}-{d.isoformat()}-{per_date[d]}",
        })
    return plan_id, events


def existing_events(plan_id, events):
    """Calendar events already created from this plan, keyed by external_id."""
    dates = sorted(e["start_date_local"][:10] for e in events)
    response = requests.get(
        f"{BASE_URL}/events",
        params={"oldest": dates[0], "newest": dates[-1]},
        auth=AUTH, timeout=30,
    )
    response.raise_for_status()
    return {
        e["external_id"]: e for e in response.json()
        if (e.get("external_id") or "").startswith(f"{plan_id}-")
    }


def describe(saved):
    """One-line check that intervals.icu parsed the workout text into steps."""
    steps = len((saved.get("workout_doc") or {}).get("steps") or [])
    minutes = round((saved.get("moving_time") or 0) / 60)
    if not steps:
        return "WARNING: intervals.icu parsed no steps; check the description syntax"
    return f"{steps} steps, ~{minutes} min"


def push(plan_id, events):
    current = existing_events(plan_id, events)
    for event in events:
        old = current.get(event["external_id"])
        if old:
            response = requests.put(f"{BASE_URL}/events/{old['id']}", json=event, auth=AUTH, timeout=30)
            action = "updated"
        else:
            response = requests.post(f"{BASE_URL}/events", json=event, auth=AUTH, timeout=30)
            action = "created"
        response.raise_for_status()
        print(f"{action:8} {event['start_date_local'][:10]}  {event['name']}  ({describe(response.json())})")


def delete(plan_id, events):
    current = existing_events(plan_id, events)
    if not current:
        print(f"No calendar workouts found for plan '{plan_id}'.")
    for ext_id, event in sorted(current.items()):
        requests.delete(f"{BASE_URL}/events/{event['id']}", auth=AUTH, timeout=30).raise_for_status()
        print(f"deleted  {event['start_date_local'][:10]}  {event['name']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan_file")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", help="print what would be sent; send nothing")
    group.add_argument("--delete", action="store_true", help="remove this plan's workouts from the calendar")
    args = parser.parse_args()

    plan_id, events = load_plan(args.plan_file)
    if args.dry_run:
        for e in events:
            print(f"{e['start_date_local'][:10]}  {e['type']:<5} {e['name']}  [{e['external_id']}]")
            print("    " + e["description"].replace("\n", "\n    "))
        return
    if not API_KEY:
        sys.exit("INTERVALS_API_KEY is not set in .env")
    if args.delete:
        delete(plan_id, events)
    else:
        push(plan_id, events)


if __name__ == "__main__":
    main()
