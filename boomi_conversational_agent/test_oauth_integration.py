"""
OAuth 2.1 Integration Tests
Phase 6A: Test OAuth flow with demo personas

This test suite validates the OAuth 2.1 implementation with:
- Martha Stewart (Executive) - Full access
- Alex Smith (Clerk) - No access
"""

import requests
import json
import base64
import hashlib
import secrets
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any

# Test configuration
SERVER_URL = "http://localhost:8001"
OAUTH_BASE_URL = f"{SERVER_URL}"
MCP_BASE_URL = f"{SERVER_URL}/mcp"

# Demo personas
DEMO_USERS = {
    "martha.stewart": {
        "name": "Martha Stewart",
        "role": "executive",
        "expected_scopes": ["read:all", "write:all"],
        "should_have_access": True
    },
    "alex.smith": {
        "name": "Alex Smith", 
        "role": "clerk",
        "expected_scopes": ["none"],
        "should_have_access": False
    }
}

def generate_pkce_pair():
    """Generate PKCE code_verifier and code_challenge"""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

class OAuthTestClient:
    """Test client for OAuth 2.1 flow"""
    
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.access_token = None
        self.refresh_token = None
        
    def register_client(self, user_id: str = "martha.stewart") -> Dict[str, Any]:
        """Register OAuth client"""
        # Create user-specific client names to trigger different user assignment
        client_name = f"Alex Smith Client" if user_id == "alex.smith" else "Martha Stewart Client"
        
        registration_data = {
            "redirect_uris": ["http://localhost:3000/callback"],
            "client_name": client_name,
            "client_uri": "http://localhost:3000",
            "scope": "read:all write:all",
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"]
        }
        
        response = requests.post(
            f"{OAUTH_BASE_URL}/oauth/register",
            json=registration_data
        )
        
        if response.status_code == 200:
            client_data = response.json()
            self.client_id = client_data["client_id"]
            self.client_secret = client_data["client_secret"]
            return {"success": True, "data": client_data}
        else:
            return {"success": False, "error": response.text}
    
    def get_authorization_url(self, user_id: str = "martha.stewart") -> str:
        """Generate authorization URL with PKCE"""
        code_verifier, code_challenge = generate_pkce_pair()
        self.code_verifier = code_verifier
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": "http://localhost:3000/callback",
            "scope": "read:all",
            "state": f"test_state_{user_id}",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        url = f"{OAUTH_BASE_URL}/oauth/authorize?" + "&".join([f"{k}={v}" for k, v in params.items()])
        return url
    
    def simulate_authorization(self, user_id: str = "martha.stewart") -> Dict[str, Any]:
        """Simulate authorization flow"""
        # In a real scenario, user would be redirected to auth server
        # Here we directly call the authorization endpoint
        response = requests.get(self.get_authorization_url(user_id), allow_redirects=False)
        
        if response.status_code in [302, 307]:  # Accept both redirect codes
            # Extract authorization code from redirect
            redirect_url = response.headers.get("Location")
            parsed_url = urlparse(redirect_url)
            query_params = parse_qs(parsed_url.query)
            
            if "code" in query_params:
                auth_code = query_params["code"][0]
                return {"success": True, "code": auth_code}
            else:
                return {"success": False, "error": "No authorization code in redirect"}
        else:
            return {"success": False, "error": f"Authorization failed: {response.status_code} - {response.text}"}
    
    def exchange_code_for_token(self, auth_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": "http://localhost:3000/callback",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code_verifier": self.code_verifier
        }
        
        response = requests.post(
            f"{OAUTH_BASE_URL}/oauth/token",
            json=token_data
        )
        
        if response.status_code == 200:
            token_response = response.json()
            self.access_token = token_response["access_token"]
            self.refresh_token = token_response.get("refresh_token")
            return {"success": True, "data": token_response}
        else:
            return {"success": False, "error": response.text}
    
    def test_mcp_endpoint(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test MCP endpoint with OAuth token"""
        if not self.access_token:
            return {"success": False, "error": "No access token"}
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        if data is None:
            data = {}
        
        response = requests.post(f"{MCP_BASE_URL}/{endpoint}", headers=headers, json=data)
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        }

def test_oauth_server_metadata():
    """Test OAuth server metadata endpoint"""
    print("🧪 Testing OAuth Server Metadata...")
    
    response = requests.get(f"{OAUTH_BASE_URL}/.well-known/oauth-authorization-server")
    
    if response.status_code == 200:
        metadata = response.json()
        print("✅ OAuth server metadata retrieved successfully")
        print(f"   Issuer: {metadata.get('issuer')}")
        print(f"   Supported scopes: {metadata.get('scopes_supported')}")
        return True
    else:
        print("❌ Failed to retrieve OAuth server metadata")
        return False

def test_client_registration():
    """Test dynamic client registration"""
    print("\n🧪 Testing Client Registration...")
    
    client = OAuthTestClient()
    result = client.register_client()
    
    if result["success"]:
        print("✅ Client registration successful")
        print(f"   Client ID: {client.client_id}")
        return client
    else:
        print("❌ Client registration failed")
        print(f"   Error: {result['error']}")
        return None

def test_oauth_flow_for_user(client: OAuthTestClient, user_id: str):
    """Test complete OAuth flow for specific user"""
    print(f"\n🧪 Testing OAuth Flow for {DEMO_USERS[user_id]['name']}...")
    
    # Register user-specific client
    register_result = client.register_client(user_id)
    if not register_result["success"]:
        print(f"❌ Client registration failed for {user_id}")
        return False
    
    # Step 1: Get authorization
    auth_result = client.simulate_authorization(user_id)
    if not auth_result["success"]:
        print(f"❌ Authorization failed: {auth_result['error']}")
        return False
    
    auth_code = auth_result["code"]
    print(f"✅ Authorization code obtained: {auth_code[:10]}...")
    
    # Step 2: Exchange code for token
    token_result = client.exchange_code_for_token(auth_code)
    if not token_result["success"]:
        print(f"❌ Token exchange failed: {token_result['error']}")
        return False
    
    token_data = token_result["data"]
    print(f"✅ Access token obtained: {token_data['access_token'][:20]}...")
    print(f"   Token type: {token_data['token_type']}")
    print(f"   Expires in: {token_data['expires_in']} seconds")
    print(f"   Scope: {token_data['scope']}")
    
    return True

def test_mcp_endpoints(client: OAuthTestClient, user_id: str):
    """Test MCP endpoints with OAuth authentication"""
    print(f"\n🧪 Testing MCP Endpoints for {DEMO_USERS[user_id]['name']}...")
    
    user_info = DEMO_USERS[user_id]
    
    # Test 1: List tools
    print("   Testing list_tools...")
    result = client.test_mcp_endpoint("list_tools", {})
    if result["success"]:
        tools = result["data"].get("tools", [])
        print(f"   ✅ List tools successful - {len(tools)} tools available")
        for tool in tools:
            print(f"      - {tool['name']}: {tool['description']}")
    else:
        print(f"   ❌ List tools failed: {result['status_code']}")
    
    # Test 2: Get all models
    print("   Testing get_all_models...")
    result = client.test_mcp_endpoint("call_tool", {
        "name": "get_all_models",
        "arguments": {}
    })
    
    if user_info["should_have_access"]:
        if result["success"]:
            print("   ✅ Get all models successful")
        else:
            print(f"   ❌ Get all models failed (but should have succeeded): {result['status_code']}")
    else:
        if result["success"]:
            print("   ❌ Get all models succeeded (but should have failed)")
        else:
            print(f"   ✅ Get all models correctly denied: {result['status_code']}")
    
    # Test 3: Execute query (should be blocked for Alex Smith)
    print("   Testing execute_query...")
    result = client.test_mcp_endpoint("call_tool", {
        "name": "execute_query",
        "arguments": {
            "model_name": "Advertisements",
            "query_params": {}
        }
    })
    
    if user_info["should_have_access"]:
        if result["success"]:
            print("   ✅ Execute query successful")
        else:
            print(f"   ❌ Execute query failed (but should have succeeded): {result['status_code']}")
    else:
        if result["success"]:
            print("   ❌ Execute query succeeded (but should have failed)")
        else:
            print(f"   ✅ Execute query correctly denied: {result['status_code']}")

def main():
    """Run all OAuth integration tests"""
    print("🚀 OAuth 2.1 Integration Tests")
    print("=" * 50)
    
    # Test 1: OAuth server metadata
    if not test_oauth_server_metadata():
        print("❌ OAuth server metadata test failed. Is the server running?")
        return
    
    # Test 2: Client registration
    client = test_client_registration()
    if not client:
        print("❌ Client registration failed. Cannot continue.")
        return
    
    # Test 3: OAuth flows for both users (each gets their own client)
    for user_id in DEMO_USERS.keys():
        user_client = OAuthTestClient()  # Create separate client for each user
        if test_oauth_flow_for_user(user_client, user_id):
            test_mcp_endpoints(user_client, user_id)
        else:
            print(f"❌ OAuth flow failed for {user_id}")
    
    print("\n🎉 OAuth 2.1 Integration Tests Complete")

if __name__ == "__main__":
    main()