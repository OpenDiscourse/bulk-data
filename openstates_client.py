"""
OpenStates API Client

Provides a client for interacting with the OpenStates v3 API with
rate limiting, pagination, and comprehensive endpoint coverage.
"""

import requests
import logging
from typing import Dict, List, Optional, Generator, Any
from urllib.parse import urljoin
from datetime import datetime

from rate_limiter import RateLimiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenStatesClient:
    """
    Client for OpenStates v3 API.
    
    Provides methods for accessing bills, people, votes, committees, and other
    legislative data from all U.S. states and territories.
    
    Attributes:
        base_url: API base URL
        api_key: OpenStates API key
        rate_limiter: Rate limiter for API requests
        session: Requests session for connection pooling
    """
    
    def __init__(self, api_key: str, rate_limiter: RateLimiter):
        """
        Initialize OpenStates API client.
        
        Args:
            api_key: OpenStates API key
            rate_limiter: Rate limiter instance
        """
        self.base_url = "https://v3.openstates.org"
        self.api_key = api_key
        self.rate_limiter = rate_limiter
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-KEY': api_key,
            'Accept': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """
        Make an HTTP request with rate limiting.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.HTTPError: On HTTP errors
        """
        # Wait for rate limiter
        wait_time = self.rate_limiter.wait_if_needed()
        if wait_time > 0:
            logger.debug(f"Rate limited: waited {wait_time:.2f}s")
        
        # Prepare request
        url = urljoin(self.base_url, endpoint)
        params = params or {}
        
        # Make request
        logger.debug(f"GET {url} with params {params}")
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        return response
    
    def _get_json(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a GET request and return JSON response.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        response = self._make_request(endpoint, params)
        return response.json()
    
    def _paginate(self, endpoint: str, params: Optional[Dict] = None,
                  per_page: int = 100, max_items: Optional[int] = None) -> Generator[Dict, None, None]:
        """
        Paginate through API results.
        
        Args:
            endpoint: API endpoint path
            params: Base query parameters
            per_page: Items per page (max 100)
            max_items: Maximum total items to retrieve (None for all)
            
        Yields:
            Individual items from paginated results
        """
        params = params or {}
        page = 1
        total_retrieved = 0
        
        while True:
            # Set pagination parameters
            params['page'] = page
            params['per_page'] = min(per_page, 100)  # API limit is 100
            
            # Make request
            try:
                data = self._get_json(endpoint, params)
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error during pagination: {e}")
                break
            
            # Extract results
            results = data.get('results', [])
            
            if not results:
                break
            
            # Yield items
            for item in results:
                if max_items and total_retrieved >= max_items:
                    return
                yield item
                total_retrieved += 1
            
            # Check pagination info
            pagination = data.get('pagination', {})
            if page >= pagination.get('max_page', page):
                break
            
            page += 1
    
    # Jurisdiction methods
    
    def get_jurisdictions(self) -> List[Dict]:
        """
        Get all jurisdictions (states and territories).
        
        Returns:
            List of jurisdiction dictionaries
        """
        logger.info("Fetching jurisdictions")
        data = self._get_json("/jurisdictions")
        return data.get('results', [])
    
    def get_jurisdiction(self, jurisdiction_id: str) -> Dict:
        """
        Get a specific jurisdiction by ID.
        
        Args:
            jurisdiction_id: Jurisdiction ID (e.g., 'ocd-jurisdiction/country:us/state:nc')
            
        Returns:
            Jurisdiction dictionary
        """
        logger.info(f"Fetching jurisdiction: {jurisdiction_id}")
        return self._get_json(f"/jurisdictions/{jurisdiction_id}")
    
    # Bill methods
    
    def search_bills(self, jurisdiction: Optional[str] = None, 
                    session: Optional[str] = None,
                    chamber: Optional[str] = None,
                    classification: Optional[str] = None,
                    subject: Optional[str] = None,
                    updated_since: Optional[str] = None,
                    query: Optional[str] = None,
                    per_page: int = 100,
                    max_items: Optional[int] = None) -> Generator[Dict, None, None]:
        """
        Search and paginate through bills.
        
        Args:
            jurisdiction: Jurisdiction abbreviation (e.g., 'NC')
            session: Legislative session identifier
            chamber: Chamber (upper, lower)
            classification: Bill classification (bill, resolution, etc.)
            subject: Subject area
            updated_since: ISO date string for incremental updates
            query: Search query string
            per_page: Items per page
            max_items: Maximum items to retrieve
            
        Yields:
            Bill dictionaries
        """
        params = {}
        if jurisdiction:
            params['jurisdiction'] = jurisdiction
        if session:
            params['session'] = session
        if chamber:
            params['chamber'] = chamber
        if classification:
            params['classification'] = classification
        if subject:
            params['subject'] = subject
        if updated_since:
            params['updated_since'] = updated_since
        if query:
            params['q'] = query
        
        logger.info(f"Searching bills with params: {params}")
        yield from self._paginate("/bills", params, per_page, max_items)
    
    def get_bill(self, bill_id: str, include: Optional[List[str]] = None) -> Dict:
        """
        Get a specific bill by ID.
        
        Args:
            bill_id: Bill ID (OCD format or jurisdiction/session/identifier)
            include: Optional list of related data to include 
                    (sponsors, votes, versions, documents, sources)
            
        Returns:
            Bill dictionary with full details
        """
        params = {}
        if include:
            params['include'] = ','.join(include)
        
        logger.info(f"Fetching bill: {bill_id}")
        return self._get_json(f"/bills/{bill_id}", params)
    
    # People methods
    
    def search_people(self, jurisdiction: Optional[str] = None,
                     name: Optional[str] = None,
                     district: Optional[str] = None,
                     party: Optional[str] = None,
                     chamber: Optional[str] = None,
                     per_page: int = 100,
                     max_items: Optional[int] = None) -> Generator[Dict, None, None]:
        """
        Search and paginate through legislators.
        
        Args:
            jurisdiction: Jurisdiction abbreviation (e.g., 'NC')
            name: Person name to search
            district: Legislative district
            party: Political party
            chamber: Chamber (upper, lower)
            per_page: Items per page
            max_items: Maximum items to retrieve
            
        Yields:
            Person dictionaries
        """
        params = {}
        if jurisdiction:
            params['jurisdiction'] = jurisdiction
        if name:
            params['name'] = name
        if district:
            params['district'] = district
        if party:
            params['party'] = party
        if chamber:
            params['chamber'] = chamber
        
        logger.info(f"Searching people with params: {params}")
        yield from self._paginate("/people", params, per_page, max_items)
    
    def get_person(self, person_id: str) -> Dict:
        """
        Get a specific person by ID.
        
        Args:
            person_id: Person ID (OCD format)
            
        Returns:
            Person dictionary with full details
        """
        logger.info(f"Fetching person: {person_id}")
        return self._get_json(f"/people/{person_id}")
    
    def get_people_by_location(self, latitude: float, longitude: float) -> List[Dict]:
        """
        Get legislators representing a geographic location.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            List of person dictionaries
        """
        params = {
            'lat': latitude,
            'lng': longitude
        }
        logger.info(f"Fetching people at location: {latitude}, {longitude}")
        data = self._get_json("/people.geo", params)
        return data.get('results', [])
    
    # Vote methods (included in bill data, but can be accessed independently)
    
    def get_vote(self, vote_id: str) -> Dict:
        """
        Get a specific vote by ID.
        
        Args:
            vote_id: Vote ID (OCD format)
            
        Returns:
            Vote dictionary with full details
        """
        logger.info(f"Fetching vote: {vote_id}")
        return self._get_json(f"/votes/{vote_id}")
    
    # Statistics and bulk operations
    
    def get_bill_count(self, jurisdiction: str, session: str) -> int:
        """
        Get count of bills for a jurisdiction and session.
        
        Args:
            jurisdiction: Jurisdiction abbreviation
            session: Legislative session identifier
            
        Returns:
            Count of bills
        """
        params = {
            'jurisdiction': jurisdiction,
            'session': session,
            'per_page': 1
        }
        data = self._get_json("/bills", params)
        pagination = data.get('pagination', {})
        return pagination.get('total_items', 0)
    
    def get_jurisdiction_sessions(self, jurisdiction: str) -> List[Dict]:
        """
        Get legislative sessions for a jurisdiction.
        
        Args:
            jurisdiction: Jurisdiction abbreviation
            
        Returns:
            List of session dictionaries
        """
        # Sessions are included in jurisdiction data
        jurisdiction_data = self._get_json(f"/jurisdictions/{jurisdiction}")
        return jurisdiction_data.get('legislative_sessions', [])


class OpenStatesScraperRunner:
    """
    Runner for executing OpenStates scrapers from the openstates-scrapers repository.
    
    This class provides methods to run individual scrapers and collect their output.
    Note: Requires openstates-scrapers to be installed or available in the environment.
    """
    
    def __init__(self):
        """Initialize the scraper runner."""
        self.logger = logging.getLogger(__name__ + ".ScraperRunner")
    
    def run_scraper(self, state: str, module: str = "bills", 
                   session: Optional[str] = None,
                   fastmode: bool = True) -> Dict[str, Any]:
        """
        Run an OpenStates scraper for a specific state and module.
        
        Args:
            state: State abbreviation (e.g., 'nc', 'ca')
            module: Scraper module to run (bills, people, votes, committees)
            session: Specific session to scrape (optional)
            fastmode: Whether to run in fast mode (skip unchanged data)
            
        Returns:
            Dictionary with scraper results and statistics
            
        Note:
            This requires the openstates-scrapers package to be properly configured.
            Results may need to be imported into the database separately.
        """
        self.logger.info(f"Running scraper for {state}/{module}")
        
        # This is a placeholder - actual implementation would use the 
        # openstates-scrapers CLI or import the scraper modules directly
        # and execute them programmatically
        
        result = {
            'state': state,
            'module': module,
            'session': session,
            'status': 'not_implemented',
            'message': 'Scraper execution requires openstates-scrapers installation'
        }
        
        self.logger.warning("Scraper runner not fully implemented - requires openstates-scrapers setup")
        return result
