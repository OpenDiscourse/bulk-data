"""
Parallel Worker System

This module provides a parallel worker system for distributed data ingestion.
Workers can process tasks concurrently with proper coordination and error handling.
"""

import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Dict, Any, Optional, Tuple
from queue import Queue, Empty
from threading import Lock
from dataclasses import dataclass, field
from datetime import datetime
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Represents a unit of work for a worker."""
    task_id: str
    task_type: str
    params: Dict[str, Any]
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TaskResult:
    """Result of a task execution."""
    task_id: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    worker_id: int = 0


class WorkerPool:
    """
    Manages a pool of workers for parallel task execution.
    
    Features:
    - Configurable worker count
    - Task queue management
    - Error handling and retries
    - Progress tracking
    - Statistics collection
    """
    
    def __init__(self, num_workers: int = 4, max_queue_size: int = 1000):
        """
        Initialize the worker pool.
        
        Args:
            num_workers: Number of parallel workers
            max_queue_size: Maximum size of task queue
        """
        self.num_workers = num_workers
        self.task_queue: Queue[Task] = Queue(maxsize=max_queue_size)
        self.results: List[TaskResult] = []
        self.executor: Optional[ThreadPoolExecutor] = None
        
        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "retried_tasks": 0,
            "total_execution_time": 0.0
        }
        self.stats_lock = Lock()
        
        # State
        self.is_running = False
        self.task_handlers: Dict[str, Callable] = {}
    
    def register_handler(self, task_type: str, handler: Callable):
        """
        Register a handler function for a task type.
        
        Args:
            task_type: Type of task
            handler: Function to handle tasks of this type
        """
        self.task_handlers[task_type] = handler
    
    def add_task(self, task: Task):
        """
        Add a task to the queue.
        
        Args:
            task: Task to add
        """
        self.task_queue.put(task)
        with self.stats_lock:
            self.stats["total_tasks"] += 1
    
    def add_tasks(self, tasks: List[Task]):
        """
        Add multiple tasks to the queue.
        
        Args:
            tasks: List of tasks to add
        """
        for task in tasks:
            self.add_task(task)
    
    def _execute_task(self, task: Task, worker_id: int) -> TaskResult:
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            worker_id: ID of the worker executing the task
            
        Returns:
            TaskResult with execution details
        """
        start_time = time.time()
        
        try:
            # Get handler for this task type
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task.task_type}")
            
            # Execute task
            logger.info(f"Worker {worker_id} executing task {task.task_id} (type: {task.task_type})")
            data = handler(task.params)
            
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                data=data,
                execution_time=execution_time,
                worker_id=worker_id
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"Worker {worker_id} failed task {task.task_id}: {error_msg}")
            
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=error_msg,
                execution_time=execution_time,
                worker_id=worker_id
            )
    
    def _worker_loop(self, worker_id: int) -> List[TaskResult]:
        """
        Main loop for a worker thread.
        
        Args:
            worker_id: Unique ID for this worker
            
        Returns:
            List of task results
        """
        results = []
        
        while self.is_running:
            try:
                # Get task from queue (with timeout to allow checking is_running)
                task = self.task_queue.get(timeout=1.0)
                
                # Execute task
                result = self._execute_task(task, worker_id)
                results.append(result)
                
                # Update statistics
                with self.stats_lock:
                    if result.success:
                        self.stats["completed_tasks"] += 1
                    else:
                        self.stats["failed_tasks"] += 1
                        
                        # Retry if allowed
                        if task.retry_count < task.max_retries:
                            task.retry_count += 1
                            self.task_queue.put(task)
                            self.stats["retried_tasks"] += 1
                            logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count + 1})")
                    
                    self.stats["total_execution_time"] += result.execution_time
                
                # Mark task as done
                self.task_queue.task_done()
                
            except Empty:
                # No task available, continue loop
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} encountered error: {e}")
        
        return results
    
    def start(self):
        """Start the worker pool."""
        if self.is_running:
            logger.warning("Worker pool already running")
            return
        
        logger.info(f"Starting worker pool with {self.num_workers} workers")
        self.is_running = True
        self.executor = ThreadPoolExecutor(max_workers=self.num_workers)
    
    def stop(self, wait: bool = True):
        """
        Stop the worker pool.
        
        Args:
            wait: Whether to wait for all tasks to complete
        """
        logger.info("Stopping worker pool")
        self.is_running = False
        
        if self.executor:
            if wait:
                # Wait for queue to be empty
                self.task_queue.join()
            
            # Shutdown executor
            self.executor.shutdown(wait=wait)
            self.executor = None
    
    def run_until_complete(self) -> List[TaskResult]:
        """
        Start workers and run until all tasks are complete.
        
        Returns:
            List of all task results
        """
        self.start()
        
        # Submit worker jobs
        futures = []
        for worker_id in range(self.num_workers):
            future = self.executor.submit(self._worker_loop, worker_id)
            futures.append(future)
        
        # Wait for queue to be empty
        self.task_queue.join()
        
        # Stop workers
        self.stop(wait=True)
        
        # Collect results
        all_results = []
        for future in as_completed(futures):
            try:
                worker_results = future.result()
                all_results.extend(worker_results)
            except Exception as e:
                logger.error(f"Error collecting worker results: {e}")
        
        self.results = all_results
        return all_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about task execution."""
        with self.stats_lock:
            stats_copy = self.stats.copy()
            stats_copy["queue_size"] = self.task_queue.qsize()
            stats_copy["num_workers"] = self.num_workers
            stats_copy["is_running"] = self.is_running
            
            if stats_copy["completed_tasks"] > 0:
                stats_copy["avg_execution_time"] = (
                    stats_copy["total_execution_time"] / stats_copy["completed_tasks"]
                )
            else:
                stats_copy["avg_execution_time"] = 0.0
            
            return stats_copy
    
    def get_progress(self) -> Tuple[int, int]:
        """
        Get progress information.
        
        Returns:
            Tuple of (completed_tasks, total_tasks)
        """
        with self.stats_lock:
            return (self.stats["completed_tasks"], self.stats["total_tasks"])


class DistributedIngestionCoordinator:
    """
    Coordinates distributed data ingestion across multiple workers.
    
    Handles task distribution, progress tracking, and result aggregation.
    """
    
    def __init__(self, worker_pool: WorkerPool):
        """
        Initialize the coordinator.
        
        Args:
            worker_pool: Worker pool for task execution
        """
        self.worker_pool = worker_pool
        self.total_items_ingested = 0
        self.lock = Lock()
    
    def ingest_collection(self, collection_name: str, items: List[Any],
                         processor: Callable[[Any], Dict]) -> List[TaskResult]:
        """
        Ingest a collection of items using parallel workers.
        
        Args:
            collection_name: Name of collection being ingested
            items: List of items to ingest
            processor: Function to process each item
            
        Returns:
            List of task results
        """
        logger.info(f"Starting ingestion of {len(items)} items from {collection_name}")
        
        # Register processor as task handler
        self.worker_pool.register_handler("ingest", processor)
        
        # Create tasks
        tasks = []
        for i, item in enumerate(items):
            task = Task(
                task_id=f"{collection_name}_{i}",
                task_type="ingest",
                params={"item": item, "collection": collection_name}
            )
            tasks.append(task)
        
        # Add tasks to worker pool
        self.worker_pool.add_tasks(tasks)
        
        # Run workers and wait for completion
        results = self.worker_pool.run_until_complete()
        
        # Update statistics
        successful = sum(1 for r in results if r.success)
        with self.lock:
            self.total_items_ingested += successful
        
        logger.info(f"Completed ingestion: {successful}/{len(items)} successful")
        
        return results
    
    def get_total_ingested(self) -> int:
        """Get total number of items ingested."""
        with self.lock:
            return self.total_items_ingested
