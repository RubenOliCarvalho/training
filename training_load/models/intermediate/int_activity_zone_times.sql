-- One row per activity x zone: seconds spent in each heart-rate and power zone,
-- as computed by intervals.icu (raw_json icu_hr_zone_times / icu_zone_times).
-- Zone boundaries are whatever intervals.icu had for that sport at the time.

with activities as (

    select
        activity_id,
        start_date_local::date as activity_date,
        activity_type,
        raw_json
    from {{ source('staging', 'intervals_activities_raw') }}

),

-- icu_hr_zone_times is a plain array of seconds, Z1 first
hr as (

    select
        a.activity_id,
        a.activity_date,
        a.activity_type,
        'hr' as zone_type,
        'Z' || z.ordinality as zone,
        z.secs::numeric as secs
    from activities a
    cross join lateral jsonb_array_elements_text(a.raw_json -> 'icu_hr_zone_times')
        with ordinality as z(secs, ordinality)
    where jsonb_typeof(a.raw_json -> 'icu_hr_zone_times') = 'array'

),

-- icu_zone_times is an array of {id, secs}: Z1..Z7 plus SS (sweet spot), which
-- overlaps Z3/Z4 and must not be added to the zone total
power as (

    select
        a.activity_id,
        a.activity_date,
        a.activity_type,
        'power' as zone_type,
        z.value ->> 'id' as zone,
        (z.value ->> 'secs')::numeric as secs
    from activities a
    cross join lateral jsonb_array_elements(a.raw_json -> 'icu_zone_times') as z(value)
    where jsonb_typeof(a.raw_json -> 'icu_zone_times') = 'array'

)

select
    activity_id || '-' || zone_type || '-' || zone as activity_zone_key,
    *,
    -- intervals.icu's zone summary leaves out strength and yoga (verified against
    -- its 2026 HR zone panel: excluding them matches within a few minutes).
    activity_type not in ('WeightTraining', 'Yoga') as counts_toward_zone_totals
from (
    select * from hr
    union all
    select * from power
) zones
