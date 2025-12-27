# Databricks notebook source
# MAGIC %md
# MAGIC # Formula 1 Data Ingestion - Incremental with Volume Staging
# MAGIC
# MAGIC This notebook fetches data from the OpenF1 API and writes it incrementally to Unity Catalog volumes.
# MAGIC
# MAGIC **Benefits of this approach:**
# MAGIC - Memory efficient - writes data incrementally instead of loading everything into memory
# MAGIC - Resilient - can resume from where it left off if interrupted
# MAGIC - Smaller API requests - filters car_data to reduce payload size
# MAGIC - Better observability - see progress as each endpoint completes
# MAGIC
# MAGIC **Configuration:**
# MAGIC - Ensure `config/pipeline_config.yaml` is configured with your Unity Catalog settings
# MAGIC - Set `use_volume_staging: true` in config (default)
# MAGIC - Adjust `car_data_filters` to reduce data volume as needed

# COMMAND ----------

# MAGIC %pip install pyyaml requests

# COMMAND ----------

from utils.volume_writer import SparkVolumeWriter
from utils.data_fetcher import F1DataFetcher
from utils.api_client import OpenF1Client
from config.settings import config
from pyspark.sql import functions as F
from datetime import datetime
import logging
import os
import sys
dbutils.library.restartPython()

# COMMAND ----------


# Add utils to path - UPDATE THIS PATH
sys.path.append(
    '/Workspace/Users/jaideep.patel@databricks.com/Formula1_Databricks')


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

# Car data filtering
car_data_config = config.config.get('data', {}).get('car_data_filters', {})
print(f"\nCar Data Filters:")
print(f"  Speed filter: >= {car_data_config.get('speed_gte', 'None')} km/h")
print(f"  Sample drivers: {car_data_config.get('sample_drivers', False)}")

print(f"\nEnabled Endpoints:")
for endpoint, enabled in config.enabled_endpoints.items():
    if enabled:
        print(f"  ✓ {endpoint}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Unity Catalog Resources

# COMMAND ----------

# Create catalog and schema if they don't exist
spark.sql(f"CREATE CATALOG IF NOT EXISTS {config.catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {config.full_schema_name}")

# Create volume for staging if it doesn't exist
spark.sql(f"""
    CREATE VOLUME IF NOT EXISTS {config.catalog}.{config.schema}.pipeline_storage
    COMMENT 'Storage for DLT pipeline checkpoints and staging data'
""")

print(f"✓ Ensured catalog and schema exist: {config.full_schema_name}")
print(
    f"✓ Ensured volume exists: {config.catalog}.{config.schema}.pipeline_storage")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Initialize Clients

# COMMAND ----------

# Create API client
api_client = OpenF1Client(
    base_url=config.api_base_url,
    rate_limit_delay=config.rate_limit_delay,
    timeout=30,
    retry_attempts=3
)

# Create volume writer
volume_writer = SparkVolumeWriter(
    spark=spark,
    catalog=config.catalog,
    schema=config.schema,
    volume="pipeline_storage",
    base_path="staging"
)

# Create data fetcher with volume writer
data_fetcher = F1DataFetcher(api_client, config, volume_writer=volume_writer)

print("✓ API client initialized")
print("✓ Volume writer initialized")
print(
    f"✓ Staging path: /Volumes/{config.catalog}/{config.schema}/pipeline_storage/staging")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fetch and Stage Data Incrementally
# MAGIC
# MAGIC This will fetch data from the API and write it to volume files incrementally.
# MAGIC Each endpoint is processed separately and written to its own directory.

# COMMAND ----------

print(f"Starting incremental data fetch for year {config.target_year}...")
print("=" * 60)

# Start timing
start_time = datetime.now()

# Fetch all data (will be written incrementally to volume)
all_data = data_fetcher.fetch_all_data()

# End timing
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

print("=" * 60)
print(f"✓ Data fetch complete in {duration:.2f} seconds!")
print(f"\nData summary:")
for endpoint, df in all_data.items():
    if not df.empty:
        print(f"  {endpoint}: {len(df)} records (in memory)")
    else:
        print(f"  {endpoint}: Written to volume")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary of Staged Files

# COMMAND ----------

# Get summary of what was written to volume
summary = volume_writer.get_summary()

print("Staged Files Summary:")
print("=" * 60)
for endpoint, file_count in summary.items():
    print(f"  {endpoint}: {file_count} batch files")

    # List actual files
    files = volume_writer.list_data_files(endpoint)
    if files:
        print(f"    Sample files:")
        for f in files[:3]:  # Show first 3 files
            print(f"      - {f}")

print(f"\n✓ All data staged to volume successfully!")
print(
    f"✓ Volume location: /Volumes/{config.catalog}/{config.schema}/pipeline_storage/staging/")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next Steps
# MAGIC
# MAGIC Data has been staged to volume. To load into Delta tables:
# MAGIC
# MAGIC 1. **Run the load notebook**: `02_load_from_volume_to_delta.py`
# MAGIC 2. **Or run DLT pipeline**: The DLT pipeline can read from volume staging
# MAGIC
# MAGIC To check staged data:
# MAGIC ```python
# MAGIC display(dbutils.fs.ls(f"/Volumes/{config.catalog}/{config.schema}/pipeline_storage/staging/car_data"))
# MAGIC ```
