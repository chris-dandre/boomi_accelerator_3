#!/usr/bin/env python3
"""
Simple test script for the Boomi DataHub REST API Client
Tests basic functionality: get all models and show their details
"""

from boomi_datahub_client import BoomiDataHubClient
import json

def test_get_all_models_and_details():
    """
    Test getting all models and displaying their details
    """
    try:
        print("🚀 Boomi DataHub Client - Simple Test")
        print("=" * 50)
        
        # Initialize client
        print("1. Initializing client...")
        client = BoomiDataHubClient()
        
        # Test connection
        print("2. Testing connection...")
        test_result = client.test_connection()
        if not test_result['success']:
            print(f"❌ Connection failed: {test_result['error']}")
            return False
        print("✅ Connection successful")
        
        # Get all models
        print("\n3. Retrieving all models...")
        all_models = client.get_models()  # Gets all models in a single list
        
        print(f"✅ Found {len(all_models)} total models")
        
        # Iterate through models and show details
        print("\n4. Model Details:")
        print("=" * 80)
        
        for i, model in enumerate(all_models, 1):
            # Extract basic model information
            name = model.get('name', 'N/A')
            model_id = model.get('id', 'N/A')
            publication_status = model.get('publicationStatus', 'N/A')
            is_published = model.get('published', False)
            latest_version = model.get('latestVersion', 'N/A')
            
            # Display model details
            print(f"\nModel {i}:")
            print(f"  Name: {name}")
            print(f"  ID: {model_id}")
            print(f"  Publication Status: {publication_status} ({'Published' if is_published else 'Draft'})")
            print(f"  Latest Version: {latest_version}")
            
            # Show all available fields from the basic model response
            print(f"  Basic Model Fields:")
            for field_name, field_value in model.items():
                if field_name not in ['name', 'id', 'publicationStatus', 'published', 'latestVersion']:
                    print(f"    {field_name}: {field_value}")
            
            # Try to get detailed model schema/fields
            print(f"  Model Fields:")
            if model_id != 'N/A':
                try:
                    # Get detailed model info with fields
                    detailed_model = client.get_model_by_id(model_id)
                    if detailed_model:
                        # Check if we got fields
                        fields = detailed_model.get('fields', [])
                        if fields:
                            print(f"    Found {len(fields)} fields:")
                            for field in fields:
                                field_name = field.get('name', 'N/A')
                                field_type = field.get('type', 'N/A')
                                field_required = field.get('required', False)
                                field_repeatable = field.get('repeatable', False)
                                field_unique_id = field.get('uniqueId', 'N/A')
                                
                                required_str = " (Required)" if field_required else ""
                                repeatable_str = " (Repeatable)" if field_repeatable else ""
                                
                                print(f"      - {field_name}: {field_type}{required_str}{repeatable_str}")
                                print(f"        Unique ID: {field_unique_id}")
                        else:
                            print(f"    No fields found in detailed model response")
                        
                        # Show other detailed model information
                        sources = detailed_model.get('sources', [])
                        if sources:
                            print(f"    Data Sources ({len(sources)}):")
                            for source in sources:
                                source_id = source.get('id', 'N/A')
                                source_type = source.get('type', 'N/A')
                                print(f"      - {source_id} ({source_type})")
                        
                        match_rules = detailed_model.get('matchRules', [])
                        if match_rules:
                            print(f"    Match Rules:")
                            for rule in match_rules:
                                operator = rule.get('topLevelOperator', 'N/A')
                                expressions = rule.get('expressions', [])
                                print(f"      - Operator: {operator}")
                                for expr in expressions:
                                    field_id = expr.get('fieldUniqueId', 'N/A')
                                    print(f"        Field: {field_id}")
                        
                        record_title_fields = detailed_model.get('recordTitleFields', [])
                        if record_title_fields:
                            print(f"    Record Title Fields: {', '.join(record_title_fields)}")
                    else:
                        print(f"    Could not retrieve detailed model information")
                        
                except Exception as e:
                    print(f"    Error retrieving detailed model: {e}")
            else:
                print(f"    Cannot retrieve fields - no model ID")
            
            print("-" * 80)
        
        # Summary
        published_count = sum(1 for model in all_models if model.get('published', False))
        draft_count = len(all_models) - published_count
        
        print(f"\n📊 Summary:")
        print(f"  Total Models: {len(all_models)}")
        print(f"  Published: {published_count}")
        print(f"  Draft: {draft_count}")
        
        # Optional: Get individual model details for the first model
        if all_models:
            print(f"\n5. Testing individual model details for first model...")
            first_model_id = all_models[0].get('id')
            if first_model_id:
                individual_model = client.get_model_by_id(first_model_id)
                if individual_model:
                    print(f"✅ Successfully retrieved individual model details")
                    print(f"   Model: {individual_model.get('name')}")
                else:
                    print(f"⚠️  Could not retrieve individual model details")
        
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """
    Main test function
    """
    success = test_get_all_models_and_details()
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Test failed. Please check your .env configuration:")
        print("   BOOMI_USERNAME=your_username")
        print("   BOOMI_PASSWORD=your_password")
        print("   BOOMI_ACCOUNT_ID=your_account_id")
        print("   BOOMI_BASE_URL=https://api.boomi.com")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)