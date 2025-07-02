#!/usr/bin/env python3
"""
Test Claude integration for field mapping
"""

import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def test_claude_integration():
    print("🧪 Testing Claude Integration for Field Mapping")
    print("=" * 60)
    
    # Test Claude client
    try:
        from claude_client import ClaudeClient
        
        print("🔄 Initializing Claude client...")
        claude = ClaudeClient()
        
        if claude.is_available():
            print("✅ Claude client is available!")
            
            # Test field mapping
            print("\n🧪 Testing intelligent field mapping...")
            
            # Sample entities and fields for Sony query
            entities = [
                {"text": "Sony", "type": "BRAND", "confidence": 0.9},
                {"text": "products", "type": "OBJECT", "confidence": 0.8}
            ]
            
            model_fields = [
                {"name": "AD_ID", "type": "STRING", "description": "Advertisement ID"},
                {"name": "ADVERTISER", "type": "STRING", "description": "Company advertising"},
                {"name": "PRODUCT", "type": "STRING", "description": "Product being advertised"},
                {"name": "CAMPAIGN", "type": "STRING", "description": "Marketing campaign name"}
            ]
            
            query_context = "how many products is Sony advertising?"
            
            print(f"Query: '{query_context}'")
            print(f"Entities: {entities}")
            print(f"Available fields: {[f['name'] for f in model_fields]}")
            
            mapping = claude.map_entities_to_fields(entities, model_fields, query_context)
            
            print(f"\n✅ Claude mapping result:")
            for entity, field_info in mapping.items():
                print(f"   '{entity}' → {field_info}")
                
            # Check if Sony mapped to ADVERTISER (correct)
            if 'Sony' in mapping:
                sony_field = mapping['Sony'].get('field_name')
                if sony_field == 'ADVERTISER':
                    print("\n🎉 SUCCESS: Claude correctly mapped 'Sony' to ADVERTISER field!")
                else:
                    print(f"\n⚠️  Claude mapped 'Sony' to {sony_field}, expected ADVERTISER")
            else:
                print("\n⚠️  Claude didn't map 'Sony' entity")
        
        else:
            print("⚠️  Claude client not available (no API key)")
            print("To enable Claude:")
            print("1. Get API key from https://console.anthropic.com/")
            print("2. Add to .env file: ANTHROPIC_API_KEY=your_key_here")
            print("3. System will use pattern-based fallback for now")
            
    except Exception as e:
        print(f"❌ Error testing Claude: {e}")
    
    # Test CLI agent with field mapping
    print(f"\n{'='*60}")
    print("🧪 Testing CLI Agent Field Mapping")
    print("=" * 60)
    
    try:
        from cli_agent.cli_agent import CLIAgent
        from integration_test import SyncBoomiMCPClient
        
        print("🔄 Initializing CLI agent...")
        cli = CLIAgent(mcp_client=SyncBoomiMCPClient())
        
        # Test the Sony query
        print("\n🎯 Testing: 'how many products is Sony advertising?'")
        result = cli.process_query("how many products is Sony advertising?")
        
        if result.get('success'):
            response = result.get('response', {})
            message = response.get('message', str(response)) if isinstance(response, dict) else str(response)
            print(f"✅ Result: {message}")
            
            # Check if we got more than 0 products (we know there are 2 Sony products)
            if "0 products" in message:
                print("⚠️  Still getting 0 products - field mapping may need adjustment")
            else:
                print("🎉 SUCCESS: Found Sony products!")
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ Error: {error}")
            
    except Exception as e:
        print(f"❌ Error testing CLI agent: {e}")

if __name__ == "__main__":
    test_claude_integration()