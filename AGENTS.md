# Agents Documentation

## Overview

This document describes the autonomous agents and automated workflows implemented in the OpenStates bulk data ingestion system. These agents handle various aspects of data collection, processing, monitoring, and maintenance.

## Architecture

The system implements a multi-agent architecture where specialized agents work together to manage the entire data pipeline:

```
┌─────────────────────────────────────────────────────────┐
│                   Orchestration Layer                    │
│              (OpenStatesOrchestrator)                    │
└─────────────────┬───────────────────────────────────────┘
                  │
      ┌───────────┴───────────┬────────────┬──────────────┐
      │                       │            │              │
┌─────▼──────┐   ┌───────────▼──┐  ┌─────▼─────┐  ┌────▼──────┐
│  API Agent │   │ Worker Pool  │  │  Database │  │  Monitor  │
│            │   │   (20 workers)│  │   Agent   │  │   Agent   │
└─────┬──────┘   └───────┬──────┘  └─────┬─────┘  └────┬──────┘
      │                  │               │              │
      │                  │               │              │
      └──────────────────┴───────────────┴──────────────┘
                           │
                    ┌──────▼──────┐
                    │ Rate Limiter│
                    │    Agent    │
                    └─────────────┘
```

## Agent Types

### 1. API Agent

**Module:** `openstates_client.py`

**Purpose:** Handles all interactions with external APIs (OpenStates API)

**Capabilities:**
- Makes authenticated HTTP requests
- Handles pagination automatically
- Implements retry logic for failed requests
- Parses and normalizes API responses

**Key Methods:**
```python
class OpenStatesClient:
    def search_bills(self, jurisdiction, session, **kwargs)
    def search_people(self, jurisdiction, **kwargs)
    def get_bill(self, bill_id, include=[])
    def get_jurisdictions(self)
```

**Configuration:**
```python
client = OpenStatesClient(
    api_key='your_api_key',
    rate_limiter=rate_limiter
)
```

**Agent Behavior:**
- Waits for rate limiter before making requests
- Logs all API calls for audit trail
- Automatically retries on transient failures
- Yields results incrementally for memory efficiency

---

### 2. Worker Pool Agent

**Module:** `worker_pool.py`

**Purpose:** Manages parallel task execution with configurable concurrency

**Capabilities:**
- Executes up to 20 concurrent tasks
- Distributes work across worker threads
- Handles task failures and retries
- Tracks task execution statistics

**Key Components:**
```python
class WorkerPool:
    - num_workers: 20 (configurable)
    - task_queue: Thread-safe queue
    - executor: ThreadPoolExecutor
    
class DistributedIngestionCoordinator:
    - Coordinates workers
    - Aggregates results
    - Tracks progress
```

**Agent Behavior:**
- Pulls tasks from queue
- Executes task handlers
- Retries failed tasks (up to 3 times)
- Reports execution statistics

**Usage Pattern:**
```python
# Register handler
pool.register_handler('process_bill', handler_function)

# Add tasks
pool.add_tasks(task_list)

# Execute with workers
results = pool.run_until_complete()
```

---

### 3. Database Agent

**Module:** `openstates_db.py`

**Purpose:** Manages all database operations and data persistence

**Capabilities:**
- CRUD operations on all entities
- Upsert logic for data updates
- Transaction management
- Connection pooling

**Key Methods:**
```python
class OpenStatesDatabase:
    def upsert_jurisdiction(self, data)
    def upsert_person(self, data)
    def upsert_bill(self, data, session_id)
    def upsert_vote(self, data, bill_id)
```

**Agent Behavior:**
- Uses context managers for safe transactions
- Implements upsert patterns to handle updates
- Cascades related entity operations
- Logs all database operations

**Transaction Management:**
```python
with db.get_session() as session:
    # All operations in this block are atomic
    db.upsert_bill(bill_data, session_id)
    # Automatically commits or rolls back
```

---

### 4. Rate Limiter Agent

**Module:** `rate_limiter.py`

**Purpose:** Enforces API rate limits to prevent throttling

**Capabilities:**
- Sliding window rate limiting
- Per-minute and per-hour limits
- Thread-safe operation
- Statistics tracking

**Algorithm:**
```
Token Bucket with Sliding Window:
1. Track timestamps of recent requests
2. Clean old timestamps outside window
3. Check if limit would be exceeded
4. Wait if necessary
5. Record new request timestamp
```

**Configuration:**
```python
rate_limiter = RateLimiter(
    requests_per_hour=5000,
    requests_per_minute=83
)
```

**Agent Behavior:**
- Monitors request frequency
- Blocks threads when limit approached
- Releases threads when tokens available
- Maintains accurate statistics

---

### 5. Monitoring Agent

**Module:** Implemented within `openstates_orchestrator.py`

**Purpose:** Tracks system health and ingestion progress

