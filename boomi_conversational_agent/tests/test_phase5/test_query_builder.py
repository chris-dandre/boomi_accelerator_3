"""
Test suite for QueryBuilder agent - TDD Phase 5
Following Red-Green-Refactor cycle
"""
import pytest
from cli_agent.agents.query_builder import QueryBuilder
from tests.mocks.mock_mcp_client import MockMCPClient
from tests.mocks.mock_claude_client import MockClaudeClient

class TestQueryBuilder:
    """Test cases for QueryBuilder agent"""
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client"""
        return MockMCPClient()
    
    @pytest.fixture
    def mock_claude_client(self):
        """Create mock Claude client"""
        return MockClaudeClient()
    
    @pytest.fixture
    def query_builder(self, mock_mcp_client, mock_claude_client):
        """Create QueryBuilder with mocked dependencies"""
        builder = QueryBuilder()
        builder.mcp_client = mock_mcp_client
        builder.claude_client = mock_claude_client
        return builder
    
    def test_build_simple_count_query(self, query_builder):
        """
        RED: Test should FAIL - QueryBuilder doesn't exist yet
        
        Test: Should build simple COUNT query
        """
        query_analysis = {
            'intent': 'COUNT',
            'entities': [
                {'text': 'products', 'type': 'OBJECT', 'confidence': 0.95}
            ],
            'query_type': 'SIMPLE'
        }
        
        field_mapping = {
            'products': {'field_name': 'product_name', 'confidence': 0.85}
        }
        
        model_id = 'Product'
        
        query = query_builder.build_query(query_analysis, field_mapping, model_id)
        
        assert isinstance(query, dict)
        assert 'query_type' in query
        assert 'model_id' in query
        assert 'operations' in query
        
        assert query['query_type'] == 'COUNT'
        assert query['model_id'] == 'Product'
        assert len(query['operations']) > 0
    
    def test_build_filtered_query(self, query_builder):
        """
        RED: Test should FAIL - QueryBuilder doesn't exist yet
        
        Test: Should build query with filters
        """
        query_analysis = {
            'intent': 'COUNT',
            'entities': [
                {'text': 'Sony', 'type': 'BRAND', 'confidence': 0.98},
                {'text': 'products', 'type': 'OBJECT', 'confidence': 0.95}
            ],
            'query_type': 'SIMPLE'
        }
        
        field_mapping = {
            'Sony': {'field_name': 'brand_name', 'confidence': 0.95},
            'products': {'field_name': 'product_name', 'confidence': 0.85}
        }
        
        model_id = 'Product'
        
        query = query_builder.build_query(query_analysis, field_mapping, model_id)
        
        assert query['query_type'] == 'COUNT'
        assert 'filters' in query
        assert len(query['filters']) > 0
        
        # Should have brand filter
        brand_filter = next((f for f in query['filters'] if f['field'] == 'brand_name'), None)
        assert brand_filter is not None
        assert brand_filter['operator'] == 'equals'
        assert brand_filter['value'] == 'Sony'
    
    def test_build_comparison_query(self, query_builder):
        """
        RED: Test should FAIL - QueryBuilder doesn't exist yet
        
        Test: Should build comparison query with multiple filters
        """
        query_analysis = {
            'intent': 'COMPARE',
            'entities': [
                {'text': 'Sony', 'type': 'BRAND', 'confidence': 0.98},
                {'text': 'Samsung', 'type': 'BRAND', 'confidence': 0.98}
            ],
            'query_type': 'COMPLEX'
        }
        
        field_mapping = {
            'Sony': {'field_name': 'brand_name', 'confidence': 0.95},
            'Samsung': {'field_name': 'brand_name', 'confidence': 0.95}
        }
        
        model_id = 'Product'
        
        query = query_builder.build_query(query_analysis, field_mapping, model_id)
        
        assert query['query_type'] == 'COMPARE'
        assert 'grouping' in query
        assert query['grouping']['field'] == 'brand_name'
        
        # Should group by brand_name
        assert 'filters' in query
        brand_values = [f['value'] for f in query['filters'] if f['field'] == 'brand_name']
        assert 'Sony' in brand_values
        assert 'Samsung' in brand_values
    
    def test_build_time_filtered_query(self, query_builder):
        """
        RED: Test should FAIL - QueryBuilder doesn't exist yet
        
        Test: Should build query with time-based filters
        """
        query_analysis = {
            'intent': 'LIST',
            'entities': [
                {'text': 'products', 'type': 'OBJECT', 'confidence': 0.95},
                {'text': 'Q1', 'type': 'TIME_PERIOD', 'confidence': 0.90}
            ],
            'query_type': 'SIMPLE'
        }
        
        field_mapping = {
            'products': {'field_name': 'product_name', 'confidence': 0.85},
            'Q1': {'field_name': 'quarter_year', 'confidence': 0.90}
        }
        
        model_id = 'Launch'
        
        query = query_builder.build_query(query_analysis, field_mapping, model_id)
        
        assert query['query_type'] == 'LIST'
        
        # Should have time filter
        time_filter = next((f for f in query['filters'] if f['field'] == 'quarter_year'), None)
        assert time_filter is not None
        assert time_filter['value'] == 'Q1'
    
    def test_validate_query_structure(self, query_builder):
        """
        RED: Test should FAIL - QueryBuilder doesn't exist yet
        
        Test: Should validate query structure
        """
        valid_query = {
            'query_type': 'COUNT',
            'model_id': 'Product',
            'operations': ['count'],
            'filters': [
                {'field': 'brand_name', 'operator': 'equals', 'value': 'Sony'}
            ]
        }
        
        validation_result = query_builder.validate_query(valid_query)
        
        assert isinstance(validation_result, dict)
        assert 'is_valid' in validation_result
        assert 'errors' in validation_result
        assert validation_result['is_valid'] is True
        assert len(validation_result['errors']) == 0
    
    def test_validate_invalid_query(self, query_builder):
        """
        RED: Test should FAIL - QueryBuilder doesn't exist yet
        
        Test: Should identify invalid query structure
        """
        invalid_query = {
            'query_type': 'INVALID_TYPE',
            'model_id': '',
            'operations': []
        }
        
        validation_result = query_builder.validate_query(invalid_query)
        
        assert validation_result['is_valid'] is False
        assert len(validation_result['errors']) > 0
        assert any('query_type' in error for error in validation_result['errors'])
        assert any('model_id' in error for error in validation_result['errors'])
    
    def test_optimize_query(self, query_builder):
        """
        RED: Test should FAIL - QueryBuilder doesn't exist yet
        
        Test: Should optimize query for performance
        """
        query = {
            'query_type': 'COUNT',
            'model_id': 'Product',
            'operations': ['count'],
            'filters': [
                {'field': 'brand_name', 'operator': 'equals', 'value': 'Sony'},
                {'field': 'brand_name', 'operator': 'equals', 'value': 'Sony'}  # Duplicate
            ]
        }
        
        optimized_query = query_builder.optimize_query(query)
        
        assert isinstance(optimized_query, dict)
        assert optimized_query['query_type'] == 'COUNT'
        
        # Should remove duplicate filters
        brand_filters = [f for f in optimized_query['filters'] if f['field'] == 'brand_name']
        assert len(brand_filters) == 1
    
    @pytest.mark.unit
    def test_query_builder_initialization(self):
        """
        RED: Test should FAIL - QueryBuilder doesn't exist yet
        
        Test: Should initialize properly with default clients
        """
        builder = QueryBuilder()
        
        assert builder is not None
        assert hasattr(builder, 'mcp_client')
        assert hasattr(builder, 'claude_client')
    
    @pytest.mark.integration
    def test_end_to_end_query_building(self, query_builder):
        """
        RED: Test should FAIL - QueryBuilder doesn't exist yet
        
        Test: Complete workflow from analysis to executable query
        """
        query_analysis = {
            'intent': 'COUNT',
            'entities': [
                {'text': 'Sony', 'type': 'BRAND', 'confidence': 0.98},
                {'text': 'products', 'type': 'OBJECT', 'confidence': 0.95},
                {'text': 'Q1', 'type': 'TIME_PERIOD', 'confidence': 0.90}
            ],
            'query_type': 'SIMPLE'
        }
        
        field_mapping = {
            'Sony': {'field_name': 'brand_name', 'confidence': 0.95},
            'products': {'field_name': 'product_name', 'confidence': 0.85},
            'Q1': {'field_name': 'quarter_year', 'confidence': 0.90}
        }
        
        model_id = 'Product'
        
        # Build query
        query = query_builder.build_query(query_analysis, field_mapping, model_id)
        
        # Validate query
        validation_result = query_builder.validate_query(query)
        
        # Optimize query
        optimized_query = query_builder.optimize_query(query)
        
        assert validation_result['is_valid'] is True
        assert optimized_query['query_type'] == 'COUNT'
        assert optimized_query['model_id'] == 'Product'
        assert len(optimized_query['filters']) >= 2  # Brand and time filters
        
        # Should have Sony brand filter
        brand_filter = next((f for f in optimized_query['filters'] if f['field'] == 'brand_name'), None)
        assert brand_filter is not None
        assert brand_filter['value'] == 'Sony'