-- One row per ride of 15+ minutes with the aerobic-fitness markers.
--   power_hr_z2: intervals.icu's average watts per heartbeat while HR was in Z2.
--     Higher = more power for the same heart rate. Only trusted on steady rides
--     (variability index <= 1.10) with 10+ Z2 minutes (z2_marker_valid): a few
--     minutes of Z2 is mostly warm-up, and on the ramp test HR lags the rising power.
--   decoupling: HR drift relative to power, first vs second half (%). Only
--     meaningful on steady rides (decoupling_valid: 30+ min, variability index
--     <= 1.10); the ramp test and interval sessions are excluded that way.
--   eftp_w: intervals.icu's rolling FTP estimate; ftp_w is the FTP set at the time.

select
    a.activity_id,
    a.start_date_local::date as activity_date,
    a.activity_name,
    round(a.moving_time_min, 1) as moving_time_min,
    a.avg_watts,
    a.weighted_avg_watts,
    a.avg_heartrate,
    round(a.power_hr_z2, 3) as power_hr_z2,
    a.power_hr_z2_mins,
    coalesce(a.power_hr_z2_mins >= 10 and a.variability_index <= 1.10, false) as z2_marker_valid,
    round(a.decoupling, 1) as decoupling,
    round(a.variability_index, 2) as variability_index,
    coalesce(a.moving_time_min >= 30 and a.variability_index <= 1.10, false) as decoupling_valid,
    round(a.eftp_w) as eftp_w,
    a.ftp_at_activity as ftp_w,
    p.best_1m_w,
    p.best_5m_w,
    p.best_20m_w
from {{ ref('stg_intervals_activities') }} a
left join {{ ref('stg_activity_power_bests') }} p using (activity_id)
where a.sport_family = 'Ride'
  and a.moving_time_min >= 15
order by a.start_date_local
