-- One row per run with grade-adjusted pace and running economy.
--   gap_pace_min_per_km: intervals.icu grade-adjusted pace (hills normalised).
--   meters_per_beat: grade-adjusted metres covered per heartbeat; higher = fitter.
--     Run/walk sessions include walking, so compare like with like: the
--     benchmark runs (is_benchmark) are the clean comparison points.

select
    activity_id,
    start_date_local::date as activity_date,
    activity_name,
    activity_type,
    round(moving_time_min, 1) as moving_time_min,
    round(distance_km, 2) as distance_km,
    avg_heartrate,
    max_heartrate,
    round(1000 / nullif(gap_mps, 0) / 60, 2) as gap_pace_min_per_km,
    round(gap_mps * 60 / nullif(avg_heartrate, 0), 2) as meters_per_beat,
    activity_name ilike '%benchmark%' as is_benchmark
from {{ ref('stg_intervals_activities') }}
where sport_family = 'Run'
  and moving_time_min >= 10
order by start_date_local
