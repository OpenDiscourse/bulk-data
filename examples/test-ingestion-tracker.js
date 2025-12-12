#!/usr/bin/env node

/**
 * Example script demonstrating ingestion tracker functionality
 * 
 * This script tests the IngestionTracker to ensure it properly
 * tracks ingested data and prevents duplicates.
 */

import { IngestionTracker } from '../dist/utils/ingestion-tracker.js';
import { unlink } from 'fs/promises';

async function testIngestionTracker() {
  console.log('Testing Ingestion Tracker...\n');

  const dbPath = './test-tracker.db';
  const tracker = new IngestionTracker(dbPath);

  try {
    // Test data
    const billData = {
      congress: 118,
      type: 'hr',
      number: 1,
      title: 'Test Bill'
    };

    const checksum = tracker.generateChecksum(billData);
    console.log('1. Generated checksum:', checksum);

    // First ingestion
    console.log('\n2. Recording first ingestion...');
    await tracker.recordIngestion({
      endpoint: 'congress/bills',
      resourceId: '118-hr-1',
      resourceType: 'bill',
      checksum,
      metadata: JSON.stringify({ congress: 118, type: 'hr' })
    });
    console.log('   ✓ First record saved');

    // Check if already ingested
    console.log('\n3. Checking if already ingested...');
    const isIngested = await tracker.isAlreadyIngested('congress/bills', '118-hr-1', checksum);
    console.log('   Already ingested:', isIngested);

    // Try to ingest again (should be detected as duplicate)
    console.log('\n4. Attempting duplicate ingestion...');
    const isDuplicate = await tracker.isAlreadyIngested('congress/bills', '118-hr-1', checksum);
    if (isDuplicate) {
      console.log('   ✓ Duplicate detected successfully');
    }

    // Ingest a different bill
    const bill2Data = {
      congress: 118,
      type: 'hr',
      number: 2,
      title: 'Another Test Bill'
    };
    const checksum2 = tracker.generateChecksum(bill2Data);
    
    console.log('\n5. Recording second bill...');
    await tracker.recordIngestion({
      endpoint: 'congress/bills',
      resourceId: '118-hr-2',
      resourceType: 'bill',
      checksum: checksum2,
      metadata: JSON.stringify({ congress: 118, type: 'hr' })
    });
    console.log('   ✓ Second record saved');

    // Get statistics
    console.log('\n6. Getting ingestion statistics...');
    const stats = await tracker.getIngestionStats('congress/bills');
    console.log('   Total records:', stats.total);
    console.log('   By type:', stats.byType);
    console.log('   Last ingestion:', stats.lastIngestion);

    console.log('\n✓ Ingestion tracker test completed successfully!');

  } finally {
    tracker.close();
    // Clean up test database
    try {
      await unlink(dbPath);
      console.log('\nTest database cleaned up.');
    } catch (err) {
      // Ignore error if file doesn't exist
    }
  }
}

testIngestionTracker().catch(console.error);
