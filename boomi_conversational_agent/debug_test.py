#!/usr/bin/env python3
"""
Simple debug test to see what's happening with the MCP client
"""
import asyncio
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
boomi_clients_dir = current_dir / "boomi_datahub_mcp_server"
sys.path.append(str(current_dir))
sys.path.append(str(boomi_clients_dir))

# Import CLI agent
from cli_agent.cli_agent import CLIAgent

def test_simple_query():
    """Test a simple query to see the actual error"""
    print("🔍 Testing simple query processing...")
    
    # Create CLI agent
    cli_agent = CLIAgent()
    
    # Test a simple query
    query = "How many models are there?"
    print(f"Query: {query}")
    
    try:
        result = cli_agent.process_query(query)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception caught: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_query()