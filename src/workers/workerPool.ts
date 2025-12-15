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
  private completedTasks: number;

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
    this.completedTasks = 0;
  }

  /**
   * Private helper to add a task with common lifecycle/error/progress logic
   */
  private addTaskWithLifecycle(
    task: Task,
    collection: string,
    operation: (workerId: string, progressCallback: (processed: number) => void) => Promise<void>
  ): void {
    this.activeTasks.set(task.id, task);
    
    this.queue.add(async () => {
      const workerId = `worker-${task.id}`;
      
      try {
        this.storage.updateWorkerProgress({
          workerId,
          collection,
          status: 'working',
          currentOffset: 0,
          itemsProcessed: 0,
          lastActivity: new Date().toISOString(),
        });

        await operation(workerId, (processed: number) => {
          this.storage.updateWorkerProgress({
            workerId,
            collection,
            status: 'working',
            currentOffset: processed,
            itemsProcessed: processed,
            lastActivity: new Date().toISOString(),
          });
        });

        this.storage.updateWorkerProgress({
          workerId,
          collection,
          status: 'idle',
          currentOffset: 0,
          itemsProcessed: 0,
          lastActivity: new Date().toISOString(),
        });

        this.activeTasks.delete(task.id);
        this.completedTasks++;
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error(`Worker ${workerId} error:`, error);
        
        this.storage.updateWorkerProgress({
          workerId,
          collection,
          status: 'error',
          currentOffset: 0,
          itemsProcessed: 0,
          lastActivity: new Date().toISOString(),
          errorMessage,
        });

        this.activeTasks.delete(task.id);
        // Do not increment completedTasks for failed tasks to maintain consistency
        // The error is logged but not re-thrown to prevent queue interruption
      }
    });
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

    this.addTaskWithLifecycle(
      task,
      `congress-${endpoint}`,
      async (workerId: string, progressCallback: (processed: number) => void) => {
        if (!this.congressClient) {
          throw new Error('Congress client not initialized');
        }
        await this.congressClient.ingestEndpoint(endpoint, params, progressCallback);
      }
    );

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

    this.addTaskWithLifecycle(
      task,
      `govinfo-${collection}`,
      async (workerId: string, progressCallback: (processed: number) => void) => {
        if (!this.govinfoClient) {
          throw new Error('GovInfo client not initialized');
        }
        await this.govinfoClient.ingestCollection(collection, progressCallback);
      }
    );

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

    this.addTaskWithLifecycle(
      task,
      `bulkdata-${path}`,
      async (workerId: string, progressCallback: (processed: number) => void) => {
        if (!this.govinfoClient) {
          throw new Error('GovInfo client not initialized');
        }
        await this.govinfoClient.ingestBulkData(path, progressCallback);
      }
    );

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
      completed: this.completedTasks,
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
