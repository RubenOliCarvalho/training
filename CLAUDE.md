# training-load-forecast: context for Claude Code

Personal training-load dashboard for Ruben. Read this first. Everything marked UNVERIFIED has not been confirmed against real data or docs.

## How Ruben wants to work
- Analytical, first-principles, accuracy over completeness. State assumptions, flag unknowns, don't guess.
- Surface the key insight first, then the reasoning. Concise but rigorous. Challenge weak premises.
- Code (SQL/Python) should be correct, readable, production-minded, with edge cases and validation checks called out.

## Architecture
intervals.icu API -> Python ingest (`pipeline/`) -> Postgres `staging` schema -> dbt (`training_load/`) -> `analytics` marts -> `pipeline/export_dashboard_data.py` writes JSON plus `docs/data/dashboard_data.js` to `docs/data/` -> static dashboard `docs/index.html`, opened locally from disk (`open_dashboard.bat`). LOCAL ONLY since 18 Nov 2026: nothing is published; the GitHub repo/Pages site is being deleted at Ruben's request (contains personal body data). Don't add any publishing, pushing or hosting back.
- `run_pipeline.py` runs everything in order: ingest_intervals, ingest_wellness (new), ingest_weather, dbt seed, dbt run, dbt test, export. No git steps; it does not commit or push.
- Windows project. Python/dbt live in `venv/Scripts/`. Credentials are in `.env`; never read, print or commit it.
- Weight tooling: `log_weight.bat` -> `pipeline/log_weight.py` (manual entry).
- dbt layers: staging (`stg_*`), intermediate (`int_training_load_daily`), marts (`mart_daily/weekly/monthly/yearly_training`, `mart_activity_diary`). Targets come from a dbt seed (`targets`).

## Where weight, body fat and muscle mass come from
Manual log only: `log_weight.py` -> `staging.weight_log_raw` (upsert per date) -> `stg_weight_log` -> forward-filled per metric in `mart_daily_training` -> averaged in weekly/monthly, start/end in yearly. Muscle mass (kg) has no confirmed intervals.icu field. Forward-filling weights weekly/monthly averages by how long a reading stayed current. 2025 has no weight data.

## Fitness/Fatigue/Form source: intervals.icu wellness (tested 18 Nov 2026, UNCOMMITTED)
ctl/atl come straight from intervals.icu's `/wellness` endpoint so numbers match https://intervals.icu/fitness.
- `sql/009_staging_wellness.sql` (applied) creates `staging.intervals_wellness_raw` (ctl, atl, ramp_rate, ctl_load, atl_load, raw_json) and grants the pipeline user select/insert/update.
- `pipeline/ingest_wellness.py` runs before weather in `run_pipeline.py`. Weight/bodyFat from wellness are deliberately NOT loaded (manual log stays the only source); they remain in raw_json.
- `int_training_load_daily.sql`: ctl/atl from wellness (carried forward on gaps), `daily_training_load` = sum of activity loads, same output columns. `tsb` is same-day ctl - atl (it used to be the prior day's value).
- dbt tests: unique `wellness_date`; unique/not_null `calendar_date`, not_null ctl/atl in the intermediate model.
- `pipeline/ingest_weather.py`: Open-Meteo archive sometimes rejects today as end_date ("out of allowed range"); it now falls back up to 3 days.
- Weather on the calendar (UNCOMMITTED): `ingest_weather.py` also requests Open-Meteo's daily `weather_code` (WMO, most severe condition of the day). It's stored inside `raw_json` (no new column) and read as `weather_code` in `stg_weather_daily` -> `mart_daily_training`. The archive lags ~1 day, so today has no weather until tomorrow.
Old recursive EWMA model is in git history.

## Verified findings
- 2026 yearly total load is 4,060 in this project vs 2,678 on intervals.icu's summary page. The gap is exactly strength (1,340) + yoga (42) = 1,382; the other sports match the page. The dashboard figure is correct as an all-activities total; the intervals.icu summary page omits strength and yoga load. Whether strength feeds Fitness/Fatigue in intervals.icu is UNVERIFIED. Consider adding a cardio-only load metric.
- Old dashboard vs intervals.icu on 31 Aug 2026: CTL 13.2 / ATL 14.7 vs Fitness 10 / Fatigue 14. New model: 9.9 / 14.2.
- Wellness returns full history from 2025-09-03 (before the first activity, 2025-09-08) with no missing days; mart ctl/atl equal wellness on all 437 days.
- 18 Nov 2026: Fitness 11.35 / Fatigue 28.59 / Form -17.24. The intervals.icu page showed 11 / 29 / -18; Form -18 is consistent with subtracting the rounded values, but how the page rounds Form is UNVERIFIED.

## Open work: Wahoo run plans -> watch
Goal: read running sessions from a Wahoo SYSTM plan and send them to ONE Garmin watch (Ruben has two Garmin devices; which one is still to be decided).
- No public SYSTM API. Wahoo's Cloud API has `/v1/plans` (`plans_read` scope), but whether it exposes SYSTM calendar sessions is UNVERIFIED and unlikely.
- Community routes: SufferSync (PyPI `suffersync`; needs SYSTM username/password in a plain-text config; run sync optional since v1.3.0; unofficial/unsupported) and a "SYSTM 2 INTERVALS Calendar Sync" Chrome extension (unmaintained; run support and Garmin compatibility unconfirmed). A 2025 forum thread suggests Wahoo may have restricted third-party access to SYSTM workouts (user speculation).
- Wahoo staff have said SYSTM has no dedicated run-only plans; run workouts exist in its library (about 126 in a 2021 figure) and are done in the Wahoo app. Ask which plan Ruben is actually following.
- Intervals.icu -> Garmin: intervals.icu can upload planned workouts to Garmin Connect (Garmin integration, "Upload planned workouts"). Garmin Connect normally syncs to all paired devices; how to restrict to one device is UNVERIFIED and not yet researched.
- Fallback if SYSTM can't be read: author the run workouts in intervals.icu and let it upload to Garmin (supported route).
- Security: avoid tools that need his SYSTM password if possible; the intervals.icu API key gives full account access.

## Conventions and cautions
- Don't delete files on the device without asking; don't commit or push without being asked.
- Keep mart output columns stable (the dashboard JSON depends on them).
- Validate against intervals.icu before trusting any rebuilt metric.
