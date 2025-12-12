import Database from 'better-sqlite3';
import { createHash } from 'crypto';
import { IngestionRecord } from '../types/index.js';

export class IngestionTracker {
  private db: Database.Database;

  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.initializeDatabase();
  }

  private initializeDatabase(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS ingestion_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        endpoint TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        ingested_at TEXT NOT NULL,
        checksum TEXT NOT NULL,
        metadata TEXT,
        UNIQUE(endpoint, resource_id)
      );

      CREATE INDEX IF NOT EXISTS idx_endpoint ON ingestion_records(endpoint);
      CREATE INDEX IF NOT EXISTS idx_resource_id ON ingestion_records(resource_id);
      CREATE INDEX IF NOT EXISTS idx_checksum ON ingestion_records(checksum);
      CREATE INDEX IF NOT EXISTS idx_ingested_at ON ingestion_records(ingested_at);
    `);
  }

  generateChecksum(data: any): string {
    const jsonString = JSON.stringify(data);
    return createHash('sha256').update(jsonString).digest('hex');
  }

  async recordIngestion(record: Omit<IngestionRecord, 'id' | 'ingestedAt'>): Promise<void> {
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO ingestion_records 
      (endpoint, resource_id, resource_type, ingested_at, checksum, metadata)
      VALUES (?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      record.endpoint,
      record.resourceId,
      record.resourceType,
      new Date().toISOString(),
      record.checksum,
      record.metadata || null
    );
  }

  async isAlreadyIngested(endpoint: string, resourceId: string, checksum: string): Promise<boolean> {
    const stmt = this.db.prepare(`
      SELECT 1 FROM ingestion_records 
      WHERE endpoint = ? AND resource_id = ? AND checksum = ?
      LIMIT 1
    `);

    const result = stmt.get(endpoint, resourceId, checksum);
    return result !== undefined;
  }

  async getIngestionStats(endpoint?: string): Promise<{
    total: number;
    byType: Record<string, number>;
    lastIngestion?: string;
  }> {
    let query = 'SELECT COUNT(*) as total FROM ingestion_records';
    let params: any[] = [];

    if (endpoint) {
      query += ' WHERE endpoint = ?';
      params.push(endpoint);
    }

    const totalResult = this.db.prepare(query).get(...params) as { total: number };

    let typeQuery = 'SELECT resource_type, COUNT(*) as count FROM ingestion_records';
    if (endpoint) {
      typeQuery += ' WHERE endpoint = ?';
    }
    typeQuery += ' GROUP BY resource_type';

    const typeResults = this.db.prepare(typeQuery).all(...params) as Array<{
      resource_type: string;
      count: number;
    }>;

    const byType: Record<string, number> = {};
    for (const row of typeResults) {
      byType[row.resource_type] = row.count;
    }

    let lastQuery = 'SELECT MAX(ingested_at) as last FROM ingestion_records';
    if (endpoint) {
      lastQuery += ' WHERE endpoint = ?';
    }

    const lastResult = this.db.prepare(lastQuery).get(...params) as { last: string | null };

    return {
      total: totalResult.total,
      byType,
      lastIngestion: lastResult.last || undefined
    };
  }

  close(): void {
    this.db.close();
  }
}
