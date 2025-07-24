"""
OAuth 2.1 MCP Server Launcher
Phase 6A: Server startup script

This script launches the OAuth-enabled MCP server with proper configuration.
"""

import sys
import os
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import authlib
        import jwt
        import cryptography
        print("✅ All OAuth dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_environment():
    """Check environment setup"""
    issues = []
    
    # Check for .env file or environment variables
    env_file = project_root / ".env"
    if not env_file.exists():
        if not os.getenv("BOOMI_API_USERNAME"):
            issues.append("Missing Boomi credentials (no .env file or BOOMI_API_USERNAME)")
    
    # Check for boomi client
    boomi_client_paths = [
        project_root / "boomi_datahub_mcp_server" / "boomi_datahub_client.py",
        project_root / "boomi_datahub_client.py"
    ]
    
    client_found = any(path.exists() for path in boomi_client_paths)
    if not client_found:
        issues.append("boomi_datahub_client.py not found")
    
    if issues:
        print("⚠️  Environment issues detected:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nServer may not function correctly without resolving these issues.")
        return False
    else:
        print("✅ Environment setup looks good")
        return True

def main():
    """Launch the OAuth-enabled MCP server"""
    print("🚀 Starting OAuth 2.1 MCP Server")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    check_environment()
    
    print("\n📋 Server Configuration:")
    print("   - Host: 0.0.0.0")
    print("   - Port: 8001")
    print("   - OAuth endpoints: /oauth/*")
    print("   - MCP endpoints: /mcp/*")
    print("   - Documentation: http://localhost:8001/docs")
    
    print("\n🔐 OAuth 2.1 Features:")
    print("   - Authorization Server Metadata")
    print("   - Dynamic Client Registration")  
    print("   - PKCE Authorization Flow")
    print("   - JWT Token Exchange")
    print("   - Role-Based Access Control")
    
    print("\n👥 Demo User Personas:")
    print("   - Sarah Chen (Executive): read:all write:all scope")
    print("   - David Williams (Manager): read:advertisements scope")
    print("   - Alex Smith (Clerk): none scope")
    
    print("\n🌐 Starting OAuth server...")
    
    try:
        # Import and run the OAuth server
        from fastapi import FastAPI
        from oauth_server import oauth_app
        
        # Create FastAPI app
        app = FastAPI(title="OAuth 2.1 Server for MCP Testing")
        
        # Mount OAuth endpoints
        app.mount("/oauth", oauth_app)
        app.mount("", oauth_app)  # Also mount at root for metadata endpoint
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "service": "oauth-server"}
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info",
            reload=False
        )
    except ImportError as e:
        print(f"❌ Failed to import server: {e}")
        print("Make sure boomi_datahub_mcp_server_oauth.py is in the current directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()