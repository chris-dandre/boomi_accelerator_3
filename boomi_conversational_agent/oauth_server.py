import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from security.audit_logger import AuditLogger, AuditEvent, AuditEventType
from shared.shared_config import JWT_SECRET_KEY, JWT_ALGORITHM, USER_SCOPES

load_dotenv()

audit_logger = AuditLogger()

ACCESS_TOKENS: Dict[str, Dict[str, Any]] = {}
REFRESH_TOKENS: Dict[str, Dict[str, Any]] = {}
AUTHORIZATION_CODES: Dict[str, Dict[str, Any]] = {}

OAUTH_CONFIG = {
    "issuer": "http://localhost:8001",
    "token_endpoint": "/oauth/token",
    "authorization_endpoint": "/oauth/authorize",
    "jwks_uri": "/oauth/jwks",
    "grant_types_supported": ["authorization_code", "refresh_token", "password"],
    "response_types_supported": ["code"],
    "scopes_supported": ["read:all", "write:all", "mcp:read", "mcp:admin"],
    "token_endpoint_auth_methods_supported": ["client_secret_post"],
}

class TokenRequest(BaseModel):
    grant_type: str
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    code: Optional[str] = None
    refresh_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    scope: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

oauth_app = FastAPI(title="OAuth 2.1 Server for MCP")

oauth = OAuth()

def create_jwt_token(payload: Dict[str, Any], expires_delta: timedelta) -> str:
    expire = datetime.utcnow() + expires_delta
    payload.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

@oauth_app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata():
    return OAUTH_CONFIG

@oauth_app.post("/oauth/token", response_model=TokenResponse)
async def token_exchange(request: TokenRequest):
    if request.grant_type == "password":
        username = request.username
        password = request.password
        demo_users = {
            "sarah.chen": "executive.access.2024",
            "david.williams": "manager.access.2024",
            "alex.smith": "newuser123"
        }
        if username in demo_users and demo_users[username] == password:
            token_payload = {
                "sub": username,
                "client_id": request.client_id,
                "scope": " ".join(USER_SCOPES.get(username, ["none"])),
                "role": "executive" if username == "sarah.chen" else ("manager" if username == "david.williams" else "clerk"),
                "aud": "boomi-mcp-server"
            }
            access_token = create_jwt_token(token_payload, timedelta(hours=1))
            refresh_token = create_jwt_token({"sub": username, "type": "refresh"}, timedelta(days=30))
            ACCESS_TOKENS[access_token] = token_payload
            REFRESH_TOKENS[refresh_token] = {"user_id": username, "client_id": request.client_id}
            audit_logger.log_oauth_event(
                AuditEventType.TOKEN_EXCHANGE,
                success=True,
                client_id=request.client_id,
                user_id=username,
                ip_address="unknown",
                details={"scope": token_payload["scope"]}
            )
            return TokenResponse(
                access_token=access_token,
                expires_in=3600,
                refresh_token=refresh_token,
                scope=token_payload["scope"]
            )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    elif request.grant_type == "authorization_code":
        code_info = AUTHORIZATION_CODES.get(request.code)
        if not code_info:
            raise HTTPException(status_code=400, detail="Invalid authorization code")
        token_payload = {
            "sub": code_info["user_id"],
            "client_id": request.client_id,
            "scope": code_info.get("scope", ""),
            "aud": "boomi-mcp-server"
        }
        access_token = create_jwt_token(token_payload, timedelta(hours=1))
        refresh_token = create_jwt_token({"sub": code_info["user_id"], "type": "refresh"}, timedelta(days=30))
        ACCESS_TOKENS[access_token] = token_payload
        REFRESH_TOKENS[refresh_token] = {"user_id": code_info["user_id"], "client_id": request.client_id}
        audit_logger.log_oauth_event(
            AuditEventType.TOKEN_EXCHANGE,
            success=True,
            client_id=request.client_id,
            user_id=code_info["user_id"],
            ip_address="unknown",
            details={"scope": token_payload["scope"]}
        )
        return TokenResponse(
            access_token=access_token,
            expires_in=3600,
            refresh_token=refresh_token,
            scope=token_payload["scope"]
        )
    elif request.grant_type == "refresh_token":
        refresh_info = REFRESH_TOKENS.get(request.refresh_token)
        if not refresh_info:
            raise HTTPException(status_code=400, detail="Invalid refresh token")
        user_id = refresh_info["user_id"]
        token_payload = {
            "sub": user_id,
            "client_id": refresh_info["client_id"],
            "scope": " ".join(USER_SCOPES.get(user_id, ["none"])),
            "aud": "boomi-mcp-server"
        }
        access_token = create_jwt_token(token_payload, timedelta(hours=1))
        ACCESS_TOKENS[access_token] = token_payload
        audit_logger.log_oauth_event(
            AuditEventType.TOKEN_REFRESH,
            success=True,
            client_id=refresh_info["client_id"],
            user_id=user_id,
            ip_address="unknown",
            details={"scope": token_payload["scope"]}
        )
        return TokenResponse(
            access_token=access_token,
            expires_in=3600,
            scope=token_payload["scope"]
        )
    raise HTTPException(status_code=400, detail="Unsupported grant type")

@oauth_app.post("/oauth/introspect")
async def introspect_token(request: Request):
    form = await request.form()
    token = form.get("token")
    if not token or token not in ACCESS_TOKENS:
        return {"active": False}
    token_info = ACCESS_TOKENS[token]
    try:
        jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return {
            "active": True,
            "username": token_info["sub"],
            "role": token_info.get("role", "unknown"),
            "permissions": USER_SCOPES.get(token_info["sub"], []),
            "has_data_access": "read" in USER_SCOPES.get(token_info["sub"], [])
        }
    except jwt.PyJWTError:
        return {"active": False}