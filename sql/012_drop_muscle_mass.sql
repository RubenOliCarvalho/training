-- Muscle mass is no longer logged or reported (26 Nov 2026); fat mass and
-- fat-free mass are derived from weight and body fat in stg_weight_log.
-- All values were already cleared. Drops the column added in 007/008.
-- Run as the staging schema owner (ruben.carvalho), after the dbt models that
-- referenced the column have been rebuilt without it.
alter table staging.weight_log_raw drop column if exists muscle_mass_kg;
