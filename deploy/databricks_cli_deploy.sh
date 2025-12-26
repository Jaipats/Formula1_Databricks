#!/bin/bash
# Databricks CLI Deployment Script for Formula 1 Data Pipeline
# This script deploys the entire F1 pipeline to Databricks using the CLI

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - UPDATE THESE VALUES
DATABRICKS_HOST="${DATABRICKS_HOST:-}"  # e.g., https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN="${DATABRICKS_TOKEN:-}"  # Your personal access token
DATABRICKS_USER="${DATABRICKS_USER:-}"  # Optional: Databricks user email (will be auto-detected)
CATALOG_NAME="jai_patel_f1_data"
SCHEMA_NAME="racing_stats"
CLUSTER_ID="${CLUSTER_ID:-}"  # Optional: existing cluster ID
WAREHOUSE_ID="${WAREHOUSE_ID:-}"  # SQL Warehouse ID for setup

# Print banner
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  F1 Data Pipeline - Databricks Deploy${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo -e "${RED}Error: Databricks CLI is not installed${NC}"
    echo "Install it with: pip install databricks-cli"
    exit 1
fi

echo -e "${GREEN}✓ Databricks CLI found${NC}"

# Check configuration
if [ -z "$DATABRICKS_HOST" ] || [ -z "$DATABRICKS_TOKEN" ]; then
    echo -e "${YELLOW}Warning: DATABRICKS_HOST or DATABRICKS_TOKEN not set${NC}"
    echo "Please configure Databricks CLI:"
    echo "  databricks configure --token"
    echo ""
    echo "Or set environment variables:"
    echo "  export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com"
    echo "  export DATABRICKS_TOKEN=your-token"
    exit 1
fi

# Configure Databricks CLI
export DATABRICKS_HOST
export DATABRICKS_TOKEN

echo -e "${GREEN}✓ Databricks credentials configured${NC}"

# Get current Databricks user
echo "Detecting Databricks user..."
if [ -z "$DATABRICKS_USER" ]; then
    # Try to get current user from Databricks API
    DATABRICKS_USER=$(databricks current-user me 2>/dev/null | jq -r '.userName' 2>/dev/null) || \
    DATABRICKS_USER=$(curl -s -H "Authorization: Bearer $DATABRICKS_TOKEN" \
        "${DATABRICKS_HOST}/api/2.0/preview/scim/v2/Me" | jq -r '.userName' 2>/dev/null) || \
    DATABRICKS_USER="${USER}@company.com"
    
    if [ "$DATABRICKS_USER" = "null" ] || [ -z "$DATABRICKS_USER" ]; then
        echo -e "${YELLOW}Could not auto-detect user. Using default: ${USER}@company.com${NC}"
        echo -e "${YELLOW}Set DATABRICKS_USER environment variable if this is incorrect${NC}"
        DATABRICKS_USER="${USER}@company.com"
    fi
fi

echo -e "${GREEN}✓ Databricks user: ${DATABRICKS_USER}${NC}"

# Set workspace path using the detected user
WORKSPACE_PATH="/Workspace/Users/${DATABRICKS_USER}/Formula1"
echo -e "${GREEN}✓ Workspace path: ${WORKSPACE_PATH}${NC}"
echo ""

# Step 1: Create workspace directory
echo -e "${BLUE}Step 1: Creating workspace directory...${NC}"
databricks workspace mkdirs "$WORKSPACE_PATH" || true
databricks workspace mkdirs "$WORKSPACE_PATH/config" || true
databricks workspace mkdirs "$WORKSPACE_PATH/utils" || true
databricks workspace mkdirs "$WORKSPACE_PATH/notebooks" || true
databricks workspace mkdirs "$WORKSPACE_PATH/dlt" || true
echo -e "${GREEN}✓ Workspace directories created${NC}"
echo ""

# Step 2: Upload Python files
echo -e "${BLUE}Step 2: Uploading Python modules...${NC}"
databricks workspace import "$WORKSPACE_PATH/config/__init__.py" --file config/__init__.py --language PYTHON --overwrite
databricks workspace import "$WORKSPACE_PATH/config/settings.py" --file config/settings.py --language PYTHON --overwrite
databricks workspace import "$WORKSPACE_PATH/utils/__init__.py" --file utils/__init__.py --language PYTHON --overwrite
databricks workspace import "$WORKSPACE_PATH/utils/api_client.py" --file utils/api_client.py --language PYTHON --overwrite
databricks workspace import "$WORKSPACE_PATH/utils/data_fetcher.py" --file utils/data_fetcher.py --language PYTHON --overwrite
echo -e "${GREEN}✓ Python modules uploaded${NC}"
echo ""

# Step 3: Upload configuration files
echo -e "${BLUE}Step 3: Uploading configuration files...${NC}"
databricks workspace import "$WORKSPACE_PATH/config/pipeline_config.yaml" --file config/pipeline_config.yaml --format AUTO --overwrite
databricks workspace import "$WORKSPACE_PATH/requirements.txt" --file requirements.txt --format AUTO --overwrite
echo -e "${GREEN}✓ Configuration files uploaded${NC}"
echo ""

# Step 4: Upload notebooks
echo -e "${BLUE}Step 4: Uploading notebooks...${NC}"
databricks workspace import "$WORKSPACE_PATH/notebooks/01_ingest_f1_data" --file notebooks/01_ingest_f1_data.py --language PYTHON --overwrite
databricks workspace import "$WORKSPACE_PATH/notebooks/02_explore_data" --file notebooks/02_explore_data.py --language PYTHON --overwrite
databricks workspace import "$WORKSPACE_PATH/dlt/f1_bronze_to_silver" --file dlt/f1_bronze_to_silver.py --language PYTHON --overwrite
databricks workspace import "$WORKSPACE_PATH/dlt/f1_gold_aggregations" --file dlt/f1_gold_aggregations.py --language PYTHON --overwrite
echo -e "${GREEN}✓ Notebooks uploaded${NC}"
echo ""

# Step 5: Create Unity Catalog and Schema
echo -e "${BLUE}Step 5: Creating Unity Catalog and Schema...${NC}"
if [ -n "$WAREHOUSE_ID" ]; then
    echo "Creating catalog: $CATALOG_NAME"
    databricks sql execute \
        --warehouse-id "$WAREHOUSE_ID" \
        --query "CREATE CATALOG IF NOT EXISTS $CATALOG_NAME COMMENT 'Formula 1 race data and analytics'" || true
    
    echo "Creating schema: $SCHEMA_NAME"
    databricks sql execute \
        --warehouse-id "$WAREHOUSE_ID" \
        --query "CREATE SCHEMA IF NOT EXISTS ${CATALOG_NAME}.${SCHEMA_NAME} COMMENT 'F1 racing statistics and telemetry data'" || true
    
    echo "Creating volumes"
    databricks sql execute \
        --warehouse-id "$WAREHOUSE_ID" \
        --query "CREATE VOLUME IF NOT EXISTS ${CATALOG_NAME}.${SCHEMA_NAME}.raw_data COMMENT 'Storage for raw API responses and files'" || true
    
    databricks sql execute \
        --warehouse-id "$WAREHOUSE_ID" \
        --query "CREATE VOLUME IF NOT EXISTS ${CATALOG_NAME}.${SCHEMA_NAME}.pipeline_storage COMMENT 'Storage for DLT pipeline checkpoints and metadata'" || true
    
    echo -e "${GREEN}✓ Unity Catalog setup complete${NC}"
else
    echo -e "${YELLOW}⚠ Skipping catalog creation (WAREHOUSE_ID not set)${NC}"
    echo "  Run setup/setup_catalog.sql manually in Databricks SQL Editor"
fi
echo ""

# Step 6: Create DLT Pipeline
echo -e "${BLUE}Step 6: Creating Delta Live Tables pipeline...${NC}"

# Create pipeline configuration JSON
PIPELINE_CONFIG=$(cat <<EOF
{
  "name": "f1_data_pipeline",
  "storage": "/Volumes/${CATALOG_NAME}/${SCHEMA_NAME}/pipeline_storage",
  "configuration": {
    "catalog": "${CATALOG_NAME}",
    "schema": "${SCHEMA_NAME}"
  },
  "clusters": [
    {
      "label": "default",
      "autoscale": {
        "min_workers": 1,
        "max_workers": 5
      }
    }
  ],
  "libraries": [
    {
      "notebook": {
        "path": "${WORKSPACE_PATH}/dlt/f1_bronze_to_silver"
      }
    },
    {
      "notebook": {
        "path": "${WORKSPACE_PATH}/dlt/f1_gold_aggregations"
      }
    }
  ],
  "target": "${CATALOG_NAME}.${SCHEMA_NAME}",
  "continuous": false,
  "development": false,
  "photon": true,
  "channel": "CURRENT"
}
EOF
)

# Save pipeline config to temp file
TEMP_PIPELINE_CONFIG="/tmp/dlt_pipeline_config.json"
echo "$PIPELINE_CONFIG" > "$TEMP_PIPELINE_CONFIG"

# Create or update the pipeline
echo "Creating/updating DLT pipeline..."
PIPELINE_ID=$(databricks pipelines create --settings "$TEMP_PIPELINE_CONFIG" --json | jq -r '.pipeline_id' 2>/dev/null) || {
    echo -e "${YELLOW}Pipeline might already exist, attempting to get existing pipeline...${NC}"
    PIPELINE_ID=$(databricks pipelines list --json | jq -r ".[] | select(.name==\"f1_data_pipeline\") | .pipeline_id" | head -1)
}

if [ -n "$PIPELINE_ID" ]; then
    echo -e "${GREEN}✓ DLT Pipeline created/found: $PIPELINE_ID${NC}"
    echo "  Pipeline URL: ${DATABRICKS_HOST}/#joblist/pipelines/${PIPELINE_ID}"
else
    echo -e "${YELLOW}⚠ Could not create pipeline automatically${NC}"
    echo "  Please create manually in Databricks UI using the configuration in dlt/pipeline_config.json"
fi

rm -f "$TEMP_PIPELINE_CONFIG"
echo ""

# Step 7: Create ingestion job
echo -e "${BLUE}Step 7: Creating data ingestion job...${NC}"

# Determine cluster configuration
if [ -n "$CLUSTER_ID" ]; then
    CLUSTER_CONFIG="\"existing_cluster_id\": \"$CLUSTER_ID\""
else
    CLUSTER_CONFIG="\"new_cluster\": {
        \"spark_version\": \"14.3.x-scala2.12\",
        \"node_type_id\": \"i3.xlarge\",
        \"num_workers\": 2,
        \"spark_conf\": {
            \"spark.databricks.delta.preview.enabled\": \"true\"
        }
    }"
