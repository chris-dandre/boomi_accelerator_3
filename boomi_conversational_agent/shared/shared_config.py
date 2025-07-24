"""
Centralized configuration for JWT and user scopes
"""

import os
from dotenv import load_dotenv

load_dotenv()

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is required")
JWT_ALGORITHM = "HS256"

# User scopes for authorization
USER_SCOPES = {
    "sarah.chen": ["read:all", "write:all", "mcp:admin"],
    "david.williams": ["read:advertisements", "mcp:read"],
    "alex.smith": ["none"]
}