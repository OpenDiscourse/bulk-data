import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { congressRateLimiter, extractRateLimitInfo, calculateDelay } from '../utils/rateLimiter.js';
import { StorageManager } from '../storage/storageManager.js';

/**
 * Configuration for Congress API client
 */
export interface CongressApiConfig {
  apiKey: string;
  baseUrl?: string;
}

/**
 * Pagination parameters
 */
export interface PaginationParams {
  offset?: number;
  limit?: number;
}

/**
 * Congress API endpoints
 */
export enum CongressEndpoint {
  BILLS = 'bill',
  AMENDMENTS = 'amendment',
  COMMITTEES = 'committee',
  MEMBERS = 'member',
  NOMINATIONS = 'nomination',
  CONGRESSIONAL_RECORD = 'congressional-record',
  COMMITTEE_COMMUNICATIONS = 'committee-communication',
  TREATIES = 'treaty',
}

/**
 * Client for interacting with api.congress.gov
 */
export class CongressApiClient {
  private axios: AxiosInstance;
  private apiKey: string;
  private storage: StorageManager;

  constructor(config: CongressApiConfig, storage: StorageManager) {
    this.apiKey = config.apiKey;
    this.storage = storage;

    this.axios = axios.create({
      baseURL: config.baseUrl || 'https://api.congress.gov/v3',
      headers: {
        'X-Api-Key': this.apiKey,
      },
    });
  }

  /**
   * Generic method to fetch data from any endpoint with pagination
   */
  async fetchEndpoint(
    endpoint: CongressEndpoint,
    params: Record<string, any> = {},
    pagination: PaginationParams = {}
  ): Promise<any> {
    const { offset = 0, limit = 250 } = pagination;

    return congressRateLimiter.schedule(async () => {
      try {
        const response = await this.axios.get(`/${endpoint}`, {
          params: {
            ...params,
            offset,
            limit: Math.min(limit, 250), // Max 250 per request
          },
        });

        // Track rate limit info
        const rateLimitInfo = extractRateLimitInfo(response.headers);
        if (rateLimitInfo) {
          console.log(`Rate limit - Remaining: ${rateLimitInfo.remaining}/${rateLimitInfo.limit}`);
          
          const delay = calculateDelay(rateLimitInfo);
          if (delay > 0) {
            console.log(`Rate limit approaching, waiting ${delay}ms`);
            await new Promise(resolve => setTimeout(resolve, delay));
          }
        }

        return response.data;
      } catch (error: any) {
        if (error.response?.status === 429) {
          console.error('Rate limit exceeded, backing off...');
          await new Promise(resolve => setTimeout(resolve, 60000)); // Wait 1 minute
          throw error;
        }
        throw error;
      }
    });
  }

  /**
   * Fetch bills with pagination support
   */
  async fetchBills(params: {
    congress?: number;
    type?: string;
  } = {}, pagination: PaginationParams = {}): Promise<any> {
    return this.fetchEndpoint(CongressEndpoint.BILLS, params, pagination);
  }

  /**
   * Fetch amendments with pagination support
   */
  async fetchAmendments(params: {
    congress?: number;
    type?: string;
  } = {}, pagination: PaginationParams = {}): Promise<any> {
    return this.fetchEndpoint(CongressEndpoint.AMENDMENTS, params, pagination);
  }

  /**
   * Fetch committees with pagination support
   */
  async fetchCommittees(params: {
    chamber?: 'house' | 'senate' | 'joint';
    congress?: number;
  } = {}, pagination: PaginationParams = {}): Promise<any> {
    return this.fetchEndpoint(CongressEndpoint.COMMITTEES, params, pagination);
  }

  /**
   * Fetch members with pagination support
   */
  async fetchMembers(params: {
    currentMember?: boolean;
    congress?: number;
  } = {}, pagination: PaginationParams = {}): Promise<any> {
    return this.fetchEndpoint(CongressEndpoint.MEMBERS, params, pagination);
  }

  /**
   * Fetch nominations with pagination support
   */
  async fetchNominations(params: {
    congress?: number;
  } = {}, pagination: PaginationParams = {}): Promise<any> {
    return this.fetchEndpoint(CongressEndpoint.NOMINATIONS, params, pagination);
  }

  /**
   * Fetch congressional record with pagination support
   */
  async fetchCongressionalRecord(params: {
    year?: number;
    month?: number;
    day?: number;
  } = {}, pagination: PaginationParams = {}): Promise<any> {
    return this.fetchEndpoint(CongressEndpoint.CONGRESSIONAL_RECORD, params, pagination);
  }

  /**
   * Fetch committee communications with pagination support
   */
  async fetchCommitteeCommunications(params: {
    congress?: number;
    type?: string;
  } = {}, pagination: PaginationParams = {}): Promise<any> {
    return this.fetchEndpoint(CongressEndpoint.COMMITTEE_COMMUNICATIONS, params, pagination);
  }

  /**
   * Fetch treaties with pagination support
   */
  async fetchTreaties(params: {
    congress?: number;
  } = {}, pagination: PaginationParams = {}): Promise<any> {
    return this.fetchEndpoint(CongressEndpoint.TREATIES, params, pagination);
  }

  /**
   * Ingest all data from an endpoint with automatic pagination
   */
  async ingestEndpoint(
    endpoint: CongressEndpoint,
    params: Record<string, any> = {},
    onProgress?: (offset: number, total: number) => void
  ): Promise<void> {
    let offset = 0;
    const limit = 250;
    let hasMore = true;

    // Check for existing pagination state
    const paginationState = this.storage.getPaginationState('congress', endpoint);
    if (paginationState && !paginationState.completed) {
      offset = paginationState.offset;
      console.log(`Resuming from offset ${offset}`);
    }

    while (hasMore) {
      try {
        const data = await this.fetchEndpoint(endpoint, params, { offset, limit });
        
        const items = data[endpoint] || data.results || [];
        const total = data.pagination?.count || 0;

        console.log(`Fetched ${items.length} items at offset ${offset} of ${total}`);

        // Process each item
        for (const item of items) {
          const packageId = item.number || item.bioguideId || item.recordId || item.url;
          
          if (!this.storage.isIngested('congress', packageId)) {
            this.storage.recordIngestion({
              collection: 'congress',
              packageId: packageId,
              url: item.url || '',
              lastModified: item.updateDate || new Date().toISOString(),
              metadata: JSON.stringify(item),
            });
          }
        }

        // Update pagination state
        offset += items.length;
        this.storage.updatePaginationState({
          collection: 'congress',
          endpoint: endpoint,
          offset: offset,
          completed: items.length < limit,
        });

        if (onProgress) {
          onProgress(offset, total);
        }

        hasMore = items.length === limit;
      } catch (error) {
        console.error(`Error ingesting ${endpoint} at offset ${offset}:`, error);
        throw error;
      }
    }

    console.log(`Completed ingestion of ${endpoint}`);
  }
}
