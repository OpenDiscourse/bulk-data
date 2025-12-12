# Bulk Data MCP Server

A Model Context Protocol (MCP) server for systematic ingestion of bulk data from api.congress.gov and govinfo.gov APIs.

## Features

- **Dual API Support**: Integrates both Congress.gov and GovInfo.gov APIs
- **Rate Limiting**: Respects API rate limits (5000/hour for Congress.gov, 1000/hour for GovInfo.gov)
- **Pagination Handling**: Automatic offset-based pagination for all endpoints
- **Deduplication**: Tracks ingested data using SQLite to avoid duplicates
- **Parallel Workers**: Configurable worker pool for parallel data ingestion
- **Comprehensive Coverage**: Access to bills, amendments, laws, committees, members, and bulk data collections

## Installation

```bash
npm install
npm run build
```

## Configuration

Create a `.env` file based on `.env.example`:

```bash
# API Keys (required)
CONGRESS_API_KEY=your_api_key_here
GOVINFO_API_KEY=your_api_key_here

# Rate Limits (requests per hour)
CONGRESS_RATE_LIMIT=5000
GOVINFO_RATE_LIMIT=1000

# Worker Configuration
MAX_WORKERS=4

# Database
DB_PATH=./ingestion-tracker.db
```

### Getting API Keys

