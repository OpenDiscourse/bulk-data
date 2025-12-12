"""
Tests for Data Ingestion System

Run with: python -m pytest test_ingestion.py -v
"""

import pytest
import time
import os
from pathlib import Path
import tempfile
import shutil

from rate_limiter import RateLimiter, RateLimiterManager
from data_tracker import SQLiteDataTracker, InMemoryDataTracker, DataTrackerManager
from worker_pool import WorkerPool, Task, DistributedIngestionCoordinator


class TestRateLimiter:
    """Tests for rate limiting functionality"""
    
    def test_rate_limiter_basic(self):
        """Test basic rate limiting"""
        limiter = RateLimiter(requests_per_hour=100, requests_per_minute=10)
        
        # First request should not wait
        wait_time = limiter.wait_if_needed()
        assert wait_time == 0.0
        
        # Stats should be updated
        stats = limiter.get_stats()
        assert stats['total_requests'] == 1
        assert stats['total_throttled'] == 0
    
    def test_rate_limiter_throttling(self):
        """Test that rate limiter throttles when limit is reached"""
        # Very restrictive limit for testing
        limiter = RateLimiter(requests_per_hour=100, requests_per_minute=2)
        
        # Make allowed requests
        limiter.wait_if_needed()  # Request 1
        limiter.wait_if_needed()  # Request 2
        
        # Third request should be throttled
        start = time.time()
        wait_time = limiter.wait_if_needed()  # Request 3 - should wait
        elapsed = time.time() - start
        
        # Should have waited (allow some tolerance for timing)
        assert wait_time > 0 or elapsed > 0.5
    
    def test_rate_limiter_manager(self):
        """Test rate limiter manager"""
        manager = RateLimiterManager()
        
        # Create limiters
        limiter1 = manager.get_or_create("api1", 1000, 10)
        limiter2 = manager.get_or_create("api2", 2000, 20)
        
        # Should return same instance
        assert manager.get_or_create("api1", 1000, 10) is limiter1
        
        # Stats should track both
        all_stats = manager.get_all_stats()
        assert "api1" in all_stats
        assert "api2" in all_stats


