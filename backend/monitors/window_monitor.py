"""
Active Window Monitor
Layer 0 - Monitors currently active application and window
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import psutil
    import win32gui
    import win32process
except ImportError as e:
    raise ImportError(f"Required dependencies not installed: {e}. Run: pip install psutil pywin32")

from utils.logger import setup_logger

logger = setup_logger(__name__)


class WindowMonitor:
    """Monitor active window and application"""
    
    def __init__(self, polling_interval: float = 3.0):
        """
        Initialize window monitor
        
        Args:
            polling_interval: Seconds between polling (default 3.0)
        """
        self.polling_interval = polling_interval
        self._last_app = None
        self._last_window = None
        logger.info(f"WindowMonitor initialized (polling interval: {polling_interval}s)")
    
    def get_active_window_info(self) -> Dict[str, Any]:
        """
        Get information about currently active window
        
        Returns:
            Dictionary with app_name, window_title, process_id, exe_path
        """
        try:
            # Get active window handle
            hwnd = win32gui.GetForegroundWindow()
            
            if not hwnd:
                return self._empty_result()
            
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process ID
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            
            # Get process info
            try:
                process = psutil.Process(process_id)
                app_name = process.name()
                exe_path = process.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                app_name = "Unknown"
                exe_path = None
            
            result = {
                'app_name': app_name,
                'window_title': window_title,
                'process_id': process_id,
                'exe_path': exe_path,
                'timestamp': datetime.now().isoformat(),
                'changed': self._has_changed(app_name, window_title)
            }
            
            # Update cache
            self._last_app = app_name
            self._last_window = window_title
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting active window info: {e}")
            return self._empty_result()
    
    def _has_changed(self, app_name: str, window_title: str) -> bool:
        """Check if active window has changed"""
        return (app_name != self._last_app) or (window_title != self._last_window)
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            'app_name': None,
            'window_title': None,
            'process_id': None,
            'exe_path': None,
            'timestamp': datetime.now().isoformat(),
            'changed': False
        }
    
    def start_monitoring(self, callback=None, duration: Optional[float] = None):
        """
        Start continuous monitoring
        
        Args:
            callback: Function to call with each window info update
            duration: Optional duration in seconds (None = infinite)
        """
        logger.info("Starting window monitoring...")
        start_time = time.time()
        
        try:
            while True:
                info = self.get_active_window_info()
                
                # Only call callback if window changed or callback wants all updates
                if callback and (info['changed'] or getattr(callback, 'all_updates', False)):
                    callback(info)
                
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    logger.info("Monitoring duration reached")
                    break
                
                time.sleep(self.polling_interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            raise


def test_monitor():
    """Test function for window monitor"""
    def print_window_change(info):
        if info['app_name']:
            print(f"[{info['timestamp']}] {info['app_name']} - {info['window_title']}")
    
    print_window_change.all_updates = False  # Only on change
    
    monitor = WindowMonitor(polling_interval=2.0)
    print("Monitoring active window (Ctrl+C to stop)...")
    monitor.start_monitoring(callback=print_window_change)


if __name__ == "__main__":
    test_monitor()
