# Databricks CLI Deployment Guide

Complete guide to deploying and running the F1 Data Pipeline using Databricks CLI.

## Prerequisites

### 1. Install Databricks CLI

```bash
# Using pip
pip install databricks-cli

# Or using Homebrew (macOS)
brew tap databricks/tap
brew install databricks
```

Verify installation:
```bash
databricks --version
```

### 2. Get Databricks Credentials

You need:
- **Databricks Host**: Your workspace URL (e.g., `https://your-workspace.cloud.databricks.com`)
- **Personal Access Token**: Generate in Databricks → User Settings → Access Tokens

### 3. Configure Databricks CLI

**Option A: Interactive Configuration**
```bash
databricks configure --token
```

Enter your host and token when prompted.

**Option B: Environment Variables**
```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-personal-access-token"
```

**Option C: Configuration File**
```bash
# Create ~/.databrickscfg
cat > ~/.databrickscfg << EOF
[DEFAULT]
host = https://your-workspace.cloud.databricks.com
token = your-personal-access-token
EOF
```

Verify configuration:
```bash
databricks workspace ls /
```

## Deployment Options

### Option 1: Automated Deployment (Recommended)

Use the provided deployment script:

```bash
cd /Users/jaideep.patel/Cursor/Formula1

# Set required environment variables
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"
export WAREHOUSE_ID="your-warehouse-id"  # Optional: for catalog setup

# Optional: use existing cluster
export CLUSTER_ID="your-cluster-id"

# Make script executable
chmod +x deploy/databricks_cli_deploy.sh

# Run deployment
./deploy/databricks_cli_deploy.sh
```

This script will:
1. ✅ Create workspace directories
2. ✅ Upload all Python modules
3. ✅ Upload configuration files
4. ✅ Upload notebooks
5. ✅ Create Unity Catalog and schema
6. ✅ Create DLT pipeline
7. ✅ Create ingestion job

### Option 2: Manual Step-by-Step Deployment

#### Step 1: Upload Files to Workspace

```bash
# Set your workspace path
WORKSPACE_PATH="/Workspace/Users/your.email@company.com/Formula1"

# Create directories
databricks workspace mkdirs "$WORKSPACE_PATH"
databricks workspace mkdirs "$WORKSPACE_PATH/config"
databricks workspace mkdirs "$WORKSPACE_PATH/utils"
databricks workspace mkdirs "$WORKSPACE_PATH/notebooks"
databricks workspace mkdirs "$WORKSPACE_PATH/dlt"

# Upload Python modules
databricks workspace import config/__init__.py "$WORKSPACE_PATH/config/__init__.py" --language PYTHON --overwrite
databricks workspace import config/settings.py "$WORKSPACE_PATH/config/settings.py" --language PYTHON --overwrite
databricks workspace import utils/__init__.py "$WORKSPACE_PATH/utils/__init__.py" --language PYTHON --overwrite
databricks workspace import utils/api_client.py "$WORKSPACE_PATH/utils/api_client.py" --language PYTHON --overwrite
databricks workspace import utils/data_fetcher.py "$WORKSPACE_PATH/utils/data_fetcher.py" --language PYTHON --overwrite

# Upload configuration
databricks workspace import config/pipeline_config.yaml "$WORKSPACE_PATH/config/pipeline_config.yaml" --overwrite

# Upload notebooks
databricks workspace import notebooks/01_ingest_f1_data.py "$WORKSPACE_PATH/notebooks/01_ingest_f1_data" --language PYTHON --overwrite
databricks workspace import notebooks/02_explore_data.py "$WORKSPACE_PATH/notebooks/02_explore_data" --language PYTHON --overwrite
databricks workspace import dlt/f1_bronze_to_silver.py "$WORKSPACE_PATH/dlt/f1_bronze_to_silver" --language PYTHON --overwrite
databricks workspace import dlt/f1_gold_aggregations.py "$WORKSPACE_PATH/dlt/f1_gold_aggregations" --language PYTHON --overwrite
```

