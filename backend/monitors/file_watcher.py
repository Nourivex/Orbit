"""
File System Watcher
Layer 0 - Monitors file system changes in workspace
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from collections import deque

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
except ImportError as e:
    raise ImportError(f"Watchdog not installed: {e}. Run: pip install watchdog")

from utils.logger import setup_logger

logger = setup_logger(__name__)


class FileChangeHandler(FileSystemEventHandler):
    """Handler for file system events"""
    
    def __init__(self, callback: Optional[Callable] = None, max_history: int = 50):
        """
        Initialize file change handler
        
        Args:
            callback: Optional callback function for events
            max_history: Maximum number of events to keep in history
        """
        super().__init__()
        self.callback = callback
        self.event_history = deque(maxlen=max_history)
        self.event_counts = {
            'created': 0,
            'modified': 0,
            'deleted': 0,
            'moved': 0
        }
    
    def on_created(self, event: FileSystemEvent):
        """Handle file/directory creation"""
        if not event.is_directory:
            self._record_event('created', event.src_path)
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file/directory modification"""
        if not event.is_directory:
            self._record_event('modified', event.src_path)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file/directory deletion"""
        if not event.is_directory:
            self._record_event('deleted', event.src_path)
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file/directory move"""
        if not event.is_directory:
            self._record_event('moved', event.src_path, event.dest_path)
    
    def _record_event(self, event_type: str, src_path: str, dest_path: str = None):
        """
        Record file system event
        
        Args:
            event_type: Type of event (created, modified, deleted, moved)
            src_path: Source file path
            dest_path: Destination path (for move events)
        """
        event_data = {
            'type': event_type,
            'path': src_path,
            'dest_path': dest_path,
            'timestamp': datetime.now().isoformat()
        }
        
        self.event_history.append(event_data)
        self.event_counts[event_type] += 1
        
        logger.debug(f"File {event_type}: {src_path}")
        
        if self.callback:
            self.callback(event_data)
    
    def get_recent_events(self, limit: int = 10) -> List[Dict]:
        """
        Get recent file system events
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent events
        """
        return list(self.event_history)[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get file system event statistics
        
        Returns:
            Dictionary with event counts
        """
        return {
            'total_events': sum(self.event_counts.values()),
            'by_type': self.event_counts.copy(),
            'history_size': len(self.event_history)
        }


class FileWatcher:
    """Watch file system changes in specified directory"""
    
    def __init__(self, watch_path: Optional[str] = None):
        """
        Initialize file watcher
        
        Args:
            watch_path: Path to watch (default: current directory)
        """
        self.watch_path = Path(watch_path) if watch_path else Path.cwd()
        self.observer = Observer()
        self.handler = FileChangeHandler()
        self._is_watching = False
        
        logger.info(f"FileWatcher initialized for: {self.watch_path}")
    
    def start(self, recursive: bool = True):
        """
        Start watching file system
        
        Args:
            recursive: Watch subdirectories recursively
        """
        if self._is_watching:
            logger.warning("Watcher already running")
            return
        
        try:
            self.observer.schedule(
                self.handler,
                str(self.watch_path),
                recursive=recursive
            )
            self.observer.start()
            self._is_watching = True
            logger.info(f"Started watching: {self.watch_path} (recursive={recursive})")
            
        except Exception as e:
            logger.error(f"Failed to start watcher: {e}")
            raise
    
    def stop(self):
        """Stop watching file system"""
        if not self._is_watching:
            return
        
        self.observer.stop()
        self.observer.join(timeout=5)
        self._is_watching = False
        logger.info("File watcher stopped")
    
    def is_watching(self) -> bool:
        """Check if watcher is active"""
        return self._is_watching
    
    def get_recent_changes(self, limit: int = 10) -> List[Dict]:
        """
        Get recent file changes
        
        Args:
            limit: Maximum number of changes to return
            
        Returns:
            List of recent file changes
        """
        return self.handler.get_recent_events(limit)
    
    def get_change_summary(self) -> Dict[str, Any]:
        """
        Get summary of file changes
        
        Returns:
            Dictionary with change statistics
        """
        stats = self.handler.get_stats()
        stats['watch_path'] = str(self.watch_path)
        stats['is_watching'] = self._is_watching
        return stats
    
    def set_callback(self, callback: Callable):
        """
        Set callback for file system events
        
        Args:
            callback: Function to call on each event
        """
        self.handler.callback = callback
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


def test_watcher():
    """Test function for file watcher"""
    
    def on_change(event):
        print(f"[{event['timestamp']}] {event['type'].upper()}: {event['path']}")
    
    # Watch current directory
    watcher = FileWatcher()
    watcher.set_callback(on_change)
    
    print(f"Watching: {watcher.watch_path}")
    print("Make some file changes to test... (Ctrl+C to stop)\n")
    
    try:
        watcher.start()
        
        while True:
            time.sleep(5)
            summary = watcher.get_change_summary()
            print(f"\nStats: {summary['total_events']} total events - {summary['by_type']}")
            
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        watcher.stop()
        print("Done")


if __name__ == "__main__":
    test_watcher()
