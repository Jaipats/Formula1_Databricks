# Formula 1 Data Pipeline - Architecture

## Overview

This project implements a modern data pipeline using the **Medallion Architecture** (Bronze → Silver → Gold) on Databricks with Unity Catalog for data governance.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCE                              │
│                     OpenF1 API (REST)                            │
│              https://api.openf1.org/v1/                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP Requests
                             │ (Rate Limited: 1 req/sec)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  Databricks Notebook: 01_ingest_f1_data.py           │      │
│  │                                                       │      │
│  │  • API Client (utils/api_client.py)                  │      │
│  │    - Rate limiting                                    │      │
│  │    - Error handling & retry logic                    │      │
│  │    - Timeout management                               │      │
│  │                                                       │      │
│  │  • Data Fetcher (utils/data_fetcher.py)              │      │
│  │    - Orchestrates API calls                          │      │
│  │    - Fetches by session (manageable batches)         │      │
│  │    - Converts to DataFrames                          │      │
│  └──────────────────────────────────────────────────────┘      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BRONZE LAYER (Raw Data)                       │
│                  Unity Catalog: catalog.schema                   │
│                                                                  │
│  Delta Tables (Overwrite Mode):                                 │
│  • bronze_meetings         • bronze_sessions                    │
│  • bronze_drivers          • bronze_laps                        │
│  • bronze_car_data         • bronze_position                    │
│  • bronze_pit              • bronze_stints                      │
│  • bronze_weather          • bronze_race_control                │
│  • bronze_team_radio       • bronze_intervals                   │
│  • bronze_overtakes        • bronze_session_result              │
│  • bronze_starting_grid                                         │
│                                                                  │
│  Metadata:                                                       │
│  • _ingestion_timestamp                                         │
│  • _ingestion_date                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              SILVER LAYER (Cleaned & Validated)                  │
│                Delta Live Tables (DLT)                           │
│              dlt/f1_bronze_to_silver.py                          │
│                                                                  │
│  Transformations:                                                │
│  • Type casting (String → Int, Timestamp, etc.)                 │
│  • Data quality checks (DLT expectations)                       │
│  • Deduplication                                                 │
│  • Schema enforcement                                            │
│                                                                  │
│  Tables:                                                         │
│  • silver_meetings         • silver_sessions                    │
│  • silver_drivers          • silver_laps                        │
│  • silver_car_data         • silver_position                    │
│  • silver_pit              • silver_stints                      │
│  • silver_weather          • silver_race_control                │
│  • silver_team_radio       • silver_intervals                   │
│  • silver_overtakes        • silver_session_result              │
│  • silver_starting_grid                                         │
│                                                                  │
│  Metadata:                                                       │
│  • _processed_timestamp                                         │
│                                                                  │
│  Data Quality Expectations:                                      │
│  • NOT NULL checks on keys                                      │
│  • Range validations (speed, RPM, etc.)                         │
│  • Date/year validations                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              GOLD LAYER (Business Analytics)                     │
│                Delta Live Tables (DLT)                           │
│              dlt/f1_gold_aggregations.py                         │
│                                                                  │
│  Aggregations & Calculations:                                    │
│                                                                  │
│  • gold_driver_performance                                      │
│    - Avg/fastest lap times per driver per session               │
│    - Pit stop statistics                                        │
│    - Speed statistics                                           │
│                                                                  │
│  • gold_team_performance                                        │
│    - Team-level aggregations                                    │
│    - Combined driver statistics                                 │
│                                                                  │
│  • gold_race_summary                                            │
│    - Race-level metrics                                         │
│    - Weather conditions                                         │
│    - Incident counts (flags, safety cars)                       │
│                                                                  │
│  • gold_tyre_strategy                                           │
│    - Performance by compound                                    │
│    - Stint length analysis                                      │
│                                                                  │
│  • gold_fastest_laps                                            │
│    - Ranked fastest laps                                        │
│    - Cross-session comparisons                                  │
│                                                                  │
│  • gold_overtakes_analysis                                      │
│    - Overtaking statistics by driver                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CONSUMPTION LAYER                              │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  SQL Dashboards  │  │   Genie Space    │                    │
│  │                  │  │   (AI/BI)        │                    │
│  │  • Charts        │  │                  │                    │
│  │  • Tables        │  │  Natural Language│                    │
│  │  • Metrics       │  │  Queries         │                    │
│  └──────────────────┘  └──────────────────┘                    │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ Databricks App   │  │   BI Tools       │                    │
│  │ (Streamlit)      │  │                  │                    │
│  │                  │  │  • Tableau       │                    │
│  │  Interactive     │  │  • Power BI      │                    │
│  │  Dashboard       │  │  • Looker        │                    │
│  └──────────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Configuration Layer
- **File**: `config/pipeline_config.yaml`
- **Purpose**: Centralized configuration for Unity Catalog, API settings, and pipeline behavior
- **Key Features**:
  - Parameterized catalog/schema (easily swappable)
  - Endpoint enable/disable flags
  - API rate limiting configuration

