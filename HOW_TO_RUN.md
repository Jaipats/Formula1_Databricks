# 🚀 How to Run the F1 Data Pipeline

## ⚠️ IMPORTANT: These are Databricks Notebooks, NOT Local Python Scripts!

You **CANNOT** run these notebooks on your local machine with `python3` because they use:
- `dbutils` (Databricks utilities - only exists in Databricks)
- `spark` (PySpark - needs Databricks cluster)
- Unity Catalog volumes (Databricks feature)

**You MUST run them in Databricks!**

---

## ✅ Step-by-Step Guide

### Step 1: Upload Code to Databricks

You have two options:

#### Option A: Use Databricks CLI (Automated)

```bash
cd /Users/jaideep.patel/Cursor/Formula1_Databricks

# Make sure you're logged in to Databricks CLI
databricks auth login --host https://YOUR_WORKSPACE.cloud.databricks.com

# Run the deploy script
bash deploy/databricks_cli_deploy.sh
```

This will automatically:
- Create the workspace folder
- Upload all notebooks and code
- Create Unity Catalog resources

#### Option B: Manual Upload via Databricks UI

1. Go to your Databricks workspace in the browser
2. Navigate to **Workspace** → **Users** → **your-email@databricks.com**
3. Right-click and select **Create** → **Folder**
4. Name it `Formula1_Databricks`
5. Upload the following folders:
   - `config/`
   - `utils/`
   - `notebooks/`
   - `dlt/`

---

### Step 2: Open the Notebook in Databricks

1. In Databricks workspace, navigate to:
   ```
   /Workspace/Users/your-email@databricks.com/Formula1_Databricks/notebooks/
   ```

2. **Open this notebook**: `01_ingest_f1_data_incremental_FIXED.py`

   ⭐ **This is the recommended notebook** - it's memory-efficient and won't crash.

---

### Step 3: Attach to a Cluster

1. At the top of the notebook, click **"Detached"** or **"Connect"**
2. Select an existing cluster OR create a new one:
   - **Cluster Name**: `F1 Pipeline Cluster`
   - **Runtime**: `14.3 LTS` or newer
   - **Node Type**: `Standard_DS3_v2` or larger
   - **Workers**: 1-3 workers
   - **Autoscale**: Enabled

3. Click **"Attach"** or **"Start Cluster"**

---

### Step 4: Run the Notebook

1. **Verify the notebook structure** - make sure it looks like this:

```python
# Cell 1: Install packages
%pip install pyyaml requests pandas

# Cell 2: Restart Python (ALONE - no imports!)
dbutils.library.restartPython()

# Cell 3: Import modules (AFTER restart)
import sys
from config.settings import config
```

2. **If imports are BEFORE `restartPython()`, stop and fix it!**

3. **Run each cell**:
   - Click **"Run Cell"** (Shift+Enter)
   - Or click **"Run All"** at the top

4. **Monitor progress**:
   - Watch the output in each cell
   - Progress bars will show data fetching status
   - Expect 20-30 minutes for full ingestion

---

### Step 5: Verify Data

After the notebook completes:

```python
# Check staged data in volume
display(dbutils.fs.ls("/Volumes/jai_patel_f1_data/racing_stats/pipeline_storage/staging/"))

# Or run the next notebook to load into Delta tables
# notebooks/02_load_from_volume_to_delta.py
```

---

## 🚫 Common Mistakes

### ❌ Mistake 1: Running Locally
```bash
# ❌ WRONG - This will NOT work!
python3 notebooks/01_ingest_f1_data_incremental.py
```

**Error**: `ModuleNotFoundError: No module named 'dbutils'`

**Fix**: Run in Databricks, not locally!

---

### ❌ Mistake 2: Imports Before `restartPython()`

```python
# ❌ WRONG - Causes kernel to be unresponsive
from config.settings import config
dbutils.library.restartPython()
```

**Error**: "Fatal error: The Python kernel is unresponsive"

**Fix**: Move ALL imports AFTER `restartPython()`

---

### ❌ Mistake 3: Wrong Workspace Path

```python
# ❌ WRONG - Path doesn't exist
sys.path.append('/Workspace/Repos/<your-username>/Formula1_Databricks')
```

**Error**: `ModuleNotFoundError: No module named 'config'`

**Fix**: Update to your actual workspace path:
```python
sys.path.append('/Workspace/Users/your-email@databricks.com/Formula1_Databricks')
```

---

## 📋 Pre-Flight Checklist

Before running, verify:

- [ ] Code is uploaded to Databricks (not running locally!)
- [ ] Notebook is open in Databricks UI
- [ ] Cluster is attached and running
- [ ] Workspace path is correct (line ~28 in the notebook)
- [ ] `restartPython()` is in its own cell with NO imports before it
- [ ] All imports are AFTER `restartPython()`
- [ ] Unity Catalog is set up (run `setup/setup_catalog.sql` first if needed)

---

## 🎯 Quick Reference

### Files to Upload to Databricks:
```
/Workspace/Users/your-email@databricks.com/Formula1_Databricks/
├── config/
│   ├── pipeline_config.yaml
│   └── settings.py
├── utils/
│   ├── api_client.py
│   ├── data_fetcher.py
│   └── volume_writer.py
├── notebooks/
│   ├── 01_ingest_f1_data_incremental_FIXED.py  ⭐ Run this one!
│   ├── 02_load_from_volume_to_delta.py
│   └── 03_explore_data.py
└── dlt/
    ├── f1_bronze_to_silver.py
    └── f1_gold_aggregations.py
```

### Recommended Notebook:
**`01_ingest_f1_data_incremental_FIXED.py`**

### Execution Flow:
1. Upload code to Databricks
2. Open notebook in Databricks UI
3. Attach cluster
4. Update workspace path
5. Run all cells
6. Wait for completion (~20-30 min)
7. Verify data in volumes

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'dbutils'"
→ **Solution**: You're running locally. Upload to Databricks and run there!

### "Fatal error: The Python kernel is unresponsive"
→ **Solution**: Imports are before `restartPython()`. Move them AFTER!

### "ModuleNotFoundError: No module named 'config'"
→ **Solution**: Workspace path is wrong or code not uploaded. Fix the path in the notebook.

### "ModuleNotFoundError: No module named 'yaml'"
→ **Solution**: Run the `%pip install` cell first, then `restartPython()`, then imports.

### Notebook crashes or hangs
→ **Solution**: Use `01_ingest_f1_data_incremental_FIXED.py` - it's memory-efficient.

---

## 📚 More Help

- **Quick Start**: `QUICK_START.md`
- **Import Issues**: `CRITICAL_WARNING_IMPORTS.md`
- **Crash Issues**: `NOTEBOOK_CRASH_FIX.md`
- **Visual Guide**: `IMPORT_ORDER_VISUAL.txt`

---

## ✅ Summary

1. **Upload code to Databricks** (use CLI or manual upload)
2. **Open notebook in Databricks UI** (not your local editor!)
3. **Attach to a cluster**
4. **Update workspace path** in the notebook
5. **Verify import order** (imports AFTER `restartPython()`)
6. **Run all cells**
7. **Wait for completion** (~20-30 minutes)
8. **Enjoy your F1 data!** 🏎️💨

**These notebooks ONLY run in Databricks, not locally!**

