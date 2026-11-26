-- Fat mass and fat-free mass are derived from weight and body fat of the same
-- reading, so weight = fat mass + fat-free mass holds exactly. They are null
-- when a reading has no body fat.
select
    log_date,
    weight_kg,
    body_fat_pct,
    round(weight_kg * body_fat_pct / 100, 2) as fat_mass_kg,
    round(weight_kg - weight_kg * body_fat_pct / 100, 2) as fat_free_mass_kg,
    logged_at
from {{ source('staging', 'weight_log_raw') }}
