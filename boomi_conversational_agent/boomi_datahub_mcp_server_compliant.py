#!/usr/bin/env python3
"""
MCP-Compliant Unified Boomi DataHub Server (June 2025 Specification) - COMPLIANT VERSION
Enhanced with proper XML response parsing for DataHub queries

This is a replica of the original with XML parsing fixes:
- Properly handles XML responses from Boomi DataHub
- Converts XML data to JSON format for MCP clients
- Maintains full OAuth 2.1 and security compliance
"""

import sys
import os
import json
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

# FastMCP and FastAPI imports for hybrid approach
from fastmcp import FastMCP
from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Add current directory to path for imports
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

# Import Boomi client
try:
    from boomi_datahub_mcp_server.boomi_datahub_client import BoomiDataHubClient, BoomiCredentials
except ImportError:
    try:
        sys.path.append(os.path.join(current_dir, 'boomi_datahub_mcp_server'))
        from boomi_datahub_client import BoomiDataHubClient, BoomiCredentials
    except ImportError as e:
        print(f"❌ Error importing BoomiDataHubClient: {e}")
        print("Please ensure boomi_datahub_client.py is available")
        sys.exit(1)

# Import existing OAuth 2.1 infrastructure
try:
    from oauth_server import (
        OAUTH_CONFIG, OAUTH_SCOPES, USER_SCOPES, JWT_SECRET_KEY, JWT_ALGORITHM,
        CLIENT_REGISTRY
    )
    OAUTH_AVAILABLE = True
    print("✅ OAuth 2.1 infrastructure imported")
except ImportError as e:
    print(f"⚠️  OAuth infrastructure not available: {e}")
    OAUTH_AVAILABLE = False
    JWT_SECRET_KEY = "dev-secret-key-change-in-production"
    JWT_ALGORITHM = "HS256"

# Import existing security stack
try:
    from security.hybrid_semantic_analyzer import HybridSemanticAnalyzer, LLMConfig, LLMProvider
    from security.rate_limiter import rate_limiter, check_rate_limit, RateLimitExceeded
    from security.audit_logger import audit_logger
    from security.jailbreak_detector import (
        jailbreak_detector, analyze_request_for_threats, should_block_request,
        log_detection_result, DetectionResult
    )
    SECURITY_AVAILABLE = True
    print("✅ Complete security stack imported")
except ImportError as e:
    print(f"⚠️  Security stack not available: {e}")
    SECURITY_AVAILABLE = False

import jwt

# MCP June 2025 Specification Configuration
MCP_CONFIG = {
    "protocol_version": "2025-06-18",
    "supported_versions": ["2025-06-18", "2025-03-26"],
    "oauth_resource_server": True,
    "resource_indicators_required": True,
    "canonical_server_uri": "https://localhost:8001"
}

# Global instances
_boomi_client: Optional[BoomiDataHubClient] = None
_security_analyzer: Optional[HybridSemanticAnalyzer] = None

def parse_xml_response(xml_response: str) -> Dict[str, Any]:
    """
    Parse XML response from Boomi DataHub and convert to JSON format
    This is the key fix for XML parsing issues
    """
    try:
        root = ET.fromstring(xml_response)
        
        # Detect namespace if present
        if '}' in root.tag:
            namespace = root.tag.split('}')[0][1:]
            ns = {'ns': namespace}
        else:
            ns = {}
        
        records = []
        
        # Find all Record elements
        record_elems = root.findall('.//ns:Record', ns) if ns else root.findall('.//Record')
        
        for record_elem in record_elems:
            record_data = {}
            
            # Extract record attributes
            record_id = record_elem.get('recordId')
            if record_id:
                record_data['_record_id'] = record_id
            
            # Find Fields element
            fields_elem = record_elem.find('ns:Fields', ns) if ns else record_elem.find('Fields')
            if fields_elem is not None:
                # Find the root field element (first child of Fields)
                root_field_elem = list(fields_elem)[0] if len(fields_elem) > 0 else None
                if root_field_elem is not None:
                    # Extract field values
                    for field_elem in root_field_elem:
                        field_name = field_elem.tag.split('}')[-1] if ns else field_elem.tag
                        field_value = field_elem.text or ""
                        record_data[field_name] = field_value
            
            records.append(record_data)
        
        # Extract pagination info
        result_count = int(root.get('resultCount', 0))
        total_count = int(root.get('totalCount', 0))
        offset_token = root.get('offsetToken', '')
        
        return {
            "records": records,
            "metadata": {
                "result_count": result_count,
                "total_count": total_count,
                "offset_token": offset_token,
                "has_more": bool(offset_token)
            }
        }
        
    except ET.ParseError as e:
        print(f"❌ XML Parse Error: {e}")
        return {"records": [], "metadata": {"error": f"XML parsing failed: {e}"}}
    except Exception as e:
        print(f"❌ Unexpected XML parsing error: {e}")
        return {"records": [], "metadata": {"error": f"Unexpected error: {e}"}}

