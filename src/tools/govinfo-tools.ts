import { z } from 'zod';
import { GovinfoAPIClient, GovinfoBulkDataClient } from '../utils/govinfo-client.js';
import { IngestionTracker } from '../utils/ingestion-tracker.js';
import { WorkerPool } from '../utils/worker-pool.js';

const ListCollectionsSchema = z.object({
  offset: z.number().default(0),
  pageSize: z.number().max(100).default(100)
});

const GetPackageSchema = z.object({
  packageId: z.string()
});

const ListPublishedSchema = z.object({
  dateIssuedStartDate: z.string(),
  dateIssuedEndDate: z.string().optional(),
  collection: z.string().optional(),
  offset: z.number().default(0),
  pageSize: z.number().max(100).default(100)
});

const SearchPackagesSchema = z.object({
  query: z.string(),
  pageSize: z.number().max(100).default(100),
  offsetMark: z.string().default('*'),
  collection: z.string().optional()
});

const BulkDataListingSchema = z.object({
  collection: z.string(),
  congress: z.number().optional(),
  session: z.number().optional(),
  format: z.enum(['xml', 'json']).default('json')
});

const BulkIngestCollectionSchema = z.object({
  collection: z.string(),
  startDate: z.string(),
  endDate: z.string().optional(),
  useWorkers: z.boolean().default(true)
});

