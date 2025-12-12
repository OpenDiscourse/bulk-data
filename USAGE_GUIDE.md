# Bulk Data MCP Server Usage Guide

This MCP server provides comprehensive access to the Congress.gov API and GovInfo.gov APIs for bulk data ingestion with features including:

- Rate limiting compliance (5000 req/hr for Congress API)
- Automatic pagination with offset tracking
- Deduplication via SQLite database
- Parallel processing with configurable worker pools
- Resume capability for interrupted ingestions

## Quick Start

### 1. Installation

```bash
npm install
```

### 2. Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
- Get API keys at: https://api.data.gov/signup/
- Both APIs use the same key from api.data.gov

### 3. Build

```bash
npm run build
```

### 4. Run

```bash
npm start
```

## Available Tools

### Congress API Tools

#### congress_fetch_bills
Fetch bills with pagination.

**Parameters:**
- `congress` (number): Congress number (e.g., 118)
- `type` (string): Bill type (hr, s, hjres, sjres, etc.)
- `offset` (number): Starting offset (default: 0)
- `limit` (number): Results per request (max: 250, default: 250)

**Example:**
```json
{
  "congress": 118,
  "type": "hr",
  "offset": 0,
  "limit": 250
}
```

#### congress_fetch_amendments
Fetch amendments with pagination.

#### congress_fetch_committees
Fetch committees with pagination.

**Parameters:**
- `chamber` (string): house, senate, or joint
- `congress` (number)
- `offset`, `limit`

#### congress_fetch_members
Fetch Congress members.

**Parameters:**
- `currentMember` (boolean): Filter current members
- `congress` (number)
- `offset`, `limit`

#### congress_ingest_endpoint
**Full ingestion with automatic pagination and deduplication.**

**Parameters:**
- `endpoint` (string): bill, amendment, committee, member, nomination, congressional-record, committee-communication, or treaty
- `params` (object): Additional filters (congress, type, etc.)

**Example:**
```json
{
  "endpoint": "bill",
  "params": {
    "congress": 118
  }
}
```

This will automatically:
1. Paginate through all results
2. Track progress in the database
3. Skip already ingested items
4. Resume from last position if interrupted

### GovInfo API Tools

#### govinfo_list_collections
List all available collections.

**Returns:** Array of collection codes and names.

**Major collections:**
- BILLS: Congressional bills
- CFR: Code of Federal Regulations
- ECFR: Electronic CFR
- FR: Federal Register
- USCODE: United States Code
- CONGRECORD: Congressional Record

#### govinfo_query_collection
Query a specific collection with pagination.

**Parameters:**
- `collection` (string): Collection code (e.g., BILLS, CFR)
- `offset` (number): Starting offset
- `pageSize` (number): Results per request (max: 1000)

**Example:**
```json
{
  "collection": "BILLS",
  "offset": 0,
  "pageSize": 1000
}
```

#### govinfo_get_package
Get detailed information about a package.

**Parameters:**
- `packageId` (string): Package ID (e.g., BILLS-118hr1-ih)

#### govinfo_search
Search across collections.

**Parameters:**
- `query` (string): Search terms
- `collection` (string, optional): Filter by collection
- `offset`, `pageSize`

#### govinfo_ingest_collection
**Full collection ingestion with automatic pagination.**

**Parameters:**
- `collection` (string): Collection code

**Example:**
```json
{
  "collection": "BILLS"
}
```

#### govinfo_ingest_bulkdata
Ingest bulk data from a path.

**Parameters:**
- `path` (string): Bulk data path (e.g., /BILLS, /CFR/2024, /FR/2024/01)

**Example:**
```json
{
  "path": "/BILLS/118/1/hr"
}
```

### Worker Pool Tools (Parallel Processing)

#### worker_add_congress_task
Add a Congress API ingestion to the parallel worker pool.

**Parameters:**
- `endpoint` (string): Endpoint name
- `params` (object): Additional parameters

**Example:**
```json
{
  "endpoint": "bill",
  "params": { "congress": 118 }
}
```

#### worker_add_govinfo_task
Add a GovInfo collection ingestion to the worker pool.

**Parameters:**
- `collection` (string): Collection code

#### worker_add_bulkdata_task
Add a bulk data ingestion to the worker pool.

**Parameters:**
- `path` (string): Bulk data path

#### worker_get_status
Get current worker pool status including:
- Pending tasks
- Active workers
- Worker progress

#### worker_pause / worker_resume
Pause or resume all workers.

### Storage Tools

#### storage_get_stats
Get ingestion statistics.

**Parameters:**
- `collection` (string, optional): Filter by collection

**Returns:**
- Total items ingested
- First and last ingestion times
- Per-collection breakdown

#### storage_check_ingested
Check if an item has been ingested.

**Parameters:**
- `collection` (string)
- `packageId` (string)

## Usage Patterns

### Pattern 1: Single Collection Ingestion

For a focused ingestion of one collection:

```json
// Step 1: Ingest the collection
{
  "tool": "govinfo_ingest_collection",
  "arguments": {
    "collection": "BILLS"
  }
}

// Step 2: Check progress
{
  "tool": "storage_get_stats",
  "arguments": {
    "collection": "BILLS"
  }
}
```

### Pattern 2: Parallel Multi-Collection Ingestion

For ingesting multiple collections simultaneously:

