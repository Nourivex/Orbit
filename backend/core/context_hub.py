"""
Context Hub - Layer 0
Aggregates all monitoring sources into unified context snapshots
"""

import time
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from monitors.window_monitor import WindowMonitor
from monitors.idle_detector import IdleDetector
from monitors.file_watcher import FileWatcher
from utils.db import ContextDB
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ContextHub:
    """
    Central hub for collecting and aggregating system context
    Layer 0 - Foundation for ORBIT decision making
    """
    
    def __init__(
        self,
        watch_path: Optional[str] = None,
        polling_interval: float = 3.0,
        db_path: str = "data/orbit_context.db"
    ):
        """
        Initialize Context Hub
        
        Args:
            watch_path: Directory to watch for file changes
            polling_interval: Seconds between context updates
            db_path: Path to SQLite database
        """
        self.polling_interval = polling_interval
        
        # Initialize monitors
        self.window_monitor = WindowMonitor(polling_interval=polling_interval)
        self.idle_detector = IdleDetector()
        self.file_watcher = FileWatcher(watch_path=watch_path)
        
        # Initialize database
        self.db = ContextDB(db_path=db_path)
        
        # State
        self._is_running = False
        self._monitoring_thread = None
        self._context_callback = None
        
        # Counters
        self._snapshot_count = 0
        self._error_count = 0
        
        logger.info(f"ContextHub initialized (polling: {polling_interval}s)")
    
    def get_context_snapshot(self) -> Dict[str, Any]:
        """
        Get current context snapshot from all monitors
        
        Returns:
            Unified context dictionary
        """
        try:
            start_time = time.time()
            
            # Gather from all monitors
            window_info = self.window_monitor.get_active_window_info()
            idle_status = self.idle_detector.get_idle_status()
            file_changes = self.file_watcher.get_change_summary()
            
            # Build unified snapshot
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'active_app': window_info.get('app_name'),
                'window_title': window_info.get('window_title'),
                'idle_time': idle_status.get('idle_time'),
                'idle_level': idle_status.get('threshold_level'),
                'is_idle': idle_status.get('is_idle'),
                'file_changes_total': file_changes.get('total_events', 0),
                'recent_file_changes': len(self.file_watcher.get_recent_changes(limit=5)),
                'error_count': self._error_count,
                'latency_ms': int((time.time() - start_time) * 1000),
                'snapshot_count': self._snapshot_count
            }
            
            self._snapshot_count += 1
            
            # Log if latency is high
            if snapshot['latency_ms'] > 100:
                logger.warning(f"High latency: {snapshot['latency_ms']}ms")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error getting context snapshot: {e}")
            self._error_count += 1
            return self._empty_snapshot()
    
    def _empty_snapshot(self) -> Dict[str, Any]:
        """Return empty snapshot on error"""
        return {
            'timestamp': datetime.now().isoformat(),
            'active_app': None,
            'window_title': None,
            'idle_time': 0,
            'idle_level': 'unknown',
            'is_idle': False,
            'file_changes_total': 0,
            'recent_file_changes': 0,
            'error_count': self._error_count,
            'latency_ms': 0,
            'snapshot_count': self._snapshot_count
        }
    
    def save_snapshot(self, snapshot: Optional[Dict[str, Any]] = None):
        """
        Save context snapshot to database
        
        Args:
            snapshot: Snapshot to save (or get current if None)
        """
        if snapshot is None:
            snapshot = self.get_context_snapshot()
        
        try:
            event = {
                'timestamp': snapshot['timestamp'],
                'event_type': 'context_snapshot',
                'app_name': snapshot['active_app'],
                'window_title': snapshot['window_title'],
                'idle_time': snapshot['idle_time'],
                'file_changes': snapshot['recent_file_changes'],
                'error_count': snapshot['error_count'],
                'data': {
                    'idle_level': snapshot['idle_level'],
                    'latency_ms': snapshot['latency_ms']
                }
            }
            
            self.db.insert_event(event)
            logger.debug(f"Snapshot saved (#{snapshot['snapshot_count']})")
            
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
    
    def start(self, save_to_db: bool = True, callback: Optional[Callable] = None):
        """
        Start continuous context monitoring
        
        Args:
            save_to_db: Whether to save snapshots to database
            callback: Optional callback for each snapshot
        """
        if self._is_running:
            logger.warning("ContextHub already running")
            return
        
        self._context_callback = callback
        self._is_running = True
        
        # Start file watcher
        self.file_watcher.start(recursive=True)
        
        # Start monitoring thread
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(save_to_db,),
            daemon=True
        )
        self._monitoring_thread.start()
        
        logger.info("ContextHub started")
    
    def _monitoring_loop(self, save_to_db: bool):
        """Internal monitoring loop"""
        logger.info("Context monitoring loop started")
        
        while self._is_running:
            try:
                # Get snapshot
                snapshot = self.get_context_snapshot()
                
                # Save to database
                if save_to_db:
                    self.save_snapshot(snapshot)
                
                # Call callback
                if self._context_callback:
                    self._context_callback(snapshot)
                
                # Sleep until next poll
                time.sleep(self.polling_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self._error_count += 1
                time.sleep(self.polling_interval)
    
    def stop(self):
        """Stop context monitoring"""
        if not self._is_running:
            return
        
        logger.info("Stopping ContextHub...")
        
        self._is_running = False
        
        # Stop file watcher
        self.file_watcher.stop()
        
        # Wait for monitoring thread
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        
        logger.info("ContextHub stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about context monitoring
        
        Returns:
            Dictionary with stats
        """
        db_stats = self.db.get_stats()
        file_stats = self.file_watcher.get_change_summary()
        
        return {
            'is_running': self._is_running,
            'snapshots_collected': self._snapshot_count,
            'errors': self._error_count,
            'database': db_stats,
            'file_watcher': file_stats,
            'polling_interval': self.polling_interval
        }
    
    def cleanup_old_data(self, days: int = 7):
        """
        Clean up old context data
        
        Args:
            days: Remove data older than N days
        """
        deleted = self.db.cleanup_old_events(days=days)
        logger.info(f"Cleaned up {deleted} old records")
        return deleted
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


def test_context_hub():
    """Test function for Context Hub"""
    
    def on_context_update(snapshot):
        """Print context updates"""
        print(f"\n[{snapshot['timestamp']}]")
        print(f"  App: {snapshot['active_app']}")
        print(f"  Idle: {snapshot['idle_time']}s ({snapshot['idle_level']})")
        print(f"  Files: {snapshot['recent_file_changes']} recent changes")
        print(f"  Latency: {snapshot['latency_ms']}ms")
    
    print("Starting Context Hub test...\n")
    
    hub = ContextHub(polling_interval=5.0)
    hub.start(save_to_db=True, callback=on_context_update)
    
    try:
        print("Monitoring context (Ctrl+C to stop)...")
        while True:
            time.sleep(10)
            stats = hub.get_stats()
            print(f"\n--- Stats: {stats['snapshots_collected']} snapshots, {stats['errors']} errors ---")
            
    except KeyboardInterrupt:
        print("\n\nStopping...")
        hub.stop()
        
        # Final stats
        final_stats = hub.get_stats()
        print("\nFinal Statistics:")
        print(f"  Total snapshots: {final_stats['snapshots_collected']}")
        print(f"  Total errors: {final_stats['errors']}")
        print(f"  DB records: {final_stats['database']['total_events']}")


if __name__ == "__main__":
    test_context_hub()
