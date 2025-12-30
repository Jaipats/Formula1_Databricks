"""
Databricks App: Formula 1 Race Analytics
Interactive dashboard for Formula 1 race statistics and performance analysis
"""

import streamlit as st
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Databricks Configuration
# Set DATABRICKS_HOST for local development (Config looks for this variable)
if not os.getenv("DATABRICKS_HOST"):
    hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME", "e2-demo-field-eng.cloud.databricks.com")
    os.environ["DATABRICKS_HOST"] = hostname

# Initialize Databricks SDK Config
# Automatically detects credentials from environment variables or Databricks Apps context
cfg = Config()

# Unity Catalog Configuration
CATALOG = os.getenv("F1_CATALOG", "jai_patel_f1_data")
SCHEMA = os.getenv("F1_SCHEMA", "racing_stats")

# Query timeout in seconds
QUERY_TIMEOUT = 30

# Page config
st.set_page_config(
    page_title="F1 Race Analytics",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #E10600;
        text-align: center;
        padding: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_connection(http_path: str):
    """
    Create database connection using Databricks Apps authentication.
    Following the official tutorial: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-streamlit
    
    The Config object automatically handles authentication:
    - In Databricks Apps: Uses service principal (DATABRICKS_CLIENT_ID/SECRET)
    - Local development: Uses DATABRICKS_TOKEN
    """
    try:
        connection = sql.connect(
            server_hostname=cfg.host,
            http_path=http_path,
            credentials_provider=lambda: cfg.authenticate,
        )
        return connection
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ Failed to connect to Databricks: {error_msg}")
        
        # Provide helpful troubleshooting info
        if "Error during request to server" in error_msg or "INVALID_TOKEN" in error_msg:
            st.warning("⚠️ Connection Error - Possible causes:")
            st.markdown("""
            - **Invalid or expired credentials** - Generate a new personal access token
            - **SQL Warehouse stopped** - Ensure the warehouse is running
            - **Incorrect HTTP path** - Verify the SQL Warehouse path
            - **Missing environment variables** - Set DATABRICKS_HOST and DATABRICKS_TOKEN
            """)
            
            st.info("💡 **For Local Development:**")
            st.code("""
export DATABRICKS_HOST='your-workspace.cloud.databricks.com'
export DATABRICKS_TOKEN='dapi...'
export DATABRICKS_HTTP_PATH='/sql/1.0/warehouses/xxxxx'
            """)
        
        with st.expander("🔍 Connection Details for Debugging"):
            token_set = os.getenv('DATABRICKS_TOKEN')
            st.code(f"""
Hostname: {cfg.host if hasattr(cfg, 'host') else 'Not configured'}
HTTP Path: {http_path}

Environment Variables:
- DATABRICKS_HOST: {os.getenv('DATABRICKS_HOST', '❌ Not set')}
- DATABRICKS_HTTP_PATH: {os.getenv('DATABRICKS_HTTP_PATH', '❌ Not set')}
- DATABRICKS_TOKEN: {'✅ Set (' + str(len(token_set)) + ' chars)' if token_set else '❌ Not set'}
- DATABRICKS_CLIENT_ID: {'✅ Set' if os.getenv('DATABRICKS_CLIENT_ID') else '❌ Not set (App mode)'}

Error: {error_msg}
            """)
        return None


@st.cache_data(ttl=3600)
def run_query(query: str, timeout: int = QUERY_TIMEOUT) -> pd.DataFrame:
    """Execute SQL query and return results as DataFrame"""
    http_path = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/4b9b953939869799")
    conn = get_connection(http_path)
    if conn is None:
        return pd.DataFrame()
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=columns)
            return df
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ Query error: {error_msg}")
        
        # Provide helpful error messages
        if "does not exist" in error_msg or "TABLE_OR_VIEW_NOT_FOUND" in error_msg:
            st.warning("⚠️ Table doesn't exist. Run the Lakeflow pipeline to create tables.")
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            st.warning("⏱️ Query timeout. Try selecting a smaller date range or fewer records.")
        
        with st.expander("Show query for debugging"):
            st.code(query, language="sql")
        return pd.DataFrame()


