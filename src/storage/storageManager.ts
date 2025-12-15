import Database from 'better-sqlite3';
import { dirname } from 'path';
import { existsSync, mkdirSync } from 'fs';

/**
 * Interface for tracking ingested data
 */
export interface IngestedRecord {
  id: string;
  collection: string;
  packageId: string;
  url: string;
  lastModified: string;
  ingestedAt: string;
  checksum?: string;
  metadata?: string;
}

/**
 * Interface for tracking pagination state
 */
export interface PaginationState {
  collection: string;
  endpoint: string;
  offset: number;
  lastUpdated: string;
  completed: boolean;
}

/**
 * Interface for tracking worker progress
 */
export interface WorkerProgress {
  workerId: string;
  collection: string;
  status: 'idle' | 'working' | 'paused' | 'error';
  currentOffset: number;
  itemsProcessed: number;
  lastActivity: string;
  errorMessage?: string;
}

/**
 * Storage manager for tracking ingestion state
 */
export class StorageManager {
  private db: Database.Database;

  constructor(dbPath: string = './data/ingestion.db') {
    // Ensure directory exists
    const dir = dirname(dbPath);
    if (dir && dir !== '.' && dir !== '' && !existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }

    this.db = new Database(dbPath);
    this.initializeTables();
  }

  /**
   * Initialize database tables
   */
  private initializeTables(): void {
    // Table for ingested records
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS ingested_records (
        id TEXT PRIMARY KEY,
        collection TEXT NOT NULL,
        packageId TEXT NOT NULL,
        url TEXT NOT NULL,
        lastModified TEXT NOT NULL,
        ingestedAt TEXT NOT NULL,
        checksum TEXT,
        metadata TEXT,
        UNIQUE(collection, packageId)
      )
    `);

    // Index for faster lookups
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_collection_packageId 
      ON ingested_records(collection, packageId)
    `);

    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_lastModified 
      ON ingested_records(lastModified)
    `);

    // Table for pagination state
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS pagination_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        collection TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        offset INTEGER NOT NULL DEFAULT 0,
        lastUpdated TEXT NOT NULL,
        completed BOOLEAN NOT NULL DEFAULT 0,
        UNIQUE(collection, endpoint)
      )
    `);

    // Table for worker progress
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS worker_progress (
        workerId TEXT PRIMARY KEY,
        collection TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'idle',
        currentOffset INTEGER NOT NULL DEFAULT 0,
        itemsProcessed INTEGER NOT NULL DEFAULT 0,
        lastActivity TEXT NOT NULL,
        errorMessage TEXT
      )
    `);
  }

  /**
   * Check if a record has been ingested
   */
  isIngested(collection: string, packageId: string): boolean {
    const stmt = this.db.prepare(
      'SELECT id FROM ingested_records WHERE collection = ? AND packageId = ?'
    );
    const result = stmt.get(collection, packageId);
    return result !== undefined;
  }

  /**
   * Record an ingested item
   */
  recordIngestion(record: Omit<IngestedRecord, 'id' | 'ingestedAt'>): void {
    const id = `${record.collection}:${record.packageId}`;
    const ingestedAt = new Date().toISOString();

    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO ingested_records 
      (id, collection, packageId, url, lastModified, ingestedAt, checksum, metadata)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      id,
      record.collection,
      record.packageId,
      record.url,
      record.lastModified,
      ingestedAt,
      record.checksum || null,
      record.metadata || null
    );
  }

  /**
   * Get pagination state for a collection/endpoint
   */
  getPaginationState(collection: string, endpoint: string): PaginationState | null {
    const stmt = this.db.prepare(
      'SELECT * FROM pagination_state WHERE collection = ? AND endpoint = ?'
    );
    return stmt.get(collection, endpoint) as PaginationState | null;
  }

  /**
   * Update pagination state
   */
  updatePaginationState(state: Omit<PaginationState, 'lastUpdated'>): void {
    const lastUpdated = new Date().toISOString();

    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO pagination_state 
      (collection, endpoint, offset, lastUpdated, completed)
      VALUES (?, ?, ?, ?, ?)
    `);

    stmt.run(
      state.collection,
      state.endpoint,
      state.offset,
      lastUpdated,
      state.completed ? 1 : 0
    );
  }

  /**
   * Get worker progress
   */
  getWorkerProgress(workerId: string): WorkerProgress | null {
    const stmt = this.db.prepare('SELECT * FROM worker_progress WHERE workerId = ?');
    return stmt.get(workerId) as WorkerProgress | null;
  }

  /**
   * Update worker progress
   */
  updateWorkerProgress(progress: WorkerProgress): void {
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO worker_progress 
      (workerId, collection, status, currentOffset, itemsProcessed, lastActivity, errorMessage)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      progress.workerId,
      progress.collection,
      progress.status,
      progress.currentOffset,
      progress.itemsProcessed,
      progress.lastActivity,
      progress.errorMessage || null
    );
  }

  /**
   * Get all active workers
   */
  getActiveWorkers(): WorkerProgress[] {
    const stmt = this.db.prepare(
      "SELECT * FROM worker_progress WHERE status IN ('working', 'paused')"
    );
    return stmt.all() as WorkerProgress[];
  }

  /**
   * Get ingestion statistics
   */
  getIngestionStats(collection?: string): any {
    let query = `
      SELECT 
        collection,
        COUNT(*) as total,
        MIN(ingestedAt) as firstIngestion,
        MAX(ingestedAt) as lastIngestion
      FROM ingested_records
    `;

    if (collection) {
      query += ' WHERE collection = ?';
    }

    query += ' GROUP BY collection';

    const stmt = this.db.prepare(query);
    return collection ? stmt.all(collection) : stmt.all();
  }

  /**
   * Close database connection
   */
  close(): void {
    this.db.close();
  }
}
