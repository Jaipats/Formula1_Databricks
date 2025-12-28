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
    def retry_attempts(self) -> int:
        """Get number of retry attempts for API calls"""
        return self.config['api'].get('retry_attempts', 5)

    @property
    def timeout(self) -> int:
        """Get API request timeout in seconds"""
        return self.config['api'].get('timeout', 30)

    @property
    def parallel_endpoints(self) -> bool:
        """Get whether to enable parallel endpoint fetching"""
        return self.config['api'].get('parallel_endpoints', False)

    @property
    def max_workers(self) -> int:
        """Get max number of parallel workers"""
        return self.config['api'].get('max_workers', 3)

    @property
    def batch_size(self) -> int:
        """Get batch size for data processing"""
        return self.config['data'].get('batch_size', 1000)

    @property
    def use_volume_staging(self) -> bool:
        """Get whether to use volume staging for incremental writes"""
        return self.config['data'].get('use_volume_staging', True)

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
