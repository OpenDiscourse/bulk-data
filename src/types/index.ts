/**
 * Type definitions for the Bulk Data MCP Server
 */

export interface RateLimitConfig {
  requestsPerHour: number;
  currentCount: number;
  resetTime: number;
}

export interface PaginationState {
  offset: number;
  limit: number;
  total?: number;
  hasMore: boolean;
}

export interface IngestionRecord {
  id: string;
  endpoint: string;
  timestamp: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  metadata?: Record<string, any>;
}

export interface WorkerTask {
  id: string;
  type: 'congress' | 'govinfo';
  endpoint: string;
  params: Record<string, any>;
  priority: number;
}

export interface APIResponse<T = any> {
  data: T;
  pagination?: PaginationState;
  rateLimitInfo?: RateLimitConfig;
}

export interface CongressAPIParams {
  congress?: number;
  billType?: string;
  billNumber?: string;
  offset?: number;
  limit?: number;
  format?: 'json' | 'xml';
}

export interface GovInfoAPIParams {
  collection?: string;
  packageId?: string;
  offsetMark?: string;
  pageSize?: number;
  format?: 'json' | 'xml';
}
