"""
OpenStates Database Layer

Handles PostgreSQL database connections and data ingestion for OpenStates data.
Provides methods for inserting and updating bills, people, votes, and related entities.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert

from openstates_models import (
    Base, Jurisdiction, LegislativeSession, Person, Bill, 
    BillSponsorship, BillVersion, BillDocument, Vote, VoteRecord,
    Committee, IngestionLog
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenStatesDatabase:
    """
    Database interface for OpenStates data ingestion.
    
    Handles connection management, schema creation, and CRUD operations
    for all OpenStates entities with upsert logic for updates.
    
    Attributes:
        engine: SQLAlchemy engine
        SessionLocal: SQLAlchemy session factory
    """
    
    def __init__(self, database_url: str, echo: bool = False):
        """
        Initialize database connection.
        
        Args:
            database_url: PostgreSQL connection string 
                         (e.g., 'postgresql://user:pass@localhost/openstates')
            echo: Whether to echo SQL statements (for debugging)
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=echo, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info(f"Database connection established")
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager for database sessions.
        
        Yields:
            SQLAlchemy session
            
        Example:
            with db.get_session() as session:
                session.add(obj)
                session.commit()
        """
        session = self.SessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """
        Create all database tables.
        
        Safe to call multiple times - only creates missing tables.
        """
        logger.info("Creating database tables")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        """
        Drop all database tables.
        
        Warning: This will delete all data!
        """
        logger.warning("Dropping all database tables")
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if table exists
        """
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()
    
    # Jurisdiction methods
    
    def upsert_jurisdiction(self, jurisdiction_data: Dict) -> str:
        """
        Insert or update a jurisdiction.
        
        Args:
            jurisdiction_data: Jurisdiction data from OpenStates API
            
        Returns:
            Jurisdiction ID
        """
        with self.get_session() as session:
            stmt = insert(Jurisdiction).values(
                id=jurisdiction_data['id'],
                name=jurisdiction_data.get('name', ''),
                abbreviation=jurisdiction_data.get('abbreviation', ''),
                classification=jurisdiction_data.get('classification'),
                url=jurisdiction_data.get('url'),
                updated_at=datetime.utcnow()
            ).on_conflict_do_update(
                index_elements=['id'],
                set_={
                    'name': jurisdiction_data.get('name', ''),
                    'abbreviation': jurisdiction_data.get('abbreviation', ''),
                    'classification': jurisdiction_data.get('classification'),
                    'url': jurisdiction_data.get('url'),
                    'updated_at': datetime.utcnow()
                }
            )
            session.execute(stmt)
            session.commit()
            
            logger.debug(f"Upserted jurisdiction: {jurisdiction_data['id']}")
            return jurisdiction_data['id']
    
    def upsert_legislative_session(self, session_data: Dict, jurisdiction_id: str) -> int:
        """
        Insert or update a legislative session.
        
        Args:
            session_data: Session data from OpenStates API
            jurisdiction_id: Parent jurisdiction ID
            
        Returns:
            Session database ID
        """
        with self.get_session() as session:
            # Check if session exists
            existing = session.query(LegislativeSession).filter_by(
                jurisdiction_id=jurisdiction_id,
                identifier=session_data['identifier']
            ).first()
            
            if existing:
                # Update
                existing.name = session_data.get('name', '')
                existing.start_date = self._parse_date(session_data.get('start_date'))
                existing.end_date = self._parse_date(session_data.get('end_date'))
                existing.classification = session_data.get('classification')
                existing.updated_at = datetime.utcnow()
                session.commit()
                logger.debug(f"Updated session: {existing.id}")
                return existing.id
            else:
                # Insert
                new_session = LegislativeSession(
                    identifier=session_data['identifier'],
                    name=session_data.get('name', ''),
                    jurisdiction_id=jurisdiction_id,
                    start_date=self._parse_date(session_data.get('start_date')),
                    end_date=self._parse_date(session_data.get('end_date')),
                    classification=session_data.get('classification')
                )
                session.add(new_session)
                session.commit()
                logger.debug(f"Inserted session: {new_session.id}")
                return new_session.id
    
    # Person methods
    
    def upsert_person(self, person_data: Dict) -> str:
        """
        Insert or update a person (legislator).
        
        Args:
            person_data: Person data from OpenStates API
            
        Returns:
            Person ID
        """
        with self.get_session() as session:
            # Extract party from current memberships
            party = None
            current_role = None
            if 'current_memberships' in person_data and person_data['current_memberships']:
                membership = person_data['current_memberships'][0]
                party = membership.get('party', {}).get('name') if isinstance(membership.get('party'), dict) else membership.get('party')
                org = membership.get('organization', {})
                post = membership.get('post', {})
                if org or post:
                    current_role = f"{org.get('name', '')} - {post.get('label', '')}".strip(' -')
            
            stmt = insert(Person).values(
                id=person_data['id'],
                name=person_data.get('name', ''),
                given_name=person_data.get('given_name'),
                family_name=person_data.get('family_name'),
                email=person_data.get('email'),
                jurisdiction_id=person_data['jurisdiction']['id'],
                party=party,
                current_role=current_role,
                image_url=person_data.get('image'),
                extras=person_data.get('extras'),
                sources=person_data.get('sources'),
                updated_at=datetime.utcnow()
            ).on_conflict_do_update(
                index_elements=['id'],
                set_={
                    'name': person_data.get('name', ''),
                    'given_name': person_data.get('given_name'),
                    'family_name': person_data.get('family_name'),
                    'email': person_data.get('email'),
                    'party': party,
                    'current_role': current_role,
                    'image_url': person_data.get('image'),
                    'extras': person_data.get('extras'),
                    'sources': person_data.get('sources'),
                    'updated_at': datetime.utcnow()
                }
            )
            session.execute(stmt)
            session.commit()
            
            logger.debug(f"Upserted person: {person_data['id']}")
            return person_data['id']
    
    # Bill methods
    
    def upsert_bill(self, bill_data: Dict, session_id: int) -> str:
        """
        Insert or update a bill with all related entities.
        
        Args:
            bill_data: Bill data from OpenStates API (with full details)
            session_id: Legislative session database ID
            
        Returns:
            Bill ID
        """
        with self.get_session() as session:
            # Upsert bill
            stmt = insert(Bill).values(
                id=bill_data['id'],
                identifier=bill_data.get('identifier', ''),
                title=bill_data.get('title', ''),
                classification=bill_data.get('classification', 'bill'),
                subject=bill_data.get('subject', []),
                abstracts=bill_data.get('abstracts', []),
                jurisdiction_id=bill_data['jurisdiction']['id'],
                legislative_session_id=session_id,
                from_organization=bill_data.get('from_organization', {}).get('name'),
                actions=bill_data.get('actions', []),
                extras=bill_data.get('extras'),
                sources=bill_data.get('sources'),
                openstates_updated_at=self._parse_date(bill_data.get('updated_at')),
                updated_at=datetime.utcnow()
            ).on_conflict_do_update(
                index_elements=['id'],
                set_={
                    'identifier': bill_data.get('identifier', ''),
                    'title': bill_data.get('title', ''),
                    'classification': bill_data.get('classification', 'bill'),
                    'subject': bill_data.get('subject', []),
                    'abstracts': bill_data.get('abstracts', []),
                    'from_organization': bill_data.get('from_organization', {}).get('name'),
                    'actions': bill_data.get('actions', []),
                    'extras': bill_data.get('extras'),
                    'sources': bill_data.get('sources'),
                    'openstates_updated_at': self._parse_date(bill_data.get('updated_at')),
                    'updated_at': datetime.utcnow()
                }
            )
            session.execute(stmt)
            
            bill_id = bill_data['id']
            
            # Delete existing related entities (to handle removals)
            session.query(BillSponsorship).filter_by(bill_id=bill_id).delete()
            session.query(BillVersion).filter_by(bill_id=bill_id).delete()
            session.query(BillDocument).filter_by(bill_id=bill_id).delete()
            
            # Insert sponsorships
            for sponsor in bill_data.get('sponsorships', []):
                sponsorship = BillSponsorship(
                    bill_id=bill_id,
                    person_id=sponsor.get('person', {}).get('id') if isinstance(sponsor.get('person'), dict) else None,
                    classification=sponsor.get('classification'),
                    name=sponsor.get('name', ''),
                    entity_type=sponsor.get('entity_type'),
                    primary=sponsor.get('primary', False)
                )
                session.add(sponsorship)
            
            # Insert versions
            for version in bill_data.get('versions', []):
                bill_version = BillVersion(
                    bill_id=bill_id,
                    note=version.get('note'),
                    date=self._parse_date(version.get('date')),
                    links=version.get('links', [])
                )
                session.add(bill_version)
            
            # Insert documents
            for document in bill_data.get('documents', []):
                bill_document = BillDocument(
                    bill_id=bill_id,
                    note=document.get('note'),
                    date=self._parse_date(document.get('date')),
                    links=document.get('links', [])
                )
                session.add(bill_document)
            
            session.commit()
            logger.debug(f"Upserted bill: {bill_id} with related entities")
            return bill_id
    
    # Vote methods
    
    def upsert_vote(self, vote_data: Dict, bill_id: str) -> str:
        """
        Insert or update a vote with individual vote records.
        
        Args:
            vote_data: Vote data from OpenStates API
            bill_id: Parent bill ID
            
        Returns:
            Vote ID
        """
        with self.get_session() as session:
            # Upsert vote
            stmt = insert(Vote).values(
                id=vote_data['id'],
                bill_id=bill_id,
                identifier=vote_data.get('identifier'),
                motion_text=vote_data.get('motion_text'),
                motion_classification=vote_data.get('motion_classification', [None])[0] if vote_data.get('motion_classification') else None,
                start_date=self._parse_date(vote_data.get('start_date')),
                result=vote_data.get('result', ''),
                organization=vote_data.get('organization', {}).get('name'),
                counts=vote_data.get('counts', []),
                sources=vote_data.get('sources'),
                updated_at=datetime.utcnow()
            ).on_conflict_do_update(
                index_elements=['id'],
                set_={
                    'identifier': vote_data.get('identifier'),
                    'motion_text': vote_data.get('motion_text'),
                    'motion_classification': vote_data.get('motion_classification', [None])[0] if vote_data.get('motion_classification') else None,
                    'start_date': self._parse_date(vote_data.get('start_date')),
                    'result': vote_data.get('result', ''),
                    'organization': vote_data.get('organization', {}).get('name'),
                    'counts': vote_data.get('counts', []),
                    'sources': vote_data.get('sources'),
                    'updated_at': datetime.utcnow()
                }
            )
            session.execute(stmt)
            
            vote_id = vote_data['id']
            
            # Delete existing vote records
            session.query(VoteRecord).filter_by(vote_id=vote_id).delete()
            
            # Insert vote records
            for voter in vote_data.get('votes', []):
                vote_record = VoteRecord(
                    vote_id=vote_id,
                    person_id=voter.get('voter', {}).get('id') if isinstance(voter.get('voter'), dict) else None,
                    option=voter.get('option', ''),
                    voter_name=voter.get('voter_name', '') or voter.get('voter', {}).get('name', '')
                )
                session.add(vote_record)
            
            session.commit()
            logger.debug(f"Upserted vote: {vote_id} with vote records")
            return vote_id
    
    # Utility methods
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse ISO date string to datetime.
        
        Args:
            date_str: ISO format date string
            
        Returns:
            datetime object or None
        """
        if not date_str:
            return None
        
        try:
            # Handle various ISO formats
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(date_str)
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse date: {date_str}")
            return None
    
    # Ingestion logging methods
    
    def start_ingestion_log(self, operation_type: str, 
                           jurisdiction_id: Optional[str] = None,
                           session_identifier: Optional[str] = None,
                           metadata: Optional[Dict] = None) -> int:
        """
        Start an ingestion operation log.
        
        Args:
            operation_type: Type of operation (bills, people, votes, etc.)
            jurisdiction_id: Target jurisdiction
            session_identifier: Target session
            metadata: Additional metadata
            
        Returns:
            Log entry ID
        """
        with self.get_session() as session:
            log = IngestionLog(
                operation_type=operation_type,
                jurisdiction_id=jurisdiction_id,
                session_identifier=session_identifier,
                status='running',
                operation_metadata=metadata
            )
            session.add(log)
            session.commit()
            logger.info(f"Started ingestion log: {log.id} for {operation_type}")
            return log.id
    
    def update_ingestion_log(self, log_id: int, 
                            items_processed: int = 0,
                            items_failed: int = 0,
                            status: Optional[str] = None,
                            error_message: Optional[str] = None):
        """
        Update an ingestion operation log.
        
        Args:
            log_id: Log entry ID
            items_processed: Number of items processed
            items_failed: Number of items failed
            status: New status (running, completed, failed)
            error_message: Error details if failed
        """
        with self.get_session() as session:
            log = session.query(IngestionLog).filter_by(id=log_id).first()
            if log:
                log.items_processed += items_processed
                log.items_failed += items_failed
                if status:
                    log.status = status
                if error_message:
                    log.error_message = error_message
                if status in ['completed', 'failed']:
                    log.end_time = datetime.utcnow()
                session.commit()
                logger.debug(f"Updated ingestion log: {log_id}")
    
    def get_recent_ingestion_logs(self, limit: int = 10) -> List[Dict]:
        """
        Get recent ingestion logs.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of log dictionaries
        """
        with self.get_session() as session:
            logs = session.query(IngestionLog).order_by(
                IngestionLog.start_time.desc()
            ).limit(limit).all()
            
            return [{
                'id': log.id,
                'operation_type': log.operation_type,
                'jurisdiction_id': log.jurisdiction_id,
                'session_identifier': log.session_identifier,
                'status': log.status,
                'items_processed': log.items_processed,
                'items_failed': log.items_failed,
                'start_time': log.start_time.isoformat() if log.start_time else None,
                'end_time': log.end_time.isoformat() if log.end_time else None,
                'error_message': log.error_message
            } for log in logs]
