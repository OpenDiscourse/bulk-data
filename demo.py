"""
Demo Script - Shows System Capabilities

This script demonstrates the data ingestion system without requiring API keys.
It shows how the components work together.
"""

import json
from rate_limiter import RateLimiter, RateLimiterManager
from data_tracker import InMemoryDataTracker, SQLiteDataTracker
from worker_pool import WorkerPool, Task
import time

def demo_rate_limiter():
    """Demonstrate rate limiting"""
    print("\n" + "="*60)
    print("DEMO 1: Rate Limiting")
    print("="*60)
    
    # Create a rate limiter for demo (more lenient for demo purposes)
    limiter = RateLimiter(requests_per_hour=100, requests_per_minute=10)
    
    print(f"\nRate limiter configured:")
    print(f"  - 100 requests per hour")
    print(f"  - 10 requests per minute")
    
    print("\nMaking 5 requests...")
    for i in range(5):
        start = time.time()
        wait_time = limiter.wait_if_needed()
        elapsed = time.time() - start
        
        if wait_time > 0:
            print(f"  Request {i+1}: THROTTLED (waited {wait_time:.2f}s)")
        else:
            print(f"  Request {i+1}: OK (no wait)")
    
    stats = limiter.get_stats()
    print(f"\nStatistics:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Throttled: {stats['total_throttled']}")
    print("\nNote: Rate limiter tracks requests and automatically")
    print("      throttles when limits are approached.")


def demo_data_tracker():
    """Demonstrate data tracking"""
    print("\n" + "="*60)
    print("DEMO 2: Data Tracking (Deduplication)")
    print("="*60)
    
    tracker = InMemoryDataTracker("demo_tracker")
    
    print("\nTracking items...")
    items = ["bill_118_hr_1", "bill_118_hr_2", "bill_118_hr_3"]
    
    # First pass - add all items
    print("First pass (add new items):")
    for item_id in items:
        if not tracker.has_item(item_id):
            tracker.add_item(item_id, {"processed": True})
            print(f"  ✓ Added: {item_id}")
    
    # Second pass - should skip all
    print("\nSecond pass (check for duplicates):")
    for item_id in items:
        if tracker.has_item(item_id):
            print(f"  ⊗ Skipped (duplicate): {item_id}")
        else:
            tracker.add_item(item_id, {"processed": True})
            print(f"  ✓ Added: {item_id}")
    
    stats = tracker.get_stats()
    print(f"\nStatistics:")
    print(f"  Total items tracked: {stats['total_items']}")


def demo_worker_pool():
    """Demonstrate parallel worker pool"""
    print("\n" + "="*60)
    print("DEMO 3: Parallel Worker Pool")
    print("="*60)
    
    pool = WorkerPool(num_workers=3)
    
    print(f"\nWorker pool configured with {pool.num_workers} workers")
    
    # Register a task handler
    def process_item(params):
        item_id = params["id"]
        # Simulate some work
        time.sleep(0.1)
        return {"processed": item_id, "result": item_id.upper()}
    
    pool.register_handler("process", process_item)
    
    # Add tasks
    print("\nAdding 10 tasks to queue...")
    for i in range(10):
        task = Task(
            task_id=f"task_{i}",
            task_type="process",
            params={"id": f"item_{i}"}
        )
        pool.add_task(task)
    
    print("Processing tasks in parallel...")
    start = time.time()
    results = pool.run_until_complete()
    elapsed = time.time() - start
    
    print(f"\nCompleted in {elapsed:.2f}s")
    
    stats = pool.get_stats()
    print(f"\nStatistics:")
    print(f"  Total tasks: {stats['total_tasks']}")
    print(f"  Completed: {stats['completed_tasks']}")
    print(f"  Failed: {stats['failed_tasks']}")
    print(f"  Avg execution time: {stats['avg_execution_time']:.3f}s")


