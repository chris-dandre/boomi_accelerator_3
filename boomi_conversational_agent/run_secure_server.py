"""
Secure MCP Server Launcher for Phase 6B
Complete Enterprise Security Edition

Launches the fully secured MCP server with all Phase 6B features:
- OAuth 2.1 authentication
- Comprehensive audit logging
- Token revocation
- Rate limiting and DDoS protection
- Jailbreak detection
"""

import sys
import os
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'authlib', 'jwt', 'cryptography', 
        'requests', 'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing dependencies: {', '.join(missing_packages)}")
        print("Please run: pip install -r requirements.txt")
        return False
    else:
        print("✅ All security dependencies installed")
        return True

def check_environment():
    """Check environment setup for secure operation"""
    issues = []
    warnings = []
    
    # Check for .env file or environment variables
    env_file = project_root / ".env"
    if not env_file.exists():
        if not os.getenv("BOOMI_API_USERNAME"):
            issues.append("Missing Boomi credentials (no .env file or BOOMI_API_USERNAME)")
    
    # Check for security directories
    security_dir = project_root / "security"
    if not security_dir.exists():
        issues.append("Security module directory not found")
    
    logs_dir = project_root / "logs"
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
        warnings.append("Created logs directory for audit logging")
    
    # Check JWT secret key
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret or jwt_secret == "dev-secret-key-change-in-production":
        warnings.append("Using default JWT secret key - change for production")
    
    # Check for boomi client
    boomi_client_paths = [
        project_root / "boomi_datahub_mcp_server" / "boomi_datahub_client.py",
        project_root / "boomi_datahub_client.py"
    ]
    
    client_found = any(path.exists() for path in boomi_client_paths)
    if not client_found:
        issues.append("boomi_datahub_client.py not found")
    
    # Report results
    if issues:
        print("❌ Environment issues detected:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    if warnings:
        print("⚠️  Environment warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    print("✅ Environment setup validated")
    return True

def display_security_info():
    """Display security feature information"""
    print("\n🔐 Security Features Enabled:")
    print("   ✅ OAuth 2.1 Authentication (RFC 6749, RFC 7636)")
    print("   ✅ Dynamic Client Registration (RFC 7591)")
    print("   ✅ Token Revocation (RFC 7009)")
    print("   ✅ Comprehensive Audit Logging")
    print("   ✅ Multi-tier Rate Limiting")
    print("   ✅ DDoS Protection")
    print("   ✅ Jailbreak Detection")
    print("   ✅ Prompt Injection Protection")
    print("   ✅ Security Headers (OWASP)")
    print("   ✅ Role-Based Access Control")
    
    print("\n📊 Monitoring & Admin:")
    print("   - Audit logs: logs/audit/")
    print("   - Security stats: /admin/security/stats")
    print("   - Health check: /health")
    print("   - API docs: /docs")
    
    print("\n👥 Demo User Personas:")
    print("   - Martha Stewart (Executive): Full access (read:all)")
    print("   - Alex Smith (Clerk): No access (none)")

def main():
    """Launch the secure MCP server"""
    print("🚀 Starting Secure Boomi DataHub MCP Server")
    print("=" * 50)
    print("Phase 6B: Enterprise Security Edition")
    print()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        print("\n⚠️  Server may not function correctly with these issues.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Display security information
    display_security_info()
    
    print("\n📋 Server Configuration:")
    print("   - Host: 0.0.0.0")
    print("   - Port: 8001")
    print("   - Security: Maximum")
    print("   - Compliance: OAuth 2.1, RFC 7009, MCP Spec")
    
    print("\n🌐 Starting secure server...")
    print("   Access: http://localhost:8001")
    print("   Docs: http://localhost:8001/docs")
    print("   Health: http://localhost:8001/health")
    print()
    
    try:
        # Import and run the secure server
        from boomi_datahub_mcp_server_secure import app
        
        # Configure for production-like security
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info",
            reload=False,
            access_log=True,
            server_header=False,  # Don't reveal server info
            date_header=True
        )
        
    except ImportError as e:
        print(f"❌ Failed to import secure server: {e}")
        print("Make sure boomi_datahub_mcp_server_secure.py is in the current directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()