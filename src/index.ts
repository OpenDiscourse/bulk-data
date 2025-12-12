#!/usr/bin/env node
/**
 * Bulk Data MCP Server
 * MCP server for interacting with Congress.gov and GovInfo APIs
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';

import { CongressAPIClient } from './api/congressAPI.js';
import { GovInfoAPIClient } from './api/govinfoAPI.js';
import { WorkerPool } from './workers/workerPool.js';
import { ingestionTracker } from './utils/ingestionTracker.js';
import { rateLimiter } from './utils/rateLimiter.js';

// Initialize clients
const congressClient = new CongressAPIClient();
const govinfoClient = new GovInfoAPIClient();
const workerPool = new WorkerPool(5); // 5 parallel workers by default

// Tool definitions
const TOOLS: Tool[] = [
  // Congress.gov API Tools
  {
    name: 'congress_get_bills',
    description: 'Get list of bills from Congress.gov API. Supports pagination with offset and limit parameters. Rate limit: 5000 requests/hour.',
    inputSchema: {
      type: 'object',
      properties: {
        offset: {
          type: 'number',
          description: 'Offset for pagination (default: 0)',
        },
        limit: {
          type: 'number',
          description: 'Number of results to return (default: 20, max: 250)',
        },
        congress: {
          type: 'number',
          description: 'Congress number to filter by',
        },
      },
    },
  },
  {
    name: 'congress_get_bill',
    description: 'Get details for a specific bill',
    inputSchema: {
      type: 'object',
      properties: {
        congress: {
          type: 'number',
          description: 'Congress number (e.g., 118)',
        },
        billType: {
          type: 'string',
          description: 'Bill type (e.g., hr, s, hjres, sjres)',
        },
        billNumber: {
          type: 'string',
          description: 'Bill number',
        },
      },
      required: ['congress', 'billType', 'billNumber'],
    },
  },
  {
    name: 'congress_get_amendments',
    description: 'Get list of amendments from Congress.gov API. Supports pagination.',
    inputSchema: {
      type: 'object',
      properties: {
        offset: {
          type: 'number',
          description: 'Offset for pagination',
        },
        limit: {
          type: 'number',
          description: 'Number of results to return',
        },
      },
    },
  },
  {
    name: 'congress_get_members',
    description: 'Get list of congressional members. Supports pagination.',
    inputSchema: {
      type: 'object',
      properties: {
        offset: {
          type: 'number',
          description: 'Offset for pagination',
        },
        limit: {
          type: 'number',
          description: 'Number of results to return',
        },
      },
    },
  },
  {
    name: 'congress_get_committees',
    description: 'Get list of committees. Supports pagination.',
    inputSchema: {
      type: 'object',
      properties: {
        congress: {
          type: 'number',
          description: 'Congress number to filter by',
        },
        offset: {
          type: 'number',
          description: 'Offset for pagination',
        },
        limit: {
          type: 'number',
          description: 'Number of results to return',
        },
      },
    },
  },
  {
    name: 'congress_get_nominations',
    description: 'Get list of nominations. Supports pagination.',
    inputSchema: {
      type: 'object',
      properties: {
        congress: {
          type: 'number',
          description: 'Congress number to filter by',
        },
        offset: {
          type: 'number',
          description: 'Offset for pagination',
        },
        limit: {
          type: 'number',
          description: 'Number of results to return',
        },
      },
    },
  },
  {
    name: 'congress_get_treaties',
    description: 'Get list of treaties. Supports pagination.',
    inputSchema: {
      type: 'object',
      properties: {
        congress: {
          type: 'number',
          description: 'Congress number to filter by',
        },
        offset: {
          type: 'number',
          description: 'Offset for pagination',
        },
        limit: {
          type: 'number',
          description: 'Number of results to return',
        },
      },
    },
  },

  // GovInfo API Tools
  {
    name: 'govinfo_get_collections',
    description: 'Get list of all available collections from GovInfo API',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'govinfo_get_packages',
    description: 'Get packages for a specific collection. Uses cursor-based pagination with offsetMark.',
    inputSchema: {
      type: 'object',
      properties: {
        collection: {
          type: 'string',
          description: 'Collection code (e.g., BILLS, CFR, FR)',
        },
        offsetMark: {
          type: 'string',
          description: 'Offset mark for pagination (default: "*" for first page)',
        },
        pageSize: {
          type: 'number',
          description: 'Number of results per page (default: 100)',
        },
      },
      required: ['collection'],
    },
  },
  {
    name: 'govinfo_get_package',
    description: 'Get details for a specific package',
    inputSchema: {
      type: 'object',
      properties: {
        packageId: {
          type: 'string',
          description: 'Package ID',
        },
      },
      required: ['packageId'],
    },
  },
  {
    name: 'govinfo_get_granules',
    description: 'Get granules for a package. Supports cursor-based pagination.',
    inputSchema: {
      type: 'object',
      properties: {
        packageId: {
          type: 'string',
          description: 'Package ID',
        },
        offsetMark: {
          type: 'string',
          description: 'Offset mark for pagination',
        },
        pageSize: {
          type: 'number',
          description: 'Number of results per page',
        },
      },
      required: ['packageId'],
    },
  },
  {
    name: 'govinfo_search',
    description: 'Search for content in GovInfo. Supports cursor-based pagination.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Search query',
        },
        collection: {
          type: 'string',
          description: 'Optional collection to search within',
        },
        offsetMark: {
          type: 'string',
          description: 'Offset mark for pagination',
        },
        pageSize: {
          type: 'number',
          description: 'Number of results per page',
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'govinfo_get_published',
    description: 'Get content published on a specific date or date range',
    inputSchema: {
      type: 'object',
      properties: {
        startDate: {
          type: 'string',
          description: 'Start date (YYYY-MM-DD)',
        },
        endDate: {
          type: 'string',
          description: 'End date (YYYY-MM-DD), optional',
        },
        collection: {
          type: 'string',
          description: 'Optional collection to filter by',
        },
        offsetMark: {
          type: 'string',
          description: 'Offset mark for pagination',
        },
        pageSize: {
          type: 'number',
          description: 'Number of results per page',
        },
      },
      required: ['startDate'],
    },
  },
  {
    name: 'govinfo_get_bulkdata',
    description: 'Get bulk data from govinfo.gov/bulkdata endpoints. Supports XML and JSON formats.',
    inputSchema: {
      type: 'object',
      properties: {
        path: {
          type: 'string',
          description: 'Path to bulk data (e.g., "BILLS/118/1/hr")',
        },
        format: {
          type: 'string',
          enum: ['json', 'xml'],
          description: 'Response format (default: json)',
        },
      },
      required: ['path'],
    },
  },

  // Worker and Tracking Tools
  {
    name: 'worker_add_tasks',
    description: 'Add tasks to the worker pool for parallel processing. Tasks will be executed asynchronously.',
    inputSchema: {
      type: 'object',
      properties: {
        tasks: {
          type: 'array',
          description: 'Array of tasks to add',
          items: {
            type: 'object',
            properties: {
              id: {
                type: 'string',
                description: 'Unique task ID',
              },
              type: {
                type: 'string',
                enum: ['congress', 'govinfo'],
                description: 'API type',
              },
              endpoint: {
                type: 'string',
                description: 'Endpoint to call',
              },
              params: {
                type: 'object',
                description: 'Parameters for the API call',
              },
              priority: {
                type: 'number',
                description: 'Task priority (higher = more important)',
              },
            },
            required: ['id', 'type', 'endpoint', 'params'],
          },
        },
      },
      required: ['tasks'],
    },
  },
  {
    name: 'worker_start',
    description: 'Start the worker pool to process queued tasks',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'worker_status',
    description: 'Get current status of the worker pool',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'tracker_get_status',
    description: 'Get ingestion tracking status and statistics',
    inputSchema: {
      type: 'object',
      properties: {
        status: {
          type: 'string',
          enum: ['pending', 'in_progress', 'completed', 'failed'],
          description: 'Filter by status',
        },
      },
    },
  },
  {
    name: 'rate_limit_info',
    description: 'Get current rate limit information for both APIs',
    inputSchema: {
      type: 'object',
      properties: {
        api: {
          type: 'string',
          enum: ['congress', 'govinfo'],
          description: 'API to get rate limit info for',
        },
      },
    },
  },
];

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

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args = {} } = request.params;

  try {
    switch (name) {
      // Congress.gov API handlers
      case 'congress_get_bills':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(await congressClient.getBills(args as any), null, 2),
            },
          ],
        };

      case 'congress_get_bill':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                await congressClient.getBill((args as any).congress, (args as any).billType, (args as any).billNumber),
                null,
                2
              ),
            },
          ],
        };

      case 'congress_get_amendments':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(await congressClient.getAmendments(args as any), null, 2),
            },
          ],
        };

      case 'congress_get_members':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(await congressClient.getMembers(args as any), null, 2),
            },
          ],
        };

      case 'congress_get_committees':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(await congressClient.getCommittees(args as any), null, 2),
            },
          ],
        };

      case 'congress_get_nominations':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(await congressClient.getNominations(args as any), null, 2),
            },
          ],
        };

      case 'congress_get_treaties':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(await congressClient.getTreaties(args as any), null, 2),
            },
          ],
        };

      // GovInfo API handlers
      case 'govinfo_get_collections':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(await govinfoClient.getCollections(), null, 2),
            },
          ],
        };

      case 'govinfo_get_packages':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(await govinfoClient.getPackages((args as any).collection, args as any), null, 2),
            },
          ],
        };

      case 'govinfo_get_package':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(await govinfoClient.getPackage((args as any).packageId), null, 2),
            },
          ],
        };

      case 'govinfo_get_granules':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(await govinfoClient.getGranules((args as any).packageId, args as any), null, 2),
            },
          ],
        };

      case 'govinfo_search':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(await govinfoClient.search((args as any).query, args as any), null, 2),
            },
          ],
        };

      case 'govinfo_get_published':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                await govinfoClient.getPublished((args as any).startDate, (args as any).endDate, args as any),
                null,
                2
              ),
            },
          ],
        };

      case 'govinfo_get_bulkdata':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                await govinfoClient.getBulkData((args as any).path, (args as any).format || 'json'),
                null,
                2
              ),
            },
          ],
        };

      // Worker pool handlers
      case 'worker_add_tasks':
        workerPool.addTasks((args as any).tasks);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                message: `Added ${(args as any).tasks.length} tasks to worker pool`,
                status: workerPool.getStatus(),
              }, null, 2),
            },
          ],
        };

      case 'worker_start':
        workerPool.start();
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                message: 'Worker pool started',
                status: workerPool.getStatus(),
              }, null, 2),
            },
          ],
        };

      case 'worker_status':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(workerPool.getStatus(), null, 2),
            },
          ],
        };

      // Tracking handlers
      case 'tracker_get_status':
        const records = (args as any).status
          ? ingestionTracker.getRecordsByStatus((args as any).status)
          : ingestionTracker.getAllRecords();
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                total: records.length,
                records: records.slice(0, 100), // Limit to first 100 for readability
              }, null, 2),
            },
          ],
        };

      case 'rate_limit_info':
        const api = (args as any).api || 'congress';
        const limitInfo = rateLimiter.getLimitInfo(api);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                api,
                ...limitInfo,
                remaining: rateLimiter.getRemainingRequests(api),
                resetTime: new Date(rateLimiter.getResetTime(api)).toISOString(),
              }, null, 2),
            },
          ],
        };

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ error: errorMessage }, null, 2),
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  // Initialize ingestion tracker
  await ingestionTracker.initialize();

  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('Bulk Data MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
