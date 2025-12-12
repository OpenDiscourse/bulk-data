# bulk-data

GPO provides the capability to download XML in bulk for select collections from https://www.govinfo.gov/bulkdata. 

Please see the User Guides within this repository for more information on how to make use of the XML data for the available collections.

## 🚀 NEW: Automated Data Ingestion System

This repository now includes a comprehensive **automated data ingestion system** for api.congress.gov and govinfo.gov APIs with:

- ✅ **Rate limiting** - Automatic throttling respecting API limits
- ✅ **Pagination** - Offset-based tracking with resumable operations  
- ✅ **Deduplication** - SQLite-based tracking to prevent re-ingestion
- ✅ **Parallel processing** - Configurable worker pools for fast ingestion
- ✅ **MCP server support** - Complete endpoint configuration

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set API keys (get free keys from api.data.gov)
export CONGRESS_API_KEY="your_key"
export GOVINFO_API_KEY="your_key"

# Run demo (no API keys needed)
python demo.py

# Run interactive examples
python example_usage.py
```

### Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get started in 5 minutes
- **[Complete Documentation](DATA_INGESTION_README.md)** - Full system documentation
- **[API Reference](API_ENDPOINTS_REFERENCE.md)** - Detailed endpoint breakdown
- **[MCP Server Config](mcp_server_config.json)** - Complete endpoint configuration

### Features

The system provides automated ingestion from:
- **api.congress.gov** - Bills, amendments, laws, members, etc.
- **api.govinfo.gov** - Collections, packages, published documents
- **govinfo.gov/bulkdata** - Bulk XML/JSON downloads

With intelligent features:
- Respects rate limits (5,000/hr for Congress, 1,000/hr for GovInfo)
- Tracks processed items to avoid duplication
- Parallel workers for fast ingestion
- Automatic retries on failures
- Real-time progress statistics

See **[DATA_INGESTION_README.md](DATA_INGESTION_README.md)** for complete documentation.

---

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




