# Lakeflow with Autoloader - Complete Guide

## 🎯 Overview

The F1 data pipeline now uses **Lakeflow Spark Declarative Pipelines (Lakeflow) with Autoloader** to incrementally load data from Unity Catalog volumes into Bronze Delta tables.

**This replaces** the manual `02_load_from_volume_to_delta.py` notebook with an automated, streaming solution.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Volume Staging (JSON files)                                     │
│ /Volumes/{catalog}/{schema}/pipeline_storage/staging/           │
│   ├── meetings/                                                  │
│   ├── sessions/                                                  │
│   ├── drivers/                                                   │
│   ├── laps/                                                      │
│   └── car_data/                                                  │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ Autoloader (Cloud Files)
                   │ Automatically detects new files
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ Bronze Tables (Raw Data)                                         │
│ {catalog}.{schema}.bronze_*                                      │
│   ├── bronze_meetings                                            │
│   ├── bronze_sessions                                            │
│   ├── bronze_drivers                                             │
│   └── ...                                                         │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ Lakeflow Transformations
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ Silver Tables (Cleaned & Validated)                              │
│ {catalog}.{schema}.silver_*                                      │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ Gold Tables (Aggregated Analytics)                               │
│ {catalog}.{schema}.gold_*                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Benefits of Autoloader

### 1. **Incremental Processing**
- Only processes new files added to volumes
- Keeps track of processed files automatically
- No need to manually track what's been loaded

### 2. **Schema Evolution**
- Automatically infers schema from JSON files
- Handles schema changes gracefully
- Schema hints ensure correct types for key columns

### 3. **Exactly-Once Semantics**
- Each file is processed exactly once
- No duplicates, no missing data
- Built-in checkpointing

### 4. **Scalability**
- Handles millions of files efficiently
- Optimized for cloud object stores
- Parallel processing

### 5. **Production-Ready**
- Fault tolerant and resumable
- Automatic retries on failures
- Built for 24/7 operation

---

## 📋 Files in the Pipeline

### 1. Volume to Bronze (NEW!)
**File**: `dlt/f1_volume_to_bronze_autoloader.py`

Uses Autoloader to load JSON files from volumes:
```python
@dp.table(name="bronze_meetings")
def bronze_meetings():
    return (
        spark.readStream
        .format("cloudFiles")  # Autoloader
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaLocation", f"{volume_base_path}/_schemas/meetings")
        .load(f"{volume_base_path}/meetings/")
        .withColumn("_ingestion_timestamp", F.current_timestamp())
    )
```

**Features**:
- Streaming reads from volumes
- Automatic schema inference with hints
- Adds ingestion metadata
- Stores schema in `_schemas/` subdirectory

### 2. Bronze to Silver
**File**: `dlt/f1_bronze_to_silver.py`

Transforms bronze to silver (unchanged):
- Type casting and validation
- Data quality checks
- Deduplication
- Adds processing timestamp

### 3. Gold Aggregations
**File**: `dlt/f1_gold_aggregations.py`

Creates analytical tables (unchanged):
- Race summaries
- Driver statistics
- Performance metrics

---

## 🔧 Configuration

### Pipeline Configuration
**File**: `dlt/pipeline_config.json`

```json
{
  "name": "f1_data_pipeline",
  "storage": "/Volumes/jai_patel_f1_data/racing_stats/pipeline_storage",
  "configuration": {
    "catalog": "jai_patel_f1_data",
    "schema": "racing_stats"
  },
  "libraries": [
    {
      "notebook": {
        "path": "/Workspace/.../f1_volume_to_bronze_autoloader"
      }
    },
    {
      "notebook": {
        "path": "/Workspace/.../f1_bronze_to_silver"
      }
    },
    {
      "notebook": {
        "path": "/Workspace/.../f1_gold_aggregations"
      }
    }
  ]
}
```

**Key settings**:
- `storage`: Location for checkpoints and metadata
- `catalog` & `schema`: Unity Catalog location
- `libraries`: Lakeflow notebooks in execution order

---

## 📖 How to Use

### Step 1: Run Data Ingestion
```bash
# Fetch data from API and stage to volumes
# Run in Databricks: notebooks/01_ingest_f1_data_incremental_FIXED.py
```

This creates JSON files in:
```
/Volumes/{catalog}/{schema}/pipeline_storage/staging/
  ├── meetings/meetings_20250101_120000.json
  ├── sessions/sessions_20250101_120100.json
  └── ...
```

### Step 2: Run Lakeflow Pipeline
```bash
# Option A: Using Databricks UI
# 1. Go to Workflows → Lakeflow Spark Declarative Pipelines
# 2. Find "f1_data_pipeline"
# 3. Click "Start"

# Option B: Using Databricks CLI
databricks pipelines start --pipeline-id <pipeline-id>
```

