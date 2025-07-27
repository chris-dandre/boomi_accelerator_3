#!/usr/bin/env python3
"""
Test Data-Driven Field Mapping with Authentication
Test the agentic approach with proper OAuth token
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
from claude_client import ClaudeClient
from cli_agent.agents.field_mapper import FieldMapper

def test_data_driven_with_auth():
    """Test data-driven field mapping with proper authentication"""
    print("🧪 Testing Data-Driven Field Mapping with Authentication")
    print("=" * 60)
    
    # Create orchestrator
    orchestrator = create_orchestrator(interface_type="cli")
    mcp_client = orchestrator.workflow_nodes.mcp_client
    claude_client = ClaudeClient()
    
    print(f"MCP client type: {type(mcp_client)}")
    print(f"Has sample_field_data: {hasattr(mcp_client, 'sample_field_data')}")
    print(f"Claude available: {claude_client.is_available()}")
    print()
    
    # Get OAuth token for executive user (has full data access)
    print("🔐 Getting OAuth token for executive user...")
    auth_result = oauth_client.authenticate("sarah.chen", "executive.access.2024")
    
    if not auth_result["success"]:
        print(f"❌ Authentication failed: {auth_result['error']}")
        return
        
    bearer_token = auth_result["access_token"]
    print(f"✅ Got bearer token: {bearer_token[:50]}...")
    
    # Set bearer token on MCP client
    mcp_client.set_bearer_token(bearer_token)
    print("✅ Bearer token set on MCP client")
    print()
    
    # Test entities (Sony query)
    entities = [
        {"text": "Sony", "type": "BRAND", "confidence": 0.9}
    ]
    
    # Get Advertisements model ID
    advertisements_model_id = "02367877-e560-4d82-b640-6a9f7ab96afa"
    
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
    
    print(f"🔍 Testing with authenticated data sampling:")
    print(f"   Model ID: {advertisements_model_id}")
    print(f"   Entities: {[e['text'] for e in entities]}")
    print(f"   Fields: {[f['name'] for f in model_fields]}")
    print(f"   Context: '{query_context}'")
    print()
    
    # Test FieldMapper with authenticated MCP client
    field_mapper = FieldMapper(mcp_client=mcp_client, claude_client=claude_client)
    
    print("🔍 Testing authenticated data-driven field discovery...")
    try:
        # Test the full mapping method (should use data-driven first with auth)
        full_mapping = field_mapper.map_entities_to_fields(
            entities, model_fields, query_context, advertisements_model_id
        )
        print(f"\n📋 Final mapping result: {full_mapping}")
        
        if full_mapping:
            print(f"\n🎯 Field Mapping Results:")
            for entity, info in full_mapping.items():
                field_name = info.get('field_name', 'Unknown')
                confidence = info.get('confidence', 0)
                reasoning = info.get('reasoning', 'No reasoning')
                evidence = info.get('evidence', [])
                match_type = info.get('match_type', 'unknown')
                sample_size = info.get('sample_size', 0)
                
                print(f"   📌 '{entity}' → {field_name}")
                print(f"      🎯 Confidence: {confidence:.2f}")
                print(f"      💭 Reasoning: {reasoning}")
                if evidence:
                    print(f"      📊 Evidence ({match_type} matches): {evidence}")
                if sample_size > 0:
                    print(f"      📈 Sample size: {sample_size}")
                    
                # Validate the result
                if field_name == 'ADVERTISER' and evidence:
                    print(f"      ✅ SUCCESS: Found Sony in ADVERTISER field with data evidence!")
                elif field_name == 'PRODUCT':
                    print(f"      ⚠️  Claude mapped to PRODUCT field (semantic guess)")
                else:
                    print(f"      ❓ Mapped to {field_name} field")
        else:
            print("❌ No mappings found")
            
    except Exception as e:
        print(f"❌ Authenticated mapping failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_driven_with_auth()