# boomi_datahub_mcp_server_v2.py
"""
Enhanced Boomi DataHub MCP Server with Field Mapping and Dual Credentials

This enhanced MCP server now supports:
- Parameterised queries with automatic field name conversion
- Dual credential support (API vs DataHub credentials)
- Enhanced field mapping (display names vs query field IDs)
- Better error handling and troubleshooting
"""

from fastmcp import FastMCP
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Try multiple import paths for boomi_datahub_client
try:
    # First try importing from the current directory
    from boomi_datahub_client import BoomiDataHubClient, BoomiCredentials
except ImportError:
    try:
        # Try importing from parent directory
        sys.path.append(os.path.dirname(__file__))
        from boomi_datahub_client import BoomiDataHubClient, BoomiCredentials
    except ImportError:
        try:
            # Try importing from ../boomi_datahub_apis directory
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'boomi_datahub_apis'))
            from boomi_datahub_client import BoomiDataHubClient, BoomiCredentials
        except ImportError:
            try:
                # Try importing from ./boomi_datahub_apis directory  
                sys.path.append(os.path.join(os.path.dirname(__file__), 'boomi_datahub_apis'))
                from boomi_datahub_client import BoomiDataHubClient, BoomiCredentials
            except ImportError as e:
                print(f"❌ Error importing BoomiDataHubClient: {e}")
                print("\n🔍 Troubleshooting Import Issues:")
                print("Please ensure boomi_datahub_client.py is in one of these locations:")
                print(f"  1. Current directory: {os.path.dirname(__file__)}")
                print(f"  2. Parent directory: {os.path.dirname(os.path.dirname(__file__))}")
                print(f"  3. Subdirectory: {os.path.join(os.path.dirname(__file__), 'boomi_datahub_apis')}")
                print(f"  4. Relative path: {os.path.join(os.path.dirname(__file__), '..', 'boomi_datahub_apis')}")
                print("\n💡 Quick Fix Options:")
                print("  • Copy boomi_datahub_client.py to the same directory as this server")
                print("  • Update the Python path in your environment")
                print("  • Install as a package: pip install -e .")
                print(f"\n📁 Current working directory: {os.getcwd()}")
                print(f"📁 Server file location: {__file__}")
                sys.exit(1)

# Create the MCP server
mcp = FastMCP("Enhanced Boomi DataHub MCP Server")

# Global client instance (will be initialized when first needed)
_boomi_client: Optional[BoomiDataHubClient] = None

def get_boomi_client() -> BoomiDataHubClient:
    """
    Get or create the Boomi DataHub client instance
    
    Returns:
        BoomiDataHubClient instance
        
    Raises:
        Exception: If client cannot be initialized
    """
    global _boomi_client
    
    if _boomi_client is None:
        try:
            _boomi_client = BoomiDataHubClient()
            
            # Test the connection
            test_result = _boomi_client.test_connection()
            if not test_result['success']:
                raise Exception(f"Boomi connection failed: {test_result['error']}")
                
        except Exception as e:
            raise Exception(f"Failed to initialize Boomi DataHub client: {str(e)}")
    
    return _boomi_client

# MCP Resources (keeping original functionality)

@mcp.resource("boomi://datahub/models/all")
def get_all_models() -> str:
    """Retrieve all Boomi DataHub models from all repositories"""
    try:
        client = get_boomi_client()
        all_models = client.get_all_models()
        
        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_models": len(all_models['published']) + len(all_models['draft']),
                "published_count": len(all_models['published']),
                "draft_count": len(all_models['draft'])
            },
            "data": all_models
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "data": None
        }
        return json.dumps(error_result, indent=2)

@mcp.resource("boomi://datahub/models/published")
def get_published_models() -> str:
    """Retrieve all published Boomi DataHub models"""
    try:
        client = get_boomi_client()
        published_models = client.get_published_models()
        
        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "published_count": len(published_models),
                "status_filter": "published_only"
            },
            "data": published_models
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "data": None
        }
        return json.dumps(error_result, indent=2)

