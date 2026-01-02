# Databricks Genie Space for F1 Analytics

This guide explains how to create and use a Databricks Genie Space for natural language querying of your F1 racing data.

**⚠️ Important:** Create the Genie Space **AFTER** you have:
1. ✅ Run the DLT pipeline and created all tables
2. ✅ Verified your data is loaded (check table counts)
3. ✅ (Optional) Set up and tested the Streamlit Databricks App

This ensures Genie has access to all your F1 data for querying.

## 🤖 What is Databricks Genie?

Databricks Genie is an AI-powered conversational analytics tool that allows you to ask questions about your data in natural language. Instead of writing SQL queries, you can simply ask:

> "Show me the top 10 fastest laps from 2025"

And Genie will automatically:
1. Understand your question
2. Query the relevant tables
3. Generate appropriate visualizations
4. Provide insights and follow-up suggestions

## 📊 What's Included

The F1 Analytics Genie Space includes **19 tables** covering comprehensive Formula 1 data:

### Silver Tables (13 tables - Core Data)
- `silver_meetings` - Race weekends and events
- `silver_sessions` - Practice, Qualifying, and Race sessions
- `silver_drivers` - Driver information per session
- `silver_laps` - Detailed lap times and telemetry
- `silver_pit` - Pit stop data and durations
- `silver_stints` - Tire stint information
- `silver_weather` - Track and weather conditions
- `silver_race_control` - Flags, safety car, and race control messages
- `silver_team_radio` - Team radio communications
- `silver_intervals` - Time gaps between drivers
- `silver_overtakes` - Overtaking events
- `silver_session_result` - Final session results
- `silver_starting_grid` - Starting grid positions

### Gold Tables (6 tables - Aggregated Analytics)
- `gold_driver_performance` - Driver statistics per session
- `gold_race_summary` - Race summary metrics and highlights
- `gold_team_performance` - Team performance aggregations
- `gold_tyre_strategy` - Tire strategy analysis
- `gold_fastest_laps` - Fastest laps ranking
- `gold_overtakes_analysis` - Overtaking statistics

## 🚀 How to Create the Genie Space

You have **three options** to create the Genie Space:

### Option 1: Python Script (Recommended for Local)

```bash
# Set environment variables
export DATABRICKS_HOST='your-workspace.cloud.databricks.com'
export DATABRICKS_TOKEN='your-token'
export DATABRICKS_WAREHOUSE_ID='your-warehouse-id'

# Run the script
cd deploy
./create_genie_space.py
```

### Option 2: Shell Script

```bash
# Set environment variables
export DATABRICKS_HOST='your-workspace.cloud.databricks.com'
export DATABRICKS_TOKEN='your-token'
export DATABRICKS_WAREHOUSE_ID='your-warehouse-id'

# Run the script
cd deploy
./create_genie_space.sh
```

### Option 3: Databricks Notebook (Easiest)

1. Upload `notebooks/create_genie_space.py` to your Databricks workspace
2. Open the notebook
3. Update `WAREHOUSE_ID` variable (~line 34) with your SQL Warehouse ID
4. Run all cells
5. The notebook will:
   - Verify all tables exist
   - Create the Genie Space
   - Provide a link to access it

**📍 How to get your Warehouse ID:**
1. Go to Databricks → **SQL Warehouses**
2. Click on your warehouse
3. Copy the ID from the URL: `/sql/warehouses/<warehouse-id>`
   - Example: `4b9b953939869799`

## 📝 Prerequisites

**⚙️ Workflow Order:**
1. First: Complete Steps 1-5 from QUICK_START.md (set up data pipeline)
2. Second (Optional): Set up Streamlit Databricks App (apps/app.py)
3. Third: Create Genie Space (this guide) ← **You are here**

**📋 Before creating the Genie Space:**

1. **Run DLT Pipeline** - Ensure all silver and gold tables are created
   ```bash
   cd deploy
   ./run_pipeline.sh
   ```

2. **Verify Tables Exist** - Check that tables are populated with data
   ```sql
   -- Should return row counts
   SELECT COUNT(*) FROM jai_patel_f1_data.racing_stats.silver_sessions;
   SELECT COUNT(*) FROM jai_patel_f1_data.racing_stats.gold_driver_performance;
   ```

3. **Genie Enabled** - Ensure Genie is enabled in your Databricks workspace
   - Contact your workspace admin if needed
   - Genie is available in most Databricks workspaces on AWS, Azure, and GCP

4. **Permissions** - You need permission to create Genie spaces
   - Typically requires workspace user or admin role

5. **Access Token** - Have your personal access token ready
   - Go to: User Settings → Developer → Access Tokens → Generate New Token

## 💬 Example Questions to Ask Genie

Once your Genie Space is created, try these questions:

### 🏎️ Driver Performance
```
Show me the top 10 fastest laps from 2025
What is Lewis Hamilton's average lap time this season?
Which driver has the most pole positions?
Compare Max Verstappen and Charles Leclerc lap times
Who had the fastest lap in the Monaco Grand Prix?
```

