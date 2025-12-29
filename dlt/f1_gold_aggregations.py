# Databricks notebook source
# MAGIC %md
# MAGIC # F1 Data Pipeline - Gold Layer (Lakeflow)
# MAGIC
# MAGIC This Lakeflow Spark Declarative Pipeline creates aggregated, business-ready tables.
# MAGIC
# MAGIC **Gold Layer:** Aggregated metrics and analytics-ready tables for:
# MAGIC - Driver performance statistics
# MAGIC - Race summaries
# MAGIC - Team performance
# MAGIC - Tyre strategy analysis

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Get configuration from pipeline parameters
catalog = spark.conf.get("catalog", "jai_patel_f1_data")
schema = spark.conf.get("schema", "racing_stats")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Driver Performance Summary

# COMMAND ----------

@dp.table(
    name="gold_driver_performance",
    comment="Aggregated driver performance metrics per session",
    table_properties={
        "quality": "gold",
        "pipelines.autoOptimize.zOrderCols": "session_key,driver_number"
    }
)
def gold_driver_performance():
    """
    Calculate comprehensive driver performance metrics including:
    - Average lap times
    - Best lap times
    - Number of pit stops
    - Average speed
    - Position gained/lost
    """
    laps = dp.read(f"{catalog}.{schema}.silver_laps")
    drivers = dp.read(f"{catalog}.{schema}.silver_drivers")
    pit_stops = dp.read(f"{catalog}.{schema}.silver_pit")
    
    # Aggregate lap statistics
    lap_stats = (
        laps
        .filter(F.col("is_pit_out_lap") == False)
        .filter(F.col("lap_duration").isNotNull())
        .groupBy("session_key", "driver_number")
        .agg(
            F.count("*").alias("total_laps"),
            F.min("lap_duration").alias("fastest_lap_time"),
            F.avg("lap_duration").alias("avg_lap_time"),
            F.stddev("lap_duration").alias("lap_time_consistency"),
            F.max("i1_speed").alias("max_speed_i1"),
            F.max("i2_speed").alias("max_speed_i2"),
            F.max("st_speed").alias("max_speed_st")
        )
    )
    
    # Count pit stops
    pit_counts = (
        pit_stops
        .groupBy("session_key", "driver_number")
        .agg(
            F.count("*").alias("pit_stop_count"),
            F.avg("pit_duration").alias("avg_pit_duration"),
            F.min("pit_duration").alias("fastest_pit_stop")
        )
    )
    
    # Join all metrics
    return (
        lap_stats
        .join(drivers, ["session_key", "driver_number"], "left")
        .join(pit_counts, ["session_key", "driver_number"], "left")
        .select(
            "session_key",
            "driver_number",
            "full_name",
            "team_name",
            "total_laps",
            "fastest_lap_time",
            "avg_lap_time",
            "lap_time_consistency",
            "max_speed_i1",
            "max_speed_i2",
            "max_speed_st",
            F.coalesce("pit_stop_count", F.lit(0)).alias("pit_stop_count"),
            "avg_pit_duration",
            "fastest_pit_stop",
            F.current_timestamp().alias("_processed_timestamp")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Race Summary

# COMMAND ----------

@dp.table(
    name="gold_race_summary",
    comment="Race session summary with key statistics",
    table_properties={
        "quality": "gold"
    }
)
def gold_race_summary():
    """
    Create race summary with:
    - Total laps completed
    - Fastest lap
    - Number of pit stops
    - Weather conditions
    - Race control incidents
    """
    sessions = dp.read(f"{catalog}.{schema}.silver_sessions")
    laps = dp.read(f"{catalog}.{schema}.silver_laps")
    race_control = dp.read(f"{catalog}.{schema}.silver_race_control")
    weather = dp.read(f"{catalog}.{schema}.silver_weather")
    
    # Filter for race sessions
    race_sessions = sessions.filter(
        F.col("session_type").isin(["Race", "Sprint"])
    )
    
    # Aggregate lap data
    lap_summary = (
        laps
        .filter(F.col("lap_duration").isNotNull())
        .groupBy("session_key")
        .agg(
            F.max("lap_number").alias("total_laps"),
            F.min("lap_duration").alias("fastest_lap"),
            F.count(F.when(F.col("is_pit_out_lap"), 1)).alias("total_pit_stops")
        )
    )
    
    # Count incidents
    incident_summary = (
        race_control
        .groupBy("session_key")
        .agg(
            F.count(F.when(F.col("flag") == "YELLOW", 1)).alias("yellow_flags"),
            F.count(F.when(F.col("flag") == "RED", 1)).alias("red_flags"),
            F.count(F.when(F.col("category") == "SafetyCar", 1)).alias("safety_cars"),
            F.count("*").alias("total_messages")
        )
    )
    
    # Weather summary
    weather_summary = (
        weather
        .groupBy("session_key")
        .agg(
            F.avg("air_temperature").alias("avg_air_temp"),
            F.avg("track_temperature").alias("avg_track_temp"),
            F.max("rainfall").alias("rainfall_detected")
        )
    )
    
    return (
        race_sessions
        .join(lap_summary, "session_key", "left")
        .join(incident_summary, "session_key", "left")
        .join(weather_summary, "session_key", "left")
        .select(
            "session_key",
            "meeting_key",
            "session_name",
            "location",
            "date_start",
            "date_end",
            "total_laps",
            "fastest_lap",
            "total_pit_stops",
            F.coalesce("yellow_flags", F.lit(0)).alias("yellow_flags"),
            F.coalesce("red_flags", F.lit(0)).alias("red_flags"),
            F.coalesce("safety_cars", F.lit(0)).alias("safety_cars"),
            "avg_air_temp",
            "avg_track_temp",
            "rainfall_detected",
            F.current_timestamp().alias("_processed_timestamp")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Team Performance

# COMMAND ----------

@dp.table(
    name="gold_team_performance",
    comment="Team performance metrics per session",
    table_properties={
        "quality": "gold"
    }
)
def gold_team_performance():
    """
    Aggregate team-level performance metrics
    """
    driver_perf = dp.read(f"{catalog}.{schema}.gold_driver_performance")
    
    return (
        driver_perf
        .groupBy("session_key", "team_name")
        .agg(
            F.count("driver_number").alias("drivers_count"),
            F.min("fastest_lap_time").alias("team_fastest_lap"),
            F.avg("avg_lap_time").alias("team_avg_lap_time"),
            F.sum("pit_stop_count").alias("total_team_pit_stops"),
            F.avg("avg_pit_duration").alias("team_avg_pit_duration"),
            F.max("max_speed_st").alias("team_max_speed")
        )
        .withColumn("_processed_timestamp", F.current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tyre Strategy Analysis

# COMMAND ----------

@dp.table(
    name="gold_tyre_strategy",
    comment="Tyre compound usage and performance analysis",
    table_properties={
        "quality": "gold"
    }
)
def gold_tyre_strategy():
    """
    Analyze tyre strategies and performance by compound
    """
    stints = dp.read(f"{catalog}.{schema}.silver_stints")
    laps = dp.read(f"{catalog}.{schema}.silver_laps")
    drivers = dp.read(f"{catalog}.{schema}.silver_drivers")
    
    # Calculate stint length
    stint_analysis = (
        stints
        .withColumn(
            "stint_laps",
            F.col("lap_end") - F.col("lap_start") + 1
        )
    )
    
    # Join with lap times to get performance per compound
    stint_perf = (
        stint_analysis
        .join(
            laps,
            (stints.session_key == laps.session_key) &
            (stints.driver_number == laps.driver_number) &
            (laps.lap_number >= stints.lap_start) &
            (laps.lap_number <= stints.lap_end),
            "inner"
        )
        .groupBy(
            stints.session_key,
            stints.driver_number,
            stints.stint_number,
            "compound",
            "stint_laps",
            "tyre_age_at_start"
        )
        .agg(
            F.avg("lap_duration").alias("avg_lap_time_on_compound"),
            F.min("lap_duration").alias("best_lap_time_on_compound")
        )
    )
    
    return (
        stint_perf
        .join(
            drivers.select("session_key", "driver_number", "full_name", "team_name"),
            ["session_key", "driver_number"],
            "left"
        )
        .select(
            "session_key",
            "driver_number",
            "full_name",
            "team_name",
            "stint_number",
            "compound",
            "stint_laps",
            "tyre_age_at_start",
            "avg_lap_time_on_compound",
            "best_lap_time_on_compound",
            F.current_timestamp().alias("_processed_timestamp")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fastest Lap Rankings

# COMMAND ----------

@dp.table(
    name="gold_fastest_laps",
    comment="Fastest lap rankings per session",
    table_properties={
        "quality": "gold"
    }
)
def gold_fastest_laps():
    """
    Rank drivers by fastest lap time per session
    """
    laps = dp.read(f"{catalog}.{schema}.silver_laps")
    drivers = dp.read(f"{catalog}.{schema}.silver_drivers")
    sessions = dp.read(f"{catalog}.{schema}.silver_sessions")
    
    # Find fastest lap per driver per session
    fastest_laps = (
        laps
        .filter(F.col("lap_duration").isNotNull())
        .filter(F.col("is_pit_out_lap") == False)
        .groupBy("session_key", "driver_number")
        .agg(
            F.min("lap_duration").alias("fastest_lap_time"),
            F.min_by("lap_number", "lap_duration").alias("lap_number")
        )
    )
    
    # Add ranking
    window_spec = Window.partitionBy("session_key").orderBy("fastest_lap_time")
    
    return (
        fastest_laps
        .join(drivers, ["session_key", "driver_number"], "left")
        .join(
            sessions.select("session_key", "session_name", "location", "date_start"),
            "session_key",
            "left"
        )
        .withColumn("rank", F.row_number().over(window_spec))
        .select(
            "session_key",
            "session_name",
            "location",
            "date_start",
            "rank",
            "driver_number",
            "full_name",
            "team_name",
            "lap_number",
            "fastest_lap_time",
            F.current_timestamp().alias("_processed_timestamp")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Overtakes Analysis

# COMMAND ----------

@dp.table(
    name="gold_overtakes_analysis",
    comment="Overtake statistics per driver and session",
    table_properties={
        "quality": "gold"
    }
)
def gold_overtakes_analysis():
    """
    Analyze overtaking statistics
    """
    overtakes = dp.read(f"{catalog}.{schema}.silver_overtakes")
    drivers = dp.read(f"{catalog}.{schema}.silver_drivers")
    
    overtakes_made = (
        overtakes
        .groupBy("session_key", "meeting_key", "overtaking_driver_number")
        .agg(F.count("*").alias("overtakes_made"))
    )
    
    return (
        overtakes_made
        .join(
            drivers.select(
                F.col("session_key").alias("drv_session_key"),
                F.col("driver_number"),
                F.col("meeting_key").alias("drv_meeting_key"),
                "full_name",
                "team_name"
            ),
            (overtakes_made.session_key == F.col("drv_session_key")) &
            (overtakes_made.meeting_key == F.col("drv_meeting_key")) &
            (overtakes_made.overtaking_driver_number == drivers.driver_number),
            "left"
        )
        .select(
            overtakes_made.session_key,
            overtakes_made.overtaking_driver_number.alias("driver_number"),
            "full_name",
            "team_name",
            "overtakes_made",
            F.current_timestamp().alias("_processed_timestamp")
        )
    )
