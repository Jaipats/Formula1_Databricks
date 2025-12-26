# Formula 1 Data Pipeline - Detailed Setup Guide

This guide provides step-by-step instructions for setting up the F1 data pipeline in Databricks.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Configuration](#configuration)
4. [Data Ingestion](#data-ingestion)
5. [DLT Pipeline Setup](#dlt-pipeline-setup)
6. [Dashboard Creation](#dashboard-creation)
7. [Databricks App Deployment](#databricks-app-deployment)
8. [Genie Space Setup](#genie-space-setup)
9. [Verification](#verification)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required
- [ ] Databricks workspace (AWS, Azure, or GCP)
- [ ] Unity Catalog enabled in your workspace
- [ ] A SQL Warehouse or compute cluster
- [ ] Workspace admin or appropriate permissions to:
  - Create catalogs and schemas
  - Create and run DLT pipelines
  - Create notebooks and SQL queries
  - Access compute resources

### Optional
- [ ] Git repository for version control
- [ ] Databricks CLI installed (for automation)
- [ ] Access to Databricks Apps (for Streamlit app deployment)

## Initial Setup

### Step 1: Create Unity Catalog and Schema

**Option A: Using SQL (Recommended)**

1. Open Databricks SQL Editor
2. Run the following commands (replace with your desired names):

```sql
-- Create catalog
CREATE CATALOG IF NOT EXISTS f1_data
COMMENT 'Formula 1 race data and analytics';

-- Use the catalog
USE CATALOG f1_data;

-- Create schema
CREATE SCHEMA IF NOT EXISTS racing_stats
COMMENT 'F1 racing statistics and telemetry data';

-- Verify creation
SHOW CATALOGS LIKE 'f1_data';
SHOW SCHEMAS IN CATALOG f1_data;
```

3. Grant permissions (if needed):

```sql
-- Example: Grant access to a group
GRANT USAGE ON CATALOG f1_data TO `data_engineers`;
GRANT ALL PRIVILEGES ON SCHEMA f1_data.racing_stats TO `data_engineers`;
```

**Option B: Using the provided script**

1. Navigate to **SQL Editor** in Databricks
2. Open `setup/setup_catalog.sql`
3. Modify the variables at the top:
   ```sql
   SET VAR catalog_name = 'your_catalog_name';
   SET VAR schema_name = 'your_schema_name';
   ```
4. Run the script

### Step 2: Upload Project to Databricks

**Option A: Using Databricks Repos (Recommended)**

1. Push this project to GitHub, GitLab, or Azure DevOps
2. In Databricks workspace:
   - Click **Repos** in the left sidebar
   - Click **Add Repo**
   - Enter your repository URL
   - Click **Create Repo**
3. Your project will be available at `/Repos/<username>/<repo-name>`

**Option B: Manual Upload**

1. In Databricks workspace:
   - Navigate to **Workspace** → **Users** → your username
   - Create a folder named `Formula1`
2. Upload files while maintaining the directory structure:
   ```
   /Users/<your-username>/Formula1/
   ├── config/
   ├── utils/
   ├── notebooks/
   ├── dlt/
   ├── dashboards/
   ├── apps/
   └── setup/
   ```

## Configuration

### Step 3: Configure the Pipeline

1. Open `config/pipeline_config.yaml`
2. Update the Unity Catalog settings:

```yaml
unity_catalog:
  catalog: "your_catalog_name"      # CHANGE THIS
  schema: "your_schema_name"         # CHANGE THIS
  volume: "raw_data"
```

3. Review and adjust other settings:

```yaml
data:
  target_year: 2025                  # Year to fetch data for

api:
  rate_limit_delay: 1                # Increase if you hit rate limits
  timeout: 30                        # Increase if requests timeout
  retry_attempts: 3

endpoints:
  # Enable/disable endpoints as needed
  location: false                    # Keep disabled (very large dataset)
  car_data: true                     # May be slow, disable if not needed
```

4. Save the configuration file

## Data Ingestion

### Step 4: Install Dependencies

1. Create a new notebook or open `notebooks/01_ingest_f1_data.py`
2. Run the installation cell:

```python
%pip install pyyaml requests pandas databricks-sdk
dbutils.library.restartPython()
```

### Step 5: Update Notebook Paths

1. Open `notebooks/01_ingest_f1_data.py`
2. Find and update this line (around line 15):

```python
# Change this to match your project location
sys.path.append('/Workspace/Repos/<your-username>/Formula1')
```

Examples:
- If using Repos: `/Workspace/Repos/john.doe/Formula1`
- If manual upload: `/Workspace/Users/john.doe@company.com/Formula1`

### Step 6: Run Data Ingestion

1. Attach the notebook to a cluster (use a cluster with at least 2 workers)
2. Run all cells in the notebook
3. Monitor progress:
   - Check log messages for API calls
   - Verify data is being fetched
   - Check bronze table creation

**Expected Output:**
```
Catalog: f1_data
Schema: racing_stats
Target Year: 2025
...
Fetched 23 meetings
Fetched 115 sessions
...
✓ Successfully wrote to f1_data.racing_stats.bronze_meetings
✓ Successfully wrote to f1_data.racing_stats.bronze_sessions
...
```

### Step 7: Verify Bronze Tables

Run this query in SQL Editor:

```sql
-- Check created tables
SHOW TABLES IN f1_data.racing_stats;

-- Check record counts
SELECT 'meetings' as table_name, COUNT(*) as records 
FROM f1_data.racing_stats.bronze_meetings
UNION ALL
SELECT 'sessions', COUNT(*) 
FROM f1_data.racing_stats.bronze_sessions
UNION ALL
SELECT 'drivers', COUNT(*) 
FROM f1_data.racing_stats.bronze_drivers
UNION ALL
SELECT 'laps', COUNT(*) 
FROM f1_data.racing_stats.bronze_laps;
```

## DLT Pipeline Setup

### Step 8: Create Delta Live Tables Pipeline

1. Navigate to **Workflows** → **Delta Live Tables**
2. Click **Create Pipeline**
3. Configure the pipeline:

**Basic Information:**
- **Pipeline Name**: `f1_data_pipeline`
- **Product Edition**: `Advanced` (or `Pro`)
- **Pipeline Mode**: `Triggered` (can change to `Continuous` later)

**Source Code:**
- Click **Add notebook library**
- Add: `/Workspace/Repos/<your-username>/Formula1/dlt/f1_bronze_to_silver`
- Click **Add notebook library** again
- Add: `/Workspace/Repos/<your-username>/Formula1/dlt/f1_gold_aggregations`

**Destination:**
- **Catalog**: `f1_data` (or your catalog name)
- **Target Schema**: `racing_stats` (or your schema name)

**Configuration:**
Click **Add configuration** and add:
```
Key: catalog
Value: f1_data

Key: schema  
Value: racing_stats
```

**Compute:**
- **Cluster Mode**: `Fixed` or `Legacy` (for starter)
- **Workers**: Start with `1` (can scale up later)
- **Photon Acceleration**: `Enabled` (recommended)

**Storage Location:**
- **Storage Path**: `/mnt/f1_pipeline` (or your preferred DBFS location)

**Advanced Settings:**
- **Channel**: `Current`
- **Pipeline options**: Enable `Development` mode for testing

4. Click **Create**

### Step 9: Start the Pipeline

1. On the pipeline page, click **Start**
2. Monitor the pipeline execution:
   - View the DAG (Directed Acyclic Graph)
   - Check data quality metrics
   - Monitor data flow through Bronze → Silver → Gold

**What to expect:**
- Bronze tables are read
- Silver tables are created with transformations
- Gold tables are created with aggregations
- Data quality expectations are checked

3. Once complete, verify in SQL:

```sql
-- Check silver tables
SELECT 'silver_meetings' as table_name, COUNT(*) as records 
FROM f1_data.racing_stats.silver_meetings
UNION ALL
SELECT 'silver_sessions', COUNT(*) 
FROM f1_data.racing_stats.silver_sessions
UNION ALL
SELECT 'silver_drivers', COUNT(*) 
FROM f1_data.racing_stats.silver_drivers;

-- Check gold tables
SELECT 'gold_driver_performance', COUNT(*) 
FROM f1_data.racing_stats.gold_driver_performance
UNION ALL
SELECT 'gold_team_performance', COUNT(*) 
FROM f1_data.racing_stats.gold_team_performance
UNION ALL
SELECT 'gold_race_summary', COUNT(*) 
FROM f1_data.racing_stats.gold_race_summary;
```

## Dashboard Creation

### Step 10: Create SQL Dashboard

**Option A: Using the provided SQL queries**

1. Open **SQL Editor** in Databricks
2. Open `dashboards/f1_race_analytics.sql`
3. Update the configuration at the top:
   ```sql
   SET catalog = 'your_catalog_name';
   SET schema = 'your_schema_name';
   ```
4. Run individual queries to test
5. Create visualizations:
   - Click **Add Visualization** below each query
   - Choose chart type (bar, line, pie, etc.)
   - Configure axes and labels

**Option B: Create a Dashboard from scratch**

1. Go to **Dashboards** → **Create Dashboard**
2. Click **Add** → **Visualization**
3. Write queries using the gold tables
4. Add charts and configure layout

**Example visualizations to create:**
- Bar chart: Fastest lap times by driver
- Line chart: Driver performance over time
- Pie chart: Tyre compound usage
- Table: Race results and standings

## Databricks App Deployment

### Step 11: Deploy Streamlit App

1. **Set up environment variables:**

Create a `.env` file or set in Databricks Secrets:
```bash
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_TOKEN=<your-token>
F1_CATALOG=f1_data
F1_SCHEMA=racing_stats
```

2. **Deploy to Databricks Apps:**

```bash
# Using Databricks CLI
databricks apps create f1-dashboard \
  --source-code-path ./apps/f1_dashboard_app.py \
  --description "F1 Race Analytics Dashboard"
```

Or use the Databricks UI:
- Navigate to **Apps**
- Click **Create App**
- Upload `apps/f1_dashboard_app.py`
- Configure environment variables
- Deploy

3. **Access the app:**
- The app will be available at a URL like: `https://<workspace>.cloud.databricks.com/apps/<app-id>`

## Genie Space Setup

### Step 12: Create Genie Space

1. Go to **Genie** in Databricks (may be under **AI/BI** menu)
2. Click **Create Space**
3. Configure:
   - **Name**: "F1 Race Analytics"
   - **Description**: "Formula 1 race data and performance analytics"
4. **Add data sources:**
   - Select tables from `f1_data.racing_stats`
   - Start with gold tables:
     - `gold_driver_performance`
     - `gold_team_performance`
     - `gold_race_summary`
     - `gold_fastest_laps`
     - `gold_tyre_strategy`
5. **Add instructions** (optional):
   ```
   This space contains Formula 1 race data including driver performance,
   lap times, tyre strategies, and race statistics.
   ```
6. Click **Create**

### Step 13: Test Genie with Sample Questions

Try these natural language queries in Genie:

1. "Show me the top 10 fastest lap times"
2. "What's the average pit stop duration by team?"
3. "Compare Max Verstappen and Lewis Hamilton's performance"
4. "Which tyre compound is fastest?"
5. "Show race results for the last event"
6. "What were the weather conditions during the last race?"

## Verification

### Step 14: End-to-End Testing

Run this verification checklist:

**Data Pipeline:**
- [ ] Bronze tables contain raw data
- [ ] Silver tables have cleaned data with proper types
- [ ] Gold tables have aggregated metrics
- [ ] DLT pipeline runs without errors
- [ ] Data quality expectations pass

**SQL Queries:**
```sql
-- Test query: Driver performance
SELECT * FROM f1_data.racing_stats.gold_driver_performance LIMIT 5;

-- Test query: Race summary
SELECT * FROM f1_data.racing_stats.gold_race_summary LIMIT 5;

-- Test query: Fastest laps
SELECT * FROM f1_data.racing_stats.gold_fastest_laps WHERE rank <= 10;
```

**Dashboards:**
- [ ] SQL dashboard displays charts correctly
- [ ] Streamlit app connects and shows data
- [ ] Genie Space answers questions accurately

## Troubleshooting

### Common Issues

**Issue: "Catalog not found"**
- Solution: Verify catalog name in configuration matches created catalog
- Run: `SHOW CATALOGS;` to see available catalogs

**Issue: "Table not found"**
- Solution: Ensure ingestion notebook completed successfully
- Check: `SHOW TABLES IN <catalog>.<schema>;`

**Issue: DLT pipeline fails**
- Solution: Check that bronze tables exist and have data
- Verify notebook paths in DLT configuration
- Check compute cluster has sufficient resources

**Issue: API timeout errors**
- Solution: Increase `timeout` value in `config/pipeline_config.yaml`
- Reduce number of enabled endpoints
- Run ingestion in smaller batches

**Issue: Permission denied**
- Solution: Grant necessary permissions:
  ```sql
  GRANT USAGE ON CATALOG f1_data TO `<user/group>`;
  GRANT ALL PRIVILEGES ON SCHEMA f1_data.racing_stats TO `<user/group>`;
  ```

**Issue: App won't connect**
- Solution: Verify environment variables are set correctly
- Check SQL Warehouse is running
- Verify access token has appropriate permissions

### Getting Help

- Check Databricks documentation: https://docs.databricks.com
- OpenF1 API docs: https://openf1.org
- Databricks Community Forum
- Project issues page (if using GitHub)

## Next Steps

After successful setup:

1. **Schedule Regular Updates:**
   - Set up job to run ingestion notebook after each race
   - Configure DLT pipeline to run automatically

2. **Customize Analytics:**
   - Add new gold layer tables for specific analyses
   - Create custom visualizations
   - Build ML models

3. **Share with Team:**
   - Grant appropriate permissions
   - Share dashboard links
   - Document custom queries

4. **Monitor Costs:**
   - Review compute usage
   - Optimize cluster sizes
   - Consider serverless compute

---

**Setup Complete! 🏁**

You now have a fully functional F1 data pipeline in Databricks!