### 🏁 Team Analysis
```
Compare Red Bull and Mercedes pit stop performance
Which team has the fastest average pit stop?
Show me team performance by race
What's the average lap time difference between teams?
Which team uses soft tires most effectively?
```

### 🌟 Race Events
```
What was the weather like during the Monaco Grand Prix?
How many overtakes happened in the last race?
Which races had safety car periods?
Show me all race control messages for the last race
What was the longest pit stop this season?
```

### 🔧 Tire Strategy
```
What tire compounds were used most in 2024?
Compare soft vs hard tire performance
Which team has the best tire strategy?
Show me average stint length by compound
Which driver had the most tire changes?
```

### 📊 Historical Analysis
```
Show me the fastest lap progression throughout the season
Which circuits have the most overtakes?
What's the correlation between starting position and final position?
Track lap time improvements over the season
Show me weather impact on lap times
```

## 🎯 Tips for Better Questions

1. **Be Specific**
   - ✅ "Show fastest laps for Lewis Hamilton in 2024 Monaco GP"
   - ❌ "Show me laps"

2. **Use Comparisons**
   - ✅ "Compare Red Bull vs Mercedes pit stop times"
   - ✅ "Which is faster: soft or medium tires?"

3. **Specify Time Ranges**
   - ✅ "Show 2024 season driver performance"
   - ✅ "Analyze the last 3 races"

4. **Ask Follow-ups**
   - Genie remembers context
   - You can ask "Show me the same for Ferrari" after a Red Bull query

5. **Request Visualizations**
   - "Create a chart of..."
   - "Visualize the trend..."

## 🔧 API Reference

The Genie Space is created using the Databricks REST API:

**Endpoint:** `POST /api/2.0/genie/spaces`

**Documentation:** https://docs.databricks.com/api/workspace/genie/createspace

**Request Body:**
```json
{
  "display_name": "F1 Race Analytics",
  "description": "Formula 1 racing analytics space...",
  "table_full_names": [
    "jai_patel_f1_data.racing_stats.silver_sessions",
    "jai_patel_f1_data.racing_stats.gold_driver_performance",
    ...
  ]
}
```

**Response:**
```json
{
  "space_id": "01234567-89ab-cdef-0123-456789abcdef"
}
```

## 🌐 Accessing Your Genie Space

After creation, access your space at:

```
https://your-workspace.cloud.databricks.com/genie/spaces/{space_id}
```

The creation scripts will provide the direct link.

## 🤖 Integrate AI Chatbot with Streamlit App

You can add an interactive AI chatbot to your Streamlit Databricks App powered by the Genie Space!

### Step 1: Get Your Genie Space ID

Run the helper script to find your Space ID:

```bash
python deploy/get_genie_space_id.py
```

This will list all Genie spaces and identify your F1 Analytics space.

**Example output:**
```
✅ Found F1 Analytics Genie Space!
======================================================================

Space ID: a1b2c3d4e5f6789012345678901234ab

📝 To enable the AI Chatbot in your Streamlit app:

Option 1: Set environment variable (for local development)
   export GENIE_SPACE_ID='a1b2c3d4e5f6789012345678901234ab'

Option 2: Update app.yaml (for Databricks Apps)
   ...
```

### Step 2: Configure the App

#### For Local Development:

```bash
export GENIE_SPACE_ID='your-space-id-here'
streamlit run apps/app.py
```

#### For Databricks Apps:

Edit `apps/app.yaml` and add the environment variable:

```yaml
env:
  - name: "DATABRICKS_WAREHOUSE_ID"
    valueFrom: "sql-warehouse"
  - name: STREAMLIT_BROWSER_GATHER_USAGE_STATS
    value: "false"
  - name: GENIE_SPACE_ID
    value: "your-genie-space-id-here"  # Replace with your actual Space ID
```

### Step 3: Deploy the Updated App

```bash
# Databricks Apps will automatically pick up the new environment variable
# Just redeploy your app or restart it
```

### Step 4: Use the AI Chatbot

1. Open your Streamlit app
2. Select **"🤖 AI Chatbot"** from the sidebar
3. Ask questions in natural language!

**Features:**
- ✨ Natural language queries
- 📊 Automatic SQL generation
- 📈 Visual results and data tables
- 💬 Conversation history
- 🔄 Follow-up questions with context
- 💡 Sample questions to get started

**Example interaction:**
```
You: "Show me the top 10 fastest laps from 2025"

AI: Here are the top 10 fastest laps from 2025:
    [displays table with driver, lap time, session, etc.]
    
    The fastest lap was achieved by Max Verstappen with a time of 1:10.234
    at the Monaco Grand Prix.
```

### API Reference

