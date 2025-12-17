"""
OpenStates Bulk Data Ingestion Example

This script demonstrates how to use the OpenStates data ingestion framework
to fetch and store legislative data from all U.S. states.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

from openstates_orchestrator import OpenStatesOrchestrator
from bicam_integration import BICAMDataManager, BICAMPostgreSQLIngester

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('openstates_ingestion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def example_1_basic_setup():
    """
    Example 1: Basic setup and database initialization.
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Setup")
    print("="*60)
    
    # Get configuration from environment
    api_key = os.getenv('OPENSTATES_API_KEY')
    database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/openstates')
    
    if not api_key:
        print("ERROR: OPENSTATES_API_KEY not set in environment")
        print("Get your API key from: https://openstates.org/api/")
        return
    
    # Initialize orchestrator
    print(f"\nInitializing orchestrator with:")
    print(f"  - 20 parallel workers")
    print(f"  - Database: {database_url}")
    
    orchestrator = OpenStatesOrchestrator(
        api_key=api_key,
        database_url=database_url,
        num_workers=20
    )
    
    # Setup database
    print("\nCreating database tables...")
    orchestrator.setup_database()
    print("✓ Database tables created successfully")
    
    return orchestrator


def example_2_ingest_jurisdictions(orchestrator):
    """
    Example 2: Ingest all U.S. jurisdictions (states and territories).
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Ingest Jurisdictions")
    print("="*60)
    
    print("\nIngesting all U.S. jurisdictions...")
    result = orchestrator.ingest_all_jurisdictions()
    
    print(f"\nResults:")
    print(f"  Total: {result['total']}")
    print(f"  Processed: {result['processed']}")
    print(f"  Failed: {result['failed']}")
    print(f"  Log ID: {result['log_id']}")


def example_3_ingest_single_state(orchestrator):
    """
    Example 3: Ingest bills from a single state (North Carolina).
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Ingest Single State Bills")
    print("="*60)
    
    jurisdiction = 'NC'
    session = '2023'
    
    print(f"\nIngesting bills from {jurisdiction} - {session} session")
    print("This may take several minutes...")
    
    result = orchestrator.ingest_bills(
        jurisdiction=jurisdiction,
        session=session,
        max_items=100  # Limit to 100 for demo
    )
    
    print(f"\nResults:")
    print(f"  Total bills: {result['total']}")
    print(f"  Processed: {result['processed']}")
    print(f"  Failed: {result['failed']}")
    print(f"  Log ID: {result['log_id']}")


def example_4_ingest_legislators(orchestrator):
    """
    Example 4: Ingest legislators from a specific state.
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Ingest Legislators")
    print("="*60)
    
    jurisdiction = 'NC'
    
    print(f"\nIngesting legislators from {jurisdiction}")
    
    result = orchestrator.ingest_people(
        jurisdiction=jurisdiction,
        max_items=200  # Limit for demo
    )
    
    print(f"\nResults:")
    print(f"  Total people: {result['total']}")
    print(f"  Processed: {result['processed']}")
    print(f"  Failed: {result['failed']}")


def example_5_incremental_update(orchestrator):
    """
    Example 5: Perform incremental update (fetch only recent changes).
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Incremental Update")
    print("="*60)
    
    # Get updates from last 7 days
    since_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"\nFetching bills updated since {since_date}")
    
    result = orchestrator.ingest_bills(
        jurisdiction='NC',
        session='2023',
        updated_since=since_date,
        max_items=50
    )
    
    print(f"\nResults:")
    print(f"  Bills updated: {result['processed']}")
    print(f"  Failed: {result['failed']}")