def test_connection():
    """Test database connection and return status"""
    try:
        st.info("Step 1/3: Checking configuration...")
        
        # Get configuration values
        hostname = cfg.host if hasattr(cfg, 'host') else None
        http_path = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/4b9b953939869799")
        
        if not hostname:
            return False, "DATABRICKS_HOST not configured"
        
        st.info(f"Step 2/3: Connecting to {hostname[:40]}...")
        
        # Create connection using the standard method
        conn = sql.connect(
            server_hostname=cfg.host,
            http_path=http_path,
            credentials_provider=lambda: cfg.authenticate,
        )
        
        st.info("Step 3/3: Running test query...")
        
        # Try a simple query
        test_query = "SELECT 1 as test, current_user() as user"
        with conn.cursor() as cursor:
            cursor.execute(test_query)
            result = cursor.fetchone()
            if result and result[0] == 1:
                user = result[1] if len(result) > 1 else "unknown"
                return True, f"Connection successful! ✅ (User: {user})"
            return False, "Unexpected query result"
            
    except TimeoutError as e:
        return False, f"Connection timeout - server may be unreachable: {str(e)}"
    except Exception as e:
        error_msg = str(e)
        if "Invalid access token" in error_msg or "INVALID_TOKEN" in error_msg:
            return False, "Authentication failed - check DATABRICKS_TOKEN"
        elif "DATABRICKS_HOST" in error_msg:
            return False, "DATABRICKS_HOST not set in environment"
        elif "Warehouse" in error_msg or "does not exist" in error_msg:
            return False, f"SQL Warehouse issue - check HTTP path: {error_msg[:100]}"
        else:
            return False, f"Connection error: {error_msg[:150]}"


def check_tables_exist():
    """Check if required tables exist"""
    tables_to_check = [
        f"{CATALOG}.{SCHEMA}.silver_sessions",
        f"{CATALOG}.{SCHEMA}.silver_drivers",
        f"{CATALOG}.{SCHEMA}.gold_driver_performance",
        f"{CATALOG}.{SCHEMA}.gold_fastest_laps"
    ]
    
    results = {}
    for table in tables_to_check:
        try:
            query = f"SELECT COUNT(*) as cnt FROM {table} LIMIT 1"
            df = run_query(query, timeout=10)
            results[table] = "✅ Exists" if not df.empty else "❌ Empty"
        except Exception as e:
            results[table] = f"❌ Error: {str(e)[:50]}"
    
    return results


def get_sessions_for_filter(year: int):
    """Get available sessions for filtering"""
    sessions_query = f"""
    SELECT DISTINCT 
        session_key,
        session_name,
        location,
        date_start,
        session_type
    FROM {CATALOG}.{SCHEMA}.silver_sessions
    WHERE year = {year}
    ORDER BY date_start DESC
    """
    return run_query(sessions_query, timeout=15)


