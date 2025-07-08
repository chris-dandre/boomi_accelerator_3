"""
Enhanced Boomi DataHub MCP Server with Advanced Security
Phase 6B: Complete Security Implementation

This server integrates all Phase 6B security features:
- OAuth 2.1 authentication (Phase 6A)
- Comprehensive audit logging
- Token revocation (RFC 7009)
- Rate limiting and DDoS protection
- Jailbreak detection and prompt injection protection
"""

import sys
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Depends, Request, Response, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic
from pydantic import BaseModel
import jwt

# Import OAuth 2.1 components from Phase 6A
from oauth_server import (
    oauth_app, OAUTH_SCOPES, USER_SCOPES, JWT_SECRET_KEY, JWT_ALGORITHM,
    oauth_metadata, register_client, authorize, token_exchange, jwks,
    CLIENT_REGISTRY
)

# Import Phase 6B security components
from security.audit_logger import (
    audit_logger, log_server_startup, log_server_shutdown,
    log_oauth_client_registration, log_token_exchange, log_access_denied
)
from security.audit_middleware import EnhancedAuditMiddleware
from security.token_revocation import (
    revoke_token_endpoint, is_token_revoked, add_jti_to_token_payload,
    get_revocation_stats
)
from security.rate_limiter import (
    rate_limiter, check_rate_limit, RateLimitExceeded,
    RateLimitStatus
)
from security.jailbreak_detector import (
    jailbreak_detector, analyze_request_for_threats, should_block_request,
    log_detection_result, DetectionResult
)

# Try to import Boomi DataHub client
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'boomi_datahub_mcp_server'))
    from boomi_datahub_client import BoomiDataHubClient, BoomiCredentials
except ImportError:
    try:
        from boomi_datahub_mcp_server.boomi_datahub_client import BoomiDataHubClient, BoomiCredentials
    except ImportError as e:
        print(f"❌ Error importing BoomiDataHubClient: {e}")
        print("🔍 Please ensure boomi_datahub_client.py is accessible")
        sys.exit(1)

# Create the main FastAPI app
app = FastAPI(
    title="Boomi DataHub MCP Server - Enterprise Security Edition",
    description="Advanced MCP server with OAuth 2.1, audit logging, rate limiting, and jailbreak detection",
    version="6.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add enhanced audit logging middleware
app.add_middleware(EnhancedAuditMiddleware)

# Add security middleware
@app.middleware("http")
async def add_security_middleware(request: Request, call_next):
    """Add comprehensive security middleware"""
    start_time = datetime.now()
    
    # Initialize rate status
    rate_status = None
    
    # Skip security checks ONLY for static endpoints (but apply headers everywhere)
    skip_security_checks = request.url.path in ["/docs", "/openapi.json", "/redoc"]
    
    if not skip_security_checks:
        # Step 1: Rate limiting check
        try:
            rate_status = check_rate_limit(request, request.url.path)
            if not rate_status.allowed:
                headers = rate_limiter.get_rate_limit_headers(rate_status)
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Rate limit exceeded. Try again in {rate_status.retry_after or 60} seconds."},
                    headers=headers
                )
        except Exception as e:
            # Log rate limiting errors but don't block
            audit_logger.log_security_event(
                "rate_limit_error",
                "error", 
                request=request,
                details={"error": str(e)}
            )
        
        # Step 2: Jailbreak detection
        try:
            # Read request body for POST requests
            request_body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    # Get the request body as bytes and decode
                    body_bytes = await request.body()
                    if body_bytes:
                        request_body = body_bytes.decode('utf-8')
                except Exception:
                    request_body = None
            
            detection_result = analyze_request_for_threats(request, request_body)
            
            if should_block_request(detection_result):
                log_detection_result(request, detection_result)
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Request blocked due to security policy",
                        "threat_detected": True,
                        "threat_level": detection_result.threat_level.value,
                        "matched_rules": detection_result.matched_rules
                    }
                )
            
            # Log suspicious but allowed requests
            if detection_result.is_threat:
                log_detection_result(request, detection_result)
                
        except Exception as e:
            # Don't block on detection errors, but log them
            audit_logger.log_security_event(
                "jailbreak_detection_error",
                "error",
                request=request, 
                details={"error": str(e)}
            )
    
    # Proceed with request
    response = await call_next(request)
    
    # Add security headers to ALL responses
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Add rate limit headers if available
    try:
        if rate_status:
            response.headers.update(rate_limiter.get_rate_limit_headers(rate_status))
    except Exception as e:
        pass
    
    return response

