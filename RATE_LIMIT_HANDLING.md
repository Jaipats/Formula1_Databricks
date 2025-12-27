# Rate Limit Handling Guide

This guide explains how the pipeline handles OpenF1 API rate limits (429 errors) and how to optimize for your use case.

## What are 429 Errors?

**429 Too Many Requests** means you've exceeded the API's rate limit:
- Sending requests too quickly
- Too many concurrent requests
- Exceeding hourly/daily quotas

## How the Pipeline Handles It

### Automatic Retry with Exponential Backoff

When a 429 error occurs:

1. **Check Retry-After Header**: If the API provides a `Retry-After` header, wait that long
2. **Exponential Backoff**: Otherwise, wait progressively longer:
   - Attempt 1: Wait 5 seconds
   - Attempt 2: Wait 10 seconds
   - Attempt 3: Wait 20 seconds
   - Attempt 4: Wait 40 seconds
   - Attempt 5: Wait 60 seconds (max)
3. **Retry**: Automatically retry up to 5 times (configurable)
4. **Log**: Clear warnings about rate limiting
5. **Continue**: If successful, continue with next request

### Example Log Output

```
WARNING: Rate limit hit for car_data (429). Waiting 10 seconds before retry 2/5
INFO: Fetching car_data with params: {'session_key': 9951, 'driver_number': 10}
✓ Fetched 1,234 car_data records for session 9951, driver 10
```

## Configuration Options

### Adjust Rate Limit Delay

```yaml
# config/pipeline_config.yaml
api:
  rate_limit_delay: 2  # Seconds between requests
  retry_attempts: 5    # Max retry attempts
```

**Recommendations:**
- **Conservative** (Avoid 429s): `rate_limit_delay: 3`
- **Balanced** (Default): `rate_limit_delay: 2`
- **Aggressive** (May hit limits): `rate_limit_delay: 1`

### Increase Retry Attempts

If you frequently hit rate limits but they eventually clear:

```yaml
api:
  retry_attempts: 10  # More retries before giving up
```

## Best Practices

### 1. Increase Base Delay

If you're consistently hitting rate limits:

```yaml
api:
  rate_limit_delay: 3  # or even 5 for very conservative approach
```

**Pros**: Fewer 429 errors
**Cons**: Slower overall ingestion

### 2. Use Filtering to Reduce Requests

Reduce the number of API calls needed:

```yaml
data:
  car_data_filters:
    speed_gte: 150     # Higher threshold = fewer data points
    sample_drivers: true  # Only first 5 drivers (for testing)
```

**Pros**: Fewer total requests
**Cons**: Less complete data

### 3. Fetch in Batches

Instead of fetching all data at once, fetch session by session:

```python
# Fetch sessions in smaller batches
for i in range(0, len(session_keys), 5):
    batch = session_keys[i:i+5]
    # Process batch
    time.sleep(30)  # Wait between batches
```

### 4. Run During Off-Peak Hours

API rate limits may be more lenient during off-peak hours:
- Run overnight
- Run on weekends
- Avoid right after race completion (high traffic)

## Monitoring Rate Limits

### Watch the Logs

Look for patterns:
```
WARNING: Rate limit hit for car_data (429)
WARNING: Rate limit hit for car_data (429)  # Multiple in a row = too aggressive
WARNING: Rate limit hit for car_data (429)
```

If you see many 429s:
1. Increase `rate_limit_delay`
2. Enable `sample_drivers` for testing
3. Process fewer sessions at once

### Track Success Rate

```python
# In your logs, look for:
"Car data summary: 45 successful, 75 skipped"

# High success rate = good
# Many retries/failures = increase delays
```

## Troubleshooting

### Issue: Constant 429 Errors

**Solution 1**: Increase delay between requests
```yaml
api:
  rate_limit_delay: 5  # Much more conservative
```

**Solution 2**: Reduce concurrent fetching
```yaml
data:
  car_data_filters:
    sample_drivers: true  # Fewer drivers = fewer requests
```

**Solution 3**: Break into smaller runs
- Process 1 meeting at a time
- Wait 5-10 minutes between meetings

### Issue: Pipeline Takes Too Long

If rate limiting makes ingestion too slow:

**Option 1**: Accept slower speed for reliability
- Increase delays, run overnight

**Option 2**: Use incremental ingestion
- Fetch and save one endpoint at a time
- Resume from where you left off

**Option 3**: Request higher limits
- Contact OpenF1 (may offer paid plans with higher limits)

### Issue: Works Sometimes, Fails Other Times

This is normal - API limits may vary:
- Time of day
- Current API load
- Recent releases (high traffic after races)

**Solution**: Use the automatic retry logic (already implemented)

## API Rate Limit Details

### OpenF1 documented limits:
- **Free tier**: Historical data, standard rate limits
- **Paid tier**: Real-time data, higher limits

The exact limits aren't publicly documented, but observations suggest:
- ~1-2 requests per second is generally safe
- Bursts may trigger limits
- Large result sets (car_data) may count more

## Configuration Examples

### Conservative (Avoid 429s at all costs)
```yaml
api:
  rate_limit_delay: 5
  retry_attempts: 10
  timeout: 60

data:
  car_data_filters:
    speed_gte: 150
    sample_drivers: false
```

### Balanced (Default - some 429s OK)
```yaml
api:
  rate_limit_delay: 2
  retry_attempts: 5
  timeout: 30

data:
  car_data_filters:
    speed_gte: 100
    sample_drivers: false
```

### Aggressive (Fast but may hit limits)
```yaml
api:
  rate_limit_delay: 1
  retry_attempts: 3
  timeout: 30

data:
  car_data_filters:
    speed_gte: 200  # Less data per request
    sample_drivers: true  # Fewer requests
```

## Summary

✅ **Pipeline handles 429s automatically** with exponential backoff
⚙️ **Configurable delays** to match your needs
📊 **Smart retry logic** respects API's Retry-After header
⏰ **Patient approach** works best - let it run slow and steady

**Key Takeaway**: If you see 429 errors, increase `rate_limit_delay` in your config. The pipeline will handle retries automatically, but being more conservative prevents the issue.

---

**Default settings work for most use cases!** Only adjust if you're seeing frequent 429 errors in the logs.