@mcp.resource("boomi://datahub/models/draft")
def get_draft_models() -> str:
    """Retrieve all draft Boomi DataHub models"""
    try:
        client = get_boomi_client()
        draft_models = client.get_draft_models()
        
        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "draft_count": len(draft_models),
                "status_filter": "draft_only"
            },
            "data": draft_models
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "data": None
        }
        return json.dumps(error_result, indent=2)

@mcp.resource("boomi://datahub/model/{model_id}")
def get_model_details(model_id: str) -> str:
    """Retrieve detailed information for a specific model"""
    try:
        client = get_boomi_client()
        model_details = client.get_model_by_id(model_id)
        
        if model_details is None:
            result = {
                "status": "not_found",
                "timestamp": datetime.now().isoformat(),
                "message": f"Model with ID '{model_id}' not found",
                "data": None
            }
        else:
            enhanced_details = model_details.copy()
            enhanced_details['_metadata'] = {
                "retrieved_at": datetime.now().isoformat(),
                "model_id": model_id,
                "has_fields": 'fields' in model_details,
                "has_sources": 'sources' in model_details,
                "has_match_rules": 'matchRules' in model_details,
                "field_count": len(model_details.get('fields', [])),
                "source_count": len(model_details.get('sources', []))
            }
            
            result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "data": enhanced_details
            }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "model_id": model_id,
            "data": None
        }
        return json.dumps(error_result, indent=2)

@mcp.resource("boomi://datahub/connection/test")
def test_datahub_connection() -> str:
    """Test connection to Boomi DataHub APIs"""
    try:
        client = get_boomi_client()
        test_result = client.test_connection()
        
        result = {
            "status": "connection_test",
            "timestamp": datetime.now().isoformat(),
            "connection_result": test_result,
            "recommendations": []
        }
        
        if test_result['success']:
            result["recommendations"].append("Connection is healthy and ready for use")
            if test_result.get('has_datahub_credentials'):
                result["recommendations"].append("DataHub credentials are configured for record queries")
            else:
                result["recommendations"].append("Consider setting DataHub credentials for record queries")
        else:
            result["recommendations"].append("Check environment variables: BOOMI_USERNAME, BOOMI_PASSWORD, BOOMI_ACCOUNT_ID")
            if test_result['status_code'] == 401:
                result["recommendations"].append("Verify authentication credentials")
            elif test_result['status_code'] == 403:
                result["recommendations"].append("Check account permissions and API access")
            elif test_result['status_code'] is None:
                result["recommendations"].append("Check network connectivity and base URL")
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "recommendations": [
                "Ensure boomi_datahub_client.py is properly configured",
                "Verify all required environment variables are set",
                "Check network connectivity to Boomi APIs"
            ]
        }
        return json.dumps(error_result, indent=2)

# NEW: Enhanced MCP Tools with Field Mapping

