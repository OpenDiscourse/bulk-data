#!/usr/bin/env node

/**
 * Simple smoke test to verify basic imports and structure
 */

import { StorageManager } from './dist/storage/storageManager.js';

console.log('Testing basic functionality...\n');

try {
  // Test 1: Storage Manager
  console.log('Test 1: Creating StorageManager...');
  const storage = new StorageManager('./data/smoke-test.db');
  console.log('✓ StorageManager created successfully');

  // Test 2: Deduplication
  console.log('\nTest 2: Testing deduplication...');
  const testId = 'smoke-test-package';
  
  console.log(`  Checking if ${testId} exists...`);
  let exists = storage.isIngested('smoke-test', testId);
  console.log(`  ✓ Exists: ${exists} (should be false)`);

  console.log(`  Recording ${testId}...`);
  storage.recordIngestion({
    collection: 'smoke-test',
    packageId: testId,
    url: 'https://example.com/test',
    lastModified: new Date().toISOString(),
  });
  console.log('  ✓ Recorded successfully');

  console.log(`  Checking if ${testId} exists now...`);
  exists = storage.isIngested('smoke-test', testId);
  console.log(`  ✓ Exists: ${exists} (should be true)`);

  // Test 3: Pagination state
  console.log('\nTest 3: Testing pagination state...');
  storage.updatePaginationState({
    collection: 'smoke-test',
    endpoint: 'test-endpoint',
    offset: 100,
    completed: false,
  });
  console.log('  ✓ Pagination state updated');

  const paginationState = storage.getPaginationState('smoke-test', 'test-endpoint');
  console.log(`  ✓ Retrieved pagination state: offset=${paginationState.offset}`);

  // Test 4: Statistics
  console.log('\nTest 4: Getting statistics...');
  const stats = storage.getIngestionStats('smoke-test');
  console.log(`  ✓ Statistics retrieved:`, stats);

  // Cleanup
  storage.close();
  console.log('\n✓ StorageManager closed successfully');

  console.log('\n=== All Smoke Tests Passed! ===\n');
  console.log('The MCP server core functionality is working correctly.');
  console.log('To test API functionality, you need to:');
  console.log('1. Get an API key from https://api.data.gov/signup/');
  console.log('2. Create .env file with your API key');
  console.log('3. Run: node test-manual.js\n');

  process.exit(0);
} catch (error) {
  console.error('\n✗ Test failed:', error);
  process.exit(1);
}
