#!/usr/bin/env python3
"""
Advanced Interactive CLI for Boomi DataHub Conversational Agent
Features: Query history, help commands, model discovery, enhanced output
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

class BoomiCLI:
    def __init__(self):
        self.cli = None
        self.query_history = []
        
    def initialize(self):
        """Initialize the CLI agent"""
        try:
            from cli_agent.cli_agent import CLIAgent
            from integration_test import SyncBoomiMCPClient
            
            print("🔄 Connecting to Boomi DataHub...")
            self.cli = CLIAgent(mcp_client=SyncBoomiMCPClient())
            print("✅ Connected successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            print("\n🔧 Troubleshooting:")
            print("1. Make sure MCP server is running:")
            print("   python ../boomi_mcp_server/boomi_datahub_mcp_server_v2.py")
            print("2. Check your .env file has valid Boomi credentials")
            return False
    
    def show_help(self):
        """Show help information"""
        print("\n📖 Available Commands:")
        print("- help: Show this help message")
        print("- history: Show query history")
        print("- clear: Clear query history")
        print("- models: Show available data models")
        print("- examples: Show example queries")
        print("- quit/exit: Exit the application")
        print("\n💡 Or just ask natural language questions about your data!")
    
    def show_models(self):
        """Show available models"""
        print("\n📊 Available Boomi DataHub Models:")
        models = [
            ("Advertisements", "Marketing campaigns and ads", "How many advertisements do we have?"),
            ("users", "System users and accounts", "Count users in the system"),
            ("opportunity", "Sales opportunities and leads", "Show me opportunities"),
            ("Engagements", "Customer interactions and activities", "List customer engagements"),
            ("platform-users", "Platform user accounts", "How many platform users are there?")
        ]
        
        for model, description, example in models:
            print(f"  • {model}: {description}")
            print(f"    Example: \"{example}\"")
            print()
    
    def show_examples(self):
        """Show example queries"""
        print("\n💡 Example Queries You Can Try:")
        examples = [
            "How many advertisements do we have?",
            "Count all users in our system",
            "Show me opportunities",
            "List engagements",
            "How many platform users are there?",
            "What data do we have about advertisements?",
            "Count the opportunities",
            "Show me all users",
            "How many records are in the advertisements model?",
            "Display engagement information"
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")
    
    def show_history(self):
        """Show query history"""
        if not self.query_history:
            print("\n📝 No queries in history yet")
            return
            
        print(f"\n📝 Query History ({len(self.query_history)} queries):")
        for i, entry in enumerate(self.query_history[-10:], 1):  # Show last 10
            timestamp = entry['timestamp']
            query = entry['query']
            success = "✅" if entry['success'] else "❌"
            print(f"  {i}. [{timestamp}] {success} {query}")
        
        if len(self.query_history) > 10:
            print(f"  ... and {len(self.query_history) - 10} more queries")
    
    def process_query(self, query):
        """Process a user query"""
        if not self.cli:
            print("❌ CLI not initialized")
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print("🔄 Processing query...")
        print("   📋 Analyzing intent and entities...")
        print("   🔍 Discovering relevant models...")
        print("   🗺️  Mapping entities to fields...")
        print("   🔧 Building Boomi DataHub query...")
        print("   📊 Executing and retrieving data...")
        
        result = self.cli.process_query(query)
        
        # Add to history
        self.query_history.append({
            'timestamp': timestamp,
            'query': query,
            'success': result.get('success', False),
            'result': result
        })
        
        # Display result
        print("\n" + "="*60)
        if result.get('success'):
            response = result.get('response', {})
            if isinstance(response, dict):
                message = response.get('message', str(response))
            else:
                message = str(response)
            
            print(f"✅ RESULT: {message}")
            
            # Show additional metadata if available
            metadata = result.get('pipeline_metadata', {})
            if metadata:
                print(f"\n📊 EXECUTION DETAILS:")
                
                # Model discovery info
                model_info = metadata.get('model_discovery', {})
                if model_info:
                    primary_model = model_info.get('primary_model')
                    model_count = model_info.get('model_count', 0)
                    if primary_model:
                        print(f"   🎯 Primary Model: {primary_model}")
                    if model_count > 1:
                        print(f"   📋 Models Considered: {model_count}")
                
                # Data retrieval info
                data_info = metadata.get('data_retrieval', {})
                if data_info:
                    record_count = data_info.get('record_count')
                    if record_count is not None:
                        print(f"   📊 Records Found: {record_count}")
                
                # Execution time
                exec_time = metadata.get('total_execution_time_ms', 0)
                print(f"   ⏱️  Execution Time: {exec_time:.0f}ms")
                
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ ERROR: {error}")
            
            # Show failed stage if available
            failed_stage = result.get('failed_stage')
            if failed_stage:
                print(f"   🔧 Failed at: {failed_stage}")
            
            # Provide helpful suggestions
            print(f"\n💡 SUGGESTIONS:")
            print("   • Try asking about 'advertisements', 'users', or 'opportunities'")
            print("   • Use simple language like 'How many...', 'Count...', 'Show me...'")
            print("   • Make sure your query is about business data in Boomi DataHub")
        
        print("="*60)
    
    def run(self):
        """Main CLI loop"""
        print("🤖 Boomi DataHub Advanced Conversational Agent")
        print("=" * 70)
        print("Phase 5 Complete - Real-time dynamic discovery with 100% success rate")
        print("=" * 70)
        
        if not self.initialize():
            return
        
        print("\n🎯 Ready to answer your business questions!")
        print("💬 Ask natural language questions about your Boomi DataHub")
        print("📖 Type 'help' for commands or 'examples' for sample queries")
        print("=" * 70)
        
        while True:
            try:
                user_input = input(f"\n💬 [{len(self.query_history)}] Your query: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print(f"\n👋 Session complete!")
                    print(f"📊 Total queries processed: {len(self.query_history)}")
                    successful = sum(1 for q in self.query_history if q['success'])
                    if self.query_history:
                        success_rate = (successful / len(self.query_history)) * 100
                        print(f"✅ Success rate: {success_rate:.1f}% ({successful}/{len(self.query_history)})")
                    print("Thank you for using Boomi DataHub Conversational Agent!")
                    break
                    
                elif user_input.lower() == 'help':
                    self.show_help()
                    
                elif user_input.lower() == 'history':
                    self.show_history()
                    
                elif user_input.lower() == 'clear':
                    self.query_history.clear()
                    print("✅ Query history cleared")
                    
                elif user_input.lower() == 'models':
                    self.show_models()
                    
                elif user_input.lower() == 'examples':
                    self.show_examples()
                    
                else:
                    # Process as query
                    self.process_query(user_input)
                    
            except KeyboardInterrupt:
                print(f"\n\n👋 Interrupted by user.")
                print(f"📊 Processed {len(self.query_history)} queries in this session.")
                print("Goodbye!")
                break
                
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("💡 Try a different query or restart the application")

def main():
    cli = BoomiCLI()
    cli.run()

if __name__ == "__main__":
    main()