@mcp.tool()
def search_models_by_name(name_pattern: str) -> dict:
    """Search for Boomi DataHub models by name pattern"""
    try:
        client = get_boomi_client()
        all_models_data = client.get_all_models()
        
        all_models = all_models_data['published'] + all_models_data['draft']
        
        matching_models = []
        for model in all_models:
            model_name = model.get('name', '').lower()
            if name_pattern.lower() in model_name:
                matching_models.append(model)
        
        result = {
            "status": "success",
            "search_pattern": name_pattern,
            "total_searched": len(all_models),
            "matches_found": len(matching_models),
            "matches": matching_models,
            "timestamp": datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "search_pattern": name_pattern,
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool()
def get_model_statistics() -> dict:
    """Get comprehensive statistics about Boomi DataHub models"""
    try:
        client = get_boomi_client()
        all_models_data = client.get_all_models()
        
        published_models = all_models_data['published']
        draft_models = all_models_data['draft']
        all_models = published_models + draft_models
        
        stats = {
            "overview": {
                "total_models": len(all_models),
                "published_models": len(published_models),
                "draft_models": len(draft_models),
                "published_percentage": round((len(published_models) / len(all_models) * 100) if all_models else 0, 1)
            },
            "field_analysis": {
                "models_with_fields": 0,
                "total_fields": 0,
                "avg_fields_per_model": 0,
                "max_fields": 0,
                "min_fields": float('inf')
            },
            "source_analysis": {
                "models_with_sources": 0,
                "total_sources": 0,
                "avg_sources_per_model": 0
            },
            "version_analysis": {
                "models_with_versions": 0,
                "unique_versions": set()
            },
            "timestamp": datetime.now().isoformat()
        }
        
        models_with_fields = []
        field_counts = []
        
        for model in all_models:
            if 'fields' in model and model['fields']:
                field_count = len(model['fields'])
                models_with_fields.append(model)
                field_counts.append(field_count)
                stats["field_analysis"]["total_fields"] += field_count
                stats["field_analysis"]["max_fields"] = max(stats["field_analysis"]["max_fields"], field_count)
                stats["field_analysis"]["min_fields"] = min(stats["field_analysis"]["min_fields"], field_count)
            
            if 'sources' in model and model['sources']:
                stats["source_analysis"]["models_with_sources"] += 1
                stats["source_analysis"]["total_sources"] += len(model['sources'])
            
            if 'version' in model or 'latestVersion' in model:
                stats["version_analysis"]["models_with_versions"] += 1
                version = model.get('version') or model.get('latestVersion')
                if version:
                    stats["version_analysis"]["unique_versions"].add(version)
        
        stats["field_analysis"]["models_with_fields"] = len(models_with_fields)
        if models_with_fields:
            stats["field_analysis"]["avg_fields_per_model"] = round(
                stats["field_analysis"]["total_fields"] / len(models_with_fields), 1
            )
        else:
            stats["field_analysis"]["min_fields"] = 0
        
        if stats["source_analysis"]["models_with_sources"] > 0:
            stats["source_analysis"]["avg_sources_per_model"] = round(
                stats["source_analysis"]["total_sources"] / stats["source_analysis"]["models_with_sources"], 1
            )
        
        stats["version_analysis"]["unique_versions"] = list(stats["version_analysis"]["unique_versions"])
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from boomi_datahub_client import BoomiDataHubClient

@mcp.tool()
def query_records(universe_id: str, repository_id: str, fields: Optional[List[str]] = None,
                  filters: Optional[List[Dict[str, Any]]] = None, limit: int = 100,
                  offset_token: str = "") -> dict:
    """
    Query Boomi DataHub records with full parameterisation and field mapping
    
    This tool enables AI agents to execute parameterised queries with automatic
    field name conversion (display names to query field IDs).
    
    Args:
        universe_id: The universe identifier to query
        repository_id: The repository identifier within the universe  
        fields: List of field names to retrieve (display names or query field IDs)
        filters: List of filter dictionaries with fieldId, operator, and value
        limit: Maximum number of records to return (default: 100)
        offset_token: Pagination token for continuing previous queries
        
    Returns:
        Dictionary containing query results and metadata
    """
    try:
        client = get_boomi_client()
        
        # Get model details to validate fields
        model_details = client.get_model_by_id(universe_id)
        
        if model_details is None:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": f"Universe/Model '{universe_id}' not found",
                "universe_id": universe_id,
                "repository_id": repository_id
            }
        
        # Get available fields from model with consistent UPPERCASE presentation
        available_fields = [field['name'].upper() for field in model_details.get('fields', [])]
        
        # Create a mapping from original field names (as in XML) to uppercase field names
        original_to_upper = {
            field['originalName'].lower(): field['name'].upper()
            for field in model_details['fields']
            if 'originalName' in field and 'name' in field
        }
        
        # Validate and prepare fields - always convert to uppercase
        if fields is None:
            query_fields = available_fields  # Already uppercase
        else:
            query_fields = [field.upper() for field in fields]
            invalid_fields = [field for field in query_fields if field not in available_fields]
            if invalid_fields:
                return {
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": f"Invalid fields: {invalid_fields}",
                    "available_fields": available_fields,
                    "suggestion": "Use uppercase field names like 'AD_ID', 'ADVERTISER', 'PRODUCT'",
                    "universe_id": universe_id,
                    "repository_id": repository_id
                }
        
        # Validate filters and ensure uppercase field IDs
        validated_filters = []
        if filters:
            for filter_def in filters:
                if not isinstance(filter_def, dict):
                    continue
                field_id = filter_def.get('fieldId')
                operator = filter_def.get('operator', 'EQUALS')
                value = filter_def.get('value')
                if field_id and value is not None:
                    field_id_upper = field_id.upper()
                    if field_id_upper in available_fields:
                        validated_filters.append({
                            "fieldId": field_id_upper,
                            "operator": operator,
                            "value": value
                        })
                    else:
                        # Skip invalid filters
                        pass
        
        # Prepare query parameters
        query_params = {
            "universe_id": universe_id,
            "repository_id": repository_id,
            "fields": query_fields,
            "filters": validated_filters,
            "limit": min(limit, 1000),  # Cap at 1000 for safety
            "offset_token": offset_token
        }
        
        # Execute the actual query using the BoomiDataHubClient
        try:
            query_result = client.query_records_by_parameters(**query_params)
            
            if query_result.get("status") == "success":
                # Map field names in each record to uppercase
                for record in query_result['data'].get('records', []):
                    mapped_record = {}
                    for key, value in record.items():
                        mapped_key = original_to_upper.get(key.lower(), key.upper())
                        mapped_record[mapped_key] = value
                    record.clear()
                    record.update(mapped_record)
                
                # Enhance the result with additional metadata
                query_result["model_info"] = {
                    "name": model_details.get('name'),
                    "id": universe_id,
                    "total_fields_available": len(available_fields),
                    "fields_in_query": len(query_fields),
                    "filters_applied": len(validated_filters)
                }
                query_result["curl_equivalent"] = generate_curl_equivalent(
                    universe_id, repository_id, query_fields, validated_filters, limit, offset_token
                )
            
            return query_result
        
        except Exception as query_error:
            # If the query execution fails, return error with helpful info
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": f"Query execution failed: {str(query_error)}",
                "query_parameters": query_params,
                "model_info": {
                    "name": model_details.get('name'),
                    "id": universe_id,
                    "total_fields_available": len(available_fields),
                    "fields_in_query": len(query_fields),
                    "filters_applied": len(validated_filters)
                },
                "troubleshooting": {
                    "curl_equivalent": generate_curl_equivalent(universe_id, repository_id, query_fields, validated_filters, limit, offset_token),
                    "suggestions": [
                        "Check if query_records_by_parameters method exists in BoomiDataHubClient",
                        "Verify Boomi credentials and network connectivity",
                        "Check if the universe and repository IDs are correct",
                        "Ensure field names match the model schema exactly",
                        "Consider setting separate DataHub credentials"
                    ]
                }
            }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "universe_id": universe_id,
            "repository_id": repository_id,
            "timestamp": datetime.now().isoformat()
        }

