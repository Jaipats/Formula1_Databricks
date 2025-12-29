"""
Databricks App: Formula 1 Race Analytics
Interactive dashboard for Formula 1 race statistics and performance analysis
"""

import streamlit as st
import pandas as pd
from databricks import sql
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuration - Update these with your Databricks settings
DATABRICKS_SERVER_HOSTNAME = os.getenv("DATABRICKS_SERVER_HOSTNAME", "e2-demo-field-eng.cloud.databricks.com")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/4b9b953939869799")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")  # Set via environment variable

# Unity Catalog Configuration - Make this configurable
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
def get_connection():
    """Create database connection with timeout"""
    try:
        # Check if token is set
        if not DATABRICKS_TOKEN:
            st.error("⚠️ DATABRICKS_TOKEN environment variable is not set!")
            st.info("Set it with: export DATABRICKS_TOKEN='your-token-here'")
            return None
        
        # Add timeout to connection - prevents hanging forever
        connection = sql.connect(
            server_hostname=DATABRICKS_SERVER_HOSTNAME,
            http_path=DATABRICKS_HTTP_PATH,
            access_token=DATABRICKS_TOKEN,
            _socket_timeout=15  # 15 second connection timeout
        )
        
        return connection
    except Exception as e:
        st.error(f"❌ Failed to connect to Databricks: {str(e)}")
        st.warning("Check your connection settings and token")
        with st.expander("Connection Details"):
            st.code(f"""
Hostname: {DATABRICKS_SERVER_HOSTNAME}
HTTP Path: {DATABRICKS_HTTP_PATH}
Token: {'Set' if DATABRICKS_TOKEN else 'NOT SET'}
            """)
        return None


@st.cache_data(ttl=3600)
def run_query(query: str, timeout: int = QUERY_TIMEOUT) -> pd.DataFrame:
    """Execute SQL query and return results as DataFrame"""
    conn = get_connection()
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
        # Check prerequisites first
        if not DATABRICKS_TOKEN:
            return False, "DATABRICKS_TOKEN not set in environment"
        
        st.info("Step 1/3: Checking token...")
        st.info("Step 2/3: Establishing connection...")
        
        # Create a fresh connection (not cached) for testing
        conn = sql.connect(
            server_hostname=DATABRICKS_SERVER_HOSTNAME,
            http_path=DATABRICKS_HTTP_PATH,
            access_token=DATABRICKS_TOKEN,
            _socket_timeout=15  # 15 second timeout for test
        )
        
        st.info("Step 3/3: Running test query...")
        
        # Try a simple query
        test_query = "SELECT 1 as test"
        with conn.cursor() as cursor:
            cursor.execute(test_query)
            result = cursor.fetchone()
            if result and result[0] == 1:
                return True, "Connection successful! ✅"
            return False, "Unexpected query result"
    except TimeoutError as e:
        return False, f"Connection timeout - server may be unreachable: {str(e)}"
    except Exception as e:
        error_msg = str(e)
        if "Invalid access token" in error_msg or "authentication" in error_msg.lower():
            return False, "Authentication failed - check your DATABRICKS_TOKEN"
        elif "refused" in error_msg.lower() or "timeout" in error_msg.lower():
            return False, f"Cannot reach server - check hostname: {error_msg}"
        else:
            return False, f"Connection error: {error_msg}"


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
        st.text(f"Host: {DATABRICKS_SERVER_HOSTNAME[:50]}...")
        st.text(f"Path: {DATABRICKS_HTTP_PATH}")
        st.text(f"Token: {'✅ Set' if DATABRICKS_TOKEN else '❌ NOT SET'}")
        if not DATABRICKS_TOKEN:
            st.warning("Set DATABRICKS_TOKEN environment variable!")
    
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
    
    # Year selector
    selected_year = st.sidebar.selectbox(
        "Select Year",
        options=[2024, 2025],
        index=1  # Default to 2025
    )
    
    # Page selection
    page = st.sidebar.radio(
        "Select View",
        ["Overview", "Driver Performance", "Team Analysis", "Race Details", "Tyre Strategy"]
    )
    
    if page == "Overview":
        show_overview(selected_year)
    elif page == "Driver Performance":
        show_driver_performance(selected_year)
    elif page == "Team Analysis":
        show_team_analysis(selected_year)
    elif page == "Race Details":
        show_race_details(selected_year)
    elif page == "Tyre Strategy":
        show_tyre_strategy(selected_year)


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
    
    # Recent races
    st.subheader("Recent Race Sessions")
    recent_races_query = f"""
    SELECT 
        session_name,
        location,
        country_name,
        date_start,
        session_type
    FROM {CATALOG}.{SCHEMA}.silver_sessions
    WHERE year = {year}
    ORDER BY date_start DESC
    LIMIT 10
    """
    
    with st.spinner("Loading recent races..."):
        recent_races = run_query(recent_races_query, timeout=15)
    
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
    WHERE rank <= 10 AND year = {year}
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


