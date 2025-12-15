/**
 * Example usage script for the Bulk Data MCP Server
 * 
 * This demonstrates how to use the MCP server programmatically
 * to fetch data from Congress.gov and GovInfo.gov
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

async function main() {
  // Create transport to connect to the MCP server
  const transport = new StdioClientTransport({
    command: 'node',
    args: ['./dist/index.js'],
    env: {
      CONGRESS_API_KEY: process.env.CONGRESS_API_KEY || '',
      GOVINFO_API_KEY: process.env.GOVINFO_API_KEY || '',
    },
  });

  // Create MCP client
  const client = new Client(
    {
      name: 'bulk-data-example-client',
      version: '1.0.0',
    },
    {
      capabilities: {},
    }
  );

  // Connect to server
  console.log('Connecting to MCP server...');
  await client.connect(transport);
  console.log('Connected!');

  try {
    // Example 1: List available tools
    console.log('\n=== Example 1: List Available Tools ===');
    const tools = await client.listTools();
    console.log(`Found ${tools.tools.length} tools:`);
    tools.tools.slice(0, 5).forEach(tool => {
      console.log(`  - ${tool.name}: ${tool.description}`);
    });

    // Example 2: Get recent bills
    console.log('\n=== Example 2: Get Recent Bills ===');
    const billsResult = await client.callTool({
      name: 'congress_get_bills',
      arguments: {
        offset: 0,
        limit: 5,
        congress: 118,
      },
    });
    console.log('Bills result:', JSON.parse(billsResult.content[0].text).data);

    // Example 3: Check rate limit status
    console.log('\n=== Example 3: Check Rate Limit ===');
    const rateLimitResult = await client.callTool({
      name: 'rate_limit_info',
      arguments: {
        api: 'congress',
      },
    });
    console.log('Rate limit info:', JSON.parse(rateLimitResult.content[0].text));

    // Example 4: Get GovInfo collections
    console.log('\n=== Example 4: Get GovInfo Collections ===');
    const collectionsResult = await client.callTool({
      name: 'govinfo_get_collections',
      arguments: {},
    });
    const collections = JSON.parse(collectionsResult.content[0].text);
    console.log(`Found ${collections.data.collections?.length || 0} collections`);
    if (collections.data.collections) {
      collections.data.collections.slice(0, 5).forEach((col: any) => {
        console.log(`  - ${col.collectionCode}: ${col.collectionName}`);
      });
    }

    // Example 5: Add tasks to worker pool
    console.log('\n=== Example 5: Worker Pool Example ===');
    const tasks = [
      {
        id: 'bills-page-1',
        type: 'congress',
        endpoint: 'bills',
        params: {
          offset: 0,
          limit: 10,
          congress: 118,
        },
        priority: 1,
      },
      {
        id: 'bills-page-2',
        type: 'congress',
        endpoint: 'bills',
        params: {
          offset: 10,
          limit: 10,
          congress: 118,
        },
        priority: 1,
      },
    ];

    const addTasksResult = await client.callTool({
      name: 'worker_add_tasks',
      arguments: { tasks },
    });
    console.log('Added tasks:', JSON.parse(addTasksResult.content[0].text));

    // Check worker status
    const statusResult = await client.callTool({
      name: 'worker_status',
      arguments: {},
    });
    console.log('Worker status:', JSON.parse(statusResult.content[0].text));

    // Example 6: Search GovInfo
    console.log('\n=== Example 6: Search GovInfo ===');
    const searchResult = await client.callTool({
      name: 'govinfo_search',
      arguments: {
        query: 'budget',
        pageSize: 5,
      },
    });
    const searchData = JSON.parse(searchResult.content[0].text);
    console.log('Search results:', searchData.data);

    // Example 7: Get tracking status
    console.log('\n=== Example 7: Get Tracking Status ===');
    const trackingResult = await client.callTool({
      name: 'tracker_get_status',
      arguments: {},
    });
    const trackingData = JSON.parse(trackingResult.content[0].text);
    console.log(`Total tracked records: ${trackingData.total}`);
    console.log('Recent records:', trackingData.records.slice(0, 3));

  } catch (error) {
    console.error('Error:', error);
  } finally {
    // Close connection
    await client.close();
    console.log('\nConnection closed.');
  }
}

// Run the example
main().catch(console.error);
