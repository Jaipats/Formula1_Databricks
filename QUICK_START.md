# Quick Start Guide - 5 Minutes to F1 Data! 🏎️

Get your F1 data pipeline running in just 5 minutes!

## Prerequisites

- ✅ Databricks workspace with Unity Catalog
- ✅ Databricks CLI installed (`pip install databricks-cli`)
- ✅ Git installed

---

## Step 1: Setup Unity Catalog (2 minutes)

Run this SQL in Databricks:

```sql
-- Create catalog and schema
CREATE CATALOG IF NOT EXISTS jai_patel_f1_data 
COMMENT 'Formula 1 race data and analytics';

CREATE SCHEMA IF NOT EXISTS jai_patel_f1_data.racing_stats 
COMMENT 'F1 racing statistics and telemetry data';

-- Create volume for data staging
CREATE VOLUME IF NOT EXISTS jai_patel_f1_data.racing_stats.pipeline_storage
COMMENT 'Storage for Lakeflow pipeline and staged data';

-- Verify
SELECT 'Setup complete!' as status;
```

**Or** use the provided script: `setup/setup_catalog.sql`

---

## Step 2: Deploy to Databricks (1 minute)

```bash
# Clone the repository
git clone https://github.com/Jaipats/Formula1_Databricks.git
cd Formula1_Databricks

# Configure Databricks CLI (if not already done)
databricks auth login --host https://YOUR_WORKSPACE.cloud.databricks.com

# Deploy
bash deploy/databricks_cli_deploy.sh
```

This uploads all code to your Databricks workspace.

---

## Step 3: Run Data Ingestion (1 minute setup + 20-30 min run)

1. **Open Databricks workspace** in your browser
2. **Navigate to**: `/Workspace/Users/YOUR_EMAIL/Formula1_Databricks/notebooks/`
3. **Open**: `01_ingest_f1_data.py`
4. **Update line 36** with your email:
   ```python
   sys.path.append('/Workspace/Users/YOUR_EMAIL@databricks.com/Formula1_Databricks')
   ```
5. **Attach to a cluster** (or create one)
6. **Click "Run All"**

**What it does**: Fetches F1 data from OpenF1 API and stages JSON files to volumes

**Output location**: `/Volumes/jai_patel_f1_data/racing_stats/pipeline_storage/staging/`

---

## Step 4: Create & Run Lakeflow Pipeline (1 minute)

1. **Go to**: Workflows → Lakeflow Pipelines
2. **Click**: "Create Pipeline"
3. **Configure**:
   - **Name**: `f1_data_pipeline`
   - **Storage**: `/Volumes/jai_patel_f1_data/racing_stats/pipeline_storage`
   - **Configuration** (click "+ Add configuration"):
     ```
     catalog: jai_patel_f1_data
     schema: racing_stats
     ```
   - **Notebook libraries** (click "+ Add notebook"):
     - `/Workspace/Users/YOUR_EMAIL/Formula1_Databricks/dlt/f1_volume_to_bronze_autoloader`
     - `/Workspace/Users/YOUR_EMAIL/Formula1_Databricks/dlt/f1_bronze_to_silver`
     - `/Workspace/Users/YOUR_EMAIL/Formula1_Databricks/dlt/f1_gold_aggregations`
   - **Target**: `production`
   - **Cluster**: Use default settings (or customize)
4. **Click**: "Create"
5. **Click**: "Start"

**What it does**: 
- Autoloader reads JSON files from volumes
- Creates Bronze tables (raw data)
- Transforms to Silver tables (cleaned)
- Aggregates to Gold tables (analytics)

**Runtime**: ~10-15 minutes

---

## Step 5: Query Your Data! (30 seconds)

```sql
-- View raw meetings data
SELECT * FROM jai_patel_f1_data.racing_stats.bronze_meetings;

-- View cleaned sessions
SELECT * FROM jai_patel_f1_data.racing_stats.silver_sessions
ORDER BY date_start DESC;

-- View race summary analytics
SELECT * FROM jai_patel_f1_data.racing_stats.gold_race_summary;

-- Driver performance
SELECT * FROM jai_patel_f1_data.racing_stats.gold_driver_performance
ORDER BY avg_lap_time;
```

---

## Step 6: Set Up Streamlit Databricks App (Optional - 5 minutes)

**After your data is loaded**, set up the interactive F1 analytics Databricks App:

```bash
# 1. Set environment variables
export DATABRICKS_HOST='your-workspace.cloud.databricks.com'
export DATABRICKS_TOKEN='your-personal-access-token'
export DATABRICKS_HTTP_PATH='/sql/1.0/warehouses/your-warehouse-id'

# 2. Run locally
cd apps
streamlit run app.py
```

**App Features:**
- 📊 Season overview with key metrics
- 🏁 Driver performance analysis (with comparison mode)
- 🏆 Team analytics (Race sessions only)
- 📈 Detailed race analysis with multiple charts
- 🔧 Tire strategy analysis with team filtering

