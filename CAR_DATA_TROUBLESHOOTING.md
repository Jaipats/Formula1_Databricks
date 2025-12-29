# car_data Troubleshooting Guide

## Problem
**Symptom**: `car_data: 0/615 fetches successful` - No car telemetry data returned

## Root Cause Analysis

Based on the code in `utils/api_client.py` (lines 82-85), when the API returns a `422` error (data not available), we gracefully return an empty list instead of raising an error. This means **the API is telling us car_data is not available** for the sessions you're querying.

### Why is car_data unavailable?

There are **3 main reasons**:

### 1. ⚠️ Year 2025 Data Not Yet Available (MOST LIKELY)

```yaml
# Current config/pipeline_config.yaml
data:
  target_year: 2025  # ← THIS IS THE PROBLEM
```

**Issue**: The 2025 F1 season hasn't happened yet or is incomplete. Car telemetry data is only available **after** sessions have been completed and processed by the API.

**Solution**: Use 2024 data instead:

```yaml
# config/pipeline_config.yaml
data:
  target_year: 2024  # ← Change this
```

---

### 2. 🔍 Speed Filter Too Restrictive

```yaml
# Current config/pipeline_config.yaml
car_data_filters:
  speed_gte: 100  # Only fetches data when speed >= 100 km/h
```

**Issue**: The filter might be excluding all data, especially:
- In pit lanes (speed < 80 km/h)
- During safety cars
- In slow corners
- For certain sessions (e.g., qualifying out-laps)

**Solutions**:

**Option A**: Lower the filter
```yaml
car_data_filters:
  speed_gte: 50  # More reasonable threshold
```

**Option B**: Remove the filter entirely
```yaml
car_data_filters:
  # speed_gte: 100  # Commented out - no filter
```

---

### 3. 🚫 Only Sampling 5 Drivers

```yaml
car_data_filters:
  sample_drivers: true  # Only fetches first 5 drivers
```

**Issue**: This is a testing feature that limits data. While this doesn't cause 0 results, it does reduce your data volume.

**Solution for production**:
```yaml
car_data_filters:
  sample_drivers: false  # Fetch all drivers
```

---

## How to Diagnose

### Step 1: Check API Directly

Test with curl to see if data exists:

```bash
# Check 2025 sessions
curl "https://api.openf1.org/v1/sessions?year=2025" | jq 'length'

# Get first 2025 session
curl "https://api.openf1.org/v1/sessions?year=2025" | jq '.[0]'

# Try to get car_data for that session
# Replace SESSION_KEY and DRIVER_NUMBER with actual values
curl "https://api.openf1.org/v1/car_data?session_key=SESSION_KEY&driver_number=DRIVER_NUMBER"
```

### Step 2: Compare with 2024

```bash
# Check 2024 sessions
curl "https://api.openf1.org/v1/sessions?year=2024" | jq 'length'

# Get a 2024 session
curl "https://api.openf1.org/v1/sessions?year=2024" | jq '.[0]'

# Try car_data for 2024
curl "https://api.openf1.org/v1/car_data?session_key=9165&driver_number=1"
```

---

## Recommended Fix

Update `config/pipeline_config.yaml`:

```yaml
# Data Configuration
data:
  target_year: 2024  # ✅ Use 2024 - complete season data

  # Car data filtering
  car_data_filters:
    speed_gte: 50  # ✅ Lowered from 100 to 50
    sample_drivers: false  # ✅ Get all drivers (not just 5)

  # OR remove filters entirely for testing:
  # car_data_filters: {}
```

---

## Expected Behavior

### ✅ Successful car_data fetch:
```
INFO: Fetching car data...
INFO: ✓ Fetched 1523 car_data records for session 9165, driver 1
INFO: ✓ Fetched 1891 car_data records for session 9165, driver 11
...
INFO: Car data summary: 450/615 successful, 165 skipped
```

### ⚠️ Current behavior (all 422 errors):
```
INFO: Fetching car data (may be unavailable for some sessions)...
WARNING: Skipping car data for session 9683, driver 1: Data not available (422 error)
WARNING: Skipping car data for session 9683, driver 4: Data not available (422 error)
...
INFO: Car data summary: 0/615 successful, 615 skipped
```

---

## Understanding the Code

From `utils/api_client.py`:

```python
# Line 82-85
if e.response.status_code == 422:
    logger.info(
        f"Data not available for {endpoint} with params {params} (422 error)")
    return []  # Return empty list instead of raising
```

**422 = "Unprocessable Entity"** means:
- The API understands your request
- But the data doesn't exist for those parameters
- Common for future/recent sessions that haven't been processed yet

---

## Testing Your Fix

After updating the config:

1. **Re-run ingestion**:
   ```bash
   # In Databricks notebook
   Run: notebooks/01_ingest_f1_data.py
   ```

2. **Check the logs** for:
   ```
   ✅ ✓ Fetched XXXX car_data records for session YYYY, driver Z
   ```

3. **Verify volume has data**:
   ```sql
   -- In Databricks
   LIST '/Volumes/jai_patel_f1_data/racing_stats/pipeline_storage/staging/car_data/'
   ```

4. **Check counts**:
   - Should see: `450+/615 successful` (instead of `0/615`)
   - Some `422` errors are normal (not all sessions have telemetry)
   - But **ALL 422 errors = wrong year or filter**

---

## Quick Test Without Changing Config

If you want to test WITHOUT changing the config file:

```python
# In Databricks notebook (temporary test)
from utils.api_client import OpenF1Client

client = OpenF1Client(base_url="https://api.openf1.org/v1")

# Test 2024 car_data
test_data = client.get_car_data(
    session_key=9165,  # 2024 Bahrain GP
    driver_number=1,   # Max Verstappen
    speed_gte=50       # Lower filter
)

print(f"Found {len(test_data)} records")
if test_data:
    print("✅ car_data IS available for 2024!")
else:
    print("❌ Still no data - check API or filters")
```

---

## Summary

| Cause | Fix | Impact |
|-------|-----|--------|
| ⚠️ **Year 2025 (most likely)** | `target_year: 2024` | ✅ Will fix 0/615 issue |
| 🔍 **Speed filter too high** | `speed_gte: 50` or remove | ✅ Will increase successful fetches |
| 🚫 **Only 5 drivers** | `sample_drivers: false` | 🔵 More data, not fixing 0/615 |

**Recommendation**: Change `target_year` to 2024 first. This is almost certainly the issue.

---

## Need More Help?

1. Check API documentation: https://openf1.org/
2. Test API manually: https://api.openf1.org/v1/sessions?year=2024
3. Review logs in notebook for specific error messages
4. Check `API_DATA_AVAILABILITY.md` for more details on data availability

