# boomi_datahub_mcp_client_v2.py
"""
Enhanced Boomi DataHub MCP Client with Field Mapping and Better Display

This enhanced client demonstrates the new capabilities:
- Automatic field name conversion
- Dual credential support
- Enhanced error handling
- Better result display
"""

import asyncio
import json
from fastmcp import Client
from datetime import datetime
from typing import Dict, List, Any, Optional

class EnhancedBoomiDataHubMCPClient:
    """Enhanced client wrapper for interacting with Boomi DataHub MCP Server"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:8001/mcp"):
        self.server_url = server_url
        self.client = Client(server_url)
    
    # Existing methods (keeping original functionality)
    
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
    
    # Enhanced Parameterised Query Methods
    
    async def get_model_fields(self, model_id: str) -> Dict[str, Any]:
        """Get detailed field information for a model with mapping"""
        try:
            async with self.client as session:
                result = await session.call_tool("get_model_fields", {"model_id": model_id})
                return json.loads(result[0].text)
        except Exception as e:
            return {"status": "error", "error": str(e), "model_id": model_id}
    
    async def query_records_advanced(self, universe_id: str, repository_id: str, 
                                   fields: List[str] = None, filters: List[Dict[str, Any]] = None,
                                   limit: int = 100, offset_token: str = "") -> Dict[str, Any]:
        """Execute advanced parameterised record query"""
        try:
            async with self.client as session:
                params = {
                    "universe_id": universe_id,
                    "repository_id": repository_id,
                    "limit": limit,
                    "offset_token": offset_token
                }
                
                if fields is not None:
                    params["fields"] = fields
                if filters is not None:
                    params["filters"] = filters
                
                result = await session.call_tool("query_records", params)
                return json.loads(result[0].text)
        except Exception as e:
            return {"status": "error", "error": str(e), "universe_id": universe_id, "repository_id": repository_id}

def print_enhanced_summary(data: Dict[str, Any], title: str):
    """Print enhanced formatted summary with new query capabilities"""
    print(f"\n{'='*20} {title} {'='*20}")
    
    if data.get("status") == "error":
        print(f"❌ Error: {data.get('error', 'Unknown error')}")
        if data.get("status_code"):
            print(f"   Status Code: {data.get('status_code')}")
        if data.get("response_body"):
            print(f"   Response: {data.get('response_body')[:200]}...")
        
        # Show troubleshooting info if available
        if "troubleshooting" in data:
            troubleshooting = data["troubleshooting"]
            print(f"\n🔍 Troubleshooting Information:")
            print(f"   Issue: {troubleshooting.get('issue', 'Unknown')}")
            
            if "possible_causes" in troubleshooting:
                print(f"\n💡 Possible Causes:")
                for cause in troubleshooting["possible_causes"]:
                    print(f"   • {cause}")
            
            if "next_steps" in troubleshooting:
                print(f"\n🔧 Next Steps:")
                for step in troubleshooting["next_steps"]:
                    print(f"   • {step}")
            
            if "auth_info" in troubleshooting:
                auth_info = troubleshooting["auth_info"]
                print(f"\n🔐 Authentication Details:")
                for key, value in auth_info.items():
                    print(f"   {key.replace('_', ' ').title()}: {value}")
                    
            if "suggestions" in troubleshooting:
                print(f"\n💡 Troubleshooting Suggestions:")
                for suggestion in troubleshooting["suggestions"]:
                    print(f"   • {suggestion}")
        
        # Show field suggestions if available
        if "available_fields" in data:
            available_fields = data["available_fields"]
            print(f"\n📝 Available Fields ({len(available_fields)}):")
            for field in available_fields[:10]:  # Show first 10
                print(f"   • {field}")
            if len(available_fields) > 10:
                print(f"   ... and {len(available_fields) - 10} more")
            
            if "available_query_ids" in data:
                print(f"\n🔑 Query Field IDs (use these in queries):")
                query_ids = data["available_query_ids"]
                for field_id in query_ids[:10]:  # Show first 10
                    print(f"   • {field_id}")
                if len(query_ids) > 10:
                    print(f"   ... and {len(query_ids) - 10} more")
            
            if "suggestion" in data:
                print(f"\n💡 Suggestion: {data['suggestion']}")
        
        return
    
    # Handle successful query results
    if data.get("status") == "success" and "data" in data:
        query_data = data.get("data", {})
        records = query_data.get("records", [])
        metadata = data.get("metadata", {})
        
        print(f"✅ SUCCESS: Query executed successfully")
        print(f"📊 Records returned: {len(records)}")
        print(f"   Has more: {metadata.get('has_more', False)}")
        if metadata.get('next_offset_token'):
            print(f"   Next offset token: {metadata['next_offset_token'][:20]}...")
        
        # Show sample records
        if records:
            print(f"\n📋 Sample Records (showing first {min(5, len(records))}):")
            for i, record in enumerate(records[:5], 1):
                print(f"   {i}. Record:")
                for key, value in record.items():
                    if key != "_record_id":  # Skip internal ID
                        display_value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                        print(f"      {key}: {display_value}")
                print()
            
            if len(records) > 5:
                print(f"   ... and {len(records) - 5} more records")
        else:
            print("📋 No records found matching the query criteria")
        
        # Show query parameters
        if "query_parameters" in data:
            params = data["query_parameters"]
            print(f"\n🔍 Query Summary:")
            print(f"   Universe ID: {params.get('universe_id', 'N/A')}")
            print(f"   Repository ID: {params.get('repository_id', 'N/A')}")
            print(f"   Fields: {len(params.get('fields', []))} selected")
            print(f"   Filters: {len(params.get('filters', []))} applied")
            print(f"   Limit: {params.get('limit', 'N/A')}")
    
    # Handle query parameters (for ready_for_implementation status)
    elif "query_parameters" in data:
        params = data["query_parameters"]
        print("🔍 Query Parameters:")
        print(f"   Universe ID: {params.get('universe_id', 'N/A')}")
        print(f"   Repository ID: {params.get('repository_id', 'N/A')}")
        print(f"   Fields: {len(params.get('fields', []))} selected")
        print(f"   Filters: {len(params.get('filters', []))} applied")
        print(f"   Limit: {params.get('limit', 'N/A')}")
        
        if params.get('fields'):
            print(f"   Selected Fields: {', '.join(params['fields'][:5])}")
            if len(params['fields']) > 5:
                print(f"                    ... and {len(params['fields']) - 5} more")
        
        if params.get('filters'):
            print("   Applied Filters:")
            for i, filter_def in enumerate(params['filters'][:3], 1):
                print(f"     {i}. {filter_def.get('fieldId')} {filter_def.get('operator')} '{filter_def.get('value')}'")
            if len(params['filters']) > 3:
                print(f"     ... and {len(params['filters']) - 3} more filters")
    
    # Handle field information with enhanced mapping display
    if "fields" in data and isinstance(data["fields"], list):
        fields = data["fields"]
        print(f"📝 Field Information ({len(fields)} total):")
        
        if "summary" in data:
            summary = data["summary"]
            print(f"   Required: {summary.get('required_fields', 0)}")
            print(f"   Optional: {summary.get('optional_fields', 0)}")
            
            field_types = summary.get('field_types', {})
            if field_types:
                print(f"   Types: {', '.join([f'{k}({v})' for k, v in field_types.items()])}")
        
        # Show sample fields with consistent uppercase display
        for i, field in enumerate(fields[:5], 1):
            required = "🔴" if field.get('required') else "⚪"
            repeatable = "🔄" if field.get('repeatable') else ""
            field_type = field.get('type', 'UNKNOWN')
            display_name = field.get('displayName', field.get('name', 'N/A'))
            
            print(f"   {i}. {required} {display_name} ({field_type}) {repeatable}")
        
        if len(fields) > 5:
            print(f"   ... and {len(fields) - 5} more fields")
        
        # Show query helpers if available
        if "query_helpers" in data:
            helpers = data["query_helpers"]
            print(f"\n💡 Query Helpers:")
            if helpers.get("all_query_field_ids"):
                print(f"   Use these field IDs in queries: {', '.join(helpers['all_query_field_ids'][:5])}")
                if len(helpers['all_query_field_ids']) > 5:
                    print(f"   ... and {len(helpers['all_query_field_ids']) - 5} more")
    
    # Handle implementation notes (for backward compatibility)
    if "implementation_note" in data:
        note = data["implementation_note"]
        print(f"\n💡 Implementation Note:")
        print(f"   {note.get('message', 'N/A')}")
        
        if "next_steps" in note:
            print("   Next Steps:")
            for step in note["next_steps"]:
                print(f"     • {step}")
    
    # Handle curl equivalent
    if "curl_equivalent" in data:
        print(f"\n📋 Equivalent cURL Command:")
        curl_cmd = data["curl_equivalent"]
        # Print first few lines of curl command
        lines = curl_cmd.split('\n')
        for line in lines[:3]:
            print(f"   {line}")
        if len(lines) > 3:
            print(f"   ... ({len(lines) - 3} more lines)")
    elif "troubleshooting" in data and "curl_equivalent" in data["troubleshooting"]:
        print(f"\n📋 Equivalent cURL Command:")
        curl_cmd = data["troubleshooting"]["curl_equivalent"]
        lines = curl_cmd.split('\n')
        for line in lines[:3]:
            print(f"   {line}")
        if len(lines) > 3:
            print(f"   ... ({len(lines) - 3} more lines)")
    
    print(f"⏰ Timestamp: {data.get('timestamp', 'N/A')}")

async def demo_parameterised_queries():
    """Demonstrate the new parameterised query capabilities"""
    print("\n" + "=" * 60)
    print("🔍 Enhanced Parameterised Query Demonstrations")
    print("=" * 60)
    print("This demo shows the enhanced parameterised query capabilities.")
    
    client = EnhancedBoomiDataHubMCPClient()
    
    # First, find an available model to work with
    print("\n🔍 Step 1: Finding available models for demonstration...")
    all_models_result = await client.get_all_models()
    
    if all_models_result.get("status") != "success":
        print("❌ Cannot demonstrate without available models")
        return
    
    # Get a published model for demonstration
    published_models = all_models_result.get("data", {}).get("published", [])
    
    if not published_models:
        print("❌ No published models available for demonstration")
        return
    
    demo_model = published_models[0]  # Use first published model
    model_id = demo_model.get("id")
    model_name = demo_model.get("name", "Unknown")
    
    print(f"✅ Using model '{model_name}' (ID: {model_id}) for demonstration")
    
    # Step 2: Get enhanced field information
    print(f"\n🔍 Step 2: Exploring enhanced field structure for '{model_name}'...")
    fields_result = await client.get_model_fields(model_id)
    print_enhanced_summary(fields_result, f"Enhanced Field Information - {model_name}")
    
    if fields_result.get("status") != "success":
        print("❌ Cannot proceed without field information")
        return
    
    # Extract available fields for query building
    query_helpers = fields_result.get("query_helpers", {})
    available_fields = query_helpers.get("all_field_names", [])
    string_fields = query_helpers.get("string_fields", [])
    
    if not available_fields:
        print("❌ No fields available for querying")
        return
    
    # Step 3: Demonstrate basic parameterised query
    print(f"\n🔍 Step 3: Basic enhanced parameterised query for '{model_name}'...")
    
    # Use a sample repository ID (you might need to adjust this)
    sample_repo_id = "43212d46-1832-4ab1-820d-c0334d619f6f"  # From your curl example
    
    basic_query_result = await client.query_records_advanced(model_id, sample_repo_id, limit=10)
    print_enhanced_summary(basic_query_result, f"Basic Enhanced Query - {model_name}")
    
    # Step 4: Demonstrate advanced query with field selection
    print(f"\n🔍 Step 4: Advanced query with custom field selection...")
    
    # Select first 3 fields for the demo
    selected_fields = available_fields[:3] if len(available_fields) >= 3 else available_fields
    
    advanced_query_result = await client.query_records_advanced(
        universe_id=model_id,
        repository_id=sample_repo_id,
        fields=selected_fields,
        limit=10
    )
    print_enhanced_summary(advanced_query_result, f"Advanced Query with Fields - {model_name}")
    
    # Step 5: Demonstrate filtering capabilities
    print(f"\n🔍 Step 5: Query with filters and field mapping...")
    
    # Create sample filters if we have string fields
    sample_filters = []
    if string_fields:
        # Create a sample filter for the first string field
        first_string_field = string_fields[0]
        sample_filters = [
            {
                "fieldId": first_string_field,  # This will be auto-converted to uppercase
                "operator": "CONTAINS", 
                "value": "test"
            }
        ]
    
    if sample_filters:
        filtered_query_result = await client.query_records_advanced(
            universe_id=model_id,
            repository_id=sample_repo_id,
            fields=selected_fields,
            filters=sample_filters,
            limit=5
        )
        print_enhanced_summary(filtered_query_result, f"Filtered Query with Field Mapping - {model_name}")
    else:
        print("ℹ️  No string fields available for filter demonstration")
    
    print("\n💡 Enhanced Query Features Summary:")
    print("🔹 Automatic field name conversion (ad_id → AD_ID)")
    print("🔹 Dual credential support (API vs DataHub credentials)")
    print("🔹 Enhanced error messages with troubleshooting")
    print("🔹 Field validation and mapping")
    print("🔹 Case-insensitive field matching")
    print("🔹 Detailed field information with display/query mapping")

async def interactive_query_builder():
    """Enhanced interactive query builder with field mapping support"""
    print("\n" + "=" * 60)
    print("🔧 Enhanced Interactive Query Builder")
    print("=" * 60)
    print("Build and test parameterised queries with automatic field mapping")
    print("Type 'help' for commands, 'quit' to exit")
    
    client = EnhancedBoomiDataHubMCPClient()
    
    # State variables
    current_model = None
    current_model_fields = None
    selected_fields = []
    active_filters = []
    current_limit = 10
    current_repo_id = "43212d46-1832-4ab1-820d-c0334d619f6f"  # Default from example
    
    def parse_field_selection(selection_str: str, total_fields: int) -> List[int]:
        """
        Parse field selection string like "1-3,5,7-9" into list of field indices
        
        Args:
            selection_str: String like "1", "1-3", "1,3,5", "1-3,5,7-9"
            total_fields: Total number of available fields
            
        Returns:
            List of 1-based field indices
        """
        indices = []
        
        # Split by commas first
        parts = [part.strip() for part in selection_str.split(',')]
        
        for part in parts:
            if '-' in part:
                # Handle range like "1-3" or "7-9"
                try:
                    start, end = part.split('-')
                    start_idx = int(start.strip())
                    end_idx = int(end.strip())
                    
                    # Validate range
                    if start_idx < 1 or end_idx > total_fields or start_idx > end_idx:
                        print(f"⚠️  Invalid range: {part} (valid range: 1-{total_fields})")
                        continue
                    
                    # Add all indices in range (inclusive)
                    indices.extend(range(start_idx, end_idx + 1))
                    
                except ValueError:
                    print(f"⚠️  Invalid range format: {part}")
                    continue
            else:
                # Handle single number like "5"
                try:
                    idx = int(part.strip())
                    if 1 <= idx <= total_fields:
                        indices.append(idx)
                    else:
                        print(f"⚠️  Invalid field number: {idx} (valid range: 1-{total_fields})")
                except ValueError:
                    print(f"⚠️  Invalid field number: {part}")
                    continue
        
        # Remove duplicates and sort
        return sorted(list(set(indices)))
    
    def print_current_state():
        print(f"\n📊 Current Query State:")
        print(f"   Model: {current_model.get('name', 'None') if current_model else 'None selected'}")
        print(f"   Repository ID: {current_repo_id}")
        print(f"   Selected Fields: {len(selected_fields)} ({', '.join(selected_fields[:3])}{'...' if len(selected_fields) > 3 else ''})")
        print(f"   Active Filters: {len(active_filters)}")
        print(f"   Limit: {current_limit}")
    
    def print_help():
        print("""