#### Step 2: Create Unity Catalog

```bash
# Get your SQL Warehouse ID
databricks warehouses list

# Set warehouse ID
WAREHOUSE_ID="your-warehouse-id"

# Create catalog
databricks sql execute \
  --warehouse-id "$WAREHOUSE_ID" \
  --query "CREATE CATALOG IF NOT EXISTS jai_patel_f1_data"

# Create schema
databricks sql execute \
  --warehouse-id "$WAREHOUSE_ID" \
  --query "CREATE SCHEMA IF NOT EXISTS jai_patel_f1_data.racing_stats"

# Create volumes
databricks sql execute \
  --warehouse-id "$WAREHOUSE_ID" \
  --query "CREATE VOLUME IF NOT EXISTS jai_patel_f1_data.racing_stats.pipeline_storage"
```

#### Step 3: Create DLT Pipeline

```bash
# Create pipeline using the configuration file
databricks pipelines create --settings dlt/pipeline_config.json

# Or create from command line
databricks pipelines create \
  --name "f1_data_pipeline" \
  --storage "/Volumes/jai_patel_f1_data/racing_stats/pipeline_storage" \
  --target "jai_patel_f1_data.racing_stats" \
  --notebook "$WORKSPACE_PATH/dlt/f1_bronze_to_silver" \
  --notebook "$WORKSPACE_PATH/dlt/f1_gold_aggregations"
```

#### Step 4: Create Ingestion Job

```bash
# Create job configuration
cat > /tmp/ingestion_job.json << 'EOF'
{
  "name": "F1 Data Ingestion",
  "tasks": [{
    "task_key": "ingest_f1_data",
    "notebook_task": {
      "notebook_path": "/Workspace/Users/your.email@company.com/Formula1/notebooks/01_ingest_f1_data",
      "source": "WORKSPACE"
    },
    "new_cluster": {
      "spark_version": "14.3.x-scala2.12",
      "node_type_id": "i3.xlarge",
      "num_workers": 2
    },
    "libraries": [
      {"pypi": {"package": "pyyaml"}},
      {"pypi": {"package": "requests"}},
      {"pypi": {"package": "pandas"}}
    ]
  }],
  "max_concurrent_runs": 1
}
EOF

# Create the job
databricks jobs create --json-file /tmp/ingestion_job.json
```

## Running the Pipeline

### Option 1: Automated Run Script

```bash
# Set environment variables with your IDs
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"
export PIPELINE_ID="your-pipeline-id"
export JOB_ID="your-job-id"

# Make script executable
chmod +x deploy/run_pipeline.sh

# Run the pipeline
./deploy/run_pipeline.sh
```

### Option 2: Manual Execution

#### Run Data Ingestion

```bash
# List jobs to find your job ID
databricks jobs list

# Run the ingestion job
JOB_ID="your-job-id"
RUN_ID=$(databricks jobs run-now --job-id "$JOB_ID" | jq -r '.run_id')

# Monitor job status
databricks runs get --run-id "$RUN_ID"

# Wait for completion
databricks runs get-output --run-id "$RUN_ID"
```

#### Run DLT Pipeline

```bash
# List pipelines to find your pipeline ID
databricks pipelines list

# Start pipeline with full refresh
PIPELINE_ID="your-pipeline-id"
databricks pipelines start-update --pipeline-id "$PIPELINE_ID" --full-refresh

# Monitor pipeline
databricks pipelines get --pipeline-id "$PIPELINE_ID"
```

## Useful Commands

### Workspace Management

```bash
# List workspace contents
databricks workspace ls /Workspace/Users/your.email@company.com/Formula1

# Export a notebook
databricks workspace export /path/to/notebook output.py --format SOURCE

# Delete a file
databricks workspace delete /path/to/file
```

### Job Management

```bash
# List all jobs
databricks jobs list

# Get job details
databricks jobs get --job-id <job-id>

# List job runs
databricks runs list --job-id <job-id>

# Cancel a run
databricks runs cancel --run-id <run-id>

# Delete a job
databricks jobs delete --job-id <job-id>
```

