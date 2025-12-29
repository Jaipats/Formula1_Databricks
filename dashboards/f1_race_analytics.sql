-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Formula 1 Race Analytics Dashboard
-- MAGIC
-- MAGIC This SQL notebook contains queries for the F1 analytics dashboard.
-- MAGIC Use Databricks SQL to create visualizations from these queries.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Dashboard Parameter
-- MAGIC Set your catalog and schema

-- COMMAND ----------

USE catalog jai_patel_f1_data;
USE schema racing_stats;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 1. Recent Race Sessions

-- COMMAND ----------

SELECT 
  s.session_name,
  s.location,
  s.country_name,
  s.date_start,
  s.session_type,
  m.meeting_name,
  COUNT(DISTINCT d.driver_number) as drivers_count
FROM silver_sessions s
JOIN silver_meetings m 
  ON s.meeting_key = m.meeting_key
LEFT JOIN silver_drivers d 
  ON s.session_key = d.session_key
GROUP BY ALL
ORDER BY s.date_start DESC
LIMIT 20;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 2. Fastest Lap Times by Driver

-- COMMAND ----------

SELECT 
  rank,
  full_name as driver,
  team_name as team,
  session_name,
  location,
  lap_number,
  ROUND(fastest_lap_time, 3) as lap_time_seconds,
  date_start
FROM gold_fastest_laps
WHERE date_start >= CURRENT_DATE() - INTERVAL '90' DAYS
ORDER BY date_start DESC, rank
LIMIT 50;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 3. Driver Performance Comparison

-- COMMAND ----------

SELECT 
  s.location,
  s.session_name,
  dp.full_name as driver,
  dp.team_name as team,
  dp.total_laps,
  ROUND(dp.fastest_lap_time, 3) as fastest_lap,
  ROUND(dp.avg_lap_time, 3) as avg_lap_time,
  ROUND(dp.lap_time_consistency, 3) as consistency_std,
  dp.pit_stop_count,
  ROUND(dp.avg_pit_duration, 2) as avg_pit_duration,
  dp.max_speed_st as max_speed_kmh
FROM gold_driver_performance dp
JOIN silver_sessions s 
  ON dp.session_key = s.session_key
WHERE s.session_type IN ('Race', 'Sprint')
  AND s.date_start >= CURRENT_DATE() - INTERVAL '90' DAYS
ORDER BY s.date_start DESC, dp.fastest_lap_time ASC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 4. Team Performance Rankings

-- COMMAND ----------

SELECT 
  s.location,
  s.session_name,
  tp.team_name,
  ROUND(tp.team_fastest_lap, 3) as fastest_lap,
  ROUND(tp.team_avg_lap_time, 3) as avg_lap_time,
  tp.total_team_pit_stops,
  ROUND(tp.team_avg_pit_duration, 2) as avg_pit_duration,
  tp.team_max_speed
FROM gold_team_performance tp
JOIN silver_sessions s 
  ON tp.session_key = s.session_key
WHERE s.session_type IN ('Race', 'Sprint')
  AND s.date_start >= CURRENT_DATE() - INTERVAL '90' DAYS
ORDER BY s.date_start DESC, tp.team_fastest_lap ASC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 5. Tyre Strategy Analysis

-- COMMAND ----------

SELECT 
  s.location,
  s.session_name,
  ts.full_name as driver,
  ts.team_name,
  ts.stint_number,
  ts.compound,
  ts.stint_laps,
  ts.tyre_age_at_start,
  ROUND(ts.avg_lap_time_on_compound, 3) as avg_lap_time,
  ROUND(ts.best_lap_time_on_compound, 3) as best_lap_time
FROM gold_tyre_strategy ts
JOIN silver_sessions s 
  ON ts.session_key = s.session_key
WHERE s.session_type IN ('Race', 'Sprint')
  AND s.date_start >= CURRENT_DATE() - INTERVAL '90' DAYS
ORDER BY s.date_start DESC, ts.driver_number, ts.stint_number;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 6. Weather Impact on Performance

-- COMMAND ----------

SELECT 
  s.location,
  s.session_name,
  s.date_start,
  ROUND(AVG(w.air_temperature), 1) as avg_air_temp_c,
  ROUND(AVG(w.track_temperature), 1) as avg_track_temp_c,
  ROUND(AVG(w.humidity), 0) as avg_humidity_pct,
  MAX(w.rainfall) as rain_detected,
  ROUND(AVG(w.wind_speed), 1) as avg_wind_speed_ms,
  ROUND(MIN(l.lap_duration), 3) as fastest_lap_in_conditions
FROM silver_weather w
JOIN silver_sessions s 
  ON w.session_key = s.session_key
LEFT JOIN silver_laps l 
  ON w.session_key = l.session_key
WHERE s.date_start >= CURRENT_DATE() - INTERVAL '90' DAYS
GROUP BY ALL
ORDER BY s.date_start DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 7. Race Control Incidents

-- COMMAND ----------

SELECT 
  s.location,
  s.session_name,
  rc.date,
  rc.category,
  rc.flag,
  rc.message,
  rc.lap_number,
  d.full_name as driver_affected
