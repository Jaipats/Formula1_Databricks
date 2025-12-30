# Databricks Genie Space for F1 Analytics

This guide explains how to create and use a Databricks Genie Space for natural language querying of your F1 racing data.

**⚠️ Important:** Create the Genie Space **AFTER** you have:
1. ✅ Run the DLT pipeline and created all tables
2. ✅ Verified your data is loaded (check table counts)
3. ✅ (Optional) Set up and tested the Streamlit Databricks App

This ensures Genie has access to all your F1 data for querying.

## 🤖 What is Databricks Genie?

Databricks Genie is an AI-powered conversational analytics tool that allows you to ask questions about your data in natural language. Instead of writing SQL queries, you can simply ask:

> "Show me the top 10 fastest laps from 2024"

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

# Run the script
cd deploy
./create_genie_space.py
```

### Option 2: Shell Script

```bash
# Set environment variables
export DATABRICKS_HOST='your-workspace.cloud.databricks.com'
export DATABRICKS_TOKEN='your-token'

# Run the script
cd deploy
./create_genie_space.sh
```

### Option 3: Databricks Notebook (Easiest)

1. Upload `notebooks/create_genie_space.py` to your Databricks workspace
2. Open the notebook
3. Run all cells
4. The notebook will:
   - Verify all tables exist
   - Create the Genie Space
   - Provide a link to access it

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
Show me the top 10 fastest laps from 2024
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

## 🐛 Troubleshooting

### Error: "Missing field serialized_space" (400 Bad Request)
- **Status:** ✅ Fixed in latest version
- **Solution:** Update to latest code from genie branch
- **Note:** API requires `serialized_space` wrapper around table list
- **Command:** `git pull origin genie`

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

