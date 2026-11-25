-- One row per planned workout with the activity that fulfilled it, if any.
--
-- Matching: intervals.icu's own pairing (paired_activity_id) first. It misses
-- sessions whose recorded type differs from the plan (planned "Run", recorded
-- "TrailRun"), so unpaired workouts fall back to an unpaired activity of the
-- same sport family on the same day, closest in duration to the plan.
-- Status is relative to the day the models were built (current_date).

with events as (

    select * from {{ ref('stg_intervals_events') }}

),

activities as (

    select
        activity_id,
        start_date_local::date as activity_date,
        sport_family,
        activity_name,
        moving_time_min,
        avg_heartrate,
        max_heartrate,
        avg_watts,
        paired_event_id
    from {{ ref('stg_intervals_activities') }}

),

-- Minutes above the easy cap (HR Z3 and up = above 140 bpm with current zones).
hr_over_cap as (

    select
        activity_id,
        sum(secs) filter (where zone in ('Z3', 'Z4', 'Z5', 'Z6', 'Z7')) / 60.0 as mins_over_hr_cap
    from {{ ref('int_activity_zone_times') }}
    where zone_type = 'hr'
    group by 1

),

paired_by_icu as (

    select e.event_id, a.activity_id
    from events e
    join activities a on a.activity_id = e.paired_activity_id

),

fallback as (

    select e.event_id, m.activity_id
    from events e
    cross join lateral (
        select a.activity_id
        from activities a
        where a.activity_date = e.event_date
          and a.sport_family = e.sport_family
          and a.activity_id not in (select activity_id from paired_by_icu)
          and (a.paired_event_id is null or a.paired_event_id = e.event_id)
        order by abs(a.moving_time_min - coalesce(e.planned_min, a.moving_time_min))
        limit 1
    ) m
    where e.event_id not in (select event_id from paired_by_icu)

),

matched as (

    select event_id, activity_id, 'intervals.icu' as matched_by from paired_by_icu
    union all
    select event_id, activity_id, 'same day and sport' as matched_by from fallback

)

select
    e.event_id,
    e.event_date,
    date_trunc('week', e.event_date)::date as week_start,
    e.sport_family,
    e.event_type,
    e.event_name,
    round(e.planned_min, 1) as planned_min,
    case
        when m.activity_id is not null then 'done'
        when e.event_date > current_date then 'upcoming'
        when e.event_date = current_date then 'today'
        else 'missed'
    end as status,
    m.activity_id,
    m.matched_by,
    a.activity_name,
    round(a.moving_time_min, 1) as actual_min,
    round(100 * a.moving_time_min / nullif(e.planned_min, 0)) as duration_pct,
    a.avg_heartrate,
    a.max_heartrate,
    a.avg_watts,
    round(h.mins_over_hr_cap, 1) as mins_over_hr_cap,
    -- The 140 bpm cap is for easy sessions; tests and harder sets are exempt.
    not (e.event_name ilike any (array[
        '%ramp test%', '%tempo%', '%steadystate%', '%force%', '%hill%', '%interval%'
    ])) as hr_cap_applies
from events e
left join matched m on m.event_id = e.event_id
left join activities a on a.activity_id = m.activity_id
left join hr_over_cap h on h.activity_id = m.activity_id
order by e.event_date, e.event_id
