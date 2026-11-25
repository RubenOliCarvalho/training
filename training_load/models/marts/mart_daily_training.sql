with training as (

    select * from {{ ref('int_training_load_daily') }}

),

daily_activity_agg as (

    select
        start_date_local::date as activity_date,
        count(*) as activity_count,
        sum(calories) as total_calories,
        sum(distance_km) as total_distance_km,
        sum(moving_time_min) as total_moving_time_min,
        sum(avg_heartrate * moving_time_min)
         / nullif(sum(moving_time_min) filter (where avg_heartrate is not null), 0)
        as avg_heartrate_weighted
    from {{ ref('stg_intervals_activities') }}
    group by 1

),

exercise_calorie_target as (

    select target_min, target_max
    from {{ ref('targets') }}
    where metric = 'exercise_calories' and period = 'day'

),

weight_joined as (

    select
        t.calendar_date,
        w.weight_kg,
        w.body_fat_pct,
        w.fat_mass_kg,
        w.fat_free_mass_kg,
        w.muscle_mass_kg,
        (w.log_date is not null) as is_weigh_in_day
    from training t
    left join {{ ref('stg_weight_log') }} w
        on w.log_date = t.calendar_date

),

-- Each body metric is forward-filled independently: body fat / muscle mass
-- are optional when logging, so a weight-only day must not reset them.
weight_filled as (

    select
        calendar_date,
        weight_kg,
        body_fat_pct,
        fat_mass_kg,
        fat_free_mass_kg,
        muscle_mass_kg,
        is_weigh_in_day,
        count(weight_kg) over (order by calendar_date) as weight_fill_group,
        count(body_fat_pct) over (order by calendar_date) as body_fat_fill_group,
        count(fat_mass_kg) over (order by calendar_date) as fat_mass_fill_group,
        count(muscle_mass_kg) over (order by calendar_date) as muscle_mass_fill_group
    from weight_joined

),

weight_ffill as (

    select
        calendar_date,
        max(weight_kg) over (partition by weight_fill_group order by calendar_date) as weight_kg,
        max(body_fat_pct) over (partition by body_fat_fill_group order by calendar_date) as body_fat_pct,
        max(fat_mass_kg) over (partition by fat_mass_fill_group order by calendar_date) as fat_mass_kg,
        max(fat_free_mass_kg) over (partition by fat_mass_fill_group order by calendar_date) as fat_free_mass_kg,
        max(muscle_mass_kg) over (partition by muscle_mass_fill_group order by calendar_date) as muscle_mass_kg,
        is_weigh_in_day
    from weight_filled

),

-- 7-day moving averages over calendar days (the spine has one row per day);
-- null unless at least 4 of the 7 days have a reading.
recovery as (

    select
        t.calendar_date,
        w.sleep_hours,
        w.sleep_score,
        w.resting_hr,
        w.hrv,
        case when count(w.resting_hr) over last7 >= 4
            then round(avg(w.resting_hr) over last7, 1) end as resting_hr_7d_avg,
        case when count(w.hrv) over last7 >= 4
            then round(avg(w.hrv) over last7, 1) end as hrv_7d_avg,
        case when count(w.sleep_hours) over last7 >= 4
            then round(avg(w.sleep_hours) over last7, 2) end as sleep_hours_7d_avg
    from training t
    left join {{ ref('stg_intervals_wellness') }} w
        on w.wellness_date = t.calendar_date
    window last7 as (order by t.calendar_date rows between 6 preceding and current row)

),

exercise_minutes_target as (

    select target_min, target_max
    from {{ ref('targets') }}
    where metric = 'exercise_minutes' and period = 'day'

)

select
    t.calendar_date,
    t.daily_training_load,
    t.ctl,
    t.atl,
    t.tsb,
    coalesce(a.activity_count, 0) as activity_count,
    (coalesce(a.activity_count, 0) > 0) as is_active_day,
    coalesce(a.total_calories, 0) as total_calories,
    case
        when coalesce(a.activity_count, 0) = 0 then 0
        else a.total_distance_km
    end as total_distance_km,
    coalesce(a.total_moving_time_min, 0) as total_moving_time_min,
    a.avg_heartrate_weighted,
    ect.target_min as exercise_calorie_target_min,
    ect.target_max as exercise_calorie_target_max,
    case
        when coalesce(a.total_calories, 0) < ect.target_min then 'below_target'
        when coalesce(a.total_calories, 0) > ect.target_max then 'above_target'
        else 'within_target'
    end as exercise_calorie_target_status,
    wf.weight_kg,
    wf.body_fat_pct,
    wf.muscle_mass_kg,
    wf.fat_mass_kg,
    wf.fat_free_mass_kg,
    wf.is_weigh_in_day,
    r.sleep_hours,
    r.sleep_score,
    r.resting_hr,
    r.hrv,
    r.resting_hr_7d_avg,
    r.hrv_7d_avg,
    r.sleep_hours_7d_avg,
    emt.target_min as exercise_minutes_target_min,
    emt.target_max as exercise_minutes_target_max,
    case
        when coalesce(a.total_moving_time_min, 0) < emt.target_min then 'below_target'
        when coalesce(a.total_moving_time_min, 0) > emt.target_max then 'above_target'
        else 'within_target'
    end as exercise_minutes_target_status
from training t
left join daily_activity_agg a
    on a.activity_date = t.calendar_date
left join weight_ffill wf
    on wf.calendar_date = t.calendar_date
left join recovery r
    on r.calendar_date = t.calendar_date
cross join exercise_calorie_target ect
cross join exercise_minutes_target emt
order by t.calendar_date