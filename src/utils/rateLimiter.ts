/**
 * Rate Limiting Utility
 * Manages API rate limits for both Congress.gov (5000/hour) and GovInfo APIs
 */

import { RateLimitConfig } from '../types/index.js';

export class RateLimiter {
  private limits: Map<string, RateLimitConfig> = new Map();

  constructor() {
    // Initialize rate limits for known APIs
    this.initializeLimit('congress', 5000); // 5000 requests per hour
    this.initializeLimit('govinfo', 5000);  // 5000 requests per hour (api.data.gov)
  }

  private initializeLimit(apiName: string, requestsPerHour: number): void {
    this.limits.set(apiName, {
      requestsPerHour,
      currentCount: 0,
      resetTime: Date.now() + 3600000, // 1 hour from now
    });
  }

  async checkLimit(apiName: string): Promise<boolean> {
    const limit = this.limits.get(apiName);
    if (!limit) {
      throw new Error(`Unknown API: ${apiName}`);
    }

    // Check if we need to reset the counter
    if (Date.now() >= limit.resetTime) {
      limit.currentCount = 0;
      limit.resetTime = Date.now() + 3600000;
    }

    // Check if we're under the limit
    if (limit.currentCount >= limit.requestsPerHour) {
      const waitTime = limit.resetTime - Date.now();
      console.warn(`Rate limit reached for ${apiName}. Reset in ${Math.ceil(waitTime / 1000)}s`);
      return false;
    }

    return true;
  }

  incrementCount(apiName: string): void {
    const limit = this.limits.get(apiName);
    if (limit) {
      limit.currentCount++;
    }
  }

  getRemainingRequests(apiName: string): number {
    const limit = this.limits.get(apiName);
    if (!limit) return 0;
    return Math.max(0, limit.requestsPerHour - limit.currentCount);
  }

  getResetTime(apiName: string): number {
    const limit = this.limits.get(apiName);
    return limit?.resetTime || 0;
  }

  getLimitInfo(apiName: string): RateLimitConfig | undefined {
    return this.limits.get(apiName);
  }
}

export const rateLimiter = new RateLimiter();
