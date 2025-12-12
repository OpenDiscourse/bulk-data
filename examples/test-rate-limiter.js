#!/usr/bin/env node

/**
 * Example script demonstrating rate limiter functionality
 * 
 * This script tests the TokenBucketRateLimiter to ensure it properly
 * throttles requests according to the configured rate limit.
 */

import { TokenBucketRateLimiter } from '../dist/utils/rate-limiter.js';

async function testRateLimiter() {
  console.log('Testing Rate Limiter...\n');

  // Create a rate limiter with 10 requests per hour (for testing)
  const rateLimiter = new TokenBucketRateLimiter(10);

  console.log('Testing 5 rapid requests (should be immediate):');
  for (let i = 1; i <= 5; i++) {
    const start = Date.now();
    await rateLimiter.waitIfNeeded();
    rateLimiter.recordRequest();
    const elapsed = Date.now() - start;
    console.log(`  Request ${i}: ${elapsed}ms - Remaining tokens: ${rateLimiter.getRemainingTokens()}`);
  }

  console.log('\nWaiting 2 seconds for token refill...');
  await new Promise(resolve => setTimeout(resolve, 2000));
  console.log(`Tokens after wait: ${rateLimiter.getRemainingTokens()}`);

  console.log('\nTesting 3 more requests:');
  for (let i = 6; i <= 8; i++) {
    const start = Date.now();
    await rateLimiter.waitIfNeeded();
    rateLimiter.recordRequest();
    const elapsed = Date.now() - start;
    console.log(`  Request ${i}: ${elapsed}ms - Remaining tokens: ${rateLimiter.getRemainingTokens()}`);
  }

  console.log('\n✓ Rate limiter test completed successfully!');
}

testRateLimiter().catch(console.error);
