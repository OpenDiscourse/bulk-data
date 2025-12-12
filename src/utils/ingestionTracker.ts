/**
 * Ingestion Tracker
 * Tracks data that has been ingested to avoid duplication
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { IngestionRecord } from '../types/index.js';

export class IngestionTracker {
  private records: Map<string, IngestionRecord> = new Map();
  private dataDir: string;

  constructor(dataDir: string = './data') {
    this.dataDir = dataDir;
  }

  async initialize(): Promise<void> {
    try {
      await fs.mkdir(this.dataDir, { recursive: true });
      await this.loadRecords();
    } catch (error) {
      console.error('Failed to initialize ingestion tracker:', error);
    }
  }

  private async loadRecords(): Promise<void> {
    try {
      const recordsPath = path.join(this.dataDir, 'ingestion-records.json');
      const data = await fs.readFile(recordsPath, 'utf-8');
      const records = JSON.parse(data) as IngestionRecord[];
      records.forEach(record => this.records.set(record.id, record));
    } catch (error) {
      // File doesn't exist yet, that's okay
      console.log('No existing ingestion records found, starting fresh');
    }
  }

  async saveRecords(): Promise<void> {
    try {
      const recordsPath = path.join(this.dataDir, 'ingestion-records.json');
      const records = Array.from(this.records.values());
      await fs.writeFile(recordsPath, JSON.stringify(records, null, 2));
    } catch (error) {
      console.error('Failed to save ingestion records:', error);
    }
  }

  hasBeenIngested(id: string): boolean {
    const record = this.records.get(id);
    return record?.status === 'completed';
  }

  markAsStarted(id: string, endpoint: string, metadata?: Record<string, any>): void {
    this.records.set(id, {
      id,
      endpoint,
      timestamp: Date.now(),
      status: 'in_progress',
      metadata,
    });
  }

  markAsCompleted(id: string): void {
    const record = this.records.get(id);
    if (record) {
      record.status = 'completed';
      record.timestamp = Date.now();
    }
  }

  markAsFailed(id: string): void {
    const record = this.records.get(id);
    if (record) {
      record.status = 'failed';
      record.timestamp = Date.now();
    }
  }

  getRecord(id: string): IngestionRecord | undefined {
    return this.records.get(id);
  }

  getAllRecords(): IngestionRecord[] {
    return Array.from(this.records.values());
  }

  getRecordsByStatus(status: IngestionRecord['status']): IngestionRecord[] {
    return Array.from(this.records.values()).filter(r => r.status === status);
  }

  clearRecord(id: string): void {
    this.records.delete(id);
  }
}

export const ingestionTracker = new IngestionTracker();
