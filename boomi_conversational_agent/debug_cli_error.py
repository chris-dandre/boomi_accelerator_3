#!/usr/bin/env python3
"""Debug CLI error to see what's happening"""
import sys
from pathlib import Path
current_dir = Path(__file__).parent
boomi_clients_dir = current_dir / "boomi_datahub_mcp_server"
sys.path.append(str(current_dir))
sys.path.append(str(boomi_clients_dir))

from integration_test import SyncBoomiMCPClient
from cli_agent.cli_agent import CLIAgent

print("Creating CLI agent with real MCP client...")
cli = CLIAgent(mcp_client=SyncBoomiMCPClient())

# Test the exact same query
query = 'How many advertisements do we have?'
print(f"Testing query: '{query}'")

result = cli.process_query(query)
print(f"Final result success: {result.get('success', False)}")
print(f"Final result error: {result.get('error', 'No error')}")