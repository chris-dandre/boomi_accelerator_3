# OAuth 2.1 Implementation Plan for MCP Compliance

**Project**: Boomi DataHub Conversational AI Agent  
**Document**: OAuth 2.1 MCP Compliance Implementation Plan  
**Created**: 2025-07-03  
**Status**: Phase 6A Planning

## 🎯 **Executive Summary**

Following Anthropic's March 2025 MCP specification updates, our HTTP transport-based MCP server requires OAuth 2.1 compliance for production deployment. This document outlines the implementation strategy to upgrade our Phase 5 working foundation with enterprise-grade authentication.

## 📋 **Current State Analysis**

### **Transport Type Confirmation**
```python
# Our current implementation uses HTTP transport
class SyncBoomiMCPClient:
    def __init__(self):
        self.client = Client("http://127.0.0.1:8001/mcp/")  # HTTP = OAuth 2.1 Required

# FastAPI MCP Server (HTTP endpoints)
@app.post("/mcp/call_tool")      # Requires OAuth 2.1 compliance
@app.post("/mcp/list_tools")     # Requires OAuth 2.1 compliance
```

### **Compliance Gap**
- ❌ **OAuth 2.1 Authorization Server**: Not implemented
- ❌ **PKCE Support**: Not implemented  
- ❌ **Bearer Token Validation**: Not implemented
- ❌ **Authorization Server Metadata**: Not implemented
- ✅ **Working MCP Foundation**: 100% success rate on business queries

## 🔧 **Technical Implementation Plan**

### **Phase 6A: OAuth 2.1 Core Implementation**

#### **1. Authorization Server Endpoints**
```python
# New FastAPI endpoints to add
@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata():
    """Authorization server metadata (RFC8414)"""

@app.post("/oauth/register")  
async def register_client():
    """Dynamic client registration (RFC7591)"""

@app.get("/oauth/authorize")
async def authorize():
    """Authorization endpoint with PKCE support"""

@app.post("/oauth/token")
async def token_exchange():
    """Token endpoint with PKCE validation"""
```

#### **2. Enhanced MCP Endpoints**
```python
# Updated MCP endpoints with OAuth validation
@app.post("/mcp/call_tool")
@require_oauth_token  # New decorator
async def call_tool(request: Request):
    """Existing functionality + OAuth token validation"""

@app.post("/mcp/list_tools")  
@require_oauth_token
async def list_tools(request: Request):
    """Existing functionality + OAuth token validation"""
```

#### **3. PKCE Implementation**
```python
# PKCE code challenge/verifier handling
def generate_pkce_pair():
    """Generate code_verifier and code_challenge"""
    code_verifier = base64url_encode(os.urandom(32))
    code_challenge = base64url_encode(sha256(code_verifier))
    return code_verifier, code_challenge

def validate_pkce(code_verifier: str, code_challenge: str):
    """Validate PKCE code_verifier against stored code_challenge"""
```

### **Phase 6B: RBAC Integration**

#### **4. OAuth Scopes for Business Logic**
```python
# OAuth scopes mapped to business permissions
OAUTH_SCOPES = {
    "read:all": "Full read access to all models and fields",
    "write:all": "Full write access (future: data modification)",
    "read:advertisements": "Read access to Advertisements model only",
    "read:users": "Read access to users model only",
    "none": "No data access (registration denied)"
}

# User-scope mapping
USER_SCOPES = {
    "martha.stewart": ["read:all", "write:all"],  # Executive
    "alex.smith": ["none"]                        # Clerk - no access
}
```

#### **5. Token Claims Structure**
```python
# JWT token payload structure
{
    "sub": "martha.stewart",           # User identifier
    "client_id": "executive_client",   # OAuth client
    "scope": "read:all write:all",     # Granted permissions
    "role": "executive",               # Business role
    "aud": "boomi-mcp-server",         # Token audience
    "iss": "http://localhost:8001",    # Token issuer
    "exp": 1625097600,                 # Expiration timestamp
    "iat": 1625094000                  # Issued at timestamp
}
```

## 📊 **Implementation Dependencies**

### **New Python Dependencies**
```python
# Add to requirements.txt
authlib>=1.3.0              # OAuth 2.1 implementation
python-jose[cryptography]   # JWT token handling
httpx>=0.27.0               # Enhanced HTTP client  
cryptography>=41.0.0        # PKCE and token security
```

### **Configuration Updates**
```python
# OAuth 2.1 server configuration
OAUTH_CONFIG = {
    "issuer": "http://localhost:8001",
    "authorization_endpoint": "/oauth/authorize",
    "token_endpoint": "/oauth/token", 
    "registration_endpoint": "/oauth/register",
    "jwks_uri": "/oauth/jwks",
    "scopes_supported": ["read:all", "write:all", "read:advertisements", "read:users"],
    "grant_types_supported": ["authorization_code", "refresh_token"],
    "code_challenge_methods_supported": ["S256"],
    "token_endpoint_auth_methods_supported": ["client_secret_post", "none"]
}
```

## 🧪 **Testing Strategy**

### **OAuth 2.1 Compliance Tests**
```python
# Test suite structure
tests/test_phase6a_oauth/
├── test_authorization_server_metadata.py
├── test_dynamic_client_registration.py  
├── test_pkce_authorization_flow.py
├── test_token_exchange_validation.py
└── test_mcp_oauth_integration.py
```

### **Integration Test Scenarios**
1. **Authorization Server Discovery**: Metadata endpoint validation
2. **Client Registration**: Dynamic registration flow
3. **PKCE Authorization**: Code challenge/verifier validation
4. **Token Exchange**: JWT token generation and validation
5. **Authenticated MCP Calls**: Bearer token validation on existing endpoints

## 🎯 **Success Criteria**

### **Phase 6A Completion**
- ✅ **MCP Specification Compliance**: All OAuth 2.1 requirements met
- ✅ **PKCE Implementation**: Mandatory for all authorization flows  
- ✅ **Backward Compatibility**: Existing Phase 5 functionality preserved
- ✅ **Security Validation**: Comprehensive OAuth security testing

### **Phase 6B Completion**  
- ✅ **RBAC Integration**: OAuth scopes mapped to business permissions
- ✅ **User Persona Testing**: Martha Stewart (executive) vs Alex Smith (clerk)
- ✅ **Enterprise Ready**: Production-grade authentication and authorization

## 🚨 **Risk Mitigation**

### **Implementation Complexity**
- **Use proven libraries**: authlib for OAuth 2.1 implementation
- **Incremental approach**: Basic OAuth first, then advanced features
- **Comprehensive testing**: Test each component independently

### **Performance Impact**
- **Token caching**: Cache validated tokens to reduce overhead
- **Efficient validation**: Optimize JWT validation routines
- **Benchmarking**: Measure performance impact at each step

### **Enterprise Integration**
- **External IdP readiness**: Design for future identity provider integration
- **Configuration flexibility**: Support multiple authentication modes
- **Migration path**: Clear upgrade path from basic to enterprise authentication

## 📋 **Next Steps**

1. **Approve implementation plan** and resource allocation
2. **Set up development environment** with OAuth 2.1 dependencies
3. **Begin Phase 6A implementation** with authorization server endpoints
4. **Implement comprehensive test suite** for OAuth compliance validation
5. **Integration with Phase 5 foundation** while maintaining 100% success rate

---

*This implementation plan ensures enterprise-grade security compliance while preserving the working Phase 5 foundation and accelerator objectives.*