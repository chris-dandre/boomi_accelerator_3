"""
OAuth 2.1 Client for Testing and CLI
Enhanced OAuth client with shared_config integration and environment variable support
"""

import jwt
import json
import time
import base64
import hashlib
import secrets
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import shared configuration
try:
    from shared.shared_config import JWT_SECRET_KEY, JWT_ALGORITHM, USER_SCOPES
except ImportError:
    # Fallback values if shared_config is not available
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    USER_SCOPES = {}

class EnhancedOAuthClient:
    """Enhanced OAuth client with shared config integration"""
    
    def __init__(self, server_url: str = None):
        self.server_url = server_url or os.getenv('OAUTH_SERVER_URL', "http://localhost:8001")
        self.jwt_secret = JWT_SECRET_KEY
        self.jwt_algorithm = JWT_ALGORITHM
        
        # Demo user credentials
        self.demo_users = {
            "sarah.chen": {
                "username": "sarah.chen",
                "password": "executive.access.2024",
                "role": "executive",
                "full_name": "Sarah Chen",
                "department": "Executive Leadership",
                "permissions": ["read:all", "write:all"],
                "has_data_access": True
            },
            "david.williams": {
                "username": "david.williams", 
                "password": "manager.access.2024",
                "role": "manager",
                "full_name": "David Williams",
                "department": "Business Intelligence",
                "permissions": ["read:advertisements"],
                "has_data_access": True
            },
            "alex.smith": {
                "username": "alex.smith",
                "password": "newuser123",
                "role": "clerk",
                "full_name": "Alex Smith",
                "department": "Operations",
                "permissions": [],
                "has_data_access": False
            }
        }
    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and return JWT token
        For testing purposes, this generates a real JWT token
        """
        
        # Validate credentials
        if username not in self.demo_users:
            return {"success": False, "error": "User not found"}
        
        user = self.demo_users[username]
        if user["password"] != password:
            return {"success": False, "error": "Invalid password"}
        
        # Generate real JWT token
        current_time = int(time.time())
        
        token_payload = {
            "sub": username,
            "aud": "boomi-mcp-server",
            "iss": "http://localhost:8001",
            "iat": current_time,
            "exp": current_time + 3600,  # 1 hour expiry
            "client_id": "test-client",
            "scope": " ".join(user["permissions"]) if user["permissions"] else "none",
            
            # Additional user context
            "role": user["role"],
            "full_name": user["full_name"],
            "department": user["department"],
            "permissions": user["permissions"],
            "has_data_access": user["has_data_access"]
        }
        
        # Create JWT token
        try:
            jwt_token = jwt.encode(
                token_payload,
                self.jwt_secret,
                algorithm=self.jwt_algorithm
            )
            
            return {
                "success": True,
                "access_token": jwt_token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "user_info": {
                    "username": username,
                    "role": user["role"],
                    "full_name": user["full_name"],
                    "department": user["department"],
                    "permissions": user["permissions"],
                    "has_data_access": user["has_data_access"]
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Token generation failed: {e}"}
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                audience="boomi-mcp-server",
                issuer="http://localhost:8001"
            )
            return {"valid": True, "payload": payload}
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError as e:
            return {"valid": False, "error": f"Invalid token: {e}"}
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        return self.demo_users.get(username)
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token (simplified implementation)
        """
        # For testing, just validate the refresh token and issue new access token
        try:
            payload = jwt.decode(
                refresh_token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            username = payload.get("sub")
            if username and username in self.demo_users:
                # Generate new access token
                return self.authenticate(username, self.demo_users[username]["password"])
            else:
                return {"success": False, "error": "Invalid refresh token"}
                
        except Exception as e:
            return {"success": False, "error": f"Token refresh failed: {e}"}

# Global OAuth client instance
oauth_client = EnhancedOAuthClient()

def get_oauth_token(username: str, password: str) -> str:
    """
    Convenience function to get OAuth token
    Returns the JWT token string or None if authentication fails
    """
    result = oauth_client.authenticate(username, password)
    if result["success"]:
        return result["access_token"]
    else:
        print(f"Authentication failed: {result['error']}")
        return None

def validate_oauth_token(token: str) -> Dict[str, Any]:
    """
    Convenience function to validate OAuth token
    """
    return oauth_client.validate_token(token)