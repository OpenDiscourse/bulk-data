"""
Example Usage of Data Ingestion System

This script demonstrates how to use the data ingestion orchestrator
to fetch data from api.congress.gov and govinfo.gov APIs.
"""

import os
import sys
from orchestrator import DataIngestionOrchestrator


def example_congress_bills():
    """Example: Ingest bills from api.congress.gov"""
    
    # Initialize orchestrator
    orchestrator = DataIngestionOrchestrator(
        congress_api_key=os.getenv("CONGRESS_API_KEY"),
        num_workers=8,  # Use 8 parallel workers
        output_dir="./output/congress"
    )
    
    # Ingest bills from 118th Congress, House Resolutions
    print("Ingesting House Resolutions from 118th Congress...")
    results = orchestrator.ingest_congress_bills(
        congress=118,
        bill_type="hr",
        max_items=100  # Limit to 100 for this example
    )
    
    print(f"Results: {results}")
    print(f"Overall stats: {orchestrator.get_overall_stats()}")


def example_govinfo_collection():
    """Example: Ingest collection from api.govinfo.gov"""
    
    # Initialize orchestrator
    orchestrator = DataIngestionOrchestrator(
        govinfo_api_key=os.getenv("GOVINFO_API_KEY"),
        num_workers=8,
        output_dir="./output/govinfo"
    )
    
    # Ingest BILLS collection from a specific date
    print("Ingesting BILLS collection from 2024-01-01...")
    results = orchestrator.ingest_govinfo_collection(
        collection_code="BILLS",
        start_date="2024-01-01",
        max_items=50  # Limit to 50 for this example
    )
    
    print(f"Results: {results}")
    print(f"Overall stats: {orchestrator.get_overall_stats()}")


def example_bulkdata():
    """Example: Ingest bulk data from govinfo.gov/bulkdata"""
    
    # Initialize orchestrator
    orchestrator = DataIngestionOrchestrator(
        num_workers=8,
        output_dir="./output/bulkdata"
    )
    
    # Ingest Federal Register bulk data from a specific year/month
    print("Ingesting Federal Register bulk data from 2024/01...")
    results = orchestrator.ingest_bulkdata_collection(
        collection="FR",
        path="2024/01",
        max_depth=2
    )
    
    print(f"Results: {results}")
    print(f"Overall stats: {orchestrator.get_overall_stats()}")


def example_full_pipeline():
    """Example: Full pipeline with multiple sources"""
    
    # Initialize orchestrator with API keys
    orchestrator = DataIngestionOrchestrator(
        congress_api_key=os.getenv("CONGRESS_API_KEY"),
        govinfo_api_key=os.getenv("GOVINFO_API_KEY"),
        num_workers=16,  # More workers for parallel processing
        output_dir="./output/full_pipeline"
    )
    
    print("=" * 60)
    print("FULL INGESTION PIPELINE")
    print("=" * 60)
    
    # Step 1: Ingest Congress bills
    if orchestrator.congress_client:
        print("\n1. Ingesting Congress Bills...")
        bills_results = orchestrator.ingest_congress_bills(
            congress=118,
            max_items=200
        )
        print(f"   Bills ingested: {bills_results['successful']}/{bills_results['total_items']}")
    
    # Step 2: Ingest GovInfo collections
    if orchestrator.govinfo_client:
        print("\n2. Ingesting GovInfo BILLS collection...")
        govinfo_results = orchestrator.ingest_govinfo_collection(
            collection_code="BILLS",
            start_date="2024-01-01",
            max_items=100
        )
        print(f"   Packages ingested: {govinfo_results['successful']}/{govinfo_results['total_items']}")
    
    # Step 3: Ingest bulk data
    print("\n3. Ingesting Bulk Data (Federal Register)...")
    bulk_results = orchestrator.ingest_bulkdata_collection(
        collection="FR",
        path="2024/01",
        max_depth=1
    )
    print(f"   Files downloaded: {bulk_results['successful']}/{bulk_results['total_items']}")
    
    # Final statistics
    print("\n" + "=" * 60)
    print("FINAL STATISTICS")
    print("=" * 60)
    stats = orchestrator.get_overall_stats()
    
    print("\nRate Limiter Stats:")
    for name, limiter_stats in stats['rate_limiters'].items():
        print(f"  {name}:")
        print(f"    Total requests: {limiter_stats['total_requests']}")
        print(f"    Throttled: {limiter_stats['total_throttled']}")
    
    print("\nData Tracker Stats:")
    for name, tracker_stats in stats['trackers'].items():
        print(f"  {name}:")
        print(f"    Total items: {tracker_stats['total_items']}")
    
    print("\nWorker Stats:")
    worker_stats = stats['workers']
    print(f"  Total tasks: {worker_stats['total_tasks']}")
    print(f"  Completed: {worker_stats['completed_tasks']}")
    print(f"  Failed: {worker_stats['failed_tasks']}")
    print(f"  Retried: {worker_stats['retried_tasks']}")
    print(f"  Avg execution time: {worker_stats.get('avg_execution_time', 0):.2f}s")
    
    print(f"\nTotal items ingested: {stats['total_ingested']}")


def main():
    """Main function to run examples"""
    
    # Check for API keys
    if not os.getenv("CONGRESS_API_KEY"):
        print("WARNING: CONGRESS_API_KEY environment variable not set")
        print("         Congress API examples will be skipped")
    
    if not os.getenv("GOVINFO_API_KEY"):
        print("WARNING: GOVINFO_API_KEY environment variable not set")
        print("         GovInfo API examples will be skipped")
    
    print("\nAvailable examples:")
    print("1. Congress Bills")
    print("2. GovInfo Collection")
    print("3. Bulk Data")
    print("4. Full Pipeline")
    print("5. All examples")
    
    choice = input("\nSelect example to run (1-5): ").strip()
    
    if choice == "1":
        example_congress_bills()
    elif choice == "2":
        example_govinfo_collection()
    elif choice == "3":
        example_bulkdata()
    elif choice == "4":
        example_full_pipeline()
    elif choice == "5":
        example_congress_bills()
        example_govinfo_collection()
        example_bulkdata()
    else:
        print("Invalid choice")
        sys.exit(1)


if __name__ == "__main__":
    main()
