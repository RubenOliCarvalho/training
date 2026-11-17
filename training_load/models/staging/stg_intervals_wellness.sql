select
    wellness_date,
    ctl,
    atl,
    ramp_rate,
    ctl_load,
    atl_load,
    pulled_at
from {{ source('staging', 'intervals_wellness_raw') }}
