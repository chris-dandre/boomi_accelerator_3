# boomi_datahub_mcp_server.py
"""
Boomi DataHub MCP Server

This MCP (Model Context Protocol) server exposes Boomi DataHub functionality through
standardized MCP resources. It allows AI agents and other MCP clients to:

1. Discover and retrieve Boomi DataHub models across all repositories
2. Access detailed model information including fields, sources, and match rules
3. Filter models by publication status (published/draft)
4. Get model schemas and field definitions

The server acts as a bridge between AI agents and Boomi DataHub APIs, enabling
intelligent data model discovery, analysis, and integration planning.

Use Cases for AI Agents:
- Data governance and catalog management
- Integration planning and mapping
- Model comparison and analysis
- Schema discovery for data transformations
- Compliance and documentation generation
"""

from fastmcp import FastMCP
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add the boomi_datahub_apis directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'boomi_datahub_apis'))

try:
    from boomi_datahub_client import BoomiDataHubClient, BoomiCredentials
except ImportError as e:
    print(f"Error importing BoomiDataHubClient: {e}")
    print("Make sure boomi_datahub_client.py is in the ../boomi_datahub_apis directory")
    sys.exit(1)

# Create the MCP server
mcp = FastMCP("Boomi DataHub MCP Server")

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

# MCP Resources

@mcp.resource("boomi://datahub/models/all")
def get_all_models() -> str:
    """
    Retrieve all Boomi DataHub models from all repositories (both published and draft)
    
    This resource provides comprehensive access to all data models in your Boomi DataHub
    environment. It includes both published (production-ready) and draft (in-development)
    models, giving AI agents complete visibility into your data landscape.
    
    The response includes:
    - Model names and unique identifiers
    - Publication status (published/draft)
    - Latest version information
    - Basic model metadata
    
    Use this resource when you need:
    - Complete data model inventory
    - Cross-repository model discovery
    - Data governance assessments
    - Integration planning and impact analysis
    """
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
    """
    Retrieve all published Boomi DataHub models from all repositories
    
    This resource focuses specifically on production-ready, published data models.
    Published models represent stable, approved data structures that are actively
    used in production integrations and business processes.
    
    The response includes:
    - Production-ready model definitions
    - Current version information
    - Field structures and data types
    - Model relationships and dependencies
    
    Use this resource when you need:
    - Production data model catalog
    - Integration endpoint discovery
    - Data mapping and transformation planning
    - API documentation generation
    - Compliance and audit reporting
    """
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
    """
    Retrieve all draft Boomi DataHub models from all repositories
    
    This resource provides access to in-development, unpublished data models.
    Draft models represent work-in-progress data structures that are being
    developed, tested, or refined before publication.
    
    The response includes:
    - Models under development
    - Experimental or test model structures
    - Version information for drafts
    - Development status indicators
    
    Use this resource when you need:
    - Development pipeline visibility
    - Model change impact analysis
    - Quality assurance and testing support
    - Development workflow optimization
    - Future state planning and roadmapping
    """
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
    """
    Retrieve detailed information for a specific Boomi DataHub model
    
    This resource provides comprehensive details about a single data model,
    including its complete field definitions, data sources, match rules,
    and structural metadata.
    
    The response includes:
    - Complete field definitions with data types
    - Source system configurations
    - Match and merge rules
    - Record title configurations
    - Model versioning information
    - Relationship mappings
    
    Use this resource when you need:
    - Detailed model schema analysis
    - Field-level data mapping
    - Integration specification development
    - Data validation rule definition
    - Model-specific documentation generation
    
    Parameters:
    - model_id: The unique identifier of the model to retrieve
    """
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
            # Enhance the model details with additional context
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
    """
    Test the connection to Boomi DataHub APIs
    
    This resource provides connection health and configuration validation
    for the Boomi DataHub integration. It verifies authentication,
    network connectivity, and API availability.
    
    The response includes:
    - Connection status (success/failure)
    - Authentication validation
    - API endpoint accessibility
    - Account configuration verification
    - Network connectivity metrics
    
    Use this resource when you need:
    - Connection troubleshooting
    - System health monitoring
    - Configuration validation
    - Integration testing support
    - Connectivity diagnostics
    """
    try:
        client = get_boomi_client()
        test_result = client.test_connection()
        
        result = {
            "status": "connection_test",
            "timestamp": datetime.now().isoformat(),
            "connection_result": test_result,
            "recommendations": []
        }
        
        # Add recommendations based on test results
        if test_result['success']:
            result["recommendations"].append("Connection is healthy and ready for use")
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

# MCP Tools

@mcp.tool()
def search_models_by_name(name_pattern: str) -> dict:
    """
    Search for Boomi DataHub models by name pattern
    
    This tool enables intelligent model discovery based on naming patterns,
    supporting substring matching and case-insensitive searches.
    
    Args:
        name_pattern: The name pattern to search for (case-insensitive substring match)
        
    Returns:
        Dictionary containing matching models and search metadata
    """
    try:
        client = get_boomi_client()
        all_models_data = client.get_all_models()
        
        # Combine all models for searching
        all_models = all_models_data['published'] + all_models_data['draft']
        
        # Search for models matching the name pattern
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
    """
    Get comprehensive statistics about Boomi DataHub models
    
    This tool provides analytical insights into your data model landscape,
    including distribution, usage patterns, and structural analysis.
    
    Returns:
        Dictionary containing detailed model statistics and insights
    """
    try:
        client = get_boomi_client()
        all_models_data = client.get_all_models()
        
        published_models = all_models_data['published']
        draft_models = all_models_data['draft']
        all_models = published_models + draft_models
        
        # Calculate statistics
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
        
        # Analyze field statistics
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
        
        # Finalize field analysis
        stats["field_analysis"]["models_with_fields"] = len(models_with_fields)
        if models_with_fields:
            stats["field_analysis"]["avg_fields_per_model"] = round(
                stats["field_analysis"]["total_fields"] / len(models_with_fields), 1
            )
        else:
            stats["field_analysis"]["min_fields"] = 0
        
        # Finalize source analysis
        if stats["source_analysis"]["models_with_sources"] > 0:
            stats["source_analysis"]["avg_sources_per_model"] = round(
                stats["source_analysis"]["total_sources"] / stats["source_analysis"]["models_with_sources"], 1
            )
        
        # Convert set to list for JSON serialization
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

if __name__ == "__main__":
    print("🚀 Starting Boomi DataHub MCP Server")
    print("=" * 60)
    print("This server exposes Boomi DataHub functionality through MCP resources.")
    print("AI agents can use these resources to discover and analyze data models.")
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