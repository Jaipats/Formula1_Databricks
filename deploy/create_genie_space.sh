#!/bin/bash
# Create a Databricks Genie Space for F1 Analytics
# Uses the Databricks REST API to create a Genie space with F1 silver and gold tables.
# API Documentation: https://docs.databricks.com/api/workspace/genie/createspace
#
# ⚠️ IMPORTANT: Run this AFTER completing the following:
#    1. ✅ DLT pipeline has created all silver and gold tables
#    2. ✅ Data is loaded and verified (check table counts)
#    3. ✅ (Optional) Streamlit Databricks App is set up and tested
#
# This ensures Genie has access to all your F1 data for querying.

set -e

# Configuration
DATABRICKS_HOST="${DATABRICKS_HOST:-${DATABRICKS_SERVER_HOSTNAME}}"
DATABRICKS_TOKEN="${DATABRICKS_TOKEN}"
CATALOG="${F1_CATALOG:-jai_patel_f1_data}"
SCHEMA="${F1_SCHEMA:-racing_stats}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Genie Space Configuration
SPACE_NAME="F1 Race Analytics"
SPACE_DESCRIPTION="Formula 1 Race Analytics Genie Space

This space provides AI-powered analytics on Formula 1 racing data including:
- Race sessions, meetings, and results
- Driver performance and telemetry
- Team comparisons and strategies
- Pit stop analysis
- Tire strategy and compound usage
- Fastest laps and overtakes
- Weather conditions and race control events

Ask questions like:
- Show me the fastest lap times for Lewis Hamilton in 2024
- Compare pit stop durations between Red Bull and Mercedes
- What tire compounds were used most in the Monaco Grand Prix?
- Which drivers had the most overtakes this season?"

# Validate configuration
if [ -z "$DATABRICKS_HOST" ]; then
    echo -e "${RED}❌ Error: DATABRICKS_HOST or DATABRICKS_SERVER_HOSTNAME not set${NC}"
    echo "Set it with: export DATABRICKS_HOST='your-workspace.cloud.databricks.com'"
    exit 1
fi

if [ -z "$DATABRICKS_TOKEN" ]; then
    echo -e "${RED}❌ Error: DATABRICKS_TOKEN not set${NC}"
    echo "Set it with: export DATABRICKS_TOKEN='your-token'"
    exit 1
fi

echo "======================================================================"
echo "Creating Databricks Genie Space for F1 Analytics"
echo "======================================================================"
echo ""
echo -e "${BLUE}📊 Catalog:${NC} $CATALOG"
echo -e "${BLUE}📊 Schema:${NC} $SCHEMA"
echo -e "${BLUE}🏎️  Space Name:${NC} $SPACE_NAME"
echo ""

# Build table list
SILVER_TABLES=(
    "silver_meetings"
    "silver_sessions"
    "silver_drivers"
    "silver_laps"
    "silver_pit"
    "silver_stints"
    "silver_weather"
    "silver_race_control"
    "silver_team_radio"
    "silver_intervals"
    "silver_overtakes"
    "silver_session_result"
    "silver_starting_grid"
)

GOLD_TABLES=(
    "gold_driver_performance"
    "gold_race_summary"
    "gold_team_performance"
    "gold_tyre_strategy"
    "gold_fastest_laps"
    "gold_overtakes_analysis"
)

# Build JSON array of table names
TABLE_ARRAY="["
FIRST=true

echo -e "${GREEN}📦 Including Silver Tables:${NC}"
for table in "${SILVER_TABLES[@]}"; do
    if [ "$FIRST" = false ]; then
        TABLE_ARRAY+=","
    fi
    FIRST=false
    TABLE_ARRAY+="\"${CATALOG}.${SCHEMA}.${table}\""
    echo "   ✓ ${CATALOG}.${SCHEMA}.${table}"
done

echo ""
echo -e "${GREEN}📦 Including Gold Tables:${NC}"
for table in "${GOLD_TABLES[@]}"; do
    TABLE_ARRAY+=",\"${CATALOG}.${SCHEMA}.${table}\""
    echo "   ✓ ${CATALOG}.${SCHEMA}.${table}"
done

TABLE_ARRAY+="]"

echo ""
echo -e "${YELLOW}🚀 Creating Genie Space...${NC}"

# Create serialized_space configuration
SPACE_CONFIG="{\"table_full_names\": ${TABLE_ARRAY}}"

# Escape for JSON string (serialize as JSON string)
# The serialized_space must be a JSON string, not an object
SERIALIZED_SPACE_JSON=$(echo "$SPACE_CONFIG" | jq -c . | jq -R .)

# Create final payload
PAYLOAD=$(jq -n \
  --arg display_name "${SPACE_NAME}" \
  --arg description "${SPACE_DESCRIPTION}" \
  --argjson serialized_space "${SPACE_CONFIG}" \
  '{
    display_name: $display_name,
    description: $description,
    serialized_space: ($serialized_space | tostring)
  }')

# Make API request
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  "https://${DATABRICKS_HOST}/api/2.0/genie/spaces" \
  -H "Authorization: Bearer ${DATABRICKS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}")

# Parse response
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
    SPACE_ID=$(echo "$BODY" | grep -o '"space_id":"[^"]*"' | cut -d'"' -f4)
    
    echo ""
    echo "======================================================================"
    echo -e "${GREEN}✅ SUCCESS! Genie Space Created${NC}"
    echo "======================================================================"
    echo -e "${BLUE}Space ID:${NC} $SPACE_ID"
    echo -e "${BLUE}Name:${NC} $SPACE_NAME"
    echo -e "${BLUE}Tables:${NC} $((${#SILVER_TABLES[@]} + ${#GOLD_TABLES[@]}))"
    echo ""
    echo "🎉 You can now use Genie to ask questions about your F1 data!"
    echo ""
    echo "Example questions:"
    echo "  - Show me the top 10 fastest laps from 2024"
    echo "  - Compare Red Bull and Mercedes pit stop performance"
    echo "  - What was the weather like during the Monaco Grand Prix?"
    echo "  - Which driver had the most overtakes this season?"
    echo ""
    echo "Access your Genie Space in Databricks UI:"
    echo "https://${DATABRICKS_HOST}/genie/spaces/${SPACE_ID}"
    echo ""
    exit 0
else
    echo ""
    echo "======================================================================"
    echo -e "${RED}❌ FAILED to create Genie Space${NC}"
    echo "======================================================================"
    echo -e "${RED}Status Code:${NC} $HTTP_CODE"
    echo -e "${RED}Response:${NC} $BODY"
    echo ""
    
    # Provide helpful error messages
    case $HTTP_CODE in
        400)
            echo "💡 Bad Request - Possible issues:"
            echo "   - Tables may not exist yet (run DLT pipeline first)"
            echo "   - Invalid table names or catalog/schema"
            echo "   - Genie may not be enabled in your workspace"
            ;;
        401)
            echo "💡 Authentication failed - check your DATABRICKS_TOKEN"
            ;;
        403)
            echo "💡 Permission denied - you may not have access to create Genie spaces"
            ;;
        404)
            echo "💡 Endpoint not found - Genie may not be available in your workspace"
            ;;
    esac
    
    exit 1
fi

