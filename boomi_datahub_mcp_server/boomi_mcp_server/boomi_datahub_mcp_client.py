# boomi_datahub_mcp_client.py
"""
Boomi DataHub MCP Client

This client demonstrates how to interact with the Boomi DataHub MCP Server
to retrieve data model information through standardized MCP resources.

The client shows how AI agents and other systems can:
1. Discover available Boomi DataHub models
2. Access detailed model information
3. Search and filter models
4. Get model statistics and insights
5. Test connection health

This serves as both a testing tool and a reference implementation
for integrating with the Boomi DataHub MCP Server.
"""

import asyncio
import json
from fastmcp import Client
from datetime import datetime
from typing import Dict, List, Any

class BoomiDataHubMCPClient:
    """
    Client wrapper for interacting with Boomi DataHub MCP Server
    """
    
    def __init__(self, server_url: str = "http://127.0.0.1:8001/mcp"):
        """
        Initialize the MCP client
        
        Args:
            server_url: URL of the Boomi DataHub MCP Server
        """
        self.server_url = server_url
        self.client = Client(server_url)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to the MCP server and Boomi DataHub"""
        try:
            async with self.client as session:
                result = await session.read_resource("boomi://datahub/connection/test")
                return json.loads(result[0].text)
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to connect to MCP server: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_all_models(self) -> Dict[str, Any]:
        """Retrieve all Boomi DataHub models"""
        try:
            async with self.client as session:
                result = await session.read_resource("boomi://datahub/models/all")
                return json.loads(result[0].text)
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_published_models(self) -> Dict[str, Any]:
        """Retrieve published Boomi DataHub models"""
        try:
            async with self.client as session:
                result = await session.read_resource("boomi://datahub/models/published")
                return json.loads(result[0].text)
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_draft_models(self) -> Dict[str, Any]:
        """Retrieve draft Boomi DataHub models"""
        try:
            async with self.client as session:
                result = await session.read_resource("boomi://datahub/models/draft")
                return json.loads(result[0].text)
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_model_details(self, model_id: str) -> Dict[str, Any]:
        """Retrieve detailed information for a specific model"""
        try:
            async with self.client as session:
                result = await session.read_resource(f"boomi://datahub/model/{model_id}")
                return json.loads(result[0].text)
        except Exception as e:
            return {"status": "error", "error": str(e), "model_id": model_id}
    
    async def search_models_by_name(self, name_pattern: str) -> Dict[str, Any]:
        """Search for models by name pattern"""
        try:
            async with self.client as session:
                result = await session.call_tool("search_models_by_name", {"name_pattern": name_pattern})
                return json.loads(result[0].text)
        except Exception as e:
            return {"status": "error", "error": str(e), "search_pattern": name_pattern}
    
    async def get_model_statistics(self) -> Dict[str, Any]:
        """Get comprehensive model statistics"""
        try:
            async with self.client as session:
                result = await session.call_tool("get_model_statistics", {})
                return json.loads(result[0].text)
        except Exception as e:
            return {"status": "error", "error": str(e)}

def print_json_summary(data: Dict[str, Any], title: str):
    """Print a formatted summary of JSON data"""
    print(f"\n{'='*20} {title} {'='*20}")
    
    if data.get("status") == "error":
        print(f"❌ Error: {data.get('error', 'Unknown error')}")
        return
    
    if "summary" in data:
        print("📊 Summary:")
        for key, value in data["summary"].items():
            print(f"   {key}: {value}")
    
    if "connection_result" in data:
        conn = data["connection_result"]
        status = "✅ Connected" if conn.get("success") else "❌ Failed"
        print(f"🔌 Connection: {status}")
        if not conn.get("success"):
            print(f"   Error: {conn.get('error', 'Unknown')}")
            print(f"   Status Code: {conn.get('status_code', 'N/A')}")
    
    if "statistics" in data:
        stats = data["statistics"]
        print("📈 Statistics:")
        overview = stats.get("overview", {})
        for key, value in overview.items():
            print(f"   {key}: {value}")
    
    print(f"⏰ Timestamp: {data.get('timestamp', 'N/A')}")

def print_model_list(models: List[Dict[str, Any]], title: str, limit: int = 5):
    """Print a formatted list of models"""
    print(f"\n{'='*10} {title} ({'showing first ' + str(limit) if len(models) > limit else 'all'} of {len(models)}) {'='*10}")
    
    for i, model in enumerate(models[:limit], 1):
        print(f"{i}. {model.get('name', 'N/A')}")
        print(f"   ID: {model.get('id', 'N/A')}")
        print(f"   Status: {model.get('publicationStatus', 'N/A')}")
        print(f"   Version: {model.get('latestVersion', model.get('version', 'N/A'))}")
        if 'fieldCount' in model:
            print(f"   Fields: {model['fieldCount']}")
        if 'sourceCount' in model:
            print(f"   Sources: {model['sourceCount']}")
        print()

async def main():
    """Main demonstration of the Boomi DataHub MCP Client"""
    
    print("🚀 Boomi DataHub MCP Client Demo")
    print("=" * 60)
    print("This client demonstrates interaction with Boomi DataHub through MCP resources")
    print("Make sure the Boomi DataHub MCP Server is running on localhost:8001!")
    print("=" * 60)
    
    # Initialize client
    client = BoomiDataHubMCPClient()
    
    # Test connection first
    print("\n🔍 Step 1: Testing connection to MCP server and Boomi DataHub...")
    connection_result = await client.test_connection()
    print_json_summary(connection_result, "Connection Test")
    
    if connection_result.get("status") == "error":
        print("\n❌ Cannot proceed without a valid connection.")
        print("Please ensure:")
        print("1. The Boomi DataHub MCP Server is running")
        print("2. Your Boomi credentials are properly configured")
        print("3. Network connectivity is available")
        return
    
    # Get all models
    print("\n🔍 Step 2: Retrieving all DataHub models...")
    all_models_result = await client.get_all_models()
    print_json_summary(all_models_result, "All Models")
    
    if all_models_result.get("status") == "success":
        data = all_models_result.get("data", {})
        published_models = data.get("published", [])
        draft_models = data.get("draft", [])
        
        # Show sample models
        if published_models:
            print_model_list(published_models, "Published Models", limit=3)
        
        if draft_models:
            print_model_list(draft_models, "Draft Models", limit=3)
        
        # Test model details for the first published model
        if published_models:
            first_model = published_models[0]
            model_id = first_model.get("id")
            
            if model_id:
                print(f"\n🔍 Step 3: Getting detailed information for model '{first_model.get('name', 'Unknown')}'...")
                model_details = await client.get_model_details(model_id)
                
                if model_details.get("status") == "success":
                    model_data = model_details.get("data", {})
                    print(f"\n📋 Model Details:")
                    print(f"   Name: {model_data.get('name', 'N/A')}")
                    print(f"   ID: {model_data.get('id', 'N/A')}")
                    print(f"   Version: {model_data.get('version', model_data.get('latestVersion', 'N/A'))}")
                    
                    if 'fields' in model_data:
                        fields = model_data['fields']
                        print(f"   Fields ({len(fields)}):")
                        for field in fields[:5]:  # Show first 5 fields
                            print(f"     - {field.get('name', 'N/A')} ({field.get('type', 'N/A')})")
                        if len(fields) > 5:
                            print(f"     ... and {len(fields) - 5} more")
                    
                    if 'sources' in model_data:
                        sources = model_data['sources']
                        print(f"   Sources ({len(sources)}):")
                        for source in sources:
                            print(f"     - {source.get('id', 'N/A')} ({source.get('type', 'N/A')})")
                else:
                    print(f"❌ Failed to get model details: {model_details.get('error', 'Unknown error')}")
    
    # Test search functionality
    print("\n🔍 Step 4: Testing model search functionality...")
    search_result = await client.search_models_by_name("customer")
    
    if search_result.get("status") == "success":
        matches = search_result.get("matches", [])
        print(f"🔍 Search Results for 'customer': {len(matches)} matches found")
        if matches:
            print_model_list(matches, "Search Results", limit=3)
    else:
        print(f"❌ Search failed: {search_result.get('error', 'Unknown error')}")
    
    # Get model statistics
    print("\n🔍 Step 5: Getting model statistics...")
    stats_result = await client.get_model_statistics()
    print_json_summary(stats_result, "Model Statistics")
    
    if stats_result.get("status") == "success":
        stats = stats_result.get("statistics", {})
        
        # Show field analysis
        field_analysis = stats.get("field_analysis", {})
        if field_analysis:
            print(f"\n📊 Field Analysis:")
            print(f"   Models with fields: {field_analysis.get('models_with_fields', 0)}")
            print(f"   Total fields: {field_analysis.get('total_fields', 0)}")
            print(f"   Average fields per model: {field_analysis.get('avg_fields_per_model', 0)}")
            print(f"   Max fields in a model: {field_analysis.get('max_fields', 0)}")
        
        # Show source analysis
        source_analysis = stats.get("source_analysis", {})
        if source_analysis:
            print(f"\n📊 Source Analysis:")
            print(f"   Models with sources: {source_analysis.get('models_with_sources', 0)}")
            print(f"   Total sources: {source_analysis.get('total_sources', 0)}")
            print(f"   Average sources per model: {source_analysis.get('avg_sources_per_model', 0)}")
        
        # Show version analysis
        version_analysis = stats.get("version_analysis", {})
        if version_analysis:
            print(f"\n📊 Version Analysis:")
            print(f"   Models with versions: {version_analysis.get('models_with_versions', 0)}")
            unique_versions = version_analysis.get('unique_versions', [])
            print(f"   Unique versions: {len(unique_versions)}")
            if unique_versions:
                print(f"   Versions: {', '.join(unique_versions[:10])}")
                if len(unique_versions) > 10:
                    print(f"   ... and {len(unique_versions) - 10} more")
    
    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("=" * 60)
    print("\nWhat this demo showed:")
    print("🔹 Connection testing and health checks")
    print("🔹 Retrieving all models (published and draft)")
    print("🔹 Getting detailed model information with fields and sources")
    print("🔹 Searching models by name patterns")
    print("🔹 Comprehensive model statistics and analysis")
    print("\nAI agents can use these MCP resources to:")
    print("🤖 Discover and catalog data models")
    print("🤖 Analyze data structures for integration planning")
    print("🤖 Generate documentation and compliance reports")
    print("🤖 Support data governance and quality initiatives")
    print("🤖 Enable intelligent data mapping and transformation")

async def demo_specific_use_cases():
    """Demonstrate specific AI agent use cases"""
    print("\n" + "=" * 60)
    print("🤖 AI Agent Use Case Demonstrations")
    print("=" * 60)
    
    client = BoomiDataHubMCPClient()
    
    # Use Case 1: Data Governance Report
    print("\n📋 Use Case 1: Data Governance Report Generation")
    print("-" * 50)
    
    stats_result = await client.get_model_statistics()
    all_models_result = await client.get_all_models()
    
    if stats_result.get("status") == "success" and all_models_result.get("status") == "success":
        stats = stats_result["statistics"]
        models_data = all_models_result["data"]
        
        print("🔍 Governance Insights:")
        overview = stats["overview"]
        
        governance_score = (overview["published_models"] / overview["total_models"] * 100) if overview["total_models"] > 0 else 0
        print(f"   📊 Model Maturity Score: {governance_score:.1f}% (published models)")
        
        if governance_score < 70:
            print("   ⚠️  Recommendation: Consider publishing more draft models for better governance")
        else:
            print("   ✅ Good model governance - high percentage of published models")
        
        field_coverage = (stats["field_analysis"]["models_with_fields"] / overview["total_models"] * 100) if overview["total_models"] > 0 else 0
        print(f"   📊 Schema Coverage: {field_coverage:.1f}% (models with defined fields)")
        
        if field_coverage < 80:
            print("   ⚠️  Recommendation: Ensure all models have complete field definitions")
    
    # Use Case 2: Integration Planning
    print("\n🔗 Use Case 2: Integration Planning Support")
    print("-" * 50)
    
    # Search for common business entities
    business_entities = ["customer", "product", "order", "invoice", "contact"]
    
    for entity in business_entities:
        search_result = await client.search_models_by_name(entity)
        if search_result.get("status") == "success":
            matches = search_result.get("matches", [])
            if matches:
                print(f"   🔍 Found {len(matches)} models for '{entity}' entity:")
                for match in matches[:2]:  # Show first 2 matches
                    status = "📗" if match.get("published") else "📙"
                    print(f"     {status} {match.get('name', 'N/A')} (ID: {match.get('id', 'N/A')})")
    
    print("\n💡 Integration Recommendations:")
    print("   🔹 Use published models for production integrations")
    print("   🔹 Review draft models for future integration opportunities")
    print("   🔹 Standardize naming conventions across similar business entities")

async def run_interactive_demo():
    """Run an interactive demo allowing user to explore specific models"""
    print("\n" + "=" * 60)
    print("🔧 Interactive Model Explorer")
    print("=" * 60)
    print("Enter model names or patterns to explore (type 'quit' to exit)")
    
    client = BoomiDataHubMCPClient()
    
    while True:
        try:
            user_input = input("\n🔍 Search for models (name pattern): ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print(f"Searching for models matching '{user_input}'...")
            search_result = await client.search_models_by_name(user_input)
            
            if search_result.get("status") == "success":
                matches = search_result.get("matches", [])
                
                if not matches:
                    print(f"❌ No models found matching '{user_input}'")
                    continue
                
                print(f"✅ Found {len(matches)} matching models:")
                
                for i, model in enumerate(matches, 1):
                    status_icon = "📗" if model.get("published") else "📙"
                    print(f"{i}. {status_icon} {model.get('name', 'N/A')}")
                
                if matches:
                    try:
                        choice = input(f"\nEnter number (1-{len(matches)}) to see details, or press Enter to search again: ").strip()
                        
                        if choice and choice.isdigit():
                            idx = int(choice) - 1
                            if 0 <= idx < len(matches):
                                selected_model = matches[idx]
                                model_id = selected_model.get("id")
                                
                                if model_id:
                                    print(f"\n📋 Getting details for '{selected_model.get('name', 'Unknown')}'...")
                                    details_result = await client.get_model_details(model_id)
                                    
                                    if details_result.get("status") == "success":
                                        model_data = details_result["data"]
                                        
                                        print(f"\n📊 Model: {model_data.get('name', 'N/A')}")
                                        print(f"   ID: {model_data.get('id', 'N/A')}")
                                        print(f"   Status: {model_data.get('publicationStatus', 'N/A')}")
                                        print(f"   Version: {model_data.get('version', model_data.get('latestVersion', 'N/A'))}")
                                        
                                        if 'fields' in model_data and model_data['fields']:
                                            fields = model_data['fields']
                                            print(f"\n   📝 Fields ({len(fields)}):")
                                            for field in fields:
                                                required = "🔴" if field.get('required') else "⚪"
                                                repeatable = "🔄" if field.get('repeatable') else ""
                                                print(f"     {required} {field.get('name', 'N/A')} ({field.get('type', 'N/A')}) {repeatable}")
                                        
                                        if 'sources' in model_data and model_data['sources']:
                                            sources = model_data['sources']
                                            print(f"\n   🔗 Sources ({len(sources)}):")
                                            for source in sources:
                                                default = "⭐" if source.get('default') else ""
                                                print(f"     {default} {source.get('id', 'N/A')} ({source.get('type', 'N/A')})")
                                        
                                        if 'matchRules' in model_data and model_data['matchRules']:
                                            print(f"\n   🎯 Match Rules: {len(model_data['matchRules'])} defined")
                                    else:
                                        print(f"❌ Failed to get model details: {details_result.get('error', 'Unknown error')}")
                            else:
                                print("❌ Invalid selection")
                    except (ValueError, KeyboardInterrupt):
                        continue
            else:
                print(f"❌ Search failed: {search_result.get('error', 'Unknown error')}")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    print("🚀 Boomi DataHub MCP Client")
    print("Choose a demo mode:")
    print("1. Full Demo (recommended)")
    print("2. Use Case Demonstrations")
    print("3. Interactive Model Explorer")
    print("4. All of the above")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            asyncio.run(main())
        elif choice == "2":
            asyncio.run(demo_specific_use_cases())
        elif choice == "3":
            asyncio.run(run_interactive_demo())
        elif choice == "4":
            print("\n🚀 Running complete demonstration suite...")
            asyncio.run(main())
            asyncio.run(demo_specific_use_cases())
            asyncio.run(run_interactive_demo())
        else:
            print("Invalid choice, running full demo...")
            asyncio.run(main())
    
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()