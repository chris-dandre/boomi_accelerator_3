#!/usr/bin/env python3
"""
Debug Claude Field Mapping
Test why Claude field mapping is failing and falling back to patterns
"""

import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.append('.')

from claude_client import ClaudeClient
from cli_agent.agents.field_mapper import FieldMapper

def test_claude_mapping():
    """Test Claude field mapping directly"""
    print("🧪 Testing Claude Field Mapping")
    print("=" * 50)
    
    # Initialize Claude client
    claude_client = ClaudeClient()
    print(f"Claude available: {claude_client.is_available()}")
    
    if not claude_client.is_available():
        print("❌ Claude client not available - check ANTHROPIC_API_KEY")
        return
    
    # Test entities (Sony query)
    entities = [
        {"text": "Sony", "type": "BRAND", "confidence": 0.9}
    ]
    
    # Advertisements model fields
    model_fields = [
        {"name": "AD_ID", "type": "string"},
        {"name": "ADVERTISER", "type": "string"}, 
        {"name": "PRODUCT", "type": "string"},
        {"name": "CAMPAIGN", "type": "string"},
        {"name": "CATEGORY", "type": "string"},
        {"name": "COMPETITORS", "type": "string"},
        {"name": "PLACEMEN_PRIORITY", "type": "string"},
        {"name": "PROSPECT_INTERESTS", "type": "string"},
        {"name": "TARGET_MARKET_BRIEF", "type": "string"},
        {"name": "VIDEO_LINK", "type": "string"}
    ]
    
    query_context = "show me Sony products"
    
    print(f"🔍 Testing with:")
    print(f"   Entities: {entities}")
    print(f"   Fields: {[f['name'] for f in model_fields]}")
    print(f"   Context: '{query_context}'")
    print()
    
    # Test Claude mapping directly
    try:
        print("🧠 Calling Claude map_entities_to_fields...")
        result = claude_client.map_entities_to_fields(entities, model_fields, query_context)
        print(f"✅ Claude result: {result}")
        print(f"   Type: {type(result)}")
        
        if isinstance(result, dict) and result:
            for entity, mapping in result.items():
                print(f"   🎯 '{entity}' → {mapping}")
        else:
            print("❌ Empty or invalid result from Claude")
            
    except Exception as e:
        print(f"❌ Claude mapping failed: {e}")
        print(f"   Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    print("🔧 Testing FieldMapper with Claude...")
    
    # Test with FieldMapper
    field_mapper = FieldMapper(claude_client=claude_client)
    
    try:
        mapping = field_mapper.map_entities_to_fields(entities, model_fields, query_context)
        print(f"✅ FieldMapper result: {mapping}")
        
        if isinstance(mapping, dict) and mapping:
            for entity, info in mapping.items():
                field_name = info.get('field_name', 'Unknown')
                confidence = info.get('confidence', 0)
                reasoning = info.get('reasoning', 'No reasoning')
                print(f"   🎯 '{entity}' → {field_name} (confidence: {confidence:.2f})")
                print(f"      💭 {reasoning}")
        else:
            print("❌ Empty or invalid result from FieldMapper")
            
    except Exception as e:
        print(f"❌ FieldMapper failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_claude_mapping()