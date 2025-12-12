"""
API Client Implementation

This module provides client classes for interacting with api.congress.gov 
and govinfo.gov APIs with built-in rate limiting and pagination support.
"""

import requests
import time
from typing import Dict, List, Optional, Generator, Any
from urllib.parse import urljoin
import logging

from rate_limiter import RateLimiter
from data_tracker import DataTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIClient:
    """Base API client with rate limiting and pagination support."""
    
    def __init__(self, base_url: str, api_key: Optional[str], 
                 rate_limiter: RateLimiter):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API
            api_key: API key for authentication (if required)
            rate_limiter: Rate limiter instance
        """
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limiter = rate_limiter
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None,
                     headers: Optional[Dict] = None) -> requests.Response:
        """
        Make an HTTP request with rate limiting.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            headers: HTTP headers
            
        Returns:
            Response object
        """
        # Wait for rate limiter
        wait_time = self.rate_limiter.wait_if_needed()
        if wait_time > 0:
            logger.info(f"Rate limited: waited {wait_time:.2f}s")
        
        # Prepare request
        url = urljoin(self.base_url, endpoint)
        params = params or {}
        headers = headers or {}
        
        # Add API key if available
        if self.api_key:
            params['api_key'] = self.api_key
        
        # Make request
        response = self.session.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        return response
    
    def get_json(self, endpoint: str, params: Optional[Dict] = None,
                headers: Optional[Dict] = None) -> Dict:
        """
        Make a GET request and return JSON response.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            headers: HTTP headers
            
        Returns:
            JSON response as dictionary
        """
        response = self._make_request(endpoint, params, headers)
        return response.json()
    
    def paginate(self, endpoint: str, params: Optional[Dict] = None,
                offset_param: str = "offset", limit_param: str = "limit",
                max_limit: int = 250, 
                max_items: Optional[int] = None) -> Generator[Dict, None, None]:
        """
        Paginate through API results.
        
        Args:
            endpoint: API endpoint path
            params: Base query parameters
            offset_param: Name of offset parameter
            limit_param: Name of limit parameter
            max_limit: Maximum items per page
            max_items: Maximum total items to retrieve (None for all)
            
        Yields:
            Individual items from paginated results
        """
        params = params or {}
        offset = 0
        total_retrieved = 0
        
        while True:
            # Set pagination parameters
            params[offset_param] = offset
            params[limit_param] = max_limit
            
            # Make request
            try:
                data = self.get_json(endpoint, params)
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error during pagination: {e}")
                break
            
            # Extract items (implementation depends on API response structure)
            items = self._extract_items(data)
            
            if not items:
                break
            
            # Yield items
            for item in items:
                if max_items and total_retrieved >= max_items:
                    return
                yield item
                total_retrieved += 1
            
            # Check if we've retrieved all items
            if len(items) < max_limit:
                break
            
            offset += len(items)
    
    def _extract_items(self, data: Dict) -> List[Dict]:
        """
        Extract items from API response.
        Override in subclasses for specific API formats.
        
        Args:
            data: API response data
            
        Returns:
            List of items
        """
        # Default implementation - override in subclasses
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'results' in data:
            return data['results']
        return []


class CongressAPIClient(APIClient):
    """Client for api.congress.gov API."""
    
    def __init__(self, api_key: str, rate_limiter: RateLimiter):
        """
        Initialize Congress API client.
        
        Args:
            api_key: API key for api.congress.gov
            rate_limiter: Rate limiter instance
        """
        super().__init__(
            base_url="https://api.congress.gov/v3",
            api_key=api_key,
            rate_limiter=rate_limiter
        )
    
    def _extract_items(self, data: Dict) -> List[Dict]:
        """Extract items from Congress API response."""
        # Congress API typically returns data in a nested structure
        if isinstance(data, dict):
            # Try common response structures
            for key in ['bills', 'members', 'amendments', 'laws', 'nominations']:
                if key in data:
                    return data[key]
            # Generic fallback
            if 'results' in data:
                return data['results']
        return []
    
    def get_bills(self, congress: Optional[int] = None, 
                 bill_type: Optional[str] = None,
                 max_items: Optional[int] = None) -> Generator[Dict, None, None]:
        """
        Get bills with pagination.
        
        Args:
            congress: Congress number (e.g., 118)
            bill_type: Bill type (e.g., 'hr', 's')
            max_items: Maximum items to retrieve
            
        Yields:
            Bill data dictionaries
        """
        endpoint = "/bill"
        if congress:
            endpoint = f"/bill/{congress}"
            if bill_type:
                endpoint = f"/bill/{congress}/{bill_type}"
        
        yield from self.paginate(endpoint, max_items=max_items)
    
    def get_amendments(self, congress: Optional[int] = None,
                      max_items: Optional[int] = None) -> Generator[Dict, None, None]:
        """Get amendments with pagination."""
        endpoint = "/amendment"
        if congress:
            endpoint = f"/amendment/{congress}"
        
        yield from self.paginate(endpoint, max_items=max_items)
    
    def get_members(self, congress: Optional[int] = None,
                   max_items: Optional[int] = None) -> Generator[Dict, None, None]:
        """Get members with pagination."""
        endpoint = "/member"
        if congress:
            endpoint = f"/member/congress/{congress}"
        
        yield from self.paginate(endpoint, max_items=max_items)


class GovInfoAPIClient(APIClient):
    """Client for api.govinfo.gov API."""
    
    def __init__(self, api_key: str, rate_limiter: RateLimiter):
        """
        Initialize GovInfo API client.
        
        Args:
            api_key: API key for api.govinfo.gov
            rate_limiter: Rate limiter instance
        """
        super().__init__(
            base_url="https://api.govinfo.gov",
            api_key=api_key,
            rate_limiter=rate_limiter
        )
    
    def _extract_items(self, data: Dict) -> List[Dict]:
        """Extract items from GovInfo API response."""
        if isinstance(data, dict):
            # Check for common response structures
            if 'packages' in data:
                return data['packages']
            elif 'results' in data:
                return data['results']
            elif 'items' in data:
                return data['items']
        return []
    
    def get_collections(self) -> List[Dict]:
        """Get list of all collections."""
        data = self.get_json("/collections")
        return data.get('collections', [])
    
    def get_collection_by_date(self, collection_code: str, start_date: str,
                              end_date: Optional[str] = None,
                              max_items: Optional[int] = None) -> Generator[Dict, None, None]:
        """
        Get collection documents by date range.
        
        Args:
            collection_code: Collection code (e.g., 'BILLS')
            start_date: Start date (ISO format)
            end_date: End date (optional)
            max_items: Maximum items to retrieve
            
        Yields:
            Package data dictionaries
        """
        endpoint = f"/collections/{collection_code}/{start_date}"
        if end_date:
            endpoint += f"/{end_date}"
        
        yield from self.paginate(
            endpoint, 
            offset_param="offset",
            limit_param="pageSize",
            max_limit=1000,
            max_items=max_items
        )
    
    def get_package_summary(self, package_id: str) -> Dict:
        """Get package summary."""
        return self.get_json(f"/packages/{package_id}/summary")


class BulkDataClient:
    """Client for govinfo.gov bulk data downloads."""
    
    def __init__(self, rate_limiter: RateLimiter):
        """
        Initialize bulk data client.
        
        Args:
            rate_limiter: Rate limiter instance
        """
        self.base_url = "https://www.govinfo.gov/bulkdata"
        self.rate_limiter = rate_limiter
        self.session = requests.Session()
    
    def list_directory(self, path: str, format: str = "json") -> List[Dict]:
        """
        List contents of a bulk data directory.
        
        Args:
            path: Path relative to bulkdata root
            format: Response format ('json' or 'xml')
            
        Returns:
            List of files/directories
        """
        # Wait for rate limiter
        wait_time = self.rate_limiter.wait_if_needed()
        if wait_time > 0:
            logger.info(f"Rate limited: waited {wait_time:.2f}s")
        
        url = f"{self.base_url}/{format}/{path}"
        headers = {'Accept': f'application/{format}'}
        
        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        
        if format == "json":
            data = response.json()
            # Extract files/folders from response
            if isinstance(data, dict):
                return data.get('files', []) + data.get('folders', [])
        
        return []
    
    def download_file(self, url: str, output_path: str) -> bool:
        """
        Download a file from bulk data.
        
        Args:
            url: URL of file to download
            output_path: Local path to save file
            
        Returns:
            True if successful
        """
        # Wait for rate limiter
        wait_time = self.rate_limiter.wait_if_needed()
        if wait_time > 0:
            logger.info(f"Rate limited: waited {wait_time:.2f}s")
        
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return False
