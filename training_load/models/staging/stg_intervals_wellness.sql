-- Recovery metrics (sleep, resting HR, HRV) come from the wellness record's raw
-- JSON; intervals.icu fills them from the connected Garmin account.
select
    wellness_date,
    ctl,
    atl,
    ramp_rate,
    ctl_load,
    atl_load,
    round((raw_json ->> 'sleepSecs')::numeric / 3600, 2) as sleep_hours,
    (raw_json ->> 'sleepScore')::numeric as sleep_score,
    (raw_json ->> 'restingHR')::numeric as resting_hr,
    (raw_json ->> 'hrv')::numeric as hrv,
    pulled_at
from {{ source('staging', 'intervals_wellness_raw') }}