# Security components
security = HTTPBearer()
basic_auth = HTTPBasic()

# Global client instance
_boomi_client: Optional[BoomiDataHubClient] = None

def get_boomi_client() -> BoomiDataHubClient:
    """Get or create the Boomi DataHub client instance"""
    global _boomi_client
    
    if _boomi_client is None:
        try:
            _boomi_client = BoomiDataHubClient()
            test_result = _boomi_client.test_connection()
            if not test_result['success']:
                raise Exception(f"Boomi connection failed: {test_result['error']}")
        except Exception as e:
            raise Exception(f"Failed to initialize Boomi DataHub client: {str(e)}")
    
    return _boomi_client

# Pydantic models for MCP requests
class MCPToolRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]

class MCPListToolsRequest(BaseModel):
    pass

class MCPListResourcesRequest(BaseModel):
    pass

class MCPReadResourceRequest(BaseModel):
    uri: str

# Enhanced security middleware functions
async def security_middleware(request: Request, call_next):
    """Comprehensive security middleware"""
    start_time = datetime.now()
    
    # Skip security checks for health and static endpoints
    if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
        response = await call_next(request)
        return response
    
    # Step 1: Rate limiting check
    try:
        rate_status = check_rate_limit(request, request.url.path)
        if not rate_status.allowed:
            headers = rate_limiter.get_rate_limit_headers(rate_status)
            raise RateLimitExceeded(rate_status)
    except RateLimitExceeded as e:
        response = JSONResponse(
            status_code=429,
            content={"detail": e.detail},
            headers=rate_limiter.get_rate_limit_headers(e.status)
        )
        return response
    
    # Step 2: Jailbreak detection
    try:
        # Read request body for analysis (if present)
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            # This is a simplified approach - in production you'd need more sophisticated body reading
            pass
        
        detection_result = analyze_request_for_threats(request, request_body)
        
        if should_block_request(detection_result):
            log_detection_result(request, detection_result)
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Request blocked due to security policy",
                    "threat_detected": True,
                    "threat_level": detection_result.threat_level.value
                }
            )
        
        # Log suspicious but allowed requests
        if detection_result.is_threat:
            log_detection_result(request, detection_result)
            
    except Exception as e:
        # Don't block on detection errors, but log them
        audit_logger.log_security_event(
            "security_error",
            "error",
            request=request,
            details={"error": str(e), "component": "jailbreak_detection"}
        )
    
    # Proceed with request
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Add rate limit headers
    if hasattr(rate_status, 'remaining'):
        response.headers.update(rate_limiter.get_rate_limit_headers(rate_status))
    
    return response

