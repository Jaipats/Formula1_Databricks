#!/usr/bin/env python3
"""
Get Genie Space ID for your F1 Analytics space
This script lists all Genie spaces in your workspace and helps you find the Space ID
"""

import os
import sys
from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config

def main():
    """List all Genie spaces and find F1 Analytics space"""
    
    print("="*70)
    print("Retrieving Genie Spaces from Databricks")
    print("="*70)
    print()
    
    try:
        # Initialize Workspace Client
        cfg = Config()
        w = WorkspaceClient(config=cfg)
        
        print(f"✓ Connected to: {cfg.host}")
        print()
        print("📋 Available Genie Spaces:")
        print("-" * 70)
        
        # List all Genie spaces
        spaces = w.genie.list_spaces()
        
        f1_space_id = None
        space_count = 0
        
        for space in spaces:
            space_count += 1
            print(f"\n{space_count}. {space.name}")
            print(f"   Space ID: {space.space_id}")
            if space.description:
                desc_preview = space.description[:100] + "..." if len(space.description) > 100 else space.description
                print(f"   Description: {desc_preview}")
            
            # Check if this is the F1 space
            if "F1" in space.name or "Formula" in space.name or "Race Analytics" in space.name:
                f1_space_id = space.space_id
                print(f"   ✨ This looks like your F1 Analytics space!")
        
        print()
        print("="*70)
        
        if f1_space_id:
            print("✅ Found F1 Analytics Genie Space!")
            print("="*70)
            print()
            print(f"Space ID: {f1_space_id}")
            print()
            print("📝 To enable the AI Chatbot in your Streamlit app:")
            print()
            print("Option 1: Set environment variable (for local development)")
            print(f"   export GENIE_SPACE_ID='{f1_space_id}'")
            print()
            print("Option 2: Update app.yaml (for Databricks Apps)")
            print("   Edit apps/app.yaml and add:")
            print("   ```yaml")
            print("   env:")
            print("     - name: GENIE_SPACE_ID")
            print(f"       value: \"{f1_space_id}\"")
            print("   ```")
            print()
            print(f"🔗 Access your Genie Space: https://{cfg.host}/genie/rooms/{f1_space_id}")
            print()
        elif space_count == 0:
            print("⚠️ No Genie Spaces found in your workspace")
            print()
            print("To create a Genie Space, run:")
            print("   python deploy/create_genie_space.py")
            print()
        else:
            print(f"ℹ️  Found {space_count} Genie Space(s), but none matched 'F1' or 'Formula'")
            print()
            print("If one of the above spaces is your F1 Analytics space,")
            print("copy its Space ID and use it in your app configuration.")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print()
        print("💡 Make sure you have:")
        print("  - DATABRICKS_HOST or DATABRICKS_SERVER_HOSTNAME set")
        print("  - DATABRICKS_TOKEN set")
        print("  - Permissions to access Genie spaces")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

