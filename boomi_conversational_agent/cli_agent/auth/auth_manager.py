"""
Authentication Manager for CLI Agent
Implements OAuth 2.1 authentication with role-based access control
"""

import json
import hashlib
import jwt
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

class UserRole(Enum):
    """User roles with different access levels"""
    EXECUTIVE = "executive"
    MANAGER = "manager"
    CLERK = "clerk"
    ADMIN = "admin"

@dataclass
class User:
    """User data structure"""
    username: str
    email: str
    role: UserRole
    full_name: str
    department: str
    permissions: List[str]
    created_at: str
    last_login: Optional[str] = None
    active: bool = True

@dataclass
class AuthSession:
    """Authentication session data"""
    user: User
    token: str
    expires_at: datetime
    issued_at: datetime
    session_id: str

class AuthManager:
    """Manages user authentication and authorization"""
    
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')  # Match oauth_server
        self.jwt_algorithm = 'HS256'
        self.token_expiry_hours = 8  # 8-hour sessions
        
        # Initialize user database
        self.users = self._load_user_database()
        
        # Active sessions
        self.active_sessions: Dict[str, AuthSession] = {}
    
    def _load_user_database(self) -> Dict[str, User]:
        """Load user database with demo personas"""
        users_data = {
            "sarah.chen": {
                "username": "sarah.chen",
                "email": "sarah.chen@company.com",
                "role": "executive",
                "full_name": "Sarah Chen",
                "department": "Executive Leadership",
                "password_hash": self._hash_password("executive.access.2024"),
                "permissions": [
                    "read_all_models",
                    "read_all_fields", 
                    "complex_queries",
                    "financial_data",
                    "strategic_analytics"
                ],
                "created_at": "2024-01-01T00:00:00Z",
                "active": True
            },
            "david.williams": {
                "username": "david.williams",
                "email": "david.williams@company.com",
                "role": "manager",
                "full_name": "David Williams",
                "department": "Business Intelligence",
                "password_hash": self._hash_password("manager.access.2024"),
                "permissions": [
                    "read_all_models",
                    "read_all_fields"
                ],
                "created_at": "2024-01-01T00:00:00Z",
                "active": True
            },
            "alex.smith": {
                "username": "alex.smith", 
                "email": "alex.smith@company.com",
                "role": "clerk",
                "full_name": "Alex Smith",
                "department": "Operations",
                "password_hash": self._hash_password("newuser123"),
                "permissions": [],  # No data access permissions
                "created_at": "2024-01-01T00:00:00Z", 
                "active": True
            },
            "admin": {
                "username": "admin",
                "email": "admin@company.com", 
                "role": "admin",
                "full_name": "System Administrator",
                "department": "IT",
                "password_hash": self._hash_password("admin.secure.2024"),
                "permissions": [
                    "read_all_models",
                    "read_all_fields",
                    "complex_queries", 
                    "financial_data",
                    "strategic_analytics",
                    "user_management",
                    "system_administration"
                ],
                "created_at": "2024-01-01T00:00:00Z",
                "active": True
            }
        }
        
        # Convert to User objects
        users = {}
        for username, data in users_data.items():
            users[username] = User(
                username=data["username"],
                email=data["email"], 
                role=UserRole(data["role"]),
                full_name=data["full_name"],
                department=data["department"],
                permissions=data["permissions"],
                created_at=data["created_at"],
                active=data["active"]
            )
            # Store password hash separately for verification
            users[username]._password_hash = data["password_hash"]
        
        return users
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = "boomi_conversational_agent_salt"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> Optional[AuthSession]:
        """Authenticate user and create session"""
        
        # Check if user exists
        if username not in self.users:
            return None
        
        user = self.users[username]
        
        # Check if user is active
        if not user.active:
            return None
        
        # Verify password
        password_hash = self._hash_password(password)
        if password_hash != user._password_hash:
            return None
        
        # Create JWT token
        import time
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.token_expiry_hours)
        
        # Use current time for timestamps
        current_timestamp = int(time.time())
        expires_timestamp = current_timestamp + (self.token_expiry_hours * 3600)
        
        token_payload = {
            'sub': user.username,  # Standard JWT 'sub' claim for user ID
            'username': user.username,
            'role': user.role.value,
            'permissions': user.permissions,
            'scope': 'read:all write:all' if user.role == UserRole.EXECUTIVE else ('read:advertisements' if user.role.value == 'manager' else 'none'),
            'iat': current_timestamp,
            'exp': expires_timestamp,
            'iss': 'http://localhost:8001',  # Match server expectation
            'aud': 'boomi-mcp-server'  # Match server expectation
        }
        
        print(f"🔍 Auth Debug - Creating token for {user.username}")
        print(f"🔍 Auth Debug - Current timestamp: {current_timestamp}")
        print(f"🔍 Auth Debug - Expires timestamp: {expires_timestamp}")
        print(f"🔍 Auth Debug - Current time: {now}")
        print(f"🔍 Auth Debug - Token will be valid for {self.token_expiry_hours} hours")
        
        token = jwt.encode(token_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        # Create session
        session_id = hashlib.sha256(f"{username}_{now.timestamp()}".encode()).hexdigest()[:16]
        
        session = AuthSession(
            user=user,
            token=token,
            expires_at=expires_at,
            issued_at=now,
            session_id=session_id
        )
        
        # Update user last login
        user.last_login = now.isoformat()
        
        # Store active session
        self.active_sessions[session_id] = session
        
        return session
    
    def validate_token(self, token: str) -> Optional[AuthSession]:
        """Validate JWT token and return session"""
        try:
            # Decode token
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check if user still exists and is active
            username = payload['username']
            if username not in self.users or not self.users[username].active:
                return None
            
            # Find session by token
            for session in self.active_sessions.values():
                if session.token == token:
                    # Check if session is expired
                    if datetime.utcnow() > session.expires_at:
                        self._cleanup_session(session.session_id)
                        return None
                    return session
            
            return None
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def logout(self, session_id: str) -> bool:
        """Logout user and cleanup session"""
        return self._cleanup_session(session_id)
    
    def _cleanup_session(self, session_id: str) -> bool:
        """Remove session from active sessions"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False
    
    def check_permission(self, session: AuthSession, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in session.user.permissions
    
    def has_data_access(self, session: AuthSession) -> bool:
        """Check if user has any data access permissions"""
        data_permissions = [
            "read_all_models", 
            "read_all_fields",
            "complex_queries"
        ]
        return any(perm in session.user.permissions for perm in data_permissions)
    
    def get_user_info(self, session: AuthSession) -> Dict:
        """Get user information for display"""
        return {
            "username": session.user.username,
            "full_name": session.user.full_name,
            "role": session.user.role.value,
            "department": session.user.department,
            "permissions": session.user.permissions,
            "session_expires": session.expires_at.isoformat(),
            "last_login": session.user.last_login
        }
    
    def get_active_sessions(self) -> List[Dict]:
        """Get all active sessions (admin only)"""
        sessions = []
        for session in self.active_sessions.values():
            sessions.append({
                "session_id": session.session_id,
                "username": session.user.username,
                "role": session.user.role.value,
                "issued_at": session.issued_at.isoformat(),
                "expires_at": session.expires_at.isoformat()
            })
        return sessions
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if now > session.expires_at
        ]
        
        for session_id in expired_sessions:
            self._cleanup_session(session_id)
        
        return len(expired_sessions)