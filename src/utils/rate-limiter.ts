import { RateLimiter } from '../types/index.js';

export class TokenBucketRateLimiter implements RateLimiter {
  private tokens: number;
  private lastRefill: number;
  private readonly maxTokens: number;
  private readonly refillRate: number; // tokens per millisecond

  constructor(requestsPerHour: number) {
    this.maxTokens = requestsPerHour;
    this.tokens = requestsPerHour;
    this.lastRefill = Date.now();
    // Refill rate: tokens per millisecond (requestsPerHour tokens over 3600000 ms)
    this.refillRate = requestsPerHour / 3600000;
  }

  private refill(): void {
    const now = Date.now();
    const timePassed = now - this.lastRefill;
    const tokensToAdd = timePassed * this.refillRate;
    
    this.tokens = Math.min(this.maxTokens, this.tokens + tokensToAdd);
    this.lastRefill = now;
  }

  async waitIfNeeded(): Promise<void> {
    this.refill();
    
    if (this.tokens < 1) {
      // Calculate how long to wait for 1 token
      const waitTime = (1 - this.tokens) / this.refillRate;
      await new Promise(resolve => setTimeout(resolve, waitTime));
      this.refill();
    }
  }

  recordRequest(): void {
    this.refill();
    this.tokens = Math.max(0, this.tokens - 1);
  }

  getRemainingTokens(): number {
    this.refill();
    return Math.floor(this.tokens);
  }
}
