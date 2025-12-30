#!/usr/bin/env python3
"""
Simple connection test script for Databricks
Use this to diagnose connection issues outside of Streamlit
"""

import os
import sys
from databricks import sql
from databricks.sdk.core import Config

def test_connection():
    """Test Databricks connection with detailed output"""
    
    print("="*60)
    print("Databricks Connection Test")
    print("="*60)
    
    # Check environment variables
    print("\n1. Checking Environment Variables:")
    print("-" * 60)
    
    host = os.getenv("DATABRICKS_HOST") or os.getenv("DATABRICKS_SERVER_HOSTNAME")
    http_path = os.getenv("DATABRICKS_HTTP_PATH")
    token = os.getenv("DATABRICKS_TOKEN")
    client_id = os.getenv("DATABRICKS_CLIENT_ID")
    client_secret = os.getenv("DATABRICKS_CLIENT_SECRET")
    
    print(f"DATABRICKS_HOST: {host if host else '❌ NOT SET'}")
    print(f"DATABRICKS_SERVER_HOSTNAME: {os.getenv('DATABRICKS_SERVER_HOSTNAME') if os.getenv('DATABRICKS_SERVER_HOSTNAME') else '❌ NOT SET'}")
    print(f"DATABRICKS_HTTP_PATH: {http_path if http_path else '❌ NOT SET'}")
    print(f"DATABRICKS_TOKEN: {'✅ SET (' + str(len(token)) + ' chars)' if token else '❌ NOT SET'}")
    print(f"DATABRICKS_CLIENT_ID: {'✅ SET' if client_id else '❌ NOT SET'}")
    print(f"DATABRICKS_CLIENT_SECRET: {'✅ SET' if client_secret else '❌ NOT SET'}")
    
    # Determine auth mode
    print("\n2. Determining Authentication Mode:")
    print("-" * 60)
    
    if client_id and client_secret:
        auth_mode = "App Authorization (Service Principal)"
    elif token:
        auth_mode = "Token Authentication"
    else:
        print("❌ ERROR: No authentication credentials found!")
        print("\nPlease set one of:")
        print("  - DATABRICKS_TOKEN=your-personal-access-token")
        print("  - DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET")
        return False
    
    print(f"Auth Mode: {auth_mode}")
    
    # Validate required settings
    print("\n3. Validating Configuration:")
    print("-" * 60)
    
    if not host:
        print("❌ ERROR: DATABRICKS_HOST not set!")
        print("Set it with: export DATABRICKS_HOST='your-workspace.cloud.databricks.com'")
        return False
    else:
        print(f"✅ Host: {host}")
    
    if not http_path:
        http_path = "/sql/1.0/warehouses/4b9b953939869799"
        print(f"⚠️  Using default HTTP path: {http_path}")
    else:
        print(f"✅ HTTP Path: {http_path}")
    
    # Attempt connection
    print("\n4. Attempting Connection:")
    print("-" * 60)
    
    try:
        print("Connecting to Databricks...")
        
        if auth_mode == "Token Authentication":
            connection = sql.connect(
                server_hostname=host,
                http_path=http_path,
                access_token=token,
                _socket_timeout=15
            )
        else:
            # Service principal OAuth
            cfg = Config()
            connection = sql.connect(
                server_hostname=host,
                http_path=http_path,
                credentials_provider=lambda: cfg.authenticate,
                _socket_timeout=15
            )
        
        print("✅ Connection established successfully!")
        
        # Test query
        print("\n5. Running Test Query:")
        print("-" * 60)
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 as test, current_timestamp() as ts")
            result = cursor.fetchone()
            print(f"✅ Query successful!")
            print(f"Result: test={result[0]}, timestamp={result[1]}")
        
        connection.close()
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED!")
        print(f"Error: {str(e)}")
        print("\n" + "="*60)
        print("Troubleshooting Tips:")
        print("="*60)
        print("""
1. Check if your token is valid:
   - Go to Databricks → User Settings → Developer → Access Tokens
   - Generate a new token if expired

2. Verify hostname format:
   - Should be: your-workspace.cloud.databricks.com
   - Should NOT include: https:// or trailing /

3. Check SQL Warehouse:
   - Make sure the warehouse is running
   - Verify the HTTP path is correct
   - Get it from: SQL Warehouses → Your Warehouse → Connection Details

4. Test connectivity:
   - Can you access Databricks UI?
   - Any firewall or VPN issues?

5. Token permissions:
   - Token must have access to the SQL Warehouse
   - Check Unity Catalog permissions
""")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

