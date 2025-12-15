import { TokenBucketRateLimiter } from '../utils/rate-limiter.js';
import { APIResponse } from '../types/index.js';

export class GovinfoAPIClient {
  private baseUrl = 'https://api.govinfo.gov';
  private apiKey: string;
  private rateLimiter: TokenBucketRateLimiter;

  constructor(apiKey: string, rateLimiter: TokenBucketRateLimiter) {
    this.apiKey = apiKey;
    this.rateLimiter = rateLimiter;
  }

  private async request<T>(endpoint: string, params: Record<string, any> = {}): Promise<APIResponse<T>> {
    await this.rateLimiter.waitIfNeeded();

    const url = new URL(`${this.baseUrl}${endpoint}`);
    url.searchParams.append('api_key', this.apiKey);

    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    }

    const response = await fetch(url.toString(), {
      headers: {
        'Accept': 'application/json'
      }
    });
    this.rateLimiter.recordRequest();

    if (!response.ok) {
      throw new Error(`GovInfo API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json() as any;
    
    // Extract pagination info if available
    const pagination = {
      offset: params.offset || 0,
      limit: params.pageSize || 100,
      total: data.count,
      hasMore: data.nextPage !== null && data.nextPage !== undefined
    };

    return {
      data: data as T,
      pagination,
      headers: {
        'x-ratelimit-limit': response.headers.get('x-ratelimit-limit') || '',
        'x-ratelimit-remaining': response.headers.get('x-ratelimit-remaining') || ''
      }
    };
  }

  async listCollections(params: {
    offset?: number;
    pageSize?: number;
  } = {}): Promise<APIResponse> {
    return this.request('/collections', {
      offset: params.offset,
      pageSize: params.pageSize || 100
    });
  }

  async getCollection(collectionCode: string): Promise<APIResponse> {
    return this.request(`/collections/${collectionCode}`);
  }

  async getPackageSummary(packageId: string): Promise<APIResponse> {
    return this.request(`/packages/${packageId}/summary`);
  }

  async getPackageGranules(packageId: string, params: {
    offset?: number;
    pageSize?: number;
  } = {}): Promise<APIResponse> {
    return this.request(`/packages/${packageId}/granules`, {
      offset: params.offset,
      pageSize: params.pageSize || 100
    });
  }

  async listPublished(params: {
    dateIssuedStartDate: string;
    dateIssuedEndDate?: string;
    collection?: string;
    offset?: number;
    pageSize?: number;
  }): Promise<APIResponse> {
    const endpoint = `/published/${params.dateIssuedStartDate}`;
    return this.request(endpoint, {
      dateIssuedEndDate: params.dateIssuedEndDate,
      collection: params.collection,
      offset: params.offset,
      pageSize: params.pageSize || 100
    });
  }

  async searchPackages(params: {
    query: string;
    pageSize?: number;
    offsetMark?: string;
    collection?: string;
  }): Promise<APIResponse> {
    return this.request('/search', {
      query: params.query,
      pageSize: params.pageSize || 100,
      offsetMark: params.offsetMark || '*',
      collection: params.collection
    });
  }

  async getRelated(accessId: string): Promise<APIResponse> {
    return this.request(`/related/${accessId}`);
  }
}

export class GovinfoBulkDataClient {
  private baseUrl = 'https://www.govinfo.gov/bulkdata';

  async listBulkDataCollections(): Promise<string[]> {
    // Common bulk data collections
    return [
      'BILLS',
      'BILLSTATUS',
      'CFR',
      'ECFR',
      'FR',
      'CHRG',
      'PLAW',
      'STATUTE',
      'USCODE'
    ];
  }

  async getBulkDataListing(params: {
    collection: string;
    congress?: number;
    session?: number;
    format?: 'xml' | 'json';
  }): Promise<Response> {
    let url = `${this.baseUrl}`;
    
    if (params.format) {
      url += `/${params.format}`;
    }
    
    url += `/${params.collection}`;
    
    if (params.congress) {
      url += `/${params.congress}`;
      if (params.session) {
        url += `/${params.session}`;
      }
    }

    const response = await fetch(url, {
      headers: {
        'Accept': params.format === 'json' ? 'application/json' : 'application/xml'
      }
    });

    if (!response.ok) {
      throw new Error(`Bulk data error: ${response.status} ${response.statusText}`);
    }

    return response;
  }

  async downloadBulkDataFile(url: string): Promise<Response> {
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Download error: ${response.status} ${response.statusText}`);
    }

    return response;
  }
}