**Production Deployment:**
- Deploy as a Databricks App using `apps/app.yaml`
- Credentials auto-injected in Databricks environment
- No manual token configuration needed!

**How to get your token (for local development):**
1. Databricks UI → User Settings → Developer → Access Tokens
2. Generate New Token → Copy immediately
3. Set as `DATABRICKS_TOKEN` environment variable

---

## Step 7: Create Genie Space (Optional - 2 minutes)

**After data is loaded and verified**, create a Genie Space for AI-powered natural language queries:

**Method 1: Databricks Notebook (Easiest)**
1. Open `notebooks/create_genie_space.py` in Databricks
2. Run all cells
3. Click the generated link to access your Genie Space

**Method 2: CLI Script**
```bash
export DATABRICKS_HOST='your-workspace.cloud.databricks.com'
export DATABRICKS_TOKEN='your-token'
cd deploy
./create_genie_space.sh
```

**What You Get:**
- ✨ AI-powered analytics on 19 tables (13 silver + 6 gold)
- 💬 Ask questions in natural language
- 📊 Automatic query generation and visualization

**Example Questions:**
```
"Show me the top 10 fastest laps from 2025"
"Compare Red Bull and Mercedes pit stop performance"
"What tire compounds were used most in Monaco?"
"Which driver had the most overtakes this season?"
```

📖 **Full Guide:** See `GENIE_SPACE_GUIDE.md` for complete documentation

---

## 🎉 All Done!

You now have a complete F1 analytics platform with:
- ✅ Bronze tables (raw API data)
- ✅ Silver tables (cleaned & validated)
- ✅ Gold tables (analytics-ready)
- ✅ Autoloader for incremental updates
- ✅ Production-ready pipeline
- ✅ Interactive Streamlit Databricks App (optional)
- ✅ Genie Space for natural language queries (optional)

---

## 🔄 Adding More Data

To add more data (e.g., different year or new races):

1. **Update config**: Edit `config/pipeline_config.yaml`
   ```yaml
   data:
     target_year: 2024  # Change year
   ```
2. **Run ingestion**: Execute `01_ingest_f1_data.py` again
3. **Lakeflow auto-updates**: Pipeline automatically processes new files!

No manual steps needed - Autoloader detects and processes new files automatically! ✨

---

## 📊 Next Steps

### 1. Streamlit Databricks App (Recommended)
```bash
# Set up the interactive analytics app
cd apps
streamlit run app.py
```
**Features:** Driver comparisons, team analytics, race details, tire strategy

### 2. Genie Space (Recommended)
```bash
# Create AI-powered analytics space
cd deploy
./create_genie_space.sh
```
**Benefit:** Ask questions in natural language, get instant insights

### 3. Custom Dashboards
```sql
-- Use queries from: dashboards/f1_race_analytics.sql
-- Create visualizations in Databricks SQL
```

### 4. Explore Data
```python
# Run: notebooks/02_explore_data.py
# Interactive data exploration and analysis
```

### 5. Customize Pipeline
- Edit `config/pipeline_config.yaml` for API settings
- Modify Lakeflow notebooks for custom transformations
- Add new endpoints or data sources

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'config'"
→ Update workspace path in notebook (line 36)

### "No sessions found"
→ Already fixed! Pull latest code from GitHub

### "Kernel unresponsive"
→ Don't move imports before `restartPython()`
→ See: [DATABRICKS_NOTEBOOK_SETUP.md](DATABRICKS_NOTEBOOK_SETUP.md)

### Lakeflow Pipeline fails
→ Check: Workflows → Lakeflow Pipelines → Your Pipeline → Logs
→ Verify: Volume path exists and has data

---

## 📚 More Documentation

- **[README.md](README.md)** - Complete project overview
- **[DLT_AUTOLOADER_GUIDE.md](DLT_AUTOLOADER_GUIDE.md)** - Lakeflow Autoloader deep dive
- **[HOW_TO_RUN.md](HOW_TO_RUN.md)** - Detailed instructions
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture

---

## ⏱️ Time Breakdown

| Step | Time | What Happens |
|------|------|--------------|
| 1. Setup Unity Catalog | 2 min | Create catalog, schema, volume |
| 2. Deploy to Databricks | 1 min | Upload code via CLI |
| 3. Run Ingestion | 20-30 min | Fetch API data → stage to volumes |
| 4. Create Lakeflow Pipeline | 1 min | Configure pipeline |
| 5. Run Lakeflow Pipeline | 10-15 min | Bronze → Silver → Gold |
| **Core Pipeline Total** | **35-50 min** | **Complete data pipeline!** |
| 6. Setup Databricks App (Optional) | 5 min | Configure and run Streamlit Databricks App |
| 7. Create Genie Space (Optional) | 2 min | AI-powered analytics setup |
| **Full Setup Total** | **42-57 min** | **Complete analytics platform!** |

---

**Ready to race! 🏁**
