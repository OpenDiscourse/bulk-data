# Quick Start Guide

Get up and running with the Bulk Data MCP Server in 5 minutes.

## 1. Install (30 seconds)

```bash
cd /path/to/bulk-data
npm install
```

## 2. Configure (1 minute)

Get your API key from [api.data.gov](https://api.data.gov/signup/), then:

```bash
cp .env.example .env
# Edit .env and add your API key
```

Your `.env` should look like:
```bash
CONGRESS_API_KEY=your_actual_api_key_here
GOVINFO_API_KEY=your_actual_api_key_here
```

## 3. Build (30 seconds)

```bash
npm run build
```

## 4. Start (immediate)

```bash
npm start
```

The server is now running and ready to accept MCP requests!

## 5. Test (1 minute)

In another terminal, test the core functionality:

```bash
# Test rate limiter
node examples/test-rate-limiter.js

# Test ingestion tracker
node examples/test-ingestion-tracker.js

# Test worker pool
node examples/test-worker-pool.js
```

All tests should pass with ✓ marks.

## Common Tasks

### List Recent Bills

```json
{
  "tool": "congress_list_bills",
  "arguments": {
    "congress": 118,
    "billType": "hr",
    "limit": 10
  }
}
```

### Search for Documents

```json
{
  "tool": "govinfo_search_packages",
  "arguments": {
    "query": "infrastructure",
    "pageSize": 50
  }
}
```

### Bulk Ingest Bills (with parallel workers)

```json
{
  "tool": "congress_bulk_ingest_bills",
  "arguments": {
    "congress": 118,
    "useWorkers": true
  }
}
```

### Check Ingestion Stats

```json
{
  "tool": "govinfo_get_ingestion_stats",
  "arguments": {}
}
```

## Available Tools

### Congress.gov (7 tools)
- `congress_list_bills` - List bills
- `congress_get_bill` - Get bill details
- `congress_bulk_ingest_bills` - Bulk ingest
- `congress_list_amendments` - List amendments
- `congress_list_laws` - List laws
- `congress_list_committees` - List committees
- `congress_list_members` - List members

### GovInfo.gov (8 tools)
- `govinfo_list_collections` - List collections
- `govinfo_get_package` - Get package
- `govinfo_list_published` - List by date
- `govinfo_search_packages` - Search
- `govinfo_bulk_data_collections` - List bulk collections
- `govinfo_bulk_data_listing` - Get bulk files
- `govinfo_bulk_ingest_collection` - Bulk ingest
- `govinfo_get_ingestion_stats` - Statistics

## Configuration Options

Edit `.env` to customize:

```bash
# Increase workers for faster processing
MAX_WORKERS=8

# Custom database location
DB_PATH=/path/to/database.db

# Adjust rate limits (if you have special access)
CONGRESS_RATE_LIMIT=5000
GOVINFO_RATE_LIMIT=1000
```

## Troubleshooting

### "Error: CONGRESS_API_KEY is required"
→ Add your API key to `.env` file

### "429 Too Many Requests"
→ You've hit the rate limit, wait a few minutes

### Database locked
→ Only one server instance can run at a time

### Build fails
→ Ensure Node.js 18+ is installed: `node --version`

## Next Steps

- Read [MCP_SERVER_README.md](MCP_SERVER_README.md) for complete documentation
- Check [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) for 18+ detailed examples
- Review [API_REFERENCE.md](API_REFERENCE.md) for all available endpoints
- Study [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system

## Rate Limits

- **Congress.gov**: 5,000 requests/hour
- **GovInfo.gov**: 1,000 requests/hour
- **Demo Key**: Only 30/hour (get a real key!)

## Tips

1. **Start small**: Test with a few bills before bulk ingestion
2. **Use workers**: Enable parallel processing for bulk operations
3. **Check stats**: Monitor progress with `govinfo_get_ingestion_stats`
4. **Pagination**: All list tools support offset for large datasets
5. **Deduplication**: The tracker prevents re-ingesting the same data

## Getting Help

- **Documentation**: See docs in this repository
- **Congress.gov API**: [api.congress.gov](https://api.congress.gov/)
- **GovInfo.gov API**: [api.govinfo.gov/docs](https://api.govinfo.gov/docs/)
- **Issues**: [GitHub Issues](https://github.com/OpenDiscourse/bulk-data/issues)

---

**Ready to go!** The server is now set up and you can start ingesting congressional data. 🚀
