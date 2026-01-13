WITH staging AS (
    SELECT * FROM "valenbisi"."public"."stg_valenbisi_raw"
)

SELECT
    station_id,
    station_name,
    date_pk,
    hour_pk,
    ROUND(AVG(available_bikes), 2) as avg_available_bikes,
    ROUND(AVG(available_slots), 2) as avg_available_slots,
    MIN(available_bikes) as min_available_bikes,
    MAX(available_bikes) as max_available_bikes,
    MAX(total_capacity) as total_capacity
FROM staging
GROUP BY 1, 2, 3, 4
ORDER BY date_pk DESC, hour_pk DESC, station_id