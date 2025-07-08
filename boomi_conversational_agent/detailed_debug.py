#!/usr/bin/env python3
"""
Detailed debug to see exact MCP errors
"""

import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def debug_mcp_execution():
    print("🔍 Detailed MCP Execution Debug")
    print("=" * 60)
    
    try:
        from cli_agent.cli_agent import CLIAgent
        from integration_test import SyncBoomiMCPClient
        
        print("🔄 Initializing CLI agent...")
        cli = CLIAgent(mcp_client=SyncBoomiMCPClient())
        
        # Test Sony query
        query = "how many products is Sony advertising?"
        
        print(f"\n🧪 Testing query: '{query}'")
        
        # Process through individual agents to see what's happening
        print("1️⃣ Query Analysis:")
        query_analysis = cli.pipeline.query_analyzer.analyze(query)
        print(f"   Intent: {query_analysis.get('intent')}")
        
        print("\n2️⃣ Model Discovery:")
        relevant_models = cli.pipeline.model_discovery.find_relevant_models(query_analysis)
        primary_model = relevant_models[0]['model_id']
        print(f"   Primary Model: {primary_model}")
        
        print("\n3️⃣ Field Mapping:")
        field_mapping = cli.pipeline.field_mapper.create_field_mapping_for_models(
            query_analysis.get('entities', []),
            relevant_models,
            query
        )
        primary_field_mapping = field_mapping.get(primary_model, {})
        print(f"   Field Mappings: {primary_field_mapping}")
        
        print("\n4️⃣ Query Building:")
        executable_query = cli.pipeline.query_builder.build_query(
            query_analysis,
            primary_field_mapping,
            primary_model
        )
        print(f"   Complete Query Structure:")
        import json
        print(json.dumps(executable_query, indent=2))
        
        print("\n5️⃣ Direct MCP Execution:")
        # Test direct MCP client call
        mcp_client = cli.pipeline.data_retrieval.mcp_client
        
        print("   Testing MCP client directly...")
        try:
            # Add default repository_id if missing
            if 'repository_id' not in executable_query:
                executable_query['repository_id'] = '43212d46-1832-4ab1-820d-c0334d619f6f'
            
            # Add timeout if missing
            if 'timeout' not in executable_query:
                executable_query['timeout'] = 30
                
            print(f"   Query with defaults:")
            print(json.dumps(executable_query, indent=2))
            
            raw_result = mcp_client.execute_query(executable_query)
            print(f"   Raw MCP Result:")
            print(json.dumps(raw_result, indent=2))
            
            # Check if there's an error in the result
            if isinstance(raw_result, dict):
                if 'error' in raw_result:
                    print(f"   ❌ MCP Error: {raw_result['error']}")
                elif 'status' in raw_result and raw_result['status'] == 'error':
                    print(f"   ❌ MCP Status Error: {raw_result.get('error', 'Unknown')}")
                else:
                    print(f"   ✅ MCP Success - Result type: {type(raw_result)}")
                    if 'data' in raw_result:
                        print(f"   📊 Data section: {type(raw_result['data'])}")
                        if isinstance(raw_result['data'], dict) and 'records' in raw_result['data']:
                            records = raw_result['data']['records']
                            print(f"   📋 Records count: {len(records) if isinstance(records, list) else 'Not a list'}")
                            if isinstance(records, list) and len(records) > 0:
                                print(f"   📋 Sample record: {records[0]}")
            
        except Exception as mcp_e:
            print(f"   ❌ MCP Exception: {mcp_e}")
            import traceback
            traceback.print_exc()
        
        print("\n6️⃣ Data Retrieval Agent Execution:")
        # Now test through data retrieval agent
        try:
            result = cli.pipeline.data_retrieval.execute_query(executable_query)
            print(f"   Data Retrieval Result:")
            print(json.dumps(result, indent=2))
        except Exception as dr_e:
            print(f"   ❌ Data Retrieval Exception: {dr_e}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_mcp_execution()