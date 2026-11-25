-- activity_name: Garmin names GPS activities after the place ("<Place> - <workout>"
-- or "<Place> <Sport>"). For GPS activities the place is removed; indoor names are
-- kept. The original name stays in staging.intervals_activities_raw (not exported).
select
    activity_id,
    athlete_id,
    case
        when not coalesce((raw_json -> 'stream_types') ? 'latlng', false) then trim(name)
        when position(' - ' in name) > 0 then trim(substr(name, position(' - ' in name) + 3))
        when name ~* '(road cycling|trail running|running|walking|cycling|hiking|other)\s*$'
            then initcap(substring(name from '(?i)(road cycling|trail running|running|walking|cycling|hiking|other)\s*$'))
        else activity_type
    end as activity_name,  -- location removed from GPS activity names (see comment above the select)
    activity_type,
    source,
    trainer,
    start_date_local,
    start_date_utc,
    moving_time_secs / 60.0 as moving_time_min,
    elapsed_time_secs / 60.0 as elapsed_time_min,
    nullif(training_load, 0) as training_load,
    ctl as ctl_intervals,
    atl as atl_intervals,
    trimp,
    avg_heartrate,
    max_heartrate,
    efficiency_factor,
    decoupling,
    intensity,
    avg_watts,
    nullif(weighted_avg_watts, 0) as weighted_avg_watts,
    ftp_at_activity,
    distance_m / 1000.0 as distance_km,
    elevation_gain_m,
    nullif(avg_speed_mps, 0) * 3.6 as avg_speed_kph,
    nullif(avg_cadence, 0) as avg_cadence,
    nullif(calories, 0) as calories,
    -- Temperature from the recording device's own sensor (no location involved).
    -- Edge 830 on the bike reads ambient/room air; the Forerunner on the wrist
    -- reads high from body heat, so only compare watch values with each other.
    round(avg_temp_c, 1) as device_avg_temp_c,
    min_temp_c as device_min_temp_c,
    max_temp_c as device_max_temp_c,
    raw_json ->> 'device_name' as device_name,
    {{ sport_family('activity_type') }} as sport_family,
    -- Progress markers computed by intervals.icu (null where not applicable):
    -- power_hr_z2 = average watts per heartbeat while HR was in Z2 (rides);
    -- eftp_w = intervals.icu's rolling FTP estimate after this activity;
    -- gap_mps = grade-adjusted average speed (runs).
    (raw_json ->> 'icu_power_hr_z2')::numeric as power_hr_z2,
    (raw_json ->> 'icu_power_hr_z2_mins')::numeric as power_hr_z2_mins,
    (raw_json ->> 'icu_variability_index')::numeric as variability_index,
    (raw_json ->> 'icu_rolling_ftp')::numeric as eftp_w,
    (raw_json ->> 'gap')::numeric as gap_mps,
    (raw_json ->> 'paired_event_id')::bigint as paired_event_id,
    pulled_at
from {{ source('staging', 'intervals_activities_raw') }}