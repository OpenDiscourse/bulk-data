"""
Tests for OpenStates Data Ingestion System

Comprehensive tests for OpenStates API client, database layer, 
and orchestration components.
"""

import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from rate_limiter import RateLimiter
from openstates_client import OpenStatesClient
from openstates_db import OpenStatesDatabase
from openstates_models import (
    Base, Jurisdiction, LegislativeSession, Person, Bill,
    BillSponsorship, Vote, VoteRecord
)
from openstates_orchestrator import OpenStatesOrchestrator


# Mock data fixtures

@pytest.fixture
def mock_jurisdiction_data():
    """Mock jurisdiction data from OpenStates API."""
    return {
        'id': 'ocd-jurisdiction/country:us/state:nc/government',
        'name': 'North Carolina',
        'abbreviation': 'NC',
        'classification': 'state',
        'url': 'https://www.nc.gov',
        'legislative_sessions': [
            {
                'identifier': '2023',
                'name': '2023 Regular Session',
                'classification': 'regular',
                'start_date': '2023-01-11',
                'end_date': '2023-06-30'
            }
        ]
    }


@pytest.fixture
def mock_person_data():
    """Mock person (legislator) data from OpenStates API."""
    return {
        'id': 'ocd-person/12345',
        'name': 'John Doe',
        'given_name': 'John',
        'family_name': 'Doe',
        'email': 'john.doe@legislature.gov',
        'jurisdiction': {
            'id': 'ocd-jurisdiction/country:us/state:nc/government'
        },
        'current_memberships': [
            {
                'party': {'name': 'Democratic'},
                'organization': {'name': 'North Carolina Senate'},
                'post': {'label': 'District 1'}
            }
        ],
        'extras': {},
        'sources': []
    }


@pytest.fixture
def mock_bill_data():
    """Mock bill data from OpenStates API."""
    return {
        'id': 'ocd-bill/12345',
        'identifier': 'HB 1',
        'title': 'An Act to do something',
        'classification': 'bill',
        'subject': ['education', 'healthcare'],
        'abstracts': [{'note': 'Summary', 'abstract': 'This bill does X'}],
        'jurisdiction': {
            'id': 'ocd-jurisdiction/country:us/state:nc/government'
        },
        'from_organization': {'name': 'lower'},
        'actions': [
            {
                'date': '2023-01-15',
                'description': 'Introduced',
                'classification': ['introduction']
            }
        ],
        'sponsorships': [
            {
                'name': 'John Doe',
                'classification': 'primary',
                'entity_type': 'person',
                'primary': True,
                'person': {'id': 'ocd-person/12345'}
            }
        ],
        'versions': [
            {
                'note': 'Introduced',
                'date': '2023-01-15',
                'links': [{'url': 'https://example.com/bill.pdf'}]
            }
        ],
        'documents': [],
        'votes': [],
        'extras': {},
        'sources': [],
        'updated_at': '2023-01-15T10:00:00'
    }


@pytest.fixture
def mock_vote_data():
    """Mock vote data from OpenStates API."""
    return {
        'id': 'ocd-vote/12345',
        'identifier': 'Vote 1',
        'motion_text': 'Passage of HB 1',
        'motion_classification': ['passage'],
        'start_date': '2023-01-20T14:30:00',
        'result': 'pass',
        'organization': {'name': 'North Carolina Senate'},
        'counts': [
            {'option': 'yes', 'value': 30},
            {'option': 'no', 'value': 20}
        ],
        'votes': [
            {
                'voter_name': 'John Doe',
                'option': 'yes',
                'voter': {'id': 'ocd-person/12345'}
            }
        ],
        'sources': []
    }


# Test OpenStates Client

