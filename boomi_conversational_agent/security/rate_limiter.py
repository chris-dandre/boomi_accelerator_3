"""
Rate Limiting and DDoS Protection System
Phase 6B: Advanced Security Features

Implements comprehensive rate limiting to protect against abuse and ensure service availability.
"""

import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass
from enum import Enum
from fastapi import Request, HTTPException
import asyncio

from .audit_logger import audit_logger, AuditEventType, AuditSeverity, log_rate_limit_exceeded

class RateLimitType(Enum):
    """Rate limit types"""
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    BURST = "burst"
    DAILY = "daily"

@dataclass
class RateLimitRule:
    """Rate limit rule configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    window_size_seconds: int = 60

@dataclass
class RateLimitStatus:
    """Current rate limit status"""
    allowed: bool
    remaining: int
    reset_time: float
    limit_type: RateLimitType
    retry_after: Optional[int] = None

# Rate limit configurations for different endpoints
RATE_LIMIT_RULES: Dict[str, RateLimitRule] = {
    # OAuth endpoints - stricter limits
    "/oauth/register": RateLimitRule(
        requests_per_minute=5,
        requests_per_hour=20,
        requests_per_day=100,
        burst_limit=2
    ),
    "/oauth/authorize": RateLimitRule(
        requests_per_minute=10,
        requests_per_hour=100,
        requests_per_day=500,
        burst_limit=3
    ),
    "/oauth/token": RateLimitRule(
        requests_per_minute=20,
        requests_per_hour=200,
        requests_per_day=1000,
        burst_limit=5
    ),
    "/oauth/revoke": RateLimitRule(
        requests_per_minute=10,
        requests_per_hour=50,
        requests_per_day=200,
        burst_limit=3
    ),
    
    # MCP endpoints - more generous for authenticated users
    "/mcp/call_tool": RateLimitRule(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=5000,
        burst_limit=15
    ),
    "/mcp/list_tools": RateLimitRule(
        requests_per_minute=30,
        requests_per_hour=500,
        requests_per_day=2000,
        burst_limit=10
    ),
    "/mcp/list_resources": RateLimitRule(
        requests_per_minute=30,
        requests_per_hour=500,
        requests_per_day=2000,
        burst_limit=10
    ),
    "/mcp/read_resource": RateLimitRule(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=5000,
        burst_limit=15
    ),
    
    # Health endpoint - normal limits (whitelisted anyway)
    "/health": RateLimitRule(
        requests_per_minute=30,
        requests_per_hour=300,
        requests_per_day=1000,
        burst_limit=5
    ),
    
    # Test endpoint - strict limits, bypasses whitelist
    "/test/rate-limit": RateLimitRule(
        requests_per_minute=3,
        requests_per_hour=10,
        requests_per_day=50,
        burst_limit=1
    ),
    
    # Default rule for other endpoints
    "default": RateLimitRule(
        requests_per_minute=30,
        requests_per_hour=300,
        requests_per_day=1000,
        burst_limit=5
    )
}

# In-memory storage for rate limit counters (use Redis in production)
RATE_LIMIT_STORAGE: Dict[str, Dict[str, Any]] = {}

# Blacklist for severe offenders
IP_BLACKLIST: Dict[str, Dict[str, Any]] = {}

# Whitelist for trusted IPs (admin, monitoring, etc.)
IP_WHITELIST: List[str] = [
    "127.0.0.1",
    "::1", 
    "localhost"
]

# Endpoints that bypass whitelist (for testing rate limiting)
WHITELIST_BYPASS_ENDPOINTS: List[str] = [
    "/test/rate-limit"
]

class RateLimiter:
    """Advanced rate limiting system"""
    
    def __init__(self):
        self.storage = RATE_LIMIT_STORAGE
        self.blacklist = IP_BLACKLIST
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""
        # Priority order: 
        # 1. X-Forwarded-For (for proxy setups)
        # 2. X-Real-IP 
        # 3. request.client.host
        # 4. User-Agent hash (fallback)
        
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in case of multiple proxies
            ip = forwarded_for.split(",")[0].strip()
        else:
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                ip = real_ip
            elif request.client:
                ip = request.client.host
            else:
                # Fallback to User-Agent hash
                user_agent = request.headers.get("User-Agent", "unknown")
                ip = hashlib.md5(user_agent.encode()).hexdigest()[:16]
        
        return ip
    
    def _get_rate_limit_key(self, client_id: str, endpoint: str, window_type: RateLimitType) -> str:
        """Generate rate limit storage key"""
        current_time = int(time.time())
        
        if window_type == RateLimitType.PER_MINUTE:
            window = current_time // 60
        elif window_type == RateLimitType.PER_HOUR:
            window = current_time // 3600
        elif window_type == RateLimitType.DAILY:
            window = current_time // 86400
        else:  # BURST
            window = current_time // 10  # 10-second burst windows
        
        return f"{client_id}:{endpoint}:{window_type.value}:{window}"
    
    def _get_rule_for_endpoint(self, endpoint: str) -> RateLimitRule:
        """Get rate limit rule for specific endpoint"""
        # Check for exact match first
        if endpoint in RATE_LIMIT_RULES:
            return RATE_LIMIT_RULES[endpoint]
        
        # Check for pattern matches
        for pattern, rule in RATE_LIMIT_RULES.items():
            if pattern.endswith("*") and endpoint.startswith(pattern[:-1]):
                return rule
            elif pattern in endpoint:
                return rule
        
        # Return default rule
        return RATE_LIMIT_RULES["default"]
    
    def _is_ip_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        return ip in IP_WHITELIST
    
    def _is_ip_blacklisted(self, ip: str) -> bool:
        """Check if IP is blacklisted"""
        if ip in self.blacklist:
            blacklist_info = self.blacklist[ip]
            # Check if blacklist has expired
            if blacklist_info.get("expires_at", 0) > time.time():
                return True
            else:
                # Remove expired blacklist entry
                del self.blacklist[ip]
        return False
    
    def _add_to_blacklist(self, ip: str, duration_minutes: int = 60, reason: str = "rate_limit_violation"):
        """Add IP to temporary blacklist"""
        expires_at = time.time() + (duration_minutes * 60)
        
        self.blacklist[ip] = {
            "added_at": time.time(),
            "expires_at": expires_at,
            "reason": reason,
            "duration_minutes": duration_minutes
        }
        
        # Log blacklisting
        audit_logger.log_security_event(
            AuditEventType.SECURITY_ALERT,
            AuditSeverity.WARNING,
            details={
                "action": "ip_blacklisted",
                "ip_address": ip,
                "reason": reason,
                "duration_minutes": duration_minutes,
                "expires_at": datetime.fromtimestamp(expires_at).isoformat()
            },
            security_flags=["ip_blacklisted", "automated_response"]
        )
    
    def _increment_counter(self, key: str, ttl: int) -> int:
        """Increment counter with TTL"""
        current_time = time.time()
        
        if key not in self.storage:
            self.storage[key] = {
                "count": 1,
                "first_request": current_time,
                "last_request": current_time,
                "expires_at": current_time + ttl
            }
            return 1
        else:
            # Check if key has expired
            if current_time > self.storage[key]["expires_at"]:
                self.storage[key] = {
                    "count": 1,
                    "first_request": current_time,
                    "last_request": current_time,
                    "expires_at": current_time + ttl
                }
                return 1
            else:
                self.storage[key]["count"] += 1
                self.storage[key]["last_request"] = current_time
                return self.storage[key]["count"]
    
    def _cleanup_expired_entries(self):
        """Clean up expired rate limit entries"""
        current_time = time.time()
        
        # Only run cleanup periodically
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        expired_keys = []
        for key, data in self.storage.items():
            if current_time > data.get("expires_at", 0):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.storage[key]
        
        # Cleanup expired blacklist entries
        expired_ips = []
        for ip, data in self.blacklist.items():
            if current_time > data.get("expires_at", 0):
                expired_ips.append(ip)
        
        for ip in expired_ips:
            del self.blacklist[ip]
        
        self.last_cleanup = current_time
        
        if expired_keys or expired_ips:
            audit_logger.log_system_event(
                AuditEventType.SECURITY_ALERT,
                details={
                    "action": "rate_limit_cleanup",
                    "expired_keys": len(expired_keys),
                    "expired_blacklist_entries": len(expired_ips)
                }
            )
    
    def check_rate_limit(self, request: Request, endpoint: str, user_id: Optional[str] = None) -> RateLimitStatus:
        """Check if request should be rate limited"""
        # Cleanup expired entries periodically
        self._cleanup_expired_entries()
        
        client_id = self._get_client_identifier(request)
        
        
        # Check whitelist first (unless endpoint bypasses whitelist)
        if self._is_ip_whitelisted(client_id) and endpoint not in WHITELIST_BYPASS_ENDPOINTS:
            return RateLimitStatus(
                allowed=True,
                remaining=999999,
                reset_time=time.time() + 3600,
                limit_type=RateLimitType.PER_HOUR
            )
        
        # Check blacklist
        if self._is_ip_blacklisted(client_id):
            blacklist_info = self.blacklist[client_id]
            retry_after = int(blacklist_info["expires_at"] - time.time())
            
            return RateLimitStatus(
                allowed=False,
                remaining=0,
                reset_time=blacklist_info["expires_at"],
                limit_type=RateLimitType.BURST,
                retry_after=max(retry_after, 1)
            )
        
        # Get rate limit rule for endpoint
        rule = self._get_rule_for_endpoint(endpoint)
        
        # Check different rate limit windows
        current_time = time.time()
        
        # Check burst limit (10-second window)
        burst_key = self._get_rate_limit_key(client_id, endpoint, RateLimitType.BURST)
        burst_count = self._increment_counter(burst_key, 10)
        
        if burst_count > rule.burst_limit:
            # Add to temporary blacklist for repeated burst violations
            if burst_count > rule.burst_limit * 2:
                self._add_to_blacklist(client_id, duration_minutes=15, reason="burst_limit_violation")
            
            log_rate_limit_exceeded(request, user_id, endpoint, "burst_limit")
            
            return RateLimitStatus(
                allowed=False,
                remaining=0,
                reset_time=current_time + 10,
                limit_type=RateLimitType.BURST,
                retry_after=10
            )
        
        # Check per-minute limit
        minute_key = self._get_rate_limit_key(client_id, endpoint, RateLimitType.PER_MINUTE)
        minute_count = self._increment_counter(minute_key, 60)
        
        if minute_count > rule.requests_per_minute:
            log_rate_limit_exceeded(request, user_id, endpoint, "per_minute")
            
            return RateLimitStatus(
                allowed=False,
                remaining=0,
                reset_time=current_time + 60,
                limit_type=RateLimitType.PER_MINUTE,
                retry_after=60
            )
        
        # Check per-hour limit
        hour_key = self._get_rate_limit_key(client_id, endpoint, RateLimitType.PER_HOUR)
        hour_count = self._increment_counter(hour_key, 3600)
        
        if hour_count > rule.requests_per_hour:
            # More severe violation - longer blacklist
            if hour_count > rule.requests_per_hour * 1.5:
                self._add_to_blacklist(client_id, duration_minutes=60, reason="hourly_limit_violation")
            
            log_rate_limit_exceeded(request, user_id, endpoint, "per_hour")
            
            return RateLimitStatus(
                allowed=False,
                remaining=0,
                reset_time=current_time + 3600,
                limit_type=RateLimitType.PER_HOUR,
                retry_after=3600
            )
        
        # Check daily limit
        day_key = self._get_rate_limit_key(client_id, endpoint, RateLimitType.DAILY)
        day_count = self._increment_counter(day_key, 86400)
        
        if day_count > rule.requests_per_day:
            # Severe violation - day-long blacklist
            self._add_to_blacklist(client_id, duration_minutes=1440, reason="daily_limit_violation")
            
            log_rate_limit_exceeded(request, user_id, endpoint, "daily_limit")
            
            return RateLimitStatus(
                allowed=False,
                remaining=0,
                reset_time=current_time + 86400,
                limit_type=RateLimitType.DAILY,
                retry_after=86400
            )
        
        # Request is allowed - calculate remaining quota
        remaining = min(
            rule.burst_limit - burst_count,
            rule.requests_per_minute - minute_count,
            rule.requests_per_hour - hour_count,
            rule.requests_per_day - day_count
        )
        
        return RateLimitStatus(
            allowed=True,
            remaining=remaining,
            reset_time=current_time + 60,  # Next minute reset
            limit_type=RateLimitType.PER_MINUTE
        )
    
    def get_rate_limit_headers(self, status: RateLimitStatus) -> Dict[str, str]:
        """Get HTTP headers for rate limiting"""
        headers = {
            "X-RateLimit-Remaining": str(status.remaining),
            "X-RateLimit-Reset": str(int(status.reset_time))
        }
        
        if status.retry_after:
            headers["Retry-After"] = str(status.retry_after)
        
        return headers
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        current_time = time.time()
        
        active_limits = len(self.storage)
        blacklisted_ips = len([ip for ip, data in self.blacklist.items() 
                              if data.get("expires_at", 0) > current_time])
        
        # Calculate recent violations
        recent_violations = 0
        for data in self.storage.values():
            if data.get("last_request", 0) > current_time - 300:  # Last 5 minutes
                if data.get("count", 0) > 10:  # Arbitrary threshold for "violation"
                    recent_violations += 1
        
        return {
            "active_rate_limits": active_limits,
            "blacklisted_ips": blacklisted_ips,
            "recent_violations": recent_violations,
            "storage_size": len(self.storage),
            "last_cleanup": self.last_cleanup,
            "whitelisted_ips": len(IP_WHITELIST)
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

# Convenience functions
def check_rate_limit(request: Request, endpoint: str, user_id: Optional[str] = None) -> RateLimitStatus:
    """Check rate limit for request"""
    return rate_limiter.check_rate_limit(request, endpoint, user_id)

def add_ip_to_whitelist(ip: str):
    """Add IP to whitelist"""
    if ip not in IP_WHITELIST:
        IP_WHITELIST.append(ip)
        audit_logger.log_system_event(
            AuditEventType.SECURITY_ALERT,
            details={"action": "ip_whitelisted", "ip_address": ip}
        )

def remove_ip_from_blacklist(ip: str):
    """Manually remove IP from blacklist"""
    if ip in IP_BLACKLIST:
        del IP_BLACKLIST[ip]
        audit_logger.log_system_event(
            AuditEventType.SECURITY_ALERT,
            details={"action": "ip_removed_from_blacklist", "ip_address": ip}
        )

# Rate limiting exception
class RateLimitExceeded(HTTPException):
    """Rate limit exceeded exception"""
    
    def __init__(self, status: RateLimitStatus):
        detail = f"Rate limit exceeded. Try again in {status.retry_after or 60} seconds."
        super().__init__(status_code=429, detail=detail)
        self.status = status

# Convenience functions
def check_rate_limit(request: Request, endpoint: str, user_id: Optional[str] = None) -> RateLimitStatus:
    """Convenience function to check rate limit"""
    return rate_limiter.check_rate_limit(request, endpoint, user_id)

def is_ip_blacklisted(ip: str) -> bool:
    """Convenience function to check if IP is blacklisted"""
    return rate_limiter._is_ip_blacklisted(ip)

def get_rate_limit_stats() -> Dict[str, Any]:
    """Convenience function to get rate limit statistics"""
    return rate_limiter.get_rate_limit_stats()