**Capabilities:**
- Real-time progress tracking with tqdm
- Ingestion log management
- Statistics aggregation
- Performance metrics

**Key Features:**
```python
# Progress tracking
for item in tqdm(items, desc="Ingesting bills"):
    process_item(item)

# Ingestion logging
log_id = db.start_ingestion_log("bills", jurisdiction="NC")
db.update_ingestion_log(log_id, items_processed=100, status="completed")

# Statistics
stats = orchestrator.get_ingestion_statistics()
```

**Monitored Metrics:**
- Items processed/failed
- Execution time per task
- API request statistics
- Database entity counts
- Worker pool utilization

---

## Agent Workflows

### Workflow 1: Full Jurisdiction Ingestion

**Participants:** API Agent, Worker Pool, Database Agent, Rate Limiter, Monitor

**Sequence:**
```
1. Orchestrator → API Agent: Fetch jurisdictions
2. API Agent → Rate Limiter: Check rate limit
3. Rate Limiter → API Agent: Grant/delay request
4. API Agent → Orchestrator: Return jurisdiction list
5. Orchestrator → Database Agent: Upsert each jurisdiction
6. Monitor: Track progress and log results
```

**Code Example:**
```python
def ingest_all_jurisdictions(self):
    log_id = self.database.start_ingestion_log("jurisdictions")
    
    jurisdictions = self.api_client.get_jurisdictions()
    
    for jur in tqdm(jurisdictions, desc="Ingesting jurisdictions"):
        self.database.upsert_jurisdiction(jur)
    
    self.database.update_ingestion_log(log_id, status='completed')
```

---

### Workflow 2: Parallel Bill Ingestion

**Participants:** All agents coordinated by Orchestrator

**Sequence:**
```
1. Orchestrator → API Agent: Search bills (paginated)
2. API Agent: Yields bills incrementally
3. Orchestrator → Worker Pool: Distribute bill processing tasks
4. Worker Pool: Creates 20 worker threads
5. Each Worker:
   a. Worker → Rate Limiter: Wait for token
   b. Worker → API Agent: Get full bill details
   c. Worker → Database Agent: Upsert bill
   d. Worker → Monitor: Report completion
6. Coordinator: Aggregates results
7. Monitor: Update ingestion log
```

**Code Example:**
```python
def ingest_bills(self, jurisdiction, session):
    # Collect bills
    bills = list(self.api_client.search_bills(jurisdiction, session))
    
    # Define worker task
    def process_bill(params):
        bill_data = self.api_client.get_bill(params["bill_id"])
        self.database.upsert_bill(bill_data, params["session_id"])
        return {"status": "success"}
    
    # Process with workers
    results = self.coordinator.ingest_collection(
        "bills",
        [{"bill_id": b["id"], "session_id": sid} for b in bills],
        process_bill
    )
```

---

### Workflow 3: Incremental Update

**Participants:** API Agent, Database Agent, Monitor

**Sequence:**
```
1. Monitor: Read last update timestamp from database
2. Orchestrator → API Agent: Search bills updated since timestamp
3. API Agent: Returns only changed bills
4. Orchestrator → Worker Pool: Process changed bills
5. Workers → Database Agent: Upsert updated bills
6. Monitor: Log incremental update completion
```

**Code Example:**
```python
def incremental_update(self, jurisdiction, session, since_date):
    result = self.ingest_bills(
        jurisdiction=jurisdiction,
        session=session,
        updated_since=since_date  # Only bills updated after this date
    )
```

---

## Agent Communication

### Message Passing

Agents communicate through:

1. **Function calls** (synchronous)
   ```python
   result = api_client.get_bill(bill_id)
   ```

2. **Task queues** (asynchronous)
   ```python
   worker_pool.add_task(Task(task_id=id, params=params))
   ```

3. **Callbacks** (event-driven)
   ```python
   def on_complete(result):
       database.update_log(result)
   ```

### Shared State

Agents share state through:

1. **Database** - Persistent state
2. **In-memory structures** - Temporary state
3. **Statistics objects** - Performance metrics

---

## Agent Configuration

### Environment Variables

```bash
# API configuration
OPENSTATES_API_KEY=your_api_key_here
BICAM_CACHE_DIR=/path/to/cache

# Database configuration
DATABASE_URL=postgresql://user:pass@host:port/db

# Worker pool configuration
MAX_WORKERS=20

# Rate limiting configuration
RATE_LIMIT_PER_HOUR=5000
RATE_LIMIT_PER_MINUTE=83
```

### Programmatic Configuration

```python
from openstates_orchestrator import OpenStatesOrchestrator

orchestrator = OpenStatesOrchestrator(
    api_key=api_key,
    database_url=db_url,
    num_workers=20,
    rate_limit_per_hour=5000
)

# Access individual agents
orchestrator.api_client        # API Agent
orchestrator.database          # Database Agent
orchestrator.worker_pool       # Worker Pool
orchestrator.rate_limiter      # Rate Limiter
orchestrator.coordinator       # Coordination Agent
```

