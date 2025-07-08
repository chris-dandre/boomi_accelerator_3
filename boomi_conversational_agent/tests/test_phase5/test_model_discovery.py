"""
Test suite for ModelDiscovery agent - TDD Phase 5
Following Red-Green-Refactor cycle
"""
import pytest
from cli_agent.agents.model_discovery import ModelDiscovery
from tests.mocks.mock_mcp_client import MockMCPClient
from tests.mocks.mock_claude_client import MockClaudeClient

class TestModelDiscovery:
    """Test cases for ModelDiscovery agent"""
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client"""
        return MockMCPClient()
    
    @pytest.fixture
    def mock_claude_client(self):
        """Create mock Claude client"""
        return MockClaudeClient()
    
    @pytest.fixture
    def model_discovery(self, mock_mcp_client, mock_claude_client):
        """Create ModelDiscovery with mocked dependencies"""
        discovery = ModelDiscovery()
        discovery.mcp_client = mock_mcp_client
        discovery.claude_client = mock_claude_client
        return discovery
    
    def test_get_all_models(self, model_discovery, mock_mcp_client):
        """
        RED: Test should FAIL - ModelDiscovery doesn't exist yet
        
        Test: Should retrieve all available models from MCP client
        """
        models = model_discovery.get_all_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert mock_mcp_client.call_count == 1
        
        # Check model structure
        first_model = models[0]
        assert 'id' in first_model
        assert 'name' in first_model
        assert 'description' in first_model
    
    def test_find_relevant_models_product_query(self, model_discovery, mock_claude_client):
        """
        RED: Test should FAIL - ModelDiscovery doesn't exist yet
        
        Test: Should find Product model as most relevant for product queries
        """
        query_analysis = {
            'intent': 'COUNT',
            'entities': [
                {'text': 'products', 'type': 'OBJECT', 'confidence': 0.95}
            ],
            'query_type': 'SIMPLE'
        }
        
        relevant_models = model_discovery.find_relevant_models(query_analysis)
        
        assert isinstance(relevant_models, list)
        assert len(relevant_models) > 0
        assert mock_claude_client.call_count == 1
        
        # Primary model should be Product
        primary_model = relevant_models[0]
        assert primary_model['model_id'] == 'Product'
        assert primary_model['role'] == 'primary'
        assert primary_model['relevance_score'] > 0.8
    
    def test_find_relevant_models_campaign_query(self, model_discovery, mock_claude_client):
        """
        RED: Test should FAIL - ModelDiscovery doesn't exist yet
        
        Test: Should find Campaign model as most relevant for campaign queries
        """
        query_analysis = {
            'intent': 'ANALYZE',
            'entities': [
                {'text': 'campaign', 'type': 'OBJECT', 'confidence': 0.90}
            ],
            'query_type': 'SIMPLE'
        }
        
        relevant_models = model_discovery.find_relevant_models(query_analysis)
        
        primary_model = relevant_models[0]
        assert primary_model['model_id'] == 'Campaign'
        assert primary_model['role'] == 'primary'
    
    def test_find_relevant_models_comparison_query(self, model_discovery, mock_claude_client):
        """
        RED: Test should FAIL - ModelDiscovery doesn't exist yet
        
        Test: Should return multiple models for comparison queries
        """
        query_analysis = {
            'intent': 'COMPARE',
            'entities': [
                {'text': 'Sony', 'type': 'BRAND', 'confidence': 0.98},
                {'text': 'Samsung', 'type': 'BRAND', 'confidence': 0.98}
            ],
            'query_type': 'COMPLEX'
        }
        
        relevant_models = model_discovery.find_relevant_models(query_analysis)
        
        # Should return multiple models for complex comparison
        assert len(relevant_models) >= 2
        
        # Should have primary and secondary roles
        roles = [model['role'] for model in relevant_models]
        assert 'primary' in roles
        assert 'secondary' in roles
    
    def test_rank_models_by_relevance(self, model_discovery, mock_claude_client):
        """
        RED: Test should FAIL - ModelDiscovery doesn't exist yet
        
        Test: Should rank models using Claude LLM reasoning
        """
        available_models = [
            {"id": "Product", "name": "Product", "description": "Product data"},
            {"id": "Campaign", "name": "Campaign", "description": "Campaign data"}
        ]
        
        query_context = "How many products are launching this quarter?"
        
        ranked_models = model_discovery.rank_models_by_relevance(
            available_models, 
            query_context
        )
        
        assert isinstance(ranked_models, list)
        assert len(ranked_models) > 0
        assert mock_claude_client.call_count == 1
        
        # Should include relevance scores
        for model in ranked_models:
            assert 'relevance_score' in model
            assert 0.0 <= model['relevance_score'] <= 1.0
            assert 'reasoning' in model
    
    def test_filter_models_by_threshold(self, model_discovery):
        """
        RED: Test should FAIL - ModelDiscovery doesn't exist yet
        
        Test: Should filter models below relevance threshold
        """
        ranked_models = [
            {"model_id": "Product", "relevance_score": 0.95, "role": "primary"},
            {"model_id": "Campaign", "relevance_score": 0.75, "role": "secondary"},
            {"model_id": "Customer", "relevance_score": 0.45, "role": "tertiary"}
        ]
        
        # Filter with threshold 0.6
        filtered_models = model_discovery.filter_by_relevance_threshold(
            ranked_models, 
            threshold=0.6
        )
        
        assert len(filtered_models) == 2
        assert all(model['relevance_score'] >= 0.6 for model in filtered_models)
    
    @pytest.mark.unit
    def test_model_discovery_initialization(self):
        """
        RED: Test should FAIL - ModelDiscovery doesn't exist yet
        
        Test: Should initialize properly with default clients
        """
        discovery = ModelDiscovery()
        
        assert discovery is not None
        assert hasattr(discovery, 'mcp_client')
        assert hasattr(discovery, 'claude_client')
    
    @pytest.mark.integration
    def test_end_to_end_model_discovery(self, model_discovery):
        """
        RED: Test should FAIL - ModelDiscovery doesn't exist yet
        
        Test: Complete workflow from query analysis to ranked models
        """
        query_analysis = {
            'intent': 'COUNT',
            'entities': [
                {'text': 'Sony', 'type': 'BRAND', 'confidence': 0.98},
                {'text': 'products', 'type': 'OBJECT', 'confidence': 0.95},
                {'text': 'quarter', 'type': 'TIME_PERIOD', 'confidence': 0.90}
            ],
            'query_type': 'SIMPLE'
        }
        
        # Complete discovery workflow
        relevant_models = model_discovery.discover_models_for_query(query_analysis)
        
        assert isinstance(relevant_models, list)
        assert len(relevant_models) > 0
        
        # Should have Product as primary model
        primary_models = [m for m in relevant_models if m['role'] == 'primary']
        assert len(primary_models) == 1
        assert primary_models[0]['model_id'] == 'Product'