fi

INGESTION_JOB_CONFIG=$(cat <<EOF
{
  "name": "F1 Data Ingestion",
  "tasks": [
    {
      "task_key": "ingest_f1_data",
      "notebook_task": {
        "notebook_path": "${WORKSPACE_PATH}/notebooks/01_ingest_f1_data",
        "source": "WORKSPACE"
      },
      ${CLUSTER_CONFIG},
      "libraries": [
        {"pypi": {"package": "pyyaml"}},
        {"pypi": {"package": "requests"}},
        {"pypi": {"package": "pandas"}},
        {"pypi": {"package": "databricks-sdk"}}
      ],
      "timeout_seconds": 0,
      "max_retries": 1
    }
  ],
  "email_notifications": {},
  "timeout_seconds": 0,
  "max_concurrent_runs": 1,
  "format": "MULTI_TASK"
}
EOF
)

TEMP_JOB_CONFIG="/tmp/ingestion_job_config.json"
echo "$INGESTION_JOB_CONFIG" > "$TEMP_JOB_CONFIG"

JOB_ID=$(databricks jobs create --json-file "$TEMP_JOB_CONFIG" | jq -r '.job_id' 2>/dev/null) || {
    echo -e "${YELLOW}Job might already exist${NC}"
    JOB_ID=$(databricks jobs list --json | jq -r ".[] | select(.settings.name==\"F1 Data Ingestion\") | .job_id" | head -1)
}

