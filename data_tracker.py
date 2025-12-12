"""
Data Tracking System

This module provides functionality to track ingested data and prevent duplication.
It supports multiple storage backends (SQLite, JSON file).
"""

import json
import sqlite3
import hashlib
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any
from threading import Lock
from pathlib import Path


class DataTracker:
    """
    Base class for tracking ingested data.
    
    Tracks unique identifiers of ingested items to prevent re-processing.
    """
    
    def __init__(self, name: str):
        """
        Initialize the data tracker.
        
        Args:
            name: Name/identifier for this tracker
        """
        self.name = name
        self.lock = Lock()
    
    def has_item(self, item_id: str) -> bool:
        """Check if an item has been ingested."""
        raise NotImplementedError
    
    def add_item(self, item_id: str, metadata: Optional[Dict] = None):
        """Mark an item as ingested."""
        raise NotImplementedError
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked items."""
        raise NotImplementedError
    
    def clear(self):
        """Clear all tracked items."""
        raise NotImplementedError


class SQLiteDataTracker(DataTracker):
    """SQLite-based data tracker for persistent storage."""
    
    def __init__(self, name: str, db_path: str = "data_tracking.db"):
        """
        Initialize SQLite data tracker.
        
        Args:
            name: Name/identifier for this tracker
            db_path: Path to SQLite database file
        """
        super().__init__(name)
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ingested_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tracker_name TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    item_hash TEXT,
                    ingested_at TEXT NOT NULL,
                    metadata TEXT,
                    UNIQUE(tracker_name, item_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tracker_item 
                ON ingested_items(tracker_name, item_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tracker_hash 
                ON ingested_items(tracker_name, item_hash)
            """)
            conn.commit()
    
    def has_item(self, item_id: str) -> bool:
        """Check if an item has been ingested."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM ingested_items WHERE tracker_name = ? AND item_id = ?",
                    (self.name, item_id)
                )
                count = cursor.fetchone()[0]
                return count > 0
    
    def add_item(self, item_id: str, metadata: Optional[Dict] = None):
        """Mark an item as ingested."""
        with self.lock:
            # Generate hash of item_id for deduplication
            item_hash = hashlib.sha256(item_id.encode()).hexdigest()
            
            metadata_json = json.dumps(metadata) if metadata else None
            timestamp = datetime.now(timezone.utc).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                try:
                    conn.execute(
                        """INSERT INTO ingested_items 
                           (tracker_name, item_id, item_hash, ingested_at, metadata)
                           VALUES (?, ?, ?, ?, ?)""",
                        (self.name, item_id, item_hash, timestamp, metadata_json)
                    )
                    conn.commit()
                except sqlite3.IntegrityError:
                    # Item already exists, update metadata
                    conn.execute(
                        """UPDATE ingested_items 
                           SET metadata = ?, ingested_at = ?
                           WHERE tracker_name = ? AND item_id = ?""",
                        (metadata_json, timestamp, self.name, item_id)
                    )
                    conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked items."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM ingested_items WHERE tracker_name = ?",
                    (self.name,)
                )
                total_items = cursor.fetchone()[0]
                
                cursor = conn.execute(
                    """SELECT MIN(ingested_at), MAX(ingested_at) 
                       FROM ingested_items WHERE tracker_name = ?""",
                    (self.name,)
                )
                first_item, last_item = cursor.fetchone()
                
                return {
                    "tracker_name": self.name,
                    "total_items": total_items,
                    "first_item_at": first_item,
                    "last_item_at": last_item
                }
    
    def clear(self):
        """Clear all tracked items for this tracker."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM ingested_items WHERE tracker_name = ?",
                    (self.name,)
                )
                conn.commit()
    
    def get_all_items(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all tracked items."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT item_id, item_hash, ingested_at, metadata
                    FROM ingested_items 
                    WHERE tracker_name = ?
                    ORDER BY ingested_at DESC
                """
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor = conn.execute(query, (self.name,))
                items = []
                for row in cursor:
                    items.append({
                        "item_id": row[0],
                        "item_hash": row[1],
                        "ingested_at": row[2],
                        "metadata": json.loads(row[3]) if row[3] else None
                    })
                return items


class InMemoryDataTracker(DataTracker):
    """In-memory data tracker for temporary tracking."""
    
    def __init__(self, name: str):
        """Initialize in-memory data tracker."""
        super().__init__(name)
        self.items: Set[str] = set()
        self.metadata: Dict[str, Dict] = {}
    
    def has_item(self, item_id: str) -> bool:
        """Check if an item has been ingested."""
        with self.lock:
            return item_id in self.items
    
    def add_item(self, item_id: str, metadata: Optional[Dict] = None):
        """Mark an item as ingested."""
        with self.lock:
            self.items.add(item_id)
            if metadata:
                self.metadata[item_id] = metadata
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked items."""
        with self.lock:
            return {
                "tracker_name": self.name,
                "total_items": len(self.items),
                "has_metadata": len(self.metadata)
            }
    
    def clear(self):
        """Clear all tracked items."""
        with self.lock:
            self.items.clear()
            self.metadata.clear()


class DataTrackerManager:
    """Manages multiple data trackers."""
    
    def __init__(self, storage_type: str = "sqlite", db_path: str = "data_tracking.db"):
        """
        Initialize the data tracker manager.
        
        Args:
            storage_type: Type of storage ("sqlite" or "memory")
            db_path: Path to database file (for SQLite)
        """
        self.storage_type = storage_type
        self.db_path = db_path
        self.trackers: Dict[str, DataTracker] = {}
        self.lock = Lock()
    
    def get_tracker(self, name: str) -> DataTracker:
        """
        Get or create a data tracker by name.
        
        Args:
            name: Unique identifier for this tracker
            
        Returns:
            DataTracker instance
        """
        with self.lock:
            if name not in self.trackers:
                if self.storage_type == "sqlite":
                    self.trackers[name] = SQLiteDataTracker(name, self.db_path)
                else:
                    self.trackers[name] = InMemoryDataTracker(name)
            return self.trackers[name]
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all trackers."""
        with self.lock:
            return {
                name: tracker.get_stats() 
                for name, tracker in self.trackers.items()
            }
