"""
Comprehensive Audit Logging System
Phase 6B: Advanced Security Features

This module provides enterprise-grade audit logging for all OAuth operations,
API calls, and security events in the Boomi DataHub MCP Server.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
import logging
from pathlib import Path
import asyncio
from fastapi import Request, Response
import os

class AuditEventType(Enum):
    """Audit event type enumeration"""
    # OAuth Events
    CLIENT_REGISTRATION = "client_registration"
    AUTHORIZATION_REQUEST = "authorization_request"
    TOKEN_EXCHANGE = "token_exchange"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOCATION = "token_revocation"
    
    # API Events
    API_REQUEST = "api_request"
    API_SUCCESS = "api_success"
    API_FAILURE = "api_failure"
    
    # Security Events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"
    ACCESS_DENIED = "access_denied"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # System Events
    SERVER_STARTUP = "server_startup"
    SERVER_SHUTDOWN = "server_shutdown"
    SECURITY_ALERT = "security_alert"

class AuditSeverity(Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AuditEvent:
    """Structured audit event"""
    
    def __init__(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: Optional[str] = None,
        client_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        success: bool = True,
        response_code: Optional[int] = None,
        processing_time_ms: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        security_flags: Optional[List[str]] = None
    ):
        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.event_type = event_type.value
        self.severity = severity.value
        self.user_id = user_id
        self.client_id = client_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.endpoint = endpoint
        self.method = method
        self.success = success
        self.response_code = response_code
        self.processing_time_ms = processing_time_ms
        self.details = details or {}
        self.security_flags = security_flags or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "severity": self.severity,
            "user_id": self.user_id,
            "client_id": self.client_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "endpoint": self.endpoint,
            "method": self.method,
            "success": self.success,
            "response_code": self.response_code,
            "processing_time_ms": self.processing_time_ms,
            "details": self.details,
            "security_flags": self.security_flags
        }
    
    def to_json(self) -> str:
        """Convert audit event to JSON string"""
        return json.dumps(self.to_dict(), default=str)

class AuditLogger:
    """Centralized audit logging system"""
    
    def __init__(self, log_directory: str = "logs/audit"):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Setup file logger
        self.logger = logging.getLogger("audit_logger")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create file handler with daily rotation
        log_file = self.log_directory / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler for critical events
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Create formatters
        file_formatter = logging.Formatter('%(message)s')
        console_formatter = logging.Formatter(
            '🚨 SECURITY ALERT: %(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    async def log_event(self, event: AuditEvent):
        """Log an audit event asynchronously"""
        try:
            # Log to file
            self.logger.info(event.to_json())
            
            # Console alert for critical/security events
            if event.severity in [AuditSeverity.CRITICAL.value, AuditSeverity.ERROR.value]:
                if event.event_type in [
                    AuditEventType.JAILBREAK_ATTEMPT.value,
                    AuditEventType.RATE_LIMIT_EXCEEDED.value,
                    AuditEventType.ACCESS_DENIED.value,
                    AuditEventType.SECURITY_ALERT.value
                ]:
                    self.logger.warning(f"Security Event: {event.event_type} - User: {event.user_id} - IP: {event.ip_address}")
        
        except Exception as e:
            # Fallback logging to prevent audit failures from breaking the application
            print(f"Audit logging failed: {e}")
    
    def log_oauth_event(
        self,
        event_type: AuditEventType,
        success: bool = True,
        client_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log OAuth-related events"""
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING
        
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            client_id=client_id,
            ip_address=ip_address,
            success=success,
            details=details
        )
        
        # Use asyncio to log without blocking
        asyncio.create_task(self.log_event(event))
    
    def log_api_request(
        self,
        request: Request,
        response: Response,
        processing_time_ms: float,
        user_id: Optional[str] = None,
        client_id: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log API request events"""
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING
        
        # Extract client IP (handle proxy headers)
        ip_address = request.headers.get("X-Forwarded-For", 
                     request.headers.get("X-Real-IP", 
                     request.client.host if request.client else "unknown"))
        
        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=severity,
            user_id=user_id,
            client_id=client_id,
            ip_address=ip_address,
            user_agent=request.headers.get("User-Agent"),
            endpoint=str(request.url.path),
            method=request.method,
            success=success,
            response_code=response.status_code,
            processing_time_ms=processing_time_ms,
            details=details
        )
        
        asyncio.create_task(self.log_event(event))
    
    def log_security_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        security_flags: Optional[List[str]] = None
    ):
        """Log security-related events"""
        ip_address = None
        user_agent = None
        endpoint = None
        method = None
        
        if request:
            ip_address = request.headers.get("X-Forwarded-For", 
                         request.headers.get("X-Real-IP", 
                         request.client.host if request.client else "unknown"))
            user_agent = request.headers.get("User-Agent")
            endpoint = str(request.url.path)
            method = request.method
        
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            success=False,  # Security events are typically failures/alerts
            details=details,
            security_flags=security_flags
        )
        
        asyncio.create_task(self.log_event(event))
    
    def log_system_event(
        self,
        event_type: AuditEventType,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log system events"""
        event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.INFO,
            details=details
        )
        
        asyncio.create_task(self.log_event(event))
    
    def get_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve audit logs with filtering"""
        logs = []
        
        try:
            # Get all log files in date range
            log_files = []
            if start_date:
                current_date = start_date.date()
                end = end_date.date() if end_date else datetime.now().date()
                
                while current_date <= end:
                    log_file = self.log_directory / f"audit_{current_date.strftime('%Y%m%d')}.jsonl"
                    if log_file.exists():
                        log_files.append(log_file)
                    current_date += current_date.resolution
            else:
                # Get all available log files
                log_files = list(self.log_directory.glob("audit_*.jsonl"))
            
            # Read and filter logs
            for log_file in sorted(log_files, reverse=True):
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            
                            # Apply filters
                            if event_type and log_entry.get("event_type") != event_type:
                                continue
                            if user_id and log_entry.get("user_id") != user_id:
                                continue
                            if severity and log_entry.get("severity") != severity:
                                continue
                            
                            # Date range filter
                            if start_date or end_date:
                                log_timestamp = datetime.fromisoformat(
                                    log_entry["timestamp"].replace('Z', '+00:00')
                                )
                                if start_date and log_timestamp < start_date:
                                    continue
                                if end_date and log_timestamp > end_date:
                                    continue
                            
                            logs.append(log_entry)
                            
                            if len(logs) >= limit:
                                return logs
                                
                        except json.JSONDecodeError:
                            continue
            
        except Exception as e:
            print(f"Error retrieving audit logs: {e}")
        
        return logs[:limit]

# Global audit logger instance
audit_logger = AuditLogger()

# Convenience functions for common audit operations
def log_oauth_client_registration(client_id: str, ip_address: str, success: bool = True):
    """Log OAuth client registration"""
    audit_logger.log_oauth_event(
        AuditEventType.CLIENT_REGISTRATION,
        success=success,
        client_id=client_id,
        ip_address=ip_address,
        details={"action": "client_registration"}
    )

def log_token_exchange(client_id: str, user_id: str, ip_address: str, scope: str, success: bool = True):
    """Log OAuth token exchange"""
    audit_logger.log_oauth_event(
        AuditEventType.TOKEN_EXCHANGE,
        success=success,
        client_id=client_id,
        user_id=user_id,
        ip_address=ip_address,
        details={"scope": scope, "action": "token_exchange"}
    )

def log_access_denied(request: Request, user_id: str, reason: str):
    """Log access denied events"""
    audit_logger.log_security_event(
        AuditEventType.ACCESS_DENIED,
        AuditSeverity.WARNING,
        request=request,
        user_id=user_id,
        details={"reason": reason},
        security_flags=["access_denied"]
    )

def log_jailbreak_attempt(request: Request, user_id: str, pattern_matched: str, content_snippet: str):
    """Log potential jailbreak attempts"""
    audit_logger.log_security_event(
        AuditEventType.JAILBREAK_ATTEMPT,
        AuditSeverity.CRITICAL,
        request=request,
        user_id=user_id,
        details={
            "pattern_matched": pattern_matched,
            "content_snippet": content_snippet[:200],  # Limit content for privacy
            "action": "request_blocked"
        },
        security_flags=["jailbreak_attempt", "potential_threat"]
    )

def log_rate_limit_exceeded(request: Request, user_id: str, endpoint: str, limit_type: str):
    """Log rate limit exceeded events"""
    audit_logger.log_security_event(
        AuditEventType.RATE_LIMIT_EXCEEDED,
        AuditSeverity.WARNING,
        request=request,
        user_id=user_id,
        details={
            "endpoint": endpoint,
            "limit_type": limit_type,
            "action": "request_throttled"
        },
        security_flags=["rate_limit_exceeded"]
    )

# System startup logging
def log_server_startup():
    """Log server startup event"""
    audit_logger.log_system_event(
        AuditEventType.SERVER_STARTUP,
        details={
            "server_version": "6.1.0",
            "security_features": ["oauth2.1", "audit_logging", "rate_limiting", "jailbreak_detection"],
            "startup_time": datetime.now(timezone.utc).isoformat()
        }
    )

def log_server_shutdown():
    """Log server shutdown event"""
    audit_logger.log_system_event(
        AuditEventType.SERVER_SHUTDOWN,
        details={
            "shutdown_time": datetime.now(timezone.utc).isoformat(),
            "reason": "normal_shutdown"
        }
    )