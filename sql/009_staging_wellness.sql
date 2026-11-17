-- Daily wellness records from the intervals.icu /wellness endpoint.
-- ctl/atl are intervals.icu's own Fitness/Fatigue values (what the /fitness page plots).
-- Weight and body composition are deliberately NOT taken from here: they come
-- from the manual log (staging.weight_log_raw via pipeline/log_weight.py).
-- The full API record is still kept in raw_json.
-- Run as the staging schema owner (ruben.carvalho).
create table if not exists staging.intervals_wellness_raw (
    wellness_date date primary key,
    ctl           numeric,
    atl           numeric,
    ramp_rate     numeric,
    ctl_load      numeric,
    atl_load      numeric,
    raw_json      jsonb not null,
    pulled_at     timestamptz not null default now()
);

-- Same rights the pipeline user has on the other staging tables
-- (002_grant_staging_privileges.sql); explicit in case default privileges don't apply.
grant select, insert, update on staging.intervals_wellness_raw to training_load;