**What happens**:
1. Autoloader detects new JSON files in volumes
2. Creates Bronze tables with raw data
3. Transforms Bronze → Silver (cleaned)
4. Aggregates Silver → Gold (analytics)

### Step 3: Query the Data
```sql
-- Bronze (raw)
SELECT * FROM jai_patel_f1_data.racing_stats.bronze_meetings;

-- Silver (cleaned)
SELECT * FROM jai_patel_f1_data.racing_stats.silver_meetings;

-- Gold (analytics)
SELECT * FROM jai_patel_f1_data.racing_stats.gold_race_summary;
```

---

## 🔄 Incremental Updates

### Automatic Processing
Once the Lakeflow pipeline is running, it **automatically** processes new files:

1. **Run ingestion**: Add more data to volumes
   ```python
   # Run: 01_ingest_f1_data_incremental_FIXED.py
   # New files: /Volumes/.../staging/laps/laps_20250102_080000.json
   ```

2. **Autoloader detects**: New files are automatically detected

3. **Pipeline processes**: Only new files are processed

4. **Tables updated**: Bronze, Silver, and Gold tables are updated

**No manual intervention needed!**

---

## 📊 Monitoring

### Check Pipeline Status
```sql
-- View pipeline execution history
SELECT * FROM system.livelineage.pipeline_events
WHERE pipeline_id = '<your-pipeline-id>'
ORDER BY timestamp DESC;
```

### Check Autoloader Progress
```python
# View checkpoint location
dbutils.fs.ls("/Volumes/{catalog}/{schema}/pipeline_storage/_checkpoints/")

# View schema location
dbutils.fs.ls("/Volumes/{catalog}/{schema}/pipeline_storage/staging/_schemas/")
```

### Check Processed Files
```sql
-- See which files were ingested
SELECT DISTINCT _source_file 
FROM jai_patel_f1_data.racing_stats.bronze_meetings;
```

---

## 🆚 Comparison: Manual vs Autoloader

| Feature | Manual (`02_load_from_volume_to_delta.py`) | Lakeflow Autoloader |
|---------|---------------------------------------------|----------------|
| **Processing** | Batch - load all files each time | Streaming - only new files |
| **Automation** | Manual notebook execution | Automatic with Lakeflow pipeline |
| **Deduplication** | Manual tracking required | Built-in |
| **Schema Evolution** | Manual updates | Automatic |
| **Monitoring** | Custom logging | Lakeflow UI & system tables |
| **Fault Tolerance** | Manual retries | Automatic checkpointing |
| **Performance** | Reprocesses all data | Incremental only |
| **Production Ready** | Requires orchestration | Built for 24/7 |

**Recommendation**: Use Lakeflow Autoloader for production pipelines!

---

## 🛠️ Troubleshooting

### Issue: No data in Bronze tables
**Check**:
```python
# 1. Verify files in volume
dbutils.fs.ls("/Volumes/{catalog}/{schema}/pipeline_storage/staging/meetings/")

# 2. Check Lakeflow pipeline logs
# Go to: Workflows → Lakeflow Spark Declarative Pipelines → f1_data_pipeline → Recent Updates
```

### Issue: Schema inference errors
**Solution**: Add explicit schema hints in `f1_volume_to_bronze_autoloader.py`:
```python
.option("cloudFiles.schemaHints", "meeting_key int, year int, date_start timestamp")
```

### Issue: Pipeline stuck
**Check**:
```python
# View checkpoint files
dbutils.fs.ls("/Volumes/{catalog}/{schema}/pipeline_storage/_checkpoints/bronze_meetings/")

# If needed, reset checkpoint (⚠️ will reprocess all files)
dbutils.fs.rm("/Volumes/{catalog}/{schema}/pipeline_storage/_checkpoints/bronze_meetings/", True)
```

---

## 📚 Additional Resources

- **Autoloader Documentation**: https://docs.databricks.com/ingestion/auto-loader/
- **Lakeflow Documentation**: https://docs.databricks.com/delta-live-tables/
- **Unity Catalog Volumes**: https://docs.databricks.com/data-governance/unity-catalog/volumes.html

---

## ✅ Summary

**Old workflow**:
1. Run `01_ingest_f1_data_incremental_FIXED.py` → stage files
2. Run `02_load_from_volume_to_delta.py` → load to Bronze ❌ (manual)
3. Run Lakeflow pipeline → Bronze to Silver to Gold

**New workflow** (Autoloader):
1. Run `01_ingest_f1_data_incremental_FIXED.py` → stage files
2. Run Lakeflow pipeline → **Autoloader loads to Bronze** + Silver + Gold ✅ (automatic!)

**Benefits**:
- ✅ Fully automated
- ✅ Incremental processing
- ✅ Production-ready
- ✅ Easier to maintain
- ✅ Better monitoring

---

**The `02_load_from_volume_to_delta.py` notebook is now deprecated.** Use Lakeflow with Autoloader instead!

