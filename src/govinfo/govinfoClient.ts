import axios, { AxiosInstance } from 'axios';
import { govinfoRateLimiter, bulkDataRateLimiter } from '../utils/rateLimiter.js';
import { StorageManager } from '../storage/storageManager.js';

/**
 * Configuration for GovInfo API client
 */
export interface GovInfoApiConfig {
  apiKey: string;
  baseUrl?: string;
  bulkDataUrl?: string;
}

/**
 * Pagination parameters for GovInfo API
 */
export interface GovInfoPaginationParams {
  offset?: number;
  pageSize?: number;
}

/**
 * Collection information
 */
export interface CollectionInfo {
  collectionCode: string;
  collectionName: string;
  packageCount?: number;
}

/**
 * Client for interacting with govinfo.gov API
 */
export class GovInfoApiClient {
  private axios: AxiosInstance;
  private bulkAxios: AxiosInstance;
  private apiKey: string;
  private storage: StorageManager;

  constructor(config: GovInfoApiConfig, storage: StorageManager) {
    this.apiKey = config.apiKey;
    this.storage = storage;

    this.axios = axios.create({
      baseURL: config.baseUrl || 'https://api.govinfo.gov',
    });

    this.bulkAxios = axios.create({
      baseURL: config.bulkDataUrl || 'https://www.govinfo.gov/bulkdata',
      headers: {
        'Accept': 'application/json',
      },
    });
  }

  /**
   * Get list of all available collections
   */
  async getCollections(): Promise<CollectionInfo[]> {
    return govinfoRateLimiter.schedule(async () => {
      try {
        const response = await this.axios.get('/collections', {
          params: { api_key: this.apiKey },
        });

        return response.data.collections || [];
      } catch (error) {
        console.error('Error fetching collections:', error);
        throw error;
      }
    });
  }

  /**
   * Query a specific collection
   */
  async queryCollection(
    collection: string,
    pagination: GovInfoPaginationParams = {}
  ): Promise<any> {
    const { offset = 0, pageSize = 100 } = pagination;

    return govinfoRateLimiter.schedule(async () => {
      try {
        const response = await this.axios.get(`/collections/${collection}`, {
          params: {
            api_key: this.apiKey,
            offset,
            pageSize: Math.min(pageSize, 1000), // Max 1000 per request
          },
        });

        return response.data;
      } catch (error) {
        console.error(`Error querying collection ${collection}:`, error);
        throw error;
      }
    });
  }

  /**
   * Query collection by last modified date
   */
  async queryCollectionByDate(
    collection: string,
    startDate: string,
    endDate?: string,
    pagination: GovInfoPaginationParams = {}
  ): Promise<any> {
    const { offset = 0, pageSize = 100 } = pagination;

    return govinfoRateLimiter.schedule(async () => {
      try {
        const params: any = {
          api_key: this.apiKey,
          offset,
          pageSize: Math.min(pageSize, 1000),
        };

        if (endDate) {
          params.lastModifiedEndDate = endDate;
        }

        const response = await this.axios.get(
          `/collections/${collection}/${startDate}`,
          { params }
        );

        return response.data;
      } catch (error) {
        console.error(`Error querying collection ${collection} by date:`, error);
        throw error;
      }
    });
  }

  /**
   * Get package summary
   */
  async getPackageSummary(packageId: string): Promise<any> {
    return govinfoRateLimiter.schedule(async () => {
      try {
        const response = await this.axios.get(`/packages/${packageId}/summary`, {
          params: { api_key: this.apiKey },
        });

        return response.data;
      } catch (error) {
        console.error(`Error fetching package summary ${packageId}:`, error);
        throw error;
      }
    });
  }

  /**
   * Get package granules
   */
  async getPackageGranules(
    packageId: string,
    pagination: GovInfoPaginationParams = {}
  ): Promise<any> {
    const { offset = 0, pageSize = 100 } = pagination;

    return govinfoRateLimiter.schedule(async () => {
      try {
        const response = await this.axios.get(`/packages/${packageId}/granules`, {
          params: {
            api_key: this.apiKey,
            offset,
            pageSize: Math.min(pageSize, 1000),
          },
        });

        return response.data;
      } catch (error) {
        console.error(`Error fetching package granules ${packageId}:`, error);
        throw error;
      }
    });
  }

  /**
   * Query by published date
   */
  async queryByPublishedDate(
    startDate: string,
    endDate?: string,
    collection?: string,
    pagination: GovInfoPaginationParams = {}
  ): Promise<any> {
    const { offset = 0, pageSize = 100 } = pagination;

    return govinfoRateLimiter.schedule(async () => {
      try {
        const params: any = {
          api_key: this.apiKey,
          offset,
          pageSize: Math.min(pageSize, 1000),
        };

        if (endDate) {
          params.dateIssuedEndDate = endDate;
        }
        if (collection) {
          params.collection = collection;
        }

        const response = await this.axios.get(`/published/${startDate}`, { params });

        return response.data;
      } catch (error) {
        console.error('Error querying by published date:', error);
        throw error;
      }
    });
  }

