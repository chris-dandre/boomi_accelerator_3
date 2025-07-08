#!/usr/bin/env python3
"""
Debug script to isolate the field discovery issue for the Advertisements model
"""
import os
import sys
import json
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Set up environment
from dotenv import load_dotenv
load_dotenv()

# Import the field mapper and MCP client
from cli_agent.agents.field_mapper import FieldMapper
from integration_test import SyncBoomiMCPClient

def debug_field_discovery():
    """Debug the field discovery for Advertisements model"""
    
    print("🐛 Debug Field Discovery for Advertisements Model")
    print("=" * 60)
    
    advertisements_model_id = '02367877-e560-4d82-b640-6a9f7ab96afa'
    
    # Step 1: Test MCP client connection
    print("\n1. Testing MCP client connection...")
    try:
        mcp_client = SyncBoomiMCPClient()
        connection_result = mcp_client.test_connection()
        print(f"   Connection status: {connection_result.get('status', 'unknown')}")
        
        if connection_result.get('status') == 'error':
            print(f"   Error: {connection_result.get('error', 'Unknown error')}")
            return
        else:
            print("   ✅ Connection successful")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # Step 2: Test direct MCP client get_model_fields call
    print(f"\n2. Testing direct MCP client get_model_fields call...")
    try:
        fields_result = mcp_client.get_model_fields(advertisements_model_id)
        print(f"   Raw response type: {type(fields_result)}")
        print(f"   Raw response keys: {list(fields_result.keys()) if isinstance(fields_result, dict) else 'Not a dict'}")
        
        if isinstance(fields_result, dict):
            print(f"   Status: {fields_result.get('status', 'unknown')}")
            
            if fields_result.get('status') == 'error':
                print(f"   Error: {fields_result.get('error', 'Unknown error')}")
                return
            
            # Check if fields key exists and has content
            if 'fields' in fields_result:
                fields_list = fields_result['fields']
                print(f"   Fields list type: {type(fields_list)}")
                print(f"   Fields count: {len(fields_list) if isinstance(fields_list, list) else 'Not a list'}")
                
                if isinstance(fields_list, list) and len(fields_list) > 0:
                    print(f"   Sample field: {fields_list[0] if fields_list else 'No fields'}")
                else:
                    print("   ❌ Fields list is empty or not a list")
            else:
                print("   ❌ No 'fields' key in response")
                print(f"   Available keys: {list(fields_result.keys())}")
        else:
            print("   ❌ Response is not a dictionary")
            print(f"   Raw response: {fields_result}")
            
    except Exception as e:
        print(f"   ❌ Direct MCP call failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Test FieldMapper get_model_fields method
    print(f"\n3. Testing FieldMapper get_model_fields method...")
    try:
        field_mapper = FieldMapper(mcp_client=mcp_client)
        
        # Test FieldMapper's get_model_fields method
        mapper_fields_result = field_mapper.get_model_fields(advertisements_model_id)
        print(f"   FieldMapper response type: {type(mapper_fields_result)}")
        print(f"   FieldMapper response: {mapper_fields_result}")
        
        if isinstance(mapper_fields_result, dict):
            print(f"   Status: {mapper_fields_result.get('status', 'unknown')}")
            
            if mapper_fields_result.get('status') == 'error':
                print(f"   Error: {mapper_fields_result.get('error', 'Unknown error')}")
                return
            
            # Check if fields key exists and has content
            if 'fields' in mapper_fields_result:
                fields_list = mapper_fields_result['fields']
                print(f"   Fields list type: {type(fields_list)}")
                print(f"   Fields count: {len(fields_list) if isinstance(fields_list, list) else 'Not a list'}")
                
                if isinstance(fields_list, list) and len(fields_list) > 0:
                    print(f"   Sample field: {fields_list[0] if fields_list else 'No fields'}")
                    print("   ✅ FieldMapper successfully retrieved fields")
                else:
                    print("   ❌ FieldMapper fields list is empty or not a list")
            else:
                print("   ❌ No 'fields' key in FieldMapper response")
                print(f"   Available keys: {list(mapper_fields_result.keys())}")
        else:
            print("   ❌ FieldMapper response is not a dictionary")
            
    except Exception as e:
        print(f"   ❌ FieldMapper call failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Test field mapping with sample entities
    print(f"\n4. Testing field mapping with sample entities...")
    try:
        # Create sample entities for testing
        sample_entities = [
            {'text': 'advertisements', 'type': 'OBJECT'},
            {'text': 'advertiser', 'type': 'BRAND'},
            {'text': 'campaign', 'type': 'OBJECT'}
        ]
        
        # Create sample model structure
        sample_model = {
            'model_id': advertisements_model_id,
            'name': 'Advertisements'
        }
        
        # Test create_field_mapping_for_models
        field_mapping = field_mapper.create_field_mapping_for_models(
            sample_entities, 
            [sample_model], 
            "List all advertisements"
        )
        
        print(f"   Field mapping result type: {type(field_mapping)}")
        print(f"   Field mapping keys: {list(field_mapping.keys()) if isinstance(field_mapping, dict) else 'Not a dict'}")
        
        if isinstance(field_mapping, dict):
            model_mapping = field_mapping.get(advertisements_model_id, {})
            print(f"   Model mapping: {model_mapping}")
            
            if model_mapping:
                print("   ✅ Field mapping completed successfully")
                print(f"   Mapped {len(model_mapping)} entities")
                for entity, mapping in model_mapping.items():
                    print(f"      {entity} -> {mapping}")
            else:
                print("   ❌ Model mapping is empty")
        else:
            print("   ❌ Field mapping result is not a dictionary")
            
    except Exception as e:
        print(f"   ❌ Field mapping failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n🎯 Debug Summary")
    print("=" * 60)
    print("Check the results above to identify where the field discovery is failing.")

if __name__ == "__main__":
    debug_field_discovery()