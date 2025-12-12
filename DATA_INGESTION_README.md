# Data Ingestion System

A comprehensive system for ingesting bulk data from api.congress.gov and govinfo.gov with support for:
- Rate limiting
- Pagination tracking
- Data deduplication
- Parallel worker processing

## Features

### API Support
- **api.congress.gov**: Bills, amendments, laws, members, committee reports, Congressional Record, nominations
- **api.govinfo.gov**: Collections, packages, published documents, search
- **govinfo.gov/bulkdata**: Bulk data downloads for BILLS, CFR, FR, CREC, PLAW, and more

### Rate Limiting
- Automatic rate limiting respecting API limits:
  - api.congress.gov: 5,000 requests/hour
  - govinfo.gov API: 1,000 requests/hour
  - Built-in throttling with per-minute and per-hour tracking

### Pagination
- Automatic pagination with configurable limits
- Offset tracking to resume from interruptions
- Handles different pagination styles across APIs

### Data Tracking
- SQLite-based tracking to prevent duplicate ingestion
- Tracks processed items with metadata
- Supports resuming interrupted operations

### Parallel Processing
- Configurable worker pool for parallel ingestion
- Task queue management with automatic retries
- Progress tracking and statistics

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Configuration

### API Keys

You'll need API keys from api.data.gov:
1. Visit https://api.data.gov/signup/
2. Sign up for a free API key
3. Set environment variables:

```bash
export CONGRESS_API_KEY="your_congress_api_key"
export GOVINFO_API_KEY="your_govinfo_api_key"
```

### MCP Server Configuration

The system includes an MCP server configuration in `mcp_server_config.json` that defines:
- API endpoints and their parameters
- Rate limits for each service
- Pagination settings
- Available collections

## Usage

### Basic Example

```python
from orchestrator import DataIngestionOrchestrator

# Initialize orchestrator
orchestrator = DataIngestionOrchestrator(
    congress_api_key="YOUR_API_KEY",
    govinfo_api_key="YOUR_API_KEY",
    num_workers=8,
    output_dir="./data"
)

# Ingest bills from 118th Congress
results = orchestrator.ingest_congress_bills(
    congress=118,
    bill_type="hr",
    max_items=100
)

print(f"Ingested {results['successful']} bills")
```

### Running Examples

```bash
# Run interactive examples
python example_usage.py
```

Choose from:
1. Congress Bills - Ingest bills from api.congress.gov
2. GovInfo Collection - Ingest from api.govinfo.gov
3. Bulk Data - Download from govinfo.gov/bulkdata
4. Full Pipeline - Run all ingestion methods
5. All examples - Run everything

### Advanced Usage

#### Congress API

```python
# Ingest bills with specific filters
orchestrator.ingest_congress_bills(
    congress=118,      # 118th Congress
    bill_type="hr",    # House Resolutions
    max_items=500      # Limit to 500 items
)

# The system automatically:
# - Respects rate limits (5,000 req/hour)
# - Handles pagination with offset tracking
# - Skips already-ingested items
# - Uses parallel workers for processing
```

#### GovInfo API

```python
# Ingest collection by date range
orchestrator.ingest_govinfo_collection(
    collection_code="BILLS",
    start_date="2024-01-01",
    end_date="2024-12-31",
    max_items=1000
)
```

#### Bulk Data

```python
# Download bulk data files
orchestrator.ingest_bulkdata_collection(
    collection="FR",        # Federal Register
    path="2024/01",        # January 2024
    max_depth=3            # Directory depth to traverse
)
```

## Architecture

### Components

1. **Rate Limiter** (`rate_limiter.py`)
   - Thread-safe rate limiting
   - Sliding window tracking
   - Per-minute and per-hour limits

2. **Data Tracker** (`data_tracker.py`)
   - SQLite-based persistence
   - Deduplication using unique IDs
   - Metadata storage

3. **API Client** (`api_client.py`)
   - Unified interface for different APIs
   - Automatic pagination
   - Built-in rate limiting

4. **Worker Pool** (`worker_pool.py`)
   - Parallel task execution
   - Automatic retries on failure
   - Progress tracking

5. **Orchestrator** (`orchestrator.py`)
   - High-level coordination
   - Manages all components
   - Provides simple API

### Data Flow

```
User Request
    ↓
Orchestrator
    ↓
API Client (with rate limiting)
    ↓
Data Tracker (check for duplicates)
    ↓
Worker Pool (parallel processing)
    ↓
Save to disk + Update tracker
```

## Rate Limiting Details

The system implements sophisticated rate limiting:

- **Per-minute limits**: Prevent bursting beyond allowed rates
- **Per-hour limits**: Stay within hourly quotas
- **Automatic throttling**: Waits when limits are approached
- **Statistics tracking**: Monitor throttling behavior

Example rate limiter stats:
```python
stats = orchestrator.get_overall_stats()
print(stats['rate_limiters']['congress_api'])
# {
#   'total_requests': 1500,
#   'total_throttled': 12,
#   'current_hour_count': 1500,
#   'requests_per_hour_limit': 5000
# }
```

