# Bulk Data Repository

This repository contains documentation for GPO bulk data and a comprehensive **MCP Server** for systematic ingestion of data from api.congress.gov and govinfo.gov.

## 📚 Original Documentation

GPO provides the capability to download XML in bulk for select collections from https://www.govinfo.gov/bulkdata.

Please see the User Guides within this repository for more information on how to make use of the XML data for the available collections:

- [Bills XML User Guide](Bills-XML-User-Guide.md)
- [Bills Summary XML User Guide](Bills-Summary-XML-User-Guide.md)
- [CFR XML User Guide](CFR-XML_User-Guide.md)
- [ECFR XML User Guide](ECFR-XML-User-Guide.md)
- [Federal Register XML User Guide](FR-XML_User-Guide.md)

### govinfo bulk data

The **govinfo** team has migrated bulk data functionality to govinfo: https://www.govinfo.gov/bulkdata

#### XML and JSON endpoints
New in govinfo, you can add /xml or /json to any govinfo bulkdata link to receive the listing in that format.

https://www.govinfo.gov/bulkdata/BILLS/115/1/hjres<br/>
XML: https://www.govinfo.gov/bulkdata/xml/BILLS/115/1/hjres<br/>
JSON: https://www.govinfo.gov/bulkdata/json/BILLS/115/1/hjres

**Note:** If crawling the xml and json endpoints programmatically, you should ensure that you set the appropriate accept headers in your request, or you may see a 406 response.
e.g for json - `Accept: application/json`

#### Examples 

- Federal Register Issues from September 2012: http://www.govinfo.gov/bulkdata/FR/2012/09
- Code of Federal Regulations: http://www.govinfo.gov/bulkdata/CFR/
- Bills back to the 113th Congress: http://www.govinfo.gov/bulkdata/BILLS

---

## 🚀 MCP Server for Bulk Data Ingestion

### Quick Start

```bash
# Install dependencies
npm install

# Configure API keys
cp .env.example .env
# Edit .env with your API keys

# Build the project
npm run build

# Start the MCP server
npm start
```

### Features

✅ **Dual API Support**: Congress.gov and GovInfo.gov APIs  
✅ **Rate Limiting**: Respects API limits (5000/hour for Congress, 1000/hour for GovInfo)  
✅ **Smart Pagination**: Automatic offset-based pagination handling  
✅ **Deduplication**: SQLite-based tracking prevents duplicate ingestion  
✅ **Parallel Workers**: Configurable worker pool for fast bulk ingestion  
✅ **Comprehensive Coverage**: Bills, amendments, laws, committees, members, bulk data

### Available Tools

#### Congress.gov API Tools
- `congress_list_bills` - List bills with pagination
- `congress_get_bill` - Get specific bill details
- `congress_bulk_ingest_bills` - Bulk ingest with parallel workers
- `congress_list_amendments` - List amendments
- `congress_list_laws` - List enacted laws
- `congress_list_committees` - List committees
- `congress_list_members` - List members

#### GovInfo.gov API Tools
- `govinfo_list_collections` - List available collections
- `govinfo_get_package` - Get package details
- `govinfo_list_published` - List by publication date
- `govinfo_search_packages` - Search packages
- `govinfo_bulk_data_collections` - List bulk collections
- `govinfo_bulk_data_listing` - Get bulk data files
- `govinfo_bulk_ingest_collection` - Bulk ingest with workers
- `govinfo_get_ingestion_stats` - View ingestion statistics

### Documentation

- **[MCP Server README](MCP_SERVER_README.md)** - Complete server documentation
- **[API Reference](API_REFERENCE.md)** - Comprehensive API endpoint documentation
- **[Usage Examples](USAGE_EXAMPLES.md)** - Practical usage examples
- **[Architecture](ARCHITECTURE.md)** - System architecture and design

### Testing

```bash
# Test rate limiter
node examples/test-rate-limiter.js

# Test ingestion tracker
node examples/test-ingestion-tracker.js

# Test worker pool
node examples/test-worker-pool.js
```

### API Keys

Get your API keys from [api.data.gov](https://api.data.gov/signup/). The same key works for both Congress.gov and GovInfo.gov APIs.

### Configuration

Edit `.env` file:

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

### Architecture Highlights

- **Rate Limiting**: Token bucket algorithm ensures API compliance
- **Deduplication**: SHA-256 checksums prevent duplicate data
- **Parallel Processing**: Worker pool with configurable concurrency
- **Data Tracking**: SQLite database tracks all ingested resources
- **Pagination**: Automatic offset handling for complete data retrieval

### Example Usage

**Bulk ingest all bills from 118th Congress:**
```json
{
  "tool": "congress_bulk_ingest_bills",
  "arguments": {
    "congress": 118,
    "useWorkers": true
  }
}
```

**Search for climate documents:**
```json
{
  "tool": "govinfo_search_packages",
  "arguments": {
    "query": "climate change",
    "collection": "FR",
    "pageSize": 100
  }
}
```

### License

MIT




