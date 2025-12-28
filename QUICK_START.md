# Quick Start Guide - Formula 1 Data Pipeline

## 🚀 Get Started in 5 Minutes

### Step 1: Upload to Databricks Workspace

```bash
# Set your Databricks credentials
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"

# Deploy using CLI
cd /path/to/Formula1
./deploy/databricks_cli_deploy.sh
```

Or manually upload via Databricks UI:
- Go to Workspace → Import
- Upload the entire `Formula1` folder

### Step 2: Update Workspace Path

Edit the notebook you want to run and update line ~28:

```python
# Change this:
sys.path.append('/Workspace/Repos/<your-username>/Formula1_Databricks')

# To your actual path:
sys.path.append('/Workspace/Users/YOUR_EMAIL@databricks.com/Formula1_Databricks')
```

### Step 3: Choose Your Notebook

#### Option A: Quick Test (Small Datasets)
**Use**: `notebooks/01_ingest_f1_data.py`
- ✅ Simple, loads all data into memory
- ✅ Good for testing with limited endpoints
- ⚠️ May crash with large datasets

#### Option B: Production (Large Datasets) **RECOMMENDED**
**Use**: `notebooks/01_ingest_f1_data_incremental_FIXED.py`
- ✅ Memory-efficient, writes incrementally
- ✅ Won't crash even with large datasets
- ✅ Progress logging
- ✅ Batched writes for car_data

### Step 4: Configure (Optional)

Edit `config/pipeline_config.yaml`:

```yaml
# Unity Catalog
unity_catalog:
  catalog: jai_patel_f1_data  # Change to your catalog name
  schema: racing_stats

# Data settings
data:
  target_year: 2025  # Change year if needed
  
  # Reduce car_data size (prevents crashes)
  car_data_filters:
    speed_gte: 200  # Only high-speed data
    sample_drivers: true  # Only first 5 drivers

# Enable/disable endpoints
enabled_endpoints:
  meetings: true
  sessions: true
  drivers: true
  laps: true
  pit: true
  car_data: true  # Set to false if crashing
  # ... others
```

### Step 5: Run the Notebook

1. Open the notebook in Databricks
2. Run all cells (Ctrl+Shift+Enter or Run All)
3. Wait for completion (5-30 minutes depending on data size)

---

## 🐛 Common Issues

### Issue 1: `NameError: name 'config' is not defined`

**Cause**: Imports are in the wrong order

**Fix**: Ensure imports come AFTER `restartPython()`:

```python
# ✅ Correct order:
dbutils.library.restartPython()  # Cell 2
# Then in Cell 3:
from config.settings import config
```

**See**: `DATABRICKS_NOTEBOOK_SETUP.md` for details

### Issue 2: Notebook Crashes / Kernel Dies

**Cause**: Out of memory (loading too much data at once)

**Fix**: Use the memory-efficient notebook:
- Switch to `01_ingest_f1_data_incremental_FIXED.py`
- Or disable large endpoints like `car_data`, `position`, `location`

**See**: `NOTEBOOK_CRASH_FIX.md` for details

### Issue 3: `ModuleNotFoundError: No module named 'yaml'`

**Cause**: `pyyaml` not installed or imports before `restartPython()`

**Fix**: 
1. Ensure Cell 1 has: `%pip install pyyaml requests pandas`
2. Ensure Cell 2 has: `dbutils.library.restartPython()`
3. Ensure imports are in Cell 3 (AFTER restart)

### Issue 4: `422 Client Error` for car_data

**Cause**: Data not available for that session/driver

**Fix**: This is normal! The pipeline handles it gracefully.
- 422 errors are logged as INFO (not ERROR)
- Pipeline continues with available data

**See**: `API_DATA_AVAILABILITY.md` for details

### Issue 5: `429 Too Many Requests`

**Cause**: API rate limiting

**Fix**: Already handled with exponential backoff!
- Pipeline will automatically retry with increasing delays
- Increase `rate_limit_delay` in config if needed

**See**: `RATE_LIMIT_HANDLING.md` for details

---

## 📊 What Happens After Ingestion?

### Data Flow