# @mcp.tool()
# def query_records(universe_id: str, repository_id: str, fields: List[str] = None, 
#                  filters: List[Dict[str, Any]] = None, limit: int = 100, 
#                  offset_token: str = "") -> dict:
#     """
#     Query Boomi DataHub records with full parameterisation and field mapping
    
#     This tool enables AI agents to execute parameterised queries with automatic
#     field name conversion (display names to query field IDs).
    
#     Args:
#         universe_id: The universe identifier to query
#         repository_id: The repository identifier within the universe  
#         fields: List of field names to retrieve (display names or query field IDs)
#         filters: List of filter dictionaries with fieldId, operator, and value
#         limit: Maximum number of records to return (default: 100)
#         offset_token: Pagination token for continuing previous queries
        
#     Returns:
#         Dictionary containing query results and metadata
#     """
#     try:
#         client = get_boomi_client()
        
#         # Get model details to validate fields
#         model_details = client.get_model_by_id(universe_id)
        
#         if model_details is None:
#             return {
#                 "status": "error",
#                 "timestamp": datetime.now().isoformat(),
#                 "error": f"Universe/Model '{universe_id}' not found",
#                 "universe_id": universe_id,
#                 "repository_id": repository_id
#             }
        
#         # Get available fields from model with consistent UPPERCASE presentation
#         available_fields = []
#         field_map = {}
#         display_to_query_map = {}
        
