#!/usr/bin/env python3
"""
Quick test script to verify the CLI agent is working
Run this to test a few queries automatically
"""

import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def test_cli_agent():
    print("🧪 Quick Test of Boomi DataHub CLI Agent")
    print("=" * 50)
    
    try:
        from cli_agent.cli_agent import CLIAgent
        from integration_test import SyncBoomiMCPClient
        
        print("🔄 Initializing CLI agent...")
        cli = CLIAgent(mcp_client=SyncBoomiMCPClient())
        print("✅ CLI agent initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        print("\n🔧 Make sure:")
        print("1. MCP server is running: python ../boomi_mcp_server/boomi_datahub_mcp_server_v2.py")
        print("2. You're in the boomi_conversational_agent directory")
        return
    
    # Test queries
    test_queries = [
        "How many advertisements do we have?",
        "Count users in the system",
        "Show me opportunities",
        "List engagements"
    ]
    
    print(f"\n🎯 Testing {len(test_queries)} queries...")
    print("=" * 50)
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("🔄 Processing...")
        
        try:
            result = cli.process_query(query)
            
            if result.get('success'):
                response = result.get('response', {})
                if isinstance(response, dict):
                    message = response.get('message', str(response))
                else:
                    message = str(response)
                
                print(f"✅ SUCCESS: {message}")
                
                # Extract metadata
                metadata = result.get('pipeline_metadata', {})
                model_info = metadata.get('model_discovery', {})
                data_info = metadata.get('data_retrieval', {})
                
                if model_info:
                    primary_model = model_info.get('primary_model')
                    if primary_model:
                        print(f"   📋 Model: {primary_model}")
                
                if data_info:
                    record_count = data_info.get('record_count')
                    if record_count is not None:
                        print(f"   📊 Records: {record_count}")
                
                exec_time = metadata.get('total_execution_time_ms', 0)
                print(f"   ⏱️  Time: {exec_time:.0f}ms")
                
                results.append(True)
                
            else:
                error = result.get('error', 'Unknown error')
                print(f"❌ FAILED: {error}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    successful = sum(results)
    total = len(results)
    success_rate = (successful / total) * 100 if total > 0 else 0
    
    print(f"✅ Successful queries: {successful}/{total}")
    print(f"📈 Success rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 All tests passed! CLI agent is working perfectly.")
        print("\n🚀 Ready to run interactive sessions:")
        print("   python interactive_cli.py")
        print("   python advanced_cli.py")
    elif success_rate > 0:
        print("⚠️  Some tests passed. CLI agent partially working.")
        print("💡 Check MCP server connection and Boomi credentials")
    else:
        print("❌ All tests failed. Check system configuration.")
    
    print("=" * 50)

if __name__ == "__main__":
    test_cli_agent()