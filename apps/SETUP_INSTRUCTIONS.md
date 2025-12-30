# F1 Dashboard App - Setup Instructions

## 📖 Authentication Method

This app follows the official [Databricks Apps Streamlit tutorial](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-streamlit) authentication pattern.

## 🔴 Common Issue

**Error:** `❌ Failed to connect to Databricks: Error during request to server`

**Root Cause:** Missing required environment variables (DATABRICKS_HOST and DATABRICKS_TOKEN).

## ✅ Solution: Configure Environment Variables

### Step 1: Get Your Databricks Personal Access Token

1. Open your Databricks workspace in a browser
2. Click your **username** in the top-right corner
3. Select **User Settings**
4. Go to **Developer** tab
5. Click **Access Tokens**
6. Click **Generate New Token**
   - Comment: "F1 Dashboard App"
   - Lifetime: 90 days (or your preference)
7. Click **Generate**
8. **COPY THE TOKEN IMMEDIATELY** (you can't see it again!)

### Step 2: Set Environment Variables

**Option A: In Your Current Terminal Session** (Temporary)

```bash
# Set the token
export DATABRICKS_TOKEN='dapi1234567890abcdef...'  # Replace with your actual token

# Set the hostname
export DATABRICKS_HOST='e2-demo-field-eng.cloud.databricks.com'

# Set the SQL Warehouse path
export DATABRICKS_HTTP_PATH='/sql/1.0/warehouses/4b9b953939869799'

# Optional: Configure catalog and schema
export F1_CATALOG='jai_patel_f1_data'
export F1_SCHEMA='racing_stats'
```

**Option B: Add to Shell Profile** (Permanent)

For Zsh (macOS default):
```bash
# Edit your .zshrc file
nano ~/.zshrc

# Add these lines at the end:
export DATABRICKS_TOKEN='dapi1234567890abcdef...'
export DATABRICKS_HOST='e2-demo-field-eng.cloud.databricks.com'
export DATABRICKS_HTTP_PATH='/sql/1.0/warehouses/4b9b953939869799'
export F1_CATALOG='jai_patel_f1_data'
export F1_SCHEMA='racing_stats'

# Save and exit (Ctrl+X, then Y, then Enter)

# Reload your shell configuration
source ~/.zshrc
```

For Bash:
```bash
# Edit your .bashrc file
nano ~/.bashrc

# Add the same exports as above
# Then reload:
source ~/.bashrc
```

**Option C: Create a .env File** (For use with python-dotenv)

```bash
cd /Users/jaideep.patel/Cursor/Formula1_Databricks/apps

cat > .env << 'EOF'
DATABRICKS_TOKEN=dapi1234567890abcdef...
DATABRICKS_HOST=e2-demo-field-eng.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/4b9b953939869799
F1_CATALOG=jai_patel_f1_data
F1_SCHEMA=racing_stats
EOF

# Add .env to .gitignore to keep it secure
echo ".env" >> ../.gitignore
```

### Step 3: Verify Configuration

Run the environment check script:

```bash
cd /Users/jaideep.patel/Cursor/Formula1_Databricks/apps
./check_env.sh
```

You should see:
```
✅ DATABRICKS_HOST: e2-demo-field-eng.cloud.databricks.com
✅ DATABRICKS_TOKEN: SET (xxx characters)
✅ ENVIRONMENT READY
```

### Step 4: Start the App

```bash
cd /Users/jaideep.patel/Cursor/Formula1_Databricks/apps
streamlit run app.py
```

### Step 5: Test the Connection

1. The app should open in your browser
2. Look at the **sidebar** - you should see "🔑 Token Authentication (Local)"
3. Click **"🔍 Test Connection"** button
4. You should see: `✅ Connection successful! (Mode: token)`

## 🔍 If You Still Get Errors

### Error: "Invalid access token"
- Your token may have expired → Generate a new one
- Copy/paste error → Make sure you copied the full token

### Error: "SQL Warehouse may be stopped"
1. Go to Databricks workspace
2. Navigate to **SQL Warehouses**
3. Find your warehouse
4. Click **Start** if it's stopped
5. Wait for it to be "Running"

### Error: "Incorrect HTTP path"
1. Go to Databricks → **SQL Warehouses**
2. Click on your warehouse
3. Go to **Connection Details** tab
4. Copy the **HTTP Path**
5. Set it: `export DATABRICKS_HTTP_PATH='/your/actual/path'`

### Check Connection Settings in App
1. Open the app
2. In sidebar, expand **"🔧 Connection Settings"**
3. Verify:
   - Host is correct
   - Path is correct
   - Auth Mode shows "token"
   - Token length is shown

## 📋 Quick Copy-Paste Setup

Replace `YOUR_TOKEN_HERE` with your actual token:

```bash
export DATABRICKS_TOKEN='YOUR_TOKEN_HERE'
export DATABRICKS_HOST='e2-demo-field-eng.cloud.databricks.com'
export DATABRICKS_HTTP_PATH='/sql/1.0/warehouses/4b9b953939869799'
export F1_CATALOG='jai_patel_f1_data'
export F1_SCHEMA='racing_stats'

cd /Users/jaideep.patel/Cursor/Formula1_Databricks/apps
streamlit run app.py
```

## 🎯 Expected Result

When properly configured, you'll see in the app:

```
Sidebar:
  🔑 Token Authentication (Local)
  🔌 Connecting to: e2-demo-field-eng...

After clicking Test Connection:
  ✅ Connection successful! (Mode: token)
  ✅ silver_sessions: Exists
  ✅ silver_drivers: Exists
  ✅ gold_driver_performance: Exists
  ✅ gold_fastest_laps: Exists
```

## 📞 Still Having Issues?

Run the diagnostics and share the output:

```bash
cd /Users/jaideep.patel/Cursor/Formula1_Databricks/apps
./check_env.sh
```

Check the **Connection Details for Debugging** section in the app sidebar.