def main():
    """Main dashboard application"""
    
    # Header
    st.markdown('<div class="main-header">🏎️ Formula 1 Race Analytics</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("Dashboard Controls")
    st.sidebar.info(f"**Catalog:** {CATALOG}\n\n**Schema:** {SCHEMA}")
    
    # Show connection status
    with st.sidebar.expander("🔧 Connection Settings"):
        hostname = cfg.host if hasattr(cfg, 'host') else "Not configured"
        http_path = os.getenv('DATABRICKS_HTTP_PATH', 'Using default')
        token = os.getenv('DATABRICKS_TOKEN')
        client_id = os.getenv('DATABRICKS_CLIENT_ID')
        
        st.text(f"Host: {hostname[:40]}..." if len(hostname) > 40 else f"Host: {hostname}")
        st.text(f"Path: {http_path[:40]}..." if len(http_path) > 40 else f"Path: {http_path}")
        
        # Determine authentication mode
        if client_id:
            st.success("✅ App Mode (Service Principal)")
            st.text(f"Client ID: {client_id[:20]}...")
        elif token:
            st.info("✅ Local Dev Mode (Token)")
            st.text(f"Token: {len(token)} chars")
        else:
            st.warning("❌ No credentials found!")
            st.caption("Set DATABRICKS_HOST and DATABRICKS_TOKEN")
    
    # Connection test button
    col_test, col_clear = st.sidebar.columns([2, 1])
    with col_test:
        test_btn = st.button("🔍 Test Connection", use_container_width=True)
    with col_clear:
        clear_btn = st.button("🔄 Reset", use_container_width=True)
    
    if clear_btn:
        st.cache_resource.clear()
        st.cache_data.clear()
        st.sidebar.success("Cache cleared! Try testing again.")
    
    if test_btn:
        with st.sidebar:
            with st.spinner("Testing connection..."):
                success, message = test_connection()
                if success:
                    st.success(f"✅ {message}")
                    with st.expander("Check Tables"):
                        tables = check_tables_exist()
                        for table, status in tables.items():
                            st.text(f"{table.split('.')[-1]}: {status}")
                else:
                    st.error(f"❌ {message}")
                    st.info("💡 Try clicking 'Reset' to clear cache")
    
    st.sidebar.markdown("---")
    
    # Page selection
    page = st.sidebar.radio(
        "Select View",
        ["Overview", "Driver Performance", "Team Analysis", "Race Details", "Tire Strategy"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters")
    
    # Year selector under Filters
    selected_year = st.sidebar.selectbox(
        "Select Year",
        options=[2024, 2025],
        index=1  # Default to 2025
    )
    
    # Get sessions for filtering (except for Overview and Race Details which have their own logic)
    session_filter = None
    if page not in ["Overview", "Race Details"]:
        # For Tire Strategy, show only Race sessions
        if page == "Tire Strategy":
            sessions_query = f"""
            SELECT DISTINCT 
                session_key,
                session_name,
                location,
                date_start,
                session_type
            FROM {CATALOG}.{SCHEMA}.silver_sessions
            WHERE year = {selected_year} AND session_type = 'Race'
            ORDER BY date_start DESC
            """
            sessions_df = run_query(sessions_query, timeout=15)
            all_sessions_label = "All Race Sessions"
        else:
            sessions_df = get_sessions_for_filter(selected_year)
            all_sessions_label = "All Sessions"
        
        if not sessions_df.empty:
            session_options = [all_sessions_label] + [
                f"{row['location']} - {row['session_type']} ({row['date_start']})"
                for _, row in sessions_df.iterrows()
            ]
            selected_session = st.sidebar.selectbox("Select Session", session_options)
            if selected_session != all_sessions_label:
                session_idx = session_options.index(selected_session) - 1
                session_filter = sessions_df.iloc[session_idx]['session_key']
    
    if page == "Overview":
        show_overview(selected_year)
    elif page == "Driver Performance":
        show_driver_performance(selected_year, session_filter)
    elif page == "Team Analysis":
        show_team_analysis(selected_year, session_filter)
    elif page == "Race Details":
        show_race_details(selected_year)
    elif page == "Tire Strategy":
        show_tyre_strategy(selected_year, session_filter)


def show_overview(year: int = 2025):
    """Display overview dashboard"""
    st.header(f"📊 Season Overview - {year}")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Simplified query for metrics (no JOIN needed)
    metrics_query = f"""
    SELECT 
        COUNT(DISTINCT meeting_key) as total_races,
        COUNT(DISTINCT session_key) as total_sessions
    FROM {CATALOG}.{SCHEMA}.silver_sessions
    WHERE year = {year}
    """
    
    # Separate query for drivers to avoid expensive JOIN
    drivers_query = f"""
    SELECT COUNT(DISTINCT driver_number) as total_drivers
    FROM {CATALOG}.{SCHEMA}.silver_drivers d
    INNER JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON d.session_key = s.session_key
    WHERE s.year = {year}
    """
    
    with st.spinner("Loading metrics..."):
        metrics = run_query(metrics_query, timeout=15)
        drivers = run_query(drivers_query, timeout=15)
    
    if not metrics.empty:
        with col1:
            st.metric("Total Races", int(metrics['total_races'].iloc[0]) if metrics['total_races'].iloc[0] else 0)
        with col2:
            st.metric("Total Sessions", int(metrics['total_sessions'].iloc[0]) if metrics['total_sessions'].iloc[0] else 0)
        with col3:
            st.metric("Total Drivers", int(drivers['total_drivers'].iloc[0]) if not drivers.empty and drivers['total_drivers'].iloc[0] else 0)
        with col4:
            st.metric("Season", year)
    
    st.markdown("---")
    
    # Recent races with team information
    st.subheader("Recent Race Sessions")
    recent_races_query = f"""
    SELECT 
        s.session_name,
        s.location,
        s.country_name,
        s.date_start,
        s.session_type,
        COUNT(DISTINCT d.team_name) as teams_count,
        CONCAT_WS(', ', COLLECT_SET(d.team_name)) as teams
    FROM {CATALOG}.{SCHEMA}.silver_sessions s
    LEFT JOIN {CATALOG}.{SCHEMA}.silver_drivers d ON s.session_key = d.session_key
    WHERE s.year = {year}
    GROUP BY s.session_name, s.location, s.country_name, s.date_start, s.session_type
    ORDER BY s.date_start DESC
    LIMIT 10
    """
    
    with st.spinner("Loading recent races..."):
        recent_races = run_query(recent_races_query, timeout=20)
    
    if not recent_races.empty:
        st.dataframe(recent_races, use_container_width=True)
    else:
        st.info(f"No race data available for {year}")
    
    # Fastest laps chart
    st.subheader("Top 10 Fastest Laps")
    fastest_laps_query = f"""
    SELECT 
        full_name as driver,
        team_name,
        location,
        fastest_lap_time as lap_time
    FROM {CATALOG}.{SCHEMA}.gold_fastest_laps
    WHERE rank <= 10
    ORDER BY fastest_lap_time ASC
    LIMIT 10
    """
    
    with st.spinner("Loading fastest laps..."):
        fastest_laps = run_query(fastest_laps_query, timeout=15)
    
    if not fastest_laps.empty:
        fig = px.bar(
            fastest_laps,
            x='driver',
            y='lap_time',
            color='team_name',
            title=f'Fastest Lap Times - {year}',
            labels={'lap_time': 'Lap Time (seconds)', 'driver': 'Driver'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No fastest lap data available for {year}. The gold_fastest_laps table may not exist yet.")


def show_driver_performance(year: int = 2025, session_filter=None):
    """Display driver performance analysis"""
    st.header(f"🏁 Driver Performance Analysis - {year}")
    
    # Comparison mode toggle
    comparison_mode = st.checkbox("Compare Drivers", value=False)
    
    # Driver selector
    session_filter_clause = f"AND s.session_key = {session_filter}" if session_filter else ""
    drivers_query = f"""
    SELECT DISTINCT d.full_name, d.driver_number
    FROM {CATALOG}.{SCHEMA}.silver_drivers d
    INNER JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON d.session_key = s.session_key
    WHERE s.year = {year} {session_filter_clause}
    ORDER BY d.full_name
    """
    
    with st.spinner("Loading drivers..."):
        drivers_df = run_query(drivers_query, timeout=15)
    
    if drivers_df.empty:
        st.warning("No driver data available")
        return
    
    if comparison_mode:
        # Multi-select for comparison
        selected_drivers = st.multiselect(
            "Select Drivers to Compare (2-4 recommended)",
            drivers_df['full_name'].tolist(),
            default=drivers_df['full_name'].tolist()[:2] if len(drivers_df) >= 2 else drivers_df['full_name'].tolist()[:1]
        )
        if not selected_drivers:
            st.warning("Please select at least one driver")
            return
        driver_numbers = drivers_df[drivers_df['full_name'].isin(selected_drivers)]['driver_number'].tolist()
    else:
        # Single driver selection
        selected_driver = st.selectbox(
            "Select Driver",
            drivers_df['full_name'].tolist()
        )
        driver_numbers = [drivers_df[drivers_df['full_name'] == selected_driver]['driver_number'].iloc[0]]
        selected_drivers = [selected_driver]
    
    # Driver stats
    driver_numbers_str = ','.join(map(str, driver_numbers))
    stats_query = f"""
    SELECT 
        d.full_name as driver,
        d.team_name,
        COUNT(DISTINCT dp.session_key) as sessions_count,
        AVG(dp.fastest_lap_time) as avg_fastest_lap,
        MIN(dp.fastest_lap_time) as best_lap,
        AVG(dp.pit_stop_count) as avg_pit_stops,
        MAX(dp.max_speed_st) as top_speed
    FROM {CATALOG}.{SCHEMA}.gold_driver_performance dp
    INNER JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON dp.session_key = s.session_key
    INNER JOIN {CATALOG}.{SCHEMA}.silver_drivers d ON dp.driver_number = d.driver_number AND dp.session_key = d.session_key
    WHERE dp.driver_number IN ({driver_numbers_str}) AND s.year = {year} {session_filter_clause}
    GROUP BY d.full_name, d.team_name
    ORDER BY avg_fastest_lap
    """
    
    with st.spinner("Loading driver stats..."):
        stats = run_query(stats_query, timeout=15)
    
    if not stats.empty:
        if comparison_mode:
            # Show comparison table
            st.subheader("Driver Comparison")
            st.dataframe(stats, use_container_width=True)
            
            # Comparison charts
            col1, col2 = st.columns(2)
            with col1:
                fig1 = px.bar(stats, x='driver', y='avg_fastest_lap', color='team_name',
                             title='Average Fastest Lap Comparison',
                             labels={'avg_fastest_lap': 'Lap Time (s)'})
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                fig2 = px.bar(stats, x='driver', y='top_speed', color='team_name',
                             title='Top Speed Comparison',
                             labels={'top_speed': 'Speed (km/h)'})
                st.plotly_chart(fig2, use_container_width=True)
        else:
            # Show single driver metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Sessions", int(stats['sessions_count'].iloc[0]))
            with col2:
                st.metric("Avg Best Lap", f"{stats['avg_fastest_lap'].iloc[0]:.3f}s")
            with col3:
                st.metric("Fastest Lap", f"{stats['best_lap'].iloc[0]:.3f}s")
            with col4:
                st.metric("Avg Pit Stops", f"{stats['avg_pit_stops'].iloc[0]:.1f}")
            with col5:
                st.metric("Top Speed", f"{stats['top_speed'].iloc[0]:.0f} km/h")
    
    # Lap time progression
    st.subheader("Lap Time Progression")
    lap_progression_query = f"""
    SELECT 
        d.full_name as driver,
        s.location,
        s.date_start,
        dp.fastest_lap_time,
        dp.avg_lap_time
    FROM {CATALOG}.{SCHEMA}.gold_driver_performance dp
    JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON dp.session_key = s.session_key
    JOIN {CATALOG}.{SCHEMA}.silver_drivers d ON dp.driver_number = d.driver_number AND dp.session_key = d.session_key
    WHERE dp.driver_number IN ({driver_numbers_str}) AND s.year = {year} {session_filter_clause}
    ORDER BY s.date_start, d.full_name
    """
    
    with st.spinner("Loading lap progression..."):
        lap_progression = run_query(lap_progression_query, timeout=15)
    if not lap_progression.empty:
        if comparison_mode:
            # Show comparison of fastest laps
            fig = px.line(
                lap_progression,
                x='date_start',
                y='fastest_lap_time',
                color='driver',
                markers=True,
                title='Fastest Lap Time Comparison',
                labels={'fastest_lap_time': 'Lap Time (seconds)', 'date_start': 'Race Date'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Single driver view
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=lap_progression['date_start'],
                y=lap_progression['fastest_lap_time'],
                mode='lines+markers',
                name='Fastest Lap',
                line=dict(color='red')
            ))
            fig.add_trace(go.Scatter(
                x=lap_progression['date_start'],
                y=lap_progression['avg_lap_time'],
                mode='lines+markers',
                name='Average Lap',
                line=dict(color='blue')
            ))
            fig.update_layout(
                title=f"Lap Time Progression - {selected_drivers[0]}",
                xaxis_title="Race Date",
                yaxis_title="Lap Time (seconds)"
            )
            st.plotly_chart(fig, use_container_width=True)


def show_team_analysis(year: int = 2025, session_filter=None):
    """Display team performance analysis - Race sessions only"""
    st.header(f"🏆 Team Performance Analysis - {year} (Race Sessions Only)")
    
    # Build session filter - only Race sessions
    session_filter_clause = f"AND s.session_key = {session_filter}" if session_filter else "AND s.session_type = 'Race'"
    
    # Team comparison with corrected pit stop calculation
    team_query = f"""
    SELECT 
        d.team_name,
        COUNT(DISTINCT s.session_key) as race_count,
        AVG(dp.fastest_lap_time) as avg_fastest_lap,
        MIN(dp.fastest_lap_time) as best_lap,
        AVG(dp.max_speed_st) as avg_max_speed,
        MAX(dp.max_speed_st) as top_speed,
        AVG(dp.pit_stop_count) as avg_pit_stops
    FROM {CATALOG}.{SCHEMA}.gold_driver_performance dp
    INNER JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON dp.session_key = s.session_key
    INNER JOIN {CATALOG}.{SCHEMA}.silver_drivers d ON dp.driver_number = d.driver_number AND dp.session_key = d.session_key
    WHERE s.year = {year} {session_filter_clause}
    GROUP BY d.team_name
    ORDER BY avg_fastest_lap
    """
    
    # Separate query for pit stop duration from pit data
    pit_query = f"""
    SELECT 
        d.team_name,
        AVG(p.pit_duration) as avg_pit_duration,
        MIN(p.pit_duration) as fastest_pit_stop,
        COUNT(*) as total_pit_stops
    FROM {CATALOG}.{SCHEMA}.silver_pit p
    INNER JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON p.session_key = s.session_key
    INNER JOIN {CATALOG}.{SCHEMA}.silver_drivers d ON p.driver_number = d.driver_number AND p.session_key = d.session_key
    WHERE s.year = {year} {session_filter_clause}
    GROUP BY d.team_name
    """
    
    with st.spinner("Loading team data..."):
        team_data = run_query(team_query, timeout=20)
        pit_data = run_query(pit_query, timeout=20)
    
    if not team_data.empty:
        # Merge pit stop data if available
        if not pit_data.empty:
            team_data = pd.merge(team_data, pit_data, on='team_name', how='left')
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Teams", len(team_data))
        with col2:
            best_team = team_data.loc[team_data['avg_fastest_lap'].idxmin(), 'team_name']
            st.metric("Fastest Team (Avg)", best_team)
        with col3:
            if 'avg_pit_duration' in team_data.columns:
                fastest_pit_team = team_data.loc[team_data['avg_pit_duration'].idxmin(), 'team_name']
                st.metric("Fastest Pit Stops", fastest_pit_team)
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.bar(
                team_data,
                x='team_name',
                y='avg_fastest_lap',
                title='Average Fastest Lap by Team (Race Only)',
                labels={'avg_fastest_lap': 'Lap Time (seconds)', 'team_name': 'Team'},
                color='avg_fastest_lap',
                color_continuous_scale='RdYlGn_r'
            )
            fig1.update_xaxes(tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            if 'avg_pit_duration' in team_data.columns:
                fig2 = px.bar(
                    team_data,
                    x='team_name',
                    y='avg_pit_duration',
                    title='Average Pit Stop Duration by Team',
                    labels={'avg_pit_duration': 'Duration (seconds)', 'team_name': 'Team'},
                    color='avg_pit_duration',
                    color_continuous_scale='RdYlGn_r'
                )
                fig2.update_xaxes(tickangle=-45)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No pit stop data available")
        
        # Speed comparison
        st.subheader("Team Speed Analysis")
        fig3 = px.scatter(
            team_data,
            x='avg_max_speed',
            y='avg_fastest_lap',
            size='race_count',
            color='team_name',
            hover_data=['team_name', 'race_count'],
            title='Speed vs Lap Time (Race Sessions)',
            labels={'avg_max_speed': 'Avg Max Speed (km/h)', 'avg_fastest_lap': 'Avg Fastest Lap (s)'}
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        # Team data table
        st.subheader("Team Statistics")
        st.dataframe(team_data, use_container_width=True)
    else:
        st.info(f"No team performance data available for {year} Race sessions. The pipeline may not have processed this data yet.")


def show_race_details(year: int = 2025):
    """Display detailed race information with enhanced statistics"""
    st.header(f"🏁 Race Details - {year}")
    
    # Get list of races
    races_query = f"""
    SELECT DISTINCT 
        session_key,
        session_name,
        location,
        date_start,
        session_type
    FROM {CATALOG}.{SCHEMA}.silver_sessions
    WHERE session_type IN ('Race', 'Sprint') AND year = {year}
    ORDER BY date_start DESC
    """
    
    with st.spinner("Loading races..."):
        races = run_query(races_query, timeout=15)
    
    if races.empty:
        st.warning("No race data available")
        return
    
    selected_race = st.selectbox(
        "Select Race",
        races.apply(lambda x: f"{x['location']} - {x['session_type']} ({x['date_start']})", axis=1).tolist()
    )
    
    race_idx = races.apply(lambda x: f"{x['location']} - {x['session_type']} ({x['date_start']})", axis=1).tolist().index(selected_race)
    session_key = races.iloc[race_idx]['session_key']
    location = races.iloc[race_idx]['location']
    
    # Enhanced Race Summary Metrics
    st.subheader("📊 Race Overview")
    
    # Get driver performance stats
    driver_stats_query = f"""
    SELECT 
        COUNT(DISTINCT dp.driver_number) as total_drivers,
        AVG(dp.fastest_lap_time) as avg_fastest_lap,
        MIN(dp.fastest_lap_time) as fastest_lap,
        MAX(dp.max_speed_st) as top_speed,
        AVG(dp.max_speed_st) as avg_speed,
        SUM(dp.pit_stop_count) as total_pit_stops
    FROM {CATALOG}.{SCHEMA}.gold_driver_performance dp
    WHERE dp.session_key = {session_key}
    """
    
    driver_stats = run_query(driver_stats_query, timeout=15)
    
    if not driver_stats.empty and driver_stats['total_drivers'].iloc[0]:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Drivers", int(driver_stats['total_drivers'].iloc[0]))
        with col2:
            st.metric("Fastest Lap", f"{driver_stats['fastest_lap'].iloc[0]:.3f}s")
        with col3:
            st.metric("Avg Lap Time", f"{driver_stats['avg_fastest_lap'].iloc[0]:.3f}s")
        with col4:
            st.metric("Top Speed", f"{driver_stats['top_speed'].iloc[0]:.0f} km/h")
        with col5:
            st.metric("Total Pit Stops", int(driver_stats['total_pit_stops'].iloc[0]))
    
    st.markdown("---")
    
    # Driver Performance Table
    st.subheader("🏁 Driver Performance")
    performance_query = f"""
    SELECT 
        d.full_name as Driver,
        d.team_name as Team,
        dp.fastest_lap_time as fastest_lap,
        dp.avg_lap_time,
        dp.max_speed_st as max_speed,
        dp.pit_stop_count
    FROM {CATALOG}.{SCHEMA}.gold_driver_performance dp
    JOIN {CATALOG}.{SCHEMA}.silver_drivers d 
        ON dp.driver_number = d.driver_number AND dp.session_key = d.session_key
    WHERE dp.session_key = {session_key}
    ORDER BY dp.fastest_lap_time
    """
    
    performance_data = run_query(performance_query, timeout=15)
    if not performance_data.empty:
        st.dataframe(performance_data, use_container_width=True)
        
        # Performance charts
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(
                performance_data.head(10),
                x='Driver',
                y='fastest_lap',
                color='Team',
                title='Top 10 Fastest Laps',
                labels={'fastest_lap': 'Lap Time (s)'}
            )
            fig1.update_xaxes(tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.bar(
                performance_data,
                x='Driver',
                y='max_speed',
                color='Team',
                title='Maximum Speed by Driver',
                labels={'max_speed': 'Speed (km/h)'}
            )
            fig2.update_xaxes(tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
    
    # Pit Stop Analysis
    st.subheader("🔧 Pit Stop Analysis")
    pit_stops_query = f"""
    SELECT 
        d.full_name as driver,
        d.team_name,
        p.lap_number,
        p.pit_duration,
        p.date as pit_time
    FROM {CATALOG}.{SCHEMA}.silver_pit p
    JOIN {CATALOG}.{SCHEMA}.silver_drivers d 
        ON p.driver_number = d.driver_number AND p.session_key = d.session_key
    WHERE p.session_key = {session_key}
    ORDER BY p.lap_number
    """
    
    pit_stops = run_query(pit_stops_query, timeout=15)
    if not pit_stops.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Pit stop duration by driver
            pit_summary = pit_stops.groupby(['driver', 'team_name'])['pit_duration'].mean().reset_index()
            fig3 = px.bar(
                pit_summary,
                x='driver',
                y='pit_duration',
                color='team_name',
                title='Average Pit Stop Duration',
                labels={'pit_duration': 'Duration (s)'}
            )
            fig3.update_xaxes(tickangle=-45)
            st.plotly_chart(fig3, use_container_width=True)
        
        with col2:
            # Pit stops over time
            fig4 = px.scatter(
                pit_stops,
                x='lap_number',
                y='pit_duration',
                color='team_name',
                hover_data=['driver'],
                title='Pit Stop Duration by Lap',
                labels={'lap_number': 'Lap Number', 'pit_duration': 'Duration (s)'}
            )
            st.plotly_chart(fig4, use_container_width=True)
        
        # Pit stop details table
        with st.expander("View Detailed Pit Stop Data"):
            st.dataframe(pit_stops, use_container_width=True)
    else:
        st.info("No pit stop data available for this race")
    
    # Position chart
    st.subheader("📈 Position Changes Throughout Race")
    position_query = f"""
    SELECT 
        d.full_name as driver,
        d.team_name,
        p.date,
        p.position
    FROM {CATALOG}.{SCHEMA}.silver_position p
    JOIN {CATALOG}.{SCHEMA}.silver_drivers d 
        ON p.session_key = d.session_key AND p.driver_number = d.driver_number
    WHERE p.session_key = {session_key}
    ORDER BY p.date, p.position
    """
    
    position_data = run_query(position_query, timeout=20)
    if not position_data.empty:
        fig5 = px.line(
            position_data,
            x='date',
            y='position',
            color='driver',
            title=f'Position Changes - {location}',
            labels={'position': 'Position', 'date': 'Time'},
            hover_data=['team_name']
        )
        fig5.update_yaxis(autorange="reversed")  # Position 1 at top
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("No position data available for this race")
    
    # Team Comparison
    st.subheader("🏆 Team Comparison")
    team_comparison_query = f"""
    SELECT 
        d.team_name,
        COUNT(DISTINCT d.driver_number) as drivers,
        AVG(dp.fastest_lap_time) as avg_lap,
        MIN(dp.fastest_lap_time) as best_lap,
        AVG(dp.max_speed_st) as avg_speed,
        SUM(dp.pit_stop_count) as total_pits
    FROM {CATALOG}.{SCHEMA}.gold_driver_performance dp
    JOIN {CATALOG}.{SCHEMA}.silver_drivers d 
        ON dp.driver_number = d.driver_number AND dp.session_key = d.session_key
    WHERE dp.session_key = {session_key}
    GROUP BY d.team_name
    ORDER BY avg_lap
    """
    
    team_comp = run_query(team_comparison_query, timeout=15)
    if not team_comp.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig6 = px.bar(
                team_comp,
                x='team_name',
                y='avg_lap',
                title='Average Lap Time by Team',
                labels={'avg_lap': 'Avg Lap Time (s)', 'team_name': 'Team'},
                color='avg_lap',
                color_continuous_scale='RdYlGn_r'
            )
            fig6.update_xaxes(tickangle=-45)
            st.plotly_chart(fig6, use_container_width=True)
        
        with col2:
            st.dataframe(team_comp, use_container_width=True)


def show_tyre_strategy(year: int = 2025, session_filter=None):
    """Display tire strategy analysis with team filtering"""
    st.header(f"🔧 Tire Strategy Analysis - {year} (Race Sessions)")
    
    # Build session filter clause - use sidebar filter or default to all Race sessions
    session_filter_clause = f"AND s.session_key = {session_filter}" if session_filter else "AND s.session_type = 'Race'"
    
    # Get available teams
    teams_query = f"""
    SELECT DISTINCT d.team_name
    FROM {CATALOG}.{SCHEMA}.silver_drivers d
    INNER JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON d.session_key = s.session_key
    WHERE s.year = {year} {session_filter_clause}
    ORDER BY d.team_name
    """
    
    with st.spinner("Loading teams..."):
        teams_df = run_query(teams_query, timeout=15)
    
    # Team multiselect filter
    selected_teams = []
    if not teams_df.empty:
        selected_teams = st.multiselect(
            "Select Teams (leave empty for all teams)",
            teams_df['team_name'].tolist(),
            default=[]
        )
    
    # Build team filter clause
    team_filter_clause = ""
    if selected_teams:
        team_list = "', '".join(selected_teams)
        team_filter_clause = f"AND d.team_name IN ('{team_list}')"
    
    # Tyre compound performance by team
    tyre_query = f"""
    SELECT 
        ts.compound,
        d.team_name,
        AVG(ts.avg_lap_time_on_compound) as avg_lap_time,
        AVG(ts.stint_laps) as avg_stint_length,
        COUNT(*) as usage_count
    FROM {CATALOG}.{SCHEMA}.gold_tyre_strategy ts
    INNER JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON ts.session_key = s.session_key
    INNER JOIN {CATALOG}.{SCHEMA}.silver_drivers d ON ts.driver_number = d.driver_number AND ts.session_key = d.session_key
    WHERE s.year = {year} {session_filter_clause} {team_filter_clause}
    GROUP BY ts.compound, d.team_name
    ORDER BY ts.compound, avg_lap_time
    """
    
    # Overall compound performance
    compound_summary_query = f"""
    SELECT 
        ts.compound,
        AVG(ts.avg_lap_time_on_compound) as avg_lap_time,
        AVG(ts.stint_laps) as avg_stint_length,
        COUNT(*) as usage_count,
        COUNT(DISTINCT d.team_name) as teams_used
    FROM {CATALOG}.{SCHEMA}.gold_tyre_strategy ts
    INNER JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON ts.session_key = s.session_key
    INNER JOIN {CATALOG}.{SCHEMA}.silver_drivers d ON ts.driver_number = d.driver_number AND ts.session_key = d.session_key
    WHERE s.year = {year} {session_filter_clause} {team_filter_clause}
    GROUP BY ts.compound
    ORDER BY avg_lap_time
    """
    
    with st.spinner("Loading tire data..."):
        tyre_data = run_query(tyre_query, timeout=20)
        compound_summary = run_query(compound_summary_query, timeout=20)
    
    if not compound_summary.empty:
        # Overall compound statistics
        st.subheader("📊 Compound Performance Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig1 = px.bar(
                compound_summary,
                x='compound',
                y='avg_lap_time',
                title='Average Lap Time by Compound',
                labels={'avg_lap_time': 'Lap Time (seconds)', 'compound': 'Tire Compound'},
                color='avg_lap_time',
                color_continuous_scale='RdYlGn_r'
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.pie(
                compound_summary,
                values='usage_count',
                names='compound',
                title='Tire Compound Usage Distribution'
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        with col3:
            fig3 = px.bar(
                compound_summary,
                x='compound',
                y='avg_stint_length',
                title='Average Stint Length by Compound',
                labels={'avg_stint_length': 'Stint Length (laps)', 'compound': 'Compound'},
                color='avg_stint_length',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        # Summary table
        st.dataframe(compound_summary, use_container_width=True)
        
        # Team-specific analysis if data available
        if not tyre_data.empty and len(tyre_data['team_name'].unique()) > 0:
            st.markdown("---")
            st.subheader("🏎️ Team-Specific Tire Performance")
            
            # Compound performance by team
            fig4 = px.bar(
                tyre_data,
                x='compound',
                y='avg_lap_time',
                color='team_name',
                barmode='group',
                title='Lap Time by Compound and Team',
                labels={'avg_lap_time': 'Avg Lap Time (s)', 'compound': 'Compound'}
            )
            st.plotly_chart(fig4, use_container_width=True)
            
            # Stint length comparison
            fig5 = px.box(
                tyre_data,
                x='compound',
                y='avg_stint_length',
                color='team_name',
                title='Stint Length Distribution by Compound',
                labels={'avg_stint_length': 'Stint Length (laps)', 'compound': 'Compound'}
            )
            st.plotly_chart(fig5, use_container_width=True)
            
            # Usage heatmap
            usage_pivot = tyre_data.pivot_table(
                values='usage_count',
                index='team_name',
                columns='compound',
                aggfunc='sum',
                fill_value=0
            )
            
            if not usage_pivot.empty:
                fig6 = px.imshow(
                    usage_pivot,
                    title='Tire Compound Usage by Team (Heatmap)',
                    labels=dict(x='Compound', y='Team', color='Usage Count'),
                    aspect='auto',
                    color_continuous_scale='YlOrRd'
                )
                st.plotly_chart(fig6, use_container_width=True)
            
            # Detailed data table
            with st.expander("View Detailed Tire Strategy Data"):
                st.dataframe(tyre_data, use_container_width=True)
    else:
        st.info(f"No tire strategy data available for {year}. The pipeline may not have processed this data yet.")


if __name__ == "__main__":
    main()

