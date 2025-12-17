# OpenStates Bulk Data Ingestion Framework

A comprehensive, production-ready framework for bulk ingestion of U.S. legislative data from OpenStates.org into PostgreSQL, with support for concurrent processing, rate limiting, and comprehensive monitoring.

## Features

- ✅ **20 Concurrent Workers** - Parallel processing for maximum throughput
- ✅ **PostgreSQL Storage** - Comprehensive relational schema for all entities
- ✅ **Rate Limiting** - Respects API limits with smart throttling
- ✅ **Progress Tracking** - Real-time progress bars and detailed logging
- ✅ **Incremental Updates** - Efficient updates of changed data only
- ✅ **Error Handling** - Robust retry logic and error recovery
- ✅ **BICAM Integration** - Congressional data from congress.gov
- ✅ **Comprehensive Docs** - Full documentation for all components
- ✅ **Test Coverage** - Extensive test suite
- ✅ **Pythonic Code** - Clean, well-documented, type-hinted code

## Architecture

```
┌─────────────────────────────────────────┐
│   OpenStates Orchestrator               │
│   (20 concurrent workers)               │
└──────────┬──────────────────────────────┘
           │
    ┌──────┴──────┬───────────┬──────────┐
    │             │           │          │
┌───▼───┐   ┌────▼────┐  ┌───▼────┐  ┌──▼───┐
│  API  │   │Database │  │ Rate   │  │ BICAM│
│Client │   │ Layer   │  │Limiter │  │ Integ│
└───────┘   └─────────┘  └────────┘  └──────┘
    │             │           │          │
    └─────────────┴───────────┴──────────┘
                  │
          ┌───────▼────────┐
          │  PostgreSQL DB │
          │  (Full Schema) │
          └────────────────┘
```

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/OpenDiscourse/bulk-data.git
cd bulk-data

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
OPENSTATES_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:pass@localhost:5432/openstates
MAX_WORKERS=20
```

Get your OpenStates API key from: https://openstates.org/api/

### 3. Initialize Database

```python
from openstates_db import OpenStatesDatabase

db = OpenStatesDatabase('postgresql://localhost/openstates')
db.create_tables()
```

### 4. Run Your First Ingestion

```python
from openstates_orchestrator import OpenStatesOrchestrator
import os

# Initialize
orchestrator = OpenStatesOrchestrator(
    api_key=os.getenv('OPENSTATES_API_KEY'),
    database_url=os.getenv('DATABASE_URL'),
    num_workers=20
)

# Ingest all jurisdictions
orchestrator.ingest_all_jurisdictions()

# Ingest bills from North Carolina
orchestrator.ingest_bills(jurisdiction='NC', session='2023')

# Get statistics
stats = orchestrator.get_ingestion_statistics()
print(f"Bills in database: {stats['database']['bills']}")
```

### 5. Run Example Script

```bash
python openstates_example.py
```

## Data Model

The framework stores data in a comprehensive PostgreSQL schema:

### Core Entities

- **Jurisdictions** - U.S. states and territories
- **Legislative Sessions** - Session information for each jurisdiction
- **People** - Legislators and officials
- **Bills** - Legislative bills and resolutions
- **Votes** - Roll call votes with individual vote records
- **Committees** - Legislative committees
- **Sponsorships** - Bill sponsor relationships
- **Versions/Documents** - Bill texts and related documents

See [OPENSTATES_DATA_MODELS.md](OPENSTATES_DATA_MODELS.md) for complete schema documentation.

## Usage Examples

### Ingest All States

```python
from openstates_orchestrator import OpenStatesOrchestrator
import os

orchestrator = OpenStatesOrchestrator(
    api_key=os.getenv('OPENSTATES_API_KEY'),
    database_url=os.getenv('DATABASE_URL'),
    num_workers=20
)

# Ingest all jurisdictions
orchestrator.setup_database()
orchestrator.ingest_all_jurisdictions()

# Ingest bills from all states (most recent session)
result = orchestrator.ingest_all_bills()
print(f"Processed {result['total_processed']} bills")
```

### Incremental Updates

```python
from datetime import datetime, timedelta

# Get updates from last 7 days
since_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

result = orchestrator.ingest_bills(
    jurisdiction='NC',
    session='2023',
    updated_since=since_date
)
```

### Query Data

```python
from openstates_db import OpenStatesDatabase
from openstates_models import Bill, Person, Vote

db = OpenStatesDatabase(database_url)

with db.get_session() as session:
    # Get all bills from NC 2023 session
    bills = session.query(Bill).filter(
        Bill.jurisdiction_id.like('%/state:nc/%')
    ).all()
    
    # Get legislators
    people = session.query(Person).filter(
        Person.party == 'Democratic'
    ).all()
    
    # Get votes
    votes = session.query(Vote).filter(
        Vote.result == 'pass'
    ).all()
