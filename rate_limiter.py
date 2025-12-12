"""
Rate Limiter Implementation

This module provides rate limiting functionality for API requests.
It supports per-hour and per-minute rate limits with automatic throttling.
"""

import time
from collections import deque
from threading import Lock
from typing import Dict, Optional


class RateLimiter:
    """
    Thread-safe rate limiter that enforces both per-minute and per-hour limits.
    
    Uses a sliding window approach to track requests and automatically
    throttles when limits are approached.
    """
    
    def __init__(self, requests_per_hour: int, requests_per_minute: int):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_hour: Maximum requests allowed per hour
            requests_per_minute: Maximum requests allowed per minute
        """
        self.requests_per_hour = requests_per_hour
        self.requests_per_minute = requests_per_minute
        
        # Track request timestamps
        self.hour_window = deque()
        self.minute_window = deque()
        
        # Thread safety
        self.lock = Lock()
        
        # Statistics
        self.total_requests = 0
        self.total_throttled = 0
        
    def _clean_window(self, window: deque, max_age: float):
        """Remove timestamps older than max_age seconds."""
        current_time = time.time()
        while window and (current_time - window[0]) > max_age:
            window.popleft()
    
    def wait_if_needed(self) -> float:
        """
        Wait if necessary to respect rate limits.
        
        Returns:
            float: Time waited in seconds (0 if no wait was needed)
        """
        with self.lock:
            current_time = time.time()
            
            # Clean old entries
            self._clean_window(self.hour_window, 3600)  # 1 hour
            self._clean_window(self.minute_window, 60)  # 1 minute
            
            wait_time = 0.0
            
            # Check minute limit
            if len(self.minute_window) >= self.requests_per_minute:
                oldest_minute = self.minute_window[0]
                wait_time = max(wait_time, 60 - (current_time - oldest_minute))
            
            # Check hour limit
            if len(self.hour_window) >= self.requests_per_hour:
                oldest_hour = self.hour_window[0]
                wait_time = max(wait_time, 3600 - (current_time - oldest_hour))
            
            # Wait if needed
            if wait_time > 0:
                self.total_throttled += 1
                time.sleep(wait_time)
                current_time = time.time()
            
            # Record this request
            self.hour_window.append(current_time)
            self.minute_window.append(current_time)
            self.total_requests += 1
            
            return wait_time
    
    def get_stats(self) -> Dict[str, any]:
        """Get statistics about rate limiting."""
        with self.lock:
            return {
                "total_requests": self.total_requests,
                "total_throttled": self.total_throttled,
                "current_hour_count": len(self.hour_window),
                "current_minute_count": len(self.minute_window),
                "requests_per_hour_limit": self.requests_per_hour,
                "requests_per_minute_limit": self.requests_per_minute
            }
    
    def reset(self):
        """Reset the rate limiter."""
        with self.lock:
            self.hour_window.clear()
            self.minute_window.clear()
            self.total_requests = 0
            self.total_throttled = 0


class RateLimiterManager:
    """Manages multiple rate limiters for different APIs."""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self.lock = Lock()
    
    def get_or_create(self, name: str, requests_per_hour: int, 
                     requests_per_minute: int) -> RateLimiter:
        """
        Get or create a rate limiter by name.
        
        Args:
            name: Unique identifier for this rate limiter
            requests_per_hour: Maximum requests per hour
            requests_per_minute: Maximum requests per minute
            
        Returns:
            RateLimiter instance
        """
        with self.lock:
            if name not in self.limiters:
                self.limiters[name] = RateLimiter(
                    requests_per_hour, 
                    requests_per_minute
                )
            return self.limiters[name]
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all rate limiters."""
        with self.lock:
            return {
                name: limiter.get_stats() 
                for name, limiter in self.limiters.items()
            }
