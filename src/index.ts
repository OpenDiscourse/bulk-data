#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';
import { CongressApiClient, CongressEndpoint } from './congress/congressClient.js';
import { GovInfoApiClient } from './govinfo/govinfoClient.js';
import { StorageManager } from './storage/storageManager.js';
import { WorkerPool } from './workers/workerPool.js';

// Load environment variables
dotenv.config();

// Initialize storage
const storage = new StorageManager();

// Initialize API clients
const congressClient = new CongressApiClient(
  {
    apiKey: process.env.CONGRESS_API_KEY || '',
  },
  storage
);

const govinfoClient = new GovInfoApiClient(
  {
    apiKey: process.env.GOVINFO_API_KEY || '',
  },
  storage
);

// Initialize worker pool
const workerPool = new WorkerPool(
  {
    maxWorkers: parseInt(process.env.MAX_WORKERS || '10', 10),
    concurrency: parseInt(process.env.WORKER_CONCURRENCY || '5', 10),
  },
  storage,
  congressClient,
  govinfoClient
);

/**
 * MCP Server for Congress and GovInfo bulk data ingestion
 */
class BulkDataMCPServer {
  private server: Server;

  constructor() {
    this.server = new Server(
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

    this.setupToolHandlers();
    
    // Error handling
    this.server.onerror = (error) => {
      console.error('[MCP Error]', error);
    };

    process.on('SIGINT', async () => {
      await this.cleanup();
      process.exit(0);
    });
  }

  private setupToolHandlers(): void {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: this.getTools(),
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          // Congress API tools
          case 'congress_fetch_bills':
            return await this.handleCongressFetchBills(args);
          case 'congress_fetch_amendments':
            return await this.handleCongressFetchAmendments(args);
          case 'congress_fetch_committees':
            return await this.handleCongressFetchCommittees(args);
          case 'congress_fetch_members':
            return await this.handleCongressFetchMembers(args);
          case 'congress_fetch_nominations':
            return await this.handleCongressFetchNominations(args);
          case 'congress_fetch_congressional_record':
            return await this.handleCongressFetchCongressionalRecord(args);
          case 'congress_fetch_committee_communications':
            return await this.handleCongressFetchCommitteeCommunications(args);
          case 'congress_fetch_treaties':
            return await this.handleCongressFetchTreaties(args);
          case 'congress_ingest_endpoint':
            return await this.handleCongressIngestEndpoint(args);

          // GovInfo API tools
          case 'govinfo_list_collections':
            return await this.handleGovInfoListCollections();
          case 'govinfo_query_collection':
            return await this.handleGovInfoQueryCollection(args);
          case 'govinfo_get_package':
            return await this.handleGovInfoGetPackage(args);
          case 'govinfo_search':
            return await this.handleGovInfoSearch(args);
          case 'govinfo_ingest_collection':
            return await this.handleGovInfoIngestCollection(args);
          case 'govinfo_ingest_bulkdata':
            return await this.handleGovInfoIngestBulkData(args);

          // Worker pool tools
          case 'worker_add_congress_task':
            return await this.handleWorkerAddCongressTask(args);
          case 'worker_add_govinfo_task':
            return await this.handleWorkerAddGovInfoTask(args);
          case 'worker_add_bulkdata_task':
            return await this.handleWorkerAddBulkDataTask(args);
          case 'worker_get_status':
            return await this.handleWorkerGetStatus();
          case 'worker_pause':
            return await this.handleWorkerPause();
          case 'worker_resume':
            return await this.handleWorkerResume();

          // Storage tools
          case 'storage_get_stats':
            return await this.handleStorageGetStats(args);
          case 'storage_check_ingested':
            return await this.handleStorageCheckIngested(args);

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  private getTools(): Tool[] {
    return [
      // Congress API tools
      {
        name: 'congress_fetch_bills',
        description: 'Fetch bills from Congress API with pagination. Returns up to 250 bills per request.',
        inputSchema: {
          type: 'object',
          properties: {
            congress: { type: 'number', description: 'Congress number (e.g., 118)' },
            type: { type: 'string', description: 'Bill type (hr, s, hjres, sjres, etc.)' },
            offset: { type: 'number', description: 'Starting offset (default: 0)' },
            limit: { type: 'number', description: 'Number of results (max: 250, default: 250)' },
          },
        },
      },
      {
        name: 'congress_fetch_amendments',
        description: 'Fetch amendments from Congress API with pagination.',
        inputSchema: {
          type: 'object',
          properties: {
            congress: { type: 'number' },
            type: { type: 'string' },
            offset: { type: 'number' },
            limit: { type: 'number' },
          },
        },
      },
      {
        name: 'congress_fetch_committees',
        description: 'Fetch committees from Congress API with pagination.',
        inputSchema: {
          type: 'object',
          properties: {
            chamber: { type: 'string', enum: ['house', 'senate', 'joint'] },
            congress: { type: 'number' },
            offset: { type: 'number' },
            limit: { type: 'number' },
          },
        },
      },
      {
        name: 'congress_fetch_members',
        description: 'Fetch Congress members with pagination.',
        inputSchema: {
          type: 'object',
          properties: {
            currentMember: { type: 'boolean' },
            congress: { type: 'number' },
            offset: { type: 'number' },
            limit: { type: 'number' },
          },
        },
      },
      {
        name: 'congress_fetch_nominations',
        description: 'Fetch nominations from Congress API with pagination.',
        inputSchema: {
          type: 'object',
          properties: {
            congress: { type: 'number' },
            offset: { type: 'number' },
            limit: { type: 'number' },
          },
        },
      },
      {
        name: 'congress_fetch_congressional_record',
        description: 'Fetch Congressional Record entries with pagination.',
        inputSchema: {
          type: 'object',
          properties: {
            year: { type: 'number' },
            month: { type: 'number' },
            day: { type: 'number' },
            offset: { type: 'number' },
            limit: { type: 'number' },
          },
        },
      },
      {
        name: 'congress_fetch_committee_communications',
        description: 'Fetch committee communications with pagination.',
        inputSchema: {
          type: 'object',
          properties: {
            congress: { type: 'number' },
            type: { type: 'string' },
            offset: { type: 'number' },
            limit: { type: 'number' },
          },
        },
      },
      {
        name: 'congress_fetch_treaties',
        description: 'Fetch treaties from Congress API with pagination.',
        inputSchema: {
          type: 'object',
          properties: {
            congress: { type: 'number' },
            offset: { type: 'number' },
            limit: { type: 'number' },
          },
        },
      },
      {
        name: 'congress_ingest_endpoint',
        description: 'Ingest all data from a Congress API endpoint with automatic pagination and deduplication.',
        inputSchema: {
          type: 'object',
          properties: {
            endpoint: {
              type: 'string',
              enum: ['bill', 'amendment', 'committee', 'member', 'nomination', 'congressional-record', 'committee-communication', 'treaty'],
            },
            params: { type: 'object', description: 'Additional parameters (congress, type, etc.)' },
          },
          required: ['endpoint'],
        },
      },

      // GovInfo API tools
      {
        name: 'govinfo_list_collections',
        description: 'List all available collections in GovInfo API.',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'govinfo_query_collection',
        description: 'Query a specific collection with pagination. Returns up to 1000 packages per request.',
        inputSchema: {
          type: 'object',
          properties: {
            collection: { type: 'string', description: 'Collection code (e.g., BILLS, CFR, FR)' },
            offset: { type: 'number' },
            pageSize: { type: 'number', description: 'Number of results (max: 1000)' },
          },
          required: ['collection'],
        },
      },
      {
        name: 'govinfo_get_package',
        description: 'Get detailed information about a specific package.',
        inputSchema: {
          type: 'object',
          properties: {
            packageId: { type: 'string', description: 'Package ID (e.g., BILLS-118hr1-ih)' },
          },
          required: ['packageId'],
        },
      },
      {
        name: 'govinfo_search',
        description: 'Search across GovInfo collections.',
        inputSchema: {
          type: 'object',
          properties: {
            query: { type: 'string', description: 'Search query' },
            collection: { type: 'string', description: 'Filter by collection' },
            offset: { type: 'number' },
            pageSize: { type: 'number' },
          },
          required: ['query'],
        },
      },
      {
        name: 'govinfo_ingest_collection',
        description: 'Ingest all packages from a collection with automatic pagination and deduplication.',
        inputSchema: {
          type: 'object',
          properties: {
            collection: { type: 'string', description: 'Collection code' },
          },
          required: ['collection'],
        },
      },
      {
        name: 'govinfo_ingest_bulkdata',
        description: 'Ingest bulk data from a specific path (e.g., /BILLS, /CFR/2024).',
        inputSchema: {
          type: 'object',
          properties: {
            path: { type: 'string', description: 'Bulk data path' },
          },
          required: ['path'],
        },
      },

      // Worker pool tools
      {
        name: 'worker_add_congress_task',
        description: 'Add a Congress API ingestion task to the worker pool for parallel processing.',
        inputSchema: {
          type: 'object',
          properties: {
            endpoint: { type: 'string' },
            params: { type: 'object' },
          },
          required: ['endpoint'],
        },
      },
      {
        name: 'worker_add_govinfo_task',
        description: 'Add a GovInfo collection ingestion task to the worker pool.',
        inputSchema: {
          type: 'object',
          properties: {
            collection: { type: 'string' },
          },
          required: ['collection'],
        },
      },
      {
        name: 'worker_add_bulkdata_task',
        description: 'Add a bulk data ingestion task to the worker pool.',
        inputSchema: {
          type: 'object',
          properties: {
            path: { type: 'string' },
          },
          required: ['path'],
        },
      },
      {
        name: 'worker_get_status',
        description: 'Get current status of the worker pool.',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'worker_pause',
        description: 'Pause all workers.',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'worker_resume',
        description: 'Resume all workers.',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },

      // Storage tools
      {
        name: 'storage_get_stats',
        description: 'Get ingestion statistics.',
        inputSchema: {
          type: 'object',
          properties: {
            collection: { type: 'string', description: 'Filter by collection' },
          },
        },
      },
      {
        name: 'storage_check_ingested',
        description: 'Check if a specific item has been ingested.',
        inputSchema: {
          type: 'object',
          properties: {
            collection: { type: 'string' },
            packageId: { type: 'string' },
          },
          required: ['collection', 'packageId'],
        },
      },
    ];
  }

  // Congress API handlers
  private async handleCongressFetchBills(args: any) {
    const data = await congressClient.fetchBills(
      { congress: args.congress, type: args.type },
      { offset: args.offset || 0, limit: args.limit || 250 }
    );
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  }

  private async handleCongressFetchAmendments(args: any) {
    const data = await congressClient.fetchAmendments(
      { congress: args.congress, type: args.type },
      { offset: args.offset || 0, limit: args.limit || 250 }
    );
    
    return {
      content: [{ type: 'text', text: JSON.stringify(data, null, 2) }],
    };
  }

  private async handleCongressFetchCommittees(args: any) {
    const data = await congressClient.fetchCommittees(
      { chamber: args.chamber, congress: args.congress },
      { offset: args.offset || 0, limit: args.limit || 250 }
    );
    
    return {
      content: [{ type: 'text', text: JSON.stringify(data, null, 2) }],
    };
  }

  private async handleCongressFetchMembers(args: any) {
    const data = await congressClient.fetchMembers(
      { currentMember: args.currentMember, congress: args.congress },
      { offset: args.offset || 0, limit: args.limit || 250 }
    );
    
    return {
      content: [{ type: 'text', text: JSON.stringify(data, null, 2) }],
    };
  }

  private async handleCongressFetchNominations(args: any) {
    const data = await congressClient.fetchNominations(
      { congress: args.congress },
      { offset: args.offset || 0, limit: args.limit || 250 }
    );
    
    return {
      content: [{ type: 'text', text: JSON.stringify(data, null, 2) }],
    };
  }

  private async handleCongressFetchCongressionalRecord(args: any) {
    const data = await congressClient.fetchCongressionalRecord(
      { year: args.year, month: args.month, day: args.day },
      { offset: args.offset || 0, limit: args.limit || 250 }
    );
    
    return {
      content: [{ type: 'text', text: JSON.stringify(data, null, 2) }],
    };
  }

  private async handleCongressFetchCommitteeCommunications(args: any) {
    const data = await congressClient.fetchCommitteeCommunications(
      { congress: args.congress, type: args.type },
      { offset: args.offset || 0, limit: args.limit || 250 }
    );
    
    return {
      content: [{ type: 'text', text: JSON.stringify(data, null, 2) }],
    };
  }

  private async handleCongressFetchTreaties(args: any) {
    const data = await congressClient.fetchTreaties(
      { congress: args.congress },
      { offset: args.offset || 0, limit: args.limit || 250 }
    );
    
    return {
      content: [{ type: 'text', text: JSON.stringify(data, null, 2) }],
    };
  }

  private async handleCongressIngestEndpoint(args: any) {
    await congressClient.ingestEndpoint(
      args.endpoint as CongressEndpoint,
      args.params || {}
    );
    
    return {
      content: [
        {
          type: 'text',
          text: `Successfully ingested all data from ${args.endpoint}`,
        },
      ],
    };
  }

  // GovInfo API handlers
  private async handleGovInfoListCollections() {
    const collections = await govinfoClient.getCollections();
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(collections, null, 2),
        },
      ],
    };
  }

  private async handleGovInfoQueryCollection(args: any) {
    const data = await govinfoClient.queryCollection(
      args.collection,
      { offset: args.offset || 0, pageSize: args.pageSize || 100 }
    );
    
    return {
      content: [{ type: 'text', text: JSON.stringify(data, null, 2) }],
    };
  }

  private async handleGovInfoGetPackage(args: any) {
    const data = await govinfoClient.getPackageSummary(args.packageId);
    
    return {
      content: [{ type: 'text', text: JSON.stringify(data, null, 2) }],
    };
  }

  private async handleGovInfoSearch(args: any) {
    const data = await govinfoClient.search(
      args.query,
      args.collection,
      { offset: args.offset || 0, pageSize: args.pageSize || 100 }
    );
    
    return {
      content: [{ type: 'text', text: JSON.stringify(data, null, 2) }],
    };
  }

  private async handleGovInfoIngestCollection(args: any) {
    await govinfoClient.ingestCollection(args.collection);
    
    return {
      content: [
        {
          type: 'text',
          text: `Successfully ingested collection ${args.collection}`,
        },
      ],
    };
  }

  private async handleGovInfoIngestBulkData(args: any) {
    await govinfoClient.ingestBulkData(args.path);
    
    return {
      content: [
        {
          type: 'text',
          text: `Successfully ingested bulk data from ${args.path}`,
        },
      ],
    };
  }

  // Worker pool handlers
  private async handleWorkerAddCongressTask(args: any) {
    const taskId = workerPool.addCongressTask(args.endpoint, args.params || {});
    
    return {
      content: [
        {
          type: 'text',
          text: `Added Congress task ${taskId} to worker pool`,
        },
      ],
    };
  }

  private async handleWorkerAddGovInfoTask(args: any) {
    const taskId = workerPool.addGovInfoTask(args.collection);
    
    return {
      content: [
        {
          type: 'text',
          text: `Added GovInfo task ${taskId} to worker pool`,
        },
      ],
    };
  }

  private async handleWorkerAddBulkDataTask(args: any) {
    const taskId = workerPool.addBulkDataTask(args.path);
    
    return {
      content: [
        {
          type: 'text',
          text: `Added bulk data task ${taskId} to worker pool`,
        },
      ],
    };
  }

  private async handleWorkerGetStatus() {
    const status = workerPool.getStatus();
    const activeWorkers = storage.getActiveWorkers();
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ queueStatus: status, activeWorkers }, null, 2),
        },
      ],
    };
  }

  private async handleWorkerPause() {
    workerPool.pause();
    
    return {
      content: [{ type: 'text', text: 'Worker pool paused' }],
    };
  }

  private async handleWorkerResume() {
    workerPool.resume();
    
    return {
      content: [{ type: 'text', text: 'Worker pool resumed' }],
    };
  }

  // Storage handlers
  private async handleStorageGetStats(args: any) {
    const stats = storage.getIngestionStats(args.collection);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(stats, null, 2),
        },
      ],
    };
  }

  private async handleStorageCheckIngested(args: any) {
    const isIngested = storage.isIngested(args.collection, args.packageId);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ ingested: isIngested }),
        },
      ],
    };
  }

  private async cleanup(): void {
    console.log('Cleaning up...');
    storage.close();
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Bulk Data MCP Server running on stdio');
  }
}

// Run the server
const server = new BulkDataMCPServer();
server.run().catch(console.error);
