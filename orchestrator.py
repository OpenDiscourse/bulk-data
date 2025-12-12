"""
Data Ingestion Orchestrator

Main orchestration module that ties together API clients, rate limiting,
data tracking, and parallel workers for efficient bulk data ingestion.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from api_client import CongressAPIClient, GovInfoAPIClient, BulkDataClient
from rate_limiter import RateLimiterManager
from data_tracker import DataTrackerManager, DataTracker
from worker_pool import WorkerPool, Task, DistributedIngestionCoordinator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataIngestionOrchestrator:
    """
    Orchestrates the entire data ingestion process.
    
    Manages API clients, rate limiting, data tracking, and parallel processing
    to efficiently ingest data from api.congress.gov and govinfo.gov.
    """
    
    def __init__(self, 
                 congress_api_key: Optional[str] = None,
                 govinfo_api_key: Optional[str] = None,
                 num_workers: int = 4,
                 output_dir: str = "./data",
                 db_path: str = "./data_tracking.db"):
        """
        Initialize the orchestrator.
        
        Args:
            congress_api_key: API key for api.congress.gov
            govinfo_api_key: API key for api.govinfo.gov
            num_workers: Number of parallel workers
            output_dir: Directory for output data
            db_path: Path to tracking database
        """
        # API keys
        self.congress_api_key = congress_api_key or os.getenv("CONGRESS_API_KEY")
        self.govinfo_api_key = govinfo_api_key or os.getenv("GOVINFO_API_KEY")
        
        # Output directory
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize rate limiters
        self.rate_limiter_manager = RateLimiterManager()
        self.congress_rate_limiter = self.rate_limiter_manager.get_or_create(
            "congress_api", 
            requests_per_hour=5000,
            requests_per_minute=83
        )
        self.govinfo_rate_limiter = self.rate_limiter_manager.get_or_create(
            "govinfo_api",
            requests_per_hour=1000,
            requests_per_minute=16
        )
        self.bulkdata_rate_limiter = self.rate_limiter_manager.get_or_create(
            "govinfo_bulkdata",
            requests_per_hour=1000,
            requests_per_minute=16
        )
        
        # Initialize API clients
        self.congress_client: Optional[CongressAPIClient] = None
        self.govinfo_client: Optional[GovInfoAPIClient] = None
        self.bulkdata_client: Optional[BulkDataClient] = None
        
        if self.congress_api_key:
            self.congress_client = CongressAPIClient(
                self.congress_api_key,
                self.congress_rate_limiter
            )
        
        if self.govinfo_api_key:
            self.govinfo_client = GovInfoAPIClient(
                self.govinfo_api_key,
                self.govinfo_rate_limiter
            )
        
        self.bulkdata_client = BulkDataClient(self.bulkdata_rate_limiter)
        
        # Initialize data tracking
        self.tracker_manager = DataTrackerManager(
            storage_type="sqlite",
            db_path=db_path
        )
        
        # Initialize worker pool
        self.worker_pool = WorkerPool(num_workers=num_workers)
        self.coordinator = DistributedIngestionCoordinator(self.worker_pool)
    
    def _get_tracker(self, name: str) -> DataTracker:
        """Get or create a data tracker."""
        return self.tracker_manager.get_tracker(name)
    
    def ingest_congress_bills(self, congress: Optional[int] = None,
                             bill_type: Optional[str] = None,
                             max_items: Optional[int] = None) -> Dict[str, Any]:
        """
        Ingest bills from api.congress.gov.
        
        Args:
            congress: Congress number (e.g., 118)
            bill_type: Bill type (e.g., 'hr', 's')
            max_items: Maximum items to retrieve
            
        Returns:
            Dictionary with ingestion statistics
        """
        if not self.congress_client:
            raise ValueError("Congress API key not configured")
        
        logger.info(f"Starting bill ingestion: congress={congress}, type={bill_type}")
        
        # Get tracker
        tracker_name = f"congress_bills_{congress}_{bill_type}" if congress and bill_type else "congress_bills"
        tracker = self._get_tracker(tracker_name)
        
        # Collect items
        items_to_process = []
        for bill in self.congress_client.get_bills(congress, bill_type, max_items):
            bill_id = bill.get('number', f"bill_{len(items_to_process)}")
            
            # Check if already processed
            if tracker.has_item(bill_id):
                logger.debug(f"Skipping already processed bill: {bill_id}")
                continue
            
            items_to_process.append({
                "id": bill_id,
                "data": bill
            })
        
        logger.info(f"Found {len(items_to_process)} new bills to process")
        
        # Define processor function
        def process_bill(params: Dict) -> Dict:
            item = params["item"]
            bill_id = item["id"]
            bill_data = item["data"]
            
            # Save bill data
            output_file = self.output_dir / f"{tracker_name}_{bill_id}.json"
            with open(output_file, 'w') as f:
                json.dump(bill_data, f, indent=2)
            
            # Mark as processed
            tracker.add_item(bill_id, {"processed_at": datetime.utcnow().isoformat()})
            
            return {"bill_id": bill_id, "saved_to": str(output_file)}
        
        # Process with workers
        results = self.coordinator.ingest_collection(
            tracker_name,
            items_to_process,
            process_bill
        )
        
        # Return statistics
        successful = sum(1 for r in results if r.success)
        return {
            "total_items": len(items_to_process),
            "successful": successful,
            "failed": len(results) - successful,
            "tracker": tracker_name
        }
    
    def ingest_govinfo_collection(self, collection_code: str, start_date: str,
                                  end_date: Optional[str] = None,
                                  max_items: Optional[int] = None) -> Dict[str, Any]:
        """
        Ingest a collection from api.govinfo.gov.
        
        Args:
            collection_code: Collection code (e.g., 'BILLS')
            start_date: Start date (ISO format)
            end_date: End date (optional)
            max_items: Maximum items to retrieve
            
        Returns:
            Dictionary with ingestion statistics
        """
        if not self.govinfo_client:
            raise ValueError("GovInfo API key not configured")
        
        logger.info(f"Starting GovInfo collection ingestion: {collection_code}")
        
        # Get tracker
        tracker_name = f"govinfo_{collection_code}_{start_date}"
        tracker = self._get_tracker(tracker_name)
        
        # Collect items
        items_to_process = []
        for package in self.govinfo_client.get_collection_by_date(
            collection_code, start_date, end_date, max_items
        ):
            package_id = package.get('packageId', f"pkg_{len(items_to_process)}")
            
            # Check if already processed
            if tracker.has_item(package_id):
                logger.debug(f"Skipping already processed package: {package_id}")
                continue
            
            items_to_process.append({
                "id": package_id,
                "data": package
            })
        
        logger.info(f"Found {len(items_to_process)} new packages to process")
        
        # Define processor function
        def process_package(params: Dict) -> Dict:
            item = params["item"]
            package_id = item["id"]
            package_data = item["data"]
            
            # Save package data
            output_file = self.output_dir / f"{tracker_name}_{package_id}.json"
            with open(output_file, 'w') as f:
                json.dump(package_data, f, indent=2)
            
            # Mark as processed
            tracker.add_item(package_id, {"processed_at": datetime.utcnow().isoformat()})
            
            return {"package_id": package_id, "saved_to": str(output_file)}
        
        # Process with workers
        results = self.coordinator.ingest_collection(
            tracker_name,
            items_to_process,
            process_package
        )
        
        # Return statistics
        successful = sum(1 for r in results if r.success)
        return {
            "total_items": len(items_to_process),
            "successful": successful,
            "failed": len(results) - successful,
            "tracker": tracker_name
        }
    
    def ingest_bulkdata_collection(self, collection: str, path: str = "",
                                   max_depth: int = 3) -> Dict[str, Any]:
        """
        Ingest bulk data from govinfo.gov/bulkdata.
        
        Args:
            collection: Collection name (e.g., 'BILLS', 'CFR')
            path: Subpath within collection
            max_depth: Maximum directory depth to traverse
            
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"Starting bulk data ingestion: {collection}/{path}")
        
        # Get tracker
        tracker_name = f"bulkdata_{collection}"
        tracker = self._get_tracker(tracker_name)
        
        # Recursively collect files
        def collect_files(current_path: str, depth: int = 0) -> List[Dict]:
            if depth > max_depth:
                return []
            
            files = []
            try:
                items = self.bulkdata_client.list_directory(f"{collection}/{current_path}")
                
                for item in items:
                    item_name = item.get('name', '')
                    item_type = item.get('type', '')
                    
                    if item_type == 'file':
                        file_url = item.get('url', '')
                        if file_url and not tracker.has_item(file_url):
                            files.append({
                                "id": file_url,
                                "url": file_url,
                                "name": item_name,
                                "path": current_path
                            })
                    elif item_type == 'directory':
                        # Recurse into subdirectory
                        subpath = f"{current_path}/{item_name}" if current_path else item_name
                        files.extend(collect_files(subpath, depth + 1))
            
            except Exception as e:
                logger.error(f"Error collecting files from {current_path}: {e}")
            
            return files
        
        items_to_process = collect_files(path)
        logger.info(f"Found {len(items_to_process)} new files to download")
        
        # Define processor function
        def download_file(params: Dict) -> Dict:
            item = params["item"]
            file_url = item["url"]
            file_name = item["name"]
            
            # Determine output path
            output_file = self.output_dir / collection / item["path"] / file_name
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            success = self.bulkdata_client.download_file(file_url, str(output_file))
            
            if success:
                # Mark as processed
                tracker.add_item(file_url, {
                    "downloaded_at": datetime.utcnow().isoformat(),
                    "local_path": str(output_file)
                })
                return {"file_url": file_url, "saved_to": str(output_file)}
            else:
                raise Exception(f"Failed to download {file_url}")
        
        # Process with workers
        results = self.coordinator.ingest_collection(
            tracker_name,
            items_to_process,
            download_file
        )
        
        # Return statistics
        successful = sum(1 for r in results if r.success)
        return {
            "total_items": len(items_to_process),
            "successful": successful,
            "failed": len(results) - successful,
            "tracker": tracker_name
        }
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall statistics for all operations."""
        return {
            "rate_limiters": self.rate_limiter_manager.get_all_stats(),
            "trackers": self.tracker_manager.get_all_stats(),
            "workers": self.worker_pool.get_stats(),
            "total_ingested": self.coordinator.get_total_ingested()
        }