def demo_mcp_config():
    """Demonstrate MCP server configuration"""
    print("\n" + "="*60)
    print("DEMO 4: MCP Server Configuration")
    print("="*60)
    
    # Load and display MCP config
    with open('mcp_server_config.json', 'r') as f:
        config = json.load(f)
    
    print("\nConfigured MCP Servers:")
    for server_name, server_config in config['mcpServers'].items():
        print(f"\n  {server_name}:")
        print(f"    Description: {server_config['description']}")
        print(f"    Base URL: {server_config.get('baseUrl', 'N/A')}")
        
        rate_limit = server_config.get('rateLimit', {})
        if rate_limit:
            print(f"    Rate Limit: {rate_limit.get('requestsPerHour', 'N/A')}/hour")
        
        # Show endpoint count
        endpoints = server_config.get('endpoints', {})
        collections = server_config.get('collections', {})
        
        if endpoints:
            print(f"    Endpoints: {len(endpoints)}")
        if collections:
            print(f"    Collections: {len(collections)}")


def demo_integration():
    """Demonstrate full integration"""
    print("\n" + "="*60)
    print("DEMO 5: Full Integration Simulation")
    print("="*60)
    
    # Simulate ingesting bills
    rate_limiter = RateLimiter(requests_per_hour=100, requests_per_minute=10)
    tracker = InMemoryDataTracker("bills")
    pool = WorkerPool(num_workers=4)
    
    print("\nSimulating bill ingestion workflow:")
    print("  Components:")
    print("    - Rate Limiter: 100 req/hr, 10 req/min")
    print("    - Data Tracker: In-memory")
    print("    - Worker Pool: 4 workers")
    
    # Simulated bills
    simulated_bills = [
        {"id": "hr-1", "title": "Example Bill 1"},
        {"id": "hr-2", "title": "Example Bill 2"},
        {"id": "hr-3", "title": "Example Bill 3"},
        {"id": "hr-4", "title": "Example Bill 4"},
        {"id": "hr-5", "title": "Example Bill 5"},
    ]
    
    print(f"\n  Processing {len(simulated_bills)} bills...")
    
    # Define processor
    def process_bill(params):
        bill = params["bill"]
        bill_id = bill["id"]
        
        # Rate limit
        rate_limiter.wait_if_needed()
        
        # Check if already processed
        if tracker.has_item(bill_id):
            return {"skipped": True, "id": bill_id}
        
        # Simulate processing
        time.sleep(0.05)
        
        # Mark as processed
        tracker.add_item(bill_id, {"title": bill["title"]})
        
        return {"processed": True, "id": bill_id}
    
    pool.register_handler("process_bill", process_bill)
    
    # Add tasks
    for bill in simulated_bills:
        pool.add_task(Task(
            task_id=bill["id"],
            task_type="process_bill",
            params={"bill": bill}
        ))
    
    # Process
    start = time.time()
    results = pool.run_until_complete()
    elapsed = time.time() - start
    
    successful = sum(1 for r in results if r.success)
    
    print(f"\n  Results:")
    print(f"    Processed: {successful}/{len(simulated_bills)}")
    print(f"    Time: {elapsed:.2f}s")
    
    # Show stats
    print(f"\n  Rate Limiter Stats:")
    rl_stats = rate_limiter.get_stats()
    print(f"    Requests: {rl_stats['total_requests']}")
    print(f"    Throttled: {rl_stats['total_throttled']}")
    
    print(f"\n  Data Tracker Stats:")
    dt_stats = tracker.get_stats()
    print(f"    Items tracked: {dt_stats['total_items']}")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("DATA INGESTION SYSTEM DEMONSTRATION")
    print("="*60)
    print("\nThis demo shows the capabilities of the system without")
    print("requiring API keys. It demonstrates:")
    print("  1. Rate limiting")
    print("  2. Data tracking (deduplication)")
    print("  3. Parallel worker pool")
    print("  4. MCP server configuration")
    print("  5. Full integration")
    
    try:
        demo_rate_limiter()
        demo_data_tracker()
        demo_worker_pool()
        demo_mcp_config()
        demo_integration()
        
        print("\n" + "="*60)
        print("DEMO COMPLETE")
        print("="*60)
        print("\nNext steps:")
        print("  1. Set API keys: export CONGRESS_API_KEY=your_key")
        print("  2. Run examples: python example_usage.py")
        print("  3. Read docs: DATA_INGESTION_README.md")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
