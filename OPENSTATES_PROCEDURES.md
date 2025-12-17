## OpenStates Bulk Data Ingestion Procedures

This document provides step-by-step procedures for operating the OpenStates bulk data ingestion system.

## Table of Contents

1. [Setup and Configuration](#setup-and-configuration)
2. [Database Initialization](#database-initialization)
3. [Data Ingestion Operations](#data-ingestion-operations)
4. [Monitoring and Maintenance](#monitoring-and-maintenance)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

---

## Setup and Configuration

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- OpenStates API key (obtain from https://openstates.org/api/)
- (Optional) BICAM library for congressional data

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/OpenDiscourse/bulk-data.git
   cd bulk-data
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   # Create .env file
   cat > .env << EOF
   OPENSTATES_API_KEY=your_api_key_here
   DATABASE_URL=postgresql://user:password@localhost:5432/openstates
   MAX_WORKERS=20
   RATE_LIMIT_PER_HOUR=5000
   EOF
   ```

4. **Verify PostgreSQL connection:**
   ```bash
   psql $DATABASE_URL -c "SELECT version();"
   ```

---

## Database Initialization

### Create Database

```bash
# Create PostgreSQL database
createdb openstates

# Or using psql
psql -c "CREATE DATABASE openstates;"
```

### Initialize Schema

```python
from openstates_db import OpenStatesDatabase

# Initialize database connection
db = OpenStatesDatabase(
    database_url='postgresql://user:password@localhost:5432/openstates'
)

# Create all tables
db.create_tables()
```

### Verify Schema

```sql
-- Connect to database
psql openstates

-- List all tables
\dt

-- Expected tables:
-- jurisdictions
-- legislative_sessions
-- people
-- bills
-- bill_sponsorships
-- bill_versions
-- bill_documents
-- votes
-- vote_records
-- committees
-- ingestion_logs
```

---

## Data Ingestion Operations

### 1. Full Initial Ingestion

Perform a complete initial data load for all states.

```python
from openstates_orchestrator import OpenStatesOrchestrator
import os

# Initialize orchestrator
orchestrator = OpenStatesOrchestrator(
    api_key=os.getenv('OPENSTATES_API_KEY'),
    database_url=os.getenv('DATABASE_URL'),
    num_workers=20  # 20 concurrent workers
)

# Setup database (if not already done)
orchestrator.setup_database()

# Step 1: Ingest all jurisdictions and sessions
print("Ingesting jurisdictions...")
jur_result = orchestrator.ingest_all_jurisdictions()
print(f"Processed {jur_result['processed']} jurisdictions")

# Step 2: Ingest all legislators
print("Ingesting people...")
people_result = orchestrator.ingest_people()
print(f"Processed {people_result['processed']} people")

# Step 3: Ingest bills for all jurisdictions
print("Ingesting bills...")
bills_result = orchestrator.ingest_all_bills()
print(f"Processed {bills_result['total_processed']} bills")

# Get final statistics
stats = orchestrator.get_ingestion_statistics()
print("Final Statistics:")
print(f"  Jurisdictions: {stats['database']['jurisdictions']}")
print(f"  People: {stats['database']['people']}")
print(f"  Bills: {stats['database']['bills']}")
print(f"  Votes: {stats['database']['votes']}")
```

**Estimated Time:** 
- Jurisdictions: ~5 minutes
- People: ~2-4 hours (depending on API rate limits)
- Bills (all states, recent session): ~8-12 hours

### 2. Single State Ingestion

Ingest data for a specific state.

```python
from openstates_orchestrator import OpenStatesOrchestrator
import os

orchestrator = OpenStatesOrchestrator(
    api_key=os.getenv('OPENSTATES_API_KEY'),
    database_url=os.getenv('DATABASE_URL'),
    num_workers=20
)

# Ingest North Carolina 2023 session
result = orchestrator.ingest_bills(
    jurisdiction='NC',
    session='2023',
    max_items=None  # All bills
)

print(f"Results: {result}")
```

### 3. Incremental Updates

Update existing data with recent changes.

```python
from openstates_orchestrator import OpenStatesOrchestrator
from datetime import datetime, timedelta
import os

orchestrator = OpenStatesOrchestrator(
    api_key=os.getenv('OPENSTATES_API_KEY'),
    database_url=os.getenv('DATABASE_URL'),
    num_workers=20
)

# Get updates from the last 7 days
since_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

# Update bills
result = orchestrator.ingest_bills(
    jurisdiction='NC',
    session='2023',
    updated_since=since_date
)

print(f"Updated {result['processed']} bills")
```

### 4. BICAM Data Integration

Ingest congressional data using BICAM library.

```python
from bicam_integration import BICAMDataManager, BICAMPostgreSQLIngester
import os

# Initialize BICAM manager
bicam_manager = BICAMDataManager(cache_dir='./bicam_cache')

# Download datasets
print("Downloading BICAM datasets...")
bicam_manager.download_all_datasets()

# Initialize ingester
ingester = BICAMPostgreSQLIngester(
    bicam_manager=bicam_manager,
    database_url=os.getenv('DATABASE_URL')
)

# Ingest all datasets
print("Ingesting BICAM data to PostgreSQL...")
result = ingester.ingest_all_datasets()

print(f"Ingested {result['successful']}/{result['total_datasets']} datasets")
print(f"Total rows: {result['total_rows_inserted']}")
```

---

## Monitoring and Maintenance

### Check Ingestion Status

```python
from openstates_orchestrator import OpenStatesOrchestrator
import os

orchestrator = OpenStatesOrchestrator(
    api_key=os.getenv('OPENSTATES_API_KEY'),
    database_url=os.getenv('DATABASE_URL')
)

# Get comprehensive statistics
stats = orchestrator.get_ingestion_statistics()

print("Database Statistics:")
for table, count in stats['database'].items():
    print(f"  {table}: {count}")

print("\nWorker Statistics:")
for key, value in stats['workers'].items():
    print(f"  {key}: {value}")

print("\nRecent Operations:")
for log in stats['recent_logs']:
    print(f"  {log['operation_type']} - {log['status']}")
    print(f"    Processed: {log['items_processed']}, Failed: {log['items_failed']}")
```

### Query Ingestion Logs

```sql
-- Recent ingestion operations
SELECT 
    operation_type,
    jurisdiction_id,
    status,
    items_processed,
    items_failed,
    start_time,
    end_time,
    EXTRACT(EPOCH FROM (end_time - start_time)) / 60 AS duration_minutes
FROM ingestion_logs
WHERE start_time > NOW() - INTERVAL '7 days'
ORDER BY start_time DESC;

-- Failed operations
SELECT 
    operation_type,
    jurisdiction_id,
    error_message,
    start_time
FROM ingestion_logs
WHERE status = 'failed'
ORDER BY start_time DESC
LIMIT 10;

-- Summary by operation type
SELECT 
    operation_type,
    COUNT(*) AS total_operations,
    SUM(items_processed) AS total_processed,
    SUM(items_failed) AS total_failed,
    AVG(items_processed) AS avg_processed
FROM ingestion_logs
WHERE status = 'completed'
GROUP BY operation_type;
```

### Database Maintenance

```sql
-- Update table statistics
ANALYZE;

-- Vacuum to reclaim space
VACUUM ANALYZE;

-- Reindex tables
REINDEX TABLE bills;
REINDEX TABLE votes;

-- Check database size
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Troubleshooting

### Common Issues

#### 1. API Rate Limit Exceeded

**Symptom:** HTTP 429 errors or rate limiter warnings

**Solution:**
```python
# Reduce rate limit
orchestrator = OpenStatesOrchestrator(
    api_key=os.getenv('OPENSTATES_API_KEY'),
    database_url=os.getenv('DATABASE_URL'),
    num_workers=10,  # Reduce workers
    rate_limit_per_hour=3000  # Lower rate limit
)
```

#### 2. Database Connection Errors

**Symptom:** `sqlalchemy.exc.OperationalError`

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection parameters
psql $DATABASE_URL -c "SELECT 1;"

# Increase connection pool
# In openstates_db.py, modify:
engine = create_engine(
    database_url,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

#### 3. Memory Issues with Large Datasets

**Symptom:** Out of memory errors during ingestion

**Solution:**
```python
# Process in smaller batches
result = orchestrator.ingest_bills(
    jurisdiction='NC',
    session='2023',
    max_items=1000  # Limit batch size
)

# Or reduce workers
orchestrator = OpenStatesOrchestrator(
    api_key=os.getenv('OPENSTATES_API_KEY'),
    database_url=os.getenv('DATABASE_URL'),
    num_workers=10  # Fewer workers use less memory
)
```

#### 4. Duplicate Key Violations

**Symptom:** `IntegrityError: duplicate key value violates unique constraint`

**Solution:**
- This is normal - the system uses upsert logic
- If errors persist, check data integrity:

```sql
-- Find duplicate bills
SELECT id, COUNT(*)
FROM bills
GROUP BY id
HAVING COUNT(*) > 1;

-- Clean up if needed (backup first!)
-- DELETE FROM bills WHERE id IN (SELECT id FROM duplicates);
```

#### 5. Stalled Workers

**Symptom:** Ingestion stops progressing

**Solution:**
```python
# Check worker statistics
stats = orchestrator.get_ingestion_statistics()
print(stats['workers'])

# If workers are stuck, restart the process
# The system will skip already-processed items
```

---

## Best Practices

### 1. Scheduling Regular Updates

Set up cron job for daily incremental updates:

```bash
# crontab -e
# Run daily at 2 AM
0 2 * * * /path/to/python /path/to/incremental_update.py >> /var/log/openstates_update.log 2>&1
```

**incremental_update.py:**
```python
#!/usr/bin/env python
from openstates_orchestrator import OpenStatesOrchestrator
from datetime import datetime, timedelta
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

orchestrator = OpenStatesOrchestrator(
    api_key=os.getenv('OPENSTATES_API_KEY'),
    database_url=os.getenv('DATABASE_URL'),
    num_workers=20
)

# Update last 7 days
since_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

# Update all jurisdictions
result = orchestrator.ingest_all_bills(updated_since=since_date)

logging.info(f"Update complete: {result['total_processed']} bills processed")
```

### 2. Backup Strategy

```bash
# Daily backup
pg_dump openstates | gzip > openstates_$(date +%Y%m%d).sql.gz

# Weekly full backup with retention
#!/bin/bash
BACKUP_DIR=/backups/openstates
DATE=$(date +%Y%m%d)

# Create backup
pg_dump openstates | gzip > $BACKUP_DIR/openstates_$DATE.sql.gz

# Keep only last 4 weeks
find $BACKUP_DIR -name "openstates_*.sql.gz" -mtime +28 -delete
```

### 3. Performance Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_bills_title_search ON bills USING GIN (to_tsvector('english', title));
CREATE INDEX idx_bills_subject ON bills USING GIN (subject);

-- Partition large tables
CREATE TABLE bills_2023 PARTITION OF bills
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

-- Use materialized views for reports
CREATE MATERIALIZED VIEW bill_summary AS
SELECT 
    j.abbreviation,
    ls.identifier as session,
    COUNT(*) as bill_count,
    COUNT(DISTINCT b.classification) as bill_types
FROM bills b
JOIN jurisdictions j ON b.jurisdiction_id = j.id
JOIN legislative_sessions ls ON b.legislative_session_id = ls.id
GROUP BY j.abbreviation, ls.identifier;

-- Refresh periodically
REFRESH MATERIALIZED VIEW bill_summary;
```

### 4. Error Handling

Always wrap ingestion operations in try-except blocks:

```python
import logging
from openstates_orchestrator import OpenStatesOrchestrator

logger = logging.getLogger(__name__)

def safe_ingest(orchestrator, jurisdiction, session):
    """Safely ingest data with error handling."""
    try:
        result = orchestrator.ingest_bills(
            jurisdiction=jurisdiction,
            session=session
        )
        logger.info(f"Successfully ingested {jurisdiction}/{session}")
        return result
    except Exception as e:
        logger.error(f"Failed to ingest {jurisdiction}/{session}: {e}")
        return None

# Use with all jurisdictions
orchestrator = OpenStatesOrchestrator(...)

states = ['NC', 'CA', 'TX', 'NY']
for state in states:
    safe_ingest(orchestrator, state, '2023')
```

### 5. Monitoring Alerts

Set up alerts for failures:

```python
def check_recent_failures():
    """Check for recent ingestion failures and alert."""
    from openstates_db import OpenStatesDatabase
    import os
    
    db = OpenStatesDatabase(os.getenv('DATABASE_URL'))
    logs = db.get_recent_ingestion_logs(limit=10)
    
    failures = [log for log in logs if log['status'] == 'failed']
    
    if failures:
        # Send alert (email, Slack, etc.)
        message = f"Warning: {len(failures)} ingestion failures detected"
        for failure in failures:
            message += f"\n- {failure['operation_type']}: {failure['error_message']}"
        
        # Send notification (implement your notification method)
        send_alert(message)
```

---

## Advanced Operations

### Parallel State Processing

Process multiple states simultaneously:

```python
from concurrent.futures import ThreadPoolExecutor
from openstates_orchestrator import OpenStatesOrchestrator

def process_state(state_abbr):
    """Process a single state."""
    orchestrator = OpenStatesOrchestrator(...)
    return orchestrator.ingest_bills(jurisdiction=state_abbr, session='2023')

states = ['NC', 'CA', 'TX', 'NY', 'FL']

with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(process_state, states)

for state, result in zip(states, results):
    print(f"{state}: {result['processed']} bills processed")
```

### Custom Data Export

Export data in custom formats:

```python
def export_bills_to_csv(jurisdiction, session, output_file):
    """Export bills to CSV."""
    from openstates_db import OpenStatesDatabase
    import csv
    import os
    
    db = OpenStatesDatabase(os.getenv('DATABASE_URL'))
    
    with db.get_session() as session:
        from openstates_models import Bill, Jurisdiction, LegislativeSession
        
        bills = session.query(Bill).join(
            Jurisdiction
        ).filter(
            Jurisdiction.abbreviation == jurisdiction
        ).all()
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Identifier', 'Title', 'Classification'])
            
            for bill in bills:
                writer.writerow([
                    bill.id,
                    bill.identifier,
                    bill.title,
                    bill.classification
                ])

# Usage
export_bills_to_csv('NC', '2023', 'nc_bills_2023.csv')
```

---

## Support and Resources

- **OpenStates API Documentation:** https://docs.openstates.org/api-v3/
- **BICAM Documentation:** https://py.docs.bicam.net/
- **Repository Issues:** https://github.com/OpenDiscourse/bulk-data/issues
- **Community Chat:** Contact repository maintainers

For additional help, please file an issue on GitHub or contact the development team.
