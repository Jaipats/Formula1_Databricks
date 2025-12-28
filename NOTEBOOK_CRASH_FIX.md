# Notebook Crash Fix Guide

## 🐛 Problem: Notebook Session Crashes

The `01_ingest_f1_data_incremental.py` notebook was crashing during execution due to **two critical issues**:

### Issue 1: Import Order (NameError)
**Symptom**: `NameError: name 'config' is not defined`

**Cause**: Imports were happening BEFORE `restartPython()`, which clears all imports.

### Issue 2: Memory Overload (Crash)
**Symptom**: Notebook session crashes, kernel dies, no error message

**Cause**: The notebook was calling `fetch_all_data()` which loads ALL data into memory at once, causing out-of-memory crashes.

---

## ✅ Solutions

### Solution 1: Fixed Import Order

**Wrong** (causes NameError):
```python
from config.settings import config  # ← Import first
dbutils.library.restartPython()     # ← This DELETES config
print(config.catalog)               # ← ERROR: config doesn't exist
```

**Correct**:
```python
dbutils.library.restartPython()     # ← Restart first
import sys
from config.settings import config  # ← Import after restart
print(config.catalog)               # ← Works! ✓
```

### Solution 2: Memory-Efficient Ingestion

**Wrong** (causes crashes):
```python
# This loads EVERYTHING into memory at once!
all_data = data_fetcher.fetch_all_data()  # ← 100MB+ of data in RAM
# ... then tries to write it all
```

**Correct** (memory-efficient):
```python
# Fetch and write each endpoint immediately
meetings = api_client.get_meetings(year)
write_to_volume(meetings, 'meetings')  # ← Write immediately, free memory

sessions = api_client.get_sessions(...)
write_to_volume(sessions, 'sessions')  # ← Write immediately, free memory

# For large datasets, write in batches
for session_key in session_keys:
    car_data = api_client.get_car_data(session_key, driver_number)
    all_car_data.extend(car_data)
    
    # Write every 10K records to avoid memory buildup
    if len(all_car_data) >= 10000:
        write_to_volume(all_car_data, 'car_data')
        all_car_data = []  # ← Clear memory!
```

---

## 📁 Fixed Notebooks

### 1. `01_ingest_f1_data.py` ✅
- **Status**: Fixed import order
- **Use Case**: Loads all data into memory, then writes to Delta tables
- **Best For**: Small to medium datasets (< 50MB)
- **Memory**: High (loads everything at once)

### 2. `01_ingest_f1_data_incremental.py` ✅
- **Status**: Fixed import order (but still has memory issues)
- **Use Case**: Uses `F1DataFetcher` with `SparkVolumeWriter`
- **Issue**: Still loads all data before writing
- **Memory**: High (not truly incremental)

### 3. `01_ingest_f1_data_incremental_FIXED.py` ✅ **RECOMMENDED**
- **Status**: Fixed import order + memory-efficient
- **Use Case**: True incremental ingestion
- **Best For**: Large datasets, production use
- **Memory**: Low (writes immediately, batches large endpoints)
- **Features**:
  - ✅ Writes each endpoint immediately to volume
  - ✅ Batches car_data every 10K records
  - ✅ Uses `dbutils.fs.put()` for direct volume writes
  - ✅ Progress logging every 5 sessions
  - ✅ Won't crash even with large datasets

---

## 🚀 Recommended Approach

**Use `01_ingest_f1_data_incremental_FIXED.py`** for production:

```python
# This notebook:
# 1. Fetches meetings → writes immediately → frees memory
# 2. Fetches sessions → writes immediately → frees memory
# 3. Fetches drivers → writes immediately → frees memory
# 4. For each endpoint:
#      - Fetches data for all sessions
#      - Writes to volume
#      - Frees memory
# 5. For car_data:
#      - Fetches in batches
#      - Writes every 10K records
#      - Never holds more than 10K records in memory
```

### Key Differences

| Feature | Original | Fixed Version |
|---------|----------|---------------|
| Import order | ❌ Wrong | ✅ Correct |
| Memory usage | ❌ High (loads all) | ✅ Low (incremental) |
| Crash risk | ❌ High | ✅ Low |
| Progress visibility | ⚠️ Limited | ✅ Detailed |
| Batch writing | ❌ No | ✅ Yes (10K records) |
| Volume writing | ⚠️ Via Spark | ✅ Direct (dbutils.fs) |

