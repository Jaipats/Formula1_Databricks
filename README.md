# Formula 1 Data Pipeline with Databricks

A production-ready data pipeline that ingests Formula 1 race data from the OpenF1 API into Databricks using Delta Live Tables (DLT) with Autoloader.

## 🏎️ Overview

This project provides a complete end-to-end pipeline for F1 data:
- **Ingestion**: Fetch data from OpenF1 API and stage to Unity Catalog volumes
- **Bronze Layer**: Autoloader streams JSON files into raw Delta tables
- **Silver Layer**: Clean, validate, and transform data with proper types
- **Gold Layer**: Aggregate data for analytics and dashboards

## 🚀 Quick Start

### Prerequisites
- Databricks workspace with Unity Catalog enabled
- Databricks CLI installed and configured
- Python 3.8+ (for local development)

### 1. Setup Unity Catalog

```sql
-- Run in Databricks SQL or notebook
CREATE CATALOG IF NOT EXISTS jai_patel_f1_data;
CREATE SCHEMA IF NOT EXISTS jai_patel_f1_data.racing_stats;
CREATE VOLUME IF NOT EXISTS jai_patel_f1_data.racing_stats.pipeline_storage;
```

Or use the provided script:
```bash
# In Databricks, run: setup/setup_catalog.sql
```

### 2. Deploy to Databricks

```bash
# Clone the repository
git clone https://github.com/Jaipats/Formula1_Databricks.git
cd Formula1_Databricks

# Deploy using Databricks CLI
bash deploy/databricks_cli_deploy.sh
```

### 3. Run Data Ingestion

1. Open Databricks workspace
2. Navigate to: `/Workspace/Users/YOUR_EMAIL/Formula1_Databricks/notebooks/`
3. Open: `01_ingest_f1_data.py`
4. Update the workspace path (line 36)
5. Attach to a cluster and run all cells

**Output**: JSON files in `/Volumes/{catalog}/{schema}/pipeline_storage/staging/`

### 4. Run DLT Pipeline

1. Go to **Workflows** → **Delta Live Tables**
2. Create new pipeline:
   - Name: `f1_data_pipeline`
   - Storage: `/Volumes/jai_patel_f1_data/racing_stats/pipeline_storage`
   - Configuration:
     ```json
     {
       "catalog": "jai_patel_f1_data",
       "schema": "racing_stats"
     }
     ```
   - Libraries: Add notebooks from `dlt/` folder
3. Click **Start**

**Result**: Bronze, Silver, and Gold tables created automatically!

### 5. Query the Data

```sql
-- Bronze (raw data)
SELECT * FROM jai_patel_f1_data.racing_stats.bronze_meetings;

-- Silver (cleaned data)
SELECT * FROM jai_patel_f1_data.racing_stats.silver_meetings;

-- Gold (analytics)
SELECT * FROM jai_patel_f1_data.racing_stats.gold_race_summary;
```

## 📁 Project Structure

```
Formula1_Databricks/
├── notebooks/
│   ├── 01_ingest_f1_data.py          # API ingestion to volumes
│   └── 02_explore_data.py            # Data exploration
├── dlt/
│   ├── f1_volume_to_bronze_autoloader.py  # Autoloader → Bronze
│   ├── f1_bronze_to_silver.py             # Bronze → Silver
│   ├── f1_gold_aggregations.py            # Silver → Gold
│   └── pipeline_config.json               # DLT pipeline config
├── config/
│   ├── pipeline_config.yaml          # Pipeline configuration
│   └── settings.py                   # Config loader
├── utils/
│   ├── api_client.py                 # OpenF1 API client
│   ├── data_fetcher.py               # Data fetching logic
│   └── volume_writer.py              # Volume writing utilities
├── setup/
│   └── setup_catalog.sql             # Unity Catalog setup
├── deploy/
│   └── databricks_cli_deploy.sh      # Deployment script
└── dashboards/
    └── f1_race_analytics.sql         # Sample dashboard queries
```

## 🎯 Key Features

### 1. Memory-Efficient Ingestion
- Writes data incrementally to volumes
- Processes data by session to avoid memory issues
- Handles large datasets without crashes

### 2. DLT with Autoloader
- **Incremental processing**: Only processes new files
- **Automatic schema evolution**: Handles schema changes gracefully
- **Exactly-once semantics**: No duplicates
- **Production-ready**: Fault tolerant with checkpointing

### 3. Parallel API Calls
- Fetches multiple endpoints simultaneously
- 50-60% faster than sequential fetching
- Configurable worker threads

### 4. Robust Error Handling
- **429 (Rate Limit)**: Exponential backoff with `Retry-After` header support
- **422 (Data Not Available)**: Gracefully skips and continues
- **Timeouts**: Automatic retry with configurable attempts

