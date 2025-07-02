"""
Test suite for DataRetrieval agent - TDD Phase 5
Following Red-Green-Refactor cycle
"""
import pytest
from cli_agent.agents.data_retrieval import DataRetrieval
from tests.mocks.mock_mcp_client import MockMCPClient
from tests.mocks.mock_claude_client import MockClaudeClient

class TestDataRetrieval:
    """Test cases for DataRetrieval agent"""
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client"""
        return MockMCPClient()
    
    @pytest.fixture
    def mock_claude_client(self):
        """Create mock Claude client"""
        return MockClaudeClient()
    
    @pytest.fixture
    def data_retrieval(self, mock_mcp_client, mock_claude_client):
        """Create DataRetrieval with mocked dependencies"""
        retrieval = DataRetrieval()
        retrieval.mcp_client = mock_mcp_client
        retrieval.claude_client = mock_claude_client
        return retrieval
    
    def test_execute_count_query(self, data_retrieval, mock_mcp_client):
        """
        RED: Test should FAIL - DataRetrieval doesn't exist yet
        
        Test: Should execute COUNT query and return count result
        """
        query = {
            'query_type': 'COUNT',
            'model_id': 'Product',
            'operations': ['count'],
            'filters': [
                {'field': 'brand_name', 'operator': 'equals', 'value': 'Sony'}
            ]
        }
        
        result = data_retrieval.execute_query(query)
        
        assert isinstance(result, dict)
        assert 'query_type' in result
        assert 'data' in result
        assert 'metadata' in result
        
        assert result['query_type'] == 'COUNT'
        assert isinstance(result['data'], dict)
        assert 'count' in result['data']
        assert result['data']['count'] > 0
        assert mock_mcp_client.call_count == 1
    
    def test_execute_list_query(self, data_retrieval, mock_mcp_client):
        """
        RED: Test should FAIL - DataRetrieval doesn't exist yet
        
        Test: Should execute LIST query and return records
        """
        query = {
            'query_type': 'LIST',
            'model_id': 'Product',
            'operations': ['select'],
            'fields': ['product_id', 'product_name', 'brand_name'],
            'filters': [
                {'field': 'brand_name', 'operator': 'equals', 'value': 'Sony'}
            ]
        }
        
        result = data_retrieval.execute_query(query)
        
        assert result['query_type'] == 'LIST'
        assert isinstance(result['data'], list)
        assert len(result['data']) > 0
        
        # Check record structure
        first_record = result['data'][0]
        assert 'product_id' in first_record
        assert 'product_name' in first_record
        assert 'brand_name' in first_record
    
    def test_execute_comparison_query(self, data_retrieval, mock_mcp_client):
        """
        RED: Test should FAIL - DataRetrieval doesn't exist yet
        
        Test: Should execute COMPARE query with grouping
        """
        query = {
            'query_type': 'COMPARE',
            'model_id': 'Product',
            'operations': ['select', 'group_by'],
            'fields': ['brand_name', 'product_count'],
            'filters': [
                {'field': 'brand_name', 'operator': 'equals', 'value': 'Sony'},
                {'field': 'brand_name', 'operator': 'equals', 'value': 'Samsung'}
            ],
            'grouping': {'field': 'brand_name', 'type': 'group_by'}
        }
        
        result = data_retrieval.execute_query(query)
        
        assert result['query_type'] == 'COMPARE'
        assert isinstance(result['data'], list)
        assert len(result['data']) >= 2  # Sony and Samsung groups
        
        # Check grouped structure
        for group in result['data']:
            assert 'brand_name' in group
            assert group['brand_name'] in ['Sony', 'Samsung']
    
    def test_handle_query_timeout(self, data_retrieval):
        """
        RED: Test should FAIL - DataRetrieval doesn't exist yet
        
        Test: Should handle query timeouts gracefully
        """
        # Simulate a complex query that might timeout
        complex_query = {
            'query_type': 'ANALYZE',
            'model_id': 'Product',
            'operations': ['select', 'aggregate'],
            'timeout': 0.001  # Very short timeout to force failure
        }
        
        result = data_retrieval.execute_query(complex_query)
        
        assert isinstance(result, dict)
        assert 'error' in result
        assert 'timeout' in result['error'].lower()
    
    def test_validate_query_before_execution(self, data_retrieval):
        """
        RED: Test should FAIL - DataRetrieval doesn't exist yet
        
        Test: Should validate query before execution
        """
        invalid_query = {
            'query_type': 'INVALID',
            'model_id': '',
            'operations': []
        }
        
        result = data_retrieval.execute_query(invalid_query)
        
        assert 'error' in result
        assert 'validation' in result['error'].lower()
    
    def test_transform_raw_data(self, data_retrieval):
        """
        RED: Test should FAIL - DataRetrieval doesn't exist yet
        
        Test: Should transform raw MCP data to standard format
        """
        raw_data = [
            {'product_id': 'P001', 'name': 'Sony TV', 'brand': 'Sony'},
            {'product_id': 'P002', 'name': 'Sony Speaker', 'brand': 'Sony'}
        ]
        
        field_mapping = {
            'name': 'product_name',
            'brand': 'brand_name'
        }
        
        transformed_data = data_retrieval.transform_raw_data(raw_data, field_mapping)
        
        assert isinstance(transformed_data, list)
        assert len(transformed_data) == 2
        
        # Check field transformation
        first_record = transformed_data[0]
        assert 'product_name' in first_record
        assert 'brand_name' in first_record
        assert first_record['product_name'] == 'Sony TV'
        assert first_record['brand_name'] == 'Sony'
    
    def test_get_execution_statistics(self, data_retrieval, mock_mcp_client):
        """
        RED: Test should FAIL - DataRetrieval doesn't exist yet
        
        Test: Should return execution statistics
        """
        query = {
            'query_type': 'COUNT',
            'model_id': 'Product',
            'operations': ['count']
        }
        
        result = data_retrieval.execute_query(query)
        
        assert 'metadata' in result
        metadata = result['metadata']
        
        assert 'execution_time_ms' in metadata
        assert 'record_count' in metadata
        assert 'query_complexity' in metadata
        assert isinstance(metadata['execution_time_ms'], (int, float))
        assert metadata['execution_time_ms'] >= 0
    
    def test_cache_query_results(self, data_retrieval):
        """
        RED: Test should FAIL - DataRetrieval doesn't exist yet
        
        Test: Should cache results for identical queries
        """
        query = {
            'query_type': 'COUNT',
            'model_id': 'Product',
            'operations': ['count'],
            'cache_enabled': True
        }
        
        # First execution
        result1 = data_retrieval.execute_query(query)
        first_execution_time = result1['metadata']['execution_time_ms']
        
        # Second execution (should be cached)
        result2 = data_retrieval.execute_query(query)
        second_execution_time = result2['metadata']['execution_time_ms']
        
        # Results should be identical
        assert result1['data'] == result2['data']
        
        # Second execution should be faster (cached)
        assert second_execution_time <= first_execution_time
        assert 'cache_hit' in result2['metadata']
        assert result2['metadata']['cache_hit'] is True
    
    @pytest.mark.unit
    def test_data_retrieval_initialization(self):
        """
        RED: Test should FAIL - DataRetrieval doesn't exist yet
        
        Test: Should initialize properly with default clients
        """
        retrieval = DataRetrieval()
        
        assert retrieval is not None
        assert hasattr(retrieval, 'mcp_client')
        assert hasattr(retrieval, 'claude_client')
        assert hasattr(retrieval, 'query_cache')
    
    @pytest.mark.integration
    def test_end_to_end_data_retrieval(self, data_retrieval):
        """
        RED: Test should FAIL - DataRetrieval doesn't exist yet
        
        Test: Complete workflow from query to formatted results
        """
        query = {
            'query_type': 'LIST',
            'model_id': 'Product',
            'operations': ['select'],
            'fields': ['product_id', 'product_name', 'brand_name'],
            'filters': [
                {'field': 'brand_name', 'operator': 'equals', 'value': 'Sony'}
            ],
            'metadata': {
                'original_intent': 'LIST',
                'complexity': 'SIMPLE'
            }
        }
        
        # Execute query
        result = data_retrieval.execute_query(query)
        
        # Validate result structure
        assert isinstance(result, dict)
        assert result['query_type'] == 'LIST'
        assert isinstance(result['data'], list)
        assert len(result['data']) > 0
        
        # Check metadata preservation
        assert 'metadata' in result
        assert 'execution_time_ms' in result['metadata']
        assert 'record_count' in result['metadata']
        
        # Verify data quality
        for record in result['data']:
            assert 'product_id' in record
            assert 'brand_name' in record
            # Should only return Sony products due to filter
            assert record['brand_name'] == 'Sony'