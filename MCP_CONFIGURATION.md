# Example MCP Server Configuration for Claude Desktop

Add this to your Claude Desktop configuration file:

## MacOS
Location: `~/Library/Application Support/Claude/claude_desktop_config.json`

## Windows
Location: `%APPDATA%\Claude\claude_desktop_config.json`

## Configuration

```json
{
  "mcpServers": {
    "bulk-data": {
      "command": "node",
      "args": [
        "/path/to/bulk-data/dist/index.js"
      ],
      "env": {
        "CONGRESS_API_KEY": "your_api_key_here",
        "GOVINFO_API_KEY": "your_api_key_here",
        "MAX_WORKERS": "10",
        "WORKER_CONCURRENCY": "5"
      }
    }
  }
}
```

Replace `/path/to/bulk-data` with the actual path to your bulk-data repository.

## Get API Keys

1. Visit https://api.data.gov/signup/
2. Fill out the signup form
3. Check your email for the API key
4. Use the same key for both CONGRESS_API_KEY and GOVINFO_API_KEY

## After Configuration

1. Restart Claude Desktop
2. The bulk-data MCP server tools will be available
3. You can use any of the 20+ tools for data ingestion

## Testing

Try these commands in Claude:

1. "List all available GovInfo collections"
   - Uses: `govinfo_list_collections`

2. "Fetch the first 10 bills from the 118th Congress"
   - Uses: `congress_fetch_bills` with congress=118, limit=10

3. "Show me the ingestion statistics"
   - Uses: `storage_get_stats`

4. "Start ingesting bills from the 118th Congress in parallel"
   - Uses: `worker_add_congress_task` with endpoint=bill

## Example Workflows

### Workflow 1: Explore Collections
```
1. "List all GovInfo collections"
2. "Query the BILLS collection with the first 100 items"
3. "Get package details for BILLS-118hr1-ih"
```

### Workflow 2: Full Ingestion
```
1. "Start parallel ingestion of BILLS, CFR, and FR collections"
2. "Check worker status"
3. "Show me ingestion statistics"
```

### Workflow 3: Targeted Search
```
1. "Search GovInfo for 'climate change' in the FR collection"
2. "Ingest all Federal Register documents from January 2024"
```
