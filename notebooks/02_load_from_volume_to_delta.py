# Databricks notebook source
# MAGIC %md
# MAGIC # Load F1 Data from Volume to Delta Tables
# MAGIC
# MAGIC This notebook loads staged JSON files from Unity Catalog volumes into Bronze Delta tables.
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC - Run `01_ingest_f1_data_incremental.py` first to stage data to volumes
# MAGIC
# MAGIC **What this does:**
# MAGIC - Reads JSON files from volume staging directories
# MAGIC - Loads into Bronze Delta tables with schema inference
# MAGIC - Adds ingestion metadata
# MAGIC - Handles empty/missing data gracefully

# COMMAND ----------

from config.settings import config
import sys
from pyspark.sql import functions as F
from datetime import datetime

# Add utils to path - UPDATE THIS PATH
sys.path.append('/Workspace/Users/jaideep.patel@databricks.com/Formula1')


# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

print(f"Catalog: {config.catalog}")
print(f"Schema: {config.schema}")
print(
    f"Volume staging path: /Volumes/{config.catalog}/{config.schema}/pipeline_storage/staging/")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Helper Functions

# COMMAND ----------


def load_endpoint_from_volume(endpoint_name):
    """
    Load data for an endpoint from volume staging to Delta table

    Args:
        endpoint_name: Name of the endpoint (e.g., 'car_data', 'laps')

    Returns:
        Number of records loaded
    """
    volume_path = f"/Volumes/{config.catalog}/{config.schema}/pipeline_storage/staging/{endpoint_name}/"
    table_name = config.get_bronze_table_name(endpoint_name)

    try:
        # Check if path exists
        files = dbutils.fs.ls(volume_path)
        json_files = [f.path for f in files if f.path.endswith(
            '.json') and not f.name.startswith('_')]

        if not json_files:
            print(f"⚠ No data files found for {endpoint_name}")
            return 0

        print(f"Loading {endpoint_name} from {len(json_files)} files...")

        # Read JSON files
        df = spark.read.option("multiLine", "false").json(volume_path)

        # Add ingestion metadata
        df = df.withColumn("_ingestion_timestamp", F.current_timestamp())
        df = df.withColumn("_ingestion_date", F.current_date())

        record_count = df.count()

        if record_count == 0:
            print(f"⚠ No records found in {endpoint_name} files")
            return 0

        # Write to Delta table
        print(f"Writing {record_count:,} records to {table_name}...")

        df.write \
            .format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable(table_name)

        print(
            f"✓ Successfully loaded {record_count:,} records to {table_name}")
        return record_count

    except Exception as e:
        print(f"✗ Error loading {endpoint_name}: {str(e)}")
        return 0

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load All Endpoints

# COMMAND ----------


# Get list of endpoints that have staged data
staging_root = f"/Volumes/{config.catalog}/{config.schema}/pipeline_storage/staging/"

try:
    endpoint_dirs = [f.name.rstrip('/')
                     for f in dbutils.fs.ls(staging_root) if f.isDir()]
    print(f"Found staged data for {len(endpoint_dirs)} endpoints:")
    for endpoint in endpoint_dirs:
        print(f"  - {endpoint}")
except Exception as e:
    print(f"Error listing staging directories: {str(e)}")
    endpoint_dirs = []

# COMMAND ----------

# Load each endpoint
results = {}
total_records = 0

print("=" * 60)
print("Loading data from volume to Delta tables...")
print("=" * 60)

for endpoint in endpoint_dirs:
    records = load_endpoint_from_volume(endpoint)
    results[endpoint] = records
    total_records += records
    print()

print("=" * 60)
print("Load Summary:")
print("=" * 60)
for endpoint, count in results.items():
    if count > 0:
        print(f"  {endpoint:20s}: {count:,} records")
    else:
        print(f"  {endpoint:20s}: No data")

print(f"\n✓ Total records loaded: {total_records:,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Tables

# COMMAND ----------

# List bronze tables
bronze_tables = spark.sql(f"""
    SHOW TABLES IN {config.full_schema_name} LIKE 'bronze_*'
""")

display(bronze_tables)

# COMMAND ----------

# Show record counts
record_counts = []

for endpoint in results.keys():
    table_name = config.get_bronze_table_name(endpoint)
    try:
        count = spark.table(table_name).count()
        record_counts.append((endpoint, count))
    except:
        pass

if record_counts:
    counts_df = spark.createDataFrame(
        record_counts, ["endpoint", "record_count"])
    display(counts_df.orderBy(F.desc("record_count")))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sample Data Preview

# COMMAND ----------

# Preview first table with data
for endpoint in results.keys():
    if results[endpoint] > 0:
        table_name = config.get_bronze_table_name(endpoint)
        print(f"Sample data from: {table_name}")
        display(spark.table(table_name).limit(10))
        break

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next Steps
# MAGIC
# MAGIC Bronze tables are now loaded! Next:
# MAGIC
# MAGIC 1. **Run DLT Pipeline** to create Silver and Gold tables
# MAGIC 2. **Create dashboards** using the analytical queries
# MAGIC 3. **Set up Genie Space** for natural language queries
# MAGIC
# MAGIC To clean up staging files after successful load:
# MAGIC ```python
# MAGIC # dbutils.fs.rm(f"/Volumes/{config.catalog}/{config.schema}/pipeline_storage/staging/", True)
# MAGIC ```
