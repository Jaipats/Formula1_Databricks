"""
Simple script to test Databricks connection without Streamlit
Run this to diagnose connection issues
"""

import os
import sys
from databricks import sql

# Configuration
DATABRICKS_SERVER_HOSTNAME = os.getenv("DATABRICKS_SERVER_HOSTNAME", "e2-demo-field-eng.cloud.databricks.com")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/4b9b953939869799")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
CATALOG = os.getenv("F1_CATALOG", "jai_patel_f1_data")
SCHEMA = os.getenv("F1_SCHEMA", "racing_stats")

def test_connection():
    """Test Databricks connection"""
    print("\n" + "="*70)
    print("  DATABRICKS CONNECTION TEST")
    print("="*70 + "\n")
    
    # Step 1: Check environment variables
    print("Step 1: Checking environment variables...")
    print(f"  ✓ DATABRICKS_SERVER_HOSTNAME: {DATABRICKS_SERVER_HOSTNAME}")
    print(f"  ✓ DATABRICKS_HTTP_PATH: {DATABRICKS_HTTP_PATH}")
    
    if not DATABRICKS_TOKEN:
        print("  ✗ DATABRICKS_TOKEN: NOT SET")
        print("\n❌ ERROR: DATABRICKS_TOKEN environment variable is not set!")
        print("\nTo fix, run:")
        print('  export DATABRICKS_TOKEN="your-token-here"')
        print("\nOr set it in your shell profile (.bashrc, .zshrc, etc.)")
        return False
    else:
        token_preview = DATABRICKS_TOKEN[:8] + "..." + DATABRICKS_TOKEN[-4:] if len(DATABRICKS_TOKEN) > 12 else "***"
        print(f"  ✓ DATABRICKS_TOKEN: {token_preview}")
    
    print(f"  ✓ CATALOG: {CATALOG}")
    print(f"  ✓ SCHEMA: {SCHEMA}")
    print()
    
    # Step 2: Attempt connection
    print("Step 2: Attempting to connect to Databricks...")
    print(f"  Connecting to {DATABRICKS_SERVER_HOSTNAME}...")
    
    try:
        connection = sql.connect(
            server_hostname=DATABRICKS_SERVER_HOSTNAME,
            http_path=DATABRICKS_HTTP_PATH,
            access_token=DATABRICKS_TOKEN,
            _socket_timeout=15  # 15 second timeout
        )
        print("  ✓ Connection established!")
        print()
        
    except Exception as e:
        print(f"  ✗ Connection failed: {str(e)}")
        print("\n❌ CONNECTION ERROR")
        print("\nPossible causes:")
        print("  1. Invalid token - check your DATABRICKS_TOKEN")
        print("  2. Incorrect hostname or HTTP path")
        print("  3. Network issues or firewall blocking connection")
        print("  4. Databricks warehouse is not running")
        print("\nTry:")
        print("  - Verify your token in Databricks UI (User Settings > Access Tokens)")
        print("  - Check if your warehouse is running")
        print("  - Verify the server hostname and HTTP path")
        return False
    
    # Step 3: Test query
    print("Step 3: Running test query...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            if result and result[0] == 1:
                print("  ✓ Test query successful!")
                print()
            else:
                print("  ✗ Unexpected query result")
                return False
    except Exception as e:
        print(f"  ✗ Query failed: {str(e)}")
        return False
    
    # Step 4: Check tables
    print("Step 4: Checking if F1 tables exist...")
    tables_to_check = [
        f"{CATALOG}.{SCHEMA}.silver_sessions",
        f"{CATALOG}.{SCHEMA}.silver_drivers",
        f"{CATALOG}.{SCHEMA}.gold_driver_performance",
        f"{CATALOG}.{SCHEMA}.gold_fastest_laps"
    ]
    
    for table in tables_to_check:
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM {table} LIMIT 1")
                result = cursor.fetchone()
                count = result[0] if result else 0
                print(f"  ✓ {table}: {count} rows")
        except Exception as e:
            error_str = str(e)
            if "does not exist" in error_str or "TABLE_OR_VIEW_NOT_FOUND" in error_str:
                print(f"  ✗ {table}: NOT FOUND (table doesn't exist)")
            else:
                print(f"  ✗ {table}: ERROR - {error_str[:80]}")
    
    print()
    print("="*70)
    print("  ✅ CONNECTION TEST PASSED!")
    print("="*70)
    print("\nYour Databricks connection is working!")
    print("If you see 'NOT FOUND' tables above, run the Lakeflow pipeline to create them.")
    print()
    
    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

