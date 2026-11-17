-- Fitness (ctl), Fatigue (atl) and Form (tsb) are taken straight from intervals.icu's
-- wellness records, so they match https://intervals.icu/fitness. Nothing is recomputed here.
-- (The previous version recomputed them with its own recursion; see git history.)

with daily_load as (

    select
        start_date_local::date as activity_date,
        sum(training_load) as daily_training_load
    from {{ ref('stg_intervals_activities') }}
    group by 1

),

calendar as (

    select generate_series(
        (select min(activity_date) from daily_load),
        current_date,
        interval '1 day'
    )::date as calendar_date

),

joined as (

    select
        c.calendar_date,
        coalesce(d.daily_training_load, 0) as daily_training_load,
        w.ctl,
        w.atl,
        count(w.ctl) over (order by c.calendar_date) as ctl_fill_group,
        count(w.atl) over (order by c.calendar_date) as atl_fill_group
    from calendar c
    left join daily_load d on d.activity_date = c.calendar_date
    left join {{ ref('stg_intervals_wellness') }} w on w.wellness_date = c.calendar_date

),

-- Safety net: if intervals.icu has no record for a day, carry the last value forward
-- rather than leaving a hole in the series.
filled as (

    select
        calendar_date,
        daily_training_load,
        max(ctl) over (partition by ctl_fill_group order by calendar_date) as ctl,
        max(atl) over (partition by atl_fill_group order by calendar_date) as atl
    from joined

)

select
    calendar_date,
    daily_training_load,
    ctl,
    atl,
    ctl - atl as tsb
from filled
order by calendar_date