The chatbot uses the [Databricks Genie Conversation API](https://docs.databricks.com/gcp/en/genie/conversation-api):

- **Start Conversation**: `w.genie.start_conversation_and_wait(space_id, content)`
- **Continue Conversation**: `w.genie.execute_message_query_and_wait(space_id, conversation_id, content)`
- **List Spaces**: `w.genie.list_spaces()`

**Authentication**: Uses the same Databricks SDK authentication as the rest of the app (OAuth 2.0 for Databricks Apps).

## 🐛 Troubleshooting

### Error: "ExportConverter only supports version 1, but got 0" (400 Bad Request)
- **Status:** ✅ Fixed in latest version
- **Solution:** Update to latest code from genie branch
- **Note:** The `serialized_space` must include `"version": 1` field
- **Command:** `git pull origin genie`
- **Technical:** See proper structure below

### Error: "Missing field warehouse_id" (400 Bad Request)
- **Status:** ✅ Fixed in latest version
- **Solution:** Set `DATABRICKS_WAREHOUSE_ID` environment variable
- **Command:** `export DATABRICKS_WAREHOUSE_ID='your-warehouse-id'`
- **How to find:** SQL Warehouses → Your Warehouse → Copy ID from URL

### Error: "Missing field serialized_space" or "Expected Scalar value" (400 Bad Request)
- **Status:** ✅ Fixed in latest version
- **Solution:** Update to latest code from genie branch
- **Note:** API requires `serialized_space` as a **JSON string** with proper structure
- **Command:** `git pull origin genie`
- **Technical:** See proper structure below

### Error: "data_sources.tables must be sorted by identifier" (400 Bad Request)
- **Status:** ✅ Fixed in latest version
- **Solution:** Update to latest code from genie branch
- **Note:** Table identifiers must be in alphabetical order
- **Command:** `git pull origin genie`
- **Technical:** Use `all_tables.sort()` in Python or `jq 'sort'` in shell before creating space_config

### Error: "Invalid id for sample_question.id" - Expected lowercase 32-hex UUID (400 Bad Request)
- **Status:** ✅ Fixed in latest version
- **Solution:** Update to latest code from genie branch
- **Note:** Sample question IDs must be lowercase 32-character hex UUIDs without hyphens
- **Command:** `git pull origin genie`
- **Technical:** Python: `str(uuid.uuid4()).replace('-', '')`, Shell: `uuidgen | tr '[:upper:]' '[:lower:]' | tr -d '-'`

### ✅ Correct `serialized_space` Structure
The `serialized_space` field must be a **compact JSON string** (no spaces) with this exact structure:

```json
{
  "version": 1,
  "config": {
    "sample_questions": [
      {
        "id": "q1",
        "question": ["Your sample question here"]
      }
    ]
  },
  "data_sources": {
    "tables": [
      {"identifier": "catalog.schema.table_name"}
    ]
  }
}
```

**Key Requirements:**
- Must be serialized as a **compact JSON string** (no spaces after colons/commas)
- Python: `json.dumps(space_config, separators=(',', ':'))`
- Shell/jq: `jq -nc` (compact output flag)
- `version` must be `1`
- Tables go in `data_sources.tables` as objects with `identifier` key
- **Tables must be sorted alphabetically by identifier** (use `sort()` in Python, `jq 'sort'` in shell)
- Sample questions are optional but recommended in `config.sample_questions`
- **Sample question IDs must be lowercase 32-hex UUIDs without hyphens** (e.g., `a1b2c3d4e5f6789012345678901234ab`)

**Example compact format:**
```
{"version":1,"config":{"sample_questions":[{"id":"a1b2c3d4e5f6789012345678901234ab","question":[...]}]},"data_sources":{"tables":[...]}}
```

### Error: "Tables do not exist"
- **Solution:** Run the DLT pipeline first to create tables
- **Command:** `cd deploy && ./run_pipeline.sh`
- **Verify:** `SELECT COUNT(*) FROM catalog.schema.silver_sessions;`

### Error: "Genie not available"
- **Solution:** Genie may not be enabled in your workspace
- **Action:** Contact your Databricks workspace admin

### Error: "Permission denied"
- **Solution:** You need permission to create Genie spaces
- **Action:** Request workspace admin or contributor role

### Error: "Authentication failed"
- **Solution:** Check your DATABRICKS_TOKEN is valid
- **Action:** Generate a new token from User Settings → Access Tokens

### Questions not working well
- **Solution:** Ensure tables have data (run DLT pipeline)
- **Tip:** Be more specific in your questions
- **Tip:** Check table schemas match expected format

## 📚 Additional Resources

- [Databricks Genie Documentation](https://docs.databricks.com/genie/)
- [Genie API Reference](https://docs.databricks.com/api/workspace/genie/)
- [Natural Language Queries Best Practices](https://docs.databricks.com/genie/best-practices.html)

## 🎉 What's Next?

After creating your Genie Space:

1. ✅ Explore with example questions
2. 📊 Create custom dashboards from Genie results
3. 🔗 Share insights with your team
4. 🤖 Let Genie learn from your questions over time
5. 📈 Monitor which questions provide the most value

**Happy querying!** 🏎️💨

