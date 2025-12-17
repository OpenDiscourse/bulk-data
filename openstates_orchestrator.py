"""
OpenStates Data Ingestion Orchestrator

Main orchestration module for OpenStates bulk data ingestion with:
- 20 concurrent workers for parallel processing
- Comprehensive progress tracking and logging
- PostgreSQL database integration
- Rate limiting and error handling
- Support for incremental updates
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path
from tqdm import tqdm

from openstates_client import OpenStatesClient, OpenStatesScraperRunner
from openstates_db import OpenStatesDatabase
from rate_limiter import RateLimiter, RateLimiterManager
from worker_pool import WorkerPool, Task, DistributedIngestionCoordinator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OpenStatesOrchestrator:
    """
    Orchestrates OpenStates bulk data ingestion with parallel processing.
    
    Features:
    - 20 concurrent workers for maximum throughput
    - Comprehensive progress tracking with tqdm
    - PostgreSQL database storage
    - Rate limiting to respect API limits
    - Incremental updates support
    - Error handling and logging
    
    Attributes:
        api_client: OpenStates API client
        database: PostgreSQL database interface
        worker_pool: Pool of 20 workers
        coordinator: Task coordination and distribution
        rate_limiter: API rate limiter
    """
    
    def __init__(self, 
                 api_key: str,
                 database_url: str,
                 num_workers: int = 20,
                 rate_limit_per_hour: int = 5000):
        """
        Initialize the orchestrator.
        
        Args:
            api_key: OpenStates API key
            database_url: PostgreSQL connection string
            num_workers: Number of parallel workers (default: 20)
            rate_limit_per_hour: API rate limit per hour
        """
        # Initialize rate limiter (OpenStates doesn't publish official limits, 
        # using conservative estimate)
        self.rate_limiter_manager = RateLimiterManager()
        self.rate_limiter = self.rate_limiter_manager.get_or_create(
            "openstates_api",
            requests_per_hour=rate_limit_per_hour,
            requests_per_minute=rate_limit_per_hour // 60
        )
        
        # Initialize API client
        self.api_client = OpenStatesClient(api_key, self.rate_limiter)
        
        # Initialize database
        self.database = OpenStatesDatabase(database_url)
        
        # Initialize worker pool with 20 workers
        self.worker_pool = WorkerPool(num_workers=num_workers)
        self.coordinator = DistributedIngestionCoordinator(self.worker_pool)
        
        # Initialize scraper runner
        self.scraper_runner = OpenStatesScraperRunner()
        
        logger.info(f"OpenStates Orchestrator initialized with {num_workers} workers")
    
    def setup_database(self):
        """
        Create database tables if they don't exist.
        """
        logger.info("Setting up database tables")
        self.database.create_tables()
        logger.info("Database setup complete")
    
    # Jurisdiction and session ingestion
    
    def ingest_all_jurisdictions(self) -> Dict[str, Any]:
        """
        Ingest all U.S. jurisdictions (states and territories).
        
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info("Starting jurisdiction ingestion")
        log_id = self.database.start_ingestion_log("jurisdictions")
        
        try:
            jurisdictions = self.api_client.get_jurisdictions()
            logger.info(f"Found {len(jurisdictions)} jurisdictions")
            
            processed = 0
            failed = 0
            
            for jurisdiction in tqdm(jurisdictions, desc="Ingesting jurisdictions"):
                try:
                    self.database.upsert_jurisdiction(jurisdiction)
                    
                    # Also ingest sessions for this jurisdiction
                    if 'legislative_sessions' in jurisdiction:
                        for session in jurisdiction['legislative_sessions']:
                            self.database.upsert_legislative_session(
                                session, 
                                jurisdiction['id']
                            )
                    
                    processed += 1
                except Exception as e:
                    logger.error(f"Failed to ingest jurisdiction {jurisdiction.get('id')}: {e}")
                    failed += 1
            
            self.database.update_ingestion_log(
                log_id, 
                items_processed=processed,
                items_failed=failed,
                status='completed'
            )
            
            return {
                "total": len(jurisdictions),
                "processed": processed,
                "failed": failed,
                "log_id": log_id
            }
            
        except Exception as e:
            logger.error(f"Jurisdiction ingestion failed: {e}")
            self.database.update_ingestion_log(
                log_id,
                status='failed',
                error_message=str(e)
            )
            raise
    
    # People (Legislators) ingestion
    
    def ingest_people(self, jurisdiction: Optional[str] = None,
                     max_items: Optional[int] = None) -> Dict[str, Any]:
        """
        Ingest legislators (people) with parallel workers.
        
        Args:
            jurisdiction: Specific jurisdiction to ingest (None for all)
            max_items: Maximum items to ingest (None for all)
            
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"Starting people ingestion for jurisdiction: {jurisdiction or 'all'}")
        log_id = self.database.start_ingestion_log(
            "people",
            jurisdiction_id=jurisdiction
        )
        
        try:
            # Collect people to process
            people_list = []
            logger.info("Collecting people from API...")
            
            for person in tqdm(
                self.api_client.search_people(jurisdiction=jurisdiction, max_items=max_items),
                desc="Collecting people"
            ):
                people_list.append(person)
            
            logger.info(f"Collected {len(people_list)} people, starting parallel ingestion")
            
            # Define processor function
            def process_person(params: Dict) -> Dict:
                person_data = params["person"]
                person_id = person_data['id']
                
                try:
                    # Get full person details if not already included
                    if 'current_memberships' not in person_data:
                        person_data = self.api_client.get_person(person_id)
                    
                    # Upsert to database
                    self.database.upsert_person(person_data)
                    
                    return {"person_id": person_id, "status": "success"}
                    
                except Exception as e:
                    logger.error(f"Failed to process person {person_id}: {e}")
                    raise
            
            # Register handler
            self.worker_pool.register_handler("process_person", process_person)
            
            # Create tasks
            items_to_process = [{"person": p} for p in people_list]
            
            # Process with workers
            results = self.coordinator.ingest_collection(
                "people",
                items_to_process,
                process_person
            )
            
            # Calculate statistics
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            self.database.update_ingestion_log(
                log_id,
                items_processed=successful,
                items_failed=failed,
                status='completed'
            )
            
            return {
                "total": len(people_list),
                "processed": successful,
                "failed": failed,
                "log_id": log_id
            }
            
        except Exception as e:
            logger.error(f"People ingestion failed: {e}")
            self.database.update_ingestion_log(
                log_id,
                status='failed',
                error_message=str(e)
            )
            raise
    
    # Bill ingestion (with full details)
    
    def ingest_bills(self, jurisdiction: str, session: str,
                    updated_since: Optional[str] = None,
                    max_items: Optional[int] = None) -> Dict[str, Any]:
        """
        Ingest bills with full details using parallel workers.
        
        Args:
            jurisdiction: Jurisdiction abbreviation (e.g., 'NC')
            session: Legislative session identifier
            updated_since: ISO date for incremental updates (optional)
            max_items: Maximum items to ingest (None for all)
            
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"Starting bill ingestion for {jurisdiction} {session}")
        log_id = self.database.start_ingestion_log(
            "bills",
            jurisdiction_id=jurisdiction,
            session_identifier=session,
            metadata={"updated_since": updated_since}
        )
        
        try:
            # Get session ID from database
            with self.database.get_session() as db_session:
                from openstates_models import LegislativeSession, Jurisdiction
                
                # Get jurisdiction
                jur = db_session.query(Jurisdiction).filter_by(abbreviation=jurisdiction).first()
                if not jur:
                    raise ValueError(f"Jurisdiction {jurisdiction} not found in database")
                
                # Get or create session
                session_obj = db_session.query(LegislativeSession).filter_by(
                    jurisdiction_id=jur.id,
                    identifier=session
                ).first()
                
                if not session_obj:
                    # Create session
                    session_obj = LegislativeSession(
                        identifier=session,
                        name=session,
                        jurisdiction_id=jur.id
                    )
                    db_session.add(session_obj)
                    db_session.commit()
                
                session_id = session_obj.id
            
            # Collect bills to process
            bills_list = []
            logger.info("Collecting bills from API...")
            
            for bill in tqdm(
                self.api_client.search_bills(
                    jurisdiction=jurisdiction,
                    session=session,
                    updated_since=updated_since,
                    max_items=max_items
                ),
                desc="Collecting bills"
            ):
                bills_list.append(bill)
            
            logger.info(f"Collected {len(bills_list)} bills, starting parallel ingestion")
            
            # Define processor function
            def process_bill(params: Dict) -> Dict:
                bill_summary = params["bill"]
                bill_id = bill_summary['id']
                
                try:
                    # Get full bill details including votes, sponsors, etc.
                    bill_data = self.api_client.get_bill(
                        bill_id,
                        include=['sponsors', 'votes', 'versions', 'documents', 'sources']
                    )
                    
                    # Upsert bill to database
                    self.database.upsert_bill(bill_data, params["session_id"])
                    
                    # Process votes
                    for vote in bill_data.get('votes', []):
                        self.database.upsert_vote(vote, bill_id)
                    
                    return {"bill_id": bill_id, "status": "success"}
                    
                except Exception as e:
                    logger.error(f"Failed to process bill {bill_id}: {e}")
                    raise
            
            # Register handler
            self.worker_pool.register_handler("process_bill", process_bill)
            
            # Create tasks
            items_to_process = [{"bill": b, "session_id": session_id} for b in bills_list]
            
            # Process with workers
            results = self.coordinator.ingest_collection(
                f"bills_{jurisdiction}_{session}",
                items_to_process,
                process_bill
            )
            
            # Calculate statistics
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            self.database.update_ingestion_log(
                log_id,
                items_processed=successful,
                items_failed=failed,
                status='completed'
            )
            
            return {
                "total": len(bills_list),
                "processed": successful,
                "failed": failed,
                "log_id": log_id
            }
            
        except Exception as e:
            logger.error(f"Bill ingestion failed: {e}")
            self.database.update_ingestion_log(
                log_id,
                status='failed',
                error_message=str(e)
            )
            raise
    
    # Bulk ingestion for all jurisdictions
    
    def ingest_all_bills(self, updated_since: Optional[str] = None,
                        max_per_jurisdiction: Optional[int] = None) -> Dict[str, Any]:
        """
        Ingest bills from all jurisdictions and their most recent sessions.
        
        Args:
            updated_since: ISO date for incremental updates (optional)
            max_per_jurisdiction: Maximum bills per jurisdiction (None for all)
            
        Returns:
            Dictionary with aggregated statistics
        """
        logger.info("Starting bulk ingestion for all jurisdictions")
        
        # Get all jurisdictions from database
        with self.database.get_session() as db_session:
            from openstates_models import Jurisdiction, LegislativeSession
            
            jurisdictions = db_session.query(Jurisdiction).all()
            
            results = {
                "jurisdictions_processed": 0,
                "total_bills": 0,
                "total_processed": 0,
                "total_failed": 0,
                "details": []
            }
            
            for jur in tqdm(jurisdictions, desc="Processing jurisdictions"):
                # Get most recent session
                recent_session = db_session.query(LegislativeSession).filter_by(
                    jurisdiction_id=jur.id
                ).order_by(LegislativeSession.identifier.desc()).first()
                
                if not recent_session:
                    logger.warning(f"No session found for {jur.abbreviation}")
                    continue
                
                try:
                    logger.info(f"Ingesting bills for {jur.abbreviation} - {recent_session.identifier}")
                    
                    result = self.ingest_bills(
                        jurisdiction=jur.abbreviation,
                        session=recent_session.identifier,
                        updated_since=updated_since,
                        max_items=max_per_jurisdiction
                    )
                    
                    results["jurisdictions_processed"] += 1
                    results["total_bills"] += result["total"]
                    results["total_processed"] += result["processed"]
                    results["total_failed"] += result["failed"]
                    results["details"].append({
                        "jurisdiction": jur.abbreviation,
                        "session": recent_session.identifier,
                        **result
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to ingest bills for {jur.abbreviation}: {e}")
                    results["details"].append({
                        "jurisdiction": jur.abbreviation,
                        "session": recent_session.identifier if recent_session else None,
                        "error": str(e)
                    })
            
            return results
    
    # Statistics and monitoring
    
    def get_ingestion_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about ingestion operations.
        
        Returns:
            Dictionary with statistics from all components
        """
        with self.database.get_session() as session:
            from openstates_models import (
                Jurisdiction, LegislativeSession, Person, 
                Bill, Vote, Committee
            )
            
            stats = {
                "database": {
                    "jurisdictions": session.query(Jurisdiction).count(),
                    "sessions": session.query(LegislativeSession).count(),
                    "people": session.query(Person).count(),
                    "bills": session.query(Bill).count(),
                    "votes": session.query(Vote).count(),
                    "committees": session.query(Committee).count()
                },
                "rate_limiter": self.rate_limiter_manager.get_all_stats(),
                "workers": self.worker_pool.get_stats(),
                "total_ingested": self.coordinator.get_total_ingested(),
                "recent_logs": self.database.get_recent_ingestion_logs(10)
            }
            
            return stats
