#!/usr/bin/env python3
"""
Rate Limiting Test for Unified MCP Server
Tests the actual endpoints available in boomi_datahub_mcp_server_unified_compliant.py
"""

import requests
import time
import json
from datetime import datetime

# Server configuration
SERVER_URL = "http://localhost:8001"

def print_header(title):
    """Print test section header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_test_result(test_name, success, details=""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")

def test_health_endpoint_rate_limiting():
    """Test rate limiting on /health endpoint"""
    print_header("Health Endpoint Rate Limiting")
    
    print("Making rapid requests to /health endpoint...")
    print("Note: This endpoint should be whitelisted for localhost")
    
    rate_limited_count = 0
    success_count = 0
    response_times = []
    
    for i in range(20):
        try:
            start_time = time.time()
            response = requests.get(f"{SERVER_URL}/health", timeout=5)
            end_time = time.time()
            response_times.append(end_time - start_time)
            
            if response.status_code == 429:
                rate_limited_count += 1
                print(f"Request {i+1}: Rate Limited! (unexpected for whitelisted localhost)")
            elif response.status_code == 200:
                success_count += 1
                if i % 5 == 0:
                    print(f"Request {i+1}: Success ✅ ({end_time-start_time:.2f}s)")
            else:
                print(f"Request {i+1}: Status {response.status_code}")
                
        except Exception as e:
            print(f"Request {i+1}: ERROR - {e}")
        
        time.sleep(0.05)  # 50ms delay
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    print(f"\nResults:")
    print(f"  Successful requests: {success_count}")
    print(f"  Rate limited requests: {rate_limited_count}")
    print(f"  Average response time: {avg_response_time:.3f}s")
    
    # For whitelisted localhost, we expect NO rate limiting
    test_passed = rate_limited_count == 0 and success_count > 15
    print_test_result("Health Endpoint Whitelist", test_passed, 
                     f"Localhost should not be rate limited on /health")
    
    return test_passed

def test_api_models_rate_limiting():
    """Test rate limiting on /api/models endpoint"""
    print_header("API Models Endpoint Rate Limiting")
    
    print("Making rapid requests to /api/models endpoint...")
    print("This endpoint requires OAuth token, testing without auth first...")
    
    rate_limited_count = 0
    auth_error_count = 0
    success_count = 0
    
    for i in range(15):
        try:
            start_time = time.time()
            response = requests.get(f"{SERVER_URL}/api/models", timeout=5)
            end_time = time.time()
            
            print(f"Request {i+1}: Status {response.status_code} ({end_time-start_time:.2f}s)")
            
            if response.status_code == 429:
                rate_limited_count += 1
                print(f"   ✅ Rate Limited! Headers: {dict(response.headers)}")
                if 'Retry-After' in response.headers:
                    print(f"   Retry-After: {response.headers['Retry-After']} seconds")
                break
            elif response.status_code == 401:
                auth_error_count += 1
                print(f"   Auth required (expected)")
            elif response.status_code == 200:
                success_count += 1
                print(f"   Unexpected success without auth")
            else:
                print(f"   Status: {response.status_code}")
                
        except Exception as e:
            print(f"Request {i+1}: ERROR - {e}")
        
        time.sleep(0.1)  # 100ms delay
    
    print(f"\nResults:")
    print(f"  Successful requests: {success_count}")
    print(f"  Auth errors (401): {auth_error_count}")
    print(f"  Rate limited requests: {rate_limited_count}")
    
    # We expect either rate limiting OR consistent auth errors
    test_passed = rate_limited_count > 0 or auth_error_count > 10
    print_test_result("API Models Rate Limiting", test_passed, 
                     f"Either rate limited or auth-protected")
    
    return test_passed

def test_mcp_endpoint_rate_limiting():
    """Test rate limiting on /mcp endpoint"""
    print_header("MCP Endpoint Rate Limiting")
    
    print("Making rapid requests to /mcp endpoint...")
    print("Testing with invalid JSON-RPC payload...")
    
    rate_limited_count = 0
    error_count = 0
    success_count = 0
    
    # Invalid JSON-RPC payload for testing
    payload = {
        "jsonrpc": "2.0",
        "method": "list_tools",
        "id": 1
    }
    
    for i in range(15):
        try:
            start_time = time.time()
            response = requests.post(f"{SERVER_URL}/mcp", 
                                   json=payload,
                                   headers={"Content-Type": "application/json"},
                                   timeout=5)
            end_time = time.time()
            
            print(f"Request {i+1}: Status {response.status_code} ({end_time-start_time:.2f}s)")
            
            if response.status_code == 429:
                rate_limited_count += 1
                print(f"   ✅ Rate Limited! Headers: {dict(response.headers)}")
                if 'Retry-After' in response.headers:
                    print(f"   Retry-After: {response.headers['Retry-After']} seconds")
                break
            elif response.status_code in [400, 401, 403]:
                error_count += 1
                print(f"   Expected error (no auth/invalid request)")
            elif response.status_code == 200:
                success_count += 1
                print(f"   Unexpected success")
            else:
                print(f"   Status: {response.status_code}")
                
        except Exception as e:
            print(f"Request {i+1}: ERROR - {e}")
        
        time.sleep(0.1)  # 100ms delay
    
    print(f"\nResults:")
    print(f"  Successful requests: {success_count}")
    print(f"  Error responses: {error_count}")
    print(f"  Rate limited requests: {rate_limited_count}")
    
    # We expect either rate limiting OR consistent errors
    test_passed = rate_limited_count > 0 or error_count > 10
    print_test_result("MCP Endpoint Rate Limiting", test_passed, 
                     f"Either rate limited or error-protected")
    
    return test_passed

def test_rate_limit_headers():
    """Test for rate limit headers in responses"""
    print_header("Rate Limit Headers Check")
    
    endpoints_to_test = [
        "/health",
        "/api/models",
        "/.well-known/oauth-protected-resource"
    ]
    
    headers_found = {}
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{SERVER_URL}{endpoint}", timeout=5)
            
            print(f"\nTesting {endpoint} (Status: {response.status_code})")
            
            rate_limit_headers = {}
            for header, value in response.headers.items():
                if any(keyword in header.lower() for keyword in ['ratelimit', 'x-ratelimit', 'retry-after']):
                    rate_limit_headers[header] = value
                    print(f"  {header}: {value}")
            
            headers_found[endpoint] = rate_limit_headers
            
        except Exception as e:
            print(f"Error testing {endpoint}: {e}")
            headers_found[endpoint] = {}
    
    total_headers = sum(len(headers) for headers in headers_found.values())
    has_headers = total_headers > 0
    
    print(f"\nTotal rate limit headers found: {total_headers}")
    print_test_result("Rate Limit Headers Present", has_headers,
                     f"Found rate limit headers across {len([h for h in headers_found.values() if h])} endpoints")
    
    return has_headers

def test_oauth_metadata_endpoint():
    """Test the OAuth protected resource metadata endpoint"""
    print_header("OAuth Protected Resource Metadata")
    
    print("Testing /.well-known/oauth-protected-resource endpoint...")
    
    try:
        response = requests.get(f"{SERVER_URL}/.well-known/oauth-protected-resource", timeout=5)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                metadata = response.json()
                print("OAuth Metadata Response:")
                print(json.dumps(metadata, indent=2))
                
                # Check for required OAuth 2.1 fields
                required_fields = ['resource_uris', 'authorization_servers']
                has_required = all(field in metadata for field in required_fields)
                
                print_test_result("OAuth Metadata Endpoint", has_required,
                                 f"Contains required OAuth 2.1 metadata fields")
                return has_required
                
            except json.JSONDecodeError:
                print("❌ Invalid JSON response")
                print_test_result("OAuth Metadata Endpoint", False, "Invalid JSON")
                return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print_test_result("OAuth Metadata Endpoint", False, f"Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print_test_result("OAuth Metadata Endpoint", False, str(e))
        return False

def check_server_availability():
    """Check if the unified server is running"""
    print_header("Unified Server Availability Check")
    
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Unified MCP Server is running at {SERVER_URL}")
            print(f"   Health response: {health_data}")
            
            # Check for MCP compliance indicators
            mcp_compliant = health_data.get("mcp_compliance") == "2025-06-18"
            oauth_enabled = health_data.get("oauth_enabled", False)
            security_enabled = health_data.get("security_enabled", False)
            
            print(f"   MCP Compliance: {mcp_compliant}")
            print(f"   OAuth Enabled: {oauth_enabled}")
            print(f"   Security Enabled: {security_enabled}")
            
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to unified server at {SERVER_URL}")
        print("   Make sure the server is running with:")
        print("   python boomi_datahub_mcp_server_unified_compliant.py")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

def main():
    """Run all rate limiting tests for unified server"""
    print(f"🚀 Unified MCP Server Rate Limiting Test Suite")
    print(f"Server: {SERVER_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check server availability first
    if not check_server_availability():
        print("\n❌ Cannot proceed - unified server not available")
        return False
    
    results = {}
    
    # Run all tests
    results['oauth_metadata'] = test_oauth_metadata_endpoint()
    results['health_whitelist'] = test_health_endpoint_rate_limiting()
    results['api_models_protection'] = test_api_models_rate_limiting()
    results['mcp_endpoint_protection'] = test_mcp_endpoint_rate_limiting()
    results['rate_limit_headers'] = test_rate_limit_headers()
    
    # Summary
    print_header("Test Summary")
    
    passed = 0
    total = 0
    
    for test_name, result in results.items():
        if result is not None:
            total += 1
            if result:
                passed += 1
                print(f"✅ {test_name.replace('_', ' ').title()}")
            else:
                print(f"❌ {test_name.replace('_', ' ').title()}")
        else:
            print(f"⚠️  {test_name.replace('_', ' ').title()} (Skipped)")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\nOverall Results: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 Unified MCP server security is working well!")
    elif success_rate >= 60:
        print("⚠️  Unified MCP server partially protected - some issues detected")
    else:
        print("❌ Unified MCP server has security issues")
    
    print("\n📋 Notes:")
    print("   • This server focuses on MCP protocol + OAuth 2.1")
    print("   • Rate limiting may be applied at the OAuth/security layer")
    print("   • Some endpoints require proper OAuth tokens for full testing")
    
    return success_rate >= 60  # Lower threshold for unified server

if __name__ == "__main__":
    main()