# auth_debug.py
"""
Debug authentication issues with Boomi DataHub queries
"""

import os
import base64
import requests
from dotenv import load_dotenv

def debug_authentication():
    """Debug authentication step by step"""
    
    load_dotenv()
    
    print("🔍 Boomi DataHub Authentication Debug")
    print("=" * 50)
    
    # Get credentials
    username = os.getenv('BOOMI_USERNAME')
    password = os.getenv('BOOMI_PASSWORD')
    account_id = os.getenv('BOOMI_ACCOUNT_ID')
    base_url = os.getenv('BOOMI_BASE_URL', 'https://api.boomi.com')
    
    print(f"📋 Environment Variables:")
    print(f"   Username: {'✅ Set' if username else '❌ Missing'} ({username[:3]}*** if set)")
    print(f"   Password: {'✅ Set' if password else '❌ Missing'} ({'*' * len(password) if password else 'Not set'})")
    print(f"   Account ID: {'✅ Set' if account_id else '❌ Missing'} ({account_id})")
    print(f"   Base URL: {base_url}")
    
    if not all([username, password, account_id]):
        print("\n❌ Missing credentials!")
        return
    
    # Test both API endpoints
    print(f"\n🔍 Testing Different Endpoints:")
    
    # Create auth header
    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    print(f"   Auth header: Basic {auth_b64[:20]}...")
    
    # Test 1: Model API (should work)
    model_url = f"{base_url}/mdm/api/rest/v1/{account_id}/models"
    print(f"\n1. Testing Model API:")
    print(f"   URL: {model_url}")
    
    try:
        response = requests.get(
            model_url,
            headers={
                "Authorization": f"Basic {auth_b64}",
                "Accept": "application/json,application/xml"
            },
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Model API authentication works!")
        else:
            print(f"   ❌ Model API failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Model API error: {e}")
    
    # Test 2: DataHub Query API with DataHub credentials
    hub_base_url = base_url.replace('api.boomi.com', 'c01-aus-local.hub.boomi.com')
    query_url = f"{hub_base_url}/mdm/universes/02367877-e560-4d82-b640-6a9f7ab96afa/records/query"
    
    print(f"\n2. Testing DataHub Query API with DataHub credentials:")
    print(f"   URL: {query_url}")
    
    # Create DataHub auth header
    datahub_auth_string = f"{datahub_username}:{datahub_password}"
    datahub_auth_bytes = datahub_auth_string.encode('ascii')
    datahub_auth_b64 = base64.b64encode(datahub_auth_bytes).decode('ascii')
    
    print(f"   DataHub Auth header: Basic {datahub_auth_b64[:20]}...")
    
    # Simple test query
    test_xml = '''<RecordQueryRequest limit="1" offsetToken="">
   <view>
     <fieldId>AD_ID</fieldId>
   </view>
</RecordQueryRequest>'''
    
    try:
        response = requests.post(
            query_url,
            params={"repositoryId": "43212d46-1832-4ab1-820d-c0334d619f6f"},
            headers={
                "Content-Type": "application/xml",
                "Authorization": f"Basic {datahub_auth_b64}"
            },
            data=test_xml,
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   🎉 SUCCESS: DataHub Query API works with DataHub credentials!")
            print(f"   Response length: {len(response.text)} chars")
            
            # Try to parse the response to see how many records
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                records = root.findall(".//record") or root.findall(".//Record")
                print(f"   📊 Records found: {len(records)}")
            except:
                print(f"   📊 Response received (parsing details not available)")
                
        elif response.status_code == 401:
            print("   ❌ Still 401 UNAUTHORIZED with DataHub credentials")
            print("   🔍 Possible issues:")
            print("      • DataHub credentials are incorrect")
            print("      • Need different permissions for this universe/repository")
            print("      • Different authentication method required")
        else:
            print(f"   ⚠️  Different error: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            
    except Exception as e:
        print(f"   ❌ DataHub Query API error: {e}")
    
    # Test 3: Alternative authentication methods
    print(f"\n3. Testing Alternative Authentication:")
    
    # Try with different headers
    alt_headers = {
        "Content-Type": "application/xml",
        "Authorization": f"Basic {auth_b64}",
        "User-Agent": "BoomiDataHubClient/1.0",
        "Accept": "application/xml"
    }
    
    try:
        response = requests.post(
            query_url,
            params={"repositoryId": "43212d46-1832-4ab1-820d-c0334d619f6f"},
            headers=alt_headers,
            data=test_xml,
            timeout=10
        )
        print(f"   Alternative headers status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Alternative headers worked!")
        elif response.status_code != 401:
            print(f"   🔄 Different error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Alternative headers error: {e}")
    
    print(f"\n💡 Recommendations:")
    
    if response.status_code == 200:
        print("   🎉 SUCCESS: DataHub queries are working!")
        print("   ✅ Your setup is correct - you can now run parameterised queries")
        print("   🚀 Try: python boomi_datahub_mcp_client_v2.py")
    elif response.status_code == 401:
        print("   🔹 DataHub credentials still not working:")
        print("      • Double-check the DataHub username and password")
        print("      • Verify with your Boomi administrator that these are the correct DataHub credentials")
        print("      • Ensure you have permissions for the specific universe/repository")
        print("   🔧 Try running: python setup_datahub_credentials.py")
    else:
        print("   🔹 Different issue (not authentication):")
        print("      • Check universe ID and repository ID are correct")
        print("      • Verify the XML request format")
        print("      • Contact your Boomi administrator for troubleshooting")

if __name__ == "__main__":
    debug_authentication()