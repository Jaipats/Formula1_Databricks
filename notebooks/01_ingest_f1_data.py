# Databricks notebook source
# MAGIC %md
# MAGIC # Formula 1 Data Ingestion from OpenF1 API
# MAGIC
# MAGIC This notebook fetches F1 race data from the OpenF1 API and stages it to Unity Catalog volumes as JSON files.
# MAGIC
# MAGIC ## 📋 Workflow
# MAGIC 1. **Run this notebook** → Fetch data from API and stage to volumes
# MAGIC 2. **Run DLT Pipeline** → Autoloader loads from volumes to Bronze/Silver/Gold tables
# MAGIC
# MAGIC ## ✨ Features
# MAGIC - Memory efficient - writes each batch immediately to volumes
# MAGIC - Incremental - processes data by session to avoid memory issues
# MAGIC - Parallel API calls - fetches multiple endpoints simultaneously
# MAGIC - Rate limit handling - automatic retry with exponential backoff
# MAGIC - Graceful error handling - skips unavailable data (422 errors)
# MAGIC
# MAGIC ## 📂 Output
# MAGIC Data is written to: `/Volumes/{catalog}/{schema}/pipeline_storage/staging/`
# MAGIC
# MAGIC ## ⏭️ Next Steps
# MAGIC After running this notebook:
# MAGIC 1. Go to **Workflows** → **Delta Live Tables**
# MAGIC 2. Find or create pipeline: `f1_data_pipeline`
# MAGIC 3. Click **Start** to run the DLT pipeline
# MAGIC 4. DLT Autoloader will automatically load the staged files into Delta tables

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

# Add utils to path
# UPDATE THIS: Replace with your actual workspace path
# Format: /Workspace/Users/YOUR_EMAIL@databricks.com/Formula1_Databricks
sys.path.append('/Workspace/Users/jaideep.patel@databricks.com/Formula1_Databricks')

# Import our modules
from config.settings import config
from utils.api_client import OpenF1Client

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Unity Catalog Resources

# COMMAND ----------

# Create catalog, schema, and volume
spark.sql(f"CREATE CATALOG IF NOT EXISTS {config.catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {config.catalog}.{config.schema}")
spark.sql(f"""
    CREATE VOLUME IF NOT EXISTS {config.catalog}.{config.schema}.raw_data
    COMMENT 'Storage for raw API data staging'
""")

