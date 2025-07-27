#!/usr/bin/env python3
"""
Test Data-Driven Field Mapping
Test the new agentic approach that samples actual data to discover field mappings
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
from claude_client import ClaudeClient
from cli_agent.agents.field_mapper import FieldMapper

def test_data_driven_mapping():
    """Test data-driven field mapping for Sony query"""
    print("🧪 Testing Data-Driven Field Mapping")
    print("=" * 50)
    
    # Create orchestrator to get MCP client
    orchestrator = create_orchestrator(interface_type="cli")
    mcp_client = orchestrator.workflow_nodes.mcp_client
    claude_client = ClaudeClient()
    
    print(f"MCP client type: {type(mcp_client)}")
    print(f"Has sample_field_data: {hasattr(mcp_client, 'sample_field_data')}")
    print(f"Claude available: {claude_client.is_available()}")
    print()
    
    # Test entities (Sony query)
    entities = [
        {"text": "Sony", "type": "BRAND", "confidence": 0.9}
    ]
    
    # Get Advertisements model ID (we know this from previous testing)
    advertisements_model_id = "02367877-e560-4d82-b640-6a9f7ab96afa"
    
    # Advertisements model fields (we know these)
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
    print(f"   Model ID: {advertisements_model_id}")
    print(f"   Entities: {entities}")
    print(f"   Fields: {[f['name'] for f in model_fields]}")
    print(f"   Context: '{query_context}'")
    print()
    
    # Test FieldMapper with data-driven discovery
    field_mapper = FieldMapper(mcp_client=mcp_client, claude_client=claude_client)
    
    print("🔍 Testing data-driven field discovery...")
    try:
        # Test the data-driven discovery method directly first
        data_mapping = field_mapper.discover_fields_from_data(
            entities, advertisements_model_id, model_fields
        )
        print(f"📊 Direct data-driven result: {data_mapping}")
        print()
        
        # Test the full mapping method (should use data-driven first)
        full_mapping = field_mapper.map_entities_to_fields(
            entities, model_fields, query_context, advertisements_model_id
        )
        print(f"📋 Full mapping result: {full_mapping}")
        
        if full_mapping:
            for entity, info in full_mapping.items():
                field_name = info.get('field_name', 'Unknown')
                confidence = info.get('confidence', 0)
                reasoning = info.get('reasoning', 'No reasoning')
                evidence = info.get('evidence', [])
                print(f"   🎯 '{entity}' → {field_name} (confidence: {confidence:.2f})")
                print(f"      💭 {reasoning}")
                if evidence:
                    print(f"      📋 Evidence: {evidence}")
        else:
            print("❌ No mappings found")
            
    except Exception as e:
        print(f"❌ Data-driven mapping failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_driven_mapping()