def show_driver_performance(year: int = 2025):
    """Display driver performance analysis"""
    st.header(f"🏁 Driver Performance Analysis - {year}")
    
    # Driver selector
    drivers_query = f"""
    SELECT DISTINCT d.full_name, d.driver_number
    FROM {CATALOG}.{SCHEMA}.silver_drivers d
    INNER JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON d.session_key = s.session_key
    WHERE s.year = {year}
    ORDER BY d.full_name
    """
    
    with st.spinner("Loading drivers..."):
        drivers_df = run_query(drivers_query, timeout=15)
    
    if drivers_df.empty:
        st.warning("No driver data available")
        return
    
    selected_driver = st.selectbox(
        "Select Driver",
        drivers_df['full_name'].tolist()
    )
    
    driver_number = drivers_df[drivers_df['full_name'] == selected_driver]['driver_number'].iloc[0]
    
    # Driver stats
    stats_query = f"""
    SELECT 
        COUNT(DISTINCT dp.session_key) as sessions_count,
        AVG(dp.fastest_lap_time) as avg_fastest_lap,
        MIN(dp.fastest_lap_time) as best_lap,
        AVG(dp.pit_stop_count) as avg_pit_stops,
        MAX(dp.max_speed_st) as top_speed
    FROM {CATALOG}.{SCHEMA}.gold_driver_performance dp
    INNER JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON dp.session_key = s.session_key
    WHERE dp.driver_number = {driver_number} AND s.year = {year}
    """
    
    with st.spinner("Loading driver stats..."):
        stats = run_query(stats_query, timeout=15)
    
    if not stats.empty:
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
        s.location,
        s.date_start,
        dp.fastest_lap_time,
        dp.avg_lap_time
    FROM {CATALOG}.{SCHEMA}.gold_driver_performance dp
    JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON dp.session_key = s.session_key
    WHERE dp.driver_number = {driver_number} AND s.year = {year}
    ORDER BY s.date_start
    """
    
    with st.spinner("Loading lap progression..."):
        lap_progression = run_query(lap_progression_query, timeout=15)
    if not lap_progression.empty:
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
            title=f"Lap Time Progression - {selected_driver}",
            xaxis_title="Race Date",
            yaxis_title="Lap Time (seconds)"
        )
        st.plotly_chart(fig, use_container_width=True)


def show_team_analysis(year: int = 2025):
    """Display team performance analysis"""
    st.header(f"🏆 Team Performance Analysis - {year}")
    
    # Team comparison
    team_query = f"""
    SELECT 
        tp.team_name,
        AVG(tp.team_fastest_lap) as avg_fastest_lap,
        AVG(tp.team_avg_pit_duration) as avg_pit_duration,
        MAX(tp.team_max_speed) as max_speed
    FROM {CATALOG}.{SCHEMA}.gold_team_performance tp
    INNER JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON tp.session_key = s.session_key
    WHERE s.year = {year}
    GROUP BY tp.team_name
    ORDER BY avg_fastest_lap
    """
    
    with st.spinner("Loading team data..."):
        team_data = run_query(team_query, timeout=20)
    
    if not team_data.empty:
        # Team fastest laps
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.bar(
                team_data,
                x='team_name',
                y='avg_fastest_lap',
                title='Average Fastest Lap by Team',
                labels={'avg_fastest_lap': 'Lap Time (seconds)', 'team_name': 'Team'}
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.bar(
                team_data,
                x='team_name',
                y='avg_pit_duration',
                title='Average Pit Stop Duration by Team',
                labels={'avg_pit_duration': 'Duration (seconds)', 'team_name': 'Team'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Team data table
        st.subheader("Team Statistics")
        st.dataframe(team_data, use_container_width=True)
    else:
        st.info(f"No team performance data available for {year}. The pipeline may not have processed this data yet.")


def show_race_details(year: int = 2025):
    """Display detailed race information"""
    st.header(f"🏁 Race Details - {year}")
    
    # Get list of races
    races_query = f"""
    SELECT DISTINCT 
        session_key,
        session_name,
        location,
        date_start
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
        races.apply(lambda x: f"{x['location']} - {x['date_start']}", axis=1).tolist()
    )
    
    race_idx = races.apply(lambda x: f"{x['location']} - {x['date_start']}", axis=1).tolist().index(selected_race)
    session_key = races.iloc[race_idx]['session_key']
    
    # Race summary
    summary_query = f"""
    SELECT *
    FROM {CATALOG}.{SCHEMA}.gold_race_summary
    WHERE session_key = {session_key}
    """
    
    summary = run_query(summary_query)
    if not summary.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Laps", summary['total_laps'].iloc[0])
        with col2:
            st.metric("Fastest Lap", f"{summary['fastest_lap'].iloc[0]:.3f}s")
        with col3:
            st.metric("Total Pit Stops", summary['total_pit_stops'].iloc[0])
        with col4:
            st.metric("Safety Cars", summary['safety_cars'].iloc[0])
    
    # Position chart
    st.subheader("Race Positions")
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
    
    position_data = run_query(position_query)
    if not position_data.empty:
        fig = px.line(
            position_data,
            x='date',
            y='position',
            color='driver',
            title='Position Changes Throughout Race',
            labels={'position': 'Position', 'date': 'Time'}
        )
        fig.update_yaxis(autorange="reversed")  # Position 1 at top
        st.plotly_chart(fig, use_container_width=True)