### 5. Medallion Architecture
- **Bronze**: Raw data from API
- **Silver**: Cleaned and validated data
- **Gold**: Aggregated analytics tables

## 📊 Data Sources

All data from [OpenF1 API](https://openf1.org/):
- **Meetings**: Race weekends
- **Sessions**: Practice, Qualifying, Race, Sprint
- **Drivers**: Driver information per session
- **Laps**: Lap timing and sector times
- **Car Data**: Telemetry (speed, RPM, throttle, brake, gear)
- **Position**: Driver positions throughout session
- **Pit Stops**: Pit stop timing
- **Stints**: Tyre strategies
- **Weather**: Track conditions
- **Race Control**: Flags and messages
- **Team Radio**: Radio communications
- **Intervals**: Time gaps between drivers
- **Overtakes**: Overtake events
- **Session Results**: Final results
- **Starting Grid**: Starting positions

## ⚙️ Configuration

Edit `config/pipeline_config.yaml`:

```yaml
# Unity Catalog
unity_catalog:
  catalog: "jai_patel_f1_data"
  schema: "racing_stats"

# Data Configuration
data:
  target_year: 2025  # Year to fetch
  batch_size: 1000   # Records per batch
  
  # Car data filters (reduce payload size)
  car_data_filters:
    speed_gte: 200        # Minimum speed (km/h)
    sample_drivers: true  # Only first 5 drivers per session

# API Configuration
api:
  rate_limit_delay: 2      # Seconds between calls
  retry_attempts: 5        # Number of retries
  parallel_endpoints: true # Enable parallel fetching
  max_workers: 3           # Parallel threads
```

## 📖 Documentation

- **[QUICK_START.md](QUICK_START.md)** - 5-minute getting started guide
- **[DLT_AUTOLOADER_GUIDE.md](DLT_AUTOLOADER_GUIDE.md)** - Complete Autoloader documentation
- **[HOW_TO_RUN.md](HOW_TO_RUN.md)** - Detailed deployment instructions
- **[DATABRICKS_NOTEBOOK_SETUP.md](DATABRICKS_NOTEBOOK_SETUP.md)** - Notebook best practices
- **[API_DATA_AVAILABILITY.md](API_DATA_AVAILABILITY.md)** - API data availability info
- **[PARALLEL_PROCESSING_GUIDE.md](PARALLEL_PROCESSING_GUIDE.md)** - Parallel API calls guide
- **[RATE_LIMIT_HANDLING.md](RATE_LIMIT_HANDLING.md)** - Rate limit handling details

## 🛠️ Troubleshooting

### Import Errors in Notebooks
**Error**: `ModuleNotFoundError: No module named 'config'`

**Solution**: Update the workspace path in the notebook (line ~36):
```python
sys.path.append('/Workspace/Users/YOUR_EMAIL@databricks.com/Formula1_Databricks')
```

### Kernel Unresponsive
**Error**: "Fatal error: The Python kernel is unresponsive"

**Cause**: Imports before `dbutils.library.restartPython()`

**Solution**: See [DATABRICKS_NOTEBOOK_SETUP.md](DATABRICKS_NOTEBOOK_SETUP.md)

### No Sessions Found
**Error**: "No sessions found"

**Cause**: Wrong parameter order in `get_sessions()`

**Solution**: Already fixed in latest version. Pull from GitHub.

### Auto-Format Breaking Notebooks
**Solution**: Disable auto-format in your IDE. See [DISABLE_AUTO_FORMAT.md](DISABLE_AUTO_FORMAT.md)

## 🔄 Pipeline Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. API Ingestion (Manual)                                   │
│    Run: notebooks/01_ingest_f1_data.py                      │
│    Output: JSON files in volumes                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. DLT Pipeline (Automatic)                                 │
│    Autoloader → Bronze → Silver → Gold                      │
│    Triggered: Workflows → Delta Live Tables                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Analytics & Dashboards                                   │
│    Query Gold tables                                        │
│    Build dashboards in Databricks                           │
└─────────────────────────────────────────────────────────────┘
```

## 📈 Performance

- **Ingestion**: ~20-30 minutes for full 2025 season
- **DLT Pipeline**: ~10-15 minutes for Bronze → Silver → Gold
- **Parallel API calls**: 50-60% faster than sequential
- **Memory usage**: < 2GB (incremental writing)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test in Databricks
5. Submit a pull request

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [OpenF1 API](https://openf1.org/) for providing F1 data
- Databricks for the amazing platform
- F1 community for inspiration

## 📧 Contact

For questions or issues:
- Create an issue on GitHub
- Check the documentation files
- Review troubleshooting guides

---

**Happy Racing! 🏎️💨**
