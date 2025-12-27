# OpenF1 API - Data Availability Notes

This document explains data availability for different OpenF1 API endpoints.

## Always Available Data

These endpoints typically have data for all sessions:

✅ **Meetings** - Race weekend information  
✅ **Sessions** - Session details (Practice, Qualifying, Race, Sprint)  
✅ **Drivers** - Driver information per session  
✅ **Laps** - Lap timing data  
✅ **Pit Stops** - Pit stop timing  
✅ **Stints** - Tyre strategy information  
✅ **Weather** - Track weather conditions  
✅ **Race Control** - Flags and race control messages  
✅ **Intervals** - Time gaps between cars  

## Conditionally Available Data

These endpoints may not have data for all sessions:

⚠️ **Car Data** (Telemetry)
- **Status**: Often unavailable during live sessions
- **Availability**: Provided shortly after sessions complete
- **Issue**: May return 422 errors for recent/future races
- **Solution**: Pipeline handles gracefully, skips unavailable data
- **Data**: Speed, RPM, throttle, brake, gear, DRS

⚠️ **Position**
- **Status**: May not be available for all session types
- **Availability**: Mainly for Race and Sprint sessions
- **Issue**: Can return 422 errors for practice/qualifying
- **Solution**: Pipeline continues without failing

⚠️ **Location**
- **Status**: Very large dataset, disabled by default
- **Availability**: When available, can be massive (GPS tracking)
- **Recommendation**: Only enable for specific analysis needs

⚠️ **Team Radio** (Beta)
- **Status**: May not be available for all sessions
- **Availability**: When F1 releases radio recordings
- **Note**: Audio URLs may have limited availability

⚠️ **Overtakes** (Beta)
- **Status**: Beta feature
- **Availability**: May not be complete for all races
- **Note**: Algorithmically detected, may have gaps

⚠️ **Session Result** (Beta)
- **Status**: Beta feature
- **Availability**: Available after session completion
- **Note**: May not be immediately available

⚠️ **Starting Grid** (Beta)
- **Status**: Beta feature
- **Availability**: Available for Race and Sprint sessions
- **Note**: May not be available for all sessions

## 2025 Season Data

For the **2025 season** (configured by default):

🔮 **Future Races**
- Most endpoints will return empty data
- Meetings and sessions may be available (schedule)
- Telemetry and results will be empty until races occur

📅 **After Race Completion**
- Data typically available within hours of race finish
- Some endpoints (car_data) may take longer to process
- Historical data becomes available gradually

## Error Handling

The pipeline handles data availability and API limits gracefully:

### 422 Errors (Data Not Available)
```
INFO: Data not available for car_data with params {'session_key': 9683, 'driver_number': 1} (422 error)
```
- **Meaning**: The data doesn't exist for that session/driver
- **Action**: Pipeline skips and continues
- **Impact**: Table will have fewer records, but no failures

### 429 Errors (Rate Limiting)
```
WARNING: Rate limit hit for car_data (429). Waiting 10 seconds before retry 1/5
```
- **Meaning**: Too many requests sent to the API
- **Action**: Automatic exponential backoff (5s, 10s, 20s, 40s, 60s)
- **Retry-After**: Respects API's Retry-After header if provided
- **Impact**: Pipeline slows down but continues successfully
- **Prevention**: Increased default delay to 2 seconds between requests

### Empty Results
```
INFO: Fetched 0 car data records (0 successful, 120 skipped)
```
- **Meaning**: No data available for any drivers in any session
- **Action**: Empty DataFrame created
- **Impact**: Bronze table will be empty (not an error)

## Recommendations

### For 2025 Season (Current Config)
1. **Run after races occur** - Don't expect data for future races
2. **Check race calendar** - Only races that have happened will have data
3. **Monitor logs** - Look for successful vs. skipped fetch counts

### For Historical Analysis
1. **Use years 2018-2024** - Complete historical data available
2. **Change config**: Set `target_year: 2024` in `config/pipeline_config.yaml`
3. **More complete data** - All endpoints will have richer datasets

### For Testing
```yaml
# config/pipeline_config.yaml
data:
  target_year: 2024  # Use 2024 for complete data
```

## Checking Data Availability

### Before Running Pipeline

Check if data exists for your target year:
```bash
# Check if meetings exist
curl "https://api.openf1.org/v1/meetings?year=2025"

# Check specific session
curl "https://api.openf1.org/v1/sessions?session_key=9683"

# Check if car_data exists
curl "https://api.openf1.org/v1/car_data?session_key=9683&driver_number=1"
```

### After Running Pipeline

Check what data was successfully fetched:
```sql
-- Check record counts
SELECT 
    'meetings' as table_name, COUNT(*) as records 
FROM jai_patel_f1_data.racing_stats.bronze_meetings
UNION ALL
SELECT 'sessions', COUNT(*) FROM jai_patel_f1_data.racing_stats.bronze_sessions
UNION ALL
SELECT 'car_data', COUNT(*) FROM jai_patel_f1_data.racing_stats.bronze_car_data
UNION ALL
SELECT 'laps', COUNT(*) FROM jai_patel_f1_data.racing_stats.bronze_laps;
```

## Disabling Problematic Endpoints

If you want to skip endpoints that often fail:

```yaml
# config/pipeline_config.yaml
endpoints:
  car_data: false      # Disable if causing issues
  position: false      # Disable if not needed
  location: false      # Already disabled (huge dataset)
  team_radio: false    # Disable if not available
```

## API Documentation

For the latest information on data availability:
- [OpenF1 API Documentation](https://openf1.org/#api-endpoints)
- [OpenF1 FAQ](https://openf1.org/#faq)

## Summary

✅ **Pipeline is resilient** - Handles missing data gracefully  
⚠️ **422 errors are normal** - Some data won't exist for all sessions  
🔧 **Configure as needed** - Enable/disable endpoints based on your needs  
📊 **Check logs** - Monitor success/skip counts to understand data availability  

---

**Note**: The OpenF1 API is continuously improving. Data availability may change over time.

