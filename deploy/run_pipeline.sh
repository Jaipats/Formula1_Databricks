#!/bin/bash
# Run F1 Data Pipeline - Execute ingestion and DLT pipeline

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Running F1 Data Pipeline${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check for required parameters
PIPELINE_ID="${PIPELINE_ID:-}"
JOB_ID="${JOB_ID:-}"

if [ -z "$DATABRICKS_HOST" ] || [ -z "$DATABRICKS_TOKEN" ]; then
    echo -e "${YELLOW}Please set DATABRICKS_HOST and DATABRICKS_TOKEN${NC}"
    exit 1
fi

export DATABRICKS_HOST
export DATABRICKS_TOKEN

# Step 1: Run data ingestion
echo -e "${BLUE}Step 1: Running data ingestion job...${NC}"
if [ -n "$JOB_ID" ]; then
    RUN_ID=$(databricks jobs run-now --job-id "$JOB_ID" | jq -r '.run_id')
    echo "Started ingestion job run: $RUN_ID"
    echo "Monitoring job status..."
    
    # Wait for job to complete
    while true; do
        STATUS=$(databricks runs get --run-id "$RUN_ID" | jq -r '.state.life_cycle_state')
        RESULT=$(databricks runs get --run-id "$RUN_ID" | jq -r '.state.result_state // "RUNNING"')
        
        echo "  Status: $STATUS - $RESULT"
        
        if [ "$STATUS" = "TERMINATED" ] || [ "$STATUS" = "INTERNAL_ERROR" ]; then
            if [ "$RESULT" = "SUCCESS" ]; then
                echo -e "${GREEN}✓ Ingestion completed successfully${NC}"
                break
            else
                echo -e "${YELLOW}⚠ Ingestion failed or was cancelled${NC}"
                echo "Check logs at: ${DATABRICKS_HOST}/#job/${JOB_ID}/run/${RUN_ID}"
                exit 1
            fi
        fi
        
        sleep 10
    done
else
    echo -e "${YELLOW}JOB_ID not set. Please run ingestion manually or set JOB_ID${NC}"
    echo "You can find the job ID with: databricks jobs list"
fi
echo ""

# Step 2: Run DLT pipeline
echo -e "${BLUE}Step 2: Starting DLT pipeline...${NC}"
if [ -n "$PIPELINE_ID" ]; then
    UPDATE_ID=$(databricks pipelines start-update --pipeline-id "$PIPELINE_ID" --full-refresh | jq -r '.update_id')
    echo "Started DLT pipeline update: $UPDATE_ID"
    echo "Pipeline URL: ${DATABRICKS_HOST}/#joblist/pipelines/${PIPELINE_ID}/updates/${UPDATE_ID}"
    echo ""
    echo "Monitoring pipeline status..."
    
    # Wait for pipeline to complete
    while true; do
        STATUS=$(databricks pipelines get-update --pipeline-id "$PIPELINE_ID" --update-id "$UPDATE_ID" | jq -r '.update.state')
        
        echo "  Pipeline Status: $STATUS"
        
        if [ "$STATUS" = "COMPLETED" ]; then
            echo -e "${GREEN}✓ Pipeline completed successfully${NC}"
            break
        elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "CANCELED" ]; then
            echo -e "${YELLOW}⚠ Pipeline failed or was canceled${NC}"
            echo "Check details at: ${DATABRICKS_HOST}/#joblist/pipelines/${PIPELINE_ID}"
            exit 1
        fi
        
        sleep 15
    done
else
    echo -e "${YELLOW}PIPELINE_ID not set. Please start pipeline manually or set PIPELINE_ID${NC}"
    echo "You can find the pipeline ID with: databricks pipelines list"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Pipeline Execution Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Your F1 data is now available in:"
echo "  Catalog: jai_patel_f1_data"
echo "  Schema: racing_stats"
echo ""
echo "Query your data:"
echo "  databricks sql execute --warehouse-id \$WAREHOUSE_ID \\"
echo "    --query 'SELECT * FROM jai_patel_f1_data.racing_stats.gold_fastest_laps LIMIT 10'"

