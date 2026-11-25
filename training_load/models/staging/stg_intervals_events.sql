-- Planned workouts only (category WORKOUT); notes and other calendar entries are dropped.
select
    event_id,
    event_date,
    event_type,
    {{ sport_family('event_type') }} as sport_family,
    name as event_name,
    planned_secs / 60.0 as planned_min,
    paired_activity_id,
    external_id,
    pulled_at
from {{ source('staging', 'intervals_events_raw') }}
where category = 'WORKOUT'
