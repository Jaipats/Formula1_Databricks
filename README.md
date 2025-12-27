# Formula 1 Data Pipeline - Databricks

A comprehensive data pipeline that fetches Formula 1 race data from the [OpenF1 API](https://openf1.org/) and loads it into Databricks using Delta Live Tables (DLT). The pipeline supports Unity Catalog for data governance and provides ready-to-use dashboards and apps for race analytics.

## 🏎️ Features

- **Automated Data Ingestion**: Fetch F1 data from OpenF1 API with rate limiting and error handling
- **Parallel Processing**: Fetch multiple endpoints simultaneously (50-60% faster!)
- **Delta Live Tables Pipeline**: Bronze → Silver → Gold medallion architecture
- **Unity Catalog Integration**: Configurable catalog and schema for data governance
- **Incremental Ingestion**: Stream data to volumes for memory efficiency
- **API Rate Limiting**: Smart request management with automatic 429 handling
- **Session-Based Fetching**: Handles large datasets by splitting requests per session
- **Data Quality Checks**: Built-in DLT expectations for data validation
- **Analytics-Ready Tables**: Pre-aggregated gold tables for driver performance, team stats, and more
- **Visualization Ready**: SQL dashboards and Streamlit app included

## 📊 Data Coverage

The pipeline fetches data for **2025** (configurable) from the following OpenF1 endpoints:

### Core Data
- **Meetings**: Race weekend information
- **Sessions**: Practice, Qualifying, Race, Sprint sessions
- **Drivers**: Driver information and team assignments
- **Laps**: Lap timing and sector times
- **Position**: Driver positions throughout the session

### Telemetry & Performance
- **Car Data**: Speed, RPM, throttle, brake, gear, DRS
- **Intervals**: Time gaps between drivers
- **Pit Stops**: Pit stop timing and duration
- **Stints**: Tyre compound strategies

### Context & Events
- **Weather**: Track and air temperature, humidity, wind, rainfall
- **Race Control**: Flags, safety cars, penalties
- **Team Radio**: Radio communication recordings
- **Overtakes**: Overtaking events (beta)
- **Starting Grid**: Grid positions (beta)
- **Session Results**: Final results (beta)

## 🏗️ Project Structure

```
Formula1/
├── config/
│   ├── pipeline_config.yaml       # Main configuration file
│   └── settings.py                 # Python configuration loader
├── utils/
│   ├── api_client.py               # OpenF1 API client
│   └── data_fetcher.py             # Data orchestration logic
├── notebooks/
│   └── 01_ingest_f1_data.py        # Data ingestion notebook
├── dlt/
│   ├── f1_bronze_to_silver.py      # Bronze → Silver DLT pipeline
│   ├── f1_gold_aggregations.py     # Silver → Gold DLT pipeline
│   └── pipeline_config.json        # DLT pipeline configuration
├── dashboards/
│   └── f1_race_analytics.sql       # SQL dashboard queries
├── apps/
│   └── f1_dashboard_app.py         # Streamlit dashboard app
├── setup/
│   └── setup_catalog.sql           # Unity Catalog setup script
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🚀 Quick Start

### Prerequisites

- Databricks workspace (AWS, Azure, or GCP)
- Unity Catalog enabled
- SQL Warehouse or compute cluster
- Python 3.9+

### Step 1: Configure Unity Catalog

Edit `config/pipeline_config.yaml` to set your catalog and schema:

```yaml
unity_catalog:
  catalog: "your_catalog_name"      # Change this
  schema: "your_schema_name"         # Change this
```

### Step 2: Create Catalog and Schema

Run the setup script in Databricks SQL or a notebook:

```sql
-- In Databricks SQL Editor
%run setup/setup_catalog.sql
```

Or manually:

```sql
CREATE CATALOG IF NOT EXISTS your_catalog_name;
CREATE SCHEMA IF NOT EXISTS your_catalog_name.your_schema_name;
```

### Step 3: Upload Project to Databricks

Option A: Using Databricks Repos (Recommended)
1. Push this project to a Git repository
2. In Databricks, go to **Repos** → **Add Repo**
3. Clone your repository

Option B: Manual Upload
1. Upload files to **Workspace** → **Users** → your folder
2. Maintain the directory structure

### Step 4: Install Dependencies

In a Databricks notebook:

```python
%pip install -r requirements.txt
dbutils.library.restartPython()
```

### Step 5: Run Data Ingestion

1. Open `notebooks/01_ingest_f1_data.py`
2. Update the path in the notebook:
   ```python
   sys.path.append('/Workspace/Repos/<your-username>/Formula1')
   ```
3. Run all cells to fetch and load data into bronze tables

### Step 6: Create DLT Pipeline

1. Go to **Workflows** → **Delta Live Tables** → **Create Pipeline**
2. Configure the pipeline:
   - **Name**: `f1_data_pipeline`
   - **Product Edition**: Advanced or Pro
   - **Notebook Libraries**: 
     - Add `/Workspace/Repos/<your-username>/Formula1/dlt/f1_bronze_to_silver`
     - Add `/Workspace/Repos/<your-username>/Formula1/dlt/f1_gold_aggregations`
   - **Configuration**:
     ```
     catalog = your_catalog_name
     schema = your_schema_name
     ```
   - **Target**: Choose your catalog and schema
   - **Storage Location**: `/mnt/f1_pipeline` (or your preferred location)
3. Click **Create** and then **Start**

### Step 7: Create Dashboard

Option A: SQL Dashboard
1. Open `dashboards/f1_race_analytics.sql` in Databricks SQL Editor
2. Update the catalog and schema variables
3. Run queries and create visualizations

Option B: Genie Space (Databricks AI)
1. Go to **Genie Spaces** in Databricks
2. Create a new space
3. Select tables from `your_catalog.your_schema`
4. Ask natural language questions like:
   - "Show me fastest lap times by driver"
   - "What's the average pit stop duration by team?"
   - "Compare tyre strategies in the last race"

Option C: Streamlit App
1. Update environment variables in `apps/f1_dashboard_app.py`
2. Deploy as a Databricks App or run locally
3. Access the interactive dashboard

## ⚙️ Configuration Reference

### pipeline_config.yaml

```yaml
unity_catalog:
  catalog: "f1_data"              # Your Unity Catalog name
  schema: "racing_stats"           # Your schema name
  volume: "raw_data"               # Optional volume for raw files

api:
  base_url: "https://api.openf1.org/v1"
  rate_limit_delay: 1              # Seconds between requests
  timeout: 30                      # Request timeout
  retry_attempts: 3                # Retry on failure

data:
  target_year: 2025                # Year to fetch data for
  batch_size: 1000                 # Records per batch

endpoints:
  sessions: true                   # Enable/disable endpoints
  drivers: true
  laps: true
  car_data: true
  position: true
  # ... more endpoints
```

### Environment Variables (for Databricks App)

```bash
export DATABRICKS_SERVER_HOSTNAME="your-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
export DATABRICKS_TOKEN="your-access-token"
export F1_CATALOG="your_catalog_name"
export F1_SCHEMA="your_schema_name"
```

## 📈 Data Pipeline Architecture

```
┌─────────────────┐
│   OpenF1 API    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Data Ingestion │  ← notebooks/01_ingest_f1_data.py
│  (API Client)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Bronze Tables  │  ← Raw API data
│  (Raw Layer)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Silver Tables  │  ← Cleaned & validated data
│ (Cleaned Layer) │  ← dlt/f1_bronze_to_silver.py
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Gold Tables   │  ← Aggregated analytics
│ (Analytics)     │  ← dlt/f1_gold_aggregations.py
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Consumption Layer              │
│  • SQL Dashboards               │
│  • Genie Spaces                 │
│  • Databricks Apps              │
│  • BI Tools (Tableau, Power BI) │
└─────────────────────────────────┘
```

## 📋 Key Tables

### Bronze Layer
- `bronze_meetings`, `bronze_sessions`, `bronze_drivers`
- `bronze_laps`, `bronze_car_data`, `bronze_position`
- `bronze_pit`, `bronze_stints`, `bronze_weather`
- And more...

### Silver Layer
- `silver_meetings`, `silver_sessions`, `silver_drivers`
- `silver_laps`, `silver_car_data`, `silver_position`
- Includes data quality checks and type casting

### Gold Layer
- `gold_driver_performance` - Driver stats per session
- `gold_team_performance` - Team-level aggregations
- `gold_race_summary` - Race summaries with weather and incidents
- `gold_tyre_strategy` - Tyre compound performance analysis
- `gold_fastest_laps` - Fastest lap rankings
- `gold_overtakes_analysis` - Overtaking statistics

## 🔍 Example Queries

### Fastest Lap Times
```sql
SELECT 
  full_name as driver,
  team_name,
  location,
  fastest_lap_time
FROM f1_data.racing_stats.gold_fastest_laps
WHERE rank <= 10
ORDER BY fastest_lap_time;
```

### Driver Performance
```sql
SELECT 
  full_name,
  team_name,
  AVG(fastest_lap_time) as avg_fastest_lap,
  AVG(pit_stop_count) as avg_pit_stops,
  MAX(max_speed_st) as top_speed
FROM f1_data.racing_stats.gold_driver_performance
GROUP BY full_name, team_name
ORDER BY avg_fastest_lap;
```

### Tyre Strategy
```sql
SELECT 
  compound,
  AVG(avg_lap_time_on_compound) as avg_lap_time,
  AVG(stint_laps) as avg_stint_length
FROM f1_data.racing_stats.gold_tyre_strategy
GROUP BY compound
ORDER BY avg_lap_time;
```

## 🛠️ Maintenance

### Updating Data

To fetch new data:
1. Update `target_year` in `config/pipeline_config.yaml` if needed
2. Run the ingestion notebook: `notebooks/01_ingest_f1_data.py`
3. Run the DLT pipeline to update silver and gold tables

### Incremental Updates

For incremental updates (e.g., after each race):
- Modify the ingestion logic to fetch only new sessions
- Use DLT's `append` mode instead of `overwrite`

### Monitoring

- Check DLT pipeline runs in **Workflows** → **Delta Live Tables**
- Monitor data quality expectations in the DLT UI
- Review `_ingestion_timestamp` and `_processed_timestamp` columns

## 🐛 Troubleshooting

### API Timeout Errors
- Increase `timeout` value in `config/pipeline_config.yaml`
- Reduce `batch_size` for large datasets
- Enable/disable endpoints to reduce data volume

### Memory Issues
- Use larger cluster for data ingestion
- Process data in smaller batches (by session or meeting)
- Disable high-volume endpoints like `location`

### Missing Data
- Check if the year has data available on OpenF1
- Verify API endpoint is enabled in configuration
- Check Databricks logs for errors

### Permission Errors
- Ensure Unity Catalog permissions are granted
- Verify catalog and schema exist
- Check cluster permissions

## 📚 Resources

- [OpenF1 API Documentation](https://openf1.org/#api-endpoints)
- [Databricks Delta Live Tables](https://docs.databricks.com/delta-live-tables/index.html)
- [Unity Catalog Documentation](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- [Databricks Apps](https://docs.databricks.com/en/apps/index.html)

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Add new gold layer aggregations
- Enhance dashboard visualizations
- Improve API client error handling
- Add data quality tests

## 📝 License

This project is for educational and analytical purposes. OpenF1 is an unofficial project not associated with Formula 1 companies. F1, FORMULA ONE, and related marks are trademarks of Formula One Licensing B.V.

## ⚠️ Important Notes

1. **API Limits**: The OpenF1 API has rate limits. The pipeline includes rate limiting (1 second between requests by default).

2. **Data Volume**: Some endpoints (especially `location` and `car_data`) generate large amounts of data. These are disabled by default or require per-driver fetching.

3. **Historical Data**: The project is configured for 2025 data. Historical data (2018-2024) is available via the API.

4. **Real-Time Data**: Real-time data access requires a paid OpenF1 account. Historical data is free.

5. **Compute Costs**: Be mindful of Databricks compute costs when running large-scale data pipelines.

## 🎯 Next Steps

After setup, you can:
1. **Create Genie Space**: Use Databricks AI to query data in natural language
2. **Build Custom Dashboards**: Use Databricks SQL or integrate with Power BI/Tableau
3. **Schedule Pipeline**: Set up automated refreshes after each race
4. **Add ML Models**: Build predictive models for race outcomes
5. **Extend Analytics**: Add championship standings, driver comparisons, etc.

---

**Happy Racing! 🏁**

