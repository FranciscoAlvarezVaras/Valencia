WITH staging AS (
    SELECT * FROM "valenbisi"."public"."stg_valenbisi_raw"
),

latest_status AS (
    SELECT DISTINCT ON (station_id)
        station_id,
        station_name,
        latitude,
        longitude,
        available_bikes,
        available_slots,
        station_status,
        timestamp as last_updated
    FROM staging
    ORDER BY station_id, timestamp DESC
),

stats AS (
    SELECT 
        station_id,
        AVG(available_bikes) as all_time_avg_bikes
    FROM staging
    GROUP BY 1
)

SELECT
    l.*,
    ROUND(s.all_time_avg_bikes, 2) as avg_bikes
FROM latest_status l
LEFT JOIN stats s ON l.station_id = s.station_id