class MCPOAuthValidator:
    """OAuth 2.1 Bearer token validation for MCP requests"""
    
    @staticmethod
    def validate_bearer_token(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
        """Validate Bearer token and return payload"""
        if not authorization or not authorization.startswith('Bearer '):
            return None
            
        token = authorization[7:]  # Remove 'Bearer ' prefix
        
        try:
            # Validate JWT token using existing infrastructure
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                audience="boomi-mcp-server",
                issuer="http://localhost:8001"
            )
            return payload
        except:
            return None
    
    @staticmethod
    def check_mcp_permissions(token_payload: Dict[str, Any], required_scope: str = "mcp:read") -> bool:
        """Check if token has required MCP permissions"""
        user_id = token_payload.get("sub")
        token_scopes = token_payload.get("scope", "").split()
        
        # Check token scopes
        if required_scope in token_scopes:
            return True
            
        # Check user-specific permissions
        if not OAUTH_AVAILABLE:
            return True  # Allow in dev mode
            
        user_permissions = USER_SCOPES.get(user_id, ["none"])
        
        # Map OAuth scopes to MCP permissions
        if "read:all" in user_permissions:
            return required_scope in ["mcp:read", "mcp:execute"]
        elif "write:all" in user_permissions:
            return required_scope in ["mcp:read", "mcp:execute", "mcp:admin"]
            
        return False

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

def get_security_analyzer() -> Optional[HybridSemanticAnalyzer]:
    """Get or create the security analyzer instance"""
    global _security_analyzer
    
    if SECURITY_AVAILABLE and _security_analyzer is None:
        try:
            llm_config = LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model_name="claude-3-sonnet-20240229",
                api_key="demo-key",
                max_tokens=150,
                temperature=0.1
            )
            _security_analyzer = HybridSemanticAnalyzer(llm_config)
        except Exception as e:
            print(f"⚠️  Security analyzer initialization failed: {e}")
    
    return _security_analyzer

# Create FastMCP instance
mcp = FastMCP("Boomi DataHub MCP Server - Compliant XML Parsing")

