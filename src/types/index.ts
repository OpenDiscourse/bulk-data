export interface RateLimiter {
  waitIfNeeded(): Promise<void>;
  recordRequest(): void;
}

export interface PaginationState {
  offset: number;
  limit: number;
  total?: number;
  hasMore: boolean;
}

export interface IngestionRecord {
  id?: number;
  endpoint: string;
  resourceId: string;
  resourceType: string;
  ingestedAt: string;
  checksum: string;
  metadata?: string;
}

export interface WorkerTask {
  id: string;
  endpoint: string;
  params: Record<string, any>;
  priority: number;
}

export interface APIConfig {
  congressApiKey: string;
  govinfoApiKey: string;
  congressRateLimit: number;
  govinfoRateLimit: number;
  maxWorkers: number;
  dbPath: string;
}

export interface APIResponse<T = any> {
  data: T;
  pagination?: {
    offset: number;
    limit: number;
    total?: number;
    hasMore: boolean;
  };
  headers?: Record<string, string>;
}

export interface CongressBill {
  congress: number;
  type: string;
  number: number;
  title: string;
  updateDate: string;
}

export interface GovinfoPackage {
  packageId: string;
  title: string;
  dateIssued: string;
  collection: string;
}
