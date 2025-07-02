#!/usr/bin/env python3
"""
Test MCP client directly to isolate the error
"""

import sys
import os
from pathlib import Path

# Add conversational agent to path
conversation_dir = Path(__file__).parent.parent / "boomi_conversational_agent"
sys.path.append(str(conversation_dir))

def test_mcp_direct():
    print("🔍 Testing MCP Client Directly")
    print("=" * 50)
    
    try:
        from integration_test import SyncBoomiMCPClient
        
        print("✅ Creating MCP client...")
        mcp_client = SyncBoomiMCPClient()
        
        # Test simple query structure
        test_query = {
            'model_id': '02367877-e560-4d82-b640-6a9f7ab96afa',
            'repository_id': '43212d46-1832-4ab1-820d-c0334d619f6f',
            'query_type': 'COUNT',
            'fields': ['ADVERTISER', 'PRODUCT'],
            'filters': [
                {
                    'field': 'ADVERTISER',
                    'operator': 'EQUALS',
                    'value': 'Sony'
                }
            ],
            'timeout': 30
        }
        
        print("📋 Test Query:")
        import json
        print(json.dumps(test_query, indent=2))
        
        print("\n🔄 Executing query...")
        result = mcp_client.execute_query(test_query)
        
        print("\n📊 Result:")
        print(json.dumps(result, indent=2))
        
        # Check result type
        if isinstance(result, dict):
            if 'error' in result:
                print(f"\n❌ Error found: {result['error']}")
            elif 'status' in result and result['status'] == 'error':
                print(f"\n❌ Status error: {result.get('error', 'Unknown')}")
            else:
                print("\n✅ Success! No error found.")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mcp_direct()