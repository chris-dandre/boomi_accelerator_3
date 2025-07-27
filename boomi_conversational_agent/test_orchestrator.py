"""
Test script for the Phase 8B LangGraph Orchestrator

⚠️ COMPLIANCE WARNING: This test uses a NON-COMPLIANT MCP server
The current server does NOT meet MCP June 2025 specification requirements.
Phase 9A implementation required for full compliance.

Current test demonstrates Phase 8B functionality with non-compliant MCP integration.
"""

import asyncio
import sys
import os
import json
import time
import subprocess
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.mcp_orchestrator import create_orchestrator
from shared.oauth_client import oauth_client

class TestOAuthServer:
    """Helper class to manage OAuth server for testing"""
    
    def __init__(self):
        self.server_process: Optional[subprocess.Popen] = None
        self.server_ready = False
    
    def start_oauth_server(self) -> bool:
        """Start the OAuth server for testing"""
        try:
            print("🔐 Starting OAuth server for testing...")
            
            # Start the OAuth server component
            self.server_process = subprocess.Popen(
                [sys.executable, "run_oauth_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'  # Fix encoding for emoji support
            )
            
            # Wait for server to be ready
            max_wait = 10
            for i in range(max_wait):
                if self.server_process.poll() is not None:
                    stdout, stderr = self.server_process.communicate()
                    print(f"❌ OAuth server failed to start:")
                    print(f"   STDOUT: {stdout}")
                    print(f"   STDERR: {stderr}")
                    return False
                
                # Test if server is responding
                try:
                    import httpx
                    with httpx.Client() as client:
                        response = client.get("http://localhost:8001/health", timeout=1)
                        if response.status_code == 200:
                            print("✅ OAuth server is ready")
                            self.server_ready = True
                            return True
                except:
                    pass
                
                time.sleep(1)
                print(f"⏳ Waiting for OAuth server... ({i+1}/{max_wait})")
            
            print("❌ OAuth server failed to start within timeout")
            return False
            
        except Exception as e:
            print(f"❌ Error starting OAuth server: {e}")
            return False
    
    def stop_oauth_server(self):
        """Stop the OAuth server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("✅ OAuth server stopped")
            except:
                self.server_process.kill()
                print("⚠️  OAuth server force-killed")
            finally:
                self.server_process = None
                self.server_ready = False

async def test_orchestrator():
    """Test the orchestrator with different user scenarios"""
    
    print("🧪 Testing Phase 8B LangGraph Orchestrator")
    print("=" * 50)
    
    # Test scenarios with real OAuth authentication
    test_scenarios = [
        {
            "name": "Executive User - Sarah Chen",
            "credentials": {
                "username": "sarah.chen",
                "password": "executive.access.2024"
            },
            "queries": [
                "list models in datahub",
                "how many advertisements do we have?",
                "show me user data"
            ]
        },
        {
            "name": "Manager User - David Williams",
            "credentials": {
                "username": "david.williams",
                "password": "manager.access.2024"
            },
            "queries": [
                "count engagements",
                "show advertisement performance"
            ]
        },
        {
            "name": "Clerk User - Alex Smith",
            "credentials": {
                "username": "alex.smith",
                "password": "newuser123"
            },
            "queries": [
                "list models",
                "show user data"
            ]
        }
    ]
    
    # Test each scenario
    for scenario in test_scenarios:
        print(f"\n🔍 Testing: {scenario['name']}")
        print("-" * 30)
        
        # Get real OAuth token
        username = scenario['credentials']['username']
        password = scenario['credentials']['password']
        
        print(f"🔐 Authenticating with OAuth: {username}")
        bearer_token = get_oauth_token(username, password)
        
        if not bearer_token:
            print(f"❌ Authentication failed for {username}")
            continue
        
        print(f"✅ OAuth token obtained: {bearer_token[:50]}...")
        
        # Create orchestrator
        orchestrator = create_orchestrator(interface_type="cli")
        
        # User context will be populated by token introspection
        user_context = {
            "role": "unknown",  # Will be populated by introspection
            "username": username,
            "permissions": [],
            "has_data_access": False
        }
        
        for query in scenario['queries']:
            print(f"\n📝 Query: '{query}'")
            
            try:
                start_time = time.time()
                
                # Process query
                result = await orchestrator.process_query(
                    query=query,
                    user_context=user_context,
                    bearer_token=bearer_token
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Display results
                print(f"⏱️  Processing Time: {processing_time:.2f}s")
                print(f"✅ Success: {result.get('success', False)}")
                
                if result.get('success'):
                    metadata = result.get('pipeline_metadata', {})
                    print(f"🔒 Security Clearance: {metadata.get('security_clearance', 'unknown')}")
                    print(f"🧠 Query Intent: {metadata.get('query_intent', 'unknown')}")
                    print(f"📊 Models Discovered: {metadata.get('models_discovered', 0)}")
                    
                    # Show insights
                    insights = metadata.get('proactive_insights', [])
                    if insights:
                        print(f"💡 Insights: {len(insights)} generated")
                        for insight in insights[:2]:  # Show first 2
                            print(f"   • {insight.get('message', 'No message')}")
                    
                    # Show follow-ups
                    followups = metadata.get('suggested_follow_ups', [])
                    if followups:
                        print(f"🔄 Follow-ups: {len(followups)} suggested")
                        for followup in followups[:2]:  # Show first 2
                            print(f"   • {followup}")
                    
                    # Show response preview
                    response = result.get('response', '')
                    if response:
                        preview = response[:100] + "..." if len(response) > 100 else response
                        print(f"📋 Response Preview: {preview}")
                
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
                    metadata = result.get('pipeline_metadata', {})
                    if metadata.get('error_state'):
                        print(f"🔴 Error State: {metadata['error_state']}")
                
            except Exception as e:
                print(f"❌ Exception: {e}")
        
        print(f"\n📊 Scenario '{scenario['name']}' completed")
    
    print("\n🎉 All tests completed!")

async def test_orchestrator_state():
    """Test orchestrator state management"""
    
    print("\n🔧 Testing State Management")
    print("=" * 30)
    
    orchestrator = create_orchestrator(interface_type="cli")
    
    # Get orchestrator summary
    summary = orchestrator.get_state_summary()
    print(f"📊 Orchestrator Summary:")
    print(f"   Type: {summary.get('orchestrator_type', 'unknown')}")
    print(f"   Nodes Initialized: {summary.get('workflow_nodes_initialized', False)}")
    print(f"   Graph Compiled: {summary.get('graph_compiled', False)}")
    
    # Test with simple query
    user_context = {
        "role": "executive",
        "username": "test_user",
        "permissions": ["READ_ALL"],
        "has_data_access": True
    }
    
    try:
        result = await orchestrator.process_query(
            query="test query",
            user_context=user_context,
            bearer_token="test_token"
        )
        
        print(f"✅ State test completed successfully")
        
    except Exception as e:
        print(f"❌ State test failed: {e}")

def main():
    """Main test function"""
    
    print("🚀 Starting Phase 8B Orchestrator Tests")
    print("=" * 50)
    
    # Initialize OAuth server
    oauth_server = TestOAuthServer()
    
    try:
        # Start OAuth server for testing
        oauth_started = oauth_server.start_oauth_server()
        
        if oauth_started:
            print("✅ OAuth server started successfully for testing")
            time.sleep(2)  # Give server time to fully initialize
        else:
            print("⚠️  OAuth server failed to start, testing in offline mode")
        
        # Run tests
        asyncio.run(test_orchestrator())
        asyncio.run(test_orchestrator_state())
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
    finally:
        # Always stop OAuth server
        oauth_server.stop_oauth_server()

if __name__ == "__main__":
    main()