  /**
   * Get related documents
   */
  async getRelatedDocuments(accessId: string): Promise<any> {
    return govinfoRateLimiter.schedule(async () => {
      try {
        const response = await this.axios.get(`/related/${accessId}`, {
          params: { api_key: this.apiKey },
        });

        return response.data;
      } catch (error) {
        console.error(`Error fetching related documents for ${accessId}:`, error);
        throw error;
      }
    });
  }

  /**
   * Search across collections
   */
  async search(
    query: string,
    collection?: string,
    pagination: GovInfoPaginationParams = {}
  ): Promise<any> {
    const { offset = 0, pageSize = 100 } = pagination;

    return govinfoRateLimiter.schedule(async () => {
      try {
        const params: any = {
          api_key: this.apiKey,
          query,
          offset,
          pageSize: Math.min(pageSize, 1000),
        };

        if (collection) {
          params.collection = collection;
        }

        const response = await this.axios.get('/search', { params });

        return response.data;
      } catch (error) {
        console.error('Error performing search:', error);
        throw error;
      }
    });
  }

  /**
   * Get bulk data listing for a collection
   */
  async getBulkDataListing(path: string): Promise<any> {
    return bulkDataRateLimiter.schedule(async () => {
      try {
        const response = await this.bulkAxios.get(`/json${path}`);
        return response.data;
      } catch (error) {
        console.error(`Error fetching bulk data listing ${path}:`, error);
        throw error;
      }
    });
  }

  /**
   * Ingest collection data with automatic pagination
   */
  async ingestCollection(
    collection: string,
    onProgress?: (offset: number, total: number) => void
  ): Promise<void> {
    let offset = 0;
    const pageSize = 1000;
    let hasMore = true;

    // Check for existing pagination state
    const paginationState = this.storage.getPaginationState('govinfo', collection);
    if (paginationState && !paginationState.completed) {
      offset = paginationState.offset;
      console.log(`Resuming collection ${collection} from offset ${offset}`);
    }

    while (hasMore) {
      try {
        const data = await this.queryCollection(collection, { offset, pageSize });
        
        const packages = data.packages || [];
        const total = data.count || 0;

        console.log(`Fetched ${packages.length} packages at offset ${offset} of ${total}`);

        // Process each package
        for (const pkg of packages) {
          const packageId = pkg.packageId;
          
          if (!this.storage.isIngested(collection, packageId)) {
            this.storage.recordIngestion({
              collection: collection,
              packageId: packageId,
              url: pkg.packageLink || '',
              lastModified: pkg.lastModified || new Date().toISOString(),
              metadata: JSON.stringify(pkg),
            });
          }
        }

        // Update pagination state
        offset += packages.length;
        this.storage.updatePaginationState({
          collection: 'govinfo',
          endpoint: collection,
          offset: offset,
          completed: packages.length < pageSize,
        });

        if (onProgress) {
          onProgress(offset, total);
        }

        hasMore = packages.length === pageSize;
      } catch (error) {
        console.error(`Error ingesting collection ${collection} at offset ${offset}:`, error);
        throw error;
      }
    }

    console.log(`Completed ingestion of collection ${collection}`);
  }

  /**
   * Ingest bulk data with automatic pagination
   */
  async ingestBulkData(
    path: string,
    onProgress?: (processed: number) => void
  ): Promise<void> {
    try {
      const listing = await this.getBulkDataListing(path);
      
      if (listing.files) {
        let processed = 0;
        
        for (const file of listing.files) {
          const fileName = file.name || file.link;
          
          if (!this.storage.isIngested(`bulkdata${path}`, fileName)) {
            this.storage.recordIngestion({
              collection: `bulkdata${path}`,
              packageId: fileName,
              url: file.link || '',
              lastModified: file.lastModified || new Date().toISOString(),
              metadata: JSON.stringify(file),
            });
          }

          processed++;
          if (onProgress) {
            onProgress(processed);
          }
        }
      }

      // Recursively handle subdirectories
      if (listing.folders) {
        for (const folder of listing.folders) {
          const folderPath = `${path}/${folder.name}`;
          await this.ingestBulkData(folderPath, onProgress);
        }
      }

      console.log(`Completed bulk data ingestion for ${path}`);
    } catch (error) {
      console.error(`Error ingesting bulk data ${path}:`, error);
      throw error;
    }
  }
}
