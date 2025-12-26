"""
Configuration Settings for F1 Data Pipeline
Load and validate configuration from YAML file
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any


class PipelineConfig:
    """Manage pipeline configuration"""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration

        Args:
            config_path: Path to YAML config file. If None, uses default location.
        """
        if config_path is None:
            # Default to config/pipeline_config.yaml relative to project root
            config_path = Path(__file__).parent / "pipeline_config.yaml"

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    @property
    def catalog(self) -> str:
        """Get Unity Catalog name"""
        return self.config['unity_catalog']['catalog']

    @property
    def schema(self) -> str:
        """Get schema name"""
        return self.config['unity_catalog']['schema']

    @property
    def volume(self) -> str:
        """Get volume name"""
        return self.config['unity_catalog'].get('volume', 'raw_data')

    @property
    def full_schema_name(self) -> str:
        """Get fully qualified schema name"""
        return f"{self.catalog}.{self.schema}"

    @property
    def api_base_url(self) -> str:
        """Get API base URL"""
        return self.config['api']['base_url']

    @property
    def target_year(self) -> int:
        """Get target year for data fetching"""
        return self.config['data']['target_year']

    @property
    def rate_limit_delay(self) -> float:
        """Get rate limit delay in seconds"""
        return self.config['api']['rate_limit_delay']

    @property
    def enabled_endpoints(self) -> Dict[str, bool]:
        """Get dictionary of enabled endpoints"""
        return self.config['endpoints']

    def get_table_name(self, endpoint: str) -> str:
        """
        Get fully qualified table name for an endpoint

        Args:
            endpoint: API endpoint name

        Returns:
            Fully qualified table name (catalog.schema.table)
        """
        return f"{self.catalog}.{self.schema}.{endpoint}"

    def get_bronze_table_name(self, endpoint: str) -> str:
        """Get bronze (raw) table name"""
        return f"{self.catalog}.{self.schema}.bronze_{endpoint}"

    def get_silver_table_name(self, endpoint: str) -> str:
        """Get silver (cleaned) table name"""
        return f"{self.catalog}.{self.schema}.silver_{endpoint}"

    def get_gold_table_name(self, table_name: str) -> str:
        """Get gold (aggregated) table name"""
        return f"{self.catalog}.{self.schema}.gold_{table_name}"


# Create a singleton instance
config = PipelineConfig()
