-- Setup Script for Unity Catalog
-- Run this in Databricks SQL or notebook to initialize the catalog and schema

-- PARAMETERS: Modify these values as needed
SET VAR catalog_name = 'jai_patel_f1_data';
SET VAR schema_name = 'racing_stats';

-- Create Catalog
CREATE CATALOG IF NOT EXISTS ${catalog_name}
COMMENT 'Formula 1 race data and analytics';

-- Use the catalog
USE CATALOG ${catalog_name};

-- Create Schema
CREATE SCHEMA IF NOT EXISTS ${schema_name}
COMMENT 'F1 racing statistics and telemetry data';

-- Use the schema
USE SCHEMA ${schema_name};

-- Grant permissions (adjust as needed for your organization)
-- GRANT USAGE ON CATALOG ${catalog_name} TO `data_analysts`;
-- GRANT SELECT ON SCHEMA ${catalog_name}.${schema_name} TO `data_analysts`;

-- Create volumes for data storage
CREATE VOLUME IF NOT EXISTS raw_data
COMMENT 'Storage for raw API responses and files';

CREATE VOLUME IF NOT EXISTS pipeline_storage
COMMENT 'Storage for DLT pipeline checkpoints and metadata';

-- Display current setup
SELECT 
    '${catalog_name}' as catalog,
    '${schema_name}' as schema,
    'Setup complete!' as status;

-- Show created objects
SHOW CATALOGS LIKE '${catalog_name}';
SHOW SCHEMAS IN CATALOG ${catalog_name};

