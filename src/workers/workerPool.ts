/**
 * Worker Pool Manager
 * Manages parallel workers for data ingestion
 */

import { WorkerTask } from '../types/index.js';
import { CongressAPIClient } from '../api/congressAPI.js';
import { GovInfoAPIClient } from '../api/govinfoAPI.js';
import { ingestionTracker } from '../utils/ingestionTracker.js';

export class WorkerPool {
  private maxWorkers: number;
  private activeWorkers: number = 0;
  private taskQueue: WorkerTask[] = [];
  private congressClient: CongressAPIClient;
  private govinfoClient: GovInfoAPIClient;
  private isRunning: boolean = false;

  constructor(maxWorkers: number = 5) {
    this.maxWorkers = maxWorkers;
    this.congressClient = new CongressAPIClient();
    this.govinfoClient = new GovInfoAPIClient();
  }

  /**
   * Add task to the queue
   */
  addTask(task: WorkerTask): void {
    this.taskQueue.push(task);
    // Sort by priority (higher priority first)
    this.taskQueue.sort((a, b) => b.priority - a.priority);
  }

  /**
   * Add multiple tasks to the queue
   */
  addTasks(tasks: WorkerTask[]): void {
    tasks.forEach(task => this.addTask(task));
  }

  /**
   * Start processing tasks
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      console.log('Worker pool is already running');
      return;
    }

    this.isRunning = true;
    console.log(`Starting worker pool with ${this.maxWorkers} workers`);
    
    await this.processQueue();
  }

  /**
   * Stop processing tasks
   */
  stop(): void {
    this.isRunning = false;
    console.log('Stopping worker pool');
  }

  /**
   * Process the task queue
   */
  private async processQueue(): Promise<void> {
    while (this.isRunning && (this.taskQueue.length > 0 || this.activeWorkers > 0)) {
      // Start new workers if we have capacity and tasks
      while (this.activeWorkers < this.maxWorkers && this.taskQueue.length > 0) {
        const task = this.taskQueue.shift();
        if (task) {
          this.activeWorkers++;
          this.processTask(task).finally(() => {
            this.activeWorkers--;
          });
        }
      }

      // Wait a bit before checking again
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    console.log('Worker pool finished processing all tasks');
    this.isRunning = false;
  }

  /**
   * Process a single task
   */
  private async processTask(task: WorkerTask): Promise<void> {
    console.log(`Processing task ${task.id}: ${task.type}/${task.endpoint}`);

    // Check if already ingested
    if (ingestionTracker.hasBeenIngested(task.id)) {
      console.log(`Task ${task.id} already completed, skipping`);
      return;
    }

    // Mark as started
    ingestionTracker.markAsStarted(task.id, task.endpoint, task.params);

    try {
      let result;

      // Execute the appropriate API call based on task type
      if (task.type === 'congress') {
        result = await this.executeCongressTask(task);
      } else if (task.type === 'govinfo') {
        result = await this.executeGovInfoTask(task);
      } else {
        throw new Error(`Unknown task type: ${task.type}`);
      }

      // Mark as completed
      ingestionTracker.markAsCompleted(task.id);
      
      // Save progress periodically
      await ingestionTracker.saveRecords();

      console.log(`Task ${task.id} completed successfully`);
      return result;
    } catch (error) {
      console.error(`Task ${task.id} failed:`, error);
      ingestionTracker.markAsFailed(task.id);
      await ingestionTracker.saveRecords();
      throw error;
    }
  }

  /**
   * Execute a Congress API task
   */
  private async executeCongressTask(task: WorkerTask): Promise<any> {
    const { endpoint, params } = task;

    switch (endpoint) {
      case 'bills':
        return await this.congressClient.getBills(params);
      case 'bill':
        return await this.congressClient.getBill(
          params.congress,
          params.billType,
          params.billNumber
        );
      case 'amendments':
        return await this.congressClient.getAmendments(params);
      case 'members':
        return await this.congressClient.getMembers(params);
      case 'committees':
        return await this.congressClient.getCommittees(params);
      case 'nominations':
        return await this.congressClient.getNominations(params);
      case 'treaties':
        return await this.congressClient.getTreaties(params);
      default:
        throw new Error(`Unknown Congress endpoint: ${endpoint}`);
    }
  }

  /**
   * Execute a GovInfo API task
   */
  private async executeGovInfoTask(task: WorkerTask): Promise<any> {
    const { endpoint, params } = task;

    switch (endpoint) {
      case 'collections':
        return await this.govinfoClient.getCollections();
      case 'packages':
        return await this.govinfoClient.getPackages(params.collection, params);
      case 'package':
        return await this.govinfoClient.getPackage(params.packageId);
      case 'granules':
        return await this.govinfoClient.getGranules(params.packageId, params);
      case 'search':
        return await this.govinfoClient.search(params.query, params);
      case 'published':
        return await this.govinfoClient.getPublished(params.startDate, params.endDate, params);
      case 'bulkdata':
        return await this.govinfoClient.getBulkData(params.path, params.format);
      default:
        throw new Error(`Unknown GovInfo endpoint: ${endpoint}`);
    }
  }

  /**
   * Get current status
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      activeWorkers: this.activeWorkers,
      queuedTasks: this.taskQueue.length,
      maxWorkers: this.maxWorkers,
    };
  }

  /**
   * Clear the task queue
   */
  clearQueue(): void {
    this.taskQueue = [];
  }
}