---

## Agent Monitoring and Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Monitor Agent Activity

```python
# Worker pool statistics
worker_stats = orchestrator.worker_pool.get_stats()
print(f"Total tasks: {worker_stats['total_tasks']}")
print(f"Completed: {worker_stats['completed_tasks']}")
print(f"Failed: {worker_stats['failed_tasks']}")
print(f"Avg execution time: {worker_stats['avg_execution_time']}")

# Rate limiter statistics
rate_stats = orchestrator.rate_limiter.get_stats()
print(f"Total requests: {rate_stats['total_requests']}")
print(f"Throttled: {rate_stats['total_throttled']}")

# Database statistics
db_stats = orchestrator.get_ingestion_statistics()
print(f"Bills in DB: {db_stats['database']['bills']}")
```

### Query Agent Logs

```sql
-- Recent agent operations
SELECT 
    operation_type,
    status,
    items_processed,
    start_time,
    end_time
FROM ingestion_logs
ORDER BY start_time DESC
LIMIT 10;
```

---

## Agent Best Practices

### 1. Resource Management

**Problem:** Agents may exhaust system resources

**Solution:**
```python
# Limit concurrent operations
orchestrator = OpenStatesOrchestrator(
    num_workers=10,  # Reduce if memory constrained
    rate_limit_per_hour=3000  # Reduce if API throttling occurs
)

# Use context managers for cleanup
with orchestrator.database.get_session() as session:
    # Resources automatically released
    pass
```

### 2. Error Handling

**Problem:** Agent failures can cascade

**Solution:**
```python
def safe_process(item):
    try:
        return process_item(item)
    except Exception as e:
        logger.error(f"Failed to process {item}: {e}")
        return None

# Register safe handler
worker_pool.register_handler("safe_process", safe_process)
```

### 3. Graceful Shutdown

**Problem:** Interrupting agents can corrupt data

**Solution:**
```python
import signal
import sys

def signal_handler(sig, frame):
    logger.info("Gracefully shutting down workers...")
    orchestrator.worker_pool.stop(wait=True)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
```

### 4. Agent Health Checks

**Implementation:**
```python
def check_agent_health(orchestrator):
    """Verify all agents are functioning."""
    checks = {
        "api_client": orchestrator.api_client is not None,
        "database": orchestrator.database.table_exists("bills"),
        "worker_pool": orchestrator.worker_pool.is_running or True,
        "rate_limiter": orchestrator.rate_limiter is not None
    }
    
    all_healthy = all(checks.values())
    return {"healthy": all_healthy, "checks": checks}
```

---

## Future Agent Enhancements

### Planned Improvements

1. **Self-Healing Agent**
   - Automatically retry failed operations
   - Detect and recover from stuck workers
   - Alert on persistent failures

2. **Optimization Agent**
   - Dynamically adjust worker count
   - Optimize batch sizes
   - Tune rate limits based on API responses

3. **Caching Agent**
   - Cache frequently accessed data
   - Reduce redundant API calls
   - Implement intelligent cache invalidation

4. **Validation Agent**
   - Verify data integrity after ingestion
   - Detect anomalies in data
   - Flag incomplete or inconsistent records

5. **Scheduler Agent**
   - Manage periodic ingestion tasks
   - Prioritize urgent updates
   - Balance load across time windows

---

## Agent Development Guidelines

### Creating a New Agent

1. **Define Agent Purpose**
   - Single, well-defined responsibility
   - Clear input/output contract

2. **Implement Agent Class**
   ```python
   class NewAgent:
       def __init__(self, config):
           self.config = config
           self.logger = logging.getLogger(__name__)
       
       def process(self, input_data):
           """Main agent logic."""
           try:
               # Process data
               result = self._do_work(input_data)
               return result
           except Exception as e:
               self.logger.error(f"Agent failed: {e}")
               raise
   ```

3. **Add Monitoring**
   ```python
   def process(self, input_data):
       start_time = time.time()
       result = self._do_work(input_data)
       duration = time.time() - start_time
       
       self.logger.info(f"Processed in {duration:.2f}s")
       return result
   ```

4. **Integrate with Orchestrator**
   ```python
   class OpenStatesOrchestrator:
       def __init__(self, ...):
           # ... existing code ...
           self.new_agent = NewAgent(config)
   ```

5. **Write Tests**
   ```python
   def test_new_agent():
       agent = NewAgent(config)
       result = agent.process(test_data)
       assert result is not None
   ```

---

## Conclusion

The multi-agent architecture provides a robust, scalable system for bulk data ingestion. Each agent has a specific responsibility and communicates through well-defined interfaces, making the system maintainable and extensible.

For questions or suggestions about agent design, please open an issue on GitHub.