#         if 'fields' in model_details:
#             for field in model_details['fields']:
#                 original_name = field.get('name', '')
#                 uppercase_name = original_name.upper()  # Always use uppercase
                
#                 if uppercase_name:
#                     available_fields.append(uppercase_name)
#                     field_map[uppercase_name.lower()] = field
#                     display_to_query_map[uppercase_name.lower()] = uppercase_name
                    
#                     # Also map original name for backward compatibility
#                     if original_name.lower() != uppercase_name.lower():
#                         field_map[original_name.lower()] = field
#                         display_to_query_map[original_name.lower()] = uppercase_name
        
#         # Validate and prepare fields - always convert to uppercase
#         if fields is None:
#             query_fields = available_fields  # Already uppercase
#         else:
#             # Validate requested fields exist and convert to uppercase
#             invalid_fields = []
#             query_fields = []
            
#             for field in fields:
#                 field_upper = field.upper()  # Convert input to uppercase
                
#                 if field_upper in available_fields:
#                     # Direct uppercase match
#                     query_fields.append(field_upper)
#                 else:
#                     # Try to find a match through mapping
#                     field_lower = field.lower()
#                     if field_lower in display_to_query_map:
#                         query_fields.append(display_to_query_map[field_lower])
#                     else:
#                         invalid_fields.append(field)
            
#             if invalid_fields:
#                 return {
#                     "status": "error",
#                     "timestamp": datetime.now().isoformat(),
#                     "error": f"Invalid fields: {invalid_fields}",
#                     "available_fields": available_fields,
#                     "suggestion": "Use uppercase field names like 'AD_ID', 'ADVERTISER', 'PRODUCT'",
#                     "universe_id": universe_id,
#                     "repository_id": repository_id
#                 }
        
#         # Validate filters and ensure uppercase field IDs
#         validated_filters = []
#         if filters:
#             for filter_def in filters:
#                 if not isinstance(filter_def, dict):
#                     continue
                    
#                 field_id = filter_def.get('fieldId')
#                 operator = filter_def.get('operator', 'EQUALS')
#                 value = filter_def.get('value')
                
#                 if field_id and value is not None:
#                     # Always convert field_id to uppercase
#                     field_id_upper = field_id.upper()
                    
#                     if field_id_upper in available_fields:
#                         validated_filters.append({
#                             "fieldId": field_id_upper,
#                             "operator": operator,
#                             "value": value
#                         })
#                     else:
#                         # Try to find a match through mapping
#                         field_id_lower = field_id.lower()
#                         if field_id_lower in display_to_query_map:
#                             validated_filters.append({
#                                 "fieldId": display_to_query_map[field_id_lower],
#                                 "operator": operator,
#                                 "value": value
#                             })
#                         else:
#                             # Add anyway with uppercase conversion as fallback
#                             validated_filters.append({
#                                 "fieldId": field_id_upper,
#                                 "operator": operator,
#                                 "value": value
#                             })
        
