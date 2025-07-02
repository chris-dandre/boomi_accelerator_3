#!/usr/bin/env python3
"""Debug what the optimized query looks like"""
import sys
from pathlib import Path
current_dir = Path(__file__).parent
boomi_clients_dir = current_dir / "boomi_datahub_mcp_server"
sys.path.append(str(current_dir))
sys.path.append(str(boomi_clients_dir))

from integration_test import SyncBoomiMCPClient
from cli_agent.agents.query_analyzer import QueryAnalyzer
from cli_agent.agents.model_discovery import ModelDiscovery
from cli_agent.agents.field_mapper import FieldMapper
from cli_agent.agents.query_builder import QueryBuilder

def debug_query_optimization():
    """Debug the query optimization step that might be causing issues"""
    print("🔍 Debugging query optimization...")
    
    client = SyncBoomiMCPClient()
    
    # Simulate the exact pipeline steps
    test_query = "How many advertisements do we have?"
    
    # Step 1: Query Analysis
    query_analyzer = QueryAnalyzer()
    analysis = query_analyzer.analyze(test_query)
    print(f"Analysis: {analysis}")
    
    # Step 2: Model Discovery  
    model_discovery = ModelDiscovery(mcp_client=client)
    relevant_models = model_discovery.find_relevant_models(analysis)
    primary_model = relevant_models[0] if relevant_models else None
    model_id = primary_model.get('model_id') if primary_model else None
    print(f"Primary model ID: {model_id}")
    
    # Step 3: Field Mapping
    field_mapper = FieldMapper(mcp_client=client)
    entities = analysis.get('entities', [])
    if model_id:
        model_fields = field_mapper.get_model_fields(model_id)
        field_mapping = field_mapper.map_entities_to_fields(entities, model_fields.get('fields', []))
    else:
        field_mapping = {}
    print(f"Field mapping: {field_mapping}")
    
    # Step 4: Query Building
    query_builder = QueryBuilder(mcp_client=client)
    if model_id:
        base_query = query_builder.build_query(analysis, field_mapping, model_id)
        print(f"Base query: {base_query}")
        
        # Step 5: Query Optimization (this might be the problem)
        optimized_query = query_builder.optimize_query(base_query)
        print(f"Optimized query: {optimized_query}")
        
        # Compare the differences
        print(f"\nKey differences:")
        print(f"  Base fields: {base_query.get('fields')}")
        print(f"  Optimized fields: {optimized_query.get('fields')}")
        print(f"  Base model_id: {base_query.get('model_id')}")
        print(f"  Optimized model_id: {optimized_query.get('model_id')}")
        
        # Test if the optimized query works
        print(f"\n🧪 Testing optimized query directly...")
        try:
            result = client.execute_query(optimized_query)
            print(f"Direct test success: {'status' in result and result['status'] != 'error'}")
            if 'error' in result:
                print(f"Direct test error: {result['error']}")
        except Exception as e:
            print(f"Direct test exception: {e}")

if __name__ == "__main__":
    debug_query_optimization()