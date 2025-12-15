import { APIConfig } from '../types/index.js';

export function loadConfig(): APIConfig {
  // In a real implementation, this would load from environment variables
  // For now, we'll use defaults that can be overridden
  const config: APIConfig = {
    congressApiKey: process.env.CONGRESS_API_KEY || 'DEMO_KEY',
    govinfoApiKey: process.env.GOVINFO_API_KEY || 'DEMO_KEY',
    congressRateLimit: parseInt(process.env.CONGRESS_RATE_LIMIT || '5000', 10),
    govinfoRateLimit: parseInt(process.env.GOVINFO_RATE_LIMIT || '1000', 10),
    maxWorkers: parseInt(process.env.MAX_WORKERS || '4', 10),
    dbPath: process.env.DB_PATH || './ingestion-tracker.db'
  };

  return config;
}

export function validateConfig(config: APIConfig): void {
  if (!config.congressApiKey) {
    throw new Error('CONGRESS_API_KEY is required');
  }
  if (!config.govinfoApiKey) {
    throw new Error('GOVINFO_API_KEY is required');
  }
  if (config.congressRateLimit <= 0) {
    throw new Error('CONGRESS_RATE_LIMIT must be positive');
  }
  if (config.govinfoRateLimit <= 0) {
    throw new Error('GOVINFO_RATE_LIMIT must be positive');
  }
  if (config.maxWorkers <= 0) {
    throw new Error('MAX_WORKERS must be positive');
  }
}
