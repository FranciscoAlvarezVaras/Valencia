
  
    

  create  table "valenbisi"."public"."daily_usage__dbt_tmp"
  
  
    as
  
  (
    WITH hourly AS (
    SELECT * FROM "valenbisi"."public"."hourly_usage"
)

SELECT
    station_id,
    station_name,
    date_pk,
    ROUND(AVG(avg_available_bikes), 2) as daily_avg_bikes,
    MIN(min_available_bikes) as daily_min_bikes,
    MAX(max_available_bikes) as daily_max_bikes,
    MAX(total_capacity) as total_capacity
FROM hourly
GROUP BY 1, 2, 3
ORDER BY date_pk DESC, station_id
  );
  