# Incremental Ingestion with Volume Staging

This guide explains the new incremental ingestion approach that writes data to Unity Catalog volumes before loading to Delta tables.

## Why Incremental Ingestion?

### Problems with the Original Approach
1. **Memory Issues**: Loading all data into memory before writing
2. **Large API Responses**: Car data endpoint can return huge payloads
3. **All-or-Nothing**: Failure means starting over completely
4. **Poor Observability**: Can't see progress until completion

### Benefits of Incremental Approach
✅ **Memory Efficient**: Writes data as it's fetched
✅ **Smaller API Requests**: Filters reduce payload size (speed >= 100 km/h)
✅ **Resilient**: Can resume from where it left off
✅ **Better Progress Tracking**: See each endpoint complete
✅ **Checkpointing**: Data persisted to volume immediately

## Architecture

```
┌─────────────────┐
│   OpenF1 API    │
└────────┬────────┘
         │ Filtered requests (speed >= 100 km/h)
         ▼
┌─────────────────┐
│  API Client     │
│  (fetch batch)  │
└────────┬────────┘
         │ Write immediately
         ▼
┌──────────────────────────────────┐
│   Unity Catalog Volume           │
│   /Volumes/catalog/schema/...    │
│   staging/                       │
│   ├── car_data/                  │
│   │   ├── session_9683_driver_1.json
│   │   ├── session_9683_driver_4.json
│   │   └── ...                    │
│   ├── laps/                      │
│   ├── pit/                       │
│   └── ...                        │
└────────┬─────────────────────────┘
         │ Load in batch
         ▼
┌─────────────────┐
│  Bronze Tables  │
│  (Delta Lake)   │
└─────────────────┘
```

## Configuration

### Enable Volume Staging

```yaml
# config/pipeline_config.yaml
data:
  # Enable incremental volume staging
  use_volume_staging: true
  volume_path: "pipeline_storage/staging"
  
  # Car data filtering (reduces API payload size)
  car_data_filters:
    speed_gte: 100        # Only fetch when speed >= 100 km/h
    sample_drivers: false # Set to true to only fetch first 5 drivers (testing)
```

### Car Data Filters

The `car_data` endpoint can return massive payloads. Filters help reduce this:

| Filter | Effect | Data Reduction |
|--------|--------|----------------|
| `speed_gte: 100` | Only fetch when speed >= 100 km/h | ~40% smaller |
| `speed_gte: 200` | Only fetch when speed >= 200 km/h | ~70% smaller |
| `sample_drivers: true` | Only first 5 drivers per session | ~75% smaller |

Example filtered API call:
```
https://api.openf1.org/v1/car_data?session_key=9683&driver_number=4&speed>=100
```

## Two-Step Process

### Step 1: Fetch and Stage to Volume

Use the incremental ingestion notebook:

```python
# notebooks/01_ingest_f1_data_incremental.py
```

This will:
1. ✅ Fetch data from OpenF1 API
2. ✅ Apply filters to reduce payload size
3. ✅ Write each batch immediately to volume
4. ✅ Create one file per session/driver combination
5. ✅ Track progress and success/skip counts

**Output**: JSON files in volume staging directory

### Step 2: Load from Volume to Delta

Use the load notebook:

```python
# notebooks/02_load_from_volume_to_delta.py
```

This will:
1. ✅ Read all JSON files from volume staging
2. ✅ Combine into DataFrames
3. ✅ Add ingestion metadata
4. ✅ Write to Bronze Delta tables
5. ✅ Show summary of loaded records

**Output**: Bronze Delta tables ready for DLT pipeline

## Usage Examples

### Example 1: Default Configuration

```bash
# Run incremental ingestion
databricks workspace export /path/to/01_ingest_f1_data_incremental.py | databricks jobs run

# Then load to Delta
databricks workspace export /path/to/02_load_from_volume_to_delta.py | databricks jobs run

# Then run DLT pipeline
databricks pipelines start-update --pipeline-id $PIPELINE_ID
```

### Example 2: Testing with Sample Data

```yaml
# config/pipeline_config.yaml
data:
  target_year: 2024  # Use 2024 for complete data
  car_data_filters:
    speed_gte: 200         # Very aggressive filtering
    sample_drivers: true   # Only 5 drivers
```

This configuration is great for:
- Testing the pipeline
- Development
- Reducing costs
- Quick iterations

### Example 3: Production Full Load

```yaml
# config/pipeline_config.yaml
data:
  target_year: 2024
  car_data_filters:
    speed_gte: 100         # Reasonable filtering
    sample_drivers: false  # All drivers
```

## File Organization in Volume

```
/Volumes/jai_patel_f1_data/racing_stats/pipeline_storage/staging/
├── car_data/
│   ├── session_9683_driver_1_20250101_120000.json
│   ├── session_9683_driver_4_20250101_120030.json
│   ├── session_9683_driver_11_20250101_120100.json
│   └── _metadata.json
├── laps/
│   ├── session_9683_20250101_120200.json
│   └── _metadata.json
├── pit/
├── stints/
└── ...
```

