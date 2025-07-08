#!/usr/bin/env python3
"""
Interactive CLI for Boomi DataHub Conversational Agent
Run your own natural language queries against Boomi DataHub
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def main():
    print("🤖 Boomi DataHub Conversational Agent")
    print("=" * 60)
    
    # Import and initialize
    try:
        from cli_agent.cli_agent import CLIAgent
        from integration_test import SyncBoomiMCPClient
        from claude_client import ClaudeClient
        
        print("🔄 Initializing connection to Boomi DataHub...")
        mcp_client = SyncBoomiMCPClient()
        claude_client = ClaudeClient()
        
        cli = CLIAgent(mcp_client=mcp_client, claude_client=claude_client)
        print("✅ Successfully connected to Boomi DataHub MCP Server")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the boomi_conversational_agent directory")
        return
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure MCP server is running:")
        print("   python ../boomi_mcp_server/boomi_datahub_mcp_server_v2.py")
        print("2. Check your .env file has valid Boomi credentials")
        return
    
    # Show available models
    print("\n📊 Your Boomi DataHub Models:")
    print("- Advertisements (marketing campaigns)")
    print("- users (system users)")
    print("- opportunity (sales opportunities)")  
    print("- Engagements (customer interactions)")
    print("- platform-users (platform users)")
    
    print("\n💡 Example queries you can try:")
    print("- How many advertisements do we have?")
    print("- Count the users in our system")
    print("- Show me opportunities")
    print("- List all engagements")
    print("- How many platform users are there?")
    
    print("\n🎯 The system uses dynamic discovery - it will:")
    print("- Find the right model for your query")
    print("- Discover the available fields")
    print("- Build and execute the query")
    print("- Return business-friendly results")
    
    print(f"\n{'='*60}")
    print("Type your questions below (or 'quit' to exit)")
    print(f"{'='*60}")
    
    query_count = 0
    
    while True:
        try:
            # Get user input
            query = input(f"\n💬 Query #{query_count + 1}: ").strip()
            
            # Check for exit
            if query.lower() in ['quit', 'exit', 'bye', 'q', 'stop']:
                print("\n👋 Thank you for using Boomi DataHub Conversational Agent!")
                break
                
            if not query:
                print("❓ Please enter a query or 'quit' to exit")
                continue
            
            query_count += 1
            
            # Process the query
            print("🔄 Processing your query...")
            print("   📋 Analyzing query intent...")
            print("   🔍 Discovering relevant models...")
            print("   🗺️  Mapping fields...")
            print("   🔧 Building query...")
            print("   📊 Retrieving data...")
            
            result = cli.process_query(query)
            
            # Display results
            print("\n" + "="*50)
            if result.get('success'):
                response = result.get('response', {})
                
                if isinstance(response, dict):
                    message = response.get('message', str(response))
                    
                    # Try to extract metadata if available
                    metadata = result.get('pipeline_metadata', {})
                    if metadata:
                        model_info = metadata.get('model_discovery', {})
                        if model_info:
                            primary_model = model_info.get('primary_model')
                            if primary_model:
                                print(f"📋 Model Used: {primary_model}")
                        
                        data_info = metadata.get('data_retrieval', {})
                        if data_info:
                            record_count = data_info.get('record_count')
                            if record_count is not None:
                                print(f"📊 Records Found: {record_count}")
                else:
                    message = str(response)
                
                print(f"✅ Result: {message}")
                
            else:
                error_msg = result.get('error', 'Unknown error occurred')
                print(f"❌ Error: {error_msg}")
                
                # Provide helpful suggestions
                print("\n💡 Suggestions:")
                print("- Try asking about 'advertisements', 'users', or 'opportunities'")
                print("- Use simple language like 'How many...', 'Count...', 'Show me...'")
                print("- Make sure your query is about business data")
            
            print("="*50)
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print("💡 Try a different query or restart the application")

if __name__ == "__main__":
    main()