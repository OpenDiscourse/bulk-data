#!/usr/bin/env node

/**
 * Manual test script for the MCP server
 * Run with: node test-manual.js
 * 
 * This script tests the core functionality without needing an MCP client
 */

import { CongressApiClient } from './dist/congress/congressClient.js';
import { GovInfoApiClient } from './dist/govinfo/govinfoClient.js';
import { StorageManager } from './dist/storage/storageManager.js';
import { WorkerPool } from './dist/workers/workerPool.js';
import dotenv from 'dotenv';

dotenv.config();

const CONGRESS_API_KEY = process.env.CONGRESS_API_KEY || 'DEMO_KEY';
const GOVINFO_API_KEY = process.env.GOVINFO_API_KEY || 'DEMO_KEY';

async function runTests() {
  console.log('=== Bulk Data MCP Server Manual Tests ===\n');

  // Initialize components
  const storage = new StorageManager('./data/test-ingestion.db');
  
  const congressClient = new CongressApiClient(
    { apiKey: CONGRESS_API_KEY },
    storage
  );

  const govinfoClient = new GovInfoApiClient(
    { apiKey: GOVINFO_API_KEY },
    storage
  );

  const workerPool = new WorkerPool(
    { maxWorkers: 5, concurrency: 2 },
    storage,
    congressClient,
    govinfoClient
  );

  try {
    // Test 1: Fetch bills
    console.log('Test 1: Fetching bills from Congress API...');
    const bills = await congressClient.fetchBills(
      { congress: 118 },
      { offset: 0, limit: 5 }
    );
    console.log(`✓ Fetched ${bills.bills?.length || 0} bills`);
    console.log(`  Total available: ${bills.pagination?.count || 0}\n`);

    // Test 2: List GovInfo collections
    console.log('Test 2: Listing GovInfo collections...');
    const collections = await govinfoClient.getCollections();
    console.log(`✓ Found ${collections.length} collections`);
    if (collections.length > 0) {
      console.log(`  Examples: ${collections.slice(0, 5).map(c => c.collectionCode).join(', ')}\n`);
    }

    // Test 3: Query a collection
    console.log('Test 3: Querying BILLS collection...');
    const billsCollection = await govinfoClient.queryCollection(
      'BILLS',
      { offset: 0, pageSize: 5 }
    );
    console.log(`✓ Fetched ${billsCollection.packages?.length || 0} packages`);
    console.log(`  Total available: ${billsCollection.count || 0}\n`);

    // Test 4: Storage - check deduplication
    console.log('Test 4: Testing deduplication...');
    const isIngested = storage.isIngested('test-collection', 'test-package-1');
    console.log(`✓ Package ingested: ${isIngested}`);
    
    storage.recordIngestion({
      collection: 'test-collection',
      packageId: 'test-package-1',
      url: 'https://example.com/test',
      lastModified: new Date().toISOString(),
      metadata: '{"test": true}',
    });
    
    const isIngestedAfter = storage.isIngested('test-collection', 'test-package-1');
    console.log(`✓ After recording: ${isIngestedAfter}\n`);

    // Test 5: Worker pool status
    console.log('Test 5: Worker pool status...');
    const status = workerPool.getStatus();
    console.log(`✓ Worker status: ${JSON.stringify(status)}\n`);

    // Test 6: Get statistics
    console.log('Test 6: Storage statistics...');
    const stats = storage.getIngestionStats();
    console.log(`✓ Statistics:`, stats);
    console.log();

    console.log('=== All Tests Passed! ===\n');
    
    console.log('Next Steps:');
    console.log('1. Set up your API keys in .env file');
    console.log('2. Configure the MCP server in Claude Desktop (see MCP_CONFIGURATION.md)');
    console.log('3. Start using the tools in Claude!\n');

  } catch (error) {
    console.error('Test failed:', error);
    if (error.response) {
      console.error('Response data:', error.response.data);
      console.error('Response status:', error.response.status);
    }
  } finally {
    storage.close();
  }
}

// Run tests
runTests().catch(console.error);
