# Databricks notebook source
# MAGIC %md
# MAGIC # F1 Data Pipeline - Volume to Bronze (DLT with Autoloader)
# MAGIC
# MAGIC This Delta Live Tables (DLT) pipeline uses Autoloader to incrementally load JSON files  
# MAGIC from Unity Catalog volumes into Bronze Delta tables.
# MAGIC
# MAGIC **Benefits of Autoloader:**
# MAGIC - Automatically detects new files in the volume
# MAGIC - Incremental processing - only processes new files
# MAGIC - Schema inference and evolution
# MAGIC - Exactly-once semantics
# MAGIC - Scalable and production-ready
# MAGIC
# MAGIC **Source**: Unity Catalog Volume `/Volumes/{catalog}/{schema}/pipeline_storage/staging/`  
# MAGIC **Target**: Bronze tables in `{catalog}.{schema}.bronze_*`
# MAGIC
# MAGIC Configure the pipeline with:
# MAGIC - `catalog`: Unity Catalog name (default: jai_patel_f1_data)
# MAGIC - `schema`: Schema name (default: racing_stats)

# COMMAND ----------

import dlt
from pyspark.sql import functions as F

# Get configuration from pipeline parameters
catalog = spark.conf.get("catalog", "jai_patel_f1_data")
schema = spark.conf.get("schema", "racing_stats")

# Volume base path
volume_base_path = f"/Volumes/{catalog}/{schema}/pipeline_storage/staging"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Tables - Using Autoloader
# MAGIC
# MAGIC These tables use Cloud Files (Autoloader) to incrementally load JSON files from volumes.

# COMMAND ----------

@dlt.table(
    name="bronze_meetings",
    comment="Raw F1 race weekend meetings data from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_meetings():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaHints", "meeting_key int, year int")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/meetings")
        .load(f"{volume_base_path}/meetings/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_sessions",
    comment="Raw F1 session data from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_sessions():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaHints", "session_key int, meeting_key int, year int")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/sessions")
        .load(f"{volume_base_path}/sessions/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_drivers",
    comment="Raw F1 drivers data from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_drivers():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaHints", "driver_number int, session_key int, meeting_key int")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/drivers")
        .load(f"{volume_base_path}/drivers/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_laps",
    comment="Raw F1 lap timing data from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_laps():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaHints", "session_key int, driver_number int, lap_number int")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/laps")
        .load(f"{volume_base_path}/laps/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_pit",
    comment="Raw F1 pit stop data from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_pit():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaHints", "session_key int, driver_number int, lap_number int")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/pit")
        .load(f"{volume_base_path}/pit/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_stints",
    comment="Raw F1 tyre stint data from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_stints():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaHints", "session_key int, driver_number int, stint_number int")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/stints")
        .load(f"{volume_base_path}/stints/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_car_data",
    comment="Raw F1 car telemetry data from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_car_data():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaHints", "session_key int, driver_number int, speed int, rpm int")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/car_data")
        .load(f"{volume_base_path}/car_data/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_position",
    comment="Raw F1 driver position data from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_position():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaHints", "session_key int, driver_number int, position int")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/position")
        .load(f"{volume_base_path}/position/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_weather",
    comment="Raw F1 weather data from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_weather():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaHints", "session_key int, meeting_key int")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/weather")
        .load(f"{volume_base_path}/weather/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_race_control",
    comment="Raw F1 race control messages from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_race_control():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaHints", "session_key int, meeting_key int, driver_number int")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/race_control")
        .load(f"{volume_base_path}/race_control/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_team_radio",
    comment="Raw F1 team radio data from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_team_radio():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaHints", "session_key int, driver_number int")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/team_radio")
        .load(f"{volume_base_path}/team_radio/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_intervals",
    comment="Raw F1 interval data from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_intervals():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaHints", "session_key int, driver_number int")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/intervals")
        .load(f"{volume_base_path}/intervals/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_overtakes",
    comment="Raw F1 overtake events from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_overtakes():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/overtakes")
        .load(f"{volume_base_path}/overtakes/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_session_result",
    comment="Raw F1 session results from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_session_result():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/session_result")
        .load(f"{volume_base_path}/session_result/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_starting_grid",
    comment="Raw F1 starting grid data from OpenF1 API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_starting_grid():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/starting_grid")
        .load(f"{volume_base_path}/starting_grid/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )

