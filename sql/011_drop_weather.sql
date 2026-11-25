-- Weather is no longer collected or shown (25 Nov 2026, privacy: the data was
-- pulled for a fixed home location). Drops the raw weather table created by
-- 003_staging_weather_daily.sql.
-- Run as the staging schema owner (ruben.carvalho).
drop table if exists staging.weather_daily;
