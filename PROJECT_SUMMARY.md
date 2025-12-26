# Formula 1 Data Pipeline - Project Summary

## 🏁 What You Have

A **production-ready** Formula 1 data pipeline built on Databricks that:
- ✅ Fetches data from OpenF1 API (2025 season)
- ✅ Loads into Unity Catalog with configurable catalog/schema
- ✅ Implements medallion architecture (Bronze → Silver → Gold)
- ✅ Uses Delta Live Tables for automated transformations
- ✅ Includes SQL dashboards, Genie Space setup, and Streamlit app
- ✅ Handles API rate limits and large datasets via session-based fetching

## 📁 Project Structure

```
Formula1/
├── 📄 README.md                    # Complete project documentation
├── 📄 SETUP_GUIDE.md              # Detailed step-by-step setup
├── 📄 QUICK_START.md              # 15-minute quick start guide
├── 📄 ARCHITECTURE.md             # Technical architecture details
├── 📄 requirements.txt            # Python dependencies
├── 📄 .gitignore                  # Git ignore patterns
│
├── 📁 config/                     # Configuration management
│   ├── __init__.py
│   ├── pipeline_config.yaml       # Main configuration (EDIT THIS!)
│   └── settings.py                # Python config loader
│
├── 📁 utils/                      # Utility modules
│   ├── __init__.py
│   ├── api_client.py              # OpenF1 API client
│   └── data_fetcher.py            # Data orchestration
│
├── 📁 notebooks/                  # Databricks notebooks
│   ├── 01_ingest_f1_data.py       # Data ingestion from API
│   └── 02_explore_data.py         # Data exploration examples
│
├── 📁 dlt/                        # Delta Live Tables
│   ├── f1_bronze_to_silver.py     # Bronze → Silver transformations
│   ├── f1_gold_aggregations.py    # Silver → Gold aggregations
│   └── pipeline_config.json       # DLT pipeline configuration
│
├── 📁 dashboards/                 # SQL dashboards
│   └── f1_race_analytics.sql      # 12 pre-built analytical queries
│
├── 📁 apps/                       # Databricks applications
│   └── f1_dashboard_app.py        # Streamlit interactive dashboard
│
└── 📁 setup/                      # Setup scripts
    └── setup_catalog.sql          # Unity Catalog initialization
```

## 🎯 Key Features

### 1. Configurable Unity Catalog
```yaml
# config/pipeline_config.yaml
unity_catalog:
  catalog: "f1_data"      # ← CHANGE TO YOUR CATALOG
  schema: "racing_stats"   # ← CHANGE TO YOUR SCHEMA
```

### 2. Comprehensive Data Coverage

**16 Data Endpoints** from OpenF1 API:
- Core: Meetings, Sessions, Drivers, Laps
- Telemetry: Car data (speed, RPM, throttle, brake, gear)
- Performance: Position, Intervals, Pit stops, Stints
- Context: Weather, Race control, Team radio
- Analysis: Overtakes, Session results, Starting grid

### 3. Three-Layer Architecture

**Bronze Layer** (Raw)
- 15 tables with raw API data
- Metadata: `_ingestion_timestamp`, `_ingestion_date`

**Silver Layer** (Cleaned)
- Type casting and validation
- Data quality checks (DLT expectations)
- Deduplication and schema enforcement

**Gold Layer** (Analytics)
- `gold_driver_performance` - Driver stats per session
- `gold_team_performance` - Team aggregations
- `gold_race_summary` - Race metrics with weather
- `gold_tyre_strategy` - Compound performance
- `gold_fastest_laps` - Ranked lap times
- `gold_overtakes_analysis` - Overtaking stats

### 4. Smart API Management
- Rate limiting (1 request/second default)
- Session-based batching for large datasets
- Exponential backoff retry logic
- Timeout handling
- Error recovery

### 5. Ready-to-Use Dashboards

**SQL Dashboard** - 12 Pre-built Queries:
1. Recent race sessions
2. Fastest lap times by driver
3. Driver performance comparison
4. Team performance rankings
5. Tyre strategy analysis
6. Weather impact on performance
7. Race control incidents
8. Pit stop performance
9. Speed trap analysis
10. Overtaking statistics
11. Race summary statistics
12. Championship points (sample)

**Streamlit App** - 5 Interactive Views:
- Overview dashboard
- Driver performance analysis
- Team comparison
- Race details with position chart
- Tyre strategy analysis

### 6. Genie Space Ready
Connect to Databricks Genie for natural language queries:
- "Show me fastest lap times by driver"
- "What's the average pit stop duration by team?"
- "Compare tyre strategies in the last race"

## 🚀 Quick Start (3 Steps)

### 1. Configure
```yaml
# Edit config/pipeline_config.yaml
catalog: "your_catalog"
schema: "your_schema"
```

### 2. Setup Catalog
```sql
CREATE CATALOG IF NOT EXISTS your_catalog;
CREATE SCHEMA IF NOT EXISTS your_catalog.your_schema;
```

### 3. Run Pipeline
1. Upload to Databricks (Repos or Workspace)
2. Run `notebooks/01_ingest_f1_data.py`
3. Create DLT pipeline with `dlt/` notebooks
4. Start pipeline

## 📊 Sample Queries

### Fastest Laps
```sql
SELECT full_name, team_name, location, fastest_lap_time
FROM f1_data.racing_stats.gold_fastest_laps
WHERE rank <= 10;
```

### Driver Performance
```sql
SELECT full_name, AVG(fastest_lap_time) as avg_lap, MAX(max_speed_st) as top_speed
FROM f1_data.racing_stats.gold_driver_performance
GROUP BY full_name
ORDER BY avg_lap;
```