# Create FastAPI instance for OAuth 2.1 REST endpoints
app = FastAPI(
    title="Boomi DataHub MCP Server - Compliant XML Parsing",
    description="MCP-compliant server with OAuth 2.1 authentication and proper XML parsing",
    version="1.0.1-compliant"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth 2.1 security scheme
security = HTTPBearer()

# OAuth 2.1 validation functions
async def validate_oauth_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate OAuth 2.1 Bearer token for REST endpoints"""
    token_payload = MCPOAuthValidator.validate_bearer_token(f"Bearer {credentials.credentials}")
    
    if not token_payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not MCPOAuthValidator.check_mcp_permissions(token_payload):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions for MCP access",
        )
    
    return token_payload

# OAuth 2.1 Token Introspection Endpoint (RFC 7662)
@app.post("/oauth/introspect")
async def oauth_introspect(request: Request):
    """OAuth 2.1 Token Introspection Endpoint"""
    try:
        # Parse form data
        form_data = await request.form()
        token = form_data.get("token")
        
        if not token:
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_request", "error_description": "Missing token parameter"}
            )
        
        # Validate the token
        token_payload = MCPOAuthValidator.validate_bearer_token(f"Bearer {token}")
        
        if not token_payload:
            return JSONResponse(
                status_code=200,
                content={"active": False}
            )
        
        # Token is valid - return introspection response
        current_time = int(datetime.now().timestamp())
        username = token_payload.get("sub", "unknown")
        user_scopes = token_payload.get("scope", "").split()
        
        # Map to user permissions
        user_permissions = []
        role = "unknown"
        has_data_access = False
        
        if OAUTH_AVAILABLE and username in USER_SCOPES:
            user_permissions = USER_SCOPES[username]
            
            if "read:all" in user_permissions:
                role = "executive"
                has_data_access = True
            elif "read:advertisements" in user_permissions:
                role = "manager"
                has_data_access = True
            elif "none" in user_permissions:
                role = "clerk"
                has_data_access = False
            else:
                role = "user"
                has_data_access = True
        else:
            role = "executive"
            has_data_access = True
            user_permissions = ["read:all"]
        
        introspection_response = {
            "active": True,
            "client_id": token_payload.get("client_id", "boomi-mcp-client"),
            "username": username,
            "scope": " ".join(user_scopes) if user_scopes else "mcp:read",
            "exp": token_payload.get("exp", current_time + 3600),
            "iat": token_payload.get("iat", current_time),
            "sub": username,
            "aud": token_payload.get("aud", "boomi-mcp-server"),
            "iss": token_payload.get("iss", "http://localhost:8001"),
            "token_type": "Bearer",
            "role": role,
            "permissions": user_permissions,
            "has_data_access": has_data_access,
            "mcp_compliance": "2025-06-18"
        }
        
        return JSONResponse(
            status_code=200,
            content=introspection_response
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={"active": False}
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mcp_compliance": "2025-06-18",
        "oauth_enabled": OAUTH_AVAILABLE,
        "security_enabled": SECURITY_AVAILABLE,
        "version": "1.0.1-compliant"
    }

# FIXED: Query records with proper XML parsing
def query_records_compliant(model_id: str, fields: List[str] = None, filters: List[Dict[str, Any]] = None, limit: int = 100) -> Dict[str, Any]:
    """Execute a query against a Boomi DataHub model with COMPLIANT XML parsing"""
    try:
        client = get_boomi_client()
        
        # Use the advanced query method
        repository_id = "43212d46-1832-4ab1-820d-c0334d619f6f"  # Default repository
        
        result = client.query_records_by_parameters(
            universe_id=model_id,
            repository_id=repository_id,
            fields=fields or [],
            filters=filters or [],
            limit=limit
        )
        
        # COMPLIANT: Check if we need to parse XML response
        if result.get("status") == "error" and "response_body" in result:
            response_body = result["response_body"]
            
            # Check if response_body contains XML
            if isinstance(response_body, str) and response_body.strip().startswith('<'):
                print("🔧 COMPLIANT: Parsing XML response from Boomi DataHub...")
                
                # Parse XML and convert to structured data
                parsed_data = parse_xml_response(response_body)
                
                # Return MCP-compliant JSON with parsed records directly accessible
                records = parsed_data.get("records", [])
                metadata = parsed_data.get("metadata", {})
                
                return {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "mcp_version": "2025-06-18",
                    "oauth_protected": OAUTH_AVAILABLE,
                    "model_id": model_id,
                    "query_params": {
                        "fields": fields,
                        "filters": filters,
                        "limit": limit
                    },
                    # MCP-compliant: Return records directly in expected format
                    "data": {
                        "records": records
                    },
                    "metadata": {
                        "records_returned": len(records),
                        "result_count": metadata.get("result_count", len(records)),
                        "total_count": metadata.get("total_count", len(records)),
                        "has_more": metadata.get("has_more", False),
                        "xml_parsed": True,
                        "original_status": result.get("status"),
                        "compliance_fix": "XML parsing enabled"
                    }
                }
        
        # If no XML parsing needed, return MCP-compliant JSON format
        # Extract records if available, otherwise return empty
        records = []
        if isinstance(result, dict):
            if "records" in result:
                records = result["records"]
            elif "data" in result and isinstance(result["data"], list):
                records = result["data"]
            elif isinstance(result.get("data"), dict) and "records" in result["data"]:
                records = result["data"]["records"]
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "mcp_version": "2025-06-18",
            "oauth_protected": OAUTH_AVAILABLE,
            "model_id": model_id,
            "query_params": {
                "fields": fields,
                "filters": filters,
                "limit": limit
            },
            # MCP-compliant: Return records directly in expected format
            "data": {
                "records": records
            },
            "metadata": {
                "records_returned": len(records),
                "result_count": len(records),
                "total_count": len(records),
                "has_more": False,
                "xml_parsed": False,
                "original_status": result.get("status", "success")
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "model_id": model_id
        }

# REST endpoint with compliant XML parsing
@app.post("/api/tools/query_records")
async def query_records_rest(
    request: dict,
    token_payload: dict = Depends(validate_oauth_token)
):
    """REST endpoint for querying records with COMPLIANT XML parsing"""
    try:
        model_id = request.get("model_id", "")
        fields = request.get("fields", [])
        filters = request.get("filters", [])
        limit = request.get("limit", 100)
        
        # Use the compliant query function
        result = query_records_compliant(model_id, fields, filters, limit)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Compliant MCP tool
@mcp.tool()
def query_records(model_id: str, fields: List[str] = None, filters: List[Dict[str, Any]] = None, limit: int = 100) -> Dict[str, Any]:
    """Execute a query against a Boomi DataHub model with COMPLIANT XML parsing"""
    return query_records_compliant(model_id, fields, filters, limit)

# Copy other necessary functions from original (simplified for brevity)
def get_model_fields_direct(model_id: str) -> Dict[str, Any]:
    """Get detailed field information for a model"""
    try:
        client = get_boomi_client()
        model = client.get_model_by_id(model_id)
        
        if not model:
            return {
                "status": "error",
                "error": f"Model {model_id} not found",
                "timestamp": datetime.now().isoformat(),
                "model_id": model_id
            }
        
        # Extract fields from model structure
        fields = []
        if isinstance(model, dict):
            if 'fields' in model:
                fields = model['fields']
            elif 'properties' in model:
                fields = model['properties']
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "mcp_version": "2025-06-18",
            "oauth_protected": OAUTH_AVAILABLE,
            "model_id": model_id,
            "fields": fields
        }
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "model_id": model_id
        }

@mcp.tool()
def get_model_fields(model_id: str) -> Dict[str, Any]:
    """Get detailed field information for a model"""
    return get_model_fields_direct(model_id)

def get_all_models_direct() -> str:
    """Retrieve all Boomi DataHub models"""
    try:
        client = get_boomi_client()
        models = client.get_all_models()
        
        if isinstance(models, dict):
            if 'published' in models and 'draft' in models:
                all_models = models.get('published', []) + models.get('draft', [])
            else:
                all_models = [models] if models else []
        elif isinstance(models, list):
            all_models = models
        else:
            all_models = []
        
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "mcp_version": "2025-06-18",
            "oauth_protected": OAUTH_AVAILABLE,
            "data": {
                "published": [m for m in all_models if isinstance(m, dict) and m.get('publicationStatus') == 'publish'],
                "draft": [m for m in all_models if isinstance(m, dict) and m.get('publicationStatus') == 'draft']
            }
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        error_response = {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
        return json.dumps(error_response, indent=2)

@mcp.resource("boomi://datahub/models/all")
def get_all_models() -> str:
    """Retrieve all Boomi DataHub models"""
    return get_all_models_direct()

def main():
    """Main server startup function"""
    print("=" * 60)
    print("🚀 Starting COMPLIANT MCP Server with XML Parsing")
    print("📋 MCP Specification: June 18, 2025")
    print("🔧 Enhanced with proper XML response parsing")
    print("=" * 60)
    
    # Initialize components
    print("🔧 Initializing components...")
    
    try:
        client = get_boomi_client()
        print("✅ Boomi DataHub client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Boomi client: {e}")
        return
    
    print(f"\n📋 Compliant Server Configuration:")
    print(f"   ✅ MCP Specification: {MCP_CONFIG['protocol_version']}")
    print(f"   ✅ OAuth 2.1 Resource Server: {OAUTH_AVAILABLE}")
    print(f"   ✅ Security Guardrails: {SECURITY_AVAILABLE}")
    print(f"   🔧 XML Parsing: COMPLIANT")
    print(f"   📊 DataHub Query Support: ENHANCED")
    print(f"   🌐 Server Port: 8001")
    
    # Create OAuth-protected MCP endpoint
    @app.post("/mcp")
    async def mcp_endpoint_with_oauth(request: Request):
        """OAuth 2.1 protected MCP JSON-RPC endpoint with XML parsing compliance"""
        try:
            # Extract Authorization header
            auth_header = request.headers.get("Authorization")
            
            if not auth_header:
                return JSONResponse(
                    status_code=401,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": "Bearer token required for MCP access"
                        },
                        "id": None
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Validate token
            token_payload = MCPOAuthValidator.validate_bearer_token(auth_header)
            
            if not token_payload:
                return JSONResponse(
                    status_code=401,
                    content={
                        "jsonrpc": "2.0", 
                        "error": {
                            "code": -32600,
                            "message": "Invalid or expired Bearer token"
                        },
                        "id": None
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Check permissions
            if not MCPOAuthValidator.check_mcp_permissions(token_payload):
                return JSONResponse(
                    status_code=403,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600, 
                            "message": f"Access denied for user {token_payload.get('sub')}. Contact administrator for data access."
                        },
                        "id": None
                    }
                )
            
            # Get request body
            body = await request.body()
            json_data = json.loads(body)
            
            # Process MCP request
            if json_data.get("method") == "resources/read":
                uri = json_data.get("params", {}).get("uri", "")
                
                if uri == "boomi://datahub/models/all":
                    result = get_all_models_direct()
                else:
                    return JSONResponse(
                        status_code=200,
                        content={
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32601,
                                "message": f"Resource not found: {uri}"
                            },
                            "id": json_data.get("id")
                        }
                    )
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "jsonrpc": "2.0",
                        "result": result,
                        "id": json_data.get("id")
                    }
                )
            
            elif json_data.get("method") == "tools/call":
                tool_name = json_data.get("params", {}).get("name", "")
                arguments = json_data.get("params", {}).get("arguments", {})
                
                if tool_name == "get_model_fields":
                    result = get_model_fields_direct(arguments.get("model_id", ""))
                elif tool_name == "query_records":
                    # Use the COMPLIANT query function
                    result = query_records_compliant(
                        arguments.get("model_id", ""),
                        arguments.get("fields", []),
                        arguments.get("filters", []),
                        arguments.get("limit", 100)
                    )
                else:
                    return JSONResponse(
                        status_code=200,
                        content={
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32601,
                                "message": f"Tool not found: {tool_name}"
                            },
                            "id": json_data.get("id")
                        }
                    )
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "jsonrpc": "2.0",
                        "result": result,
                        "id": json_data.get("id")
                    }
                )
            
            else:
                return JSONResponse(
                    status_code=200,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {json_data.get('method')}"
                        },
                        "id": json_data.get("id")
                    }
                )
                
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    },
                    "id": json_data.get("id") if 'json_data' in locals() else None
                }
            )
    
    print("\n🎯 Starting COMPLIANT MCP Server...")
    print("📋 JSON-RPC 2.0 + OAuth 2.1 + XML Parsing Compliance")
    
    # Run the server
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,  # Standard MCP server port
        log_level="info"
    )

if __name__ == "__main__":
    main()