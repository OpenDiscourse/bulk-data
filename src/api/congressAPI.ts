/**
 * Congress.gov API Client
 * Handles requests to api.congress.gov with rate limiting and pagination
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { CongressAPIParams, APIResponse, PaginationState } from '../types/index.js';
import { rateLimiter } from '../utils/rateLimiter.js';

export class CongressAPIClient {
  private client: AxiosInstance;
  private apiKey: string;
  private baseURL: string = 'https://api.congress.gov/v3';

  constructor(apiKey?: string) {
    this.apiKey = apiKey || process.env.CONGRESS_API_KEY || '';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Accept': 'application/json',
      },
    });

    // Add request interceptor to include API key
    this.client.interceptors.request.use(async (config) => {
      // Check rate limit before making request
      const canProceed = await rateLimiter.checkLimit('congress');
      if (!canProceed) {
        const resetTime = rateLimiter.getResetTime('congress');
        throw new Error(`Rate limit exceeded. Resets at ${new Date(resetTime).toISOString()}`);
      }

      // Add API key to params
      if (this.apiKey) {
        config.params = { ...config.params, api_key: this.apiKey };
      }

      return config;
    });

    // Add response interceptor to track rate limit
    this.client.interceptors.response.use((response) => {
      rateLimiter.incrementCount('congress');
      
      // Log rate limit headers if available
      const remaining = response.headers['x-ratelimit-remaining'];
      const limit = response.headers['x-ratelimit-limit'];
      if (remaining !== undefined) {
        console.log(`Congress API - Remaining: ${remaining}/${limit}`);
      }

      return response;
    });
  }

  /**
   * Get list of bills
   */
  async getBills(params: CongressAPIParams = {}): Promise<APIResponse> {
    const { offset = 0, limit = 20, format = 'json' } = params;
    
    const response = await this.client.get('/bill', {
      params: { offset, limit, format },
    });

    return this.formatResponse(response, offset, limit);
  }

  /**
   * Get a specific bill
   */
  async getBill(congress: number, billType: string, billNumber: string): Promise<APIResponse> {
    const response = await this.client.get(`/bill/${congress}/${billType}/${billNumber}`);
    return this.formatResponse(response);
  }

  /**
   * Get list of amendments
   */
  async getAmendments(params: CongressAPIParams = {}): Promise<APIResponse> {
    const { offset = 0, limit = 20, format = 'json' } = params;
    
    const response = await this.client.get('/amendment', {
      params: { offset, limit, format },
    });

    return this.formatResponse(response, offset, limit);
  }

  /**
   * Get list of members
   */
  async getMembers(params: CongressAPIParams = {}): Promise<APIResponse> {
    const { offset = 0, limit = 20, format = 'json' } = params;
    
    const response = await this.client.get('/member', {
      params: { offset, limit, format },
    });

    return this.formatResponse(response, offset, limit);
  }

  /**
   * Get list of committees
   */
  async getCommittees(params: CongressAPIParams = {}): Promise<APIResponse> {
    const { offset = 0, limit = 20, format = 'json', congress } = params;
    
    const endpoint = congress ? `/committee/${congress}` : '/committee';
    const response = await this.client.get(endpoint, {
      params: { offset, limit, format },
    });

    return this.formatResponse(response, offset, limit);
  }

  /**
   * Get nominations
   */
  async getNominations(params: CongressAPIParams = {}): Promise<APIResponse> {
    const { offset = 0, limit = 20, format = 'json', congress } = params;
    
    const endpoint = congress ? `/nomination/${congress}` : '/nomination';
    const response = await this.client.get(endpoint, {
      params: { offset, limit, format },
    });

    return this.formatResponse(response, offset, limit);
  }

  /**
   * Get treaties
   */
  async getTreaties(params: CongressAPIParams = {}): Promise<APIResponse> {
    const { offset = 0, limit = 20, format = 'json', congress } = params;
    
    const endpoint = congress ? `/treaty/${congress}` : '/treaty';
    const response = await this.client.get(endpoint, {
      params: { offset, limit, format },
    });

    return this.formatResponse(response, offset, limit);
  }

  /**
   * Format API response with pagination info
   */
  private formatResponse(response: AxiosResponse, offset?: number, limit?: number): APIResponse {
    const data = response.data;
    
    const result: APIResponse = {
      data,
    };

    // Add pagination info if applicable
    if (offset !== undefined && limit !== undefined) {
      const pagination = data.pagination || {};
      const count = pagination.count || 0;
      
      result.pagination = {
        offset,
        limit,
        total: count,
        hasMore: offset + limit < count,
      };
    }

    // Add rate limit info
    result.rateLimitInfo = rateLimiter.getLimitInfo('congress');

    return result;
  }

  /**
   * Get rate limit info
   */
  getRateLimitInfo() {
    return rateLimiter.getLimitInfo('congress');
  }
}