def example_6_get_statistics(orchestrator):
    """
    Example 6: Get comprehensive statistics about ingested data.
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: Get Statistics")
    print("="*60)
    
    stats = orchestrator.get_ingestion_statistics()
    
    print("\nDatabase Statistics:")
    print(f"  Jurisdictions: {stats['database']['jurisdictions']}")
    print(f"  Legislative Sessions: {stats['database']['sessions']}")
    print(f"  People: {stats['database']['people']}")
    print(f"  Bills: {stats['database']['bills']}")
    print(f"  Votes: {stats['database']['votes']}")
    print(f"  Committees: {stats['database']['committees']}")
    
    print("\nWorker Pool Statistics:")
    print(f"  Total tasks: {stats['workers']['total_tasks']}")
    print(f"  Completed: {stats['workers']['completed_tasks']}")
    print(f"  Failed: {stats['workers']['failed_tasks']}")
    print(f"  Retried: {stats['workers']['retried_tasks']}")
    
    if stats['workers'].get('avg_execution_time'):
        print(f"  Avg execution time: {stats['workers']['avg_execution_time']:.2f}s")
    
    print(f"\nTotal items ingested: {stats['total_ingested']}")
    
    if stats['recent_logs']:
        print("\nRecent Operations:")
        for log in stats['recent_logs'][:5]:
            print(f"  - {log['operation_type']}: {log['status']}")
            print(f"    Processed: {log['items_processed']}, Failed: {log['items_failed']}")


def example_7_bicam_integration():
    """
    Example 7: Integrate congressional data using BICAM library.
    """
    print("\n" + "="*60)
    print("EXAMPLE 7: BICAM Integration")
    print("="*60)
    
    try:
        # Initialize BICAM manager
        bicam_manager = BICAMDataManager(cache_dir='./bicam_cache')
        
        print("\nListing available BICAM datasets...")
        datasets = bicam_manager.list_datasets()
        print(f"Found {len(datasets)} datasets:")
        for ds in datasets[:5]:
            print(f"  - {ds}")
        
        # Get info about bills dataset
        print("\nGetting info about 'bills' dataset...")
        info = bicam_manager.get_dataset_info('bills')
        if info:
            print(f"  Dataset: {info.get('name', 'bills')}")
            print(f"  Size: {info.get('size', 'unknown')}")
        
        # Note: Actual download and ingestion would be done here
        # Commented out to avoid large downloads in example
        
        # print("\nDownloading bills dataset...")
        # path = bicam_manager.download_dataset('bills')
        # print(f"  Downloaded to: {path}")
        
        # print("\nIngesting to PostgreSQL...")
        # database_url = os.getenv('DATABASE_URL')
        # ingester = BICAMPostgreSQLIngester(bicam_manager, database_url)
        # result = ingester.ingest_dataset('bills')
        # print(f"  Status: {result['status']}")
        # print(f"  Rows inserted: {result.get('rows_inserted', 0)}")
        
        print("\n(Download and ingestion commented out in example)")
        
    except ImportError:
        print("\nBICAM library not installed.")
        print("Install with: pip install bicam")


def example_8_full_pipeline():
    """
    Example 8: Full data ingestion pipeline.
    """
    print("\n" + "="*60)
    print("EXAMPLE 8: Full Ingestion Pipeline")
    print("="*60)
    
    api_key = os.getenv('OPENSTATES_API_KEY')
    database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/openstates')
    
    if not api_key:
        print("ERROR: OPENSTATES_API_KEY not set")
        return
    
    # Initialize
    orchestrator = OpenStatesOrchestrator(
        api_key=api_key,
        database_url=database_url,
        num_workers=20
    )
    
    orchestrator.setup_database()
    
    # Step 1: Ingest jurisdictions
    print("\n[1/4] Ingesting jurisdictions...")
    jur_result = orchestrator.ingest_all_jurisdictions()
    print(f"      ✓ {jur_result['processed']} jurisdictions")
    
    # Step 2: Ingest people
    print("\n[2/4] Ingesting legislators...")
    people_result = orchestrator.ingest_people(max_items=500)
    print(f"      ✓ {people_result['processed']} people")
    
    # Step 3: Ingest bills from multiple states
    print("\n[3/4] Ingesting bills...")
    states = ['NC', 'CA', 'TX']
    total_bills = 0
    
    for state in states:
        result = orchestrator.ingest_bills(
            jurisdiction=state,
            session='2023',
            max_items=50
        )
        total_bills += result['processed']
        print(f"      ✓ {state}: {result['processed']} bills")
    
    print(f"      Total: {total_bills} bills")
    
    # Step 4: Get final statistics
    print("\n[4/4] Final statistics...")
    stats = orchestrator.get_ingestion_statistics()
    print(f"      Database entities:")
    print(f"        - Jurisdictions: {stats['database']['jurisdictions']}")
    print(f"        - People: {stats['database']['people']}")
    print(f"        - Bills: {stats['database']['bills']}")
    print(f"        - Votes: {stats['database']['votes']}")
    
    print("\n✓ Pipeline complete!")


def main():
    """Main function to run examples."""
    
    print("\n" + "="*60)
    print("OpenStates Bulk Data Ingestion Examples")
    print("="*60)
    
    print("\nAvailable examples:")
    print("1. Basic setup and database initialization")
    print("2. Ingest all jurisdictions")
    print("3. Ingest bills from a single state")
    print("4. Ingest legislators")
    print("5. Incremental update (recent changes)")
    print("6. Get statistics")
    print("7. BICAM integration")
    print("8. Full ingestion pipeline")
    print("9. Run all examples")
    
    choice = input("\nSelect example to run (1-9): ").strip()
    
    try:
        if choice == '1':
            orchestrator = example_1_basic_setup()
        elif choice == '2':
            orchestrator = example_1_basic_setup()
            example_2_ingest_jurisdictions(orchestrator)
        elif choice == '3':
            orchestrator = example_1_basic_setup()
            example_3_ingest_single_state(orchestrator)
        elif choice == '4':
            orchestrator = example_1_basic_setup()
            example_4_ingest_legislators(orchestrator)
        elif choice == '5':
            orchestrator = example_1_basic_setup()
            example_5_incremental_update(orchestrator)
        elif choice == '6':
            orchestrator = example_1_basic_setup()
            example_6_get_statistics(orchestrator)
        elif choice == '7':
            example_7_bicam_integration()
        elif choice == '8':
            example_8_full_pipeline()
        elif choice == '9':
            orchestrator = example_1_basic_setup()
            example_2_ingest_jurisdictions(orchestrator)
            example_3_ingest_single_state(orchestrator)
            example_4_ingest_legislators(orchestrator)
            example_5_incremental_update(orchestrator)
            example_6_get_statistics(orchestrator)
            example_7_bicam_integration()
        else:
            print("Invalid choice")
            sys.exit(1)
        
        print("\n" + "="*60)
        print("Example completed successfully!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
