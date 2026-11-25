-- Plan compliance per week (Monday start), from the first week with a planned
-- workout up to the current week. Completion counts only sessions that are due
-- (done or missed); today's and upcoming sessions are shown separately.
-- Unplanned sessions are activities not matched to any planned workout.

with planned as (

    select * from {{ ref('mart_planned_sessions') }}

),

weeks as (

    select generate_series(
        (select min(week_start) from planned),
        date_trunc('week', current_date)::date,
        interval '1 week'
    )::date as week_start

),

plan_agg as (

    select
        week_start,
        count(*) as planned_sessions,
        count(*) filter (where status = 'done') as done_sessions,
        count(*) filter (where status = 'missed') as missed_sessions,
        count(*) filter (where status in ('today', 'upcoming')) as remaining_sessions,
        count(*) filter (where sport_family = 'Ride') as planned_rides,
        count(*) filter (where sport_family = 'Ride' and status = 'done') as done_rides,
        count(*) filter (where sport_family = 'Run') as planned_runs,
        count(*) filter (where sport_family = 'Run' and status = 'done') as done_runs,
        round(sum(actual_min) filter (where status = 'done')) as done_minutes,
        -- Planned minutes of sessions already due, so done vs planned compares like with like.
        round(sum(planned_min) filter (where status in ('done', 'missed'))) as planned_due_minutes,
        round(sum(mins_over_hr_cap) filter (where status = 'done' and hr_cap_applies), 1) as mins_over_hr_cap
    from planned
    group by 1

),

unplanned as (

    select
        date_trunc('week', a.start_date_local)::date as week_start,
        count(*) filter (where a.activity_type = 'Tennis') as tennis_sessions,
        count(*) filter (where a.activity_type = 'WeightTraining') as strength_sessions,
        count(*) filter (where a.activity_type not in ('Tennis', 'WeightTraining')) as other_unplanned_sessions
    from {{ ref('stg_intervals_activities') }} a
    where a.activity_id not in (select activity_id from planned where activity_id is not null)
    group by 1

)

select
    w.week_start,
    coalesce(p.planned_sessions, 0) as planned_sessions,
    coalesce(p.done_sessions, 0) as done_sessions,
    coalesce(p.missed_sessions, 0) as missed_sessions,
    coalesce(p.remaining_sessions, 0) as remaining_sessions,
    round(100.0 * p.done_sessions / nullif(p.done_sessions + p.missed_sessions, 0)) as completion_pct,
    coalesce(p.planned_rides, 0) as planned_rides,
    coalesce(p.done_rides, 0) as done_rides,
    coalesce(p.planned_runs, 0) as planned_runs,
    coalesce(p.done_runs, 0) as done_runs,
    p.planned_due_minutes,
    p.done_minutes,
    p.mins_over_hr_cap,
    coalesce(u.tennis_sessions, 0) as tennis_sessions,
    coalesce(u.strength_sessions, 0) as strength_sessions,
    coalesce(u.other_unplanned_sessions, 0) as other_unplanned_sessions,
    (w.week_start = date_trunc('week', current_date)::date) as is_current_week
from weeks w
left join plan_agg p using (week_start)
left join unplanned u using (week_start)
order by w.week_start
