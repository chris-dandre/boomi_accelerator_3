"""
Token Revocation System (RFC 7009)
Phase 6B: Advanced Security Features

Implements OAuth 2.0 Token Revocation specification for secure token lifecycle management.
"""

import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Set, Any
from fastapi import HTTPException, Form, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import jwt

from .audit_logger import audit_logger, AuditEventType, log_oauth_client_registration

# In-memory storage for revoked tokens (use Redis/database in production)
REVOKED_TOKENS: Dict[str, Dict[str, Any]] = {}
REVOKED_REFRESH_TOKENS: Dict[str, Dict[str, Any]] = {}

# Import client registry from oauth_server
try:
    import sys
    import os
    # Add parent directory to path to import oauth_server
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from oauth_server import CLIENT_REGISTRY
except ImportError:
    # Fallback local registry  
    CLIENT_REGISTRY: Dict[str, Dict[str, Any]] = {}

# Configuration
TOKEN_CLEANUP_INTERVAL_HOURS = 24
MAX_REVOKED_TOKENS_CACHE = 10000

security = HTTPBasic()

class TokenRevocationError(Exception):
    """Custom exception for token revocation errors"""
    pass

def get_token_jti(token: str) -> Optional[str]:
    """Extract JTI (JWT ID) from token without verification"""
    try:
        # Decode without verification to get JTI
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        return unverified_payload.get("jti")
    except Exception:
        return None

def hash_token(token: str) -> str:
    """Create a hash of the token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()

def add_jti_to_token_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Add JTI (JWT ID) to token payload for revocation tracking"""
    if "jti" not in payload:
        payload["jti"] = secrets.token_urlsafe(32)
    return payload

def is_token_revoked(token: str) -> bool:
    """Check if a token has been revoked"""
    try:
        # First try to get JTI from token
        jti = get_token_jti(token)
        if jti and jti in REVOKED_TOKENS:
            return True
        
        # Fallback to token hash check
        token_hash = hash_token(token)
        return token_hash in REVOKED_TOKENS
        
    except Exception:
        # If we can't process the token, consider it potentially compromised
        return True

def revoke_token(
    token: str, 
    token_type_hint: Optional[str] = None,
    client_id: Optional[str] = None,
    reason: str = "client_request"
) -> bool:
    """Revoke a token (access or refresh token)"""
    try:
        revocation_time = datetime.now(timezone.utc)
        
        # Extract token information
        jti = get_token_jti(token)
        token_hash = hash_token(token)
        
        # Determine token type
        actual_token_type = "unknown"
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            if payload.get("type") == "refresh":
                actual_token_type = "refresh_token"
            else:
                actual_token_type = "access_token"
        except Exception:
            actual_token_type = token_type_hint or "unknown"
        
        # Store revocation information
        revocation_info = {
            "revoked_at": revocation_time.isoformat(),
            "revoked_by": client_id,
            "reason": reason,
            "token_type": actual_token_type,
            "token_hash": token_hash
        }
        
        # Store by JTI if available, otherwise by hash
        if jti:
            REVOKED_TOKENS[jti] = revocation_info
        else:
            REVOKED_TOKENS[token_hash] = revocation_info
        
        # Also store refresh tokens separately for easier cleanup
        if actual_token_type == "refresh_token":
            REVOKED_REFRESH_TOKENS[jti or token_hash] = revocation_info
        
        # Log the revocation
        audit_logger.log_oauth_event(
            AuditEventType.TOKEN_REVOCATION,
            success=True,
            client_id=client_id,
            details={
                "token_type": actual_token_type,
                "reason": reason,
                "jti": jti,
                "revocation_time": revocation_time.isoformat()
            }
        )
        
        # Cleanup old revoked tokens if cache is getting too large
        if len(REVOKED_TOKENS) > MAX_REVOKED_TOKENS_CACHE:
            cleanup_expired_revoked_tokens()
        
        return True
        
    except Exception as e:
        # Log revocation failure
        audit_logger.log_oauth_event(
            AuditEventType.TOKEN_REVOCATION,
            success=False,
            client_id=client_id,
            details={
                "error": str(e),
                "reason": reason,
                "token_type": token_type_hint
            }
        )
        raise TokenRevocationError(f"Failed to revoke token: {str(e)}")

def revoke_all_user_tokens(user_id: str, client_id: Optional[str] = None, reason: str = "admin_action"):
    """Revoke all tokens for a specific user"""
    revoked_count = 0
    
    # This is a simplified implementation
    # In production, you'd need to track tokens by user_id
    for token_id, revocation_info in list(REVOKED_TOKENS.items()):
        try:
            # In a real implementation, you'd have user_id indexed tokens
            # For now, we'll just mark the action in audit logs
            pass
        except Exception:
            continue
    
    # Log bulk revocation
    audit_logger.log_oauth_event(
        AuditEventType.TOKEN_REVOCATION,
        success=True,
        client_id=client_id,
        user_id=user_id,
        details={
            "action": "bulk_revocation",
            "reason": reason,
            "tokens_revoked": revoked_count
        }
    )
    
    return revoked_count