export function createGovinfoTools(
  client: GovinfoAPIClient,
  bulkClient: GovinfoBulkDataClient,
  tracker: IngestionTracker,
  workerPool: WorkerPool
) {
  return {
    govinfo_list_collections: {
      description: 'List available collections from GovInfo API',
      inputSchema: {
        type: 'object',
        properties: {
          offset: {
            type: 'number',
            description: 'Pagination offset',
            default: 0
          },
          pageSize: {
            type: 'number',
            description: 'Number of results (max 100)',
            default: 100
          }
        }
      },
      handler: async (params: unknown) => {
        const validated = ListCollectionsSchema.parse(params);
        const response = await client.listCollections(validated);

        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              collections: response.data.collections,
              pagination: response.pagination,
              rateLimit: response.headers
            }, null, 2)
          }]
        };
      }
    },

    govinfo_get_package: {
      description: 'Get detailed package information from GovInfo',
      inputSchema: {
        type: 'object',
        properties: {
          packageId: {
            type: 'string',
            description: 'Package identifier'
          }
        },
        required: ['packageId']
      },
      handler: async (params: unknown) => {
        const validated = GetPackageSchema.parse(params);
        const response = await client.getPackageSummary(validated.packageId);

        return {
          content: [{
            type: 'text',
            text: JSON.stringify(response.data, null, 2)
          }]
        };
      }
    },

    govinfo_list_published: {
      description: 'List published documents by date',
      inputSchema: {
        type: 'object',
        properties: {
          dateIssuedStartDate: {
            type: 'string',
            description: 'Start date (YYYY-MM-DD)'
          },
          dateIssuedEndDate: {
            type: 'string',
            description: 'End date (YYYY-MM-DD)'
          },
          collection: {
            type: 'string',
            description: 'Filter by collection code'
          },
          offset: {
            type: 'number',
            default: 0
          },
          pageSize: {
            type: 'number',
            default: 100
          }
        },
        required: ['dateIssuedStartDate']
      },
      handler: async (params: unknown) => {
        const validated = ListPublishedSchema.parse(params);
        const response = await client.listPublished(validated);

        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              packages: response.data.packages,
              pagination: response.pagination,
              rateLimit: response.headers
            }, null, 2)
          }]
        };
      }
    },

    govinfo_search_packages: {
      description: 'Search for packages using query',
      inputSchema: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'Search query'
          },
          pageSize: {
            type: 'number',
            default: 100
          },
          offsetMark: {
            type: 'string',
            description: 'Offset marker for pagination',
            default: '*'
          },
          collection: {
            type: 'string',
            description: 'Filter by collection'
          }
        },
        required: ['query']
      },
      handler: async (params: unknown) => {
        const validated = SearchPackagesSchema.parse(params);
        const response = await client.searchPackages(validated);

        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              results: response.data.results,
              nextOffsetMark: response.data.nextOffsetMark,
              pagination: response.pagination
            }, null, 2)
          }]
        };
      }
    },

    govinfo_bulk_data_collections: {
      description: 'List available bulk data collections',
      inputSchema: {
        type: 'object',
        properties: {}
      },
      handler: async () => {
        const collections = await bulkClient.listBulkDataCollections();

        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              collections,
              description: {
                BILLS: 'Congressional Bills',
                BILLSTATUS: 'Bill Status (XML)',
                CFR: 'Code of Federal Regulations',
                ECFR: 'Electronic Code of Federal Regulations',
                FR: 'Federal Register',
                CHRG: 'Congressional Hearings',
                PLAW: 'Public Laws',
                STATUTE: 'Statutes at Large',
                USCODE: 'United States Code'
              }
            }, null, 2)
          }]
        };
      }
    },

    govinfo_bulk_data_listing: {
      description: 'Get bulk data file listing for a collection',
      inputSchema: {
        type: 'object',
        properties: {
          collection: {
            type: 'string',
            description: 'Collection code (BILLS, CFR, FR, etc.)'
          },
          congress: {
            type: 'number',
            description: 'Congress number (for BILLS)'
          },
          session: {
            type: 'number',
            description: 'Session number'
          },
          format: {
            type: 'string',
            enum: ['xml', 'json'],
            default: 'json',
            description: 'Response format'
          }
        },
        required: ['collection']
      },
      handler: async (params: unknown) => {
        const validated = BulkDataListingSchema.parse(params);
        const response = await bulkClient.getBulkDataListing(validated);
        
        const contentType = response.headers.get('content-type') || '';
        let data: any;

        if (contentType.includes('json')) {
          data = await response.json();
        } else {
          data = await response.text();
        }

        return {
          content: [{
            type: 'text',
            text: JSON.stringify({ data }, null, 2)
          }]
        };
      }
    },

    govinfo_bulk_ingest_collection: {
      description: 'Bulk ingest packages from a collection by date range',
      inputSchema: {
        type: 'object',
        properties: {
          collection: {
            type: 'string',
            description: 'Collection code'
          },
          startDate: {
            type: 'string',
            description: 'Start date (YYYY-MM-DD)'
          },
          endDate: {
            type: 'string',
            description: 'End date (YYYY-MM-DD)'
          },
          useWorkers: {
            type: 'boolean',
            description: 'Use parallel workers',
            default: true
          }
        },
        required: ['collection', 'startDate']
      },
      handler: async (params: unknown) => {
        const validated = BulkIngestCollectionSchema.parse(params);
        
        let totalIngested = 0;
        let totalSkipped = 0;
        let offset = 0;
        let hasMore = true;

        while (hasMore) {
          const response = await client.listPublished({
            dateIssuedStartDate: validated.startDate,
            dateIssuedEndDate: validated.endDate,
            collection: validated.collection,
            offset,
            pageSize: 100
          });

          if (!response.data.packages || response.data.packages.length === 0) {
            break;
          }

          if (validated.useWorkers) {
            // Process packages in parallel
            const tasks = response.data.packages.map((pkg: any) => {
              return workerPool.addTask(
                {
                  id: `package-${pkg.packageId}`,
                  endpoint: 'govinfo/packages',
                  params: { pkg },
                  priority: 1
                },
                async () => {
                  const checksum = tracker.generateChecksum(pkg);
                  const resourceId = pkg.packageId;

                  if (!await tracker.isAlreadyIngested('govinfo/packages', resourceId, checksum)) {
                    await tracker.recordIngestion({
                      endpoint: 'govinfo/packages',
                      resourceId,
                      resourceType: 'package',
                      checksum,
                      metadata: JSON.stringify({ 
                        collection: pkg.collection,
                        dateIssued: pkg.dateIssued 
                      })
                    });
                    return 'ingested';
                  }
                  return 'skipped';
                }
              );
            });

            const results = await Promise.all(tasks);
            totalIngested += results.filter(r => r === 'ingested').length;
            totalSkipped += results.filter(r => r === 'skipped').length;
          } else {
            // Process sequentially
            for (const pkg of response.data.packages) {
              const checksum = tracker.generateChecksum(pkg);
              const resourceId = pkg.packageId;

              if (!await tracker.isAlreadyIngested('govinfo/packages', resourceId, checksum)) {
                await tracker.recordIngestion({
                  endpoint: 'govinfo/packages',
                  resourceId,
                  resourceType: 'package',
                  checksum,
                  metadata: JSON.stringify({ 
                    collection: pkg.collection,
                    dateIssued: pkg.dateIssued 
                  })
                });
                totalIngested++;
              } else {
                totalSkipped++;
              }
            }
          }

          hasMore = response.pagination?.hasMore || false;
          offset += 100;
        }

        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              success: true,
              collection: validated.collection,
              dateRange: {
                start: validated.startDate,
                end: validated.endDate
              },
              totalIngested,
              totalSkipped,
              workerStats: {
                active: workerPool.getActiveCount(),
                pending: workerPool.getPendingCount(),
                queued: workerPool.getQueueSize()
              }
            }, null, 2)
          }]
        };
      }
    },

    govinfo_get_ingestion_stats: {
      description: 'Get statistics about ingested data',
      inputSchema: {
        type: 'object',
        properties: {
          endpoint: {
            type: 'string',
            description: 'Filter by endpoint (optional)'
          }
        }
      },
      handler: async (params: any) => {
        const stats = await tracker.getIngestionStats(params?.endpoint);

        return {
          content: [{
            type: 'text',
            text: JSON.stringify(stats, null, 2)
          }]
        };
      }
    }
  };
}
