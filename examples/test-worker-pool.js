#!/usr/bin/env node

/**
 * Example script demonstrating worker pool functionality
 * 
 * This script tests the WorkerPool to ensure it properly
 * manages parallel task execution.
 */

import { WorkerPool } from '../dist/utils/worker-pool.js';

async function simulateTask(id, duration) {
  console.log(`  Task ${id} started`);
  await new Promise(resolve => setTimeout(resolve, duration));
  console.log(`  Task ${id} completed (${duration}ms)`);
  return `Result from task ${id}`;
}

async function testWorkerPool() {
  console.log('Testing Worker Pool...\n');

  // Create a worker pool with 3 concurrent workers
  const workerPool = new WorkerPool(3);

  console.log('1. Adding 6 tasks (3 workers, so first 3 run immediately):\n');

  const tasks = [];
  for (let i = 1; i <= 6; i++) {
    const task = {
      id: `task-${i}`,
      endpoint: 'test',
      params: {},
      priority: i <= 3 ? 2 : 1 // First 3 have higher priority
    };

    const taskPromise = workerPool.addTask(
      task,
      () => simulateTask(i, 500 + Math.random() * 500)
    );
    tasks.push(taskPromise);

    console.log(`   Added task ${i} - Active: ${workerPool.getActiveCount()}, Pending: ${workerPool.getPendingCount()}, Queued: ${workerPool.getQueueSize()}`);
  }

  console.log('\n2. Waiting for all tasks to complete...\n');
  const results = await Promise.all(tasks);

  console.log('\n3. All tasks completed!');
  console.log('   Results:', results);

  console.log('\n4. Final worker stats:');
  console.log(`   Active: ${workerPool.getActiveCount()}`);
  console.log(`   Pending: ${workerPool.getPendingCount()}`);
  console.log(`   Queued: ${workerPool.getQueueSize()}`);

  await workerPool.waitForAll();

  console.log('\n✓ Worker pool test completed successfully!');
}

testWorkerPool().catch(console.error);
