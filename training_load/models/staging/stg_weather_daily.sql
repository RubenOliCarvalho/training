select
    weather_date,
    latitude,
    longitude,
    temp_max_c,
    temp_min_c,
    precipitation_mm,
    wind_speed_max_kmh,
    -- WMO code; null for rows loaded before weather_code was requested
    (raw_json ->> 'weather_code')::int as weather_code,
    pulled_at
from {{ source('staging', 'weather_daily') }}