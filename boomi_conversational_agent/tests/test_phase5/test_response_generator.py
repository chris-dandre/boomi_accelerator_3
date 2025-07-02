"""
Test suite for ResponseGenerator agent - TDD Phase 5
Following Red-Green-Refactor cycle
"""
import pytest
from cli_agent.agents.response_generator import ResponseGenerator
from tests.mocks.mock_mcp_client import MockMCPClient
from tests.mocks.mock_claude_client import MockClaudeClient

class TestResponseGenerator:
    """Test cases for ResponseGenerator agent"""
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client"""
        return MockMCPClient()
    
    @pytest.fixture
    def mock_claude_client(self):
        """Create mock Claude client"""
        return MockClaudeClient()
    
    @pytest.fixture
    def response_generator(self, mock_mcp_client, mock_claude_client):
        """Create ResponseGenerator with mocked dependencies"""
        generator = ResponseGenerator()
        generator.mcp_client = mock_mcp_client
        generator.claude_client = mock_claude_client
        return generator
    
    def test_generate_count_response(self, response_generator):
        """
        RED: Test should FAIL - ResponseGenerator doesn't exist yet
        
        Test: Should generate natural language response for count queries
        """
        user_query = "How many Sony products are there?"
        
        query_result = {
            'query_type': 'COUNT',
            'data': {'count': 45},
            'metadata': {
                'execution_time_ms': 150.5,
                'model_id': 'Product'
            }
        }
        
        response = response_generator.generate_response(user_query, query_result)
        
        assert isinstance(response, dict)
        assert 'message' in response
        assert 'response_type' in response
        assert 'metadata' in response
        
        assert response['response_type'] == 'COUNT'
        assert '45' in response['message']
        assert 'Sony' in response['message']
        assert 'product' in response['message'].lower()
    
    def test_generate_list_response(self, response_generator):
        """
        RED: Test should FAIL - ResponseGenerator doesn't exist yet
        
        Test: Should generate natural language response for list queries
        """
        user_query = "Show me Sony products"
        
        query_result = {
            'query_type': 'LIST',
            'data': [
                {'product_id': 'P001', 'product_name': 'Sony TV 55"', 'brand_name': 'Sony'},
                {'product_id': 'P002', 'product_name': 'Sony Speaker', 'brand_name': 'Sony'}
            ],
            'metadata': {
                'execution_time_ms': 250.0,
                'record_count': 2,
                'model_id': 'Product'
            }
        }
        
        response = response_generator.generate_response(user_query, query_result)
        
        assert response['response_type'] == 'LIST'
        assert 'Sony TV' in response['message']
        assert 'Sony Speaker' in response['message']
        assert '2' in response['message'] or 'two' in response['message'].lower()
    
    def test_generate_comparison_response(self, response_generator):
        """
        RED: Test should FAIL - ResponseGenerator doesn't exist yet
        
        Test: Should generate natural language response for comparison queries
        """
        user_query = "Compare Sony and Samsung product counts"
        
        query_result = {
            'query_type': 'COMPARE',
            'data': [
                {'brand_name': 'Sony', 'product_count': 45, 'avg_price': 299.99},
                {'brand_name': 'Samsung', 'product_count': 38, 'avg_price': 349.99}
            ],
            'metadata': {
                'execution_time_ms': 400.0,
                'comparison_groups': 2,
                'model_id': 'Product'
            }
        }
        
        response = response_generator.generate_response(user_query, query_result)
        
        assert response['response_type'] == 'COMPARE'
        assert 'Sony' in response['message']
        assert 'Samsung' in response['message']
        assert '45' in response['message']
        assert '38' in response['message']
    
    def test_generate_error_response(self, response_generator):
        """
        RED: Test should FAIL - ResponseGenerator doesn't exist yet
        
        Test: Should generate appropriate error responses
        """
        user_query = "Show me invalid data"
        
        error_result = {
            'error': 'Query validation failed: Invalid model_id',
            'query_type': 'LIST'
        }
        
        response = response_generator.generate_response(user_query, error_result)
        
        assert response['response_type'] == 'ERROR'
        assert 'error' in response['message'].lower() or 'sorry' in response['message'].lower()
        assert 'validation' in response['message'].lower()
    
    def test_format_data_for_display(self, response_generator):
        """
        RED: Test should FAIL - ResponseGenerator doesn't exist yet
        
        Test: Should format data in readable format
        """
        data = [
            {'product_name': 'Sony TV 55"', 'price': 899.99, 'brand_name': 'Sony'},
            {'product_name': 'Samsung TV 55"', 'price': 849.99, 'brand_name': 'Samsung'}
        ]
        
        formatted_data = response_generator.format_data_for_display(data, display_type='table')
        
        assert isinstance(formatted_data, str)
        assert 'Sony TV' in formatted_data
        assert 'Samsung TV' in formatted_data
        assert '899.99' in formatted_data
        assert '849.99' in formatted_data
    
    def test_generate_summary_statistics(self, response_generator):
        """
        RED: Test should FAIL - ResponseGenerator doesn't exist yet
        
        Test: Should generate summary statistics for datasets
        """
        data = [
            {'brand_name': 'Sony', 'price': 299.99},
            {'brand_name': 'Sony', 'price': 199.99},
            {'brand_name': 'Samsung', 'price': 349.99},
            {'brand_name': 'Samsung', 'price': 249.99}
        ]
        
        summary = response_generator.generate_summary_statistics(data)
        
        assert isinstance(summary, dict)
        assert 'total_records' in summary
        assert 'unique_brands' in summary
        assert 'price_range' in summary
        
        assert summary['total_records'] == 4
        assert summary['unique_brands'] == 2
    
    def test_personalize_response_tone(self, response_generator):
        """
        RED: Test should FAIL - ResponseGenerator doesn't exist yet
        
        Test: Should personalize response tone based on user context
        """
        user_context = {
            'role': 'executive',
            'experience_level': 'expert',
            'preferred_detail_level': 'summary'
        }
        
        base_response = "Found 45 Sony products with average price of $299.99"
        
        personalized_response = response_generator.personalize_response_tone(
            base_response, 
            user_context
        )
        
        assert isinstance(personalized_response, str)
        assert len(personalized_response) > 0
        # Executive responses should be concise and business-focused
        assert 'executive' not in personalized_response.lower()  # Shouldn't mention role
    
    def test_add_visualization_suggestions(self, response_generator):
        """
        RED: Test should FAIL - ResponseGenerator doesn't exist yet
        
        Test: Should suggest appropriate visualizations for data
        """
        query_result = {
            'query_type': 'COMPARE',
            'data': [
                {'brand_name': 'Sony', 'product_count': 45},
                {'brand_name': 'Samsung', 'product_count': 38}
            ]
        }
        
        suggestions = response_generator.add_visualization_suggestions(query_result)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Should suggest appropriate chart types for comparison
        chart_types = [s['type'] for s in suggestions]
        assert 'bar_chart' in chart_types or 'pie_chart' in chart_types
    
    def test_handle_large_datasets(self, response_generator):
        """
        RED: Test should FAIL - ResponseGenerator doesn't exist yet
        
        Test: Should handle large datasets appropriately
        """
        user_query = "List all products"
        
        # Simulate large dataset
        large_data = [{'product_id': f'P{i:03d}', 'product_name': f'Product {i}'} 
                     for i in range(1000)]
        
        query_result = {
            'query_type': 'LIST',
            'data': large_data,
            'metadata': {'record_count': 1000}
        }
        
        response = response_generator.generate_response(user_query, query_result)
        
        # Should summarize rather than list all items
        assert 'summary' in response['message'].lower() or 'showing' in response['message'].lower()
        assert '1000' in response['message'] or 'thousand' in response['message'].lower()
        
        # Should suggest pagination or filtering
        assert 'metadata' in response
        assert 'suggestions' in response['metadata']
    
    @pytest.mark.unit
    def test_response_generator_initialization(self):
        """
        RED: Test should FAIL - ResponseGenerator doesn't exist yet
        
        Test: Should initialize properly with default clients
        """
        generator = ResponseGenerator()
        
        assert generator is not None
        assert hasattr(generator, 'mcp_client')
        assert hasattr(generator, 'claude_client')
        assert hasattr(generator, 'response_templates')
    
    @pytest.mark.integration
    def test_end_to_end_response_generation(self, response_generator, mock_claude_client):
        """
        RED: Test should FAIL - ResponseGenerator doesn't exist yet
        
        Test: Complete workflow from query result to final response
        """
        user_query = "How many Sony products launched in Q1?"
        
        query_result = {
            'query_type': 'COUNT',
            'data': {'count': 12},
            'metadata': {
                'execution_time_ms': 180.5,
                'model_id': 'Product',
                'filters_applied': 2,
                'query_complexity': 'moderate'
            }
        }
        
        user_context = {
            'role': 'marketing_manager',
            'experience_level': 'intermediate'
        }
        
        # Generate complete response
        response = response_generator.generate_response(
            user_query, 
            query_result, 
            user_context=user_context
        )
        
        # Validate complete response structure
        assert isinstance(response, dict)
        assert 'message' in response
        assert 'response_type' in response
        assert 'metadata' in response
        
        # Should be contextually appropriate
        assert response['response_type'] == 'COUNT'
        assert '12' in response['message']
        assert 'Sony' in response['message']
        
        # Should include metadata
        assert 'execution_time_ms' in response['metadata']
        assert 'data_summary' in response['metadata']
        
        # Should have called Claude for natural language generation
        assert mock_claude_client.call_count >= 1