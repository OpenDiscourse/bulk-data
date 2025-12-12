# Bulk Data MCP Server Configuration

## Environment Variables

Create a `.env` file in the root directory with your API keys:

```env
# API Keys from api.data.gov (https://api.data.gov/signup/)
CONGRESS_API_KEY=your_congress_api_key_here
GOVINFO_API_KEY=your_govinfo_api_key_here
```

## MCP Client Configuration

### Claude Desktop

Add this to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bulk-data": {
      "command": "node",
      "args": ["/path/to/bulk-data/dist/index.js"],
      "env": {
        "CONGRESS_API_KEY": "your_congress_api_key_here",
        "GOVINFO_API_KEY": "your_govinfo_api_key_here"
      }
    }
  }
}
```

### VS Code with MCP Extension

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "bulk-data": {
      "type": "stdio",
      "command": "node",
      "args": ["./dist/index.js"],
      "env": {
        "CONGRESS_API_KEY": "your_congress_api_key_here",
        "GOVINFO_API_KEY": "your_govinfo_api_key_here"
      }
    }
  }
}
```

### Custom MCP Client

```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const transport = new StdioClientTransport({
  command: 'node',
  args: ['/path/to/bulk-data/dist/index.js'],
  env: {
    CONGRESS_API_KEY: 'your_key',
    GOVINFO_API_KEY: 'your_key',
  },
});

const client = new Client({
  name: 'bulk-data-client',
  version: '1.0.0',
}, {
  capabilities: {},
});

await client.connect(transport);

// List available tools
const tools = await client.listTools();

// Call a tool
const result = await client.callTool({
  name: 'congress_get_bills',
  arguments: {
    offset: 0,
    limit: 20,
  },
});
```

## Worker Pool Configuration

You can adjust the number of parallel workers by modifying the WorkerPool initialization in `src/index.ts`:

```typescript
const workerPool = new WorkerPool(10); // 10 parallel workers
```

Recommended values:
- Conservative: 3-5 workers
- Moderate: 5-10 workers
- Aggressive: 10-20 workers

Note: Higher worker counts consume rate limits faster. Monitor the rate limit status regularly.

## Data Directory

The server stores ingestion tracking data in the `data/` directory by default. You can change this by modifying the IngestionTracker initialization:

```typescript
const ingestionTracker = new IngestionTracker('./custom-data-path');
```

## Rate Limiting

Rate limits are enforced automatically:
- Congress.gov: 5,000 requests/hour
- GovInfo.gov: 5,000 requests/hour

The server will:
1. Track requests per hour
2. Prevent requests that would exceed the limit
3. Automatically reset counters every hour
4. Log warnings when approaching the limit

To check current rate limit status, use the `rate_limit_info` tool.

## Example Usage Patterns

### Sequential Processing

```javascript
// Get bills one page at a time
let offset = 0;
const limit = 250;
let hasMore = true;

while (hasMore) {
  const result = await callTool('congress_get_bills', {
    offset,
    limit,
    congress: 118,
  });
  
  // Process result...
  
  offset += limit;
  hasMore = result.pagination.hasMore;
  
  // Small delay to be nice to the API
  await sleep(1000);
}
```

### Parallel Processing with Worker Pool

```javascript
// Create tasks for parallel processing
const tasks = [];
for (let i = 0; i < 10; i++) {
  tasks.push({
    id: `bills-page-${i}`,
    type: 'congress',
    endpoint: 'bills',
    params: {
      offset: i * 250,
      limit: 250,
      congress: 118,
    },
    priority: 1,
  });
}

// Add tasks to worker pool
await callTool('worker_add_tasks', { tasks });

// Start processing
await callTool('worker_start');

// Monitor progress
const status = await callTool('worker_status');
```

### Bulk Data Download

```javascript
// Download bulk data for Federal Register
const result = await callTool('govinfo_get_bulkdata', {
  path: 'FR/2024/12',
  format: 'json',
});

// The result contains the directory listing
// Process each file as needed
```

## Troubleshooting

### Rate Limit Errors

If you see rate limit errors:
1. Check your current rate limit status: `rate_limit_info`
2. Reduce the number of parallel workers
3. Add delays between sequential requests
4. Wait for the rate limit to reset (shown in rate_limit_info)

### API Key Issues

If you see authentication errors:
1. Verify your API keys are set correctly in environment variables
2. Check that the keys are valid at https://api.data.gov
3. Ensure there are no extra spaces or quotes in the keys

### Missing Data

If ingestion tracking shows missing data:
1. Check the ingestion status: `tracker_get_status`
2. Look for failed records: `tracker_get_status({ status: 'failed' })`
3. Retry failed tasks by re-adding them to the worker pool

### Build Errors

If the TypeScript build fails:
1. Delete `node_modules` and `package-lock.json`
2. Run `npm install` again
3. Ensure you have Node.js 18+ installed
4. Run `npm run build`

## Performance Tuning

### For Maximum Speed
- Use 10-20 workers
- Request maximum page sizes (250 for Congress, 100 for GovInfo)
- Monitor rate limits closely

### For Reliability
- Use 3-5 workers
- Add 1-2 second delays between requests
- Implement retry logic for failed tasks

### For Rate Limit Conservation
- Use 1-3 workers
- Smaller page sizes (50-100)
- Longer delays (5+ seconds)
- Process during off-peak hours

## Support

For issues or questions:
1. Check the API_ENDPOINTS_DOCUMENTATION.md for API details
2. Check the MCP_SERVER_DOCUMENTATION.md for server usage
3. Review the source code in `src/` directory
4. File an issue on the repository