#         # Prepare query parameters
#         query_params = {
#             "universe_id": universe_id,
#             "repository_id": repository_id,
#             "fields": query_fields,
#             "filters": validated_filters,
#             "limit": min(limit, 1000),  # Cap at 1000 for safety
#             "offset_token": offset_token
#         }
        
#         # Execute the actual query using the BoomiDataHubClient
#         try:
#             query_result = client.query_records_by_parameters(**query_params)
            
#             # Enhance the result with additional metadata
#             if query_result.get("status") == "success":
#                 query_result["model_info"] = {
#                     "name": model_details.get('name'),
#                     "id": universe_id,
#                     "total_fields_available": len(available_fields),
#                     "fields_in_query": len(query_fields),
#                     "filters_applied": len(validated_filters)
#                 }
#                 query_result["curl_equivalent"] = generate_curl_equivalent(
#                     universe_id, repository_id, query_fields, validated_filters, limit, offset_token
#                 )
            
#             result = query_result
            
#         except Exception as query_error:
#             # If the query execution fails, return error with helpful info
#             result = {
#                 "status": "error",
#                 "timestamp": datetime.now().isoformat(),
#                 "error": f"Query execution failed: {str(query_error)}",
#                 "query_parameters": query_params,
#                 "model_info": {
#                     "name": model_details.get('name'),
#                     "id": universe_id,
#                     "total_fields_available": len(available_fields),
#                     "fields_in_query": len(query_fields),
#                     "filters_applied": len(validated_filters)
#                 },
#                 "troubleshooting": {
#                     "curl_equivalent": generate_curl_equivalent(universe_id, repository_id, query_fields, validated_filters, limit, offset_token),
#                     "suggestions": [
#                         "Check if query_records_by_parameters method exists in BoomiDataHubClient",
#                         "Verify Boomi credentials and network connectivity",
#                         "Check if the universe and repository IDs are correct",
#                         "Ensure field names match the model schema exactly",
#                         "Consider setting separate DataHub credentials"
#                     ]
#                 }
#             }
        
#         return result
        
#     except Exception as e:
#         return {
#             "status": "error",
#             "error": str(e),
#             "universe_id": universe_id,
#             "repository_id": repository_id,
#             "timestamp": datetime.now().isoformat()
#         }

@mcp.tool()
def get_model_fields(model_id: str) -> dict:
    """
    Get detailed field information for a specific model with enhanced mapping
    
    This tool provides field mapping information to help with query construction.
    
    Args:
        model_id: The model/universe identifier
        
    Returns:
        Dictionary containing detailed field information with display/query mappings
    """
    try:
        client = get_boomi_client()
        model_details = client.get_model_by_id(model_id)
        
        if model_details is None:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": f"Model '{model_id}' not found",
                "model_id": model_id
            }
        
        # Extract and enhance field information
        fields_info = []
        if 'fields' in model_details:
            for field in model_details['fields']:
                # Always present fields as UPPERCASE for consistency
                original_name = field.get('name', '')
                display_name = original_name.upper()  # Show as uppercase
                query_field_id = original_name.upper()  # Ensure uppercase for queries
                
                field_info = {
                    "name": display_name,  # Show uppercase
                    "displayName": display_name,  # Show uppercase  
                    "queryFieldId": query_field_id,  # Always uppercase
                    "originalName": original_name,  # Keep original for reference
                    "type": field.get('type', ''),
                    "required": field.get('required', False),
                    "repeatable": field.get('repeatable', False),
                    "searchable": field.get('searchable', True),
                    "description": field.get('description', ''),
                }
                fields_info.append(field_info)
        
        # Categorise fields by type
        field_types = {}
        required_fields = []
        optional_fields = []
        
        for field in fields_info:
            field_type = field['type']
            if field_type not in field_types:
                field_types[field_type] = 0
            field_types[field_type] += 1
            
            if field['required']:
                required_fields.append(field['displayName'])
            else:
                optional_fields.append(field['displayName'])
        
        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "model_id": model_id,
            "model_name": model_details.get('name', ''),
            "fields": fields_info,
            "summary": {
                "total_fields": len(fields_info),
                "required_fields": len(required_fields),
                "optional_fields": len(optional_fields),
                "field_types": field_types
            },
            "query_helpers": {
                "all_field_names": [f['displayName'] for f in fields_info],
                "all_query_field_ids": [f['queryFieldId'] for f in fields_info],
                "required_field_names": [f['displayName'] for f in fields_info if f['required']],
                "optional_field_names": [f['displayName'] for f in fields_info if not f['required']],
                "string_fields": [f['displayName'] for f in fields_info if f['type'] == 'STRING'],
                "searchable_fields": [f['displayName'] for f in fields_info if f['searchable']]
            }
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "model_id": model_id,
            "timestamp": datetime.now().isoformat()
        }

