#!/usr/bin/env python3
"""Test dynamic field discovery for all models"""
import sys
from pathlib import Path
current_dir = Path(__file__).parent
boomi_clients_dir = current_dir / "boomi_datahub_mcp_server"
sys.path.append(str(current_dir))
sys.path.append(str(boomi_clients_dir))

from integration_test import SyncBoomiMCPClient
from cli_agent.agents.query_builder import QueryBuilder

def test_dynamic_field_discovery():
    """Test field discovery for all models"""
    print("🔍 Testing dynamic field discovery...")
    
    client = SyncBoomiMCPClient()
    query_builder = QueryBuilder(mcp_client=client)
    
    # Get all models first
    all_models = client.get_all_models()
    if 'data' in all_models and 'published' in all_models['data']:
        models = all_models['data']['published']
        print(f"Found {len(models)} models to test")
        
        for model in models:
            model_name = model.get('name', 'Unknown')
            model_id = model.get('id', 'Unknown')
            
            print(f"\n📊 Model: {model_name} (ID: {model_id})")
            
            # Test dynamic field discovery
            available_fields = query_builder._get_available_fields_for_model(model_id)
            print(f"   Dynamic fields found: {len(available_fields)}")
            if available_fields:
                print(f"   Fields: {available_fields[:5]}{'...' if len(available_fields) > 5 else ''}")
            else:
                print("   ❌ No fields discovered")
                
            # Test fallback to hardcoded fields
            common_fields = query_builder._get_common_fields_for_model(model_id)
            print(f"   Fallback fields: {common_fields}")
            
    else:
        print("❌ Could not get models")

def test_specific_model_queries():
    """Test queries using dynamically discovered fields"""
    print("\n🧪 Testing queries with dynamic fields...")
    
    client = SyncBoomiMCPClient()
    
    test_queries = [
        "How many users do we have?",
        "List engagements",
        "Count opportunities",
        "Show me advertisements"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        
        # Import here to avoid circular imports
        from cli_agent.cli_agent import CLIAgent
        cli = CLIAgent(mcp_client=client)
        
        result = cli.process_query(query)
        print(f"   Success: {result.get('success', False)}")
        if result.get('success'):
            # Try to extract useful info from response
            response = result.get('response', '')
            if 'found' in response.lower():
                print(f"   Result: {response[:100]}...")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")

if __name__ == "__main__":
    test_dynamic_field_discovery()
    test_specific_model_queries()