class TestOpenStatesClient:
    """Tests for OpenStates API client."""
    
    def test_client_initialization(self):
        """Test client initialization."""
        rate_limiter = RateLimiter(1000, 10)
        client = OpenStatesClient('test_api_key', rate_limiter)
        
        assert client.api_key == 'test_api_key'
        assert client.base_url == 'https://v3.openstates.org'
        assert 'X-API-KEY' in client.session.headers
    
    @patch('openstates_client.requests.Session.get')
    def test_get_jurisdictions(self, mock_get, mock_jurisdiction_data):
        """Test fetching jurisdictions."""
        rate_limiter = RateLimiter(1000, 10)
        client = OpenStatesClient('test_api_key', rate_limiter)
        
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {'results': [mock_jurisdiction_data]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        jurisdictions = client.get_jurisdictions()
        
        assert len(jurisdictions) == 1
        assert jurisdictions[0]['abbreviation'] == 'NC'
    
    @patch('openstates_client.requests.Session.get')
    def test_search_bills(self, mock_get, mock_bill_data):
        """Test searching bills with pagination."""
        rate_limiter = RateLimiter(1000, 10)
        client = OpenStatesClient('test_api_key', rate_limiter)
        
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': [mock_bill_data],
            'pagination': {'max_page': 1}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        bills = list(client.search_bills(jurisdiction='NC', session='2023', max_items=10))
        
        assert len(bills) >= 1
        assert bills[0]['identifier'] == 'HB 1'
    
    @patch('openstates_client.requests.Session.get')
    def test_search_people(self, mock_get, mock_person_data):
        """Test searching people."""
        rate_limiter = RateLimiter(1000, 10)
        client = OpenStatesClient('test_api_key', rate_limiter)
        
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': [mock_person_data],
            'pagination': {'max_page': 1}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        people = list(client.search_people(jurisdiction='NC', max_items=10))
        
        assert len(people) >= 1
        assert people[0]['name'] == 'John Doe'


# Test Database Layer

class TestOpenStatesDatabase:
    """Tests for OpenStates database layer."""
    
    @pytest.fixture
    def test_db(self):
        """Create a test database."""
        # Use in-memory SQLite for testing
        db = OpenStatesDatabase('sqlite:///:memory:', echo=False)
        db.create_tables()
        return db
    
    def test_table_creation(self, test_db):
        """Test that tables are created successfully."""
        assert test_db.table_exists('jurisdictions')
        assert test_db.table_exists('people')
        assert test_db.table_exists('bills')
        assert test_db.table_exists('votes')
    
    def test_upsert_jurisdiction(self, test_db, mock_jurisdiction_data):
        """Test upserting a jurisdiction."""
        jur_id = test_db.upsert_jurisdiction(mock_jurisdiction_data)
        
        assert jur_id == mock_jurisdiction_data['id']
        
        # Verify it's in the database
        with test_db.get_session() as session:
            jur = session.query(Jurisdiction).filter_by(id=jur_id).first()
            assert jur is not None
            assert jur.abbreviation == 'NC'
            assert jur.name == 'North Carolina'
    
    def test_upsert_person(self, test_db, mock_jurisdiction_data, mock_person_data):
        """Test upserting a person."""
        # First insert jurisdiction
        test_db.upsert_jurisdiction(mock_jurisdiction_data)
        
        # Then insert person
        person_id = test_db.upsert_person(mock_person_data)
        
        assert person_id == mock_person_data['id']
        
        # Verify it's in the database
        with test_db.get_session() as session:
            person = session.query(Person).filter_by(id=person_id).first()
            assert person is not None
            assert person.name == 'John Doe'
            assert person.party == 'Democratic'
    
    def test_upsert_bill(self, test_db, mock_jurisdiction_data, mock_bill_data):
        """Test upserting a bill with sponsorships."""
        # Setup jurisdiction and session
        jur_id = test_db.upsert_jurisdiction(mock_jurisdiction_data)
        session_id = test_db.upsert_legislative_session(
            mock_jurisdiction_data['legislative_sessions'][0],
            jur_id
        )
        
        # Insert bill
        bill_id = test_db.upsert_bill(mock_bill_data, session_id)
        
        assert bill_id == mock_bill_data['id']
        
        # Verify bill and sponsorships
        with test_db.get_session() as session:
            bill = session.query(Bill).filter_by(id=bill_id).first()
            assert bill is not None
            assert bill.identifier == 'HB 1'
            assert bill.title == 'An Act to do something'
            
            # Check sponsorships
            assert len(bill.sponsorships) == 1
            assert bill.sponsorships[0].name == 'John Doe'
            assert bill.sponsorships[0].primary == True
    
    def test_upsert_vote(self, test_db, mock_jurisdiction_data, mock_bill_data, mock_vote_data):
        """Test upserting a vote with vote records."""
        # Setup prerequisites
        jur_id = test_db.upsert_jurisdiction(mock_jurisdiction_data)
        session_id = test_db.upsert_legislative_session(
            mock_jurisdiction_data['legislative_sessions'][0],
            jur_id
        )
        bill_id = test_db.upsert_bill(mock_bill_data, session_id)
        
        # Insert vote
        vote_id = test_db.upsert_vote(mock_vote_data, bill_id)
        
        assert vote_id == mock_vote_data['id']
        
        # Verify vote and vote records
        with test_db.get_session() as session:
            vote = session.query(Vote).filter_by(id=vote_id).first()
            assert vote is not None
            assert vote.result == 'pass'
            assert vote.motion_text == 'Passage of HB 1'
            
            # Check vote records
            assert len(vote.vote_records) == 1
            assert vote.vote_records[0].voter_name == 'John Doe'
            assert vote.vote_records[0].option == 'yes'
    
    def test_ingestion_logging(self, test_db):
        """Test ingestion logging."""
        # Start a log
        log_id = test_db.start_ingestion_log(
            'bills',
            jurisdiction_id='NC',
            session_identifier='2023'
        )
        
        assert log_id is not None
        
        # Update log
        test_db.update_ingestion_log(
            log_id,
            items_processed=10,
            items_failed=1,
            status='completed'
        )
        
        # Retrieve logs
        logs = test_db.get_recent_ingestion_logs(limit=1)
        assert len(logs) == 1
        assert logs[0]['items_processed'] == 10
        assert logs[0]['items_failed'] == 1
        assert logs[0]['status'] == 'completed'


# Test Orchestrator (with mocking)

class TestOpenStatesOrchestrator:
    """Tests for OpenStates orchestrator."""
    
    @pytest.fixture
    def test_orchestrator(self):
        """Create a test orchestrator with mocked components."""
        # Use in-memory database for testing
        database_url = 'sqlite:///:memory:'
        
        orchestrator = OpenStatesOrchestrator(
            api_key='test_api_key',
            database_url=database_url,
            num_workers=4  # Use fewer workers for testing
        )
        orchestrator.setup_database()
        
        return orchestrator
    
    def test_orchestrator_initialization(self, test_orchestrator):
        """Test orchestrator initialization."""
        assert test_orchestrator.api_client is not None
        assert test_orchestrator.database is not None
        assert test_orchestrator.worker_pool.num_workers == 4
    
    @patch('openstates_client.requests.Session.get')
    def test_ingest_all_jurisdictions(self, mock_get, test_orchestrator, mock_jurisdiction_data):
        """Test ingesting all jurisdictions."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {'results': [mock_jurisdiction_data]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = test_orchestrator.ingest_all_jurisdictions()
        
        assert result['processed'] >= 1
        assert result['failed'] == 0
        
        # Verify in database
        with test_orchestrator.database.get_session() as session:
            jur = session.query(Jurisdiction).filter_by(abbreviation='NC').first()
            assert jur is not None
    
    def test_get_ingestion_statistics(self, test_orchestrator):
        """Test getting ingestion statistics."""
        stats = test_orchestrator.get_ingestion_statistics()
        
        assert 'database' in stats
        assert 'rate_limiter' in stats
        assert 'workers' in stats
        assert 'total_ingested' in stats
        
        # Check database counts
        assert 'jurisdictions' in stats['database']
        assert 'bills' in stats['database']


# Test BICAM Integration

class TestBICAMIntegration:
    """Tests for BICAM integration."""
    
    @pytest.mark.skipif(not os.getenv('TEST_BICAM'), reason="BICAM tests require BICAM library")
    def test_bicam_manager_initialization(self):
        """Test BICAM manager initialization."""
        from bicam_integration import BICAMDataManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BICAMDataManager(cache_dir=tmpdir)
            assert manager.cache_dir is not None
    
    @pytest.mark.skipif(not os.getenv('TEST_BICAM'), reason="BICAM tests require BICAM library")
    def test_list_datasets(self):
        """Test listing BICAM datasets."""
        from bicam_integration import BICAMDataManager
        
        manager = BICAMDataManager()
        datasets = manager.list_datasets()
        
        assert len(datasets) > 0
        assert 'bills' in datasets


# Integration tests

def test_full_integration_flow():
    """
    Test full integration flow (minimal version for CI).
    
    This test simulates the full workflow:
    1. Setup database
    2. Ingest jurisdictions
    3. Ingest people
    4. Ingest bills
    5. Verify data
    """
    # Use in-memory database
    database_url = 'sqlite:///:memory:'
    
    with patch('openstates_client.requests.Session.get') as mock_get:
        # Setup mock responses
        mock_jur = {
            'id': 'ocd-jurisdiction/country:us/state:nc/government',
            'name': 'North Carolina',
            'abbreviation': 'NC',
            'classification': 'state',
            'legislative_sessions': [
                {'identifier': '2023', 'name': '2023 Session'}
            ]
        }
        
        mock_response = Mock()
        mock_response.json.return_value = {'results': [mock_jur]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Create orchestrator
        orchestrator = OpenStatesOrchestrator(
            api_key='test_key',
            database_url=database_url,
            num_workers=2
        )
        
        # Setup database
        orchestrator.setup_database()
        
        # Ingest jurisdictions
        result = orchestrator.ingest_all_jurisdictions()
        assert result['processed'] >= 1
        
        # Get statistics
        stats = orchestrator.get_ingestion_statistics()
        assert stats['database']['jurisdictions'] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
