import { TokenBucketRateLimiter } from '../utils/rate-limiter.js';
import { APIResponse } from '../types/index.js';

export class CongressAPIClient {
  private baseUrl = 'https://api.congress.gov/v3';
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
    url.searchParams.append('format', 'json');

    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    }

    const response = await fetch(url.toString());
    this.rateLimiter.recordRequest();

    if (!response.ok) {
      throw new Error(`Congress API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json() as any;
    
    // Extract pagination info from response
    const pagination = {
      offset: params.offset || 0,
      limit: params.limit || 20,
      total: data.pagination?.count,
      hasMore: data.pagination?.next !== null && data.pagination?.next !== undefined
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

  async listBills(params: {
    congress?: number;
    billType?: string;
    offset?: number;
    limit?: number;
  } = {}): Promise<APIResponse> {
    let endpoint = '/bill';
    if (params.congress) {
      endpoint += `/${params.congress}`;
      if (params.billType) {
        endpoint += `/${params.billType}`;
      }
    }

    return this.request(endpoint, {
      offset: params.offset,
      limit: params.limit || 250 // Max allowed by API
    });
  }

  async getBill(congress: number, billType: string, billNumber: number): Promise<APIResponse> {
    return this.request(`/bill/${congress}/${billType}/${billNumber}`);
  }

  async listAmendments(params: {
    congress?: number;
    amendmentType?: string;
    offset?: number;
    limit?: number;
  } = {}): Promise<APIResponse> {
    let endpoint = '/amendment';
    if (params.congress) {
      endpoint += `/${params.congress}`;
      if (params.amendmentType) {
        endpoint += `/${params.amendmentType}`;
      }
    }

    return this.request(endpoint, {
      offset: params.offset,
      limit: params.limit || 250
    });
  }

  async listLaws(params: {
    congress?: number;
    lawType?: string;
    offset?: number;
    limit?: number;
  } = {}): Promise<APIResponse> {
    let endpoint = '/law';
    if (params.congress) {
      endpoint += `/${params.congress}`;
      if (params.lawType) {
        endpoint += `/${params.lawType}`;
      }
    }

    return this.request(endpoint, {
      offset: params.offset,
      limit: params.limit || 250
    });
  }

  async listCommittees(params: {
    chamber?: 'house' | 'senate';
    offset?: number;
    limit?: number;
  } = {}): Promise<APIResponse> {
    let endpoint = '/committee';
    if (params.chamber) {
      endpoint += `/${params.chamber}`;
    }

    return this.request(endpoint, {
      offset: params.offset,
      limit: params.limit || 250
    });
  }

  async listMembers(params: {
    congress?: number;
    offset?: number;
    limit?: number;
  } = {}): Promise<APIResponse> {
    let endpoint = '/member';
    if (params.congress) {
      endpoint += `/congress/${params.congress}`;
    }

    return this.request(endpoint, {
      offset: params.offset,
      limit: params.limit || 250
    });
  }

  async listNominations(params: {
    congress?: number;
    offset?: number;
    limit?: number;
  } = {}): Promise<APIResponse> {
    let endpoint = '/nomination';
    if (params.congress) {
      endpoint += `/${params.congress}`;
    }

    return this.request(endpoint, {
      offset: params.offset,
      limit: params.limit || 250
    });
  }

  async listTreaties(params: {
    congress?: number;
    offset?: number;
    limit?: number;
  } = {}): Promise<APIResponse> {
    let endpoint = '/treaty';
    if (params.congress) {
      endpoint += `/${params.congress}`;
    }

    return this.request(endpoint, {
      offset: params.offset,
      limit: params.limit || 250
    });
  }
}