Available Commands:
  📋 Model Commands:
    list models          - Show available models
    select model <n>  - Select a model for querying
    show fields          - Show fields for current model (all UPPERCASE)
    reload fields        - Reload field information for current model
    
  🔍 Query Building:
    add field <n>        - Add single field by number or name
    add field <ranges>   - Add multiple fields (e.g., "1-3,5,7-9")
    remove field <n>     - Remove field from selection
    clear fields         - Clear all selected fields
    show selection       - Show current field selection
    
  🎯 Filter Commands:
    add filter <field> <operator> <value>  - Add a filter (auto-converts to uppercase)
    list filters         - Show current filters
    clear filters        - Clear all filters
    
  ⚙️  Query Execution:
    set limit <number>   - Set query limit (default: 10)
    set repo <id>        - Set repository ID
    execute query        - Run the query with current parameters
    show query           - Preview query parameters
    
  ℹ️  Examples:
    add field 1          - Add first field
    add field 1-3        - Add fields 1, 2, and 3
    add field 1,3,5      - Add fields 1, 3, and 5
    add field 1-3,5,7-9  - Add fields 1,2,3,5,7,8,9
    add field AD_ID      - Add field by name
    
  ℹ️  Debugging:
    debug                - Show debug information
    help                 - Show this help  
    quit                 - Exit builder
        """)
    
    print_help()
    print_current_state()
    
    while True:
        try:
            user_input = input(f"\n🔧 Enhanced Query Builder> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'help':
                print_help()
            elif user_input.lower() == 'debug':
                print(f"\n🔍 Debug Information:")
                print(f"   current_model: {current_model is not None} ({current_model.get('name') if current_model else 'None'})")
                print(f"   current_model_fields: {current_model_fields is not None}")
                if current_model_fields:
                    field_count = len(current_model_fields.get('fields', []))
                    print(f"   Fields available: {field_count}")
                    print(f"   Fields status: {current_model_fields.get('status', 'Unknown')}")
                else:
                    print(f"   Fields available: 0")
                print(f"   selected_fields: {len(selected_fields)} ({selected_fields})")
                print(f"   active_filters: {len(active_filters)}")
                
                if current_model and not current_model_fields:
                    print(f"\n💡 Suggested fix: Try 'reload fields' command")
                        
            elif user_input.lower() == 'reload fields':
                if not current_model:
                    print("❌ No model selected. Use 'select model <n>' first")
                else:
                    print(f"🔄 Reloading field information for '{current_model.get('name')}'...")
                    
                    # Reload field information
                    fields_result = await client.get_model_fields(current_model.get('id'))
                    if fields_result.get("status") == "success":
                        current_model_fields = fields_result
                        field_count = len(fields_result.get('fields', []))
                        print(f"✅ Successfully reloaded {field_count} fields")
                    else:
                        print(f"❌ Failed to reload field information: {fields_result.get('error', 'Unknown error')}")
                        current_model_fields = None
                        
            elif user_input.lower() == 'list models':
                print("📋 Fetching available models...")
                models_result = await client.get_all_models()
                if models_result.get("status") == "success":
                    published = models_result.get("data", {}).get("published", [])
                    print(f"\n📗 Published Models ({len(published)}):")
                    for i, model in enumerate(published, 1):
                        print(f"   {i}. {model.get('name', 'N/A')} (ID: {model.get('id', 'N/A')})")
                else:
                    print(f"❌ Error: {models_result.get('error', 'Unknown error')}")
                    
            elif user_input.lower().startswith('select model '):
                model_name = user_input[13:].strip()
                print(f"🔍 Searching for model '{model_name}'...")
                
                search_result = await client.search_models_by_name(model_name)
                if search_result.get("status") == "success" and search_result.get("matches"):
                    matches = search_result["matches"]
                    if len(matches) == 1:
                        current_model = matches[0]
                        print(f"✅ Selected model: {current_model.get('name')}")
                        
                        # Get enhanced field information
                        fields_result = await client.get_model_fields(current_model.get('id'))
                        if fields_result.get("status") == "success":
                            current_model_fields = fields_result
                            field_count = len(fields_result.get('fields', []))
                            print(f"   📝 {field_count} fields available with mapping information")
                        else:
                            print(f"⚠️  Could not load field information: {fields_result.get('error', 'Unknown error')}")
                            current_model_fields = None
                            
                        # Reset selections
                        selected_fields = []
                        active_filters = []
                    else:
                        print(f"🔍 Found {len(matches)} matches:")
                        for i, match in enumerate(matches[:5], 1):
                            print(f"   {i}. {match.get('name', 'N/A')}")
                        print("Please be more specific or use exact name")
                else:
                    print(f"❌ Model '{model_name}' not found")
                    
            elif user_input.lower() == 'show fields':
                if not current_model:
                    print("❌ No model selected. Use 'select model <n>' first")
                elif not current_model_fields:
                    print(f"⚠️  Model '{current_model.get('name')}' is selected but field information is not available")
                    print("🔄 Use 'reload fields' to try loading field information again")
                else:
                    fields = current_model_fields.get("fields", [])
                    print(f"\n📝 Available Fields for {current_model.get('name', 'Unknown')} ({len(fields)}):")
                    print(f"{'#':<3} {'Field Name':<20} {'Type':<10} {'Req'}")
                    print("-" * 40)
                    for i, field in enumerate(fields, 1):
                        display_name = field.get('displayName', field.get('name', 'N/A')).upper()
                        field_type = field.get('type', 'UNKNOWN')
                        required = "Yes" if field.get('required') else "No"
                        print(f"{i:<3} {display_name:<20} {field_type:<10} {required}")
                    
                    print(f"\n💡 Use field numbers or names in commands:")
                    print(f"   Examples: 'add field 1', 'add field 1-3', 'add field 1,3,5', 'add field AD_ID'")
                        
            elif user_input.lower().startswith('add field '):
                field_input = user_input[10:].strip()
                if not current_model_fields:
                    print("❌ No model selected. Use 'select model <n>' first")
                else:
                    fields = current_model_fields.get("fields", [])
                    
                    # Check if input contains numbers (bulk selection) or is a field name
                    if any(char.isdigit() for char in field_input):
                        # Handle bulk field selection by numbers
                        indices = parse_field_selection(field_input, len(fields))
                        
                        if indices:
                            added_fields = []
                            for idx in indices:
                                field = fields[idx - 1]  # Convert to 0-based index
                                field_name = field.get('displayName', field.get('name', '')).upper()
                                if field_name and field_name not in selected_fields:
                                    selected_fields.append(field_name)
                                    added_fields.append(field_name)
                            
                            if added_fields:
                                print(f"✅ Added {len(added_fields)} fields: {', '.join(added_fields)}")
                            else:
                                print("ℹ️  All specified fields were already selected")
                        else:
                            print("❌ No valid field indices found")
                    else:
                        # Handle single field by name
                        field_name_upper = field_input.upper()
                        field_found = False
                        
                        for field in fields:
                            available_name = field.get('displayName', field.get('name', '')).upper()
                            
                            if field_name_upper == available_name:
                                if field_name_upper not in selected_fields:
                                    selected_fields.append(field_name_upper)
                                    print(f"✅ Added field: {field_name_upper}")
                                    field_found = True
                                    break
                                else:
                                    print(f"ℹ️  Field '{field_name_upper}' already selected")
                                    field_found = True
                                    break
                        
                        if not field_found:
                            print(f"❌ Field '{field_input}' not found in model")
                        
            elif user_input.lower().startswith('remove field '):
                field_name = user_input[13:].strip()
                if field_name in selected_fields:
                    selected_fields.remove(field_name)
                    print(f"✅ Removed field: {field_name}")
                else:
                    print(f"ℹ️  Field '{field_name}' not in selection")
                    
            elif user_input.lower() == 'clear fields':
                selected_fields = []
                print("✅ Cleared all selected fields")
                
            elif user_input.lower() == 'show selection':
                print(f"\n📋 Current Field Selection ({len(selected_fields)}):")
                for i, field in enumerate(selected_fields, 1):
                    print(f"   {i}. {field}")
                if not selected_fields:
                    print("   (No fields selected - will use all available fields)")
                    
            elif user_input.lower().startswith('add filter '):
                parts = user_input[11:].split()
                if len(parts) >= 3:
                    field_id = parts[0].upper()  # Convert to uppercase
                    operator = parts[1].upper()
                    value = ' '.join(parts[2:])
                    
                    new_filter = {
                        "fieldId": field_id,
                        "operator": operator,
                        "value": value
                    }
                    active_filters.append(new_filter)
                    print(f"✅ Added filter: {field_id} {operator} '{value}'")
                else:
                    print("❌ Invalid filter format. Use: add filter <field> <operator> <value>")
                    print("   Example: add filter ADVERTISER EQUALS Sony")
                    
            elif user_input.lower() == 'list filters':
                print(f"\n🎯 Active Filters ({len(active_filters)}):")
                for i, filter_def in enumerate(active_filters, 1):
                    print(f"   {i}. {filter_def['fieldId']} {filter_def['operator']} '{filter_def['value']}'")
                if not active_filters:
                    print("   (No filters active)")
                    
            elif user_input.lower() == 'clear filters':
                active_filters = []
                print("✅ Cleared all filters")
                
            elif user_input.lower().startswith('set limit '):
                try:
                    new_limit = int(user_input[10:])
                    current_limit = min(new_limit, 1000)  # Cap at 1000
                    print(f"✅ Set limit to: {current_limit}")
                except ValueError:
                    print("❌ Invalid limit. Use a number (e.g., 'set limit 50')")
                    
            elif user_input.lower().startswith('set repo '):
                current_repo_id = user_input[9:].strip()
                print(f"✅ Set repository ID to: {current_repo_id}")
                
            elif user_input.lower() == 'show query':
                print_current_state()
                if current_model:
                    print(f"\n📋 Query Preview:")
                    print(f"   Universe ID: {current_model.get('id')}")
                    print(f"   Repository ID: {current_repo_id}")
                    print(f"   Fields: {selected_fields if selected_fields else 'All available fields (UPPERCASE)'}")
                    print(f"   Filters: {len(active_filters)} applied")
                    print(f"   Limit: {current_limit}")
                    
                    if active_filters:
                        print(f"\n   Filter Details:")
                        for i, filter_def in enumerate(active_filters, 1):
                            print(f"     {i}. {filter_def['fieldId']} {filter_def['operator']} '{filter_def['value']}'")
                    
                    print(f"\n💡 All field names are automatically uppercase for query compatibility")
                    
            elif user_input.lower() == 'execute query':
                if not current_model:
                    print("❌ No model selected. Use 'select model <n>' first")
                else:
                    print(f"🔍 Executing enhanced query for {current_model.get('name')}...")
                    
                    query_result = await client.query_records_advanced(
                        universe_id=current_model.get('id'),
                        repository_id=current_repo_id,
                        fields=selected_fields if selected_fields else None,
                        filters=active_filters if active_filters else None,
                        limit=current_limit
                    )
                    
                    print_enhanced_summary(query_result, f"Enhanced Query Results - {current_model.get('name')}")
                    
            else:
                print(f"❌ Unknown command: {user_input}")
                print("Type 'help' for available commands")
                
            # Show current state after most commands
            if user_input.lower() not in ['help', 'quit', 'exit']:
                print_current_state()
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    """Main demonstration including enhanced functionality"""
    print("🚀 Enhanced Boomi DataHub MCP Client")
    print("=" * 60)
    print("Now with automatic field mapping and dual credential support!")
    
    # Test connection first
    client = EnhancedBoomiDataHubMCPClient()
    print("\n🔍 Testing connection...")
    connection_result = await client.test_connection()
    
    if connection_result.get("status") == "error":
        print("❌ Connection failed - cannot proceed")
        return
    
    print("✅ Connection successful")
    
    # Check for DataHub credentials
    if connection_result.get("connection_result", {}).get("has_datahub_credentials"):
        print("🔑 DataHub credentials detected - ready for record queries")
    else:
        print("⚠️  No separate DataHub credentials - using API credentials for queries")
        print("💡 Consider setting BOOMI_DATAHUB_USERNAME and BOOMI_DATAHUB_PASSWORD for optimal performance")
    
    print("\n🎯 Enhanced Features Available:")
    print("🔹 Automatic field name conversion (ad_id → AD_ID)")
    print("🔹 Case-insensitive field matching")
    print("🔹 Enhanced error messages with troubleshooting")
    print("🔹 Field validation and mapping")
    print("🔹 Dual credential support")

if __name__ == "__main__":
    print("🚀 Enhanced Boomi DataHub MCP Client")
    print("Choose a demo mode:")
    print("1. Quick Demo (connection + basic functionality)")
    print("2. Enhanced Parameterised Query Demonstrations")
    print("3. Enhanced Interactive Query Builder (RECOMMENDED)")
    print("4. All Enhanced Demonstrations")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            asyncio.run(main())
        elif choice == "2":
            asyncio.run(demo_parameterised_queries())
        elif choice == "3":
            asyncio.run(interactive_query_builder())
        elif choice == "4":
            print("\n🚀 Running complete enhanced demonstration suite...")
            asyncio.run(main())
            asyncio.run(demo_parameterised_queries())
            asyncio.run(interactive_query_builder())
        else:
            print("Invalid choice, running enhanced interactive query builder...")
            asyncio.run(interactive_query_builder())
    
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()