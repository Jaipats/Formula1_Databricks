#!/usr/bin/env python3
"""
Create a Databricks Genie Space for F1 Analytics
Uses the Databricks REST API to create a Genie space with F1 silver and gold tables.
API Documentation: https://docs.databricks.com/api/workspace/genie/createspace

⚠️ IMPORTANT: Run this AFTER completing the following:
   1. ✅ DLT pipeline has created all silver and gold tables
   2. ✅ Data is loaded and verified (check table counts)
   3. ✅ (Optional) Streamlit Databricks App is set up and tested

This ensures Genie has access to all your F1 data for querying.
"""

import os
import sys
import requests
import json

# Configuration
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST") or os.getenv("DATABRICKS_SERVER_HOSTNAME")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
CATALOG = os.getenv("F1_CATALOG", "jai_patel_f1_data")
SCHEMA = os.getenv("F1_SCHEMA", "racing_stats")

# Genie Space Configuration
GENIE_SPACE_NAME = "F1 Race Analytics"
GENIE_SPACE_DESCRIPTION = """
Formula 1 Race Analytics Genie Space

This space provides AI-powered analytics on Formula 1 racing data including:
- Race sessions, meetings, and results
- Driver performance and telemetry
- Team comparisons and strategies
- Pit stop analysis
- Tire strategy and compound usage
- Fastest laps and overtakes
- Weather conditions and race control events

Ask questions like:
- "Show me the fastest lap times for Lewis Hamilton in 2024"
- "Compare pit stop durations between Red Bull and Mercedes"
- "What tire compounds were used most in the Monaco Grand Prix?"
- "Which drivers had the most overtakes this season?"
"""

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

def validate_config():
    """Validate required configuration"""
    if not DATABRICKS_HOST:
        print("❌ Error: DATABRICKS_HOST or DATABRICKS_SERVER_HOSTNAME not set")
        print("Set it with: export DATABRICKS_HOST='your-workspace.cloud.databricks.com'")
        return False
    
    if not DATABRICKS_TOKEN:
        print("❌ Error: DATABRICKS_TOKEN not set")
        print("Set it with: export DATABRICKS_TOKEN='your-token'")
        return False
    
    return True

def create_genie_space():
    """Create Genie Space using Databricks REST API"""
    
    print("="*70)
    print("Creating Databricks Genie Space for F1 Analytics")
    print("="*70)
    print()
    
    # Validate configuration
    if not validate_config():
        return False
    
    print(f"📊 Catalog: {CATALOG}")
    print(f"📊 Schema: {SCHEMA}")
    print(f"🏎️  Space Name: {GENIE_SPACE_NAME}")
    print(f"📋 Tables: {len(SILVER_TABLES)} silver + {len(GOLD_TABLES)} gold = {len(SILVER_TABLES) + len(GOLD_TABLES)} total")
    print()
    
    # Build table references in Unity Catalog format
    all_tables = []
    
    print("📦 Including Silver Tables:")
    for table in SILVER_TABLES:
        full_table_name = f"{CATALOG}.{SCHEMA}.{table}"
        all_tables.append(full_table_name)
        print(f"   ✓ {full_table_name}")
    
    print()
    print("📦 Including Gold Tables:")
    for table in GOLD_TABLES:
        full_table_name = f"{CATALOG}.{SCHEMA}.{table}"
        all_tables.append(full_table_name)
        print(f"   ✓ {full_table_name}")
    
    print()
    print("🚀 Creating Genie Space...")
    
    # Prepare API request
    url = f"https://{DATABRICKS_HOST}/api/2.0/genie/spaces"
    
    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "display_name": GENIE_SPACE_NAME,
        "description": GENIE_SPACE_DESCRIPTION.strip(),
        "table_full_names": all_tables
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            space_id = result.get("space_id", "unknown")
            
            print("="*70)
            print("✅ SUCCESS! Genie Space Created")
            print("="*70)
            print(f"Space ID: {space_id}")
            print(f"Name: {GENIE_SPACE_NAME}")
            print(f"Tables: {len(all_tables)}")
            print()
            print("🎉 You can now use Genie to ask questions about your F1 data!")
            print()
            print("Example questions:")
            print("  - Show me the top 10 fastest laps from 2024")
            print("  - Compare Red Bull and Mercedes pit stop performance")
            print("  - What was the weather like during the Monaco Grand Prix?")
            print("  - Which driver had the most overtakes this season?")
            print()
            print(f"Access your Genie Space in Databricks UI:")
            print(f"https://{DATABRICKS_HOST}/genie/spaces/{space_id}")
            print()
            
            return True
            
        else:
            print("="*70)
            print("❌ FAILED to create Genie Space")
            print("="*70)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            print()
            
            # Provide helpful error messages
            if response.status_code == 400:
                print("💡 Bad Request - Possible issues:")
                print("   - Tables may not exist yet (run DLT pipeline first)")
                print("   - Invalid table names or catalog/schema")
                print("   - Genie may not be enabled in your workspace")
            elif response.status_code == 401:
                print("💡 Authentication failed - check your DATABRICKS_TOKEN")
            elif response.status_code == 403:
                print("💡 Permission denied - you may not have access to create Genie spaces")
            elif response.status_code == 404:
                print("💡 Endpoint not found - Genie may not be available in your workspace")
            
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - server took too long to respond")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Main function"""
    success = create_genie_space()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

