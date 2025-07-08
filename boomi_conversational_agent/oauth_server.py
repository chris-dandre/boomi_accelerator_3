"""
OAuth 2.1 Authorization Server for Boomi MCP Server
Phase 6A: OAuth 2.1 Core Implementation

This module implements OAuth 2.1 authorization server endpoints
to ensure MCP specification compliance for HTTP transport.
"""

import os
import base64
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode, parse_qs

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2 import OAuth2Request
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc7636 import CodeChallenge


# OAuth 2.1 Configuration
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

# OAuth Scopes mapped to business permissions
OAUTH_SCOPES = {
    "read:all": "Full read access to all models and fields",
    "write:all": "Full write access (future: data modification)",
    "read:advertisements": "Read access to Advertisements model only",
    "read:users": "Read access to users model only",
    "none": "No data access (registration denied)"
}

# User-scope mapping for demo personas
USER_SCOPES = {
    "martha.stewart": ["read:all", "write:all"],  # Executive
    "alex.smith": ["none"]                        # Clerk - no access
}

# In-memory storage for demo purposes
# In production, use proper database storage
CLIENT_REGISTRY = {}
AUTHORIZATION_CODES = {}
ACCESS_TOKENS = {}
REFRESH_TOKENS = {}

# JWT signing key (generate new key for production)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


class ClientRegistrationRequest(BaseModel):
    """OAuth 2.1 Dynamic Client Registration Request"""
    redirect_uris: List[str]
    client_name: str
    client_uri: Optional[str] = None
    scope: Optional[str] = "read:all"
    grant_types: List[str] = ["authorization_code", "refresh_token"]
    response_types: List[str] = ["code"]
    
    
class ClientRegistrationResponse(BaseModel):
    """OAuth 2.1 Dynamic Client Registration Response"""
    client_id: str
    client_secret: Optional[str] = None
    client_id_issued_at: int
    client_secret_expires_at: int = 0
    redirect_uris: List[str]
    client_name: str
    client_uri: Optional[str] = None
    scope: str
    grant_types: List[str]
    response_types: List[str]


class TokenRequest(BaseModel):
    """OAuth 2.1 Token Request"""
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: str
    client_secret: Optional[str] = None
    code_verifier: Optional[str] = None
    refresh_token: Optional[str] = None


class TokenResponse(BaseModel):
    """OAuth 2.1 Token Response"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str


def generate_pkce_pair():
    """Generate PKCE code_verifier and code_challenge"""
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge


def validate_pkce(code_verifier: str, code_challenge: str) -> bool:
    """Validate PKCE code_verifier against stored code_challenge"""
    expected_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return expected_challenge == code_challenge


def create_jwt_token(payload: Dict[str, Any], expires_delta: timedelta = None) -> str:
    """Create JWT token with given payload"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=1)
    
    payload.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": OAUTH_CONFIG["issuer"]
    })
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# OAuth 2.1 Endpoints
from fastapi import APIRouter
oauth_app = APIRouter()

security = HTTPBearer()


@oauth_app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata():
    """Authorization server metadata (RFC8414)"""
    return OAUTH_CONFIG


@oauth_app.post("/oauth/register", response_model=ClientRegistrationResponse)
async def register_client(request: ClientRegistrationRequest):
    """Dynamic client registration (RFC7591)"""
    client_id = f"client_{secrets.token_urlsafe(16)}"
    client_secret = secrets.token_urlsafe(32)
    
    client_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_id_issued_at": int(datetime.utcnow().timestamp()),
        "client_secret_expires_at": 0,  # Never expires for demo
        "redirect_uris": request.redirect_uris,
        "client_name": request.client_name,
        "client_uri": request.client_uri,
        "scope": request.scope,
        "grant_types": request.grant_types,
        "response_types": request.response_types
    }
    
    CLIENT_REGISTRY[client_id] = client_data
    
    return ClientRegistrationResponse(**client_data)


