/**
 * GovInfo Bulk Data API Client
 * Handles requests to api.govinfo.gov with rate limiting and pagination
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { GovInfoAPIParams, APIResponse } from '../types/index.js';
import { rateLimiter } from '../utils/rateLimiter.js';

export class GovInfoAPIClient {
  private client: AxiosInstance;
  private apiKey: string;
  private baseURL: string = 'https://api.govinfo.gov';

  constructor(apiKey?: string) {
    this.apiKey = apiKey || process.env.GOVINFO_API_KEY || '';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Accept': 'application/json',
      },
    });

    // Add request interceptor to include API key and check rate limit
    this.client.interceptors.request.use(async (config) => {
      // Check rate limit before making request
      const canProceed = await rateLimiter.checkLimit('govinfo');
      if (!canProceed) {
        const resetTime = rateLimiter.getResetTime('govinfo');
        throw new Error(`Rate limit exceeded. Resets at ${new Date(resetTime).toISOString()}`);
      }

      // Add API key to headers
      if (this.apiKey) {
        config.headers['X-Api-Key'] = this.apiKey;
      }

      return config;
    });

    // Add response interceptor to track rate limit
    this.client.interceptors.response.use((response) => {
      rateLimiter.incrementCount('govinfo');
      return response;
    });
  }

  /**
   * Get list of collections
   */
  async getCollections(): Promise<APIResponse> {
    const response = await this.client.get('/collections');
    return this.formatResponse(response);
  }

  /**
   * Get packages for a collection
   */
  async getPackages(collection: string, params: GovInfoAPIParams = {}): Promise<APIResponse> {
    const { offsetMark = '*', pageSize = 100 } = params;
    
    const response = await this.client.get(`/collections/${collection}`, {
      params: { offsetMark, pageSize },
    });

    return this.formatResponse(response, offsetMark, pageSize);
  }

  /**
   * Get a specific package
   */
  async getPackage(packageId: string): Promise<APIResponse> {
    const response = await this.client.get(`/packages/${packageId}/summary`);
    return this.formatResponse(response);
  }

  /**
   * Get package granules
   */
  async getGranules(packageId: string, params: GovInfoAPIParams = {}): Promise<APIResponse> {
    const { offsetMark = '*', pageSize = 100 } = params;
    
    const response = await this.client.get(`/packages/${packageId}/granules`, {
      params: { offsetMark, pageSize },
    });

    return this.formatResponse(response, offsetMark, pageSize);
  }

  /**
   * Search for content
   */
  async search(query: string, params: GovInfoAPIParams = {}): Promise<APIResponse> {
    const { offsetMark = '*', pageSize = 100, collection } = params;
    
    const searchParams: any = {
      query,
      offsetMark,
      pageSize,
    };

    if (collection) {
      searchParams.collection = collection;
    }

    const response = await this.client.post('/search', searchParams);
    return this.formatResponse(response, offsetMark, pageSize);
  }

  /**
   * Get published content
   */
  async getPublished(startDate: string, endDate?: string, params: GovInfoAPIParams = {}): Promise<APIResponse> {
    const { offsetMark = '*', pageSize = 100, collection } = params;
    
    const endpoint = endDate 
      ? `/published/${startDate}/${endDate}`
      : `/published/${startDate}`;

    const queryParams: any = { offsetMark, pageSize };
    if (collection) {
      queryParams.collection = collection;
    }

    const response = await this.client.get(endpoint, {
      params: queryParams,
    });

    return this.formatResponse(response, offsetMark, pageSize);
  }

  /**
   * Get bulk data from govinfo.gov/bulkdata
   */
  async getBulkData(path: string, format: 'json' | 'xml' = 'json'): Promise<APIResponse> {
    const url = `https://www.govinfo.gov/bulkdata/${format}/${path}`;
    
    const response = await axios.get(url, {
      headers: {
        'Accept': format === 'json' ? 'application/json' : 'application/xml',
      },
    });

    // Track the request in our rate limiter
    rateLimiter.incrementCount('govinfo');

    return this.formatResponse(response);
  }

  /**
   * Format API response with pagination info
   */
  private formatResponse(response: AxiosResponse, offsetMark?: string, pageSize?: number): APIResponse {
    const data = response.data;
    
    const result: APIResponse = {
      data,
    };

    // Add pagination info if applicable
    if (offsetMark !== undefined && pageSize !== undefined) {
      const nextOffsetMark = data.nextPage || data.offsetMark;
      
      result.pagination = {
        offset: 0, // GovInfo uses cursor-based pagination
        limit: pageSize,
        hasMore: !!nextOffsetMark && nextOffsetMark !== offsetMark,
      };

      // Store the next offset mark in metadata for cursor-based pagination
      if (nextOffsetMark) {
        result.data.nextOffsetMark = nextOffsetMark;
      }
    }

    // Add rate limit info
    result.rateLimitInfo = rateLimiter.getLimitInfo('govinfo');

    return result;
  }

  /**
   * Get rate limit info
   */
  getRateLimitInfo() {
    return rateLimiter.getLimitInfo('govinfo');
  }
}
