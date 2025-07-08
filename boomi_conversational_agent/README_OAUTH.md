# OAuth 2.1 MCP Server - Quick Start Guide

**🚀 Enterprise OAuth 2.1 Implementation for Boomi DataHub MCP Server**

## Quick Start

### 1. Setup
```bash
# Clone and navigate to project
cd boomi_conversational_agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Server
```bash
python run_oauth_server.py
```

### 3. Test Implementation
```bash
python test_oauth_integration.py
```

## Key Features ✅

- **OAuth 2.1 Authorization Server** with metadata discovery
- **PKCE Support** (RFC 7636) - S256 challenge method
- **Dynamic Client Registration** (RFC 7591)
- **JWT Token Validation** with audience/issuer verification  
- **Role-Based Access Control** - Executive vs Clerk permissions
- **MCP Specification Compliant** for HTTP transport

## Demo Users

### Martha Stewart (Executive)
- **Scope**: `read:all`
- **Access**: Full access to all MCP endpoints
- **Tools**: All 3 tools available

### Alex Smith (Clerk)  
- **Scope**: `none`
- **Access**: Denied with 403 Forbidden
- **Tools**: Limited listing only

## API Endpoints

```
OAuth 2.1:
├── /.well-known/oauth-authorization-server  # Metadata
├── /oauth/register                          # Client registration
├── /oauth/authorize                         # Authorization
├── /oauth/token                            # Token exchange
└── /oauth/jwks                             # Key set

MCP (OAuth Protected):
├── /mcp/call_tool                          # Execute tools
├── /mcp/list_tools                         # List tools
├── /mcp/list_resources                     # List resources
└── /mcp/read_resource                      # Read resources

Server:
├── /                                       # Server info
├── /health                                 # Health check  
└── /docs                                   # API docs
```

## Example Usage

### Get Access Token
```bash
# 1. Register client
curl -X POST http://localhost:8001/oauth/register \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_uris": ["http://localhost:3000/callback"],
    "client_name": "My App"
  }'

# 2. Authorization flow (with PKCE)
# Visit: /oauth/authorize?response_type=code&client_id=...

# 3. Exchange code for token
curl -X POST http://localhost:8001/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "authorization_code",
    "code": "auth_code",
    "client_id": "client_id",
    "code_verifier": "verifier"
  }'
```

### Use MCP API
```bash
# List available tools
curl -X POST http://localhost:8001/mcp/list_tools \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# Execute tool
curl -X POST http://localhost:8001/mcp/call_tool \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_all_models",
    "arguments": {}
  }'
```

## Test Results

```
✅ OAuth Server Metadata retrieved
✅ Client registration successful  
✅ Martha Stewart: Full access (read:all scope)
✅ Alex Smith: Properly denied (none scope)
✅ PKCE authorization flow working
✅ JWT token validation working
✅ Role-based access control working
```

## Files

- `oauth_server.py` - OAuth 2.1 authorization server
- `boomi_datahub_mcp_server_oauth.py` - MCP server with OAuth
- `run_oauth_server.py` - Server launcher
- `test_oauth_integration.py` - Integration tests
- `docs/OAUTH_2_1_IMPLEMENTATION.md` - Detailed documentation

## Status: ✅ Production Ready

**Version**: 6.0.0  
**MCP Compliant**: ✅  
**Security**: Enterprise-grade OAuth 2.1 with RBAC