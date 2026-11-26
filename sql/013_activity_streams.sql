-- Per-activity time series (heart rate, power, pace, cadence, elevation) for the
-- session chart on the Daily tab, landed by pipeline/ingest_streams.py.
-- Run as the staging schema owner (ruben.carvalho).
--
-- PRIVACY: no GPS track. The ingest requests only the channels listed in
-- ingest_streams.STREAM_TYPES (latlng is never downloaded) and stores elevation
-- relative to the start, not absolute altitude. Lap rows keep a whitelist of
-- fields (no weather or wind values from intervals.icu).
--
-- streams: {"sample_secs": 5, "t": [...], "hr": [...], "watts": [...], ...}
--   5-second averages; a channel is left out when the activity has no data for it.
-- laps: [{"start": s, "end": s, "type": "WORK", "avg_hr": ..., ...}, ...]
create table if not exists staging.activity_streams (
    activity_id  text primary key,
    streams      jsonb not null,
    laps         jsonb not null default '[]'::jsonb,
    pulled_at    timestamptz not null default now()
);

grant select, insert, update, delete on staging.activity_streams to training_load;