### Pipeline Management

```bash
# List all pipelines
databricks pipelines list

# Get pipeline details
databricks pipelines get --pipeline-id <pipeline-id>

# List pipeline updates
databricks pipelines list-updates --pipeline-id <pipeline-id>

# Stop pipeline
databricks pipelines stop --pipeline-id <pipeline-id>

# Delete pipeline
databricks pipelines delete --pipeline-id <pipeline-id>
```

### SQL Execution

```bash
# Execute SQL query
databricks sql execute \
  --warehouse-id <warehouse-id> \
  --query "SELECT * FROM jai_patel_f1_data.racing_stats.gold_fastest_laps LIMIT 10"

# Execute SQL from file
databricks sql execute \
  --warehouse-id <warehouse-id> \
  --file dashboards/f1_race_analytics.sql
```

### Cluster Management

```bash
# List clusters
databricks clusters list

# Get cluster details
databricks clusters get --cluster-id <cluster-id>

# Start cluster
databricks clusters start --cluster-id <cluster-id>

# Stop cluster
databricks clusters stop --cluster-id <cluster-id>
```

## Environment-Specific Configurations

### Development Environment

```bash
export DATABRICKS_HOST="https://dev-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="dev-token"
export CLUSTER_ID="dev-cluster-id"

./deploy/databricks_cli_deploy.sh
```

### Production Environment

```bash
export DATABRICKS_HOST="https://prod-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="prod-token"
export CLUSTER_ID="prod-cluster-id"

./deploy/databricks_cli_deploy.sh
```

## Troubleshooting

### Authentication Issues

```bash
# Test connection
databricks workspace ls /

# Reconfigure
databricks configure --token
```

### File Upload Issues

```bash
# Check if file exists
databricks workspace ls /Workspace/Users/your.email@company.com/Formula1/

# Force overwrite
databricks workspace import file.py /path/to/file --overwrite --language PYTHON
```

### Pipeline Creation Issues

```bash
# Check existing pipelines
databricks pipelines list

# Get detailed error
databricks pipelines get --pipeline-id <pipeline-id>
```

### Job Execution Issues

```bash
# Get detailed run info
databricks runs get --run-id <run-id>

# Get run output/logs
databricks runs get-output --run-id <run-id>
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy F1 Pipeline

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install Databricks CLI
        run: pip install databricks-cli
      
      - name: Deploy to Databricks
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
          WAREHOUSE_ID: ${{ secrets.WAREHOUSE_ID }}
        run: |
          chmod +x deploy/databricks_cli_deploy.sh
          ./deploy/databricks_cli_deploy.sh
```

## Next Steps

After deployment:

1. **Verify Deployment**:
   ```bash
   databricks workspace ls /Workspace/Users/your.email@company.com/Formula1
   ```

2. **Run Initial Load**:
   ```bash
   ./deploy/run_pipeline.sh
   ```

3. **Query Data**:
   ```bash
   databricks sql execute --warehouse-id $WAREHOUSE_ID \
     --query "SELECT COUNT(*) FROM jai_patel_f1_data.racing_stats.silver_sessions"
   ```

4. **Set Up Scheduling**:
   ```bash
   # Update job with schedule
   databricks jobs update --job-id $JOB_ID --json '{
     "schedule": {
       "quartz_cron_expression": "0 0 * * * ?",
       "timezone_id": "America/Los_Angeles"
     }
   }'
   ```

## Additional Resources

- [Databricks CLI Documentation](https://docs.databricks.com/dev-tools/cli/index.html)
- [Delta Live Tables API](https://docs.databricks.com/workflows/delta-live-tables/delta-live-tables-api-guide.html)
- [Jobs API](https://docs.databricks.com/dev-tools/api/latest/jobs.html)

---

**Ready to deploy!** 🚀

Run the automated deployment script or follow the manual steps above to get your F1 data pipeline running on Databricks.

