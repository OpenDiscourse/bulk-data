import PQueue from 'p-queue';
import { CongressApiClient, CongressEndpoint } from '../congress/congressClient.js';
import { GovInfoApiClient } from '../govinfo/govinfoClient.js';
import { StorageManager } from '../storage/storageManager.js';

/**
 * Worker configuration
 */
export interface WorkerConfig {
  maxWorkers: number;
  concurrency: number;
}

/**
 * Task definition for workers
 */
export interface Task {
  id: string;
  type: 'congress' | 'govinfo' | 'bulkdata';
  target: string;
  params?: any;
}

/**
 * Worker pool manager for parallel ingestion
 */
export class WorkerPool {
  private queue: PQueue;
  private storage: StorageManager;
  private congressClient?: CongressApiClient;
  private govinfoClient?: GovInfoApiClient;
  private activeTasks: Map<string, Task>;

  constructor(
    config: WorkerConfig,
    storage: StorageManager,
    congressClient?: CongressApiClient,
    govinfoClient?: GovInfoApiClient
  ) {
    this.queue = new PQueue({
      concurrency: config.concurrency,
    });

    this.storage = storage;
    this.congressClient = congressClient;
    this.govinfoClient = govinfoClient;
    this.activeTasks = new Map();
  }

  /**
   * Add a Congress API task to the queue
   */
  addCongressTask(endpoint: CongressEndpoint, params: any = {}): string {
    const taskId = `congress-${endpoint}-${Date.now()}`;
    
    const task: Task = {
      id: taskId,
      type: 'congress',
      target: endpoint,
      params,
    };

    this.activeTasks.set(taskId, task);

    this.queue.add(async () => {
      const workerId = `worker-${taskId}`;
      
      try {
        this.storage.updateWorkerProgress({
          workerId,
          collection: `congress-${endpoint}`,
          status: 'working',
          currentOffset: 0,
          itemsProcessed: 0,
          lastActivity: new Date().toISOString(),
        });

        if (!this.congressClient) {
          throw new Error('Congress client not initialized');
        }

        await this.congressClient.ingestEndpoint(
          endpoint,
          params,
          (offset, total) => {
            this.storage.updateWorkerProgress({
              workerId,
              collection: `congress-${endpoint}`,
              status: 'working',
              currentOffset: offset,
              itemsProcessed: offset,
              lastActivity: new Date().toISOString(),
            });
          }
        );

        this.storage.updateWorkerProgress({
          workerId,
          collection: `congress-${endpoint}`,
          status: 'idle',
          currentOffset: 0,
          itemsProcessed: 0,
          lastActivity: new Date().toISOString(),
        });

        this.activeTasks.delete(taskId);
      } catch (error: any) {
        console.error(`Worker ${workerId} error:`, error);
        
        this.storage.updateWorkerProgress({
          workerId,
          collection: `congress-${endpoint}`,
          status: 'error',
          currentOffset: 0,
          itemsProcessed: 0,
          lastActivity: new Date().toISOString(),
          errorMessage: error.message,
        });

        this.activeTasks.delete(taskId);
        throw error;
      }
    });

    return taskId;
  }

  /**
   * Add a GovInfo collection task to the queue
   */
  addGovInfoTask(collection: string): string {
    const taskId = `govinfo-${collection}-${Date.now()}`;
    
    const task: Task = {
      id: taskId,
      type: 'govinfo',
      target: collection,
    };

    this.activeTasks.set(taskId, task);

    this.queue.add(async () => {
      const workerId = `worker-${taskId}`;
      
      try {
        this.storage.updateWorkerProgress({
          workerId,
          collection: `govinfo-${collection}`,
          status: 'working',
          currentOffset: 0,
          itemsProcessed: 0,
          lastActivity: new Date().toISOString(),
        });

        if (!this.govinfoClient) {
          throw new Error('GovInfo client not initialized');
        }

        await this.govinfoClient.ingestCollection(
          collection,
          (offset, total) => {
            this.storage.updateWorkerProgress({
              workerId,
              collection: `govinfo-${collection}`,
              status: 'working',
              currentOffset: offset,
              itemsProcessed: offset,
              lastActivity: new Date().toISOString(),
            });
          }
        );

        this.storage.updateWorkerProgress({
          workerId,
          collection: `govinfo-${collection}`,
          status: 'idle',
          currentOffset: 0,
          itemsProcessed: 0,
          lastActivity: new Date().toISOString(),
        });

        this.activeTasks.delete(taskId);
      } catch (error: any) {
        console.error(`Worker ${workerId} error:`, error);
        
        this.storage.updateWorkerProgress({
          workerId,
          collection: `govinfo-${collection}`,
          status: 'error',
          currentOffset: 0,
          itemsProcessed: 0,
          lastActivity: new Date().toISOString(),
          errorMessage: error.message,
        });

        this.activeTasks.delete(taskId);
        throw error;
      }
    });

    return taskId;
  }

  /**
   * Add a bulk data task to the queue
   */
  addBulkDataTask(path: string): string {
    const taskId = `bulkdata-${path.replace(/\//g, '-')}-${Date.now()}`;
    
    const task: Task = {
      id: taskId,
      type: 'bulkdata',
      target: path,
    };

    this.activeTasks.set(taskId, task);

    this.queue.add(async () => {
      const workerId = `worker-${taskId}`;
      
      try {
        this.storage.updateWorkerProgress({
          workerId,
          collection: `bulkdata-${path}`,
          status: 'working',
          currentOffset: 0,
          itemsProcessed: 0,
          lastActivity: new Date().toISOString(),
        });

        if (!this.govinfoClient) {
          throw new Error('GovInfo client not initialized');
        }

        await this.govinfoClient.ingestBulkData(
          path,
          (processed) => {
            this.storage.updateWorkerProgress({
              workerId,
              collection: `bulkdata-${path}`,
              status: 'working',
              currentOffset: processed,
              itemsProcessed: processed,
              lastActivity: new Date().toISOString(),
            });
          }
        );

        this.storage.updateWorkerProgress({
          workerId,
          collection: `bulkdata-${path}`,
          status: 'idle',
          currentOffset: 0,
          itemsProcessed: 0,
          lastActivity: new Date().toISOString(),
        });

        this.activeTasks.delete(taskId);
      } catch (error: any) {
        console.error(`Worker ${workerId} error:`, error);
        
        this.storage.updateWorkerProgress({
          workerId,
          collection: `bulkdata-${path}`,
          status: 'error',
          currentOffset: 0,
          itemsProcessed: 0,
          lastActivity: new Date().toISOString(),
          errorMessage: error.message,
        });

        this.activeTasks.delete(taskId);
        throw error;
      }
    });

    return taskId;
  }

  /**
   * Wait for all tasks to complete
   */
  async waitForCompletion(): Promise<void> {
    await this.queue.onIdle();
  }

  /**
   * Get current queue status
   */
  getStatus(): {
    pending: number;
    active: number;
    completed: number;
  } {
    return {
      pending: this.queue.pending,
      active: this.activeTasks.size,
      completed: 0, // Could track this separately if needed
    };
  }

  /**
   * Pause the queue
   */
  pause(): void {
    this.queue.pause();
  }

  /**
   * Resume the queue
   */
  resume(): void {
    this.queue.start();
  }

  /**
   * Clear all pending tasks
   */
  clear(): void {
    this.queue.clear();
  }
}