1. **Congress.gov API**: Sign up at [api.data.gov](https://api.data.gov/signup/)
2. **GovInfo.gov API**: Same key from api.data.gov works for both

## Usage

### Running the MCP Server

```bash
npm start
```

The server runs using stdio transport and can be integrated with any MCP client.

### Available Tools

#### Congress.gov API Tools

##### `congress_list_bills`
List bills with pagination support.

**Parameters:**
- `congress` (number, optional): Congress number (e.g., 118)
- `billType` (string, optional): Bill type (hr, s, hjres, sjres, etc.)
- `offset` (number, default: 0): Pagination offset
- `limit` (number, default: 250): Results per page (max 250)
- `ingest` (boolean, default: false): Track ingestion in database

**Example:**
```json
{
  "congress": 118,
  "billType": "hr",
  "offset": 0,
  "limit": 250,
  "ingest": true
}
```

##### `congress_get_bill`
Get detailed information about a specific bill.

**Parameters:**
- `congress` (number, required)
- `billType` (string, required)
- `billNumber` (number, required)

##### `congress_bulk_ingest_bills`
Bulk ingest all bills for a congress with parallel workers.

**Parameters:**
- `congress` (number, required): Congress to ingest
- `billType` (string, optional): Specific bill type
- `useWorkers` (boolean, default: true): Enable parallel processing

**Example:**
```json
{
  "congress": 118,
  "useWorkers": true
}
```

##### `congress_list_amendments`
List congressional amendments.

**Parameters:**
- `congress` (number, optional)
- `amendmentType` (string, optional): hamdt or samdt
- `offset` (number, default: 0)
- `limit` (number, default: 250)

##### `congress_list_laws`
List enacted laws.

**Parameters:**
- `congress` (number, optional)
- `lawType` (string, optional): pub or priv
- `offset` (number, default: 0)
- `limit` (number, default: 250)

##### `congress_list_committees`
List congressional committees.

**Parameters:**
- `chamber` (string, optional): house or senate
- `offset` (number, default: 0)
- `limit` (number, default: 250)

##### `congress_list_members`
List members of Congress.

**Parameters:**
- `congress` (number, optional)
- `offset` (number, default: 0)
- `limit` (number, default: 250)

#### GovInfo.gov API Tools

##### `govinfo_list_collections`
List available GovInfo collections.

**Parameters:**
- `offset` (number, default: 0)
- `pageSize` (number, default: 100, max: 100)

##### `govinfo_get_package`
Get detailed package information.

**Parameters:**
- `packageId` (string, required): Package identifier

##### `govinfo_list_published`
List published documents by date.

**Parameters:**
- `dateIssuedStartDate` (string, required): Start date (YYYY-MM-DD)
- `dateIssuedEndDate` (string, optional): End date (YYYY-MM-DD)
- `collection` (string, optional): Filter by collection
- `offset` (number, default: 0)
- `pageSize` (number, default: 100)

##### `govinfo_search_packages`
Search for packages.

**Parameters:**
- `query` (string, required): Search query
- `pageSize` (number, default: 100)
- `offsetMark` (string, default: '*'): Pagination marker
- `collection` (string, optional): Filter by collection

##### `govinfo_bulk_data_collections`
List available bulk data collections.

**Returns:** List of collection codes and descriptions:
- `BILLS`: Congressional Bills
- `BILLSTATUS`: Bill Status (XML)
- `CFR`: Code of Federal Regulations
- `ECFR`: Electronic Code of Federal Regulations
- `FR`: Federal Register
- `CHRG`: Congressional Hearings
- `PLAW`: Public Laws
- `STATUTE`: Statutes at Large
- `USCODE`: United States Code

##### `govinfo_bulk_data_listing`
Get bulk data file listing for a collection.

**Parameters:**
- `collection` (string, required): Collection code
- `congress` (number, optional): Congress number
- `session` (number, optional): Session number
- `format` (string, default: json): xml or json

##### `govinfo_bulk_ingest_collection`
Bulk ingest packages from a collection by date range.

**Parameters:**
- `collection` (string, required): Collection code
- `startDate` (string, required): Start date (YYYY-MM-DD)
- `endDate` (string, optional): End date (YYYY-MM-DD)
- `useWorkers` (boolean, default: true): Enable parallel processing

**Example:**
```json
{
  "collection": "BILLS",
  "startDate": "2024-01-01",
  "endDate": "2024-12-31",
  "useWorkers": true
}
```

##### `govinfo_get_ingestion_stats`
Get statistics about ingested data.

**Parameters:**
- `endpoint` (string, optional): Filter by endpoint

**Returns:**
```json
{
  "total": 1500,
  "byType": {
    "bill": 1200,
    "package": 300
  },
  "lastIngestion": "2024-12-12T08:00:00.000Z"
}
```

## Architecture

### Rate Limiting

The server implements a token bucket algorithm for rate limiting:
- Tokens refill continuously based on the configured rate
- Requests wait automatically when tokens are depleted
- Respects API-specific limits (5000/hour for Congress, 1000/hour for GovInfo)

### Pagination

All list endpoints support offset-based pagination:
- `offset`: Starting position in results
- `limit`/`pageSize`: Number of results per page
- Automatic tracking of `hasMore` status
- For bulk ingestion, automatically iterates through all pages

### Deduplication

Data tracking using SQLite:
- Each ingested resource is checksummed (SHA-256)
- Unique constraint on (endpoint, resource_id)
- Tracks ingestion timestamp and metadata
- Prevents re-ingesting unchanged data

### Parallel Workers

Worker pool implementation:
- Configurable concurrency (default: 4 workers)
- Priority-based task queue
- Automatic task distribution
- Real-time worker statistics

## Examples

### Ingest All Bills from 118th Congress

```json
{
  "tool": "congress_bulk_ingest_bills",
  "arguments": {
    "congress": 118,
    "useWorkers": true
  }
}
```

### Ingest Federal Register for a Month

```json
{
  "tool": "govinfo_bulk_ingest_collection",
  "arguments": {
    "collection": "FR",
    "startDate": "2024-01-01",
    "endDate": "2024-01-31",
    "useWorkers": true
  }
}
```

### Search for Climate-Related Bills

```json
{
  "tool": "govinfo_search_packages",
  "arguments": {
    "query": "climate change",
    "collection": "BILLS",
    "pageSize": 100
  }
}
```

## API Endpoint Reference

### Congress.gov API

**Base URL:** `https://api.congress.gov/v3`

**Main Endpoints:**
- `/bill` - Bills
- `/amendment` - Amendments
- `/law` - Laws
- `/committee` - Committees
- `/member` - Members
- `/nomination` - Nominations
- `/treaty` - Treaties

**Rate Limit:** 5000 requests/hour
**Max Results per Page:** 250

### GovInfo.gov API

**Base URL:** `https://api.govinfo.gov`

**Main Endpoints:**
- `/collections` - List collections
- `/packages/{packageId}/summary` - Package details
- `/published/{date}` - Published documents
- `/search` - Search packages
- `/related/{accessId}` - Related documents

**Rate Limit:** 1000 requests/hour
**Max Results per Page:** 100

### GovInfo.gov Bulk Data

**Base URL:** `https://www.govinfo.gov/bulkdata`

**Format:** Append `/xml` or `/json` to get listings in that format

**Example:**
- `https://www.govinfo.gov/bulkdata/json/BILLS/118/1/hr`

## Development

### Building

```bash
npm run build
```

### Development Mode

```bash
npm run dev
```

## License

MIT

## Contributing

Contributions welcome! Please ensure all changes:
- Maintain rate limiting compliance
- Include pagination support
- Update ingestion tracking
- Add appropriate documentation

## Support

For issues related to:
- **Congress.gov API**: [GitHub Issues](https://github.com/LibraryOfCongress/api.congress.gov/issues)
- **GovInfo.gov API**: [GitHub Issues](https://github.com/usgpo/api/issues)
- **This MCP Server**: [Project Issues](https://github.com/OpenDiscourse/bulk-data/issues)
