WITH source AS (
    SELECT * FROM "valenbisi"."public"."valenbisi_raw"
)

SELECT
    id,
    station_id,
    station_name,
    latitude,
    longitude,
    available_bikes,
    available_slots,
    station_status,
    total_capacity,
    timestamp,
    -- Derived fields
    CAST(timestamp AS DATE) as date_pk,
    EXTRACT(HOUR FROM timestamp) as hour_pk
FROM source