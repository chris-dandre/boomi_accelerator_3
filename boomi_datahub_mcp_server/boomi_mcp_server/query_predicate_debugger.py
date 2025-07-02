# query_predicate_debugger.py
"""
Debug the "invalid predicate" error step by step
"""

import asyncio
import json
from fastmcp import Client

async def debug_predicate_issue():
    """Debug the invalid predicate error step by step"""
    
    print("🔍 Query Predicate Debugger")
    print("=" * 50)
    print("Let's debug the 'invalid predicate' error step by step")
    
    # Use the MCP client directly instead of importing
    client = Client("http://127.0.0.1:8001/mcp")
    
    model_id = "02367877-e560-4d82-b640-6a9f7ab96afa"
    repo_id = "43212d46-1832-4ab1-820d-c0334d619f6f"
    
    print(f"\n🔍 Step 1: Test basic query without filters")
    print("=" * 40)
    
    try:
        async with client as session:
            # Test 1: Basic query without filters (should work)
            result = await session.call_tool("query_records", {
                "universe_id": model_id,
                "repository_id": repo_id,
                "fields": ["AD_ID", "ADVERTISER"],  # Just 2 fields to start
                "limit": 5
            })
            basic_result = json.loads(result[0].text)
            
            if basic_result.get("status") == "success":
                records = basic_result.get("data", {}).get("records", [])
                print(f"✅ Basic query works: {len(records)} records returned")
                
                if records:
                    print(f"\n📋 Sample data from ADVERTISER field:")
                    advertisers = set()
                    for i, record in enumerate(records, 1):
                        advertiser_value = record.get("ADVERTISER", "")
                        advertisers.add(advertiser_value)
                        print(f"   {i}. AD_ID: {record.get('AD_ID', 'N/A')}, ADVERTISER: '{advertiser_value}'")
                    
                    print(f"\n📊 Unique advertiser values found: {sorted(list(advertisers))}")
                    
                    # Check if 'Sony' exists
                    if "Sony" in advertisers:
                        print(f"✅ 'Sony' found in data - filter should work")
                    else:
                        print(f"❌ 'Sony' NOT found in data")
                        print(f"💡 Try one of these values instead: {list(advertisers)}")
                    
                    # Test with Sony filter
                    print(f"\n🔍 Step 2: Test Sony filter")
                    print("=" * 40)
                    
                    sony_result_tool = await session.call_tool("query_records", {
                        "universe_id": model_id,
                        "repository_id": repo_id,
                        "fields": ["AD_ID", "ADVERTISER"],
                        "filters": [
                            {
                                "fieldId": "ADVERTISER",
                                "operator": "EQUALS",
                                "value": "Sony"
                            }
                        ],
                        "limit": 5
                    })
                    sony_result = json.loads(sony_result_tool[0].text)
                    
                    if sony_result.get("status") == "success":
                        sony_records = sony_result.get("data", {}).get("records", [])
                        print(f"✅ Sony filter works: {len(sony_records)} records returned")
                        
                        if sony_records:
                            print(f"📋 Sony records:")
                            for i, record in enumerate(sony_records, 1):
                                print(f"   {i}. AD_ID: {record.get('AD_ID', 'N/A')}, ADVERTISER: '{record.get('ADVERTISER', 'N/A')}'")
                        else:
                            print(f"⚠️  Sony filter returned 0 records (filter works but no matches)")
                    else:
                        print(f"❌ Sony filter failed: {sony_result.get('error', 'Unknown error')}")
                        print(f"   Status code: {sony_result.get('status_code', 'N/A')}")
                        
                        # Show the curl equivalent to debug
                        if "curl_equivalent" in sony_result:
                            print(f"\n📋 Generated cURL command:")
                            curl_lines = sony_result["curl_equivalent"].split('\n')
                            for line in curl_lines[:5]:  # Show first 5 lines
                                print(f"   {line}")
                    
                    # Test with CONTAINS operator
                    print(f"\n🔍 Step 3: Test CONTAINS operator")
                    print("=" * 40)
                    
                    contains_result_tool = await session.call_tool("query_records", {
                        "universe_id": model_id,
                        "repository_id": repo_id,
                        "fields": ["AD_ID", "ADVERTISER"],
                        "filters": [
                            {
                                "fieldId": "ADVERTISER",
                                "operator": "CONTAINS",
                                "value": "Sony"
                            }
                        ],
                        "limit": 5
                    })
                    contains_result = json.loads(contains_result_tool[0].text)
                    
                    if contains_result.get("status") == "success":
                        contains_records = contains_result.get("data", {}).get("records", [])
                        print(f"✅ CONTAINS filter works: {len(contains_records)} records returned")
                    else:
                        print(f"❌ CONTAINS filter failed: {contains_result.get('error', 'Unknown error')}")
                    
                    # Test with existing value
                    if advertisers:
                        print(f"\n🔍 Step 4: Test filter with known value")
                        print("=" * 40)
                        
                        test_value = list(advertisers)[0]
                        print(f"Testing with value: '{test_value}'")
                        
                        known_result_tool = await session.call_tool("query_records", {
                            "universe_id": model_id,
                            "repository_id": repo_id,
                            "fields": ["AD_ID", "ADVERTISER"],
                            "filters": [
                                {
                                    "fieldId": "ADVERTISER",
                                    "operator": "EQUALS",
                                    "value": test_value
                                }
                            ],
                            "limit": 3
                        })
                        known_result = json.loads(known_result_tool[0].text)
                        
                        if known_result.get("status") == "success":
                            known_records = known_result.get("data", {}).get("records", [])
                            print(f"✅ Known value filter works: {len(known_records)} records returned")
                        else:
                            print(f"❌ Known value filter failed: {known_result.get('error', 'Unknown error')}")
                            
                            # Show the query parameters being used
                            if "query_parameters" in known_result:
                                params = known_result["query_parameters"]
                                print(f"\n🔍 Query parameters:")
                                print(f"   Fields: {params.get('fields', [])}")
                                print(f"   Filters: {params.get('filters', [])}")
                    
                else:
                    print(f"⚠️  No records returned from basic query")
            else:
                print(f"❌ Basic query failed: {basic_result.get('error', 'Unknown error')}")
                print(f"   This indicates a more fundamental issue")
                return
    
    except Exception as e:
        print(f"❌ Debug script failed: {e}")
        print(f"💡 Make sure the MCP server is running: python boomi_datahub_mcp_server_v2.py")
        return
    
    print(f"\n💡 Summary and Recommendations:")
    print("=" * 40)
    
    if records:
        print("✅ Basic queries work")
        available_values = sorted(list(advertisers))[:5]  # Show first 5
        
        if "Sony" in advertisers:
            print("✅ 'Sony' exists in the data")
            print("🔍 If Sony filter failed, try using 'CONTAINS' instead of 'EQUALS'")
        else:
            print("❌ 'Sony' does not exist in the data")
            print(f"💡 Try one of these values instead: {available_values}")
        
        print(f"\n🔧 Commands to try in Query Builder:")
        if available_values:
            suggested_value = available_values[0]
            print(f"   clear filters")
            print(f"   add filter ADVERTISER EQUALS {suggested_value}")
            print(f"   execute query")
    else:
        print("❌ No data available - check repository and connectivity")

