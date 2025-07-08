"""
Enhanced Boomi DataHub MCP Server with OAuth 2.1 Authentication
Phase 6A: OAuth 2.1 Integration

This enhanced MCP server integrates OAuth 2.1 authentication with existing MCP functionality.
Combines the original MCP server with OAuth authorization server endpoints.
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Import OAuth server components
from oauth_server import oauth_app, OAUTH_SCOPES, USER_SCOPES, JWT_SECRET_KEY, JWT_ALGORITHM
import jwt

# Try multiple import paths for boomi_datahub_client
try:
    # First try importing from the boomi_datahub_mcp_server directory
    sys.path.append(os.path.join(os.path.dirname(__file__), 'boomi_datahub_mcp_server'))
    from boomi_datahub_client import BoomiDataHubClient, BoomiCredentials
except ImportError:
    try:
        # Try importing from current directory
        from boomi_datahub_mcp_server.boomi_datahub_client import BoomiDataHubClient, BoomiCredentials
    except ImportError:
        try:
            # Try importing from ../boomi_datahub_mcp_server directory
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'boomi_datahub_mcp_server'))
            from boomi_datahub_client import BoomiDataHubClient, BoomiCredentials
        except ImportError as e:
            print(f"❌ Error importing BoomiDataHubClient: {e}")
            print("\n🔍 Troubleshooting Import Issues:")
            print("Please ensure boomi_datahub_client.py is accessible")
            sys.exit(1)

# Create the main FastAPI app
app = FastAPI(
    title="Boomi DataHub MCP Server with OAuth 2.1",
    description="Enhanced MCP server with OAuth 2.1 authentication for enterprise security",
    version="6.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include OAuth server endpoints
app.include_router(oauth_app, prefix="")

# Add OAuth endpoints directly to main app
from oauth_server import (
    oauth_metadata, register_client, authorize, token_exchange, jwks,
    ClientRegistrationRequest, TokenRequest
)

# Re-register OAuth endpoints on main app
app.get("/.well-known/oauth-authorization-server")(oauth_metadata)
app.post("/oauth/register")(register_client)
app.get("/oauth/authorize")(authorize)
app.post("/oauth/token")(token_exchange)
app.get("/oauth/jwks")(jwks)

# Global client instance
_boomi_client: Optional[BoomiDataHubClient] = None

def get_boomi_client() -> BoomiDataHubClient:
    """Get or create the Boomi DataHub client instance"""
    global _boomi_client
    
    if _boomi_client is None:
        try:
            _boomi_client = BoomiDataHubClient()
            
            # Test the connection
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

# Create our own token validation function
security = HTTPBearer()

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
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

def require_oauth_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """OAuth token validation decorator"""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    
    token = credentials.credentials
    
    try:
        payload = verify_jwt_token(token)
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

# Test endpoint for OAuth validation
@app.post("/mcp/test")
async def test_auth(request: Request):
    """Simple test endpoint for OAuth validation"""
    # Manual token extraction and validation
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization token")
    
    token = auth_header.split(" ")[1]
    
    try:
        payload = jwt.decode(
            token, 
            JWT_SECRET_KEY, 
            algorithms=[JWT_ALGORITHM],
            audience="boomi-mcp-server",
            issuer="http://localhost:8001"
        )
        return {"status": "success", "user": payload.get("sub"), "message": "OAuth working!"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# OAuth-protected MCP endpoints
@app.post("/mcp/call_tool")
async def call_tool(
    request: MCPToolRequest,
    token_payload: Dict[str, Any] = Depends(require_oauth_token)
):
    """Execute MCP tool with OAuth authentication"""
    
    # Validate permissions based on tool
    required_scope = "read:all"  # Default scope for most tools
    if not validate_user_permissions(token_payload, required_scope):
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied. Required scope: {required_scope}"
        )
    
    try:
        client = get_boomi_client()
        
        # Handle different tool types
        if request.name == "get_all_models":
            result = client.get_all_models()
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "tool": request.name,
                "user": token_payload.get("sub"),
                "result": result
            }
        
        elif request.name == "get_model_details":
            model_name = request.arguments.get("model_name")
            if not model_name:
                raise HTTPException(status_code=400, detail="model_name is required")
            
            result = client.get_model_details(model_name)
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "tool": request.name,
                "user": token_payload.get("sub"),
                "result": result
            }
        
        elif request.name == "execute_query":
            model_name = request.arguments.get("model_name")
            query_params = request.arguments.get("query_params", {})
            
            if not model_name:
                raise HTTPException(status_code=400, detail="model_name is required")
            
            # Check if user has permission for specific model
            if model_name.lower() == "advertisements":
                if not validate_user_permissions(token_payload, "read:advertisements"):
                    if not validate_user_permissions(token_payload, "read:all"):
                        raise HTTPException(
                            status_code=403, 
                            detail="Access denied to advertisements data"
                        )
            
            result = client.execute_query(model_name, query_params)
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "tool": request.name,
                "user": token_payload.get("sub"),
                "result": result
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {request.name}")
            
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "tool": request.name,
            "user": token_payload.get("sub"),
            "error": str(e)
        }

@app.post("/mcp/list_tools")
async def list_tools(
    request: MCPListToolsRequest,
    token_payload: Dict[str, Any] = Depends(require_oauth_token)
):
    """List available MCP tools with OAuth authentication"""
    
    user_role = token_payload.get("role", "clerk")
    user_scopes = token_payload.get("scope", "").split()
    
    # Base tools available to all authenticated users
    tools = [
        {
            "name": "get_all_models",
            "description": "Retrieve all Boomi DataHub models",
            "required_scope": "read:all"
        }
    ]
    
    # Add tools based on user permissions
    if "read:all" in user_scopes or user_role == "executive":
        tools.extend([
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
    
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "user": token_payload.get("sub"),
        "user_role": user_role,
        "user_scopes": user_scopes,
        "tools": tools
    }

@app.post("/mcp/list_resources")
async def list_resources(
    request: MCPListResourcesRequest,
    token_payload: Dict[str, Any] = Depends(require_oauth_token)
):
    """List available MCP resources with OAuth authentication"""
    
    user_scopes = token_payload.get("scope", "").split()
    
    resources = []
    
    # Add resources based on user permissions
    if "read:all" in user_scopes:
        resources.extend([
            {
                "uri": "boomi://datahub/models/all",
                "name": "All Models",
                "description": "All Boomi DataHub models",
                "mimeType": "application/json"
            },
            {
                "uri": "boomi://datahub/models/published",
                "name": "Published Models",
                "description": "Published Boomi DataHub models",
                "mimeType": "application/json"
            }
        ])
    
    if "read:advertisements" in user_scopes:
        resources.append({
            "uri": "boomi://datahub/models/advertisements",
            "name": "Advertisements Model",
            "description": "Advertisements data model",
            "mimeType": "application/json"
        })
    
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "user": token_payload.get("sub"),
        "resources": resources
    }

@app.post("/mcp/read_resource")
async def read_resource(
    request: MCPReadResourceRequest,
    token_payload: Dict[str, Any] = Depends(require_oauth_token)
):
    """Read MCP resource with OAuth authentication"""
    
    try:
        client = get_boomi_client()
        
        if request.uri == "boomi://datahub/models/all":
            if not validate_user_permissions(token_payload, "read:all"):
                raise HTTPException(status_code=403, detail="Access denied to all models")
            
            result = client.get_all_models()
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "uri": request.uri,
                "user": token_payload.get("sub"),
                "contents": [{"mimeType": "application/json", "text": json.dumps(result, indent=2)}]
            }
        
        elif request.uri == "boomi://datahub/models/published":
            if not validate_user_permissions(token_payload, "read:all"):
                raise HTTPException(status_code=403, detail="Access denied to published models")
            
            all_models = client.get_all_models()
            published_models = all_models.get("published", [])
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "uri": request.uri,
                "user": token_payload.get("sub"),
                "contents": [{"mimeType": "application/json", "text": json.dumps(published_models, indent=2)}]
            }
        
        else:
            raise HTTPException(status_code=404, detail=f"Resource not found: {request.uri}")
            
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "uri": request.uri,
            "user": token_payload.get("sub"),
            "error": str(e)
        }

# Health check endpoint (no auth required)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Boomi DataHub MCP Server with OAuth 2.1",
        "version": "6.0.0"
    }

# Server info endpoint (no auth required)
@app.get("/")
async def server_info():
    """Server information endpoint"""
    return {
        "name": "Boomi DataHub MCP Server with OAuth 2.1",
        "version": "6.0.0",
        "description": "Enterprise MCP server with OAuth 2.1 authentication and RBAC",
        "features": [
            "OAuth 2.1 Authorization Server",
            "PKCE Support (RFC 7636)", 
            "Dynamic Client Registration (RFC 7591)",
            "JWT Token Validation",
            "Role-Based Access Control",
            "MCP Specification Compliant"
        ],
        "endpoints": {
            "oauth_metadata": "/.well-known/oauth-authorization-server",
            "oauth_register": "/oauth/register",
            "oauth_authorize": "/oauth/authorize", 
            "oauth_token": "/oauth/token",
            "mcp_endpoints": "/mcp/*",
            "health": "/health",
            "documentation": "/docs"
        },
        "demo_users": {
            "martha.stewart": "Executive - Full Access (read:all)",
            "alex.smith": "Clerk - No Access (none)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)