### 2. Ingestion Layer
- **Files**: 
  - `utils/api_client.py` - HTTP client with retry logic
  - `utils/data_fetcher.py` - Orchestration logic
  - `notebooks/01_ingest_f1_data.py` - Execution notebook
- **Pattern**: Batch ingestion (session-based)
- **Frequency**: On-demand (can be scheduled)
- **Error Handling**: 
  - Exponential backoff
  - Request timeouts
  - Partial failure tolerance

### 3. Bronze Layer
- **Storage**: Delta Lake tables in Unity Catalog
- **Schema**: Flexible (schema-on-read)
- **Mode**: Overwrite (full refresh)
- **Metadata**: Ingestion timestamps for lineage
- **Purpose**: Audit trail and data recovery

### 4. Silver Layer
- **Technology**: Delta Live Tables (DLT)
- **Transformations**: 
  - Schema enforcement
  - Type casting
  - Data validation
  - Deduplication
- **Quality**: DLT expectations (drop invalid records)
- **Optimization**: Z-ordering on key columns

### 5. Gold Layer
- **Technology**: Delta Live Tables (DLT)
- **Purpose**: Business-ready analytics tables
- **Aggregations**:
  - Driver performance metrics
  - Team comparisons
  - Race summaries
  - Tyre strategies
- **Updates**: Cascades from Silver layer changes

### 6. Consumption Layer
- **SQL Dashboards**: Pre-built analytical queries
- **Genie Space**: AI-powered natural language interface
- **Databricks App**: Interactive Streamlit dashboard
- **External BI**: JDBC/ODBC connections to BI tools

## Data Flow

### Batch Processing Flow
```
API Request → Parse JSON → Pandas DataFrame → Spark DataFrame → Delta Table
```

### DLT Processing Flow
```
Bronze (Raw) → [DLT] → Silver (Clean) → [DLT] → Gold (Agg) → Query
```

### Update Pattern
```
1. Run ingestion notebook (Bronze)
2. DLT auto-triggers (or manual trigger)
3. Silver tables update
4. Gold tables update
5. Dashboards refresh
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Storage | Delta Lake | ACID transactions, versioning |
| Catalog | Unity Catalog | Data governance, lineage |
| Processing | Apache Spark | Distributed processing |
| Orchestration | Delta Live Tables | Declarative pipeline management |
| Notebook | Databricks Notebooks | Development & execution |
| Visualization | Databricks SQL | Dashboards and reporting |
| AI/BI | Genie | Natural language queries |
| App | Streamlit | Interactive web app |

## Scalability

### Horizontal Scaling
- **Ingestion**: Parallel API requests (within rate limits)
- **Processing**: Spark auto-scales workers
- **Storage**: Delta Lake handles petabyte-scale data

### Optimization Techniques
1. **Z-Ordering**: On frequently filtered columns
2. **Partitioning**: Could add by year/month if needed
3. **Liquid Clustering**: For high-cardinality columns
4. **Photon**: Accelerated query engine
5. **Caching**: Frequently accessed tables

## Security & Governance

### Unity Catalog Features
- **Lineage**: Track data flow from source to consumption
- **Access Control**: Fine-grained permissions (catalog/schema/table/column)
- **Audit Logging**: Track all data access
- **Data Classification**: Tag sensitive data

### Best Practices Implemented
- Parameterized catalog/schema for environment isolation
- Separate bronze/silver/gold for data quality boundaries
- Metadata columns for debugging and auditing
- DLT expectations for data quality validation

## Monitoring & Observability

### Built-in Monitoring
1. **DLT Pipeline UI**: View DAG, data quality metrics, lineage
2. **Table History**: Delta Lake versioning (`DESCRIBE HISTORY`)
3. **Ingestion Logs**: Databricks notebook logs
4. **Query Profiling**: Databricks SQL query history

### Key Metrics to Monitor
- Ingestion success rate
- DLT expectation failures
- Table growth over time
- Query performance
- Cost per pipeline run

## Disaster Recovery

### Data Recovery
- **Bronze**: Re-run ingestion from API (if data available)
- **Silver/Gold**: Re-run DLT pipeline
- **Delta Time Travel**: Query historical versions
  ```sql
  SELECT * FROM table VERSION AS OF 123
  SELECT * FROM table TIMESTAMP AS OF '2025-01-01'
  ```

### Backup Strategy
- Unity Catalog manages Delta Lake checkpoints
- Bronze layer serves as raw data backup
- Consider periodic snapshots for critical tables

## Future Enhancements

### Potential Additions
1. **Real-time Streaming**: Use OpenF1 MQTT for live data
2. **Change Data Capture**: Track row-level changes
3. **ML Integration**: Add MLflow for predictions
4. **Advanced Analytics**: Correlation analysis, predictions
5. **Data Sharing**: Delta Sharing for external access
6. **Incremental Processing**: Append-only mode for efficiency
7. **Cost Optimization**: Serverless compute, spot instances

---

This architecture provides a scalable, maintainable, and governed solution for Formula 1 data analytics on Databricks.

