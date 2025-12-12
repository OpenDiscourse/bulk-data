# Quick Start Guide

## Prerequisites

1. Python 3.7 or higher
2. API keys from api.data.gov (free)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API Keys

Visit https://api.data.gov/signup/ and sign up for a free API key.

### 3. Set Environment Variables

```bash
# Linux/Mac
export CONGRESS_API_KEY="your_congress_api_key"
export GOVINFO_API_KEY="your_govinfo_api_key"

# Windows
set CONGRESS_API_KEY=your_congress_api_key
set GOVINFO_API_KEY=your_govinfo_api_key
```

## Quick Start

### Option 1: Run Interactive Examples

```bash
python example_usage.py
```

Follow the prompts to choose which example to run.

### Option 2: Use Python API Directly

```python
from orchestrator import DataIngestionOrchestrator

# Initialize
orchestrator = DataIngestionOrchestrator(
    congress_api_key="YOUR_KEY",
    num_workers=8,
    output_dir="./my_data"
)

# Ingest data
results = orchestrator.ingest_congress_bills(
    congress=118,
    max_items=50
)

print(f"Ingested {results['successful']} bills")
```

### Option 3: Custom Script

Create a file `my_ingestion.py`:

```python
import os
from orchestrator import DataIngestionOrchestrator

# Setup
orchestrator = DataIngestionOrchestrator(
    congress_api_key=os.getenv("CONGRESS_API_KEY"),
    govinfo_api_key=os.getenv("GOVINFO_API_KEY"),
    num_workers=16,
    output_dir="./data"
)

# Ingest from multiple sources
print("1. Ingesting Congress bills...")
results1 = orchestrator.ingest_congress_bills(
    congress=118,
    max_items=100
)

print("2. Ingesting GovInfo packages...")
results2 = orchestrator.ingest_govinfo_collection(
    collection_code="BILLS",
    start_date="2024-01-01",
    max_items=50
)

print("3. Downloading bulk data...")
results3 = orchestrator.ingest_bulkdata_collection(
    collection="FR",
    path="2024/01",
    max_depth=1
)

# Print statistics
print("\nResults:")
print(f"  Congress bills: {results1['successful']}/{results1['total_items']}")
print(f"  GovInfo packages: {results2['successful']}/{results2['total_items']}")
print(f"  Bulk data files: {results3['successful']}/{results3['total_items']}")

# Overall stats
stats = orchestrator.get_overall_stats()
print(f"\nTotal items ingested: {stats['total_ingested']}")
```

Run it:
```bash
python my_ingestion.py
```

## What Gets Created

The system creates:

- `./data/` - Downloaded data files (JSON format)
- `./data_tracking.db` - SQLite database tracking ingested items
- Log output to console showing progress

## Monitoring Progress

The system provides detailed logging:

```
2024-12-12 10:30:00 - orchestrator - INFO - Starting bill ingestion: congress=118, type=hr
2024-12-12 10:30:01 - api_client - INFO - Rate limited: waited 0.00s
2024-12-12 10:30:02 - worker_pool - INFO - Worker 0 executing task congress_bills_118_hr_0
2024-12-12 10:30:03 - orchestrator - INFO - Completed ingestion: 95/100 successful
```

## Testing

Run tests to verify installation:

```bash
python -m pytest test_ingestion.py -v
```

## Next Steps

1. Read `DATA_INGESTION_README.md` for comprehensive documentation
2. Check `mcp_server_config.json` for all available endpoints
3. Customize worker count and output directory for your needs
4. Set up scheduled runs (cron, systemd timer, etc.)

## Troubleshooting

**"ModuleNotFoundError"**
- Run: `pip install -r requirements.txt`

**"CONGRESS_API_KEY not set"**
- Set environment variable: `export CONGRESS_API_KEY="your_key"`

**"Rate limit exceeded"**
- The system handles this automatically
- Reduce `num_workers` if you see many throttle messages

**"Database is locked"**
- Reduce `num_workers` (SQLite has concurrency limits)
- Or use separate database files for different collections

## Getting Help

1. Check `DATA_INGESTION_README.md` for detailed documentation
2. Review example code in `example_usage.py`
3. Run tests to verify setup: `python -m pytest test_ingestion.py -v`
