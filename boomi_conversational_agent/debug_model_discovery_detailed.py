#!/usr/bin/env python3
"""Debug exactly what ModelDiscovery returns in CLI vs direct test"""
import sys
from pathlib import Path
current_dir = Path(__file__).parent
boomi_clients_dir = current_dir / "boomi_datahub_mcp_server"
sys.path.append(str(current_dir))
sys.path.append(str(boomi_clients_dir))

from integration_test import SyncBoomiMCPClient
from cli_agent.agents.query_analyzer import QueryAnalyzer
from cli_agent.agents.model_discovery import ModelDiscovery

# Monkey patch ModelDiscovery to add logging
original_find_relevant_models = ModelDiscovery.find_relevant_models

def logged_find_relevant_models(self, query_analysis):
    """Wrapper to log model discovery results"""
    print(f"\n🔍 MODEL DISCOVERY INPUT:")
    print(f"   Query analysis: {query_analysis}")
    print(f"   Self has mcp_client: {self.mcp_client is not None}")
    print(f"   MCP client type: {type(self.mcp_client)}")
    
    result = original_find_relevant_models(self, query_analysis)
    
    print(f"📋 MODEL DISCOVERY OUTPUT:")
    print(f"   Found {len(result)} relevant models")
    for i, model in enumerate(result):
        print(f"   Model {i}: {model}")
    
    return result

# Apply the monkey patch
ModelDiscovery.find_relevant_models = logged_find_relevant_models

def test_model_discovery_direct_vs_cli():
    """Compare ModelDiscovery results when called directly vs via CLI"""
    print("🔍 Comparing ModelDiscovery results...")
    
    client = SyncBoomiMCPClient()
    query_analysis = {'intent': 'COUNT', 'entities': [], 'query_type': 'SIMPLE'}
    
    # Test 1: Direct call to ModelDiscovery (this should work)
    print("\n1️⃣ Direct ModelDiscovery call:")
    model_discovery_direct = ModelDiscovery(mcp_client=client)
    direct_result = model_discovery_direct.find_relevant_models(query_analysis)
    
    # Test 2: Via CLI agent pipeline (this fails)
    print("\n2️⃣ Via CLI agent (should show the problem):")
    from cli_agent.cli_agent import CLIAgent
    cli = CLIAgent(mcp_client=client)
    print(f"CLI pipeline model discovery client type: {type(cli.pipeline.model_discovery.mcp_client)}")
    
    # This should trigger the logged model discovery
    cli_result = cli.process_query("How many advertisements do we have?")

if __name__ == "__main__":
    test_model_discovery_direct_vs_cli()