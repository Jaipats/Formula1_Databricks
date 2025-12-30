# Databricks notebook source
# MAGIC %md
# MAGIC # Create Genie Space for F1 Analytics
# MAGIC
# MAGIC This notebook creates a Databricks Genie Space with all F1 silver and gold tables.
# MAGIC
# MAGIC **⚠️ IMPORTANT: Run this AFTER completing:**
# MAGIC 1. ✅ DLT pipeline has created all silver and gold tables
# MAGIC 2. ✅ Data is loaded and verified (see Step 5 below)
# MAGIC 3. ✅ (Optional) Streamlit Databricks App is set up and tested
# MAGIC
# MAGIC This ensures Genie has access to all your F1 data for querying.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **What is Genie?**
# MAGIC Genie is an AI-powered conversational analytics tool that allows you to ask natural language questions about your data.
# MAGIC
# MAGIC **What this notebook does:**
# MAGIC - Creates a Genie Space named "F1 Race Analytics"
# MAGIC - Includes all silver tables (raw race data)
# MAGIC - Includes all gold tables (aggregated analytics)
# MAGIC - Enables natural language queries on F1 data
# MAGIC
# MAGIC **API Documentation:** https://docs.databricks.com/api/workspace/genie/createspace

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import requests
import json

# Configuration
CATALOG = "jai_patel_f1_data"
SCHEMA = "racing_stats"

# Get Warehouse ID from environment or use default
# You can find your warehouse ID in: SQL Warehouses → Your Warehouse → Details
# Or from the URL: /sql/warehouses/<warehouse-id>
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "4b9b953939869799")  # Update with your warehouse ID

# Genie Space Configuration
SPACE_NAME = "F1 Race Analytics"
SPACE_DESCRIPTION = """Formula 1 Race Analytics Genie Space

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
- Which drivers had the most overtakes this season?
"""

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define Tables to Include

# COMMAND ----------

# Silver Tables (Core Data)
SILVER_TABLES = [
    "silver_meetings",      # Race weekends
    "silver_sessions",      # Practice, Qualifying, Race sessions
    "silver_drivers",       # Driver information per session
    "silver_laps",          # Lap times and telemetry
    "silver_pit",           # Pit stop data
    "silver_stints",        # Tire stints
    "silver_weather",       # Weather conditions
    "silver_race_control",  # Race control messages (flags, safety car, etc.)
    "silver_team_radio",    # Team radio messages
    "silver_intervals",     # Time intervals between drivers
    "silver_overtakes",     # Overtaking events
    "silver_session_result",# Session results
    "silver_starting_grid", # Starting grid positions
]

# Gold Tables (Aggregated Analytics)
GOLD_TABLES = [
    "gold_driver_performance",  # Driver stats per session
    "gold_race_summary",        # Race summary metrics
    "gold_team_performance",    # Team performance aggregations
    "gold_tyre_strategy",       # Tire strategy analysis
    "gold_fastest_laps",        # Fastest laps ranking
    "gold_overtakes_analysis",  # Overtake statistics
]

# Build complete table list
all_tables = []
all_tables.extend([f"{CATALOG}.{SCHEMA}.{table}" for table in SILVER_TABLES])
all_tables.extend([f"{CATALOG}.{SCHEMA}.{table}" for table in GOLD_TABLES])

