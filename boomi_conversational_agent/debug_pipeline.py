#!/usr/bin/env python3
"""
Debug pipeline to see what's happening at each stage
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
from cli_agent.agents.query_builder import QueryBuilder

def debug_pipeline_step_by_step():
    """Debug each pipeline step individually"""
    print("🔍 Debugging Pipeline Step by Step...")
    
    # Create real MCP client
    mcp_client = SyncBoomiMCPClient()
    
    # Test query
    test_query = "How many advertisements do we have?"
    print(f"\n📝 Test Query: '{test_query}'")
    
    # Step 1: Query Analysis
    print("\n1️⃣ QUERY ANALYSIS")
    query_analyzer = QueryAnalyzer()
    analysis = query_analyzer.analyze(test_query)
    print(f"   Analysis: {analysis}")
    
    # Step 2: Model Discovery
    print("\n2️⃣ MODEL DISCOVERY")
    model_discovery = ModelDiscovery(mcp_client=mcp_client)
    
    # First, get all available models
    print("   Getting all models...")
    all_models = model_discovery.get_all_models()
    print(f"   Found {len(all_models.get('data', {}).get('published', []))} published models")
    
    # Then find relevant models for our query
    print("   Finding relevant models...")
    try:
        relevant_models = model_discovery.find_relevant_models(analysis)
        print(f"   Relevant models: {len(relevant_models)}")
        for model in relevant_models[:3]:  # Show top 3
            print(f"     - {model.get('name', 'Unknown')} (ID: {model.get('model_id', 'Unknown')}) - Score: {model.get('relevance_score', 0):.2f}")
    except Exception as e:
        print(f"   ❌ Error in find_relevant_models: {e}")
        return
    
    # Step 3: Field Mapping
    print("\n3️⃣ FIELD MAPPING")
    if relevant_models:
        primary_model = relevant_models[0]
        model_id = primary_model.get('model_id')
        print(f"   Using primary model: {primary_model.get('name')} (ID: {model_id})")
        
        field_mapper = FieldMapper(mcp_client=mcp_client)
        try:
            # Get fields for the primary model
            model_fields = field_mapper.get_model_fields(model_id)
            print(f"   Model fields result type: {type(model_fields)}")
            
            if isinstance(model_fields, dict) and 'fields' in model_fields:
                print(f"   Found {len(model_fields['fields'])} fields:")
                for field in model_fields['fields'][:3]:  # Show first 3
                    print(f"     - {field.get('name', 'Unknown')} ({field.get('type', 'Unknown')})")
            else:
                print(f"   Raw model fields: {model_fields}")
            
            # Try to map entities to fields
            entities = analysis.get('entities', [])
            print(f"   Mapping {len(entities)} entities to fields...")
            if entities:
                field_mapping = field_mapper.map_entities_to_fields(entities, model_fields.get('fields', []))
                print(f"   Field mapping: {field_mapping}")
            else:
                print("   No entities to map")
                field_mapping = {}
            
        except Exception as e:
            print(f"   ❌ Error in field mapping: {e}")
            import traceback
            traceback.print_exc()
            return
    
    # Step 4: Query Building
    print("\n4️⃣ QUERY BUILDING")
    if relevant_models:
        query_builder = QueryBuilder(mcp_client=mcp_client)
        try:
            query = query_builder.build_query(
                query_analysis=analysis,
                field_mapping=field_mapping,
                model_id=model_id
            )
            print(f"   Built query: {query}")
            print(f"   Query model_id: {query.get('model_id')}")
            print(f"   Query fields: {query.get('fields')}")
            print(f"   Query filters: {query.get('filters')}")
            
        except Exception as e:
            print(f"   ❌ Error in query building: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_pipeline_step_by_step()