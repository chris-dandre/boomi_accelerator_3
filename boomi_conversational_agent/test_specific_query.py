#!/usr/bin/env python3
"""
Test a specific query that should work with real Boomi models
"""
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
boomi_clients_dir = current_dir / "boomi_datahub_mcp_server"
sys.path.append(str(current_dir))
sys.path.append(str(boomi_clients_dir))

from integration_test import SyncBoomiMCPClient
from cli_agent.cli_agent import CLIAgent

def test_specific_real_query():
    """Test a specific query using real models"""
    print("🔍 Testing specific query with real models...")
    
    # Create real MCP client
    mcp_client = SyncBoomiMCPClient()
    
    # Create CLI agent with real client
    cli_agent = CLIAgent(mcp_client=mcp_client, claude_client=None)
    
    # Test a query that should map to a real model
    test_queries = [
        "How many advertisements do we have?",          # Should map to Advertisements model
        "Show me users",                               # Should map to users model  
        "Count opportunities",                         # Should map to opportunity model
        "List engagements"                             # Should map to Engagements model
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        try:
            result = cli_agent.process_query(query)
            print(f"✅ Success: {result['success']}")
            if result['success']:
                print(f"   Response: {result['response'][:100]}...")
                print(f"   Response Type: {result.get('response_type', 'Unknown')}")
                print(f"   Time: {result['execution_time']:.1f}ms")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_specific_real_query()