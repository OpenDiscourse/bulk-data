# Usage Examples

This guide provides practical examples of using the Bulk Data MCP Server.

## Table of Contents

- [Getting Started](#getting-started)
- [Congress.gov Examples](#congressgov-examples)
- [GovInfo.gov Examples](#govinfogov-examples)
- [Bulk Data Ingestion Examples](#bulk-data-ingestion-examples)
- [Advanced Usage](#advanced-usage)

## Getting Started

### 1. Configure Your Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```bash
CONGRESS_API_KEY=your_congress_api_key_here
GOVINFO_API_KEY=your_govinfo_api_key_here
```

### 2. Install and Build

```bash
npm install
npm run build
```

### 3. Start the Server

```bash
npm start
```

## Congress.gov Examples

### Example 1: List Recent House Bills

**Tool:** `congress_list_bills`

**Input:**
```json
{
  "congress": 118,
  "billType": "hr",
  "offset": 0,
  "limit": 10
}
```

**Output:**
```json
{
  "bills": [
    {
      "congress": 118,
      "type": "hr",
      "number": 1,
      "title": "Lower Energy Costs Act",
      "updateDate": "2024-01-15"
    }
    // ... more bills
  ],
  "pagination": {
    "offset": 0,
    "limit": 10,
    "total": 8500,
    "hasMore": true
  }
}
```

### Example 2: Get Specific Bill Details

**Tool:** `congress_get_bill`

**Input:**
```json
{
  "congress": 118,
  "billType": "hr",
  "billNumber": 1
}
```

**Output:**
```json
{
  "bill": {
    "congress": 118,
    "type": "hr",
    "number": 1,
    "title": "Lower Energy Costs Act",
    "introducedDate": "2023-01-09",
    "sponsors": [...],
    "cosponsors": [...],
    "committees": [...],
    "actions": [...]
  }
}
```

### Example 3: List All Senate Amendments

**Tool:** `congress_list_amendments`

**Input:**
```json
{
  "congress": 118,
  "amendmentType": "samdt",
  "offset": 0,
  "limit": 50
}
```

### Example 4: Bulk Ingest All Bills from 118th Congress

**Tool:** `congress_bulk_ingest_bills`

**Input:**
```json
{
  "congress": 118,
  "useWorkers": true
}
```

**Output:**
```json
{
  "success": true,
  "congress": 118,
  "billTypes": ["hr", "s", "hjres", "sjres", "hconres", "sconres", "hres", "sres"],
  "totalIngested": 8234,
  "totalSkipped": 266,
  "workerStats": {
    "active": 2,
    "pending": 45,
    "queued": 120
  }
}
```

### Example 5: List Congressional Committees

**Tool:** `congress_list_committees`

**Input:**
```json
{
  "chamber": "house",
  "offset": 0,
  "limit": 100
}
```

## GovInfo.gov Examples

### Example 6: List Available Collections

**Tool:** `govinfo_list_collections`

**Input:**
```json
{
  "offset": 0,
  "pageSize": 20
}
```

**Output:**
```json
{
  "collections": [
    {
      "collectionCode": "BILLS",
      "collectionName": "Congressional Bills",
      "packageCount": 180234
    },
    {
      "collectionCode": "FR",
      "collectionName": "Federal Register",
      "packageCount": 95678
    }
    // ... more collections
  ]
}
```

### Example 7: Search for Climate Change Documents

**Tool:** `govinfo_search_packages`

**Input:**
```json
{
  "query": "climate change",
  "collection": "FR",
  "pageSize": 25,
  "offsetMark": "*"
}
```

**Output:**
```json
{
  "results": [
    {
      "packageId": "FR-2024-01-15",
      "title": "Climate Change Regulations",
      "dateIssued": "2024-01-15",
      "collection": "FR"
    }
    // ... more results
  ],
  "nextOffsetMark": "AoIIP4AAACxQYWNrYWdlU3VtbWFyeToxNzI3MzAw"
}
```

### Example 8: Get Documents Published on Specific Date

**Tool:** `govinfo_list_published`

**Input:**
```json
{
  "dateIssuedStartDate": "2024-01-01",
  "dateIssuedEndDate": "2024-01-31",
  "collection": "PLAW",
  "offset": 0,
  "pageSize": 100
}
```

**Output:**
```json
{
  "packages": [
    {
      "packageId": "PLAW-118publ1",
      "title": "An Act to...",
      "dateIssued": "2024-01-05",
      "collection": "PLAW"
    }
    // ... more packages
  ],
  "pagination": {
    "offset": 0,
    "limit": 100,
    "total": 45,
    "hasMore": false
  }
}
```

## Bulk Data Ingestion Examples

### Example 9: List Bulk Data Collections

**Tool:** `govinfo_bulk_data_collections`

**Input:**
```json
{}
```

**Output:**
```json
{
  "collections": [
    "BILLS",
    "BILLSTATUS",
    "CFR",
    "ECFR",
    "FR",
    "CHRG",
    "PLAW",
    "STATUTE",
    "USCODE"
  ],
  "description": {
    "BILLS": "Congressional Bills",
    "BILLSTATUS": "Bill Status (XML)",
    "CFR": "Code of Federal Regulations",
    "ECFR": "Electronic Code of Federal Regulations",
    "FR": "Federal Register",
    "CHRG": "Congressional Hearings",
    "PLAW": "Public Laws",
    "STATUTE": "Statutes at Large",
    "USCODE": "United States Code"
  }
}
```

### Example 10: Get Bulk Data Listing for Bills

**Tool:** `govinfo_bulk_data_listing`

**Input:**
```json
{
  "collection": "BILLS",
  "congress": 118,
  "session": 1,
  "format": "json"
}
```

### Example 11: Bulk Ingest Federal Register for a Month

**Tool:** `govinfo_bulk_ingest_collection`

**Input:**
```json
{
  "collection": "FR",
  "startDate": "2024-01-01",
  "endDate": "2024-01-31",
  "useWorkers": true
}
```

**Output:**
```json
{
  "success": true,
  "collection": "FR",
  "dateRange": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "totalIngested": 312,
  "totalSkipped": 0,
  "workerStats": {
    "active": 4,
    "pending": 0,
    "queued": 0
  }
}
```

### Example 12: Bulk Ingest Public Laws from 118th Congress

**Tool:** `govinfo_bulk_ingest_collection`

**Input:**
```json
{
  "collection": "PLAW",
  "startDate": "2023-01-01",
  "endDate": "2024-12-31",
  "useWorkers": true
}
```

## Advanced Usage

### Example 13: Check Ingestion Statistics

**Tool:** `govinfo_get_ingestion_stats`

**Input:**
```json
{
  "endpoint": "congress/bills"
}
```

**Output:**
```json
{
  "total": 8500,
  "byType": {
    "bill": 8500
  },
  "lastIngestion": "2024-12-12T08:15:00.000Z"
}
```

### Example 14: Sequential Pagination Through All Results

To get all bills from the 118th Congress:

**Step 1:** Initial request
```json
{
  "congress": 118,
  "billType": "hr",
  "offset": 0,
  "limit": 250
}
```

**Step 2:** Next page
```json
{
  "congress": 118,
  "billType": "hr",
  "offset": 250,
  "limit": 250
}
```

**Step 3:** Continue until `hasMore` is `false`

### Example 15: Ingesting Specific Bill Type Only

**Tool:** `congress_bulk_ingest_bills`

**Input:**
```json
{
  "congress": 118,
  "billType": "hr",
  "useWorkers": true
}
```

This will only ingest House Bills from the 118th Congress.

### Example 16: Multi-Collection Workflow

To ingest multiple types of congressional data:

1. **Ingest Bills:**
```json
{
  "tool": "congress_bulk_ingest_bills",
  "arguments": {
    "congress": 118,
    "useWorkers": true
  }
}
```

2. **Ingest Amendments:**
```json
{
  "tool": "congress_list_amendments",
  "arguments": {
    "congress": 118,
    "offset": 0,
    "limit": 250
  }
}
```

3. **Ingest Public Laws:**
```json
{
  "tool": "govinfo_bulk_ingest_collection",
  "arguments": {
    "collection": "PLAW",
    "startDate": "2023-01-01",
    "endDate": "2024-12-31",
    "useWorkers": true
  }
}
```

### Example 17: Date Range Search

To find all documents in a specific date range:

**Tool:** `govinfo_list_published`

**Input:**
```json
{
  "dateIssuedStartDate": "2024-11-01",
  "dateIssuedEndDate": "2024-11-30",
  "offset": 0,
  "pageSize": 100
}
```

### Example 18: Collection-Specific Search

**Tool:** `govinfo_search_packages`

**Input:**
```json
{
  "query": "artificial intelligence",
  "collection": "CHRG",
  "pageSize": 50
}
```

This searches for "artificial intelligence" in Congressional Hearings only.

## Worker Configuration Tips

### Default Configuration (4 Workers)

Good for:
- Moderate ingestion tasks
- Standard rate limits
- General use

### High Throughput (8-10 Workers)

For faster ingestion:
```bash
MAX_WORKERS=8
```

Good for:
- Large historical data ingestion
- When you have high rate limits
- Bulk data operations

### Conservative (1-2 Workers)

For rate limit preservation:
```bash
MAX_WORKERS=1
```

Good for:
- Real-time monitoring
- Low rate limit accounts
- Testing and development

## Monitoring Progress

### Check Active Workers

The `workerStats` in bulk ingestion responses shows:
- `active`: Currently executing tasks
- `pending`: Tasks awaiting completion
- `queued`: Tasks waiting to start

### Track Ingestion Over Time

Use `govinfo_get_ingestion_stats` periodically to monitor:
- Total records ingested
- Breakdown by resource type
- Last ingestion timestamp

## Error Handling

All tools return error information in the response:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Error: Congress API error: 429 Too Many Requests"
    }
  ],
  "isError": true
}
```

Common errors:
- **429 Too Many Requests**: Rate limit exceeded, wait before retrying
- **404 Not Found**: Resource doesn't exist
- **401 Unauthorized**: Invalid API key
- **500 Internal Server Error**: API service issue

## Best Practices

1. **Start Small**: Test with small date ranges or single bill types first
2. **Monitor Rate Limits**: Check remaining rate limit in response headers
3. **Use Workers**: Enable parallel processing for bulk operations
4. **Check Stats**: Regularly verify ingestion statistics
5. **Handle Errors**: Implement retry logic for failed requests
6. **Incremental Ingestion**: Ingest data by congress/year to manage scope
7. **Track Progress**: Use the database to avoid duplicate ingestion