@oauth_app.get("/oauth/authorize")
async def authorize(
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str = "read:all",
    state: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = None
):
    """Authorization endpoint with PKCE support"""
    
    # Validate client_id
    if client_id not in CLIENT_REGISTRY:
        raise HTTPException(status_code=400, detail="Invalid client_id")
    
    client = CLIENT_REGISTRY[client_id]
    
    # Validate redirect_uri
    if redirect_uri not in client["redirect_uris"]:
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")
    
    # Validate PKCE parameters
    if code_challenge and code_challenge_method != "S256":
        raise HTTPException(status_code=400, detail="Invalid code_challenge_method")
    
    # Generate authorization code
    auth_code = secrets.token_urlsafe(32)
    
    # For demo: determine user based on client name  
    # In production, this would come from user session/login
    client_info = CLIENT_REGISTRY.get(client_id, {})
    client_name = client_info.get("client_name", "").lower()
    user_id = "alex.smith" if "alex" in client_name else "martha.stewart"
    
    # Store authorization code with associated data
    AUTHORIZATION_CODES[auth_code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "code_challenge": code_challenge,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
        "user_id": user_id
    }
    
    # Build redirect URL with authorization code
    params = {"code": auth_code}
    if state:
        params["state"] = state
    
    redirect_url = f"{redirect_uri}?{urlencode(params)}"
    return RedirectResponse(url=redirect_url)


@oauth_app.post("/oauth/token", response_model=TokenResponse)
async def token_exchange(request: TokenRequest):
    """Token endpoint with PKCE validation"""
    
    if request.grant_type == "authorization_code":
        # Validate authorization code
        if not request.code or request.code not in AUTHORIZATION_CODES:
            raise HTTPException(status_code=400, detail="Invalid authorization code")
        
        auth_data = AUTHORIZATION_CODES[request.code]
        
        # Check expiration
        if datetime.utcnow() > auth_data["expires_at"]:
            del AUTHORIZATION_CODES[request.code]
            raise HTTPException(status_code=400, detail="Authorization code expired")
        
        # Validate client credentials
        if request.client_id != auth_data["client_id"]:
            raise HTTPException(status_code=400, detail="Invalid client_id")
        
        # Validate PKCE if used
        if auth_data.get("code_challenge") and request.code_verifier:
            if not validate_pkce(request.code_verifier, auth_data["code_challenge"]):
                raise HTTPException(status_code=400, detail="Invalid code_verifier")
        
        # Generate access token with user-specific scope
        user_id = auth_data["user_id"]
        requested_scope = auth_data["scope"]
        
        # Grant scope based on user permissions
        user_permissions = USER_SCOPES.get(user_id, ["none"])
        if "none" in user_permissions:
            # Alex Smith gets no access
            granted_scope = "none"
        elif "read:all" in user_permissions:
            # Martha Stewart gets full access
            granted_scope = "read:all"
        else:
            # Default to no access for unknown users
            granted_scope = "none"
        
        token_payload = {
            "sub": user_id,
            "client_id": request.client_id,
            "scope": granted_scope,  # Use granted scope, not requested
            "role": "executive" if user_id == "martha.stewart" else "clerk",
            "aud": "boomi-mcp-server"
        }
        
        access_token = create_jwt_token(token_payload, timedelta(hours=1))
        refresh_token = create_jwt_token({"sub": user_id, "type": "refresh"}, timedelta(days=30))
        
        # Store tokens
        ACCESS_TOKENS[access_token] = token_payload
        REFRESH_TOKENS[refresh_token] = {"user_id": user_id, "client_id": request.client_id}
        
        # Clean up authorization code
        del AUTHORIZATION_CODES[request.code]
        
        return TokenResponse(
            access_token=access_token,
            expires_in=3600,
            refresh_token=refresh_token,
            scope=granted_scope  # Return granted scope in response
        )
    
    elif request.grant_type == "refresh_token":
        # Handle refresh token grant
        if not request.refresh_token or request.refresh_token not in REFRESH_TOKENS:
            raise HTTPException(status_code=400, detail="Invalid refresh token")
        
        refresh_data = REFRESH_TOKENS[request.refresh_token]
        
        # Generate new access token
        token_payload = {
            "sub": refresh_data["user_id"],
            "client_id": request.client_id,
            "scope": "read:all",  # Default scope for refresh
            "role": "executive" if refresh_data["user_id"] == "martha.stewart" else "clerk",
            "aud": "boomi-mcp-server"
        }
        
        access_token = create_jwt_token(token_payload, timedelta(hours=1))
        ACCESS_TOKENS[access_token] = token_payload
        
        return TokenResponse(
            access_token=access_token,
            expires_in=3600,
            scope="read:all"
        )
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported grant type")


@oauth_app.get("/oauth/jwks")
async def jwks():
    """JSON Web Key Set endpoint"""
    # In production, use proper key management
    return {
        "keys": [
            {
                "kty": "oct",
                "kid": "default",
                "use": "sig",
                "alg": "HS256"
            }
        ]
    }


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


# Export OAuth app for integration with main MCP server
__all__ = ["oauth_app", "require_oauth_token", "OAUTH_SCOPES", "USER_SCOPES"]