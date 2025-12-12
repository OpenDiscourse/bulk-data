import { z } from 'zod';
import { CongressAPIClient } from '../utils/congress-client.js';
import { IngestionTracker } from '../utils/ingestion-tracker.js';
import { WorkerPool } from '../utils/worker-pool.js';

const ListBillsSchema = z.object({
  congress: z.number().optional(),
  billType: z.string().optional(),
  offset: z.number().default(0),
  limit: z.number().max(250).default(250),
  ingest: z.boolean().default(false)
});

const GetBillSchema = z.object({
  congress: z.number(),
  billType: z.string(),
  billNumber: z.number()
});

const BulkIngestBillsSchema = z.object({
  congress: z.number(),
  billType: z.string().optional(),
  useWorkers: z.boolean().default(true)
});

export function createCongressTools(
  client: CongressAPIClient,
  tracker: IngestionTracker,
  workerPool: WorkerPool
) {
  return {
    congress_list_bills: {
      description: 'List bills from Congress.gov API with pagination support',
      inputSchema: {
        type: 'object',
        properties: {
          congress: {
            type: 'number',
            description: 'Congress number (e.g., 118 for current congress)'
          },
          billType: {
            type: 'string',
            description: 'Bill type (hr, s, hjres, sjres, hconres, sconres, hres, sres)'
          },
          offset: {
            type: 'number',
            description: 'Pagination offset',
            default: 0
          },
          limit: {
            type: 'number',
            description: 'Number of results (max 250)',
            default: 250
          },
          ingest: {
            type: 'boolean',
            description: 'Whether to track ingestion',
            default: false
          }
        }
      },
      handler: async (params: unknown) => {
        const validated = ListBillsSchema.parse(params);
        const response = await client.listBills(validated);

        if (validated.ingest && response.data.bills) {
          for (const bill of response.data.bills) {
            const checksum = tracker.generateChecksum(bill);
            const resourceId = `${bill.congress}-${bill.type}-${bill.number}`;

            if (!await tracker.isAlreadyIngested('congress/bills', resourceId, checksum)) {
              await tracker.recordIngestion({
                endpoint: 'congress/bills',
                resourceId,
                resourceType: 'bill',
                checksum,
                metadata: JSON.stringify({ congress: bill.congress, type: bill.type })
              });
            }
          }
        }

        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              bills: response.data.bills,
              pagination: response.pagination,
              rateLimit: response.headers
            }, null, 2)
          }]
        };
      }
    },

    congress_get_bill: {
      description: 'Get detailed information about a specific bill',
      inputSchema: {
        type: 'object',
        properties: {
          congress: {
            type: 'number',
            description: 'Congress number'
          },
          billType: {
            type: 'string',
            description: 'Bill type'
          },
          billNumber: {
            type: 'number',
            description: 'Bill number'
          }
        },
        required: ['congress', 'billType', 'billNumber']
      },
      handler: async (params: unknown) => {
        const validated = GetBillSchema.parse(params);
        const response = await client.getBill(
          validated.congress,
          validated.billType,
          validated.billNumber
        );

        return {
          content: [{
            type: 'text',
            text: JSON.stringify(response.data, null, 2)
          }]
        };
      }
    },

    congress_bulk_ingest_bills: {
      description: 'Bulk ingest all bills for a congress with parallel workers',
      inputSchema: {
        type: 'object',
        properties: {
          congress: {
            type: 'number',
            description: 'Congress number to ingest'
          },
          billType: {
            type: 'string',
            description: 'Specific bill type to ingest (optional)'
          },
          useWorkers: {
            type: 'boolean',
            description: 'Use parallel workers',
            default: true
          }
        },
        required: ['congress']
      },
      handler: async (params: unknown) => {
        const validated = BulkIngestBillsSchema.parse(params);
        const billTypes = validated.billType 
          ? [validated.billType]
          : ['hr', 's', 'hjres', 'sjres', 'hconres', 'sconres', 'hres', 'sres'];

        let totalIngested = 0;
        let totalSkipped = 0;

        for (const billType of billTypes) {
          let offset = 0;
          let hasMore = true;

          while (hasMore) {
            const response = await client.listBills({
              congress: validated.congress,
              billType,
              offset,
              limit: 250
            });

            if (!response.data.bills || response.data.bills.length === 0) {
              break;
            }

            if (validated.useWorkers) {
              // Process bills in parallel using worker pool
              const tasks = response.data.bills.map((bill: any, index: number) => {
                return workerPool.addTask(
                  {
                    id: `bill-${bill.congress}-${bill.type}-${bill.number}`,
                    endpoint: 'congress/bills',
                    params: { bill },
                    priority: 1
                  },
                  async () => {
                    const checksum = tracker.generateChecksum(bill);
                    const resourceId = `${bill.congress}-${bill.type}-${bill.number}`;

                    if (!await tracker.isAlreadyIngested('congress/bills', resourceId, checksum)) {
                      await tracker.recordIngestion({
                        endpoint: 'congress/bills',
                        resourceId,
                        resourceType: 'bill',
                        checksum,
                        metadata: JSON.stringify({ congress: bill.congress, type: bill.type })
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
              for (const bill of response.data.bills) {
                const checksum = tracker.generateChecksum(bill);
                const resourceId = `${bill.congress}-${bill.type}-${bill.number}`;

                if (!await tracker.isAlreadyIngested('congress/bills', resourceId, checksum)) {
                  await tracker.recordIngestion({
                    endpoint: 'congress/bills',
                    resourceId,
                    resourceType: 'bill',
                    checksum,
                    metadata: JSON.stringify({ congress: bill.congress, type: bill.type })
                  });
                  totalIngested++;
                } else {
                  totalSkipped++;
                }
              }
            }

            hasMore = response.pagination?.hasMore || false;
            offset += 250;
          }
        }

        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              success: true,
              congress: validated.congress,
              billTypes,
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

    congress_list_amendments: {
      description: 'List amendments from Congress.gov API',
      inputSchema: {
        type: 'object',
        properties: {
          congress: {
            type: 'number',
            description: 'Congress number'
          },
          amendmentType: {
            type: 'string',
            description: 'Amendment type (hamdt, samdt)'
          },
          offset: {
            type: 'number',
            default: 0
          },
          limit: {
            type: 'number',
            default: 250
          }
        }
      },
      handler: async (params: any) => {
        const response = await client.listAmendments(params);
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              amendments: response.data.amendments,
              pagination: response.pagination
            }, null, 2)
          }]
        };
      }
    },

    congress_list_laws: {
      description: 'List laws from Congress.gov API',
      inputSchema: {
        type: 'object',
        properties: {
          congress: {
            type: 'number',
            description: 'Congress number'
          },
          lawType: {
            type: 'string',
            description: 'Law type (pub, priv)'
          },
          offset: {
            type: 'number',
            default: 0
          },
          limit: {
            type: 'number',
            default: 250
          }
        }
      },
      handler: async (params: any) => {
        const response = await client.listLaws(params);
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              laws: response.data.laws,
              pagination: response.pagination
            }, null, 2)
          }]
        };
      }
    },

    congress_list_committees: {
      description: 'List congressional committees',
      inputSchema: {
        type: 'object',
        properties: {
          chamber: {
            type: 'string',
            enum: ['house', 'senate'],
            description: 'Chamber (house or senate)'
          },
          offset: {
            type: 'number',
            default: 0
          },
          limit: {
            type: 'number',
            default: 250
          }
        }
      },
      handler: async (params: any) => {
        const response = await client.listCommittees(params);
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              committees: response.data.committees,
              pagination: response.pagination
            }, null, 2)
          }]
        };
      }
    },

    congress_list_members: {
      description: 'List members of Congress',
      inputSchema: {
        type: 'object',
        properties: {
          congress: {
            type: 'number',
            description: 'Congress number'
          },
          offset: {
            type: 'number',
            default: 0
          },
          limit: {
            type: 'number',
            default: 250
          }
        }
      },
      handler: async (params: any) => {
        const response = await client.listMembers(params);
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              members: response.data.members,
              pagination: response.pagination
            }, null, 2)
          }]
        };
      }
    }
  };
}
