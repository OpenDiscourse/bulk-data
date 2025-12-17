"""
BICAM Integration Module

Provides integration with the BICAM (Bulk Ingestion of Congressional Actions & Materials)
Python library for accessing congressional data from congress.gov and GovInfo.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import pandas as pd

# Check BICAM availability without logging immediately
try:
    import bicam
    BICAM_AVAILABLE = True
except ImportError:
    BICAM_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BICAMDataManager:
    """
    Manager for BICAM congressional data operations.
    
    Provides methods for downloading, loading, and managing congressional
    datasets including bills, amendments, members, committees, hearings,
    reports, roll calls, nominations, and communications.
    
    Attributes:
        cache_dir: Directory for caching downloaded datasets
        datasets_info: Information about available datasets
    """
    
    # Available BICAM datasets
    AVAILABLE_DATASETS = [
        'bills',
        'amendments',
        'members',
        'committees',
        'hearings',
        'reports',
        'rollcalls',
        'nominations',
        'communications',
        'texts',
        'complete'  # All datasets combined
    ]
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize BICAM data manager.
        
        Args:
            cache_dir: Directory for caching datasets (None for default)
            
        Raises:
            ImportError: If BICAM library is not installed
        """
        if not BICAM_AVAILABLE:
            error_msg = (
                "BICAM library is not installed. "
                "Install it with: pip install bicam"
            )
            logger.warning(error_msg)
            raise ImportError(error_msg)
        
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.datasets_info = {}
        logger.info("BICAM Data Manager initialized")
    
    def list_datasets(self) -> List[str]:
        """
        List all available BICAM datasets.
        
        Returns:
            List of dataset names
        """
        try:
            datasets = bicam.list_datasets()
            logger.info(f"Found {len(datasets)} available datasets")
            return datasets
        except Exception as e:
            logger.error(f"Failed to list datasets: {e}")
            return self.AVAILABLE_DATASETS
    
    def get_dataset_info(self, dataset_name: str) -> Dict[str, Any]:
        """
        Get information about a specific dataset.
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Dictionary with dataset metadata
        """
        try:
            info = bicam.get_dataset_info(dataset_name)
            logger.info(f"Retrieved info for dataset: {dataset_name}")
            return info
        except Exception as e:
            logger.error(f"Failed to get dataset info: {e}")
            return {}
    
    def download_dataset(self, dataset_name: str, 
                        force: bool = False,
                        quiet: bool = False) -> str:
        """
        Download a BICAM dataset.
        
        Args:
            dataset_name: Name of the dataset to download
            force: Force re-download even if cached
            quiet: Suppress download progress output
            
        Returns:
            Path to downloaded dataset directory
        """
        logger.info(f"Downloading dataset: {dataset_name}")
        
        try:
            kwargs = {
                'dataset_name': dataset_name,
                'force': force,
                'quiet': quiet
            }
            
            if self.cache_dir:
                kwargs['cache_dir'] = str(self.cache_dir)
            
            path = bicam.download_dataset(**kwargs)
            logger.info(f"Dataset downloaded to: {path}")
            return path
            
        except Exception as e:
            logger.error(f"Failed to download dataset {dataset_name}: {e}")
            raise
    
    def load_dataframe(self, dataset_name: str,
                      file_name: Optional[str] = None,
                      engine: str = 'pandas',
                      download: bool = True,
                      force: bool = False) -> Any:
        """
        Load a dataset into a DataFrame.
        
        Args:
            dataset_name: Name of the dataset
            file_name: Specific file to load (None for default)
            engine: DataFrame engine ('pandas', 'polars', 'dask', 'spark', 'duckdb')
            download: Whether to download if not cached
            force: Force re-download
            
        Returns:
            DataFrame object (type depends on engine)
        """
        logger.info(f"Loading dataset: {dataset_name} with engine: {engine}")
        
        try:
            kwargs = {
                'dataset_name': dataset_name,
                'engine': engine,
                'download': download,
                'force': force
            }
            
            if file_name:
                kwargs['file_name'] = file_name
            
            if self.cache_dir:
                kwargs['cache_dir'] = str(self.cache_dir)
            
            df = bicam.load_dataframe(**kwargs)
            
            if hasattr(df, 'shape'):
                logger.info(f"Loaded DataFrame with shape: {df.shape}")
            else:
                logger.info(f"Loaded DataFrame (engine: {engine})")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load dataset {dataset_name}: {e}")
            raise
    
    # Convenience methods for specific datasets
    
    def get_bills_dataframe(self, download: bool = True) -> pd.DataFrame:
        """
        Get bills dataset as pandas DataFrame.
        
        Args:
            download: Whether to download if not cached
            
        Returns:
            Pandas DataFrame with bills data
        """
        return self.load_dataframe('bills', engine='pandas', download=download)
    
    def get_amendments_dataframe(self, download: bool = True) -> pd.DataFrame:
        """
        Get amendments dataset as pandas DataFrame.
        
        Args:
            download: Whether to download if not cached
            
        Returns:
            Pandas DataFrame with amendments data
        """
        return self.load_dataframe('amendments', engine='pandas', download=download)
    
    def get_members_dataframe(self, download: bool = True) -> pd.DataFrame:
        """
        Get members (legislators) dataset as pandas DataFrame.
        
        Args:
            download: Whether to download if not cached
            
        Returns:
            Pandas DataFrame with members data
        """
        return self.load_dataframe('members', engine='pandas', download=download)
    
    def get_committees_dataframe(self, download: bool = True) -> pd.DataFrame:
        """
        Get committees dataset as pandas DataFrame.
        
        Args:
            download: Whether to download if not cached
            
        Returns:
            Pandas DataFrame with committees data
        """
        return self.load_dataframe('committees', engine='pandas', download=download)
    
    def get_hearings_dataframe(self, download: bool = True) -> pd.DataFrame:
        """
        Get hearings dataset as pandas DataFrame.
        
        Args:
            download: Whether to download if not cached
            
        Returns:
            Pandas DataFrame with hearings data
        """
        return self.load_dataframe('hearings', engine='pandas', download=download)
    
    def get_rollcalls_dataframe(self, download: bool = True) -> pd.DataFrame:
        """
        Get roll calls (votes) dataset as pandas DataFrame.
        
        Args:
            download: Whether to download if not cached
            
        Returns:
            Pandas DataFrame with roll calls data
        """
        return self.load_dataframe('rollcalls', engine='pandas', download=download)
    
    def download_all_datasets(self, force: bool = False) -> Dict[str, str]:
        """
        Download all available BICAM datasets.
        
        Args:
            force: Force re-download even if cached
            
        Returns:
            Dictionary mapping dataset names to their paths
        """
        logger.info("Downloading all BICAM datasets")
        results = {}
        
        for dataset_name in self.AVAILABLE_DATASETS:
            if dataset_name == 'complete':
                # Skip 'complete' as it's a meta-dataset
                continue
            
            try:
                path = self.download_dataset(dataset_name, force=force, quiet=False)
                results[dataset_name] = path
            except Exception as e:
                logger.error(f"Failed to download {dataset_name}: {e}")
                results[dataset_name] = None
        
        successful = sum(1 for v in results.values() if v is not None)
        logger.info(f"Downloaded {successful}/{len(results)} datasets")
        
        return results
    
    def get_summary_statistics(self, dataset_name: str) -> Dict[str, Any]:
        """
        Get summary statistics for a dataset.
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Dictionary with summary statistics
        """
        try:
            df = self.load_dataframe(dataset_name, engine='pandas', download=True)
            
            stats = {
                'dataset': dataset_name,
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 ** 2),
                'dtypes': df.dtypes.to_dict()
            }
            
            logger.info(f"Summary statistics for {dataset_name}: {stats['row_count']} rows, {stats['column_count']} columns")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics for {dataset_name}: {e}")
            return {}


