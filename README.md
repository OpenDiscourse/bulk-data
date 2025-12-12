# bulk-data

GPO provides the capability to download XML in bulk for select collections from https://www.govinfo.gov/bulkdata. 

This repository now includes a comprehensive **MCP (Model Context Protocol) Server** for systematically ingesting and managing bulk governmental data from both Congress.gov and GovInfo.gov APIs.

## Features

### MCP Server for API Integration

- **Comprehensive API Coverage**: Full access to Congress.gov and GovInfo.gov APIs
- **Smart Rate Limiting**: Automatic tracking and enforcement of 5,000 requests/hour limit
- **Advanced Pagination**: Handles both offset-based (Congress.gov) and cursor-based (GovInfo.gov) pagination
- **Deduplication Tracking**: Prevents duplicate data ingestion
- **Parallel Processing**: Worker pool system for concurrent data fetching (configurable workers)
- **Complete Error Handling**: Retry logic and robust error management

### API Endpoints Supported

#### Congress.gov API
- Bills, amendments, members, committees
- Nominations, treaties, congressional records
- All endpoints with full pagination support

#### GovInfo.gov API
- Collections, packages, granules
- Search functionality
- Published content by date
- Direct bulk data access (XML/JSON)

## Quick Start

### Installation

```bash
npm install
npm run build
```

### Configuration

1. Get API keys from https://api.data.gov/signup/
2. Set environment variables:

```bash
export CONGRESS_API_KEY="your_key_here"
export GOVINFO_API_KEY="your_key_here"
```

### Running the MCP Server

```bash
npm start
```

See [CONFIGURATION.md](CONFIGURATION.md) for detailed setup instructions.

## Documentation

- **[MCP Server Documentation](MCP_SERVER_DOCUMENTATION.md)** - Complete guide to using the MCP server
- **[API Endpoints Documentation](API_ENDPOINTS_DOCUMENTATION.md)** - Comprehensive breakdown of all API endpoints
- **[Configuration Guide](CONFIGURATION.md)** - Setup and configuration options

## User Guides (Legacy Documentation)

Please see the User Guides within this repository for more information on how to make use of the XML data for the available collections:

- [Bills XML User Guide](Bills-XML-User-Guide.md)
- [Bills Summary XML User Guide](Bills-Summary-XML-User-Guide.md)
- [CFR XML User Guide](CFR-XML_User-Guide.md)
- [ECFR XML User Guide](ECFR-XML-User-Guide.md)
- [Federal Register XML User Guide](FR-XML_User-Guide.md)

## govinfo bulk data

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

## MCP Server Usage Examples

### Fetching Bills

```javascript
// Get recent bills from the 118th Congress
congress_get_bills({
  congress: 118,
  offset: 0,
  limit: 250
});
```

### Parallel Data Ingestion

```javascript
// Add tasks to worker pool
worker_add_tasks({
  tasks: [
    {
      id: "bills-118-0",
      type: "congress",
      endpoint: "bills",
      params: { congress: 118, offset: 0, limit: 250 },
      priority: 1
    }
  ]
});

// Start workers
worker_start();

// Check status
worker_status();
```

### Bulk Data Download

```javascript
// Download Federal Register bulk data
govinfo_get_bulkdata({
  path: "FR/2024/12",
  format: "json"
});
```

## Architecture

The MCP server is built with:
- **TypeScript** for type safety
- **@modelcontextprotocol/sdk** for MCP compliance
- **Axios** for HTTP requests
- **Rate limiting** to respect API limits
- **Worker pool** for parallel processing
- **Ingestion tracking** to prevent duplicates

## Rate Limits

Both APIs use the same rate limit infrastructure:
- **5,000 requests per hour** per API key
- Automatically tracked and enforced
- Resets every hour
- Use `rate_limit_info` tool to check current status

## Contributing

Contributions are welcome! Please:
1. Follow TypeScript best practices
2. Respect rate limiting in all code
3. Add comprehensive error handling
4. Update documentation for any changes

## License

ISC





