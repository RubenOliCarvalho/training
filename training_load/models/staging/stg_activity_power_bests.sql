select
    activity_id,
    best_1m_w,
    best_5m_w,
    best_20m_w
from {{ source('staging', 'activity_power_bests') }}
