# Bulk Data MCP Server

An MCP (Model Context Protocol) server for interacting with Congress.gov and GovInfo.gov APIs to systematically ingest bulk governmental data.

## Features

- **Comprehensive API Coverage**: Access to Congress.gov and GovInfo.gov APIs
- **Rate Limiting**: Automatic rate limiting (5,000 requests/hour for both APIs)
- **Pagination Management**: Smart handling of both offset-based and cursor-based pagination
- **Deduplication Tracking**: Tracks ingested data to avoid duplicates
- **Parallel Processing**: Worker pool system for concurrent data ingestion
- **Error Handling**: Robust error handling with retry capabilities

## Installation

1. Install dependencies:
```bash
npm install
```

2. Build the project:
```bash
npm run build
```

3. Set up API keys (optional but recommended):
```bash
export CONGRESS_API_KEY="your-congress-api-key"
export GOVINFO_API_KEY="your-govinfo-api-key"
```

Get your API keys from:
- Congress.gov: https://api.data.gov/signup/
- GovInfo.gov: https://api.data.gov/signup/

## Usage

### Running the Server

Start the MCP server:
```bash
npm start
```

Or in development mode:
```bash
npm run dev
```

### Available Tools

#### Congress.gov API Tools

1. **congress_get_bills** - Get list of bills with pagination
   - Parameters: `offset`, `limit`, `congress`
   
2. **congress_get_bill** - Get specific bill details
   - Parameters: `congress`, `billType`, `billNumber`
   
3. **congress_get_amendments** - Get amendments
   - Parameters: `offset`, `limit`
   
4. **congress_get_members** - Get congressional members
   - Parameters: `offset`, `limit`
   
5. **congress_get_committees** - Get committees
   - Parameters: `congress`, `offset`, `limit`
   
6. **congress_get_nominations** - Get nominations
   - Parameters: `congress`, `offset`, `limit`
   
7. **congress_get_treaties** - Get treaties
   - Parameters: `congress`, `offset`, `limit`

#### GovInfo.gov API Tools

1. **govinfo_get_collections** - List all collections
   
2. **govinfo_get_packages** - Get packages for a collection
   - Parameters: `collection`, `offsetMark`, `pageSize`
   
3. **govinfo_get_package** - Get package details
   - Parameters: `packageId`
   
4. **govinfo_get_granules** - Get package granules
   - Parameters: `packageId`, `offsetMark`, `pageSize`
   
5. **govinfo_search** - Search for content
   - Parameters: `query`, `collection`, `offsetMark`, `pageSize`
   
6. **govinfo_get_published** - Get published content by date
   - Parameters: `startDate`, `endDate`, `collection`, `offsetMark`, `pageSize`
   
7. **govinfo_get_bulkdata** - Get bulk data from govinfo.gov/bulkdata
   - Parameters: `path`, `format` (json/xml)

#### Worker Pool Tools

1. **worker_add_tasks** - Add tasks for parallel processing
   - Parameters: `tasks` (array of task objects)
   
2. **worker_start** - Start processing queued tasks
   
3. **worker_status** - Get worker pool status

#### Tracking Tools

1. **tracker_get_status** - Get ingestion tracking status
   - Parameters: `status` (optional filter)
   
2. **rate_limit_info** - Get rate limit information
   - Parameters: `api` (congress/govinfo)

## Architecture

### Rate Limiting

The server implements automatic rate limiting for both APIs:
- **Congress.gov**: 5,000 requests per hour
- **GovInfo.gov**: 5,000 requests per hour

Rate limits are tracked per API and automatically reset after one hour. The server will prevent requests that would exceed the limit.

### Pagination

Two pagination strategies are supported:

1. **Offset-based** (Congress.gov):
   - Uses `offset` and `limit` parameters
   - Tracks position numerically

2. **Cursor-based** (GovInfo.gov):
   - Uses `offsetMark` parameter
   - Returns next cursor in response

### Ingestion Tracking

All ingested data is tracked in `data/ingestion-records.json` to prevent duplicate processing:
- Each record has a unique ID
- Status tracking: pending, in_progress, completed, failed
- Metadata storage for debugging

### Worker Pool

The worker pool enables parallel processing:
- Configurable number of workers (default: 5)
- Priority-based task queue
- Automatic task distribution
- Progress tracking

## API Endpoints Breakdown

### Congress.gov API (api.congress.gov)

Main endpoints accessible through this server:

- **/bill** - Bills from Congress
- **/amendment** - Amendments to bills
- **/member** - Congressional members
- **/committee** - Congressional committees
- **/nomination** - Presidential nominations
- **/treaty** - Treaties

Each endpoint supports:
- Pagination (offset/limit)
- Filtering by congress number
- JSON format responses

Rate Limit: 5,000 requests/hour
Headers tracked: `X-Ratelimit-Limit`, `X-Ratelimit-Remaining`

### GovInfo.gov API (api.govinfo.gov)

Main endpoints accessible through this server:

- **/collections** - Available document collections
- **/packages** - Document packages within collections
- **/granules** - Sub-elements of packages
- **/published** - Content by publication date
- **/search** - Search across content

Bulk Data endpoint:
- **govinfo.gov/bulkdata** - Direct bulk data access
  - Supports XML and JSON formats
  - Collections: BILLS, CFR, ECFR, FR, and more

Pagination: Cursor-based with `offsetMark` and `pageSize`
Rate Limit: 5,000 requests/hour (via api.data.gov)

## Example Workflows

### 1. Fetch All Bills from 118th Congress

```javascript
// Add tasks to worker pool
worker_add_tasks({
  tasks: [
    {
      id: "bills-118-page-0",
      type: "congress",
      endpoint: "bills",
      params: { congress: 118, offset: 0, limit: 250 },
      priority: 1
    },
    {
      id: "bills-118-page-250",
      type: "congress",
      endpoint: "bills",
      params: { congress: 118, offset: 250, limit: 250 },
      priority: 1
    }
  ]
});

// Start processing
worker_start();

// Check status
worker_status();
```

### 2. Download Bulk Federal Register Data

```javascript
// Get bulk data for a specific path
govinfo_get_bulkdata({
  path: "FR/2024/12",
  format: "json"
});
```

### 3. Search and Track Progress

```javascript
// Search for specific content
govinfo_search({
  query: "climate change",
  collection: "BILLS",
  pageSize: 100
});

// Check what's been ingested
tracker_get_status({
  status: "completed"
});
```

## Data Storage

Ingested data is tracked in the `data/` directory:
- `ingestion-records.json` - Tracking database

This file is automatically created and updated as data is processed.

## Error Handling

The server handles various error conditions:
- Rate limit exceeded: Waits until reset time
- Network errors: Logged and task marked as failed
- Invalid parameters: Returns error message
- API errors: Propagated with context

## Development

### Project Structure

```
src/
├── api/
│   ├── congressAPI.ts      # Congress.gov API client
│   └── govinfoAPI.ts        # GovInfo.gov API client
├── utils/
│   ├── rateLimiter.ts       # Rate limiting logic
│   ├── paginationHandler.ts # Pagination management
│   └── ingestionTracker.ts  # Data deduplication
├── workers/
│   └── workerPool.ts        # Parallel worker system
├── types/
│   └── index.ts             # TypeScript types
└── index.ts                 # Main MCP server

```

### Building

```bash
npm run build
```

### Testing

To test the server, you can use an MCP client like Claude Desktop or create your own client using the MCP SDK.

## License

ISC

## Contributing

Contributions are welcome! Please ensure:
- Code follows TypeScript best practices
- Rate limiting is respected
- Error handling is comprehensive
- Documentation is updated
