"""
Audit Logging Middleware
Phase 6B: Advanced Security Features

FastAPI middleware for comprehensive request/response audit logging.
"""

import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import json

from .audit_logger import audit_logger, AuditEventType

class AuditLoggingMiddleware:
    """FastAPI middleware for audit logging"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip audit logging for health checks and static files
        if self._should_skip_logging(request.url.path):
            await self.app(scope, receive, send)
            return
        
        # Start timing
        start_time = time.time()
        
        # Extract user info from token if available
        user_id = None
        client_id = None
        
        try:
            # Try to extract user info from Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # This would require importing JWT decoding, but we'll keep it simple
                # In a full implementation, you'd decode the token here
                pass
        except Exception:
            pass
        
        # Process request and capture response
        response_body = {}
        status_code = 500
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
            success = 200 <= status_code < 400
            
        except Exception as e:
            status_code = 500
            success = False
            # Send error response
            error_response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
            await error_response(scope, receive, send)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Create mock response for logging
        response = Response(status_code=status_code)
        
        # Log the request
        details = {
            "query_params": dict(request.query_params),
            "content_length": request.headers.get("Content-Length"),
            "content_type": request.headers.get("Content-Type")
        }
        
        # Add error details if applicable
        if not success:
            details["error"] = "Request failed"
        
        audit_logger.log_api_request(
            request=request,
            response=response,
            processing_time_ms=processing_time_ms,
            user_id=user_id,
            client_id=client_id,
            success=success,
            details=details
        )
    
    def _should_skip_logging(self, path: str) -> bool:
        """Determine if request should be skipped from audit logging"""
        skip_paths = [
            "/health",
            "/favicon.ico",
            "/static/",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)

class EnhancedAuditMiddleware:
    """Enhanced audit middleware with token extraction"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip non-important endpoints
        if self._should_skip_logging(request.url.path):
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Enhanced user extraction
        user_context = await self._extract_user_context(request)
        
        # Capture request body for security analysis (limited size)
        request_body = await self._capture_request_body(request)
        
        response_data = {"status_code": 500, "success": False}
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_data["status_code"] = message["status"]
                response_data["success"] = 200 <= message["status"] < 400
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            response_data["status_code"] = 500
            response_data["success"] = False
            # Handle the exception appropriately
            error_response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
            await error_response(scope, receive, send)
        
        # Calculate metrics
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Enhanced logging with security context
        await self._log_enhanced_request(
            request, response_data, processing_time_ms, 
            user_context, request_body
        )
    
    async def _extract_user_context(self, request: Request) -> dict:
        """Extract user context from request"""
        context = {"user_id": None, "client_id": None, "scopes": []}
        
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                # In full implementation, decode JWT here
                # For now, we'll mark that a token was present
                context["has_token"] = True
        except Exception:
            pass
        
        return context
    
    async def _capture_request_body(self, request: Request) -> dict:
        """Safely capture request body for security analysis"""
        try:
            # Only capture for POST/PUT requests and limit size
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    # Read body (this is tricky with FastAPI, simplified here)
                    return {"content_type": content_type, "size": request.headers.get("Content-Length")}
        except Exception:
            pass
        
        return {}
    
    async def _log_enhanced_request(
        self, request: Request, response_data: dict, 
        processing_time_ms: float, user_context: dict, request_body: dict
    ):
        """Log request with enhanced security context"""
        
        # Create response object for logging
        response = Response(status_code=response_data["status_code"])
        
        # Enhanced details
        details = {
            "query_params": dict(request.query_params),
            "content_length": request.headers.get("Content-Length"),
            "content_type": request.headers.get("Content-Type"),
            "has_authorization": bool(request.headers.get("Authorization")),
            "request_body_info": request_body,
            "user_context": user_context
        }
        
        # Security-specific details
        if not response_data["success"]:
            details["failure_type"] = "http_error"
            if response_data["status_code"] == 401:
                details["security_event"] = "authentication_failure"
            elif response_data["status_code"] == 403:
                details["security_event"] = "authorization_failure"
        
        audit_logger.log_api_request(
            request=request,
            response=response,
            processing_time_ms=processing_time_ms,
            user_id=user_context.get("user_id"),
            client_id=user_context.get("client_id"),
            success=response_data["success"],
            details=details
        )
    
    def _should_skip_logging(self, path: str) -> bool:
        """Determine if request should be skipped"""
        skip_paths = [
            "/health",
            "/favicon.ico", 
            "/static/",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)