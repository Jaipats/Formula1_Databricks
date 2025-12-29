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
DATABRICKS_SERVER_HOSTNAME = os.getenv("DATABRICKS_SERVER_HOSTNAME", "e2-demo-field-eng.cloud.databricks.com/.cloud.databricks.com")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/4b9b953939869799")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")  # Set via environment variable

# Unity Catalog Configuration - Make this configurable
CATALOG = os.getenv("F1_CATALOG", "jai_patel_f1_data")
SCHEMA = os.getenv("F1_SCHEMA", "racing_stats")

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
    """Create database connection"""
    try:
        connection = sql.connect(
            server_hostname=DATABRICKS_SERVER_HOSTNAME,
            http_path=DATABRICKS_HTTP_PATH,
            access_token=DATABRICKS_TOKEN
        )
        return connection
    except Exception as e:
        st.error(f"Failed to connect to Databricks: {str(e)}")
        return None


@st.cache_data(ttl=3600)
def run_query(query: str) -> pd.DataFrame:
    """Execute SQL query and return results as DataFrame"""
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            return pd.DataFrame(data, columns=columns)
    except Exception as e:
        st.error(f"Query error: {str(e)}")
        return pd.DataFrame()


def main():
    """Main dashboard application"""
    
    # Header
    st.markdown('<div class="main-header">🏎️ Formula 1 Race Analytics</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("Dashboard Controls")
    st.sidebar.info(f"**Catalog:** {CATALOG}\n\n**Schema:** {SCHEMA}")
    
    # Page selection
    page = st.sidebar.radio(
        "Select View",
        ["Overview", "Driver Performance", "Team Analysis", "Race Details", "Tyre Strategy"]
    )
    
    if page == "Overview":
        show_overview()
    elif page == "Driver Performance":
        show_driver_performance()
    elif page == "Team Analysis":
        show_team_analysis()
    elif page == "Race Details":
        show_race_details()
    elif page == "Tyre Strategy":
        show_tyre_strategy()


def show_overview():
    """Display overview dashboard"""
    st.header("📊 Season Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Query for metrics
    metrics_query = f"""
    SELECT 
        COUNT(DISTINCT meeting_key) as total_races,
        COUNT(DISTINCT session_key) as total_sessions,
        COUNT(DISTINCT driver_number) as total_drivers
    FROM {CATALOG}.{SCHEMA}.silver_sessions s
    LEFT JOIN {CATALOG}.{SCHEMA}.silver_drivers d ON s.session_key = d.session_key
    WHERE s.year = YEAR(CURRENT_DATE())
    """
    
    metrics = run_query(metrics_query)
    
    if not metrics.empty:
        with col1:
            st.metric("Total Races", metrics['total_races'].iloc[0])
        with col2:
            st.metric("Total Sessions", metrics['total_sessions'].iloc[0])
        with col3:
            st.metric("Total Drivers", metrics['total_drivers'].iloc[0])
        with col4:
            st.metric("Season", datetime.now().year)
    
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
    WHERE year = YEAR(CURRENT_DATE())
    ORDER BY date_start DESC
    LIMIT 10
    """
    
    recent_races = run_query(recent_races_query)
    if not recent_races.empty:
        st.dataframe(recent_races, use_container_width=True)
    
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
    
    fastest_laps = run_query(fastest_laps_query)
    if not fastest_laps.empty:
        fig = px.bar(
            fastest_laps,
            x='driver',
            y='lap_time',
            color='team_name',
            title='Fastest Lap Times',
            labels={'lap_time': 'Lap Time (seconds)', 'driver': 'Driver'}
        )
        st.plotly_chart(fig, use_container_width=True)


def show_driver_performance():
    """Display driver performance analysis"""
    st.header("🏁 Driver Performance Analysis")
    
    # Driver selector
    drivers_query = f"""
    SELECT DISTINCT full_name, driver_number
    FROM {CATALOG}.{SCHEMA}.silver_drivers
    ORDER BY full_name
    """
    drivers_df = run_query(drivers_query)
    
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
        COUNT(DISTINCT session_key) as sessions_count,
        AVG(fastest_lap_time) as avg_fastest_lap,
        MIN(fastest_lap_time) as best_lap,
        AVG(pit_stop_count) as avg_pit_stops,
        MAX(max_speed_st) as top_speed
    FROM {CATALOG}.{SCHEMA}.gold_driver_performance
    WHERE driver_number = {driver_number}
    """
    
    stats = run_query(stats_query)
    
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
    WHERE dp.driver_number = {driver_number}
    ORDER BY s.date_start
    """
    
    lap_progression = run_query(lap_progression_query)
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


def show_team_analysis():
    """Display team performance analysis"""
    st.header("🏆 Team Performance Analysis")
    
    # Team comparison
    team_query = f"""
    SELECT 
        team_name,
        AVG(team_fastest_lap) as avg_fastest_lap,
        AVG(team_avg_pit_duration) as avg_pit_duration,
        MAX(team_max_speed) as max_speed
    FROM {CATALOG}.{SCHEMA}.gold_team_performance
    GROUP BY team_name
    ORDER BY avg_fastest_lap
    """
    
    team_data = run_query(team_query)
    
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


def show_race_details():
    """Display detailed race information"""
    st.header("🏁 Race Details")
    
    # Get list of races
    races_query = f"""
    SELECT DISTINCT 
        session_key,
        session_name,
        location,
        date_start
    FROM {CATALOG}.{SCHEMA}.silver_sessions
    WHERE session_type IN ('Race', 'Sprint')
    ORDER BY date_start DESC
    """
    
    races = run_query(races_query)
    
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


def show_tyre_strategy():
    """Display tyre strategy analysis"""
    st.header("🔧 Tyre Strategy Analysis")
    
    # Tyre compound performance
    tyre_query = f"""
    SELECT 
        compound,
        AVG(avg_lap_time_on_compound) as avg_lap_time,
        AVG(stint_laps) as avg_stint_length,
        COUNT(*) as usage_count
    FROM {CATALOG}.{SCHEMA}.gold_tyre_strategy
    GROUP BY compound
    ORDER BY avg_lap_time
    """
    
    tyre_data = run_query(tyre_query)
    
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


if __name__ == "__main__":
    main()

