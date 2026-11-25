-- Planned workouts and best-power efforts, for the Plan and Progress reporting.
-- Run as the staging schema owner (ruben.carvalho).

-- Calendar events (planned workouts, notes, ...) from the intervals.icu /events
-- endpoint, landed by pipeline/ingest_events.py. The script reloads a rolling
-- window, deleting rows for events that were removed from the calendar, so the
-- pipeline user also needs DELETE here.
create table if not exists staging.intervals_events_raw (
    event_id            bigint primary key,
    event_date          date not null,
    category            text not null,
    event_type          text,
    name                text,
    planned_secs        integer,
    paired_activity_id  text,
    external_id         text,
    raw_json            jsonb not null,
    pulled_at           timestamptz not null default now()
);

-- Best average power over 1, 5 and 20 minutes per ride, from the intervals.icu
-- per-activity power curve (pipeline/ingest_power_bests.py). Null where the ride
-- is shorter than the duration.
create table if not exists staging.activity_power_bests (
    activity_id  text primary key,
    best_1m_w    integer,
    best_5m_w    integer,
    best_20m_w   integer,
    pulled_at    timestamptz not null default now()
);

grant select, insert, update, delete on staging.intervals_events_raw to training_load;
grant select, insert, update on staging.activity_power_bests to training_load;