FROM silver_race_control rc
JOIN silver_sessions s 
  ON rc.session_key = s.session_key
LEFT JOIN silver_drivers d 
  ON rc.session_key = d.session_key 
  AND rc.driver_number = d.driver_number
WHERE s.date_start >= CURRENT_DATE() - INTERVAL '90' DAYS
  AND rc.flag IN ('YELLOW', 'RED', 'BLUE')
ORDER BY rc.date DESC
LIMIT 100;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 8. Pit Stop Performance

-- COMMAND ----------

SELECT 
  s.location,
  s.session_name,
  d.full_name as driver,
  d.team_name,
  p.lap_number,
  ROUND(p.pit_duration, 2) as pit_duration_seconds,
  p.date as pit_time
FROM silver_pit p
JOIN silver_sessions s 
  ON p.session_key = s.session_key
JOIN silver_drivers d 
  ON p.session_key = d.session_key 
  AND p.driver_number = d.driver_number
WHERE s.session_type IN ('Race', 'Sprint')
  AND s.date_start >= CURRENT_DATE() - INTERVAL '90' DAYS
  AND p.pit_duration IS NOT NULL
ORDER BY p.pit_duration ASC
LIMIT 50;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 9. Speed Trap Analysis

-- COMMAND ----------

-- SELECT 
--   s.location,
--   s.session_name,
--   d.full_name as driver,
--   d.team_name,
--   MAX(cd.speed) as max_speed_kmh,
--   MAX(cd.rpm) as max_rpm,
--   AVG(cd.speed) as avg_speed_kmh
-- FROM silver_car_data cd
-- JOIN silver_sessions s 
--   ON cd.session_key = s.session_key
-- JOIN silver_drivers d 
--   ON cd.session_key = d.session_key 
--   AND cd.driver_number = d.driver_number
-- WHERE s.date_start >= CURRENT_DATE() - INTERVAL '90' DAYS
-- GROUP BY ALL
-- ORDER BY max_speed_kmh DESC
-- LIMIT 50;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 10. Overtaking Statistics

-- COMMAND ----------

SELECT 
  s.location,
  s.session_name,
  oa.full_name as driver,
  oa.team_name,
  oa.overtakes_made
FROM gold_overtakes_analysis oa
JOIN silver_sessions s 
  ON oa.session_key = s.session_key
WHERE s.session_type IN ('Race', 'Sprint')
  AND s.date_start >= CURRENT_DATE() - INTERVAL '90' DAYS
ORDER BY oa.overtakes_made DESC, s.date_start DESC
LIMIT 30;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 11. Race Summary Statistics

-- COMMAND ----------

SELECT 
  rs.session_name,
  rs.location,
  rs.date_start,
  rs.total_laps,
  ROUND(rs.fastest_lap, 3) as fastest_lap_time,
  rs.total_pit_stops,
  rs.yellow_flags,
  rs.red_flags,
  rs.safety_cars,
  ROUND(rs.avg_air_temp, 1) as avg_air_temp_c,
  ROUND(rs.avg_track_temp, 1) as avg_track_temp_c,
  CASE WHEN rs.rainfall_detected > 0 THEN 'Yes' ELSE 'No' END as rain
FROM gold_race_summary rs
ORDER BY rs.date_start DESC
LIMIT 20;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 12. Driver Championship Points (Sample Calculation)

-- COMMAND ----------

-- Note: This is a simplified points calculation based on finishing position
-- Adjust points system based on F1 rules

WITH race_positions AS (
  SELECT 
    s.session_key,
    s.location,
    s.date_start,
    d.driver_number,
    d.full_name,
    d.team_name,
    FIRST_VALUE(pos.position) OVER (
      PARTITION BY s.session_key, d.driver_number 
      ORDER BY pos.date DESC
    ) as final_position
  FROM silver_sessions s
  JOIN silver_drivers d 
    ON s.session_key = d.session_key
  JOIN silver_position pos 
    ON s.session_key = pos.session_key 
    AND d.driver_number = pos.driver_number
  WHERE s.session_type = 'Race'
    AND s.date_start >= CURRENT_DATE() - INTERVAL '365' DAYS
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY s.session_key, d.driver_number 
    ORDER BY pos.date DESC
  ) = 1
)
SELECT 
  full_name as driver,
  team_name,
  COUNT(DISTINCT session_key) as races_entered,
  SUM(
    CASE 
      WHEN final_position = 1 THEN 25
      WHEN final_position = 2 THEN 18
      WHEN final_position = 3 THEN 15
      WHEN final_position = 4 THEN 12
      WHEN final_position = 5 THEN 10
      WHEN final_position = 6 THEN 8
      WHEN final_position = 7 THEN 6
      WHEN final_position = 8 THEN 4
      WHEN final_position = 9 THEN 2
      WHEN final_position = 10 THEN 1
      ELSE 0
    END
  ) as total_points,
  SUM(CASE WHEN final_position = 1 THEN 1 ELSE 0 END) as wins,
  SUM(CASE WHEN final_position <= 3 THEN 1 ELSE 0 END) as podiums
FROM race_positions
GROUP BY ALL
ORDER BY total_points DESC, wins DESC;

