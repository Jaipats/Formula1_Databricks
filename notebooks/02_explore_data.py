# Databricks notebook source
# MAGIC %md
# MAGIC # F1 Data Exploration
# MAGIC 
# MAGIC This notebook provides examples of exploring and analyzing the F1 data.
# MAGIC Use this as a template for your own analyses.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Configuration - Update with your catalog and schema
CATALOG = "jai_patel_f1_data"
SCHEMA = "racing_stats"

print(f"Using: {CATALOG}.{SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Explore Available Tables

# COMMAND ----------

# List all tables
display(spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Layer - Raw Data

# COMMAND ----------

# View raw meetings data
meetings = spark.table(f"{CATALOG}.{SCHEMA}.bronze_meetings")
print(f"Total meetings: {meetings.count()}")
display(meetings.limit(10))

# COMMAND ----------

# View raw sessions data
sessions = spark.table(f"{CATALOG}.{SCHEMA}.bronze_sessions")
print(f"Total sessions: {sessions.count()}")
display(sessions.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Layer - Cleaned Data

# COMMAND ----------

# Explore session types
session_types = spark.sql(f"""
SELECT 
    session_type,
    COUNT(*) as count,
    MIN(date_start) as first_session,
    MAX(date_start) as last_session
FROM {CATALOG}.{SCHEMA}.silver_sessions
GROUP BY session_type
ORDER BY count DESC
""")

display(session_types)

# COMMAND ----------

# Driver statistics
drivers = spark.sql(f"""
SELECT 
    full_name,
    name_acronym,
    team_name,
    country_code,
    COUNT(DISTINCT session_key) as sessions_count
FROM {CATALOG}.{SCHEMA}.silver_drivers
GROUP BY full_name, name_acronym, team_name, country_code
ORDER BY full_name
""")

display(drivers)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer - Analytics

# COMMAND ----------

# MAGIC %md
# MAGIC ### Driver Performance Analysis

# COMMAND ----------

# Top performing drivers by fastest lap
top_drivers = spark.sql(f"""
SELECT 
    full_name,
    team_name,
    AVG(fastest_lap_time) as avg_fastest_lap,
    MIN(fastest_lap_time) as best_lap_ever,
    AVG(pit_stop_count) as avg_pit_stops,
    MAX(max_speed_st) as top_speed,
    COUNT(DISTINCT session_key) as races
FROM {CATALOG}.{SCHEMA}.gold_driver_performance
GROUP BY full_name, team_name
ORDER BY avg_fastest_lap
LIMIT 15
""")

display(top_drivers)

# COMMAND ----------

# Driver performance over time
driver_trend = spark.sql(f"""
SELECT 
    s.date_start,
    s.location,
    dp.full_name,
    dp.team_name,
    dp.fastest_lap_time,
    dp.pit_stop_count
FROM {CATALOG}.{SCHEMA}.gold_driver_performance dp
JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON dp.session_key = s.session_key
WHERE s.session_type = 'Race'
ORDER BY s.date_start, dp.fastest_lap_time
""")

display(driver_trend)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Team Performance Comparison

# COMMAND ----------

team_comparison = spark.sql(f"""
SELECT 
    team_name,
    AVG(team_fastest_lap) as avg_fastest_lap,
    MIN(team_fastest_lap) as best_team_lap,
    AVG(team_avg_pit_duration) as avg_pit_duration,
    AVG(total_team_pit_stops) as avg_team_pit_stops,
    MAX(team_max_speed) as max_speed,
    COUNT(DISTINCT session_key) as races
FROM {CATALOG}.{SCHEMA}.gold_team_performance
GROUP BY team_name
ORDER BY avg_fastest_lap
""")

display(team_comparison)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Race Analysis

# COMMAND ----------

# Race summaries
race_summary = spark.sql(f"""
SELECT 
    session_name,
    location,
    date_start,
    total_laps,
    fastest_lap,
    total_pit_stops,
    yellow_flags,
    red_flags,
    safety_cars,
    avg_air_temp,
    avg_track_temp,
    CASE WHEN rainfall_detected > 0 THEN 'Yes' ELSE 'No' END as rain
FROM {CATALOG}.{SCHEMA}.gold_race_summary
ORDER BY date_start DESC
""")

display(race_summary)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Tyre Strategy Analysis

# COMMAND ----------

# Tyre compound performance
tyre_performance = spark.sql(f"""
SELECT 
    compound,
    COUNT(*) as usage_count,
    AVG(avg_lap_time_on_compound) as avg_lap_time,
    MIN(best_lap_time_on_compound) as best_lap_time,
    AVG(stint_laps) as avg_stint_length
FROM {CATALOG}.{SCHEMA}.gold_tyre_strategy
WHERE compound IS NOT NULL
GROUP BY compound
ORDER BY avg_lap_time
""")

display(tyre_performance)

# COMMAND ----------

# Team tyre strategies
team_tyre_strategy = spark.sql(f"""
SELECT 
    team_name,
    compound,
    COUNT(*) as times_used,
    AVG(avg_lap_time_on_compound) as avg_performance,
    AVG(stint_laps) as avg_stint_length
FROM {CATALOG}.{SCHEMA}.gold_tyre_strategy
WHERE compound IS NOT NULL
GROUP BY team_name, compound
ORDER BY team_name, avg_performance
""")

display(team_tyre_strategy)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Weather Impact Analysis

# COMMAND ----------

weather_impact = spark.sql(f"""
SELECT 
    CASE 
        WHEN avg_track_temp < 30 THEN 'Cold (<30°C)'
        WHEN avg_track_temp BETWEEN 30 AND 40 THEN 'Moderate (30-40°C)'
        WHEN avg_track_temp BETWEEN 40 AND 50 THEN 'Warm (40-50°C)'
        ELSE 'Hot (>50°C)'
    END as track_temp_category,
    COUNT(*) as races,
    AVG(fastest_lap) as avg_fastest_lap,
    AVG(total_pit_stops) as avg_pit_stops,
    AVG(safety_cars) as avg_safety_cars
FROM {CATALOG}.{SCHEMA}.gold_race_summary
WHERE avg_track_temp IS NOT NULL
GROUP BY track_temp_category
ORDER BY 
    CASE track_temp_category
        WHEN 'Cold (<30°C)' THEN 1
        WHEN 'Moderate (30-40°C)' THEN 2
        WHEN 'Warm (40-50°C)' THEN 3
        ELSE 4
    END
""")

display(weather_impact)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Advanced Queries

# COMMAND ----------

# MAGIC %md
# MAGIC ### Lap Time Distribution by Circuit

# COMMAND ----------

lap_distribution = spark.sql(f"""
SELECT 
    s.location,
    s.circuit_short_name,
    COUNT(l.lap_number) as total_laps,
    MIN(l.lap_duration) as fastest_lap,
    AVG(l.lap_duration) as avg_lap,
    PERCENTILE(l.lap_duration, 0.5) as median_lap,
    STDDEV(l.lap_duration) as lap_consistency
FROM {CATALOG}.{SCHEMA}.silver_laps l
JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON l.session_key = s.session_key
WHERE l.lap_duration IS NOT NULL 
    AND l.is_pit_out_lap = false
    AND s.session_type = 'Race'
GROUP BY s.location, s.circuit_short_name
ORDER BY fastest_lap
""")

display(lap_distribution)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Overtaking Analysis

# COMMAND ----------

overtakes = spark.sql(f"""
SELECT 
    oa.full_name,
    oa.team_name,
    SUM(oa.overtakes_made) as total_overtakes,
    COUNT(DISTINCT oa.session_key) as races,
    ROUND(SUM(oa.overtakes_made) * 1.0 / COUNT(DISTINCT oa.session_key), 2) as overtakes_per_race
FROM {CATALOG}.{SCHEMA}.gold_overtakes_analysis oa
GROUP BY oa.full_name, oa.team_name
HAVING SUM(oa.overtakes_made) > 0
ORDER BY total_overtakes DESC
""")

display(overtakes)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Fastest Laps Leaderboard

# COMMAND ----------

fastest_laps_leaderboard = spark.sql(f"""
SELECT 
    rank,
    full_name,
    team_name,
    location,
    lap_number,
    fastest_lap_time,
    date_start
FROM {CATALOG}.{SCHEMA}.gold_fastest_laps
WHERE rank <= 20
ORDER BY fastest_lap_time
""")

display(fastest_laps_leaderboard)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Checks

# COMMAND ----------

# Check for missing data
data_quality = spark.sql(f"""
SELECT 
    'drivers' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT driver_number) as unique_drivers,
    SUM(CASE WHEN full_name IS NULL THEN 1 ELSE 0 END) as missing_names
FROM {CATALOG}.{SCHEMA}.silver_drivers

UNION ALL

SELECT 
    'laps' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT session_key) as unique_sessions,
    SUM(CASE WHEN lap_duration IS NULL THEN 1 ELSE 0 END) as missing_durations
FROM {CATALOG}.{SCHEMA}.silver_laps

UNION ALL

SELECT 
    'car_data' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT driver_number) as unique_drivers,
    SUM(CASE WHEN speed IS NULL THEN 1 ELSE 0 END) as missing_speed
FROM {CATALOG}.{SCHEMA}.silver_car_data
""")

display(data_quality)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Export Results
# MAGIC 
# MAGIC You can export any result to CSV using the UI, or programmatically:

# COMMAND ----------

# Example: Save top drivers analysis to Delta table
top_drivers.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.analysis_top_drivers")

print(f"Results saved to {CATALOG}.{SCHEMA}.analysis_top_drivers")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next Steps
# MAGIC 
# MAGIC - Create custom visualizations in Databricks SQL
# MAGIC - Build ML models for race predictions
# MAGIC - Set up alerts for data quality issues
# MAGIC - Schedule this notebook to run regularly