volume_path = f"/Volumes/{config.catalog}/{config.schema}/raw_data"
print(f"✓ Volume ready: {volume_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Initialize API Client

# COMMAND ----------

# Create API client
api_client = OpenF1Client(
    base_url=config.api_base_url,
    rate_limit_delay=config.rate_limit_delay,
    timeout=30,
    retry_attempts=config.retry_attempts
)

print("✓ API client initialized")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Helper Function: Write Data to Volume

# COMMAND ----------


def write_to_volume(data_list, endpoint_name):
    """Write data to volume as JSON lines - memory efficient"""
    if not data_list:
        logger.warning(f"No data to write for {endpoint_name}")
        return

    import json
    from pyspark.sql import Row

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"{volume_path}/{endpoint_name}/{endpoint_name}_{timestamp}.json"

    # Write as JSON lines (one JSON object per line)
    json_lines = [json.dumps(record) for record in data_list]
    json_content = "\n".join(json_lines)

    # Write using dbutils
    dbutils.fs.put(filepath, json_content, overwrite=True)

    logger.info(f"✓ Wrote {len(data_list)} records to {filepath}")
    return filepath

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fetch and Write Data Incrementally

# COMMAND ----------


print("=" * 80)
print(f"Starting incremental data fetch for year {config.target_year}")
print("=" * 80)

start_time = datetime.now()
stats = {}

try:
    # Step 1: Fetch meetings
    if config.enabled_endpoints.get('meetings', True):
        logger.info("Fetching meetings...")
        meetings = api_client.get_meetings(config.target_year)
        if meetings:
            write_to_volume(meetings, 'meetings')
            stats['meetings'] = len(meetings)
            logger.info(f"✓ Meetings: {len(meetings)} records")
        else:
            logger.error("No meetings found - cannot continue")
            dbutils.notebook.exit("No meetings found for target year")
    else:
        logger.error("Meetings endpoint disabled - cannot continue")
        dbutils.notebook.exit("Meetings endpoint required")

    # Step 2: Fetch sessions
    if config.enabled_endpoints.get('sessions', True):
        logger.info("Fetching sessions...")
        all_sessions = []
        for meeting in meetings:
            sessions = api_client.get_sessions(meeting['meeting_key'])
            all_sessions.extend(sessions)

        if all_sessions:
            write_to_volume(all_sessions, 'sessions')
            stats['sessions'] = len(all_sessions)
            logger.info(f"✓ Sessions: {len(all_sessions)} records")
            session_keys = [s['session_key'] for s in all_sessions]
        else:
            logger.error("No sessions found")
            session_keys = []
    else:
        session_keys = []

    # Step 3: Fetch drivers (needed for car_data filtering)
    session_drivers = {}
    if config.enabled_endpoints.get('drivers', True):
        logger.info("Fetching drivers...")
        all_drivers = []
        for session_key in session_keys:
            drivers = api_client.get_drivers(session_key)
            if drivers:
                all_drivers.extend(drivers)
                session_drivers[session_key] = [
                    d['driver_number'] for d in drivers]

        if all_drivers:
            write_to_volume(all_drivers, 'drivers')
            stats['drivers'] = len(all_drivers)
            logger.info(f"✓ Drivers: {len(all_drivers)} records")

    # Step 4: Fetch session-level data (one endpoint at a time to avoid memory issues)
    session_endpoints = {
        'laps': api_client.get_laps,
        'pit': api_client.get_pit_stops,
        'stints': api_client.get_stints,
        'weather': api_client.get_weather,
        'race_control': api_client.get_race_control,
        'team_radio': api_client.get_team_radio,
        'intervals': api_client.get_intervals,
        'overtakes': api_client.get_overtakes,
        # Fixed: was get_session_results (plural)
        'session_result': api_client.get_session_result,
        'starting_grid': api_client.get_starting_grid,
    }

    for endpoint_name, fetch_method in session_endpoints.items():
        if not config.enabled_endpoints.get(endpoint_name, False):
            logger.info(f"Skipping {endpoint_name} (disabled)")
            continue

        logger.info(f"Fetching {endpoint_name}...")
        all_records = []

        for i, session_key in enumerate(session_keys):
            if (i + 1) % 5 == 0:
                logger.info(f"  Progress: {i+1}/{len(session_keys)} sessions")

            records = fetch_method(session_key)
            if records:
                all_records.extend(records)

        if all_records:
            write_to_volume(all_records, endpoint_name)
            stats[endpoint_name] = len(all_records)
            logger.info(f"✓ {endpoint_name}: {len(all_records)} records")
        else:
            logger.warning(f"No data for {endpoint_name}")

    # Step 5: Fetch car_data (with filters to reduce size)
    if config.enabled_endpoints.get('car_data', False):
        logger.info("Fetching car_data (filtered)...")

        car_filters = config.config.get('data', {}).get('car_data_filters', {})
        speed_gte = car_filters.get('speed_gte', 200)
        sample_drivers = car_filters.get('sample_drivers', True)

        all_car_data = []
        total_fetches = 0
        successful = 0

        for session_key in session_keys:
            drivers_to_fetch = session_drivers.get(session_key, [])

            # Sample first 5 drivers if filtering enabled
            if sample_drivers and len(drivers_to_fetch) > 5:
                drivers_to_fetch = drivers_to_fetch[:5]

            for driver_number in drivers_to_fetch:
                total_fetches += 1
                try:
                    car_data = api_client.get_car_data(
                        session_key, driver_number, speed_gte=speed_gte)
                    if car_data:
                        all_car_data.extend(car_data)
                        successful += 1

                        # Write in batches to avoid memory issues
                        if len(all_car_data) >= 10000:
                            write_to_volume(all_car_data, 'car_data')
                            logger.info(
                                f"  Wrote batch of {len(all_car_data)} car_data records")
                            all_car_data = []  # Clear memory

                except Exception as e:
                    logger.warning(
                        f"Skipping car_data for session {session_key}, driver {driver_number}: {e}")

        # Write remaining car_data
        if all_car_data:
            write_to_volume(all_car_data, 'car_data')

        stats['car_data'] = f"{successful}/{total_fetches} fetches successful"
        logger.info(f"✓ car_data: {successful}/{total_fetches} successful")

except Exception as e:
    logger.error(f"Fatal error during data ingestion: {e}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

print("=" * 80)
print(
    f"✓ Data ingestion completed in {duration:.2f} seconds ({duration/60:.1f} minutes)")
print("=" * 80)
print("\nData written to volume:")
for endpoint, count in stats.items():
    print(f"  {endpoint}: {count}")

print(f"\n✓ All data staged to: {volume_path}")
print("\nNext step: Run notebook 02_load_from_volume_to_delta.py to load into Delta tables")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next Steps
# MAGIC
# MAGIC Data has been staged to volume. To load into Delta tables, run:
# MAGIC
# MAGIC 1. `02_load_from_volume_to_delta.py` - Load staged data into bronze Delta tables
# MAGIC 2. DLT pipeline - Transform bronze → silver → gold
# MAGIC
# MAGIC To inspect staged data:
# MAGIC ```python
# MAGIC display(dbutils.fs.ls(f"{volume_path}/meetings"))
# MAGIC ```
