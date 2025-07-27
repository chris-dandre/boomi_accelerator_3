#!/usr/bin/env python3
"""
Test script to verify the authentication fix for DataHub record queries
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

# Load environment variables
load_dotenv()

try:
    from boomi_datahub_mcp_server.boomi_datahub_client import BoomiDataHubClient
    
    print("🧪 Testing Authentication Fix for DataHub Record Queries")
    print("=" * 60)
    
    # Initialize client
    client = BoomiDataHubClient()
    print("✅ Client initialized successfully")
    
    # Test connection first
    print("\n🔗 Testing connection...")
    test_result = client.test_connection()
    if test_result['success']:
        print("✅ Connection test successful")
    else:
        print(f"❌ Connection test failed: {test_result['error']}")
        sys.exit(1)
    
    # Get models to test model discovery (should work)
    print("\n📋 Testing model discovery...")
    models = client.get_all_models()
    published_models = models.get('published', [])
    if published_models:
        print(f"✅ Found {len(published_models)} published models")
        
        # Try to find the Advertisements model
        ads_model = None
        for model in published_models:
            if 'advertisement' in model.get('name', '').lower():
                ads_model = model
                break
        
        if ads_model:
            print(f"✅ Found Advertisements model: {ads_model['name']} (ID: {ads_model['id']})")
            
            # Test record query with fixed authentication
            print(f"\n🔍 Testing record query with fixed DataHub credentials...")
            model_id = ads_model['id']
            repository_id = "43212d46-1832-4ab1-820d-c0334d619f6f"
            
            # Simple query for Sony products
            filters = [
                {"fieldId": "BRAND", "operator": "EQUALS", "value": "Sony"}
            ]
            
            try:
                result = client.query_records_by_parameters(
                    universe_id=model_id,
                    repository_id=repository_id,
                    fields=["BRAND", "PRODUCT_NAME"],
                    filters=filters,
                    limit=10
                )
                
                if result.get('status') == 'success':
                    records = result.get('data', {}).get('records', [])
                    print(f"✅ Query successful! Found {len(records)} Sony products")
                    
                    if records:
                        print("\n📊 Sample records:")
                        for i, record in enumerate(records[:3], 1):
                            brand = record.get('BRAND', 'N/A')
                            product = record.get('PRODUCT_NAME', 'N/A')
                            print(f"  {i}. Brand: {brand}, Product: {product}")
                    else:
                        print("   No Sony products found in the data")
                        
                else:
                    print(f"❌ Query failed: {result.get('error')}")
                    print(f"   Status code: {result.get('status_code')}")
                    
            except Exception as e:
                print(f"❌ Query exception: {e}")
                
        else:
            print("⚠️  Advertisements model not found, cannot test record queries")
    else:
        print("❌ No published models found")
        
    print("\n" + "=" * 60)
    print("🏁 Test completed")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)