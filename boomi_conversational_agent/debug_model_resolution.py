#!/usr/bin/env python3
"""Debug model resolution to see what's happening with UUIDs vs names"""
import sys
from pathlib import Path
current_dir = Path(__file__).parent
boomi_clients_dir = current_dir / "boomi_datahub_mcp_server"
sys.path.append(str(current_dir))
sys.path.append(str(boomi_clients_dir))

from integration_test import SyncBoomiMCPClient

def test_model_resolution():
    """Test if the issue is UUID vs model name"""
    print("🔍 Testing model resolution...")
    
    client = SyncBoomiMCPClient()
    
    # First, get all models to see their names and IDs
    print("\n1️⃣ Getting all models...")
    all_models = client.get_all_models()
    if 'data' in all_models and 'published' in all_models['data']:
        print(f"Found {len(all_models['data']['published'])} published models:")
        for model in all_models['data']['published']:
            print(f"   - Name: '{model.get('name', 'Unknown')}' | ID: '{model.get('id', 'Unknown')}'")
    
    # Test querying with UUID (current failing approach)
    print("\n2️⃣ Testing query with UUID...")
    uuid_query = {
        'model_id': '02367877-e560-4d82-b640-6a9f7ab96afa',  # Real UUID
        'fields': ['AD_ID'],
        'filters': [],
        'limit': 5
    }
    uuid_result = client.execute_query(uuid_query)
    print(f"UUID result success: {'status' in uuid_result and uuid_result['status'] != 'error'}")
    if 'error' in uuid_result:
        print(f"UUID error: {uuid_result['error']}")
    
    # Test querying with model name (potential fix)
    print("\n3️⃣ Testing query with model name...")
    name_query = {
        'model_id': 'Advertisements',  # Model name instead of UUID
        'fields': ['AD_ID'],
        'filters': [],
        'limit': 5
    }
    name_result = client.execute_query(name_query)
    print(f"Name result success: {'status' in name_result and name_result['status'] != 'error'}")
    if 'error' in name_result:
        print(f"Name error: {name_result['error']}")
    
    # Test with lowercase name
    print("\n4️⃣ Testing query with lowercase name...")
    lower_query = {
        'model_id': 'advertisements',  # Lowercase model name
        'fields': ['AD_ID'],
        'filters': [],
        'limit': 5
    }
    lower_result = client.execute_query(lower_query)
    print(f"Lowercase result success: {'status' in lower_result and lower_result['status'] != 'error'}")
    if 'error' in lower_result:
        print(f"Lowercase error: {lower_result['error']}")

if __name__ == "__main__":
    test_model_resolution()