### Tyre Strategy
```sql
SELECT compound, AVG(avg_lap_time_on_compound) as avg_time
FROM f1_data.racing_stats.gold_tyre_strategy
GROUP BY compound;
```

## 🛠️ Technologies Used

- **Databricks**: Platform and notebooks
- **Unity Catalog**: Data governance
- **Delta Lake**: Storage format
- **Delta Live Tables**: Pipeline orchestration
- **Apache Spark**: Distributed processing
- **Python**: Data ingestion
- **SQL**: Analytics queries
- **Streamlit**: Interactive dashboards

## 📈 Data Pipeline Flow

```
OpenF1 API
    ↓
Data Ingestion (Notebook)
    ↓
Bronze Tables (Raw Delta)
    ↓
DLT Pipeline (Bronze → Silver)
    ↓
Silver Tables (Cleaned Delta)
    ↓
DLT Pipeline (Silver → Gold)
    ↓
Gold Tables (Analytics)
    ↓
Consumption (Dashboards, Genie, Apps)
```

## 🎓 Learning Resources

### Included Documentation
- `README.md` - Complete documentation
- `SETUP_GUIDE.md` - Detailed setup instructions
- `QUICK_START.md` - Fast track guide
- `ARCHITECTURE.md` - Technical deep-dive

### External Resources
- [OpenF1 API Docs](https://openf1.org/#api-endpoints)
- [Databricks DLT Guide](https://docs.databricks.com/delta-live-tables/)
- [Unity Catalog Docs](https://docs.databricks.com/data-governance/unity-catalog/)

## ✨ What Makes This Special

1. **Production-Ready**: Not a toy project - ready for real use
2. **Configurable**: Easy to swap catalogs/schemas via config
3. **Scalable**: Handles API limits with smart batching
4. **Maintainable**: Clean code structure with documentation
5. **Complete**: Ingestion → Storage → Processing → Visualization
6. **Best Practices**: Medallion architecture, DLT, Unity Catalog
7. **Extensible**: Easy to add new transformations or endpoints

## 🔧 Customization Points

### Easy to Modify
1. **Target Year**: Change `data.target_year` in config
2. **Endpoints**: Enable/disable in `endpoints:` section
3. **API Settings**: Adjust rate limits, timeouts
4. **Catalogs**: Update `unity_catalog` section
5. **Transformations**: Edit DLT notebook files
6. **Dashboards**: Modify SQL queries or add new ones

### Extension Ideas
- Add historical data (2018-2024)
- Build ML models for predictions
- Create championship standings tables
- Add real-time streaming (requires paid API)
- Integrate with external BI tools
- Build driver comparison features
- Add weather correlation analysis

## 📊 Expected Data Volumes (2025 Season)

Approximate record counts:
- **Meetings**: ~24 (race weekends)
- **Sessions**: ~115 (5 per weekend avg)
- **Drivers**: ~2,300 (20 per session)
- **Laps**: ~100,000 (varies by session type)
- **Car Data**: ~1M+ telemetry points
- **Weather**: ~6,900 (per minute updates)
- **Pit Stops**: ~1,500
- **Race Control**: ~5,000 messages

## ⚙️ System Requirements

**Minimum:**
- Databricks workspace (any cloud)
- Unity Catalog enabled
- 1-2 worker cluster for ingestion
- SQL Warehouse for queries

**Recommended:**
- 2-5 worker cluster with Photon
- Serverless SQL Warehouse
- Delta Live Tables Advanced/Pro edition

## 🎯 Success Checklist

After setup, you should have:
- [ ] Bronze tables with raw data
- [ ] Silver tables with cleaned data
- [ ] Gold tables with aggregations
- [ ] DLT pipeline running successfully
- [ ] SQL dashboard with visualizations
- [ ] Genie Space answering questions
- [ ] (Optional) Databricks App deployed

## 🆘 Need Help?

**Check These First:**
1. `SETUP_GUIDE.md` → Troubleshooting section
2. Databricks notebook logs
3. DLT pipeline UI for errors
4. API response in ingestion logs

**Common Issues:**
- Catalog not found → Create catalog first
- Module not found → Check sys.path in notebook
- API timeout → Increase timeout or reduce endpoints
- Permission denied → Grant Unity Catalog permissions

## 🏆 What You Can Do Now

### Analytics
- Analyze driver performance trends
- Compare team strategies
- Study weather impact on lap times
- Track pit stop efficiency
- Identify overtaking patterns

### Visualizations
- Create interactive dashboards
- Build executive reports
- Share insights with stakeholders
- Set up automated refreshes

### Advanced
- Build predictive models
- Forecast race outcomes
- Analyze tyre degradation
- Study driver consistency
- Calculate championship scenarios

## 📝 Next Steps

1. **Complete Setup**: Follow `QUICK_START.md` or `SETUP_GUIDE.md`
2. **Explore Data**: Run `notebooks/02_explore_data.py`
3. **Create Dashboards**: Use `dashboards/f1_race_analytics.sql`
4. **Deploy App**: Set up `apps/f1_dashboard_app.py`
5. **Customize**: Extend with your own analyses

---

## 🎉 You're Ready to Analyze F1 Data!

This is a complete, production-ready data pipeline. Everything you need is included:
- ✅ Code
- ✅ Configuration
- ✅ Documentation
- ✅ Examples
- ✅ Best practices

**Just configure, deploy, and start analyzing!** 🏁

---

*Built with ❤️ for F1 data enthusiasts*
*Data provided by [OpenF1](https://openf1.org/) (unofficial, not affiliated with Formula 1)*