## Data Tracking

Prevents duplicate ingestion:

```python
# First run: ingests 100 items
results1 = orchestrator.ingest_congress_bills(max_items=100)
# Saves items and marks them as processed

# Second run: skips already-ingested items
results2 = orchestrator.ingest_congress_bills(max_items=100)
# Only ingests new items since last run
```

Track ingestion progress:
```python
stats = orchestrator.get_overall_stats()
for tracker_name, tracker_stats in stats['trackers'].items():
    print(f"{tracker_name}: {tracker_stats['total_items']} items")
```

## Parallel Workers

Configure worker count based on your system:

```python
# More workers = faster ingestion (but more memory/CPU)
orchestrator = DataIngestionOrchestrator(
    num_workers=16,  # 16 parallel workers
    # ...
)
```

Worker statistics:
```python
stats = orchestrator.get_overall_stats()
print(stats['workers'])
# {
#   'total_tasks': 500,
#   'completed_tasks': 485,
#   'failed_tasks': 15,
#   'retried_tasks': 10,
#   'avg_execution_time': 1.23
# }
```

## API Endpoints Breakdown

### api.congress.gov

| Endpoint | Description | Pagination | Rate Limit |
|----------|-------------|------------|------------|
| `/bill` | Bills data | Yes (250/page) | 5000/hour |
| `/amendment` | Amendments | Yes (250/page) | 5000/hour |
| `/law` | Laws | Yes (250/page) | 5000/hour |
| `/member` | Members of Congress | Yes (250/page) | 5000/hour |
| `/committee-report` | Committee reports | Yes (250/page) | 5000/hour |
| `/congressional-record` | Congressional Record | Yes (250/page) | 5000/hour |
| `/nomination` | Nominations | Yes (250/page) | 5000/hour |

### api.govinfo.gov

| Endpoint | Description | Pagination | Rate Limit |
|----------|-------------|------------|------------|
| `/collections` | List collections | No | 1000/hour |
| `/collections/{code}/{date}` | Collection by date | Yes (1000/page) | 1000/hour |
| `/packages/{id}/summary` | Package details | No | 1000/hour |
| `/published/{date}` | Published documents | Yes (1000/page) | 1000/hour |
| `/search` | Search documents | Yes (1000/page) | 1000/hour |

### govinfo.gov/bulkdata

| Collection | Description | Format |
|------------|-------------|--------|
| BILLS | Congressional Bills | XML, JSON |
| BILLSTATUS | Bill Status | XML, JSON |
| CFR | Code of Federal Regulations | XML, JSON |
| ECFR | Electronic CFR | XML, JSON |
| FR | Federal Register | XML, JSON |
| CREC | Congressional Record | XML, JSON |
| PLAW | Public and Private Laws | XML, JSON |
| STATUTE | Statutes at Large | XML, JSON |
| USCOURTS | Court Opinions | XML, JSON |
| PPP | Public Papers of Presidents | XML, JSON |

## Error Handling

The system includes comprehensive error handling:

- **Automatic retries**: Failed tasks are retried up to 3 times
- **Graceful degradation**: Individual failures don't stop the entire process
- **Error logging**: All errors are logged with full stack traces
- **Statistics tracking**: Failed/retried tasks are tracked

## Performance Tuning

### For Maximum Speed
```python
orchestrator = DataIngestionOrchestrator(
    num_workers=32,  # More workers
    # ...
)
```

### For Resource-Constrained Systems
```python
orchestrator = DataIngestionOrchestrator(
    num_workers=2,   # Fewer workers
    # ...
)
```

### For Rate Limit Compliance
The system automatically handles rate limiting, but you can monitor:
```python
stats = orchestrator.get_overall_stats()
throttled = stats['rate_limiters']['congress_api']['total_throttled']
if throttled > 100:
    print("Consider reducing worker count to avoid excessive throttling")
```

## Troubleshooting

### "No API key configured"
Set environment variables:
```bash
export CONGRESS_API_KEY="your_key"
export GOVINFO_API_KEY="your_key"
```

### "Rate limit exceeded"
The system should handle this automatically, but if you see errors:
- Reduce `num_workers`
- The rate limiter will automatically throttle

### "Database is locked"
SQLite has concurrency limits. For high-volume ingestion:
- Use fewer workers
- Or switch to PostgreSQL (requires modifying data_tracker.py)

## Future Enhancements

Potential improvements:
- PostgreSQL support for better concurrency
- Incremental updates (only fetch new/changed items)
- Data validation and schema checking
- Export to different formats (CSV, Parquet, etc.)
- Web dashboard for monitoring
- Kubernetes deployment support

## License

This project is released into the public domain, consistent with the bulk-data repository.

## Contributing

Contributions welcome! Please ensure:
- Code follows existing patterns
- Rate limiting is respected
- Tests pass (if adding tests)
- Documentation is updated