```
OpenF1 API
    ↓
[Notebook: Ingest Data]
    ↓
Unity Catalog Volume (raw JSON)
    ↓
[Notebook: Load to Delta]
    ↓
Bronze Tables (raw data)
    ↓
[DLT Pipeline: Bronze → Silver]
    ↓
Silver Tables (cleaned data)
    ↓
[DLT Pipeline: Silver → Gold]
    ↓
Gold Tables (aggregated data)
    ↓
Dashboards / Genie Space / Apps
```

### Next Steps After Ingestion

1. **Load raw data to Delta tables**:
   ```python
   # Run: notebooks/02_load_from_volume_to_delta.py
   ```

2. **Run DLT pipeline** (transforms bronze → silver → gold):
   ```bash
   databricks pipelines create --settings dlt/pipeline_config.json
   databricks pipelines start --pipeline-id <your-pipeline-id>
   ```

3. **Explore the data**:
   ```python
   # Run: notebooks/02_explore_data.py
   ```

4. **Create dashboards**:
   - Import SQL queries from `dashboards/f1_race_analytics.sql`
   - Create visualizations in Databricks SQL

5. **Launch the app**:
   ```bash
   databricks apps deploy apps/f1_dashboard_app.py
   ```

---

## 📁 Project Structure

```
Formula1/
├── config/
│   ├── pipeline_config.yaml     # Main configuration
│   └── settings.py              # Config loader
├── notebooks/
│   ├── 01_ingest_f1_data.py                    # Simple ingestion
│   ├── 01_ingest_f1_data_incremental_FIXED.py  # Memory-efficient ✅
│   └── 02_explore_data.py                      # Data exploration
├── utils/
│   ├── api_client.py            # OpenF1 API client
│   ├── data_fetcher.py          # Data orchestration
│   └── volume_writer.py         # Volume writing
├── dlt/
│   ├── f1_bronze_to_silver.py   # Bronze → Silver
│   └── f1_gold_aggregations.py  # Silver → Gold
├── dashboards/
│   └── f1_race_analytics.sql    # Dashboard queries
└── apps/
    └── f1_dashboard_app.py      # Streamlit app
```

---

## 🎯 Recommended Workflow

### For Testing (Small Data)
1. Edit `config/pipeline_config.yaml`:
   ```yaml
   enabled_endpoints:
     meetings: true
     sessions: true
     drivers: true
     laps: true
     # Disable large endpoints
     car_data: false
     position: false
     location: false
   ```

2. Run `01_ingest_f1_data.py`
3. Check results in Unity Catalog

### For Production (Full Data)
1. Use default config (all endpoints enabled)
2. Run `01_ingest_f1_data_incremental_FIXED.py`
3. Wait for completion (20-30 minutes)
4. Run `02_load_from_volume_to_delta.py`
5. Run DLT pipeline
6. Create dashboards

---

## 📚 Documentation

- **Setup**: `README.md` - Full project overview
- **Import Issues**: `DATABRICKS_NOTEBOOK_SETUP.md`
- **Crash Issues**: `NOTEBOOK_CRASH_FIX.md`
- **API Limits**: `API_DATA_AVAILABILITY.md`
- **Rate Limits**: `RATE_LIMIT_HANDLING.md`
- **Parallel Processing**: `PARALLEL_PROCESSING_GUIDE.md`
- **Deployment**: `DATABRICKS_CLI_GUIDE.md`

---

## 🆘 Need Help?

1. **Check the error message** - most issues are documented above
2. **Read the relevant guide** - see Documentation section
3. **Check the logs** - look for ERROR or WARNING messages
4. **Simplify** - disable endpoints, reduce data size, test incrementally

---

## ✅ Success Checklist

After running the ingestion notebook, verify:

- [ ] No errors in the output
- [ ] Volume created: `/Volumes/jai_patel_f1_data/racing_stats/raw_data`
- [ ] Data files visible in volume
- [ ] Stats printed at the end showing record counts
- [ ] Notebook completed without crashing

Check data:
```python
# List files
display(dbutils.fs.ls("/Volumes/jai_patel_f1_data/racing_stats/raw_data/meetings"))

# Read sample
df = spark.read.json("/Volumes/jai_patel_f1_data/racing_stats/raw_data/meetings/*.json")
display(df.limit(5))
```

---

## 🚀 You're Ready!

Start with `01_ingest_f1_data_incremental_FIXED.py` and you'll have F1 data in your Unity Catalog in minutes! 🏎️💨
