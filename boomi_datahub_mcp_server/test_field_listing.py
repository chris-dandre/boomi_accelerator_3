#!/usr/bin/env python3
"""
Test field listing functionality
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent / "boomi_conversational_agent"
sys.path.append(str(parent_dir))

def test_field_listing():
    print("🧪 Testing Field Listing Functionality")
    print("=" * 50)
    
    try:
        from cli_agent.cli_agent import CLIAgent
        from integration_test import SyncBoomiMCPClient
        from claude_client import ClaudeClient
        
        print("🔄 Initializing clients...")
        mcp_client = SyncBoomiMCPClient()
        claude_client = ClaudeClient()
        cli = CLIAgent(mcp_client=mcp_client, claude_client=claude_client)
        
        print("✅ Clients initialized successfully")
        
        # Test field listing queries
        field_queries = [
            "list all fields in the advertisements model",
            "show me fields in users model",
            "what fields are in the opportunity model"
        ]
        
        print("\n🔍 Testing Field Listing Queries:")
        print("-" * 50)
        
        for query in field_queries:
            print(f"\n💭 Query: '{query}'")
            try:
                result = cli.process_query(query)
                if result.get('success'):
                    response = result.get('response', {})
                    response_type = response.get('response_type', 'Unknown')
                    print(f"✅ Response Type: {response_type}")
                    
                    message = response.get('message', '')
                    # Show first few lines of the response
                    lines = message.split('\n')[:8]
                    preview = '\n'.join(lines)
                    print(f"📝 Response Preview:\n{preview}")
                    if len(lines) < len(message.split('\n')):
                        print("...")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Exception: {e}")
        
        print(f"\n✅ Field listing test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are available")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_field_listing()