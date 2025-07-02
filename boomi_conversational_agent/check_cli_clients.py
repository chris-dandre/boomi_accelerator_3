#!/usr/bin/env python3
"""Check CLI agent client types"""
import sys
from pathlib import Path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from cli_agent.cli_agent import CLIAgent
from integration_test import SyncBoomiMCPClient

print("Creating CLI agent with real MCP client...")
cli = CLIAgent(mcp_client=SyncBoomiMCPClient())

print(f"CLI agent mcp_client type: {type(cli.mcp_client)}")
print(f"CLI agent data_retrieval.mcp_client type: {type(cli.data_retrieval.mcp_client)}")
print(f"CLI agent model_discovery.mcp_client type: {type(cli.model_discovery.mcp_client)}")
print(f"CLI agent field_mapper.mcp_client type: {type(cli.field_mapper.mcp_client)}")
print(f"CLI agent query_builder.mcp_client type: {type(cli.query_builder.mcp_client)}")

# Check if they're the same object
print(f"Are they the same object? {cli.mcp_client is cli.data_retrieval.mcp_client}")