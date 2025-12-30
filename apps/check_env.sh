#!/bin/bash
# Simple environment check for Databricks connection

echo "=========================================="
echo "Databricks Environment Check"
echo "=========================================="
echo ""

echo "Required Environment Variables:"
echo "------------------------------------------"

if [ -z "$DATABRICKS_HOST" ] && [ -z "$DATABRICKS_SERVER_HOSTNAME" ]; then
    echo "❌ DATABRICKS_HOST: NOT SET"
    echo "❌ DATABRICKS_SERVER_HOSTNAME: NOT SET"
    echo ""
    echo "⚠️  Please set ONE of these variables:"
    echo "   export DATABRICKS_HOST='your-workspace.cloud.databricks.com'"
    echo "   OR"
    echo "   export DATABRICKS_SERVER_HOSTNAME='your-workspace.cloud.databricks.com'"
else
    echo "✅ DATABRICKS_HOST: ${DATABRICKS_HOST:-not set}"
    echo "✅ DATABRICKS_SERVER_HOSTNAME: ${DATABRICKS_SERVER_HOSTNAME:-not set}"
fi

echo ""

if [ -z "$DATABRICKS_HTTP_PATH" ]; then
    echo "⚠️  DATABRICKS_HTTP_PATH: NOT SET (will use default)"
else
    echo "✅ DATABRICKS_HTTP_PATH: $DATABRICKS_HTTP_PATH"
fi

echo ""
echo "Authentication:"
echo "------------------------------------------"

if [ -n "$DATABRICKS_TOKEN" ]; then
    echo "✅ DATABRICKS_TOKEN: SET (${#DATABRICKS_TOKEN} characters)"
elif [ -n "$DATABRICKS_CLIENT_ID" ] && [ -n "$DATABRICKS_CLIENT_SECRET" ]; then
    echo "✅ DATABRICKS_CLIENT_ID: SET"
    echo "✅ DATABRICKS_CLIENT_SECRET: SET"
    echo "   (App Authorization mode)"
else
    echo "❌ NO AUTHENTICATION FOUND!"
    echo ""
    echo "For local development, set:"
    echo "   export DATABRICKS_TOKEN='your-personal-access-token'"
    echo ""
    echo "To get a token:"
    echo "   1. Go to Databricks workspace"
    echo "   2. Click your username (top right)"
    echo "   3. User Settings → Developer → Access Tokens"
    echo "   4. Generate New Token"
    echo "   5. Copy and set as environment variable"
fi

echo ""
echo "=========================================="

# Check if all required vars are set
if [ -z "$DATABRICKS_TOKEN" ] && [ -z "$DATABRICKS_CLIENT_ID" ]; then
    echo "❌ SETUP INCOMPLETE"
    echo ""
    echo "Quick setup for local development:"
    echo "-----------------------------------"
    echo "export DATABRICKS_HOST='e2-demo-field-eng.cloud.databricks.com'"
    echo "export DATABRICKS_HTTP_PATH='/sql/1.0/warehouses/4b9b953939869799'"
    echo "export DATABRICKS_TOKEN='dapi...'  # Your personal access token"
    echo ""
    echo "Then restart your Streamlit app:"
    echo "   streamlit run app.py"
    exit 1
else
    echo "✅ ENVIRONMENT READY"
    exit 0
fi

