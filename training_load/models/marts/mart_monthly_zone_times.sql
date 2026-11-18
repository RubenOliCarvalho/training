-- Time in each heart-rate / power zone per month, matching intervals.icu's zone bars
-- (strength and yoga excluded, as intervals.icu does).
-- pct_of_total is the share of all zone time of that type in the month. SS (sweet
-- spot) overlaps power Z3/Z4, so it's excluded from the denominator and its pct
-- is relative to the same Z1-Z7 total (as intervals.icu shows it).

with zone_times as (

    select
        date_trunc('month', activity_date)::date as month,
        zone_type,
        zone,
        sum(secs) as secs
    from {{ ref('int_activity_zone_times') }}
    where counts_toward_zone_totals
    group by 1, 2, 3

)

select
    month || '-' || zone_type || '-' || zone as zone_key,
    month,
    zone_type,
    zone,
    secs,
    round(secs / 3600.0, 2) as hours,
    round(
        secs / nullif(sum(secs) filter (where zone <> 'SS') over (partition by month, zone_type), 0),
        4
    ) as pct_of_total
from zone_times
order by month, zone_type, zone
