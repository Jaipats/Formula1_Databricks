# Databricks notebook source
# MAGIC %md
# MAGIC # F1 Data Pipeline - Bronze to Silver (Lakeflow)
# MAGIC
# MAGIC This Lakeflow Spark Declarative Pipeline transforms raw F1 data from bronze to silver tables.
# MAGIC
# MAGIC **Bronze Layer:** Raw data from OpenF1 API
# MAGIC **Silver Layer:** Cleaned, validated, and transformed data with proper types
# MAGIC
# MAGIC Configure the pipeline with:
# MAGIC - `catalog`: Unity Catalog name
# MAGIC - `schema`: Schema name

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Get configuration from pipeline parameters
catalog = spark.conf.get("catalog", "jai_patel_f1_data")
schema = spark.conf.get("schema", "racing_stats")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Meetings (Race Weekends)

# COMMAND ----------


@dp.table(
    name="silver_meetings",
    comment="Cleaned F1 race weekend meetings data",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "meeting_key,year"
    }
)
@dp.expect_or_drop("valid_meeting_key", "meeting_key IS NOT NULL")
@dp.expect_or_drop("valid_year", "year >= 2018 AND year <= 2030")
def silver_meetings():
    return (
        dp.read(f"{catalog}.{schema}.bronze_meetings")
        .select(
            F.col("meeting_key").cast(IntegerType()),
            F.col("meeting_name").cast(StringType()),
            F.col("meeting_official_name").cast(StringType()),
            F.col("location").cast(StringType()),
            F.col("country_name").cast(StringType()),
            F.col("country_code").cast(StringType()),
            F.col("circuit_short_name").cast(StringType()),
            F.col("circuit_key").cast(IntegerType()),
            F.col("date_start").cast(TimestampType()),
            F.col("year").cast(IntegerType()),
            F.col("gmt_offset").cast(StringType()),
            F.current_timestamp().alias("_processed_timestamp")
        )
        .dropDuplicates(["meeting_key"])
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sessions

# COMMAND ----------


@dp.table(
    name="silver_sessions",
    comment="Cleaned F1 session data (Practice, Qualifying, Race, Sprint)",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "session_key,meeting_key"
    }
)
@dp.expect_or_drop("valid_session_key", "session_key IS NOT NULL")
@dp.expect_or_drop("valid_meeting_key", "meeting_key IS NOT NULL")
def silver_sessions():
    return (
        dp.read(f"{catalog}.{schema}.bronze_sessions")
        .select(
            F.col("session_key").cast(IntegerType()),
            F.col("session_name").cast(StringType()),
            F.col("session_type").cast(StringType()),
            F.col("meeting_key").cast(IntegerType()),
            F.col("location").cast(StringType()),
            F.col("country_name").cast(StringType()),
            F.col("country_code").cast(StringType()),
            F.col("circuit_short_name").cast(StringType()),
            F.col("circuit_key").cast(IntegerType()),
            F.col("date_start").cast(TimestampType()),
            F.col("date_end").cast(TimestampType()),
            F.col("gmt_offset").cast(StringType()),
            F.col("year").cast(IntegerType()),
            F.current_timestamp().alias("_processed_timestamp")
        )
        .dropDuplicates(["session_key"])
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Drivers

# COMMAND ----------


@dp.table(
    name="silver_drivers",
    comment="F1 drivers information per session",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "driver_number,session_key"
    }
)
@dp.expect_or_drop("valid_driver_number", "driver_number IS NOT NULL")
def silver_drivers():
    return (
        dp.read(f"{catalog}.{schema}.bronze_drivers")
        .select(
            F.col("driver_number").cast(IntegerType()),
            F.col("broadcast_name").cast(StringType()),
            F.col("full_name").cast(StringType()),
            F.col("first_name").cast(StringType()),
            F.col("last_name").cast(StringType()),
            F.col("name_acronym").cast(StringType()),
            F.col("team_name").cast(StringType()),
            F.col("team_colour").cast(StringType()),
            F.col("country_code").cast(StringType()),
            F.col("session_key").cast(IntegerType()),
            F.col("meeting_key").cast(IntegerType()),
            F.col("headshot_url").cast(StringType()),
            F.current_timestamp().alias("_processed_timestamp")
        )
        .dropDuplicates(["driver_number", "session_key"])
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Laps

# COMMAND ----------


@dp.table(
    name="silver_laps",
    comment="F1 lap timing data",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "session_key,driver_number,lap_number"
    }
)
@dp.expect_or_drop("valid_lap", "lap_number IS NOT NULL AND lap_number > 0")
@dp.expect_or_drop("valid_duration", "lap_duration IS NULL OR lap_duration > 0")
def silver_laps():
    return (
        dp.read(f"{catalog}.{schema}.bronze_laps")
        .select(
            F.col("session_key").cast(IntegerType()),
            F.col("meeting_key").cast(IntegerType()),
            F.col("driver_number").cast(IntegerType()),
            F.col("lap_number").cast(IntegerType()),
            F.col("date_start").cast(TimestampType()),
            F.col("lap_duration").cast(DoubleType()),
            F.col("is_pit_out_lap").cast(BooleanType()),
            F.col("duration_sector_1").cast(DoubleType()),
            F.col("duration_sector_2").cast(DoubleType()),
            F.col("duration_sector_3").cast(DoubleType()),
            F.col("i1_speed").cast(IntegerType()),
            F.col("i2_speed").cast(IntegerType()),
            F.col("st_speed").cast(IntegerType()),
            F.col("segments_sector_1").cast(StringType()),
            F.col("segments_sector_2").cast(StringType()),
            F.col("segments_sector_3").cast(StringType()),
            F.current_timestamp().alias("_processed_timestamp")
        )
        .dropDuplicates(["session_key", "driver_number", "lap_number"])
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pit Stops

# COMMAND ----------


@dp.table(
    name="silver_pit",
    comment="F1 pit stop data",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "session_key,driver_number"
    }
)
def silver_pit():
    return (
        dp.read(f"{catalog}.{schema}.bronze_pit")
        .select(
            F.col("session_key").cast(IntegerType()),
            F.col("meeting_key").cast(IntegerType()),
            F.col("driver_number").cast(IntegerType()),
            F.col("date").cast(TimestampType()),
            F.col("lap_number").cast(IntegerType()),
            F.col("pit_duration").cast(DoubleType()),
            F.current_timestamp().alias("_processed_timestamp")
        )
        .dropDuplicates(["session_key", "driver_number", "date"])
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stints (Tyre Strategies)

# COMMAND ----------


@dp.table(
    name="silver_stints",
    comment="F1 tyre stint data",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "session_key,driver_number,stint_number"
    }
)
def silver_stints():
    return (
        dp.read(f"{catalog}.{schema}.bronze_stints")
        .select(
            F.col("session_key").cast(IntegerType()),
            F.col("meeting_key").cast(IntegerType()),
            F.col("driver_number").cast(IntegerType()),
            F.col("stint_number").cast(IntegerType()),
            F.col("lap_start").cast(IntegerType()),
            F.col("lap_end").cast(IntegerType()),
            F.col("compound").cast(StringType()),
            F.col("tyre_age_at_start").cast(IntegerType()),
            F.current_timestamp().alias("_processed_timestamp")
        )
        .dropDuplicates(["session_key", "driver_number", "stint_number"])
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Car Telemetry Data

# COMMAND ----------


@dp.table(
    name="silver_car_data",
    comment="F1 car telemetry data (speed, throttle, brake, RPM, gear)",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "session_key,driver_number,date"
    }
)
@dp.expect("valid_speed", "speed >= 0 AND speed <= 400")
@dp.expect("valid_rpm", "rpm >= 0 AND rpm <= 15000")
def silver_car_data():
    return (
        dp.read(f"{catalog}.{schema}.bronze_car_data")
        .select(
            F.col("session_key").cast(IntegerType()),
            F.col("meeting_key").cast(IntegerType()),
            F.col("driver_number").cast(IntegerType()),
            F.col("date").cast(TimestampType()),
            F.col("speed").cast(IntegerType()),
            F.col("rpm").cast(IntegerType()),
            F.col("n_gear").cast(IntegerType()),
            F.col("throttle").cast(IntegerType()),
            F.col("brake").cast(IntegerType()),
            F.col("drs").cast(IntegerType()),
            F.current_timestamp().alias("_processed_timestamp")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Position Data

# COMMAND ----------


@dp.table(
    name="silver_position",
    comment="F1 driver position throughout session",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "session_key,driver_number,date"
    }
)
def silver_position():
    return (
        dp.read(f"{catalog}.{schema}.bronze_position")
        .select(
            F.col("session_key").cast(IntegerType()),
            F.col("meeting_key").cast(IntegerType()),
            F.col("driver_number").cast(IntegerType()),
            F.col("date").cast(TimestampType()),
            F.col("position").cast(IntegerType()),
            F.current_timestamp().alias("_processed_timestamp")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Weather

# COMMAND ----------


@dp.table(
    name="silver_weather",
    comment="F1 track weather conditions",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "session_key,date"
    }
)
def silver_weather():
    return (
        dp.read(f"{catalog}.{schema}.bronze_weather")
        .select(
            F.col("session_key").cast(IntegerType()),
            F.col("meeting_key").cast(IntegerType()),
            F.col("date").cast(TimestampType()),
            F.col("air_temperature").cast(DoubleType()),
            F.col("track_temperature").cast(DoubleType()),
            F.col("humidity").cast(IntegerType()),
            F.col("pressure").cast(DoubleType()),
            F.col("rainfall").cast(IntegerType()),
            F.col("wind_speed").cast(DoubleType()),
            F.col("wind_direction").cast(IntegerType()),
            F.current_timestamp().alias("_processed_timestamp")
        )
        .dropDuplicates(["session_key", "date"])
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Race Control Messages

# COMMAND ----------


@dp.table(
    name="silver_race_control",
    comment="F1 race control messages and flags",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "session_key,date"
    }
)
def silver_race_control():
    return (
        dp.read(f"{catalog}.{schema}.bronze_race_control")
        .select(
            F.col("session_key").cast(IntegerType()),
            F.col("meeting_key").cast(IntegerType()),
            F.col("date").cast(TimestampType()),
            F.col("category").cast(StringType()),
            F.col("flag").cast(StringType()),
            F.col("lap_number").cast(IntegerType()),
            F.col("message").cast(StringType()),
            F.col("scope").cast(StringType()),
            F.col("sector").cast(IntegerType()),
            F.col("driver_number").cast(IntegerType()),
            F.current_timestamp().alias("_processed_timestamp")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Team Radio

# COMMAND ----------


@dp.table(
    name="silver_team_radio",
    comment="F1 team radio communications",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "session_key,driver_number,date"
    }
)
def silver_team_radio():
    return (
        dp.read(f"{catalog}.{schema}.bronze_team_radio")
        .select(
            F.col("session_key").cast(IntegerType()),
            F.col("meeting_key").cast(IntegerType()),
            F.col("driver_number").cast(IntegerType()),
            F.col("date").cast(TimestampType()),
            F.col("recording_url").cast(StringType()),
            F.current_timestamp().alias("_processed_timestamp")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Additional Tables (Beta Endpoints)

# COMMAND ----------


@dp.table(
    name="silver_intervals",
    comment="F1 time intervals between drivers",
    table_properties={"quality": "silver"}
)
def silver_intervals():
    return (
        dp.read(f"{catalog}.{schema}.bronze_intervals")
        .select(
            F.col("session_key").cast(IntegerType()),
            F.col("meeting_key").cast(IntegerType()),
            F.col("driver_number").cast(IntegerType()),
            F.col("date").cast(TimestampType()),
            F.col("gap_to_leader").cast(DoubleType()),
            F.col("interval").cast(DoubleType()),
            F.current_timestamp().alias("_processed_timestamp")
        )
    )


@dp.table(
    name="silver_overtakes",
    comment="F1 overtake events",
    table_properties={"quality": "silver"}
)
def silver_overtakes():
    return (
        dp.read(f"{catalog}.{schema}.bronze_overtakes")
        .withColumn("_processed_timestamp", F.current_timestamp())
    )


@dp.table(
    name="silver_session_result",
    comment="F1 session final results",
    table_properties={"quality": "silver"}
)
def silver_session_result():
    return (
        dp.read(f"{catalog}.{schema}.bronze_session_result")
        .withColumn("_processed_timestamp", F.current_timestamp())
    )


@dp.table(
    name="silver_starting_grid",
    comment="F1 starting grid positions",
    table_properties={"quality": "silver"}
)
def silver_starting_grid():
    return (
        dp.read(f"{catalog}.{schema}.bronze_starting_grid")
        .withColumn("_processed_timestamp", F.current_timestamp())
    )
