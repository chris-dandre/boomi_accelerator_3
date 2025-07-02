#!/usr/bin/env python3
"""Trace the exact execution path in CLI agent vs direct test"""
import sys
from pathlib import Path
current_dir = Path(__file__).parent
boomi_clients_dir = current_dir / "boomi_datahub_mcp_server"
sys.path.append(str(current_dir))
sys.path.append(str(boomi_clients_dir))

from integration_test import SyncBoomiMCPClient
from cli_agent.agents.data_retrieval import DataRetrieval

def trace_execution_paths():
    """Compare the execution paths between direct test and CLI agent"""
    print("🔍 Tracing execution paths...")
    
    client = SyncBoomiMCPClient()
    
    # Test 1: Direct client call (this works)
    print("\n1️⃣ Direct client call (working approach)...")
    direct_query = {
        'model_id': '02367877-e560-4d82-b640-6a9f7ab96afa',
        'fields': ['AD_ID'],
        'filters': [],
        'limit': 5
    }
    direct_result = client.execute_query(direct_query)
    print(f"Direct result success: {'status' in direct_result and direct_result['status'] != 'error'}")
    if 'error' in direct_result:
        print(f"Direct error: {direct_result['error']}")
    
    # Test 2: Via DataRetrieval agent (this should work but doesn't in CLI)
    print("\n2️⃣ Via DataRetrieval agent...")
    data_retrieval = DataRetrieval(mcp_client=client)
    
    # Use the exact same query structure that QueryBuilder creates
    agent_query = {
        'query_type': 'COUNT',
        'model_id': '02367877-e560-4d82-b640-6a9f7ab96afa',
        'operations': ['count'],
        'filters': [],
        'fields': ['AD_ID'],
        'metadata': {
            'original_intent': 'COUNT',
            'complexity': 'SIMPLE',
            'entity_count': 0
        }
    }
    
    print(f"Agent query structure: {agent_query}")
    
    try:
        agent_result = data_retrieval.execute_query(agent_query)
        print(f"Agent result success: {agent_result.get('metadata', {}).get('success', False)}")
        if 'error' in agent_result:
            print(f"Agent error: {agent_result['error']}")
        else:
            print(f"Agent result: {agent_result}")
    except Exception as e:
        print(f"Agent exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    trace_execution_paths()