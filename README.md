# bulk-data

GPO provides the capability to download XML in bulk for select collections from https://www.govinfo.gov/bulkdata. 

This repository contains documentation on bulk data formats AND a comprehensive MCP (Model Context Protocol) server for programmatically ingesting bulk data from both api.congress.gov and govinfo.gov APIs.

## MCP Server for Bulk Data Ingestion

We've built a complete MCP server that provides:

- **Comprehensive API Coverage**: Full access to all api.congress.gov and govinfo.gov API endpoints
- **Rate Limiting Compliance**: Automatic rate limiting (5000 req/hr for Congress API, conservative limits for GovInfo)
- **Smart Pagination**: Automatic offset tracking and pagination through large datasets
- **Deduplication**: SQLite-based tracking to avoid re-ingesting data
- **Parallel Processing**: Configurable worker pools for concurrent ingestion across multiple collections
- **Resume Capability**: Interrupted ingestions can resume from last successful position
- **Progress Tracking**: Real-time monitoring of worker status and ingestion progress

### Quick Start

```bash
# Install dependencies
npm install

# Configure API keys
cp .env.example .env
# Edit .env and add your API key from https://api.data.gov/signup/

# Build
npm run build

# Run the MCP server
npm start
```

### Documentation

- **[USAGE_GUIDE.md](USAGE_GUIDE.md)**: Complete guide to using the MCP server with examples
- **[API_ENDPOINTS.md](API_ENDPOINTS.md)**: Detailed breakdown of all available API endpoints
- User Guides (existing): XML format documentation for various collections

### Key Features

#### 1. Congress.gov API Integration
Access all Congress API endpoints with automatic pagination:
- Bills, Amendments, Committees
- Members, Nominations, Treaties
- Congressional Record, Committee Communications

#### 2. GovInfo.gov API Integration
Query and ingest from GovInfo collections:
- 30+ collections (BILLS, CFR, FR, USCODE, etc.)
- Package metadata and granules
- Advanced search capabilities
- Related documents discovery

#### 3. Bulk Data Ingestion
Directly ingest from bulk data hierarchies:
- Automatic directory traversal
- JSON/XML format support
- Configurable parallel downloads

#### 4. Worker Pool System
Distribute ingestion across parallel workers:
- Configurable concurrency (default: 5-10 workers)
- Task queue management
- Progress monitoring per worker
- Pause/resume capability

#### 5. Data Tracking & Deduplication
SQLite database tracks all ingested items:
- Prevents duplicate downloads
- Stores metadata and checksums
- Pagination state persistence
- Worker progress tracking

### Architecture

```
MCP Server
├── Congress API Client (rate-limited, paginated)
├── GovInfo API Client (rate-limited, paginated)
├── Worker Pool (parallel processing)
└── Storage Manager (SQLite deduplication)
```

### Example Usage

**Ingest all bills from 118th Congress:**
```json
{
  "tool": "congress_ingest_endpoint",
  "arguments": {
    "endpoint": "bill",
    "params": { "congress": 118 }
  }
}
```

**Parallel ingestion of multiple collections:**
```json
{
  "tool": "worker_add_govinfo_task",
  "arguments": { "collection": "BILLS" }
}
{
  "tool": "worker_add_govinfo_task", 
  "arguments": { "collection": "CFR" }
}
```

See [USAGE_GUIDE.md](USAGE_GUIDE.md) for complete documentation and more examples.

---

## govinfo bulk data (Original Documentation)

The **govinfo** team has migrated bulk data functionality to govinfo. 

https://www.govinfo.gov/bulkdata

### XML and JSON endpoints
New in govinfo, you can add /xml or /json to any govinfo bulkdata link to receive the listing in that format.

https://www.govinfo.gov/bulkdata/BILLS/115/1/hjres<br/>
XML: https://www.govinfo.gov/bulkdata/xml/BILLS/115/1/hjres<br/>
JSON: https://www.govinfo.gov/bulkdata/json/BILLS/115/1/hjres

#### Note
If crawling the xml and json endpoints programmatically, you should ensure that you set the appropriate accept headers in your request, or you may see a 406 response.
e.g for json - `Accept: application/json`

### Examples 

Federal Register Issues from September 2012: http://www.govinfo.gov/bulkdata/FR/2012/09

Code of Federal Regulations: http://www.govinfo.gov/bulkdata/CFR/

Bills back to the 113th Congress: http://www.govinfo.gov/bulkdata/BILLS