if [ -n "$JOB_ID" ]; then
    echo -e "${GREEN}✓ Ingestion job created: $JOB_ID${NC}"
    echo "  Job URL: ${DATABRICKS_HOST}/#job/${JOB_ID}"
else
    echo -e "${YELLOW}⚠ Could not create job automatically${NC}"
fi

rm -f "$TEMP_JOB_CONFIG"
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Resources Created:${NC}"
echo "  • Workspace Path: $WORKSPACE_PATH"
echo "  • Catalog: $CATALOG_NAME"
echo "  • Schema: ${CATALOG_NAME}.${SCHEMA_NAME}"
if [ -n "$PIPELINE_ID" ]; then
    echo "  • DLT Pipeline ID: $PIPELINE_ID"
fi
if [ -n "$JOB_ID" ]; then
    echo "  • Ingestion Job ID: $JOB_ID"
fi
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Run data ingestion:"
if [ -n "$JOB_ID" ]; then
    echo "     databricks jobs run-now --job-id $JOB_ID"
else
    echo "     Open ${WORKSPACE_PATH}/notebooks/01_ingest_f1_data in Databricks"
fi
echo ""
echo "  2. Start DLT pipeline:"
if [ -n "$PIPELINE_ID" ]; then
    echo "     databricks pipelines start-update --pipeline-id $PIPELINE_ID --full-refresh"
else
    echo "     Create and start pipeline in Databricks UI"
fi
echo ""
echo -e "${GREEN}Deployment completed successfully!${NC}"