class BICAMPostgreSQLIngester:
    """
    Ingests BICAM datasets into PostgreSQL database.
    
    Provides methods to load BICAM data and insert it into PostgreSQL
    tables for integration with OpenStates data.
    """
    
    def __init__(self, bicam_manager: BICAMDataManager, database_url: str):
        """
        Initialize BICAM PostgreSQL ingester.
        
        Args:
            bicam_manager: BICAM data manager instance
            database_url: PostgreSQL connection string
        """
        self.bicam_manager = bicam_manager
        self.database_url = database_url
        logger.info("BICAM PostgreSQL Ingester initialized")
    
    def ingest_dataset(self, dataset_name: str, 
                      table_name: Optional[str] = None,
                      if_exists: str = 'replace',
                      chunksize: int = 1000) -> Dict[str, Any]:
        """
        Ingest a BICAM dataset into PostgreSQL.
        
        Args:
            dataset_name: Name of the BICAM dataset
            table_name: PostgreSQL table name (defaults to dataset_name)
            if_exists: How to behave if table exists ('fail', 'replace', 'append')
            chunksize: Number of rows to insert at a time
            
        Returns:
            Dictionary with ingestion statistics
        """
        from sqlalchemy import create_engine
        
        table_name = table_name or f"bicam_{dataset_name}"
        logger.info(f"Ingesting BICAM dataset {dataset_name} into table {table_name}")
        
        try:
            # Load dataset
            df = self.bicam_manager.load_dataframe(dataset_name, engine='pandas', download=True)
            
            # Create engine
            engine = create_engine(self.database_url)
            
            # Ingest to PostgreSQL
            df.to_sql(
                table_name,
                engine,
                if_exists=if_exists,
                index=False,
                chunksize=chunksize
            )
            
            stats = {
                'dataset': dataset_name,
                'table': table_name,
                'rows_inserted': len(df),
                'columns': len(df.columns),
                'status': 'success'
            }
            
            logger.info(f"Successfully ingested {stats['rows_inserted']} rows into {table_name}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to ingest {dataset_name}: {e}")
            return {
                'dataset': dataset_name,
                'table': table_name,
                'status': 'failed',
                'error': str(e)
            }
    
    def ingest_all_datasets(self, chunksize: int = 1000) -> Dict[str, Any]:
        """
        Ingest all BICAM datasets into PostgreSQL.
        
        Args:
            chunksize: Number of rows to insert at a time
            
        Returns:
            Dictionary with aggregated statistics
        """
        logger.info("Ingesting all BICAM datasets")
        results = []
        
        for dataset_name in self.bicam_manager.AVAILABLE_DATASETS:
            if dataset_name == 'complete':
                continue
            
            result = self.ingest_dataset(dataset_name, chunksize=chunksize)
            results.append(result)
        
        successful = sum(1 for r in results if r.get('status') == 'success')
        total_rows = sum(r.get('rows_inserted', 0) for r in results if r.get('status') == 'success')
        
        summary = {
            'total_datasets': len(results),
            'successful': successful,
            'failed': len(results) - successful,
            'total_rows_inserted': total_rows,
            'details': results
        }
        
        logger.info(f"Ingestion complete: {successful}/{len(results)} datasets, {total_rows} total rows")
        return summary
