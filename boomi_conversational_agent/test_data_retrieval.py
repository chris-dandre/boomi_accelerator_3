#!/usr/bin/env python3
"""
Test the DataRetrieval stage specifically
"""
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
boomi_clients_dir = current_dir / "boomi_datahub_mcp_server"
sys.path.append(str(current_dir))
sys.path.append(str(boomi_clients_dir))

from integration_test import SyncBoomiMCPClient
from cli_agent.agents.data_retrieval import DataRetrieval

def test_data_retrieval_directly():
    """Test DataRetrieval with real model ID"""
    print("🔍 Testing DataRetrieval directly...")
    
    # Create real MCP client
    mcp_client = SyncBoomiMCPClient()
    
    # Create DataRetrieval agent
    data_retrieval = DataRetrieval(mcp_client=mcp_client)
    
    # Test with the real Advertisements model ID (using valid field names)
    test_query = {
        'query_type': 'COUNT',
        'model_id': '02367877-e560-4d82-b640-6a9f7ab96afa',  # Real Advertisements model ID
        'operations': ['count'],
        'filters': [],
        'fields': ['AD_ID'],  # Use valid field name instead of '*'
        'metadata': {
            'original_intent': 'COUNT',
            'complexity': 'SIMPLE',
            'entity_count': 0
        }
    }
    
    print(f"📝 Test Query: {test_query}")
    print(f"🎯 Model ID: {test_query['model_id']}")
    
    try:
        result = data_retrieval.execute_query(test_query)
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
    
    # Also test the raw MCP client directly
    print("\n🔍 Testing raw MCP client...")
    try:
        # Test with the exact parameters our wrapper should use
        raw_result = mcp_client.execute_query(test_query)
        print(f"✅ Raw MCP result: {raw_result}")
    except Exception as e:
        print(f"❌ Raw MCP exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_retrieval_directly()