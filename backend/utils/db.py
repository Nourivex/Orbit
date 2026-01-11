"""
Database utility for ORBIT Context Cache
Layer 0 - Stores monitoring events and context history
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from utils.logger import setup_logger

logger = setup_logger(__name__)


class ContextDB:
    """SQLite database for storing context events"""
    
    def __init__(self, db_path: str = "data/orbit_context.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        logger.info(f"ContextDB initialized at {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_schema(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Context events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS context_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    app_name TEXT,
                    window_title TEXT,
                    idle_time INTEGER,
                    file_changes INTEGER,
                    error_count INTEGER,
                    data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON context_events(timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_type 
                ON context_events(event_type)
            """)
            
            logger.info("Database schema initialized")
    
    def insert_event(self, event: Dict[str, Any]) -> int:
        """
        Insert a context event
        
        Args:
            event: Event data dictionary
            
        Returns:
            ID of inserted row
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO context_events 
                (timestamp, event_type, app_name, window_title, 
                 idle_time, file_changes, error_count, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.get('timestamp', datetime.now().isoformat()),
                event.get('event_type', 'context_snapshot'),
                event.get('app_name'),
                event.get('window_title'),
                event.get('idle_time', 0),
                event.get('file_changes', 0),
                event.get('error_count', 0),
                json.dumps(event.get('data', {}))
            ))
            
            return cursor.lastrowid
    
    def get_recent_events(self, limit: int = 10, event_type: Optional[str] = None) -> List[Dict]:
        """
        Get recent context events
        
        Args:
            limit: Maximum number of events to retrieve
            event_type: Filter by event type (optional)
            
        Returns:
            List of event dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM context_events"
            params = []
            
            if event_type:
                query += " WHERE event_type = ?"
                params.append(event_type)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_events_in_timerange(self, minutes: int = 60) -> List[Dict]:
        """
        Get events within specified time range
        
        Args:
            minutes: Time range in minutes from now
            
        Returns:
            List of event dictionaries
        """
        cutoff = (datetime.now() - timedelta(minutes=minutes)).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM context_events
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """, (cutoff,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def cleanup_old_events(self, days: int = 7):
        """
        Remove events older than specified days
        
        Args:
            days: Keep only events from last N days
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM context_events
                WHERE timestamp < ?
            """, (cutoff,))
            
            deleted = cursor.rowcount
            logger.info(f"Cleaned up {deleted} old events (older than {days} days)")
            
            return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with stats
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total events
            cursor.execute("SELECT COUNT(*) as total FROM context_events")
            total = cursor.fetchone()['total']
            
            # Events by type
            cursor.execute("""
                SELECT event_type, COUNT(*) as count
                FROM context_events
                GROUP BY event_type
            """)
            by_type = {row['event_type']: row['count'] for row in cursor.fetchall()}
            
            # Events in last 24 hours
            cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) as recent
                FROM context_events
                WHERE timestamp > ?
            """, (cutoff,))
            recent = cursor.fetchone()['recent']
            
            return {
                'total_events': total,
                'by_type': by_type,
                'last_24h': recent
            }