---

## 🔧 How to Use the Fixed Notebook

1. **Update the workspace path** (line 28):
   ```python
   sys.path.append('/Workspace/Users/YOUR_EMAIL@databricks.com/Formula1_Databricks')
   ```

2. **Configure endpoints** in `config/pipeline_config.yaml`:
   ```yaml
   enabled_endpoints:
     meetings: true
     sessions: true
     drivers: true
     laps: true
     car_data: true  # Will be filtered and batched
     # ... other endpoints
   
   data:
     car_data_filters:
       speed_gte: 200  # Only fetch high-speed data
       sample_drivers: true  # Only first 5 drivers per session
   ```

3. **Run the notebook**:
   - It will create the volume automatically
   - Write data incrementally as it fetches
   - Show progress every 5 sessions
   - Won't crash even with large datasets

4. **Check the results**:
   ```python
   # List staged files
   display(dbutils.fs.ls("/Volumes/jai_patel_f1_data/racing_stats/raw_data/meetings"))
   
   # Read a sample
   df = spark.read.json("/Volumes/jai_patel_f1_data/racing_stats/raw_data/meetings/*.json")
   display(df)
   ```

---

## 📊 Memory Comparison

### Original Approach (Crashes)
```
Memory Usage Over Time:
|
|                    ╱─────────╲ CRASH!
|                   ╱           ╲
|                  ╱             ╲
|                 ╱               ╲
|                ╱                 ╲
|               ╱                   ╲
|______________╱_____________________╲____________
   Start    Fetch All Data         Write
```

### Fixed Approach (Stable)
```
Memory Usage Over Time:
|
|   ╱╲    ╱╲    ╱╲    ╱╲    ╱╲    ╱╲
|  ╱  ╲  ╱  ╲  ╱  ╲  ╱  ╲  ╱  ╲  ╱  ╲
| ╱    ╲╱    ╲╱    ╲╱    ╲╱    ╲╱    ╲
|╱______________________________________╲________
   Fetch→Write→Free (repeated for each endpoint)
```

---

## 🎯 Best Practices

1. **Always restart Python before imports**:
   ```python
   dbutils.library.restartPython()  # First!
   # Then imports
   ```

2. **Write data incrementally**:
   ```python
   # Don't do this:
   all_data = fetch_everything()  # ← Loads 100MB+ into RAM
   write_all(all_data)
   
   # Do this:
   for batch in fetch_in_batches():
       write_batch(batch)  # ← Max 10K records in RAM
       batch = None  # ← Free memory
   ```

3. **Monitor memory usage**:
   ```python
   import psutil
   process = psutil.Process()
   print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
   ```

4. **Use batch writes for large endpoints**:
   ```python
   BATCH_SIZE = 10000
   if len(accumulated_data) >= BATCH_SIZE:
       write_to_volume(accumulated_data, endpoint_name)
       accumulated_data = []  # Clear memory
   ```

---

## 🐛 Troubleshooting

### Notebook still crashing?

1. **Check memory limits**: Databricks clusters have memory limits
   - Use a larger cluster (e.g., Standard_DS3_v2 → Standard_DS4_v2)
   - Or reduce `BATCH_SIZE` from 10000 to 5000

2. **Disable large endpoints temporarily**:
   ```yaml
   enabled_endpoints:
     car_data: false  # Disable temporarily
     position: false
     location: false
   ```

3. **Increase filtering**:
   ```yaml
   car_data_filters:
     speed_gte: 250  # More aggressive (was 200)
     sample_drivers: true
   ```

4. **Check logs**:
   ```python
   # Add this at the top
   logging.basicConfig(level=logging.DEBUG)  # More verbose
   ```

---

## 📚 Related Documentation

- `DATABRICKS_NOTEBOOK_SETUP.md` - Import order guide
- `INCREMENTAL_INGESTION_GUIDE.md` - Volume staging architecture
- `API_DATA_AVAILABILITY.md` - Data filtering strategies

---

## ✅ Summary

**The crashes were caused by**:
1. ❌ Wrong import order → NameError
2. ❌ Loading all data into memory → Out of memory crash

**The fix**:
1. ✅ Move imports AFTER `restartPython()`
2. ✅ Write data incrementally (fetch → write → free memory)
3. ✅ Batch large endpoints (car_data) every 10K records

**Use**: `01_ingest_f1_data_incremental_FIXED.py` for production! 🚀

