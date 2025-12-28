# Databricks notebook source
# MAGIC %md
# MAGIC # Formula 1 Data Ingestion
# MAGIC
# MAGIC This notebook fetches data from the OpenF1 API and saves it to Delta tables.
# MAGIC
# MAGIC **Configuration:**
# MAGIC - Ensure `config/pipeline_config.yaml` is configured with your Unity Catalog settings
# MAGIC - The notebook will fetch data for the configured year (default: 2025)

# COMMAND ----------

# MAGIC %pip install pyyaml requests pandas

# COMMAND ----------

# ⚠️⚠️⚠️ YOUR AUTO-FORMAT IS CAUSING THE NameError! ⚠️⚠️⚠️
# When you save, your IDE moves imports here, then restartPython() kills them!
# Result: "NameError: name 'sys' is not defined"
# FIX: Disable auto-format NOW! See DISABLE_AUTO_FORMAT.md
dbutils.library.restartPython()

# COMMAND ----------

# ✅ ALL imports MUST go here (AFTER restart)
import sys
import os
import logging
from datetime import datetime
from pyspark.sql import functions as F

# Add utils to path - UPDATE THIS PATH
sys.path.append('/Workspace/Repos/<your-username>/Formula1_Databricks')

# Import our modules (config.settings needs pyyaml which was just installed)
from config.settings import config
from utils.api_client import OpenF1Client
from utils.data_fetcher import F1DataFetcher

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Display current configuration
print(f"Catalog: {config.catalog}")
print(f"Schema: {config.schema}")
print(f"Target Year: {config.target_year}")
print(f"API Base URL: {config.api_base_url}")
print(f"\nEnabled Endpoints:")
for endpoint, enabled in config.enabled_endpoints.items():
    if enabled:
        print(f"  ✓ {endpoint}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Initialize API Client

# COMMAND ----------

# Create API client
api_client = OpenF1Client(
    base_url=config.api_base_url,
    rate_limit_delay=config.rate_limit_delay,
    timeout=30,
    retry_attempts=3
)

# Create data fetcher
data_fetcher = F1DataFetcher(api_client, config)

print("API client initialized successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fetch Data from API

# COMMAND ----------

# Fetch all data
print(f"Starting data fetch for year {config.target_year}...")
print("This may take several minutes depending on the amount of data...")

all_data = data_fetcher.fetch_all_data()

print(f"\nData fetch complete! Retrieved data for {len(all_data)} endpoints:")
for endpoint, df in all_data.items():
    print(f"  {endpoint}: {len(df)} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Unity Catalog Schema (if not exists)

# COMMAND ----------

# Create catalog and schema if they don't exist
spark.sql(f"CREATE CATALOG IF NOT EXISTS {config.catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {config.full_schema_name}")

print(f"Ensured catalog and schema exist: {config.full_schema_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save Data to Bronze Tables

# COMMAND ----------

# Save each DataFrame to a bronze (raw) Delta table
for endpoint, df in all_data.items():
    if df.empty:
        print(f"Skipping {endpoint} - no data")
        continue

    table_name = config.get_bronze_table_name(endpoint)

    # Convert pandas DataFrame to Spark DataFrame
    spark_df = spark.createDataFrame(df)

    # Add ingestion metadata
    spark_df = spark_df.withColumn(
        "_ingestion_timestamp", F.current_timestamp())
    spark_df = spark_df.withColumn("_ingestion_date", F.current_date())

    # Write to Delta table (overwrite mode for full refresh)
    print(f"Writing {len(df)} records to {table_name}...")

    spark_df.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable(table_name)

    print(f"✓ Successfully wrote to {table_name}")

print("\nAll data ingestion complete!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Checks

# COMMAND ----------

# Display record counts for each table
print("Final record counts:")
print("-" * 60)

for endpoint in all_data.keys():
    table_name = config.get_bronze_table_name(endpoint)

    try:
        count = spark.table(table_name).count()
        print(f"{endpoint:20s}: {count:,} records")
    except:
        print(f"{endpoint:20s}: Table not found or error")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sample Data Preview

# COMMAND ----------

# Preview first table with data
for endpoint in ['meetings', 'sessions', 'drivers', 'laps']:
    table_name = config.get_bronze_table_name(endpoint)

    try:
        print(f"\n{'=' * 60}")
        print(f"Sample data from: {endpoint}")
        print('=' * 60)
        display(spark.table(table_name).limit(5))
        break  # Just show first available table
    except:
        continue
