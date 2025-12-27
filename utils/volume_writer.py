"""
Volume Writer Module
Handles writing data incrementally to Unity Catalog volumes
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class VolumeDataWriter:
    """Write data incrementally to Unity Catalog volumes"""
    
    def __init__(self, catalog: str, schema: str, volume: str, base_path: str = "staging"):
        """
        Initialize volume writer
        
        Args:
            catalog: Unity Catalog name
            schema: Schema name
            volume: Volume name
            base_path: Base path within volume for staging files
        """
        self.catalog = catalog
        self.schema = schema
        self.volume = volume
        self.base_path = base_path
        
        # Volume path format: /Volumes/{catalog}/{schema}/{volume}/{path}
        self.volume_root = f"/Volumes/{catalog}/{schema}/{volume}/{base_path}"
        
        # Track what's been written
        self.written_files = {}
        
    def get_endpoint_path(self, endpoint: str) -> str:
        """Get full path for an endpoint's staging directory"""
        return f"{self.volume_root}/{endpoint}"
    
    def write_data_batch(self, endpoint: str, data: List[Dict], 
                        batch_id: str = None) -> str:
        """
        Write a batch of data to volume
        
        Args:
            endpoint: API endpoint name (e.g., 'car_data', 'laps')
            data: List of records to write
            batch_id: Optional batch identifier (e.g., session_key_driver_number)
            
        Returns:
            Path to written file
        """
        if not data:
            logger.info(f"No data to write for {endpoint}")
            return None
        
        # Create batch ID if not provided
        if batch_id is None:
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create directory path
        endpoint_path = self.get_endpoint_path(endpoint)
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{batch_id}_{timestamp}.json"
        filepath = f"{endpoint_path}/{filename}"
        
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(data)
        
        # Write as JSON lines (more efficient for appending)
        logger.info(f"Writing {len(data)} records to {filepath}")
        
        # Note: In Databricks, you'd use dbutils.fs or spark to write
        # This is a placeholder that works locally
        try:
            # For Databricks: dbutils.fs.put(filepath, df.to_json(orient='records', lines=True))
            # For local testing:
            Path(endpoint_path).mkdir(parents=True, exist_ok=True)
            df.to_json(filepath, orient='records', lines=True)
            
            # Track written file
            if endpoint not in self.written_files:
                self.written_files[endpoint] = []
            self.written_files[endpoint].append(filepath)
            
            logger.info(f"✓ Wrote {len(data)} records to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error writing to volume: {str(e)}")
            raise
    
    def write_metadata(self, endpoint: str, metadata: Dict[str, Any]):
        """Write metadata about the ingestion"""
        endpoint_path = self.get_endpoint_path(endpoint)
        metadata_path = f"{endpoint_path}/_metadata.json"
        
        try:
            Path(endpoint_path).mkdir(parents=True, exist_ok=True)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            logger.info(f"✓ Wrote metadata to {metadata_path}")
        except Exception as e:
            logger.error(f"Error writing metadata: {str(e)}")
    
    def list_data_files(self, endpoint: str) -> List[str]:
        """List all data files for an endpoint"""
        endpoint_path = self.get_endpoint_path(endpoint)
        
        try:
            # For Databricks: dbutils.fs.ls(endpoint_path)
            # For local:
            path = Path(endpoint_path)
            if not path.exists():
                return []
            
            files = [str(f) for f in path.glob("*.json") if not f.name.startswith("_")]
            return files
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary of written files"""
        summary = {}
        for endpoint, files in self.written_files.items():
            summary[endpoint] = len(files)
        return summary


class SparkVolumeWriter(VolumeDataWriter):
    """Spark-based volume writer for Databricks"""
    
    def __init__(self, spark, catalog: str, schema: str, volume: str, base_path: str = "staging"):
        """
        Initialize Spark volume writer
        
        Args:
            spark: SparkSession
            catalog: Unity Catalog name
            schema: Schema name
            volume: Volume name
            base_path: Base path within volume
        """
        super().__init__(catalog, schema, volume, base_path)
        self.spark = spark
    
    def write_data_batch(self, endpoint: str, data: List[Dict], 
                        batch_id: str = None) -> str:
        """Write batch using Spark"""
        if not data:
            logger.info(f"No data to write for {endpoint}")
            return None
        
        if batch_id is None:
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        endpoint_path = self.get_endpoint_path(endpoint)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{batch_id}_{timestamp}.json"
        filepath = f"{endpoint_path}/{filename}"
        
        try:
            # Convert to Spark DataFrame
            df = self.spark.createDataFrame(pd.DataFrame(data))
            
            # Write as JSON (single file)
            logger.info(f"Writing {len(data)} records to {filepath}")
            df.coalesce(1).write.mode("overwrite").json(filepath)
            
            # Track written file
            if endpoint not in self.written_files:
                self.written_files[endpoint] = []
            self.written_files[endpoint].append(filepath)
            
            logger.info(f"✓ Wrote {len(data)} records to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error writing to volume: {str(e)}")
            raise
    
    def list_data_files(self, endpoint: str) -> List[str]:
        """List data files using dbutils"""
        endpoint_path = self.get_endpoint_path(endpoint)
        
        try:
            files = [f.path for f in dbutils.fs.ls(endpoint_path) if f.path.endswith('.json') and not f.name.startswith('_')]
            return files
        except Exception as e:
            logger.warning(f"No files found for {endpoint}: {str(e)}")
            return []