def show_tyre_strategy(year: int = 2025):
    """Display tyre strategy analysis"""
    st.header(f"🔧 Tyre Strategy Analysis - {year}")
    
    # Tyre compound performance
    tyre_query = f"""
    SELECT 
        ts.compound,
        AVG(ts.avg_lap_time_on_compound) as avg_lap_time,
        AVG(ts.stint_laps) as avg_stint_length,
        COUNT(*) as usage_count
    FROM {CATALOG}.{SCHEMA}.gold_tyre_strategy ts
    INNER JOIN {CATALOG}.{SCHEMA}.silver_sessions s ON ts.session_key = s.session_key
    WHERE s.year = {year}
    GROUP BY ts.compound
    ORDER BY avg_lap_time
    """
    
    with st.spinner("Loading tyre data..."):
        tyre_data = run_query(tyre_query, timeout=20)
    
    if not tyre_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.bar(
                tyre_data,
                x='compound',
                y='avg_lap_time',
                title='Average Lap Time by Compound',
                labels={'avg_lap_time': 'Lap Time (seconds)', 'compound': 'Tyre Compound'}
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.pie(
                tyre_data,
                values='usage_count',
                names='compound',
                title='Tyre Compound Usage Distribution'
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader("Compound Statistics")
        st.dataframe(tyre_data, use_container_width=True)
    else:
        st.info(f"No tyre strategy data available for {year}. The pipeline may not have processed this data yet.")


if __name__ == "__main__":
    main()

