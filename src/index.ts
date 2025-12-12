#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

import { loadConfig, validateConfig } from './utils/config.js';
import { TokenBucketRateLimiter } from './utils/rate-limiter.js';
import { IngestionTracker } from './utils/ingestion-tracker.js';
import { WorkerPool } from './utils/worker-pool.js';
import { CongressAPIClient } from './utils/congress-client.js';
import { GovinfoAPIClient, GovinfoBulkDataClient } from './utils/govinfo-client.js';
import { createCongressTools } from './tools/congress-tools.js';
import { createGovinfoTools } from './tools/govinfo-tools.js';

// Load configuration
const config = loadConfig();
validateConfig(config);

// Initialize rate limiters
const congressRateLimiter = new TokenBucketRateLimiter(config.congressRateLimit);
const govinfoRateLimiter = new TokenBucketRateLimiter(config.govinfoRateLimit);

// Initialize ingestion tracker
const tracker = new IngestionTracker(config.dbPath);

// Initialize worker pool
const workerPool = new WorkerPool(config.maxWorkers);

// Initialize API clients
const congressClient = new CongressAPIClient(config.congressApiKey, congressRateLimiter);
const govinfoClient = new GovinfoAPIClient(config.govinfoApiKey, govinfoRateLimiter);
const bulkDataClient = new GovinfoBulkDataClient();

// Create tools
const congressTools = createCongressTools(congressClient, tracker, workerPool);
const govinfoTools = createGovinfoTools(govinfoClient, bulkDataClient, tracker, workerPool);

// Combine all tools
const allTools = {
  ...congressTools,
  ...govinfoTools
};

// Create MCP server
const server = new Server(
  {
    name: 'bulk-data-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Handle list tools request
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: Object.entries(allTools).map(([name, tool]) => ({
      name,
      description: tool.description,
      inputSchema: tool.inputSchema,
    })),
  };
});

// Handle call tool request
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const toolName = request.params.name;
  const tool = allTools[toolName as keyof typeof allTools];

  if (!tool) {
    throw new Error(`Unknown tool: ${toolName}`);
  }

  try {
    const result = await tool.handler(request.params.arguments);
    return result;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${errorMessage}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('Bulk Data MCP Server running on stdio');
  console.error(`Congress API Rate Limit: ${config.congressRateLimit} req/hour`);
  console.error(`GovInfo API Rate Limit: ${config.govinfoRateLimit} req/hour`);
  console.error(`Max Workers: ${config.maxWorkers}`);
  console.error(`Database: ${config.dbPath}`);
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});

// Cleanup on exit
process.on('SIGINT', () => {
  console.error('Shutting down...');
  tracker.close();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.error('Shutting down...');
  tracker.close();
  process.exit(0);
});
