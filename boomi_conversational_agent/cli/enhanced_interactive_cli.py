"""
Enhanced Interactive CLI with LangGraph Orchestration
Phase 8B implementation with unified orchestrator
"""

import asyncio
import sys
import os
from typing import Dict, Any, Optional
import json
import time
import requests
import subprocess
import signal
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set default configuration to disable proactive features for CLI
os.environ.setdefault("ENABLE_PROACTIVE_INSIGHTS", "false")
os.environ.setdefault("ENABLE_FOLLOW_UP_SUGGESTIONS", "false")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.mcp_orchestrator import create_orchestrator
from shared.agent_state import AuthStatus, SecurityClearance
from shared.oauth_client import oauth_client

class EnhancedInteractiveCLI:
    """Enhanced CLI with LangGraph orchestration"""
    
    def __init__(self):
        self.orchestrator = create_orchestrator(interface_type="cli")
        self.session = None
        self.is_running = False
        self.oauth_server_process = None
        self.oauth_server_url = os.getenv('OAUTH_SERVER_URL', "http://localhost:8001")
        self.field_mappings = {}
        
        # Demo users for testing
        self.demo_users = {
            "sarah.chen": {
                "username": "sarah.chen",
                "password": "executive.access.2024",
                "role": "executive",
                "full_name": "Sarah Chen",
                "department": "Executive Leadership",
                "title": "Chief Data Officer",
                "has_data_access": True,
                "permissions": ["READ_ALL", "METADATA_ALL", "ANALYTICS_ALL", "EXPORT_ALL"],
                "description": "Chief Data Officer with full system access"
            },
            "david.williams": {
                "username": "david.williams",
                "password": "manager.access.2024",
                "role": "manager",
                "full_name": "David Williams",
                "department": "Business Intelligence",
                "title": "BI Manager",
                "has_data_access": True,
                "permissions": ["READ_ASSIGNED", "METADATA_ASSIGNED", "ANALYTICS_STANDARD"],
                "description": "BI Manager with departmental data access"
            },
            "alex.smith": {
                "username": "alex.smith",
                "password": "newuser123",
                "role": "clerk",
                "full_name": "Alex Smith",
                "department": "Operations",
                "title": "Operations Clerk",
                "has_data_access": False,
                "permissions": [],
                "description": "Operations clerk with no data access"
            }
        }
    
    def print_banner(self):
        """Print enhanced CLI banner"""
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      SWX MCP Server for Boomi DataHub                       ║
║                    Enhanced CLI with LangGraph Orchestration                 ║
║                              Phase 8B Implementation                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Features:                                                                    ║
║  • LangGraph Orchestration     • MCP June 2025 Compliance                   ║
║  • 4-Layer Security           • Proactive Intelligence                       ║
║  • OAuth 2.1 Authentication   • Follow-up Suggestions                       ║
║  • Role-Based Access          • Performance Monitoring                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)
        
        # Initialize OAuth server
        self._initialize_oauth_server()
    
    def print_help(self):
        """Print help information"""
        print("""
Available Commands:
  authenticate <username> <password>  - Authenticate with user credentials
  help                               - Show this help message
  status                            - Show current session status
  quit/exit                         - Exit the CLI
  
Demo Users:
  sarah.chen / executive.access.2024  - Executive with full access
  david.williams / manager.access.2024 - Manager with limited access
  alex.smith / newuser123             - Clerk with no data access
  
Query Examples:
  "list models in datahub"
  "how many advertisements do we have?"
  "show me user data"
  "count opportunities"
        """)
    
    def _initialize_oauth_server(self):
        """Initialize OAuth server for authentication"""
        print("🔐 Initializing OAuth 2.1 authentication server...")
        
        # Check if OAuth server is already running
        if self._check_oauth_server_health():
            print("✅ OAuth server is already running")
            return True
        
        # Start OAuth server
        print("🚀 Starting OAuth server...")
        success = self._start_oauth_server()
        
        if success:
            print("✅ OAuth server started successfully")
            return True
        else:
            print("⚠️  OAuth server failed to start - authentication may not work")
            return False
    
    def _check_oauth_server_health(self) -> bool:
        """Check if OAuth server is running and healthy"""
        try:
            response = requests.get(f"{self.oauth_server_url}/health", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def _start_oauth_server(self) -> bool:
        """Start OAuth server subprocess"""
        try:
            # Check if unified compliant MCP server is available (the one that works!)
            mcp_server_script = Path(__file__).parent.parent / "boomi_datahub_mcp_server_unified_compliant.py"
            
            if not mcp_server_script.exists():
                print(f"❌ MCP server script not found: {mcp_server_script}")
                return False
            
            # Start the compliant MCP server (includes OAuth server)
            cmd = [sys.executable, str(mcp_server_script)]
            
            self.oauth_server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            print("⏳ Waiting for OAuth server to initialize...")
            for i in range(10):  # Try for 10 seconds
                time.sleep(1)
                if self._check_oauth_server_health():
                    print(f"✅ OAuth server ready after {i+1} seconds")
                    return True
                print(f"   Attempt {i+1}/10...")
            
            print("❌ OAuth server failed to start within timeout")
            return False
            
        except Exception as e:
            print(f"❌ Error starting OAuth server: {e}")
            return False
    
    def _stop_oauth_server(self):
        """Stop OAuth server subprocess"""
        if self.oauth_server_process:
            try:
                self.oauth_server_process.terminate()
                self.oauth_server_process.wait(timeout=5)
                print("✅ OAuth server stopped")
            except subprocess.TimeoutExpired:
                self.oauth_server_process.kill()
                print("🔴 OAuth server force-killed")
            except Exception as e:
                print(f"⚠️  Error stopping OAuth server: {e}")
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user with real OAuth 2.1 token exchange"""
        
        # Check if OAuth server is available
        if not self._check_oauth_server_health():
            print("❌ OAuth server is not available. Please restart the application.")
            return False
        
        if username in self.demo_users:
            user = self.demo_users[username]
            if user["password"] == password:
                # Get real OAuth token from server
                bearer_token = self._get_oauth_token(username)
                
                if bearer_token:
                    self.session = {
                        "username": username,
                        "role": user["role"],
                        "full_name": user["full_name"],
                        "department": user["department"],
                        "title": user["title"],
                        "has_data_access": user["has_data_access"],
                        "permissions": user["permissions"],
                        "bearer_token": bearer_token,
                        "authenticated_at": time.time()
                    }
                    
                    print(f"✅ Authentication successful!")
                    print(f"   Welcome, {user['full_name']} ({user['title']})")
                    print(f"   Role: {user['role']}")
                    print(f"   Department: {user['department']}")
                    print(f"   Data Access: {'✅ Granted' if user['has_data_access'] else '❌ Denied'}")
                    print(f"   Permissions: {', '.join(user['permissions']) if user['permissions'] else 'None'}")
                    print(f"   Token: {bearer_token[:50]}...")
                    
                    return True
                else:
                    print("❌ Failed to obtain OAuth token")
                    return False
            else:
                print("❌ Invalid password")
                return False
        else:
            print("❌ User not found")
            return False
    
    def _get_oauth_token(self, username: str) -> Optional[str]:
        """Get OAuth token using shared OAuth client"""
        try:
            user_info = self.demo_users[username]
            result = oauth_client.authenticate(username, user_info["password"])
            
            if result["success"]:
                print(f"🔐 OAuth token generated successfully")
                return result["access_token"]
            else:
                print(f"❌ OAuth token generation failed: {result['error']}")
                return None
                
        except Exception as e:
            print(f"❌ OAuth token generation failed: {e}")
            return None
    
    def _get_oauth_scope(self, username: str) -> str:
        """Get OAuth scope for user"""
        user_info = self.demo_users[username]
        role = user_info["role"]
        
        # Map roles to OAuth scopes
        scope_mapping = {
            "executive": "read:all write:all mcp:admin",
            "manager": "read:advertisements mcp:read", 
            "clerk": "none"
        }
        
        return scope_mapping.get(role, "none")
    
    def print_status(self):
        """Print current session status"""
        if self.session:
            print(f"""
Session Status:
  User: {self.session['full_name']} ({self.session['username']})
  Role: {self.session['role']}
  Department: {self.session['department']}
  Data Access: {'✅ Granted' if self.session['has_data_access'] else '❌ Denied'}
  Permissions: {', '.join(self.session['permissions']) if self.session['permissions'] else 'None'}
  Session Duration: {int(time.time() - self.session['authenticated_at'])}s
            """)
        else:
            print("❌ No active session. Please authenticate first.")
    
    async def process_query_enhanced(self, query: str) -> Dict[str, Any]:
        """Enhanced query processing with LangGraph orchestration"""
        
        if not self.session or not self.session.get("bearer_token"):
            return {"error": "Authentication required. Use 'authenticate <username> <password>'."}
        
        # Prepare user context with field_mappings
        user_context = {
            "role": self.session.get("role", "unknown"),
            "username": self.session.get("username", "anonymous"),
            "permissions": self.session.get("permissions", []),
            "has_data_access": self.session.get("has_data_access", False),
            "full_name": self.session.get("full_name", "Unknown"),
            "department": self.session.get("department", "Unknown"),
            "field_mappings": self.field_mappings
        }
        
        print(f"\n🚀 Processing query through LangGraph orchestration...")
        print(f"   User: {user_context['full_name']} ({user_context['role']})")
        print(f"   Query: '{query}'")
        
        start_time = time.time()
        
        try:
            # Process through unified orchestrator
            result = await self.orchestrator.process_query(
                query=query,
                user_context=user_context,
                bearer_token=self.session["bearer_token"]
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"\n⚡ Processing completed in {processing_time:.2f}s")
            
            # Display results
            self._display_enhanced_result(result)
            
            return result
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            return {"error": str(e)}
    
    def _display_enhanced_result(self, result: Dict[str, Any]):
        """Display enhanced result with proactive features (aligned with orchestrator output)"""
        
        if result.get("success"):
            print(f"\n✅ Query processed successfully!")
            
            # Main response - handle both string and dict formats
            if result.get("response"):
                response = result["response"]
                print(f"\n" + "="*80)
                print(f"🎯 QUERY RESULTS")
                print(f"="*80)
                
                if isinstance(response, dict):
                    # Handle structured response
                    if response.get("message"):
                        print(f"\n{response['message']}")
                        
                        # Add metadata if available
                        if response.get("item_count"):
                            print(f"\n📈 Summary: {response['item_count']} items found")
                        elif response.get("count"):
                            print(f"\n📈 Summary: Count = {response['count']}")
                            
                    elif response.get("response_type"):
                        print(f"\nResponse Type: {response['response_type']}")
                        if response.get("data"):
                            print(f"Data: {response['data']}")
                else:
                    # Handle string response with better formatting
                    print(f"\n{response}")
                    
                print(f"\n" + "="*80)
            
            # Pipeline metadata - aligned with orchestrator structure
            metadata = result.get("pipeline_metadata", {})
            if metadata:
                print(f"\n🔍 Processing Details:")
                print(f"   Security Clearance: {metadata.get('security_clearance', 'unknown')}")
                print(f"   Query Intent: {metadata.get('query_intent', 'unknown')}")
                print(f"   Models Discovered: {metadata.get('models_discovered', 0)}")
                print(f"   Processing Time: {metadata.get('processing_time', 0):.2f}s")
            
            # Proactive insights - aligned with orchestrator structure
            insights = result.get("pipeline_metadata", {}).get("proactive_insights", [])
            if insights:
                print(f"\n💡 Proactive Insights:")
                for insight in insights:
                    try:
                        if isinstance(insight, dict):
                            confidence = insight.get("confidence", 0)
                            message = insight.get("message", insight.get("text", str(insight)))
                            print(f"   • {message} (confidence: {confidence:.1f})")
                            if insight.get("action"):
                                print(f"     Action: {insight['action']}")
                        else:
                            print(f"   • {insight}")
                    except Exception as e:
                        print(f"   • Error displaying insight: {e}")
                        print(f"     Raw insight: {insight}")
            
            # Follow-up suggestions - aligned with orchestrator structure
            suggestions = result.get("pipeline_metadata", {}).get("suggested_follow_ups", [])
            if suggestions:
                print(f"\n🔄 Suggested Follow-ups:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"   {i}. {suggestion}")
        
        else:
            print(f"\n❌ Query failed:")
            if result.get("error"):
                print(f"   Error: {result['error']}")
            
            # Show error details if available
            metadata = result.get("pipeline_metadata", {})
            if metadata.get("error_state"):
                print(f"   Error State: {metadata['error_state']}")
    
    async def run(self):
        """Run the enhanced interactive CLI"""
        
        self.print_banner()
        print("Type 'help' for available commands or 'quit' to exit.\n")
        
        self.is_running = True
        
        while self.is_running:
            try:
                if self.session:
                    prompt = f"[{self.session['username']}@swx-mcp]> "
                else:
                    prompt = "[guest@swx-mcp]> "
                
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit']:
                    print("👋 Goodbye!")
                    self.is_running = False
                    self._cleanup()
                    break
                
                elif user_input.lower() == 'help':
                    self.print_help()
                    continue
                
                elif user_input.lower() == 'status':
                    self.print_status()
                    continue
                
                elif user_input.lower().startswith('authenticate'):
                    parts = user_input.split()
                    if len(parts) == 3:
                        username, password = parts[1], parts[2]
                        self.authenticate_user(username, password)
                    else:
                        print("Usage: authenticate <username> <password>")
                    continue
                
                # Process as query
                if not self.session:
                    print("❌ Please authenticate first. Use 'authenticate <username> <password>'")
                    continue
                
                # Process query through orchestrator
                await self.process_query_enhanced(user_input)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                self.is_running = False
                self._cleanup()
                break
            except EOFError:
                print("\n👋 Goodbye!")
                self.is_running = False
                self._cleanup()
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
    
    def _cleanup(self):
        """Clean up resources when exiting"""
        print("🧹 Cleaning up resources...")
        self._stop_oauth_server()
        # Close orchestrator if it has a close method
        if hasattr(self.orchestrator, 'close'):
            try:
                asyncio.run(self.orchestrator.close())
                print("✅ Orchestrator closed successfully")
            except Exception as e:
                print(f"⚠️ Error closing orchestrator: {e}")
    
    def close(self):
        """Close method for cleanup"""
        self._cleanup()

def main():
    """Main entry point"""
    cli = EnhancedInteractiveCLI()
    asyncio.run(cli.run())

if __name__ == "__main__":
    main()