if __name__ == "__main__":
    asyncio.run(debug_predicate_issue())

async def debug_predicate_issue():
    """Debug the invalid predicate error step by step"""
    
    print("🔍 Query Predicate Debugger")
    print("=" * 50)
    print("Let's debug the 'invalid predicate' error step by step")
    
    client = EnhancedBoomiDataHubMCPClient()
    
    model_id = "02367877-e560-4d82-b640-6a9f7ab96afa"
    repo_id = "43212d46-1832-4ab1-820d-c0334d619f6f"
    
    print(f"\n🔍 Step 1: Test basic query without filters")
    print("=" * 40)
    
    # Test 1: Basic query without filters (should work)
    basic_result = await client.query_records_advanced(
        universe_id=model_id,
        repository_id=repo_id,
        fields=["AD_ID", "ADVERTISER"],  # Just 2 fields to start
        limit=3
    )
    
    if basic_result.get("status") == "success":
        records = basic_result.get("data", {}).get("records", [])
        print(f"✅ Basic query works: {len(records)} records returned")
        
        if records:
            print(f"\n📋 Sample data from ADVERTISER field:")
            advertisers = set()
            for i, record in enumerate(records, 1):
                advertiser_value = record.get("ADVERTISER", "")
                advertisers.add(advertiser_value)
                print(f"   {i}. AD_ID: {record.get('AD_ID', 'N/A')}, ADVERTISER: '{advertiser_value}'")
            
            print(f"\n📊 Unique advertiser values found: {sorted(list(advertisers))}")
            
            # Check if 'Sony' exists
            if "Sony" in advertisers:
                print(f"✅ 'Sony' found in data - filter should work")
            else:
                print(f"❌ 'Sony' NOT found in data")
                print(f"💡 Try one of these values instead: {list(advertisers)}")
        else:
            print(f"⚠️  No records returned from basic query")
    else:
        print(f"❌ Basic query failed: {basic_result.get('error', 'Unknown error')}")
        print(f"   This indicates a more fundamental issue")
        return
    
    print(f"\n🔍 Step 2: Test query with simple filter")
    print("=" * 40)
    
    # Test 2: Query with a filter using a value we know exists
    if records and advertisers:
        # Use the first advertiser value we found
        test_advertiser = list(advertisers)[0]
        print(f"Testing filter with advertiser: '{test_advertiser}'")
        
        filtered_result = await client.query_records_advanced(
            universe_id=model_id,
            repository_id=repo_id,
            fields=["AD_ID", "ADVERTISER"],
            filters=[
                {
                    "fieldId": "ADVERTISER",
                    "operator": "EQUALS",
                    "value": test_advertiser
                }
            ],
            limit=3
        )
        
        if filtered_result.get("status") == "success":
            filtered_records = filtered_result.get("data", {}).get("records", [])
            print(f"✅ Filter query works: {len(filtered_records)} records returned")
            
            if filtered_records:
                print(f"📋 Filtered results:")
                for i, record in enumerate(filtered_records, 1):
                    print(f"   {i}. AD_ID: {record.get('AD_ID', 'N/A')}, ADVERTISER: '{record.get('ADVERTISER', 'N/A')}'")
        else:
            print(f"❌ Filter query failed: {filtered_result.get('error', 'Unknown error')}")
            
            # Show the curl equivalent to debug the XML
            if "curl_equivalent" in filtered_result:
                print(f"\n📋 Generated XML (from curl equivalent):")
                curl_cmd = filtered_result["curl_equivalent"]
                # Extract the XML from the curl command
                xml_start = curl_cmd.find("--data '") + 8
                xml_end = curl_cmd.find("'", xml_start)
                if xml_start > 7 and xml_end > xml_start:
                    xml_content = curl_cmd[xml_start:xml_end]
                    print(xml_content)
    
    print(f"\n🔍 Step 3: Test specific Sony filter")
    print("=" * 40)
    
    # Test 3: Try the Sony filter specifically
    sony_result = await client.query_records_advanced(
        universe_id=model_id,
        repository_id=repo_id,
        fields=["AD_ID", "ADVERTISER"],
        filters=[
            {
                "fieldId": "ADVERTISER",
                "operator": "EQUALS",
                "value": "Sony"
            }
        ],
        limit=3
    )
    
    if sony_result.get("status") == "success":
        sony_records = sony_result.get("data", {}).get("records", [])
        print(f"✅ Sony filter works: {len(sony_records)} records returned")
        
        if sony_records:
            print(f"📋 Sony records:")
            for i, record in enumerate(sony_records, 1):
                print(f"   {i}. AD_ID: {record.get('AD_ID', 'N/A')}, ADVERTISER: '{record.get('ADVERTISER', 'N/A')}'")
        else:
            print(f"⚠️  Sony filter returned 0 records (filter works but no matches)")
    else:
        print(f"❌ Sony filter failed: {sony_result.get('error', 'Unknown error')}")
        print(f"   Status code: {sony_result.get('status_code', 'N/A')}")
        
        # Show detailed error info
        if "response_body" in sony_result:
            response_body = sony_result["response_body"]
            print(f"   Response body: {response_body}")
        
        # Show the curl equivalent to debug
        if "curl_equivalent" in sony_result:
            print(f"\n📋 Generated cURL command:")
            curl_lines = sony_result["curl_equivalent"].split('\n')
            for line in curl_lines[:5]:  # Show first 5 lines
                print(f"   {line}")
            if len(curl_lines) > 5:
                print(f"   ... ({len(curl_lines) - 5} more lines)")
    
    print(f"\n🔍 Step 4: Try different operators")
    print("=" * 40)
    
    # Test 4: Try CONTAINS operator instead of EQUALS
    contains_result = await client.query_records_advanced(
        universe_id=model_id,
        repository_id=repo_id,
        fields=["AD_ID", "ADVERTISER"],
        filters=[
            {
                "fieldId": "ADVERTISER",
                "operator": "CONTAINS",
                "value": "Sony"
            }
        ],
        limit=3
    )
    
    if contains_result.get("status") == "success":
        contains_records = contains_result.get("data", {}).get("records", [])
        print(f"✅ CONTAINS filter works: {len(contains_records)} records returned")
    else:
        print(f"❌ CONTAINS filter failed: {contains_result.get('error', 'Unknown error')}")
    
    print(f"\n💡 Summary and Recommendations:")
    print("=" * 40)
    
    if basic_result.get("status") == "success":
        print("✅ Basic queries work")
        
        if records and "Sony" in advertisers:
            print("✅ 'Sony' exists in the data")
            print("🔍 The issue is likely with the filter XML structure or operator")
            print("💡 Try using 'CONTAINS' instead of 'EQUALS' in your query builder")
        elif records:
            print("❌ 'Sony' does not exist in the data")
            available_values = sorted(list(advertisers))[:5]  # Show first 5
            print(f"💡 Try one of these values instead: {available_values}")
        else:
            print("⚠️  No data returned - check if repository has records")
    else:
        print("❌ Basic queries don't work - check credentials and connectivity")
    
    print(f"\n🔧 Quick fixes to try in Query Builder:")
    if records and advertisers:
        suggested_value = list(advertisers)[0]
        print(f"   1. clear filters")
        print(f"   2. add filter ADVERTISER CONTAINS {suggested_value}")
        print(f"   3. execute query")
        print(f"\n   OR try:")
        print(f"   1. clear filters") 
        print(f"   2. add filter ADVERTISER EQUALS {suggested_value}")
        print(f"   3. execute query")

if __name__ == "__main__":
    asyncio.run(debug_predicate_issue())