def cleanup_expired_revoked_tokens():
    """Clean up expired revoked tokens from cache"""
    current_time = datetime.now(timezone.utc)
    cleanup_threshold = current_time - timedelta(days=30)  # Keep revocation records for 30 days
    
    expired_tokens = []
    
    for token_id, revocation_info in REVOKED_TOKENS.items():
        try:
            revoked_at = datetime.fromisoformat(revocation_info["revoked_at"].replace('Z', '+00:00'))
            if revoked_at < cleanup_threshold:
                expired_tokens.append(token_id)
        except Exception:
            # If we can't parse the date, consider it for cleanup
            expired_tokens.append(token_id)
    
    # Remove expired tokens
    for token_id in expired_tokens:
        REVOKED_TOKENS.pop(token_id, None)
        REVOKED_REFRESH_TOKENS.pop(token_id, None)
    
    if expired_tokens:
        audit_logger.log_oauth_event(
            AuditEventType.TOKEN_REVOCATION,
            success=True,
            details={
                "action": "cleanup_expired_tokens",
                "tokens_cleaned": len(expired_tokens)
            }
        )

def verify_client_credentials(credentials: HTTPBasicCredentials) -> str:
    """Verify client credentials for revocation endpoint"""
    client_id = credentials.username
    client_secret = credentials.password
    
    # Check if client exists and credentials are valid
    if client_id not in CLIENT_REGISTRY:
        raise HTTPException(status_code=401, detail="Invalid client credentials")
    
    client_info = CLIENT_REGISTRY[client_id]
    if client_info.get("client_secret") != client_secret:
        raise HTTPException(status_code=401, detail="Invalid client credentials")
    
    return client_id

# RFC 7009 Token Revocation Endpoint
async def revoke_token_endpoint(
    token: str = Form(),
    token_type_hint: Optional[str] = Form(None),
    credentials: HTTPBasicCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    OAuth 2.0 Token Revocation Endpoint (RFC 7009)
    
    Revokes access tokens or refresh tokens.
    """
    try:
        # Verify client credentials
        client_id = verify_client_credentials(credentials)
        
        # Validate token_type_hint
        if token_type_hint and token_type_hint not in ["access_token", "refresh_token"]:
            raise HTTPException(status_code=400, detail="Invalid token_type_hint")
        
        # Revoke the token
        success = revoke_token(
            token=token,
            token_type_hint=token_type_hint,
            client_id=client_id,
            reason="client_request"
        )
        
        if success:
            return {"revoked": True}
        else:
            # RFC 7009 specifies that revocation endpoint should return 200 even for invalid tokens
            return {"revoked": True}
            
    except TokenRevocationError as e:
        # Log the error but still return success per RFC 7009
        audit_logger.log_oauth_event(
            AuditEventType.TOKEN_REVOCATION,
            success=False,
            client_id=credentials.username if credentials else None,
            details={"error": str(e)}
        )
        return {"revoked": True}
    
    except HTTPException:
        raise
    
    except Exception as e:
        audit_logger.log_oauth_event(
            AuditEventType.TOKEN_REVOCATION,
            success=False,
            client_id=credentials.username if credentials else None,
            details={"error": f"Unexpected error: {str(e)}"}
        )
        # Return success per RFC 7009 specification
        return {"revoked": True}

# Token introspection helpers (for internal use)
def get_token_info(token: str) -> Optional[Dict[str, Any]]:
    """Get information about a token"""
    try:
        # Check if token is revoked
        if is_token_revoked(token):
            return {"active": False, "revoked": True}
        
        # Decode token (without verification for info purposes)
        payload = jwt.decode(token, options={"verify_signature": False})
        
        return {
            "active": True,
            "revoked": False,
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
            "sub": payload.get("sub"),
            "client_id": payload.get("client_id"),
            "scope": payload.get("scope"),
            "jti": payload.get("jti")
        }
        
    except Exception:
        return {"active": False, "error": "invalid_token"}

def get_revocation_stats() -> Dict[str, Any]:
    """Get statistics about token revocations"""
    current_time = datetime.now(timezone.utc)
    
    # Count revocations by time period
    last_hour = current_time - timedelta(hours=1)
    last_day = current_time - timedelta(days=1)
    
    recent_revocations = 0
    daily_revocations = 0
    
    for revocation_info in REVOKED_TOKENS.values():
        try:
            revoked_at = datetime.fromisoformat(revocation_info["revoked_at"].replace('Z', '+00:00'))
            if revoked_at > last_hour:
                recent_revocations += 1
            if revoked_at > last_day:
                daily_revocations += 1
        except Exception:
            continue
    
    return {
        "total_revoked_tokens": len(REVOKED_TOKENS),
        "revoked_refresh_tokens": len(REVOKED_REFRESH_TOKENS),
        "revocations_last_hour": recent_revocations,
        "revocations_last_day": daily_revocations,
        "cache_usage_percent": (len(REVOKED_TOKENS) / MAX_REVOKED_TOKENS_CACHE) * 100
    }

# Export functions for integration
__all__ = [
    "is_token_revoked",
    "revoke_token",
    "revoke_token_endpoint", 
    "revoke_all_user_tokens",
    "cleanup_expired_revoked_tokens",
    "get_token_info",
    "get_revocation_stats",
    "add_jti_to_token_payload",
    "TokenRevocationError"
]