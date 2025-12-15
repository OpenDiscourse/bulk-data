import PQueue from 'p-queue';
import { WorkerTask } from '../types/index.js';

export class WorkerPool {
  private queue: PQueue;
  private activeTasks: Map<string, Promise<any>>;

  constructor(concurrency: number) {
    this.queue = new PQueue({ concurrency });
    this.activeTasks = new Map();
  }

  async addTask<T>(task: WorkerTask, executor: () => Promise<T>): Promise<T> {
    const taskPromise = this.queue.add(async () => {
      try {
        return await executor();
      } finally {
        this.activeTasks.delete(task.id);
      }
    }, { priority: task.priority }) as Promise<T>;

    this.activeTasks.set(task.id, taskPromise);
    return taskPromise;
  }

  async waitForAll(): Promise<void> {
    await this.queue.onIdle();
  }

  getActiveCount(): number {
    return this.activeTasks.size;
  }

  getPendingCount(): number {
    return this.queue.pending;
  }

  getQueueSize(): number {
    return this.queue.size;
  }

  async clear(): Promise<void> {
    this.queue.clear();
  }
}
