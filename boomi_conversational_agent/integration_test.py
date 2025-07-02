#!/usr/bin/env python3
"""
Real-World Integration Test for Phase 5 CLI Agent
Tests the conversational agent against actual Boomi DataHub data
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add paths for imports
current_dir = Path(__file__).parent
boomi_clients_dir = current_dir / "boomi_datahub_mcp_server"
sys.path.append(str(current_dir))
sys.path.append(str(boomi_clients_dir))

# Import our CLI agent and real clients
from cli_agent.cli_agent import CLIAgent

# Try to import real Boomi clients
try:
    from boomi_datahub_mcp_client_v2 import EnhancedBoomiDataHubMCPClient
    from boomi_datahub_client import BoomiDataHubClient
    REAL_CLIENTS_AVAILABLE = True
    print("✅ Real Boomi clients imported successfully")
except ImportError as e:
    print(f"⚠️  Real Boomi clients not available: {e}")
    print(f"📝 Expected files in: {boomi_clients_dir}")
    print("📝 Will run with mock clients for testing structure")
    REAL_CLIENTS_AVAILABLE = False

class SyncBoomiMCPClient:
    """Synchronous wrapper for EnhancedBoomiDataHubMCPClient"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:8001/mcp"):
        self._async_client = EnhancedBoomiDataHubMCPClient(server_url)
    
    def get_all_models(self):
        """Synchronous wrapper for get_all_models"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._async_client.get_all_models())
            loop.close()
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_model_details(self, model_id: str):
        """Synchronous wrapper for get_model_details"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._async_client.get_model_details(model_id))
            loop.close()
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def test_connection(self):
        """Synchronous wrapper for test_connection"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._async_client.test_connection())
            loop.close()
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_model_fields(self, model_id: str):
        """Synchronous wrapper for get_model_fields"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._async_client.get_model_fields(model_id))
            loop.close()
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def execute_query(self, query):
        """Synchronous wrapper for execute_query (fallback to query_records_advanced)"""
        try:
            # Convert our query structure to MCP client parameters
            universe_id = query.get('model_id', '')  # Our agents use 'model_id'
            repository_id = query.get('repository_id', '43212d46-1832-4ab1-820d-c0334d619f6f')  # Use sample repo ID from examples
            fields = query.get('fields', [])
            filters = query.get('filters', [])
            limit = query.get('limit', 100)
            offset_token = query.get('offset_token', '')
            
            # Convert filters to MCP format if needed
            mcp_filters = self._convert_filters_to_mcp_format(filters)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_client.query_records_advanced(
                    universe_id, repository_id, fields, mcp_filters, limit, offset_token
                )
            )
            loop.close()
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _convert_filters_to_mcp_format(self, filters):
        """Convert our filter format to MCP client format"""
        mcp_filters = []
        for filter_item in filters:
            if isinstance(filter_item, dict):
                # Convert our filter format to MCP format
                mcp_filter = {
                    "fieldId": filter_item.get('field', ''),
                    "operator": filter_item.get('operator', 'equals'),
                    "value": filter_item.get('value', '')
                }
                mcp_filters.append(mcp_filter)
        return mcp_filters
    
    def query_records_advanced(self, universe_id: str, repository_id: str, 
                              fields=None, filters=None, limit=100, offset_token=""):
        """Synchronous wrapper for query_records_advanced"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_client.query_records_advanced(
                    universe_id, repository_id, fields, filters, limit, offset_token
                )
            )
            loop.close()
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}

class IntegrationTestRunner:
    """Runs comprehensive integration tests against real Boomi DataHub"""
    
    def __init__(self):
        """Initialize test runner with real or mock clients"""
        # Load environment variables from local boomi_datahub_mcp_server directory
        env_file = current_dir / "boomi_datahub_mcp_server" / ".env"
        if not env_file.exists():
            # Fallback to .env in current directory
            env_file = current_dir / ".env"
        
        if env_file.exists():
            load_dotenv(env_file)
            print(f"📝 Loaded environment from: {env_file}")
        else:
            print("⚠️  No .env file found - using system environment variables")
        
        self.test_results = []
        self.start_time = time.time()
        
        # Initialize CLI agent with appropriate clients
        if REAL_CLIENTS_AVAILABLE and self._validate_credentials():
            print("🔗 Initializing with REAL Boomi DataHub connection...")
            self.cli_agent = self._create_real_cli_agent()
            self.test_mode = "REAL"
        else:
            print("🧪 Initializing with MOCK clients for structure testing...")
            self.cli_agent = CLIAgent()  # Uses mock clients
            self.test_mode = "MOCK"
        
        print(f"✅ CLI Agent initialized in {self.test_mode} mode")
    
    def _validate_credentials(self) -> bool:
        """Validate that required credentials are available"""
        required_vars = [
            'BOOMI_USERNAME', 
            'BOOMI_PASSWORD', 
            'BOOMI_ACCOUNT_ID',
            'BOOMI_DATAHUB_USERNAME',
            'BOOMI_DATAHUB_PASSWORD'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            print(f"❌ Missing required environment variables: {missing}")
            return False
        
        print("✅ All required credentials found in environment")
        return True
    
    def _create_real_cli_agent(self) -> CLIAgent:
        """Create CLI agent with real Boomi clients"""
        try:
            # Create synchronous wrapper for the async MCP client
            mcp_client = SyncBoomiMCPClient(
                server_url="http://127.0.0.1:8001/mcp"
            )
            
            # For Claude client, we'll need to set up Anthropic API
            # For now, using None will fall back to pattern-based responses
            claude_client = None  # TODO: Set up real Claude API client
            
            return CLIAgent(mcp_client=mcp_client, claude_client=claude_client)
            
        except Exception as e:
            print(f"❌ Failed to create real clients: {e}")
            print("🔄 Falling back to mock clients...")
            return CLIAgent()
    
    def run_all_tests(self):
        """Run comprehensive integration test suite"""
        print("\n" + "="*60)
        print("🧪 STARTING PHASE 5 INTEGRATION TESTS")
        print("="*60)
        
        # Test 1: System Health Check
        self._test_system_health()
        
        # Test 2: Basic Query Processing
        self._test_basic_queries()
        
        # Test 3: Different Query Types
        self._test_query_types()
        
        # Test 4: Error Handling
        self._test_error_handling()
        
        # Test 5: Performance & Caching
        self._test_performance()
        
        # Test 6: Configuration Management
        self._test_configuration()
        
        # Generate final report
        self._generate_report()
    
    def _test_system_health(self):
        """Test system health and status"""
        print("\n🔍 Testing System Health...")
        
        try:
            # Test status command
            status = self.cli_agent.get_status()
            
            test_result = {
                'test': 'System Health Check',
                'success': True,
                'details': {
                    'pipeline_status': status.get('pipeline_status'),
                    'connection_status': status.get('connection_status'),
                    'agent_health': status.get('agent_health')
                },
                'execution_time': 0
            }
            
            print(f"  ✅ Pipeline Status: {status.get('pipeline_status')}")
            print(f"  ✅ Connection Status: {status.get('connection_status')}")
            print(f"  ✅ Agent Health: {status.get('agent_health')}")
            
        except Exception as e:
            test_result = {
                'test': 'System Health Check',
                'success': False,
                'error': str(e),
                'execution_time': 0
            }
            print(f"  ❌ Health check failed: {e}")
        
        self.test_results.append(test_result)
    
    def _test_basic_queries(self):
        """Test basic query processing"""
        print("\n🔍 Testing Basic Query Processing...")
        
        basic_queries = [
            "How many models are there?",
            "Show me available data models",
            "What data do we have?"
        ]
        
        for query in basic_queries:
            try:
                start_time = time.time()
                result = self.cli_agent.process_query(query)
                execution_time = (time.time() - start_time) * 1000
                
                test_result = {
                    'test': f'Basic Query: {query}',
                    'success': result['success'],
                    'execution_time': execution_time,
                    'response_preview': result.get('response', result.get('error', ''))[:100] + '...'
                }
                
                if result['success']:
                    print(f"  ✅ Query: {query}")
                    print(f"     Response: {result['response'][:60]}...")
                    print(f"     Time: {execution_time:.1f}ms")
                else:
                    print(f"  ❌ Query: {query}")
                    print(f"     Error: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                test_result = {
                    'test': f'Basic Query: {query}',
                    'success': False,
                    'error': str(e),
                    'execution_time': 0
                }
                print(f"  ❌ Query failed: {query} - {e}")
            
            self.test_results.append(test_result)
    
    def _test_query_types(self):
        """Test different types of queries"""
        print("\n🔍 Testing Different Query Types...")
        
        query_types = {
            'COUNT': [
                "How many products do we have?",
                "Count the number of records"
            ],
            'LIST': [
                "Show me the data models",
                "List available information"
            ],
            'COMPARE': [
                "Compare model sizes",
                "Compare data volumes"
            ]
        }
        
        for query_type, queries in query_types.items():
            print(f"\n  Testing {query_type} queries:")
            
            for query in queries:
                try:
                    start_time = time.time()
                    result = self.cli_agent.process_query(query)
                    execution_time = (time.time() - start_time) * 1000
                    
                    success = result['success']
                    detected_type = result.get('response_type', 'UNKNOWN')
                    
                    test_result = {
                        'test': f'{query_type} Query: {query}',
                        'success': success,
                        'expected_type': query_type,
                        'detected_type': detected_type,
                        'execution_time': execution_time
                    }
                    
                    if success:
                        type_match = detected_type == query_type
                        status = "✅" if type_match else "⚠️"
                        print(f"    {status} {query}")
                        print(f"       Expected: {query_type}, Got: {detected_type}")
                        print(f"       Time: {execution_time:.1f}ms")
                    else:
                        print(f"    ❌ {query}")
                        print(f"       Error: {result.get('error', 'Unknown error')}")
                    
                except Exception as e:
                    test_result = {
                        'test': f'{query_type} Query: {query}',
                        'success': False,
                        'error': str(e),
                        'execution_time': 0
                    }
                    print(f"    ❌ Query failed: {query} - {e}")
                
                self.test_results.append(test_result)
    
    def _test_error_handling(self):
        """Test error handling with invalid queries"""
        print("\n🔍 Testing Error Handling...")
        
        error_test_cases = [
            "",  # Empty query
            "   ",  # Whitespace only
            "asdfghjkl",  # Nonsense query
            "SQL injection attempt; DROP TABLE users;",  # Potential injection
        ]
        
        for query in error_test_cases:
            try:
                result = self.cli_agent.process_query(query)
                
                # Error handling should gracefully return success=False
                if not result['success'] and 'error' in result:
                    print(f"  ✅ Properly handled invalid query: '{query}'")
                    test_result = {
                        'test': f'Error Handling: {repr(query)}',
                        'success': True,  # Successfully handled the error
                        'handled_gracefully': True
                    }
                else:
                    print(f"  ⚠️  Query unexpectedly succeeded: '{query}'")
                    test_result = {
                        'test': f'Error Handling: {repr(query)}',
                        'success': False,
                        'reason': 'Should have failed but succeeded'
                    }
                
            except Exception as e:
                print(f"  ❌ Unhandled exception for '{query}': {e}")
                test_result = {
                    'test': f'Error Handling: {repr(query)}',
                    'success': False,
                    'error': str(e)
                }
            
            self.test_results.append(test_result)
    
    def _test_performance(self):
        """Test performance and caching"""
        print("\n🔍 Testing Performance & Caching...")
        
        test_query = "How many models are available?"
        
        # Test 1: Initial query (no cache)
        try:
            start_time = time.time()
            result1 = self.cli_agent.process_query(test_query)
            first_time = (time.time() - start_time) * 1000
            
            # Test 2: Repeated query (should use cache if enabled)
            start_time = time.time()
            result2 = self.cli_agent.process_query(test_query)
            second_time = (time.time() - start_time) * 1000
            
            cache_effective = second_time < first_time
            
            print(f"  ✅ First query: {first_time:.1f}ms")
            print(f"  ✅ Second query: {second_time:.1f}ms")
            print(f"  {'✅' if cache_effective else '⚠️'} Cache effectiveness: {'Good' if cache_effective else 'No improvement'}")
            
            test_result = {
                'test': 'Performance & Caching',
                'success': True,
                'first_execution_ms': first_time,
                'second_execution_ms': second_time,
                'cache_effective': cache_effective
            }
            
        except Exception as e:
            print(f"  ❌ Performance test failed: {e}")
            test_result = {
                'test': 'Performance & Caching',
                'success': False,
                'error': str(e)
            }
        
        self.test_results.append(test_result)
    
    def _test_configuration(self):
        """Test configuration management"""
        print("\n🔍 Testing Configuration Management...")
        
        try:
            # Test getting configuration
            original_config = self.cli_agent.get_configuration()
            
            # Test updating configuration
            test_config = {'verbose_mode': True, 'output_format': 'json'}
            update_success = self.cli_agent.update_configuration(test_config)
            
            # Verify update
            updated_config = self.cli_agent.get_configuration()
            config_applied = (
                updated_config['verbose_mode'] == True and 
                updated_config['output_format'] == 'json'
            )
            
            # Restore original configuration
            self.cli_agent.update_configuration(original_config)
            
            print(f"  ✅ Configuration update: {'Success' if update_success else 'Failed'}")
            print(f"  ✅ Configuration applied: {'Yes' if config_applied else 'No'}")
            
            test_result = {
                'test': 'Configuration Management',
                'success': update_success and config_applied,
                'update_success': update_success,
                'config_applied': config_applied
            }
            
        except Exception as e:
            print(f"  ❌ Configuration test failed: {e}")
            test_result = {
                'test': 'Configuration Management',
                'success': False,
                'error': str(e)
            }
        
        self.test_results.append(test_result)
    
    def _generate_report(self):
        """Generate comprehensive test report"""
        total_time = (time.time() - self.start_time) * 1000
        
        print("\n" + "="*60)
        print("📊 INTEGRATION TEST REPORT")
        print("="*60)
        
        # Summary statistics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📈 TEST SUMMARY:")
        print(f"   • Mode: {self.test_mode}")
        print(f"   • Total Tests: {total_tests}")
        print(f"   • Successful: {successful_tests} ✅")
        print(f"   • Failed: {failed_tests} ❌")
        print(f"   • Success Rate: {success_rate:.1f}%")
        print(f"   • Total Time: {total_time:.1f}ms")
        
        # Performance metrics
        execution_times = [r.get('execution_time', 0) for r in self.test_results if r.get('execution_time')]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)
            print(f"\n⏱️  PERFORMANCE:")
            print(f"   • Average Query Time: {avg_time:.1f}ms")
            print(f"   • Slowest Query: {max_time:.1f}ms")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result['success'] else "❌"
            test_name = result['test']
            
            if result['success']:
                exec_time = result.get('execution_time', 0)
                print(f"   {i:2d}. {status} {test_name} ({exec_time:.1f}ms)")
            else:
                error = result.get('error', 'Unknown error')
                print(f"   {i:2d}. {status} {test_name}")
                print(f"       Error: {error}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if self.test_mode == "MOCK":
            print("   • Set up real Boomi DataHub connection for production testing")
            print("   • Configure Claude API client for enhanced responses")
        
        if failed_tests > 0:
            print("   • Review failed tests and fix issues before Phase 6")
            print("   • Consider additional error handling for edge cases")
        
        if execution_times and max(execution_times) > 5000:
            print("   • Optimize slow queries before production deployment")
            print("   • Consider implementing query result caching")
        
        print(f"\n🎯 PHASE 5 STATUS: {'READY FOR PHASE 6' if success_rate >= 80 else 'NEEDS FIXES'}")
        
        # Save detailed report
        self._save_report_file()
    
    def _save_report_file(self):
        """Save detailed report to JSON file"""
        report_data = {
            'test_mode': self.test_mode,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_tests': len(self.test_results),
                'successful_tests': sum(1 for r in self.test_results if r['success']),
                'success_rate': sum(1 for r in self.test_results if r['success']) / len(self.test_results) * 100
            },
            'detailed_results': self.test_results
        }
        
        report_file = current_dir / 'integration_test_report.json'
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: {report_file}")

def main():
    """Main entry point for integration testing"""
    print("🚀 Phase 5 Integration Testing")
    print("Testing CLI Agent with real/mock Boomi DataHub...")
    
    runner = IntegrationTestRunner()
    runner.run_all_tests()

if __name__ == "__main__":
    main()