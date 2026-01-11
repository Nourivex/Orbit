"""
Idle Time Detector
Layer 0 - Tracks user idle time based on last input activity
"""

import time
from typing import Dict, Any
from datetime import datetime, timedelta
from ctypes import Structure, windll, c_uint, sizeof, byref

from utils.logger import setup_logger

logger = setup_logger(__name__)


class LASTINPUTINFO(Structure):
    """Windows structure for GetLastInputInfo"""
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]


class IdleDetector:
    """Detect user idle time on Windows"""
    
    # Idle thresholds in seconds
    THRESHOLD_SHORT = 60   # 1 minute
    THRESHOLD_MEDIUM = 180  # 3 minutes
    THRESHOLD_LONG = 300    # 5 minutes
    
    def __init__(self):
        """Initialize idle detector"""
        self._last_idle_time = 0
        logger.info("IdleDetector initialized")
    
    def get_idle_time(self) -> int:
        """
        Get current idle time in seconds
        
        Returns:
            Idle time in seconds since last input
        """
        try:
            lastInputInfo = LASTINPUTINFO()
            lastInputInfo.cbSize = sizeof(lastInputInfo)
            
            # Get last input info from Windows
            if windll.user32.GetLastInputInfo(byref(lastInputInfo)):
                millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
                idle_seconds = millis / 1000.0
                return int(idle_seconds)
            else:
                logger.warning("Failed to get last input info")
                return 0
                
        except Exception as e:
            logger.error(f"Error getting idle time: {e}")
            return 0
    
    def get_idle_status(self) -> Dict[str, Any]:
        """
        Get detailed idle status with threshold classification
        
        Returns:
            Dictionary with idle_time, is_idle, threshold_level, changed
        """
        idle_time = self.get_idle_time()
        
        # Determine threshold level
        if idle_time >= self.THRESHOLD_LONG:
            level = "long"
        elif idle_time >= self.THRESHOLD_MEDIUM:
            level = "medium"
        elif idle_time >= self.THRESHOLD_SHORT:
            level = "short"
        else:
            level = "active"
        
        # Check if idle status changed significantly
        changed = self._has_changed(idle_time)
        self._last_idle_time = idle_time
        
        return {
            'idle_time': idle_time,
            'is_idle': idle_time >= self.THRESHOLD_SHORT,
            'threshold_level': level,
            'changed': changed,
            'timestamp': datetime.now().isoformat()
        }
    
    def _has_changed(self, current_idle: int) -> bool:
        """
        Check if idle status changed significantly
        
        Args:
            current_idle: Current idle time in seconds
            
        Returns:
            True if crossed a threshold boundary
        """
        # Detect threshold crossings
        thresholds = [self.THRESHOLD_SHORT, self.THRESHOLD_MEDIUM, self.THRESHOLD_LONG]
        
        for threshold in thresholds:
            # Crossed threshold upward
            if self._last_idle_time < threshold <= current_idle:
                return True
            # Crossed threshold downward (became active)
            if current_idle < threshold <= self._last_idle_time:
                return True
        
        # Also detect return to active state
        if self._last_idle_time >= self.THRESHOLD_SHORT and current_idle < self.THRESHOLD_SHORT:
            return True
        
        return False
    
    def wait_for_activity(self, timeout: float = None) -> bool:
        """
        Block until user activity detected
        
        Args:
            timeout: Maximum seconds to wait (None = infinite)
            
        Returns:
            True if activity detected, False if timeout
        """
        start_time = time.time()
        initial_idle = self.get_idle_time()
        
        logger.info(f"Waiting for user activity (current idle: {initial_idle}s)...")
        
        while True:
            current_idle = self.get_idle_time()
            
            # Activity detected (idle time decreased)
            if current_idle < initial_idle:
                logger.info("User activity detected")
                return True
            
            # Timeout check
            if timeout and (time.time() - start_time) >= timeout:
                logger.info("Wait timeout reached")
                return False
            
            time.sleep(1)  # Poll every second
    
    def is_user_active(self, max_idle: int = 10) -> bool:
        """
        Check if user is currently active
        
        Args:
            max_idle: Maximum idle seconds to consider active
            
        Returns:
            True if user is active
        """
        return self.get_idle_time() < max_idle


def test_detector():
    """Test function for idle detector"""
    detector = IdleDetector()
    
    print("Monitoring idle time (Ctrl+C to stop)...")
    print(f"Thresholds: {detector.THRESHOLD_SHORT}s / {detector.THRESHOLD_MEDIUM}s / {detector.THRESHOLD_LONG}s\n")
    
    try:
        while True:
            status = detector.get_idle_status()
            
            if status['changed']:
                print(f"[{status['timestamp']}] Idle: {status['idle_time']}s - Level: {status['threshold_level']}")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped")


if __name__ == "__main__":
    test_detector()