print(f"📊 Total Tables: {len(all_tables)}")
print(f"   - Silver: {len(SILVER_TABLES)}")
print(f"   - Gold: {len(GOLD_TABLES)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Display Tables to Include

# COMMAND ----------

print("="*70)
print("Tables to be included in Genie Space")
print("="*70)
print()
print("📦 Silver Tables (Core Data):")
for table in SILVER_TABLES:
    print(f"   ✓ {CATALOG}.{SCHEMA}.{table}")

print()
print("📦 Gold Tables (Aggregated Analytics):")
for table in GOLD_TABLES:
    print(f"   ✓ {CATALOG}.{SCHEMA}.{table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Tables Exist (Optional)
# MAGIC
# MAGIC Run this cell to check if all tables exist before creating the Genie space.

# COMMAND ----------

print("🔍 Checking if tables exist...")
print()

missing_tables = []
existing_tables = []

for table in all_tables:
    try:
        # Try to read just one row to verify table exists
        df = spark.sql(f"SELECT * FROM {table} LIMIT 1")
        existing_tables.append(table)
        print(f"✅ {table}")
    except Exception as e:
        missing_tables.append(table)
        print(f"❌ {table} - {str(e)[:50]}")

print()
print("="*70)
print(f"Summary: {len(existing_tables)} exist, {len(missing_tables)} missing")
print("="*70)

if missing_tables:
    print()
    print("⚠️ Missing tables - you may want to run the DLT pipeline first:")
    for table in missing_tables:
        print(f"   - {table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Genie Space

# COMMAND ----------

# Get workspace context
workspace_url = spark.conf.get("spark.databricks.workspaceUrl")
# Get token using Databricks secrets or dbutils
token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

print("🚀 Creating Genie Space...")
print(f"Workspace: {workspace_url}")
print(f"Space Name: {SPACE_NAME}")
print(f"Tables: {len(all_tables)}")
print()

# API endpoint
url = f"https://{workspace_url}/api/2.0/genie/spaces"

# Request headers
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Request payload - serialized_space must be a JSON string (not object!)
space_config = {
    "table_full_names": all_tables
}

payload = {
    "display_name": SPACE_NAME,
    "description": SPACE_DESCRIPTION.strip(),
    "warehouse_id": WAREHOUSE_ID,
    "serialized_space": json.dumps(space_config)  # Convert to JSON string
}

# Make API request
try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    if response.status_code == 200 or response.status_code == 201:
        result = response.json()
        space_id = result.get("space_id", "unknown")
        
        print("="*70)
        print("✅ SUCCESS! Genie Space Created")
        print("="*70)
        print(f"Space ID: {space_id}")
        print(f"Name: {SPACE_NAME}")
        print(f"Tables: {len(all_tables)}")
        print()
        print("🎉 You can now use Genie to ask questions about your F1 data!")
        print()
        print("Access your Genie Space:")
        print(f"https://{workspace_url}/genie/spaces/{space_id}")
        
        displayHTML(f"""
        <div style="padding: 20px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px;">
            <h3 style="color: #155724;">✅ Genie Space Created Successfully!</h3>
            <p><strong>Space ID:</strong> {space_id}</p>
            <p><strong>Name:</strong> {SPACE_NAME}</p>
            <p><strong>Tables:</strong> {len(all_tables)}</p>
            <p><a href="https://{workspace_url}/genie/spaces/{space_id}" target="_blank" style="color: #155724; font-weight: bold;">
                🚀 Open Genie Space →
            </a></p>
        </div>
        """)
        
    else:
        print("="*70)
        print("❌ FAILED to create Genie Space")
        print("="*70)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Provide helpful error messages
        if response.status_code == 400:
            print("\n💡 Bad Request - Possible issues:")
            print("   - Some tables may not exist yet (check verification above)")
            print("   - Genie may not be enabled in your workspace")
        elif response.status_code == 401:
            print("\n💡 Authentication failed")
        elif response.status_code == 403:
            print("\n💡 Permission denied - you may not have access to create Genie spaces")
        elif response.status_code == 404:
            print("\n💡 Endpoint not found - Genie may not be available in your workspace")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Example Questions to Ask Genie
# MAGIC
# MAGIC Once your Genie Space is created, try these questions:
# MAGIC
# MAGIC ### Driver Performance
# MAGIC - "Show me the top 10 fastest laps from 2024"
# MAGIC - "What is Lewis Hamilton's average lap time this season?"
# MAGIC - "Which driver has the most pole positions?"
# MAGIC - "Compare Max Verstappen and Charles Leclerc lap times"
# MAGIC
# MAGIC ### Team Analysis
# MAGIC - "Compare Red Bull and Mercedes pit stop performance"
# MAGIC - "Which team has the fastest average pit stop?"
# MAGIC - "Show me team performance by race"
# MAGIC
# MAGIC ### Race Events
# MAGIC - "What was the weather like during the Monaco Grand Prix?"
# MAGIC - "How many overtakes happened in the last race?"
# MAGIC - "Which races had safety car periods?"
# MAGIC - "Show me all race control messages for the last race"
# MAGIC
# MAGIC ### Tire Strategy
# MAGIC - "What tire compounds were used most in 2024?"
# MAGIC - "Compare soft vs hard tire performance"
# MAGIC - "Which team has the best tire strategy?"
# MAGIC
# MAGIC ### Historical Analysis
# MAGIC - "Show me the fastest lap progression throughout the season"
# MAGIC - "Which circuits have the most overtakes?"
# MAGIC - "What's the correlation between starting position and final position?"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next Steps
# MAGIC
# MAGIC 1. ✅ Genie Space created with F1 data
# MAGIC 2. 🔗 Click the link above to access your Genie Space
# MAGIC 3. 💬 Start asking questions in natural language
# MAGIC 4. 📊 Genie will automatically query your tables and visualize results
# MAGIC 5. 🎯 Refine questions based on Genie's suggestions
# MAGIC
# MAGIC **Tips:**
# MAGIC - Be specific about time ranges, drivers, or teams
# MAGIC - Ask for comparisons to get interesting insights
# MAGIC - Use follow-up questions to drill down into details
# MAGIC - Genie learns from your questions and improves over time

