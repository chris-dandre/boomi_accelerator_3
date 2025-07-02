#!/usr/bin/env python3
"""
Debug LIST query to see what's different from COUNT query
"""

import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def debug_list_vs_count():
    print("🐛 Debugging LIST vs COUNT Query Differences")
    print("=" * 60)
    
    try:
        from cli_agent.cli_agent import CLIAgent
        from integration_test import SyncBoomiMCPClient
        
        print("🔄 Initializing CLI agent...")
        cli = CLIAgent(mcp_client=SyncBoomiMCPClient())
        
        # Test queries
        queries = [
            ("COUNT Query", "how many products is Sony advertising?"),
            ("LIST Query", "list the products that Sony is advertising")
        ]
        
        for query_type, query in queries:
            print(f"\n{'='*60}")
            print(f"🧪 Testing {query_type}: '{query}'")
            print("="*60)
            
            # Process through individual agents to see what's happening
            try:
                # 1. Query Analysis
                print("1️⃣ Query Analysis:")
                query_analysis = cli.pipeline.query_analyzer.analyze(query)
                print(f"   Intent: {query_analysis.get('intent')}")
                print(f"   Entities: {query_analysis.get('entities')}")
                print(f"   Query Type: {query_analysis.get('query_type')}")
                
                # 2. Model Discovery
                print("\n2️⃣ Model Discovery:")
                relevant_models = cli.pipeline.model_discovery.find_relevant_models(query_analysis)
                if relevant_models:
                    primary_model = relevant_models[0]['model_id']
                    print(f"   Primary Model: {primary_model}")
                    print(f"   Model Name: {relevant_models[0].get('name', 'Unknown')}")
                
                # 3. Field Mapping
                print("\n3️⃣ Field Mapping:")
                field_mapping = cli.pipeline.field_mapper.create_field_mapping_for_models(
                    query_analysis.get('entities', []),
                    relevant_models,
                    query
                )
                primary_field_mapping = field_mapping.get(primary_model, {})
                print(f"   Field Mappings: {primary_field_mapping}")
                
                # 4. Query Building
                print("\n4️⃣ Query Building:")
                executable_query = cli.pipeline.query_builder.build_query(
                    query_analysis,
                    primary_field_mapping,
                    primary_model
                )
                print(f"   Model ID: {executable_query.get('model_id')}")
                print(f"   Query Type: {executable_query.get('query_type')}")
                print(f"   Operation: {executable_query.get('operation')}")
                print(f"   Fields: {executable_query.get('fields')}")
                print(f"   Filters: {executable_query.get('filters')}")
                
                # 5. Execute Query
                print("\n5️⃣ Data Retrieval:")
                result = cli.pipeline.data_retrieval.execute_query(executable_query)
                print(f"   Success: {not bool(result.get('error'))}")
                if not result.get('error'):
                    metadata = result.get('metadata', {})
                    record_count = metadata.get('record_count', 0)
                    print(f"   Record Count: {record_count}")
                    
                    # Show some sample data
                    data = result.get('data', [])
                    if data:
                        print(f"   Sample Records: {len(data)}")
                        for i, record in enumerate(data[:2], 1):
                            print(f"     {i}. {record.get('PRODUCT', 'No PRODUCT field')} by {record.get('ADVERTISER', 'No ADVERTISER field')}")
                else:
                    print(f"   Error: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"   ❌ Error in {query_type}: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")

if __name__ == "__main__":
    debug_list_vs_count()