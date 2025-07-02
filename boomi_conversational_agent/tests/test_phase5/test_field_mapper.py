"""
Test suite for FieldMapper agent - TDD Phase 5
Following Red-Green-Refactor cycle
"""
import pytest
from cli_agent.agents.field_mapper import FieldMapper
from tests.mocks.mock_mcp_client import MockMCPClient
from tests.mocks.mock_claude_client import MockClaudeClient

class TestFieldMapper:
    """Test cases for FieldMapper agent"""
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client"""
        return MockMCPClient()
    
    @pytest.fixture
    def mock_claude_client(self):
        """Create mock Claude client"""
        return MockClaudeClient()
    
    @pytest.fixture
    def field_mapper(self, mock_mcp_client, mock_claude_client):
        """Create FieldMapper with mocked dependencies"""
        mapper = FieldMapper()
        mapper.mcp_client = mock_mcp_client
        mapper.claude_client = mock_claude_client
        return mapper
    
    def test_get_model_fields(self, field_mapper, mock_mcp_client):
        """
        RED: Test should FAIL - FieldMapper doesn't exist yet
        
        Test: Should retrieve field information for a model
        """
        model_id = "Product"
        
        fields = field_mapper.get_model_fields(model_id)
        
        assert isinstance(fields, list)
        assert len(fields) > 0
        assert mock_mcp_client.call_count == 1
        
        # Check field structure
        first_field = fields[0]
        assert 'name' in first_field
        assert 'type' in first_field
        assert 'description' in first_field
    
    def test_map_entities_to_fields_simple(self, field_mapper, mock_claude_client):
        """
        RED: Test should FAIL - FieldMapper doesn't exist yet
        
        Test: Should map entities to model fields using Claude
        """
        entities = [
            {'text': 'Sony', 'type': 'BRAND', 'confidence': 0.98}
        ]
        
        model_fields = [
            {'name': 'brand_name', 'type': 'string', 'description': 'Product brand'},
            {'name': 'product_name', 'type': 'string', 'description': 'Product name'}
        ]
        
        field_mapping = field_mapper.map_entities_to_fields(entities, model_fields)
        
        assert isinstance(field_mapping, dict)
        assert len(field_mapping) > 0
        assert mock_claude_client.call_count == 1
        
        # Should map Sony to brand_name field
        assert 'Sony' in field_mapping
        assert field_mapping['Sony']['field_name'] == 'brand_name'
        assert field_mapping['Sony']['confidence'] > 0.8
    
    def test_map_entities_to_fields_multiple(self, field_mapper, mock_claude_client):
        """
        RED: Test should FAIL - FieldMapper doesn't exist yet
        
        Test: Should map multiple entities to different fields
        """
        entities = [
            {'text': 'Sony', 'type': 'BRAND', 'confidence': 0.98},
            {'text': 'products', 'type': 'OBJECT', 'confidence': 0.95},
            {'text': 'quarter', 'type': 'TIME_PERIOD', 'confidence': 0.90}
        ]
        
        model_fields = [
            {'name': 'brand_name', 'type': 'string', 'description': 'Product brand'},
            {'name': 'product_name', 'type': 'string', 'description': 'Product name'},
            {'name': 'launch_date', 'type': 'date', 'description': 'Launch date'},
            {'name': 'quarter_year', 'type': 'string', 'description': 'Quarter and year'}
        ]
        
        field_mapping = field_mapper.map_entities_to_fields(entities, model_fields)
        
        assert isinstance(field_mapping, dict)
        assert len(field_mapping) >= 2  # At least Sony and quarter should map
        
        # Check specific mappings
        assert 'Sony' in field_mapping
        assert field_mapping['Sony']['field_name'] == 'brand_name'
        
        # Quarter should map to quarter_year or launch_date
        assert 'quarter' in field_mapping
        mapped_field = field_mapping['quarter']['field_name']
        assert mapped_field in ['quarter_year', 'launch_date']
    
    def test_create_field_mapping_for_models(self, field_mapper):
        """
        RED: Test should FAIL - FieldMapper doesn't exist yet
        
        Test: Should create complete field mapping for relevant models
        """
        entities = [
            {'text': 'Sony', 'type': 'BRAND', 'confidence': 0.98},
            {'text': 'products', 'type': 'OBJECT', 'confidence': 0.95}
        ]
        
        relevant_models = [
            {'model_id': 'Product', 'relevance_score': 0.95, 'role': 'primary'},
            {'model_id': 'Campaign', 'relevance_score': 0.70, 'role': 'secondary'}
        ]
        
        complete_mapping = field_mapper.create_field_mapping_for_models(
            entities, 
            relevant_models
        )
        
        assert isinstance(complete_mapping, dict)
        assert 'Product' in complete_mapping
        assert 'Campaign' in complete_mapping
        
        # Each model should have field mappings
        product_mapping = complete_mapping['Product']
        assert isinstance(product_mapping, dict)
        assert len(product_mapping) > 0
    
    def test_validate_field_mapping(self, field_mapper):
        """
        RED: Test should FAIL - FieldMapper doesn't exist yet
        
        Test: Should validate field mappings for completeness
        """
        field_mapping = {
            'Sony': {'field_name': 'brand_name', 'confidence': 0.95},
            'products': {'field_name': 'product_name', 'confidence': 0.80}
        }
        
        validation_result = field_mapper.validate_field_mapping(field_mapping)
        
        assert isinstance(validation_result, dict)
        assert 'is_valid' in validation_result
        assert 'missing_entities' in validation_result
        assert 'low_confidence_mappings' in validation_result
        
        # Should be valid mapping
        assert validation_result['is_valid'] is True
        assert len(validation_result['missing_entities']) == 0
    
    def test_validate_field_mapping_with_issues(self, field_mapper):
        """
        RED: Test should FAIL - FieldMapper doesn't exist yet
        
        Test: Should identify issues in field mappings
        """
        field_mapping = {
            'Sony': {'field_name': 'brand_name', 'confidence': 0.95},
            'unknown_entity': {'field_name': 'unknown_field', 'confidence': 0.30}
        }
        
        validation_result = field_mapper.validate_field_mapping(field_mapping)
        
        # Should identify low confidence mapping
        assert len(validation_result['low_confidence_mappings']) > 0
        assert 'unknown_entity' in validation_result['low_confidence_mappings']
    
    @pytest.mark.unit
    def test_field_mapper_initialization(self):
        """
        RED: Test should FAIL - FieldMapper doesn't exist yet
        
        Test: Should initialize properly with default clients
        """
        mapper = FieldMapper()
        
        assert mapper is not None
        assert hasattr(mapper, 'mcp_client')
        assert hasattr(mapper, 'claude_client')
    
    @pytest.mark.integration
    def test_end_to_end_field_mapping(self, field_mapper):
        """
        RED: Test should FAIL - FieldMapper doesn't exist yet
        
        Test: Complete workflow from entities to field mappings
        """
        entities = [
            {'text': 'Sony', 'type': 'BRAND', 'confidence': 0.98},
            {'text': 'products', 'type': 'OBJECT', 'confidence': 0.95},
            {'text': 'Q1', 'type': 'TIME_PERIOD', 'confidence': 0.90}
        ]
        
        relevant_models = [
            {'model_id': 'Product', 'relevance_score': 0.95, 'role': 'primary'}
        ]
        
        # Complete field mapping workflow
        complete_mapping = field_mapper.create_field_mapping_for_models(
            entities, 
            relevant_models
        )
        
        # Validate the mapping
        validation_result = field_mapper.validate_field_mapping(
            complete_mapping['Product']
        )
        
        assert isinstance(complete_mapping, dict)
        assert 'Product' in complete_mapping
        assert validation_result['is_valid'] is True
        
        # Should have at least Sony mapped
        product_mapping = complete_mapping['Product']
        assert 'Sony' in product_mapping
        assert product_mapping['Sony']['field_name'] == 'brand_name'