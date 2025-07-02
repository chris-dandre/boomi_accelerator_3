#!/usr/bin/env python3
"""
Test script for meta-query detection
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent / "boomi_conversational_agent"
sys.path.append(str(parent_dir))

def test_meta_query():
    print("🧪 Testing Meta-Query Detection")
    print("=" * 50)
    
    try:
        from cli_agent.cli_agent import CLIAgent
        from integration_test import SyncBoomiMCPClient
        from claude_client import ClaudeClient
        
        print("🔄 Initializing clients...")
        mcp_client = SyncBoomiMCPClient()
        claude_client = ClaudeClient()
        cli = CLIAgent(mcp_client=mcp_client, claude_client=claude_client)
        
        print("✅ Clients initialized successfully")
        
        # Test meta-queries
        meta_queries = [
            "list models",
            "list all data models", 
            "what models are available",
            "show me the data models"
        ]
        
        # Test data queries
        data_queries = [
            "list users",
            "show Sony products",
            "count advertisements"
        ]
        
        print("\n🔍 Testing Meta-Queries (should show system structure):")
        print("-" * 50)
        
        for query in meta_queries:
            print(f"\n💭 Query: '{query}'")
            try:
                result = cli.process_query(query)
                if result.get('success'):
                    response = result.get('response', {})
                    print(f"✅ Response Type: {response.get('response_type', 'Unknown')}")
                    message = response.get('message', '')
                    print(f"📝 Message Preview: {message[:100]}...")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Exception: {e}")
        
        print(f"\n🔍 Testing Data Queries (should query actual data):")
        print("-" * 50)
        
        for query in data_queries:
            print(f"\n💭 Query: '{query}'")
            try:
                result = cli.process_query(query)
                if result.get('success'):
                    response = result.get('response', {})
                    print(f"✅ Response Type: {response.get('response_type', 'Unknown')}")
                    
                    # Check if it used a specific model
                    metadata = result.get('pipeline_metadata', {})
                    model_info = metadata.get('model_discovery', {})
                    if model_info:
                        primary_model = model_info.get('primary_model')
                        print(f"📋 Model Used: {primary_model}")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Exception: {e}")
        
        print(f"\n✅ Meta-query detection test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are available")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_meta_query()