```

### BICAM Integration

```python
from bicam_integration import BICAMDataManager, BICAMPostgreSQLIngester

# Initialize BICAM
bicam = BICAMDataManager(cache_dir='./bicam_cache')

# Download congressional data
bicam.download_dataset('bills')
bicam.download_dataset('members')

# Ingest to PostgreSQL
ingester = BICAMPostgreSQLIngester(bicam, database_url)
result = ingester.ingest_all_datasets()
print(f"Ingested {result['total_rows_inserted']} rows")
```

## Documentation

- **[Data Models](OPENSTATES_DATA_MODELS.md)** - Complete database schema documentation
- **[Procedures](OPENSTATES_PROCEDURES.md)** - Step-by-step operational procedures
- **[Agents](AGENTS.md)** - Multi-agent architecture documentation
- **[API Reference](API_REFERENCE.md)** - API client documentation

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest test_openstates.py -v

# Run with coverage
pytest test_openstates.py --cov=. --cov-report=html

# Run specific test class
pytest test_openstates.py::TestOpenStatesClient -v
```

## Configuration Options

### Environment Variables

```bash
# Required
OPENSTATES_API_KEY=your_api_key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/openstates

# Performance
MAX_WORKERS=20                    # Number of concurrent workers
RATE_LIMIT_PER_HOUR=5000         # API requests per hour
RATE_LIMIT_PER_MINUTE=83         # API requests per minute

# Optional
LOG_LEVEL=INFO                    # Logging level
BICAM_CACHE_DIR=./bicam_cache    # BICAM cache directory
```

### Programmatic Configuration

```python
orchestrator = OpenStatesOrchestrator(
    api_key='your_key',
    database_url='postgresql://...',
    num_workers=20,              # Concurrent workers
    rate_limit_per_hour=5000     # API rate limit
)
```

## Monitoring

### Real-time Progress

The framework uses `tqdm` for real-time progress tracking:

```
Ingesting bills: 100%|████████████| 1234/1234 [02:15<00:00, 9.12it/s]
```

### Database Logs

All operations are logged to the `ingestion_logs` table:

```sql
SELECT * FROM ingestion_logs 
ORDER BY start_time DESC 
LIMIT 10;
```

### Statistics API

```python
stats = orchestrator.get_ingestion_statistics()

print(f"Database counts: {stats['database']}")
print(f"Worker stats: {stats['workers']}")
print(f"Recent logs: {stats['recent_logs']}")
```

## Performance

### Benchmarks

On a typical system with good network connectivity:

- **Jurisdictions**: ~5 minutes for all 52 jurisdictions
- **People**: ~2-4 hours for all ~7,500 legislators
- **Bills**: ~100-200 bills per minute with 20 workers
- **Full state**: ~30-60 minutes per state (recent session)

### Optimization Tips

1. **Increase workers** for faster processing (up to API limits)
2. **Use incremental updates** for regular maintenance
3. **Partition large tables** for better query performance
4. **Create indexes** on frequently queried columns
5. **Use connection pooling** for high concurrency

## Troubleshooting

### Common Issues

#### API Rate Limiting

```python
# Reduce workers and rate limit
orchestrator = OpenStatesOrchestrator(
    num_workers=10,
    rate_limit_per_hour=3000
)
```

#### Database Connection Pool

```python
# Increase pool size in openstates_db.py
engine = create_engine(
    database_url,
    pool_size=30,
    max_overflow=50
)
```

#### Memory Issues

```python
# Process in smaller batches
result = orchestrator.ingest_bills(
    jurisdiction='NC',
    session='2023',
    max_items=1000  # Process 1000 at a time
)
```

See [OPENSTATES_PROCEDURES.md](OPENSTATES_PROCEDURES.md#troubleshooting) for more solutions.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Add appropriate license]

## Credits

- **OpenStates**: https://openstates.org/
- **BICAM**: https://py.docs.bicam.net/
- Data provided by state legislatures

## Support

- **Issues**: https://github.com/OpenDiscourse/bulk-data/issues
- **Documentation**: See docs/ directory
- **OpenStates API**: https://docs.openstates.org/api-v3/

## Changelog

### v1.0.0 (2024-01-XX)

- Initial release
- 20 concurrent workers
- Full OpenStates v3 API coverage
- PostgreSQL storage
- BICAM integration
- Comprehensive documentation
- Test suite

## Roadmap

- [ ] GraphQL API support
- [ ] Real-time event streaming
- [ ] Web dashboard
- [ ] Elasticsearch integration
- [ ] Docker containerization
- [ ] Kubernetes deployment configs
- [ ] Data export utilities
- [ ] API server for querying data