```json
// Add multiple tasks to worker pool
{
  "tool": "worker_add_govinfo_task",
  "arguments": { "collection": "BILLS" }
}

{
  "tool": "worker_add_govinfo_task",
  "arguments": { "collection": "CFR" }
}

{
  "tool": "worker_add_govinfo_task",
  "arguments": { "collection": "FR" }
}

// Monitor progress
{
  "tool": "worker_get_status",
  "arguments": {}
}
```

### Pattern 3: Bulk Data Ingestion

For ingesting specific bulk data hierarchies:

```json
// Ingest entire Bills collection for 118th Congress
{
  "tool": "govinfo_ingest_bulkdata",
  "arguments": {
    "path": "/BILLS/118"
  }
}

// Or specific subcollection
{
  "tool": "worker_add_bulkdata_task",
  "arguments": {
    "path": "/FR/2024/01"
  }
}
```

### Pattern 4: Congress API Ingestion

For ingesting from Congress.gov API:

```json
// Single endpoint
{
  "tool": "congress_ingest_endpoint",
  "arguments": {
    "endpoint": "bill",
    "params": { "congress": 118 }
  }
}

// Parallel multiple endpoints
{
  "tool": "worker_add_congress_task",
  "arguments": {
    "endpoint": "bill",
    "params": { "congress": 118 }
  }
}

{
  "tool": "worker_add_congress_task",
  "arguments": {
    "endpoint": "member",
    "params": { "currentMember": true }
  }
}
```

## Rate Limiting

The server automatically handles rate limiting:

- **Congress API**: 5,000 requests per hour
- **GovInfo API**: Conservative 1,000 requests per hour (actual limit not documented)
- **Bulk Data**: 500 requests per hour

Rate limiters use:
- Token bucket algorithm with reservoir refill
- Automatic backoff on 429 responses
- Header monitoring for remaining quota

## Deduplication

Items are automatically deduplicated using:
- SQLite database tracking
- Unique collection + packageId index
- Check before download to avoid re-ingesting

## Resume Capability

Ingestions can be resumed after interruption:
- Pagination state is saved to database
- Resume from last successful offset
- No re-processing of already ingested items

## Data Storage

Ingested metadata is stored in SQLite (`./data/ingestion.db`):

**Tables:**
- `ingested_records`: All ingested items with metadata
- `pagination_state`: Pagination tracking per endpoint
- `worker_progress`: Worker status and progress

## Performance Tuning

Adjust worker pool settings in `.env`:

```env
# For faster ingestion (if rate limits allow)
MAX_WORKERS=20
WORKER_CONCURRENCY=10

# For conservative/slower ingestion
MAX_WORKERS=5
WORKER_CONCURRENCY=2
```

**Recommendations:**
- Congress API (5000/hr): 10-15 workers
- GovInfo API: 5-10 workers
- Monitor rate limit headers and adjust accordingly

## Error Handling

The server handles:
- Network errors: Exponential backoff retry
- Rate limit errors (429): Wait for reset
- Not found (404): Skip and continue
- All errors logged with context

## Examples

### Complete Bills Ingestion for 118th Congress

```json
{
  "tool": "worker_add_congress_task",
  "arguments": {
    "endpoint": "bill",
    "params": {
      "congress": 118
    }
  }
}
```

### Search and Ingest Federal Register Documents

```json
// First, search
{
  "tool": "govinfo_search",
  "arguments": {
    "query": "climate change",
    "collection": "FR"
  }
}

// Then ingest the collection
{
  "tool": "govinfo_ingest_collection",
  "arguments": {
    "collection": "FR"
  }
}
```

### Parallel Ingestion of Multiple Congress Sessions

```json
{
  "tool": "worker_add_congress_task",
  "arguments": {
    "endpoint": "bill",
    "params": { "congress": 118 }
  }
}

{
  "tool": "worker_add_congress_task",
  "arguments": {
    "endpoint": "bill",
    "params": { "congress": 117 }
  }
}

{
  "tool": "worker_add_congress_task",
  "arguments": {
    "endpoint": "bill",
    "params": { "congress": 116 }
  }
}
```

## Troubleshooting

### Rate Limit Exceeded
If you see 429 errors:
1. Check worker concurrency settings
2. Monitor with `worker_get_status`
3. Reduce MAX_WORKERS or WORKER_CONCURRENCY

### Database Locked
If SQLite locking occurs:
1. Reduce WORKER_CONCURRENCY
2. Ensure proper cleanup on exit

### Missing API Key
Ensure `.env` file has valid API keys from api.data.gov

## Architecture

```
┌─────────────────┐
│  MCP Server     │
├─────────────────┤
│ Tool Handlers   │
└────────┬────────┘
         │
    ┌────┴────────────────────┐
    │                         │
┌───▼──────────┐    ┌────────▼────────┐
│ Congress     │    │ GovInfo         │
│ Client       │    │ Client          │
├──────────────┤    ├─────────────────┤
│ - Rate Limit │    │ - Rate Limit    │
│ - Pagination │    │ - Pagination    │
│ - Endpoints  │    │ - Collections   │
└───┬──────────┘    └────────┬────────┘
    │                        │
    └────────┬───────────────┘
             │
    ┌────────▼────────┐
    │ Worker Pool     │
    ├─────────────────┤
    │ - Task Queue    │
    │ - Concurrency   │
    │ - Progress      │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │ Storage Manager │
    ├─────────────────┤
    │ - SQLite DB     │
    │ - Deduplication │
    │ - State Tracking│
    └─────────────────┘
```

## License

MIT