# Enhanced token validation with revocation check
def verify_jwt_token_enhanced(token: str) -> Dict[str, Any]:
    """Enhanced JWT token verification with revocation checking"""
    try:
        # Step 1: Check if token is revoked
        if is_token_revoked(token):
            raise HTTPException(status_code=401, detail="Token has been revoked")
        
        # Step 2: Verify JWT signature and claims
        payload = jwt.decode(
            token, 
            JWT_SECRET_KEY, 
            algorithms=[JWT_ALGORITHM],
            audience="boomi-mcp-server",
            issuer="http://localhost:8001"
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_oauth_token_enhanced(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Enhanced OAuth token validation with full security checks"""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    
    token = credentials.credentials
    
    try:
        payload = verify_jwt_token_enhanced(token)
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

def validate_user_permissions(token_payload: Dict[str, Any], requested_scope: str = "read:all") -> bool:
    """Validate user permissions based on token payload and requested scope"""
    user_id = token_payload.get("sub")
    token_scopes = token_payload.get("scope", "").split()
    
    # Check if user has required scope
    if requested_scope in token_scopes:
        return True
    
    # Check user-specific permissions
    user_permissions = USER_SCOPES.get(user_id, ["none"])
    if requested_scope in user_permissions:
        return True
    
    return False

# Add OAuth endpoints to main app
app.get("/.well-known/oauth-authorization-server")(oauth_metadata)
app.post("/oauth/register")(register_client)
app.get("/oauth/authorize")(authorize)
app.post("/oauth/token")(token_exchange)
app.get("/oauth/jwks")(jwks)

# Add token revocation endpoint with shared client registry
from security.token_revocation import revoke_token_endpoint as _revoke_token_endpoint

# Override the CLIENT_REGISTRY in token_revocation module
import security.token_revocation as token_revocation_module
token_revocation_module.CLIENT_REGISTRY = CLIENT_REGISTRY

app.post("/oauth/revoke")(_revoke_token_endpoint)

# Enhanced MCP endpoints with full security
@app.post("/mcp/call_tool")
async def call_tool_secure(
    request: Request,
    mcp_request: MCPToolRequest,
    token_payload: Dict[str, Any] = Depends(require_oauth_token_enhanced)
):
    """Execute MCP tool with comprehensive security"""
    
    # Validate permissions based on tool
    required_scope = "read:all"  # Default scope for most tools
    if not validate_user_permissions(token_payload, required_scope):
        log_access_denied(request, token_payload.get("sub"), f"Insufficient scope for {mcp_request.name}")
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied. Required scope: {required_scope}"
        )
    
    try:
        client = get_boomi_client()
        
        # Handle different tool types
        if mcp_request.name == "get_all_models":
            result = client.get_all_models()
        elif mcp_request.name == "get_model_details":
            model_name = mcp_request.arguments.get("model_name")
            if not model_name:
                raise HTTPException(status_code=400, detail="model_name is required")
            result = client.get_model_details(model_name)
        elif mcp_request.name == "execute_query":
            model_name = mcp_request.arguments.get("model_name")
            query_params = mcp_request.arguments.get("query_params", {})
            
            if not model_name:
                raise HTTPException(status_code=400, detail="model_name is required")
            
            # Additional permission check for specific models
            if model_name.lower() == "advertisements":
                if not validate_user_permissions(token_payload, "read:advertisements"):
                    if not validate_user_permissions(token_payload, "read:all"):
                        log_access_denied(request, token_payload.get("sub"), f"Access denied to {model_name} data")
                        raise HTTPException(
                            status_code=403, 
                            detail="Access denied to advertisements data"
                        )
            
            result = client.execute_query(model_name, query_params)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {mcp_request.name}")
        
        # Log successful operation
        audit_logger.log_api_request(
            request=request,
            response=Response(status_code=200),
            processing_time_ms=0,  # Would calculate actual time in production
            user_id=token_payload.get("sub"),
            client_id=token_payload.get("client_id"),
            success=True,
            details={
                "tool_name": mcp_request.name,
                "scopes_required": [required_scope],
                "scopes_granted": token_payload.get("scope", "").split()
            }
        )
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "tool": mcp_request.name,
            "user": token_payload.get("sub"),
            "result": result
        }
            
    except Exception as e:
        # Log failed operation
        audit_logger.log_api_request(
            request=request,
            response=Response(status_code=500),
            processing_time_ms=0,
            user_id=token_payload.get("sub"),
            client_id=token_payload.get("client_id"),
            success=False,
            details={
                "tool_name": mcp_request.name,
                "error": str(e)
            }
        )
        
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "tool": mcp_request.name,
            "user": token_payload.get("sub"),
            "error": str(e)
        }

@app.post("/mcp/list_tools")
async def list_tools_secure(
    request: MCPListToolsRequest,
    token_payload: Dict[str, Any] = Depends(require_oauth_token_enhanced)
):
    """List available MCP tools with security filtering"""
    
    user_role = token_payload.get("role", "clerk")
    user_scopes = token_payload.get("scope", "").split()
    
    # Base tools available to all authenticated users
    tools = []
    
    # Add tools based on user permissions
    if "read:all" in user_scopes or user_role == "executive":
        tools.extend([
            {
                "name": "get_all_models",
                "description": "Retrieve all Boomi DataHub models",
                "required_scope": "read:all"
            },
            {
                "name": "get_model_details",
                "description": "Get detailed information about a specific model",
                "required_scope": "read:all"
            },
            {
                "name": "execute_query",
                "description": "Execute a query against a Boomi DataHub model",
                "required_scope": "read:all"
            }
        ])
    elif "read:advertisements" in user_scopes:
        tools.append({
            "name": "get_all_models",
            "description": "Retrieve all Boomi DataHub models",
            "required_scope": "read:advertisements"
        })
    else:
        # Users with no permissions still see limited tool list
        tools.append({
            "name": "get_all_models", 
            "description": "Retrieve all Boomi DataHub models",
            "required_scope": "read:all",
            "note": "Access denied - insufficient permissions"
        })
    
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "user": token_payload.get("sub"),
        "user_role": user_role,
        "user_scopes": user_scopes,
        "tools": tools
    }

# Admin endpoints for security monitoring
@app.get("/admin/security/stats")
async def get_security_stats(token_payload: Dict[str, Any] = Depends(require_oauth_token_enhanced)):
    """Get comprehensive security statistics (admin only)"""
    
    # Check admin permissions
    if token_payload.get("role") != "executive":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "rate_limiting": rate_limiter.get_rate_limit_stats(),
        "token_revocation": get_revocation_stats(),
        "jailbreak_detection": jailbreak_detector.get_detection_stats(),
        "audit_logging": {
            "log_directory": "logs/audit",
            "active": True
        }
    }

# Health check endpoint (no auth required)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Boomi DataHub MCP Server - Enterprise Security Edition",
        "version": "6.1.0",
        "security_features": [
            "oauth2.1_authentication",
            "comprehensive_audit_logging", 
            "token_revocation_rfc7009",
            "rate_limiting_ddos_protection",
            "jailbreak_detection",
            "prompt_injection_protection"
        ]
    }

# Rate limit test endpoint (for testing purposes)
@app.get("/test/rate-limit")
async def rate_limit_test(request: Request):
    """Test endpoint with strict rate limiting - NOT whitelisted"""
    client_ip = request.headers.get("X-Forwarded-For", 
                request.headers.get("X-Real-IP", 
                request.client.host if request.client else "unknown"))
    
    return {
        "message": "Rate limit test endpoint",
        "client_ip": client_ip,
        "timestamp": datetime.now().isoformat(),
        "note": "This endpoint has strict rate limits for testing"
    }

# Enhanced server info endpoint
@app.get("/")
async def server_info():
    """Enhanced server information endpoint"""
    return {
        "name": "Boomi DataHub MCP Server - Enterprise Security Edition",
        "version": "6.1.0",
        "description": "Production-ready MCP server with comprehensive security features",
        "security_features": {
            "authentication": "OAuth 2.1 with PKCE",
            "authorization": "Role-Based Access Control (RBAC)",
            "audit_logging": "Comprehensive audit trail",
            "token_management": "RFC 7009 token revocation",
            "rate_limiting": "Multi-tier DDoS protection",
            "threat_detection": "Jailbreak and prompt injection detection",
            "security_headers": "OWASP recommended headers"
        },
        "endpoints": {
            "oauth_metadata": "/.well-known/oauth-authorization-server",
            "oauth_register": "/oauth/register",
            "oauth_authorize": "/oauth/authorize", 
            "oauth_token": "/oauth/token",
            "oauth_revoke": "/oauth/revoke",
            "mcp_endpoints": "/mcp/*",
            "admin_security": "/admin/security/*",
            "health": "/health",
            "documentation": "/docs"
        },
        "demo_users": {
            "martha.stewart": "Executive - Full Access (read:all)",
            "alex.smith": "Clerk - No Access (none)"
        },
        "compliance": [
            "OAuth 2.1 (RFC 6749, RFC 7636)",
            "Token Revocation (RFC 7009)",
            "MCP Specification",
            "OWASP Security Guidelines"
        ]
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Server startup event"""
    log_server_startup()

@app.on_event("shutdown") 
async def shutdown_event():
    """Server shutdown event"""
    log_server_shutdown()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)