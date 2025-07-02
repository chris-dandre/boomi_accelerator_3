#!/usr/bin/env python3
"""Add logging to see exactly what queries are being executed"""
import sys
from pathlib import Path
current_dir = Path(__file__).parent
boomi_clients_dir = current_dir / "boomi_datahub_mcp_server"
sys.path.append(str(current_dir))
sys.path.append(str(boomi_clients_dir))

from integration_test import SyncBoomiMCPClient
from cli_agent.cli_agent import CLIAgent

# Monkey patch the SyncBoomiMCPClient to add logging
original_execute_query = SyncBoomiMCPClient.execute_query

def logged_execute_query(self, query):
    """Wrapper to log all execute_query calls"""
    print(f"\n🔍 EXECUTING QUERY:")
    print(f"   Query structure: {query}")
    print(f"   Model ID: {query.get('model_id', 'MISSING')}")
    print(f"   Fields: {query.get('fields', 'MISSING')}")
    
    result = original_execute_query(self, query)
    
    print(f"📋 QUERY RESULT:")
    if 'error' in result:
        print(f"   ❌ Error: {result['error']}")
    else:
        print(f"   ✅ Success: {result.get('status', 'unknown')}")
    
    return result

# Apply the monkey patch
SyncBoomiMCPClient.execute_query = logged_execute_query

def test_with_logging():
    """Test CLI agent with detailed logging"""
    print("🔍 Testing CLI agent with detailed logging...")
    
    cli = CLIAgent(mcp_client=SyncBoomiMCPClient())
    
    query = 'How many advertisements do we have?'
    print(f"\n📝 User Query: '{query}'")
    
    result = cli.process_query(query)
    
    print(f"\n📊 Final CLI Result:")
    print(f"   Success: {result.get('success', False)}")
    if 'error' in result:
        print(f"   Error: {result['error']}")

if __name__ == "__main__":
    test_with_logging()