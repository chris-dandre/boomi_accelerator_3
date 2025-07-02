#!/usr/bin/env python3
"""
Test dynamic model and field discovery with real Boomi DataHub
"""
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
boomi_clients_dir = current_dir / "boomi_datahub_mcp_server"
sys.path.append(str(current_dir))
sys.path.append(str(boomi_clients_dir))

from integration_test import SyncBoomiMCPClient
from cli_agent.agents.query_analyzer import QueryAnalyzer
from cli_agent.agents.model_discovery import ModelDiscovery
from cli_agent.agents.field_mapper import FieldMapper

def test_dynamic_discovery():
    """Test dynamic discovery of real models and fields"""
    print("🔍 Testing Dynamic Model & Field Discovery...")
    
    # Create real MCP client
    mcp_client = SyncBoomiMCPClient()
    
    # Test 1: Dynamic Model Discovery
    print("\n1. Testing dynamic model discovery...")
    model_discovery = ModelDiscovery(mcp_client=mcp_client)
    
    try:
        # Get all real models
        all_models = model_discovery.get_all_models()
        print(f"✅ Retrieved {len(all_models.get('data', {}).get('published', []))} published models")
        
        # Show what we found
        if 'data' in all_models and 'published' in all_models['data']:
            for model in all_models['data']['published']:
                print(f"  - {model['name']} (ID: {model['id']})")
    except Exception as e:
        print(f"❌ Model discovery failed: {e}")
        return
    
    # Test 2: Query Analysis with Real Context  
    print("\n2. Testing query analysis...")
    query_analyzer = QueryAnalyzer()
    test_query = "How many advertisements do we have?"
    
    analysis = query_analyzer.analyze(test_query)
    print(f"✅ Query analysis: {analysis}")
    
    # Test 3: Dynamic Field Discovery
    print("\n3. Testing dynamic field discovery...")
    field_mapper = FieldMapper(mcp_client=mcp_client)
    
    # Try to get fields for the Advertisements model (which we know exists)
    ads_model_id = "02367877-e560-4d82-b640-6a9f7ab96afa"
    try:
        model_fields = field_mapper.get_model_fields(ads_model_id)
        print(f"✅ Fields for Advertisements model:")
        if isinstance(model_fields, dict) and 'fields' in model_fields:
            for field in model_fields['fields'][:5]:  # Show first 5 fields
                print(f"  - {field.get('name', 'Unknown')} ({field.get('type', 'Unknown type')})")
        else:
            print(f"  Raw response: {model_fields}")
    except Exception as e:
        print(f"❌ Field discovery failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Model Selection Logic
    print("\n4. Testing model selection for query...")
    if 'data' in all_models:
        query_analysis = {"intent": "COUNT", "entities": [{"text": "advertisements", "type": "OBJECT"}]}
        relevant_models = model_discovery.find_relevant_models(query_analysis)
        print(f"✅ Relevant models for 'advertisements' query: {len(relevant_models)}")
        for model in relevant_models[:3]:  # Show top 3
            print(f"  - {model.get('name')} (confidence: {model.get('confidence', 'N/A')})")

if __name__ == "__main__":
    test_dynamic_discovery()