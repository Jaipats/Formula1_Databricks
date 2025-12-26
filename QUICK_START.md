# Quick Start Guide - F1 Data Pipeline

Get up and running in 15 minutes! ⏱️

## 🚀 5-Step Quick Start

### 1️⃣ Configure (2 minutes)

Edit `config/pipeline_config.yaml`:
```yaml
unity_catalog:
  catalog: "your_catalog_name"    # ← CHANGE THIS
  schema: "your_schema_name"      # ← CHANGE THIS
```

### 2️⃣ Create Catalog (2 minutes)

In Databricks SQL Editor:
```sql
CREATE CATALOG IF NOT EXISTS your_catalog_name;
CREATE SCHEMA IF NOT EXISTS your_catalog_name.your_schema_name;
```

### 3️⃣ Upload to Databricks (3 minutes)

**Using Databricks Repos:**
- Push to Git → Repos → Add Repo → Clone

**Or Manual Upload:**
- Workspace → Users → your folder → Upload files

### 4️⃣ Ingest Data (5 minutes)

1. Open `notebooks/01_ingest_f1_data.py`
2. Update path on line ~15:
   ```python
   sys.path.append('/Workspace/Repos/<your-username>/Formula1')
   ```
3. Run all cells

### 5️⃣ Create DLT Pipeline (3 minutes)

Workflows → Delta Live Tables → Create Pipeline:
- **Name**: `f1_data_pipeline`
- **Notebooks**: 
  - `dlt/f1_bronze_to_silver`
  - `dlt/f1_gold_aggregations`
- **Configuration**:
  ```
  catalog = your_catalog_name
  schema = your_schema_name
  ```
- Click Create → Start

## ✅ Verify

Check data is loaded:
```sql
SELECT * FROM your_catalog.your_schema.gold_fastest_laps LIMIT 10;
```

## 🎯 What's Next?

### Create a Dashboard
- Open `dashboards/f1_race_analytics.sql`
- Run queries in Databricks SQL
- Add visualizations

### Use Genie Space
- Go to Genie → Create Space
- Select tables from your schema
- Ask: "Show me fastest lap times by driver"

### Deploy App
- Update environment variables in `apps/f1_dashboard_app.py`
- Deploy to Databricks Apps

## 📚 Need More Details?

- Full setup instructions: See `SETUP_GUIDE.md`
- Project overview: See `README.md`
- Troubleshooting: Check `SETUP_GUIDE.md` → Troubleshooting section

## 🆘 Common Issues

**"Catalog not found"**
→ Run: `CREATE CATALOG your_catalog_name;`

**"No module named config"**
→ Check `sys.path.append()` path in notebook

**"API timeout"**
→ Increase timeout in `config/pipeline_config.yaml`

**"Permission denied"**
→ Grant permissions:
```sql
GRANT USAGE ON CATALOG your_catalog TO `your_user`;
```

---

**That's it! You're ready to analyze F1 data! 🏁**

