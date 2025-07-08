#!/usr/bin/env python3
"""
Manual Rate Limiting Test Script
Test the rate limiting functionality by making rapid requests to various endpoints
"""

import requests
import time
import json
from datetime import datetime

# Server configuration
SERVER_URL = "http://localhost:8001"
MCP_BASE_URL = f"{SERVER_URL}/mcp"

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

def test_rate_limit_endpoint():
    """Test the dedicated rate limit test endpoint"""
    print_header("Rate Limit Test Endpoint (/test/rate-limit)")
    
    # This endpoint has very strict limits: 3/min, burst=1
    print("Making rapid requests to /test/rate-limit endpoint...")
    print("Expected: First request OK, subsequent requests rate limited")
    
    rate_limited_count = 0
    success_count = 0
    
    for i in range(8):
        try:
            start_time = time.time()
            response = requests.get(f"{SERVER_URL}/test/rate-limit", timeout=5)
            end_time = time.time()
            
            print(f"Request {i+1}: Status {response.status_code} ({end_time-start_time:.2f}s)")
            
            if response.status_code == 429:
                rate_limited_count += 1
                print(f"   Rate Limited! Headers: {dict(response.headers)}")
                if 'Retry-After' in response.headers:
                    print(f"   Retry-After: {response.headers['Retry-After']} seconds")
            elif response.status_code == 200:
                success_count += 1
                print(f"   Success! Response: {response.text[:100]}")
            else:
                print(f"   Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"Request {i+1}: ERROR - {e}")
        
        # Small delay to avoid overwhelming
        time.sleep(0.1)
    
    print(f"\nResults:")
    print(f"  Successful requests: {success_count}")
    print(f"  Rate limited requests: {rate_limited_count}")
    
    test_passed = rate_limited_count > 0
    print_test_result("Rate Limiting Active", test_passed, 
                     f"{rate_limited_count}/{8} requests were rate limited")
    
    return test_passed

def test_oauth_endpoints():
    """Test rate limiting on OAuth endpoints"""
    print_header("OAuth Endpoints Rate Limiting")
    
    # Test /oauth/register endpoint (5/min limit)
    print("Testing /oauth/register endpoint (5 requests/minute limit)...")
    
    rate_limited = False
    for i in range(8):
        try:
            response = requests.post(f"{SERVER_URL}/oauth/register", 
                                   json={
                                       "redirect_uris": [f"http://test{i}.com"],
                                       "client_name": f"Test Client {i}"
                                   }, timeout=5)
            
            print(f"Request {i+1}: Status {response.status_code}")
            
            if response.status_code == 429:
                rate_limited = True
                print(f"   ✅ Rate limited after {i+1} requests")
                break
            elif response.status_code in [200, 201]:
                print(f"   ✅ Request successful")
            else:
                print(f"   Status {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"Request {i+1}: ERROR - {e}")
        
        time.sleep(0.2)  # 200ms delay
    
    print_test_result("OAuth Rate Limiting", rate_limited, 
                     "Rate limiting triggered on OAuth endpoints")
    
    return rate_limited

def test_mcp_endpoints():
    """Test rate limiting on MCP endpoints"""
    print_header("MCP Endpoints Rate Limiting")
    
    # First try to get an access token (skip if fails)
    print("Attempting to test MCP endpoints (requires OAuth token)...")
    
    try:
        # Try to use any existing test client credentials
        auth_response = requests.post(f"{SERVER_URL}/oauth/token", 
                                    data={
                                        "grant_type": "client_credentials",
                                        "client_id": "test_client",
                                        "client_secret": "test_secret"
                                    })
        
        if auth_response.status_code == 200:
            token_data = auth_response.json()
            access_token = token_data.get("access_token")
            
            if access_token:
                print("✅ Got access token, testing MCP endpoints...")
                
                headers = {"Authorization": f"Bearer {access_token}"}
                rate_limited = False
                
                # Test with high frequency
                for i in range(15):
                    response = requests.post(f"{MCP_BASE_URL}/list_tools", 
                                           headers=headers, 
                                           json={}, timeout=5)
                    
                    print(f"MCP Request {i+1}: Status {response.status_code}")
                    
                    if response.status_code == 429:
                        rate_limited = True
                        print(f"   ✅ MCP rate limited after {i+1} requests")
                        break
                    
                    time.sleep(0.1)
                
                print_test_result("MCP Rate Limiting", rate_limited,
                                 "Rate limiting on authenticated MCP endpoints")
                return rate_limited
            
    except Exception as e:
        print(f"❌ Could not test MCP endpoints: {e}")
    
    print("⚠️  Skipping MCP rate limiting test (no valid OAuth token)")
    return None

def test_rate_limit_headers():
    """Test for proper rate limit headers"""
    print_header("Rate Limit Headers")
    
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        
        print(f"Health endpoint status: {response.status_code}")
        print("Response headers:")
        
        rate_limit_headers = {}
        for header, value in response.headers.items():
            if 'ratelimit' in header.lower() or 'x-ratelimit' in header.lower():
                rate_limit_headers[header] = value
                print(f"  {header}: {value}")
        
        has_headers = len(rate_limit_headers) > 0
        print_test_result("Rate Limit Headers", has_headers,
                         f"Found {len(rate_limit_headers)} rate limit headers")
        
        return has_headers
        
    except Exception as e:
        print(f"❌ Error testing headers: {e}")
        return False

def test_whitelist_behavior():
    """Test that localhost is whitelisted properly"""
    print_header("Whitelist Behavior")
    
    print("Testing that localhost/127.0.0.1 is whitelisted...")
    print("Making many requests to /health endpoint (should be whitelisted)...")
    
    all_success = True
    for i in range(20):
        try:
            response = requests.get(f"{SERVER_URL}/health", timeout=5)
            if response.status_code != 200:
                all_success = False
                print(f"Request {i+1}: Status {response.status_code} (unexpected)")
            elif i % 5 == 0:
                print(f"Request {i+1}: Status {response.status_code} ✅")
        except Exception as e:
            all_success = False
            print(f"Request {i+1}: ERROR - {e}")
        
        time.sleep(0.05)  # 50ms delay
    
    print_test_result("Whitelist Protection", all_success,
                     "Localhost requests not rate limited on normal endpoints")
    
    return all_success

def check_server_availability():
    """Check if the server is running"""
    print_header("Server Availability Check")
    
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Server is running at {SERVER_URL}")
            print(f"   Health check response: {response.text}")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {SERVER_URL}")
        print("   Make sure the server is running with:")
        print("   python run_secure_server.py")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

def main():
    """Run all rate limiting tests"""
    print(f"🚀 Rate Limiting Test Suite")
    print(f"Server: {SERVER_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check server availability first
    if not check_server_availability():
        print("\n❌ Cannot proceed - server not available")
        return False
    
    results = {}
    
    # Run all tests
    results['rate_limit_endpoint'] = test_rate_limit_endpoint()
    results['oauth_endpoints'] = test_oauth_endpoints()
    results['mcp_endpoints'] = test_mcp_endpoints()
    results['rate_limit_headers'] = test_rate_limit_headers()
    results['whitelist_behavior'] = test_whitelist_behavior()
    
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
        print("🎉 Rate limiting is working well!")
    elif success_rate >= 60:
        print("⚠️  Rate limiting partially working - some issues detected")
    else:
        print("❌ Rate limiting has significant issues")
    
    return success_rate >= 80

if __name__ == "__main__":
    main()