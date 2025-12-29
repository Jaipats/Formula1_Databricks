# Quick Fix: car_data Returns 0 Results

## TL;DR - The Fix

Edit `config/pipeline_config.yaml`:

```yaml
data:
  target_year: 2024  # ← Change from 2025 to 2024
  
  car_data_filters:
    speed_gte: 50  # ← Change from 100 to 50 (or remove entirely)
    sample_drivers: false  # ← Change from true to false
```

**Then re-run**: `notebooks/01_ingest_f1_data.py`

---

## Why?

**2025 F1 season hasn't happened yet → No car telemetry data available**

The API returns `422` (data not available) for all 2025 car_data requests.

2024 has complete data! ✅

---

## Expected Result After Fix

**Before**:
```
car_data: 0/615 fetches successful
```

**After**:
```
car_data: 450/615 fetches successful  ✅
```

(Some 422 errors are normal - not all sessions have telemetry)

---

## Verify the Fix

```sql
-- Check that data was written to volume
LIST '/Volumes/jai_patel_f1_data/racing_stats/pipeline_storage/staging/car_data/'
```

You should see files like:
- `session_9165_driver_1/`
- `session_9165_driver_11/`
- etc.

---

## Still Having Issues?

See: `CAR_DATA_TROUBLESHOOTING.md` for detailed diagnosis.