def generate_curl_equivalent(universe_id: str, repository_id: str, fields: List[str], 
                           filters: List[Dict[str, Any]], limit: int, offset_token: str) -> str:
    """Generate equivalent curl command for the query"""
    
    # Build XML request body
    xml_body = f'<RecordQueryRequest limit="{limit}" offsetToken="{offset_token}">\n'
    xml_body += '   <view>\n'
    
    for field in fields:
        xml_body += f'     <fieldId>{field}</fieldId>\n'
    
    xml_body += '   </view>\n'
    
    if filters:
        xml_body += '   <filter op="AND">\n'  # Using AND for multiple filters
        for filter_def in filters:
            xml_body += ' <fieldValue>\n'
            xml_body += f'    <fieldId>{filter_def["fieldId"]}</fieldId>\n'
            xml_body += f'    <operator>{filter_def["operator"]}</operator>\n'
            xml_body += f'    <value>{filter_def["value"]}</value>\n'
            xml_body += ' </fieldValue>\n'
        xml_body += '   </filter>\n'
    
    xml_body += '</RecordQueryRequest>'
    
    # Generate curl command
    curl_cmd = f"""curl --location 'https://c01-aus-local.hub.boomi.com/mdm/universes/{universe_id}/records/query?repositoryId={repository_id}' \\
--header 'Content-Type: application/xml' \\
--header 'Authorization: Basic [YOUR_DATAHUB_CREDENTIALS]' \\
--data '{xml_body}'"""
    
    return curl_cmd

if __name__ == "__main__":
    print("🚀 Starting Enhanced Boomi DataHub MCP Server")
    print("=" * 60)
    print("Enhanced with field mapping and dual credential support")
    print("=" * 60)
    print()
    print("Available MCP Resources:")
    print("  • boomi://datahub/models/all - All models (published + draft)")
    print("  • boomi://datahub/models/published - Published models only")
    print("  • boomi://datahub/models/draft - Draft models only") 
    print("  • boomi://datahub/model/{model_id} - Specific model details")
    print("  • boomi://datahub/connection/test - Connection health check")
    print()
    print("Available MCP Tools:")
    print("  • search_models_by_name - Search models by name pattern")
    print("  • get_model_statistics - Get comprehensive model statistics")
    print("  • query_records - Execute parameterised record queries with field mapping")
    print("  • get_model_fields - Get detailed field information with display/query mapping")
    print()
    print("Enhanced Features:")
    print("  🔹 Automatic field name conversion (ad_id → AD_ID)")
    print("  🔹 Dual credential support (API vs DataHub credentials)")
    print("  🔹 Enhanced error handling and troubleshooting")
    print("  🔹 Field validation and mapping")
    print("  🔹 Case-insensitive field matching")
    print()
    print("Server will be available at: http://127.0.0.1:8001/mcp")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Run with Streamable HTTP transport
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
        path="/mcp",
        log_level="info"
    )