#!/usr/bin/env python3
"""
Test script to understand FastMCP endpoint structure
"""
import asyncio
import json
import requests
from datetime import datetime

def test_fastmcp_endpoint_structure():
    """Test FastMCP endpoint structure with different URL patterns"""
    
    # Test server URL
    base_url = "http://127.0.0.1:8001"
    
    # Different endpoint patterns to test
    test_endpoints = [
        # Standard MCP endpoint
        f"{base_url}/mcp",
        
        # Resource endpoints as they appear in the MCP client
        f"{base_url}/resources/boomi://datahub/models/all",
        f"{base_url}/resources/boomi://datahub/connection/test",
        
        # Direct resource URIs
        f"{base_url}/boomi://datahub/models/all",
        f"{base_url}/boomi://datahub/connection/test",
        
        # Alternative patterns
        f"{base_url}/resource/boomi://datahub/models/all",
        f"{base_url}/api/resources/boomi://datahub/models/all",
        
        # Root path
        f"{base_url}/",
        
        # Health check
        f"{base_url}/health",
        f"{base_url}/status"
    ]
    
    print("=" * 80)
    print("🔍 FastMCP Endpoint Structure Test")
    print("=" * 80)
    print(f"Testing server: {base_url}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    results = []
    
    for endpoint in test_endpoints:
        print(f"Testing: {endpoint}")
        
        try:
            # Test GET request
            response = requests.get(endpoint, timeout=5)
            result = {
                "endpoint": endpoint,
                "method": "GET",
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "success": response.status_code < 400
            }
            
            # Try to parse response content
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    result["content"] = response.json()
                else:
                    result["content"] = response.text[:500]  # First 500 chars
            except Exception as e:
                result["content"] = f"Content parse error: {str(e)}"
            
            results.append(result)
            
            if result["success"]:
                print(f"  ✅ Success: {response.status_code}")
            else:
                print(f"  ❌ Failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            result = {
                "endpoint": endpoint,
                "method": "GET",
                "error": str(e),
                "success": False
            }
            results.append(result)
            print(f"  ❌ Connection error: {str(e)}")
        
        print()
    
    # Summary
    print("=" * 80)
    print("📊 Test Results Summary")
    print("=" * 80)
    
    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]
    
    print(f"Total endpoints tested: {len(results)}")
    print(f"Successful responses: {len(successful)}")
    print(f"Failed responses: {len(failed)}")
    print()
    
    if successful:
        print("✅ Working endpoints:")
        for result in successful:
            print(f"  • {result['endpoint']} ({result['status_code']})")
        print()
    
    if failed:
        print("❌ Failed endpoints:")
        for result in failed:
            if "error" in result:
                print(f"  • {result['endpoint']} - {result['error']}")
            else:
                print(f"  • {result['endpoint']} - HTTP {result['status_code']}")
        print()
    
    # Detailed analysis of successful responses
    if successful:
        print("🔍 Detailed Analysis of Successful Responses:")
        print("-" * 50)
        
        for result in successful:
            print(f"\nEndpoint: {result['endpoint']}")
            print(f"Status: {result['status_code']}")
            print(f"Content-Type: {result.get('headers', {}).get('content-type', 'N/A')}")
            
            if isinstance(result.get('content'), dict):
                print("Content (JSON):")
                print(json.dumps(result['content'], indent=2)[:1000])
            elif isinstance(result.get('content'), str):
                print("Content (Text):")
                print(result['content'][:500])
            print("-" * 30)
    
    return results

def test_mcp_post_requests():
    """Test MCP POST requests with proper MCP protocol"""
    
    base_url = "http://127.0.0.1:8001"
    mcp_endpoint = f"{base_url}/mcp"
    
    print("=" * 80)
    print("🔍 MCP Protocol POST Request Test")
    print("=" * 80)
    
    # Test MCP resource read request
    mcp_resource_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "resources/read",
        "params": {
            "uri": "boomi://datahub/models/all"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "MCP-Protocol-Version": "2025-06-18"
    }
    
    try:
        print(f"Testing MCP resource read: {mcp_endpoint}")
        print(f"Request: {json.dumps(mcp_resource_request, indent=2)}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        
        response = requests.post(
            mcp_endpoint,
            json=mcp_resource_request,
            headers=headers,
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"Response Content:")
                print(json.dumps(result, indent=2)[:2000])
            except:
                print(f"Response Text: {response.text[:1000]}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ MCP POST request failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting FastMCP Endpoint Structure Tests")
    print("Make sure the FastMCP server is running on http://127.0.0.1:8001")
    print()
    
    # Test basic endpoint structure
    endpoint_results = test_fastmcp_endpoint_structure()
    
    print("\n" + "=" * 80)
    
    # Test MCP protocol requests
    test_mcp_post_requests()
    
    print("\n" + "=" * 80)
    print("🎯 Analysis Complete")
    print("=" * 80)
    
    # Provide recommendations
    print("\n💡 FastMCP Endpoint Structure Insights:")
    print("1. FastMCP uses the MCP protocol over HTTP")
    print("2. The main endpoint is typically /mcp (not /resources/...)")
    print("3. Resources are accessed via MCP JSON-RPC protocol")
    print("4. Resource URIs like 'boomi://datahub/models/all' are sent as parameters")
    print("5. The client should POST to /mcp with proper MCP protocol messages")
    print()
    print("🔧 Troubleshooting:")
    print("- Check if server is running on the expected port")
    print("- Verify MCP protocol version compatibility")
    print("- Ensure proper JSON-RPC request format")
    print("- Check authentication headers if required")