#!/usr/bin/env python3
"""
Test real connection to Boomi DataHub to see what's available
"""
import asyncio
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
boomi_clients_dir = current_dir / "boomi_datahub_mcp_server"
sys.path.append(str(current_dir))
sys.path.append(str(boomi_clients_dir))

from integration_test import SyncBoomiMCPClient

def test_connection():
    """Test what models are actually available"""
    print("🔍 Testing real Boomi DataHub connection...")
    
    try:
        # Create synchronous MCP client
        client = SyncBoomiMCPClient()
        
        # Test connection
        print("\n1. Testing MCP server connection...")
        connection_result = client.test_connection()
        print(f"Connection result: {connection_result}")
        
        # Get all models
        print("\n2. Getting all available models...")
        models_result = client.get_all_models()
        print(f"Models result: {models_result}")
        
        # If models are returned, show what's available
        if isinstance(models_result, dict) and models_result.get('status') != 'error':
            if 'models' in models_result:
                models = models_result['models']
                print(f"\n✅ Found {len(models)} models:")
                for i, model in enumerate(models, 1):
                    print(f"  {i}. {model.get('id', 'Unknown ID')} - {model.get('name', 'Unknown Name')}")
            else:
                print(f"✅ Models data structure: {list(models_result.keys())}")
        else:
            print(f"❌ Error getting models: {models_result}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()