import Bottleneck from 'bottleneck';

/**
 * Rate limiter configuration for different APIs
 */
export interface RateLimiterConfig {
  maxConcurrent: number;
  minTime: number;
  reservoir: number;
  reservoirRefreshAmount: number;
  reservoirRefreshInterval: number;
}

/**
 * Rate limiter for Congress.gov API
 * Limit: 5000 requests per hour
 */
export const congressRateLimiter = new Bottleneck({
  maxConcurrent: 10, // Max concurrent requests
  minTime: 100, // Minimum time between requests (ms)
  reservoir: 5000, // Initial number of requests
  reservoirRefreshAmount: 5000, // Refill amount
  reservoirRefreshInterval: 60 * 60 * 1000, // Refill every hour
});

/**
 * Rate limiter for GovInfo.gov API
 * Conservative limit: 1000 requests per hour (actual limit not documented)
 */
export const govinfoRateLimiter = new Bottleneck({
  maxConcurrent: 5,
  minTime: 200,
  reservoir: 1000,
  reservoirRefreshAmount: 1000,
  reservoirRefreshInterval: 60 * 60 * 1000,
});

/**
 * Rate limiter for bulk data downloads
 * More conservative to avoid overwhelming the server
 */
export const bulkDataRateLimiter = new Bottleneck({
  maxConcurrent: 3,
  minTime: 500,
  reservoir: 500,
  reservoirRefreshAmount: 500,
  reservoirRefreshInterval: 60 * 60 * 1000,
});

/**
 * Track rate limit headers from API responses
 */
export interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset: Date;
}

/**
 * Extract rate limit information from response headers
 */
export function extractRateLimitInfo(headers: any): RateLimitInfo | null {
  const limit = headers['x-ratelimit-limit'];
  const remaining = headers['x-ratelimit-remaining'];
  const reset = headers['x-ratelimit-reset'];

  if (limit && remaining && reset) {
    return {
      limit: parseInt(limit, 10),
      remaining: parseInt(remaining, 10),
      reset: new Date(parseInt(reset, 10) * 1000),
    };
  }

  return null;
}

/**
 * Calculate delay needed based on rate limit info
 */
export function calculateDelay(rateLimitInfo: RateLimitInfo): number {
  if (rateLimitInfo.remaining <= 10) {
    const now = new Date();
    const resetTime = rateLimitInfo.reset.getTime();
    const nowTime = now.getTime();
    
    if (resetTime > nowTime) {
      return resetTime - nowTime;
    }
  }
  
  return 0;
}