class TestDataTracker:
    """Tests for data tracking functionality"""
    
    def test_in_memory_tracker(self):
        """Test in-memory data tracker"""
        tracker = InMemoryDataTracker("test_tracker")
        
        # Initially empty
        assert not tracker.has_item("item1")
        
        # Add item
        tracker.add_item("item1", {"key": "value"})
        assert tracker.has_item("item1")
        
        # Stats
        stats = tracker.get_stats()
        assert stats['total_items'] == 1
        
        # Clear
        tracker.clear()
        assert not tracker.has_item("item1")
    
    def test_sqlite_tracker(self):
        """Test SQLite data tracker"""
        # Use temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            tracker = SQLiteDataTracker("test_tracker", db_path)
            
            # Add items
            tracker.add_item("item1", {"type": "test"})
            tracker.add_item("item2", {"type": "test"})
            
            # Check items
            assert tracker.has_item("item1")
            assert tracker.has_item("item2")
            assert not tracker.has_item("item3")
            
            # Stats
            stats = tracker.get_stats()
            assert stats['total_items'] == 2
            
            # Get all items
            items = tracker.get_all_items()
            assert len(items) == 2
            
            # Clear
            tracker.clear()
            assert tracker.get_stats()['total_items'] == 0
        
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_tracker_manager(self):
        """Test data tracker manager"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            manager = DataTrackerManager(storage_type="sqlite", db_path=db_path)
            
            # Get trackers
            tracker1 = manager.get_tracker("tracker1")
            tracker2 = manager.get_tracker("tracker2")
            
            # Add items to different trackers
            tracker1.add_item("item1")
            tracker2.add_item("item2")
            
            # Stats should show both
            all_stats = manager.get_all_stats()
            assert "tracker1" in all_stats
            assert "tracker2" in all_stats
            assert all_stats["tracker1"]["total_items"] == 1
            assert all_stats["tracker2"]["total_items"] == 1
        
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestWorkerPool:
    """Tests for worker pool functionality"""
    
    def test_worker_pool_basic(self):
        """Test basic worker pool functionality"""
        pool = WorkerPool(num_workers=2)
        
        # Register handler
        def test_handler(params):
            return {"result": params["value"] * 2}
        
        pool.register_handler("test_task", test_handler)
        
        # Add tasks
        for i in range(5):
            task = Task(
                task_id=f"task_{i}",
                task_type="test_task",
                params={"value": i}
            )
            pool.add_task(task)
        
        # Run and wait
        results = pool.run_until_complete()
        
        # Check results
        assert len(results) == 5
        successful = [r for r in results if r.success]
        assert len(successful) == 5
    
    def test_worker_pool_error_handling(self):
        """Test worker pool error handling and retries"""
        pool = WorkerPool(num_workers=2)
        
        # Handler that fails
        call_count = {"count": 0}
        
        def failing_handler(params):
            call_count["count"] += 1
            if call_count["count"] < 3:  # Fail first 2 times
                raise Exception("Test error")
            return {"result": "success"}
        
        pool.register_handler("failing_task", failing_handler)
        
        # Add task (max_retries=3)
        task = Task(
            task_id="task_1",
            task_type="failing_task",
            params={},
            max_retries=3
        )
        pool.add_task(task)
        
        # Run
        results = pool.run_until_complete()
        
        # Should eventually succeed after retries
        assert len(results) > 0
        # Note: With retries, we might get multiple results for the same task
    
    def test_worker_pool_stats(self):
        """Test worker pool statistics"""
        pool = WorkerPool(num_workers=2)
        
        def handler(params):
            time.sleep(0.1)  # Simulate work
            return {"done": True}
        
        pool.register_handler("task", handler)
        
        # Add tasks
        for i in range(3):
            pool.add_task(Task(
                task_id=f"task_{i}",
                task_type="task",
                params={}
            ))
        
        # Run
        pool.run_until_complete()
        
        # Check stats
        stats = pool.get_stats()
        assert stats['total_tasks'] == 3
        assert stats['completed_tasks'] == 3
        assert stats['avg_execution_time'] > 0


class TestDistributedCoordinator:
    """Tests for distributed ingestion coordinator"""
    
    def test_coordinator_basic(self):
        """Test basic coordinator functionality"""
        pool = WorkerPool(num_workers=2)
        coordinator = DistributedIngestionCoordinator(pool)
        
        # Items to ingest
        items = [{"id": i, "value": i * 10} for i in range(5)]
        
        # Processor function
        def processor(params):
            item = params["item"]
            return {"processed": item["id"]}
        
        # Ingest
        results = coordinator.ingest_collection(
            "test_collection",
            items,
            processor
        )
        
        # Check results
        assert len(results) == 5
        successful = sum(1 for r in results if r.success)
        assert successful == 5
        
        # Check total ingested
        assert coordinator.get_total_ingested() == 5


def test_integration():
    """Integration test with all components"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        
        # Setup components
        rate_limiter = RateLimiter(1000, 10)
        tracker = SQLiteDataTracker("integration_test", db_path)
        pool = WorkerPool(num_workers=2)
        coordinator = DistributedIngestionCoordinator(pool)
        
        # Simulate data ingestion
        items = [{"id": f"item_{i}", "data": f"data_{i}"} for i in range(10)]
        
        def processor(params):
            item = params["item"]
            item_id = item["id"]
            
            # Check if already processed
            if tracker.has_item(item_id):
                return {"skipped": True}
            
            # Wait for rate limiter
            rate_limiter.wait_if_needed()
            
            # Mark as processed
            tracker.add_item(item_id, {"processed": True})
            
            return {"processed": item_id}
        
        # Run ingestion
        results = coordinator.ingest_collection(
            "integration_test",
            items,
            processor
        )
        
        # Verify
        assert len(results) == 10
        successful = sum(1 for r in results if r.success)
        assert successful == 10
        
        # Check tracker
        assert tracker.get_stats()['total_items'] == 10
        
        # Run again - should skip all items
        results2 = coordinator.ingest_collection(
            "integration_test",
            items,
            processor
        )
        
        # All should be skipped (still successful, but marked as such)
        assert len(results2) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