Each endpoint gets its own directory with:
- Multiple JSON files (one per batch)
- Optional `_metadata.json` with ingestion info

## Monitoring Progress

### During Ingestion

Watch the logs:
```
✓ Fetched 1,234 car_data records for session 9683, driver 1
✓ Fetched 987 car_data records for session 9683, driver 4
Car data summary: 45 successful, 75 skipped
✓ Car data written incrementally to volume
```

### Check Staged Files

```python
# List staging directories
display(dbutils.fs.ls("/Volumes/jai_patel_f1_data/racing_stats/pipeline_storage/staging/"))

# Check car_data files
display(dbutils.fs.ls("/Volumes/jai_patel_f1_data/racing_stats/pipeline_storage/staging/car_data/"))

# Read a sample file
df = spark.read.json("/Volumes/.../staging/car_data/session_9683_driver_1_*.json")
display(df.limit(10))
```

### After Loading

```sql
-- Check record counts
SELECT 'car_data', COUNT(*) FROM jai_patel_f1_data.racing_stats.bronze_car_data
UNION ALL
SELECT 'laps', COUNT(*) FROM jai_patel_f1_data.racing_stats.bronze_laps;
```

## Error Handling

### Scenario 1: API Failures

If API calls fail:
- ✅ Errors are logged but don't stop the process
- ✅ Successfully fetched data is already in volume
- ✅ Can re-run to fetch missing data
- ✅ Volume files are timestamped to avoid conflicts

### Scenario 2: Out of Memory

If ingestion runs out of memory:
- ✅ Data already written to volume is safe
- ✅ Can resume from last successful batch
- ✅ Reduce `sample_drivers` or increase filters

### Scenario 3: 422 Errors (Data Not Available)

- ✅ Automatically handled and logged as INFO
- ✅ Continues to next session/driver
- ✅ Empty files not created

## Cleanup

### After Successful Load

Once data is in Delta tables, you can clean up staging:

```python
# CAUTION: This deletes all staging data
dbutils.fs.rm("/Volumes/jai_patel_f1_data/racing_stats/pipeline_storage/staging/", True)
```

### Keep for Debugging

Or keep staging files for:
- Audit trail
- Debugging
- Re-processing without API calls
- Comparing with new data

## Performance Tips

### 1. Optimize API Filters

```yaml
# Balance between data volume and usability
car_data_filters:
  speed_gte: 150  # Good balance - keeps corners, removes slow sections
```

### 2. Parallel Processing

The current implementation is sequential. For production:
- Use Databricks Jobs with multiple tasks
- Process sessions in parallel
- Use thread pools for driver-level fetching

### 3. Volume Performance

- ✅ Unity Catalog volumes are optimized for this pattern
- ✅ Many small files are OK (will be compacted in Delta)
- ✅ Volume I/O is fast compared to API calls

## Comparison: Old vs New Approach

| Aspect | Old Approach | New Incremental Approach |
|--------|--------------|-------------------------|
| Memory | All data in memory | Streaming to volume |
| API Payload | Full dataset | Filtered (40-70% smaller) |
| Resilience | Start over on failure | Resume from checkpoint |
| Observability | All-or-nothing | Per-batch progress |
| Time to First Data | Wait for all fetches | Immediate |
| Testing | Full load required | Can sample drivers |

## Migration Guide

### For Existing Pipelines

1. **Keep old notebook**: `01_ingest_f1_data.py` still works
2. **Try incremental**: Test with `01_ingest_f1_data_incremental.py`
3. **Compare results**: Both should produce same final Delta tables
4. **Switch when ready**: Use incremental for production

### Configuration Changes

```yaml
# Add these to your existing config
data:
  use_volume_staging: true
  car_data_filters:
    speed_gte: 100
    sample_drivers: false
```

## FAQ

**Q: Do I need to change my DLT pipelines?**  
A: No, DLT reads from Bronze tables same as before

**Q: Can I use the old ingestion method?**  
A: Yes, both notebooks are provided

**Q: What if I don't want filtering?**  
A: Set `speed_gte: null` to disable filtering

**Q: How much space do staging files use?**  
A: Roughly same as the data you're fetching, compressed as JSON

**Q: Can I re-process without calling the API?**  
A: Yes! Just run step 2 (load from volume) again

## Troubleshooting

### Issue: "Volume not found"

```sql
-- Create the volume
CREATE VOLUME IF NOT EXISTS jai_patel_f1_data.racing_stats.pipeline_storage;
```

### Issue: "No space left"

- Clean up old staging files
- Use more aggressive filters
- Sample fewer drivers

### Issue: "JSON parse errors"

- Check volume files aren't corrupted
- Re-run ingestion for affected sessions

---

**Ready to use incremental ingestion!** 🚀

Start with `01_ingest_f1_data_incremental.py` and see the benefits of streaming ingestion!

