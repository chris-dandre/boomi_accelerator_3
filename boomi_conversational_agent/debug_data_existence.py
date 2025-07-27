#!/usr/bin/env python3
"""
Debug Data Existence
Check if there's any data at all in the Advertisements model
"""

import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.append('.')

from shared.mcp_orchestrator import create_orchestrator
from shared.oauth_client import oauth_client

def debug_data_existence():
    """Check if Advertisements model has any data"""
    print("🧪 Debugging Data Existence in Advertisements Model")
    print("=" * 55)
    
    # Create orchestrator and get authenticated client
    orchestrator = create_orchestrator(interface_type="cli")
    mcp_client = orchestrator.workflow_nodes.mcp_client
    
    # Get OAuth token
    print("🔐 Getting OAuth token...")
    auth_result = oauth_client.authenticate("sarah.chen", "executive.access.2024")
    
    if not auth_result["success"]:
        print(f"❌ Authentication failed: {auth_result['error']}")
        return
        
    bearer_token = auth_result["access_token"]
    mcp_client.set_bearer_token(bearer_token)
    print(f"✅ Authenticated with token: {bearer_token[:30]}...")
    print()
    
    # Advertisements model ID
    advertisements_model_id = "02367877-e560-4d82-b640-6a9f7ab96afa"
    
    # Test 1: Basic count query - just count all records
    print("🔍 Test 1: Count all records in Advertisements model...")
    try:
        count_query = {
            "model_id": advertisements_model_id,
            "fields": ["AD_ID"],  # Just get AD_ID for counting
            "filters": [],        # No filters - get everything
            "limit": 100         # Get up to 100 records
        }
        
        result = mcp_client.execute_query(count_query)
        print(f"📊 Count query result: {result}")
        
        if isinstance(result, dict):
            if result.get('status') == 'success' and 'data' in result:
                records = result['data']
                print(f"✅ Found {len(records)} total records")
                
                if records:
                    print(f"📋 First few records:")
                    for i, record in enumerate(records[:3]):
                        print(f"   Record {i+1}: {record}")
                else:
                    print("⚠️  Model exists but contains no records")
            else:
                print(f"❌ Query failed: {result}")
        else:
            print(f"❌ Unexpected result type: {type(result)}")
            
    except Exception as e:
        print(f"❌ Count query failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 2: Try to get field samples directly
    print("🔍 Test 2: Try sampling ADVERTISER field specifically...")
    try:
        advertiser_sample = mcp_client.sample_field_data(advertisements_model_id, "ADVERTISER", limit=10)
        print(f"📊 ADVERTISER sample result: {advertiser_sample}")
        
        if advertiser_sample.get('status') == 'success':
            field_values = advertiser_sample.get('field_values', [])
            sample_size = advertiser_sample.get('sample_size', 0)
            print(f"✅ ADVERTISER field has {sample_size} values: {field_values}")
        else:
            print(f"❌ ADVERTISER sampling failed: {advertiser_sample.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ ADVERTISER sampling exception: {e}")
    
    print()
    
    # Test 3: Try a simple direct query for Sony
    print("🔍 Test 3: Direct query for ADVERTISER = 'Sony'...")
    try:
        sony_query = {
            "model_id": advertisements_model_id,
            "fields": ["AD_ID", "ADVERTISER", "PRODUCT"],
            "filters": [{"fieldId": "ADVERTISER", "operator": "EQUALS", "value": "Sony"}],
            "limit": 10
        }
        
        result = mcp_client.execute_query(sony_query)
        print(f"📊 Sony query result: {result}")
        
    except Exception as e:
        print(f"❌ Sony query failed: {e}")
        
    print()
    print("🔍 Summary:")
    print("   If all tests show 0 records, the model may be empty")
    print("   If basic count works but sampling fails, there's a sampling issue") 
    print("   If Sony query works, the data exists but field mapping was wrong")

if __name__ == "__main__":
    debug_data_existence()