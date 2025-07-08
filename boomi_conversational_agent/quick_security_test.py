"""
Quick test to verify Phase 6B security features are working
"""
import requests
import time

SERVER_URL = "http://localhost:8001"

def test_security_headers():
    """Test security headers"""
    print("🧪 Testing Security Headers...")
    
    # Test on a non-skipped endpoint
    test_endpoints = ["/health", "/docs", "/oauth/register"]
    
    for endpoint in test_endpoints:
        print(f"\n   Testing {endpoint}:")
        try:
            if endpoint == "/oauth/register":
                # POST request for register endpoint
                response = requests.post(f"{SERVER_URL}{endpoint}", json={
                    "redirect_uris": ["http://test.com"],
                    "client_name": "Test"
                })
            else:
                response = requests.get(f"{SERVER_URL}{endpoint}")
            
            expected_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Strict-Transport-Security"
            ]
            
            headers_present = 0
            for header in expected_headers:
                present = header in response.headers
                if present:
                    headers_present += 1
                print(f"      {header}: {'✅' if present else '❌'}")
            
            if headers_present > 0:
                print(f"   ✅ Found {headers_present}/{len(expected_headers)} security headers on {endpoint}")
                break
        except Exception as e:
            print(f"      Error testing {endpoint}: {e}")
    else:
        print("   ❌ No security headers found on any endpoint")

def test_rate_limiting():
    """Test rate limiting"""
    print("\n🧪 Testing Rate Limiting...")
    
    # Test on OAuth register endpoint which should have strict limits
    rate_limited = False
    rate_headers_found = False
    
    for i in range(30):
        try:
            response = requests.post(f"{SERVER_URL}/oauth/register", json={
                "redirect_uris": ["http://test.com"],
                "client_name": f"Test Client {i}"
            })
            
            # Check for rate limit headers
            if any("ratelimit" in header.lower() or "x-ratelimit" in header.lower() for header in response.headers):
                rate_headers_found = True
                print(f"   ✅ Rate limit headers found after {i+1} requests")
            
            if response.status_code == 429:
                rate_limited = True
                print(f"   ✅ Rate limited after {i+1} requests")
                break
                
        except Exception as e:
            print(f"   Error on request {i+1}: {e}")
        
        time.sleep(0.02)  # Very small delay
    
    if rate_limited:
        print("   ✅ Rate limiting is working")
    elif rate_headers_found:
        print("   ✅ Rate limiting headers detected")
    else:
        print("   ❌ No rate limiting detected")

def test_jailbreak_detection():
    """Test jailbreak detection"""
    print("\n🧪 Testing Jailbreak Detection...")
    
    # Test multiple endpoints with malicious patterns
    test_cases = [
        {
            "name": "Query Parameter Attack",
            "url": f"{SERVER_URL}/oauth/register?ignore_previous_instructions=true",
            "method": "POST",
            "json": {"redirect_uris": ["http://test.com"], "client_name": "Test"}
        },
        {
            "name": "URL Path Attack", 
            "url": f"{SERVER_URL}/health?ignore_all_rules=true",
            "method": "GET"
        },
        {
            "name": "Header Attack",
            "url": f"{SERVER_URL}/health",
            "method": "GET",
            "headers": {"X-Custom": "ignore previous instructions"}
        }
    ]
    
    blocked_count = 0
    for test_case in test_cases:
        try:
            kwargs = {"timeout": 5}
            if test_case.get("json"):
                kwargs["json"] = test_case["json"]
            if test_case.get("headers"):
                kwargs["headers"] = test_case["headers"]
                
            if test_case["method"] == "POST":
                response = requests.post(test_case["url"], **kwargs)
            else:
                response = requests.get(test_case["url"], **kwargs)
            
            if response.status_code == 403:
                print(f"   ✅ {test_case['name']}: Blocked (403)")
                blocked_count += 1
            else:
                print(f"   ❌ {test_case['name']}: Not blocked ({response.status_code})")
                
        except Exception as e:
            print(f"   ⚠️  {test_case['name']}: Error - {e}")
    
    if blocked_count > 0:
        print(f"   ✅ Jailbreak detection working ({blocked_count}/{len(test_cases)} blocked)")
    else:
        print("   ❌ Jailbreak detection not working")

def main():
    """Run quick security tests"""
    print("🚀 Quick Phase 6B Security Test")
    print("=" * 40)
    
    try:
        test_security_headers()
        test_rate_limiting()
        test_jailbreak_detection()
        
        print("\n📋 Summary:")
        print("If you see ✅ marks above, the security features are working!")
        print("If you see ❌ marks, restart the secure server:")
        print("   python run_secure_server.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the secure server is running: python run_secure_server.py")

if __name__ == "__main__":
    main()