"""
Test suite for AgentPipeline - TDD Phase 5
Following Red-Green-Refactor cycle
"""
import pytest
from cli_agent.pipeline.agent_pipeline import AgentPipeline
from tests.mocks.mock_mcp_client import MockMCPClient
from tests.mocks.mock_claude_client import MockClaudeClient

class TestAgentPipeline:
    """Test cases for AgentPipeline orchestration"""
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client"""
        return MockMCPClient()
    
    @pytest.fixture
    def mock_claude_client(self):
        """Create mock Claude client"""
        return MockClaudeClient()
    
    @pytest.fixture
    def agent_pipeline(self, mock_mcp_client, mock_claude_client):
        """Create AgentPipeline with mocked dependencies"""
        pipeline = AgentPipeline(
            mcp_client=mock_mcp_client,
            claude_client=mock_claude_client
        )
        return pipeline
    
    def test_simple_count_query_pipeline(self, agent_pipeline):
        """
        RED: Test should FAIL - AgentPipeline doesn't exist yet
        
        Test: Should process simple count query through full pipeline
        """
        user_query = "How many Sony products are there?"
        
        result = agent_pipeline.process_query(user_query)
        
        assert isinstance(result, dict)
        assert 'response' in result
        assert 'pipeline_metadata' in result
        assert 'success' in result
        
        assert result['success'] is True
        assert 'Sony' in result['response']['message']
        assert result['response']['response_type'] == 'COUNT'
        
        # Should have metadata from each stage
        metadata = result['pipeline_metadata']
        assert 'query_analysis' in metadata
        assert 'model_discovery' in metadata
        assert 'field_mapping' in metadata
        assert 'query_building' in metadata
        assert 'data_retrieval' in metadata
        assert 'response_generation' in metadata
    
    def test_filtered_list_query_pipeline(self, agent_pipeline):
        """
        RED: Test should FAIL - AgentPipeline doesn't exist yet
        
        Test: Should process filtered list query through full pipeline
        """
        user_query = "Show me Sony products"
        
        result = agent_pipeline.process_query(user_query)
        
        assert result['success'] is True
        assert result['response']['response_type'] == 'LIST'
        assert 'Sony' in result['response']['message']
        
        # Should have discovered Product model
        discovery_metadata = result['pipeline_metadata']['model_discovery']
        assert discovery_metadata['primary_model'] == 'Product'
    
    def test_comparison_query_pipeline(self, agent_pipeline):
        """
        RED: Test should FAIL - AgentPipeline doesn't exist yet
        
        Test: Should process comparison query through full pipeline
        """
        user_query = "Compare Sony and Samsung product counts"
        
        result = agent_pipeline.process_query(user_query)
        
        assert result['success'] is True
        assert result['response']['response_type'] == 'COMPARE'
        assert 'Sony' in result['response']['message']
        assert 'Samsung' in result['response']['message']
        
        # Should have mapped both brands
        field_metadata = result['pipeline_metadata']['field_mapping']
        assert 'Sony' in field_metadata['mapped_entities']
        assert 'Samsung' in field_metadata['mapped_entities']
    
    def test_pipeline_error_handling(self, agent_pipeline):
        """
        RED: Test should FAIL - AgentPipeline doesn't exist yet
        
        Test: Should handle errors gracefully in pipeline
        """
        # Invalid query that should cause errors
        user_query = ""
        
        result = agent_pipeline.process_query(user_query)
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert result['success'] is False
        assert 'error' in result
        assert 'pipeline_metadata' in result
    
    def test_pipeline_stage_timing(self, agent_pipeline):
        """
        RED: Test should FAIL - AgentPipeline doesn't exist yet
        
        Test: Should track timing for each pipeline stage
        """
        user_query = "How many products are there?"
        
        result = agent_pipeline.process_query(user_query)
        
        assert result['success'] is True
        
        # Each stage should have timing information
        metadata = result['pipeline_metadata']
        stages = ['query_analysis', 'model_discovery', 'field_mapping', 
                 'query_building', 'data_retrieval', 'response_generation']
        
        for stage in stages:
            assert stage in metadata
            assert 'execution_time_ms' in metadata[stage]
            assert isinstance(metadata[stage]['execution_time_ms'], (int, float))
            assert metadata[stage]['execution_time_ms'] >= 0
    
    def test_pipeline_with_user_context(self, agent_pipeline):
        """
        RED: Test should FAIL - AgentPipeline doesn't exist yet
        
        Test: Should handle user context throughout pipeline
        """
        user_query = "How many Sony products launched in Q1?"
        user_context = {
            'role': 'marketing_manager',
            'experience_level': 'intermediate'
        }
        
        result = agent_pipeline.process_query(user_query, user_context=user_context)
        
        assert result['success'] is True
        assert 'user_context' in result['pipeline_metadata']
        assert result['pipeline_metadata']['user_context'] == user_context
    
    def test_pipeline_caching(self, agent_pipeline):
        """
        RED: Test should FAIL - AgentPipeline doesn't exist yet
        
        Test: Should support query result caching
        """
        user_query = "How many products are there?"
        
        # First execution
        result1 = agent_pipeline.process_query(user_query, enable_cache=True)
        first_time = result1['pipeline_metadata']['total_execution_time_ms']
        
        # Second execution (should be cached)
        result2 = agent_pipeline.process_query(user_query, enable_cache=True)
        second_time = result2['pipeline_metadata']['total_execution_time_ms']
        
        assert result1['success'] is True
        assert result2['success'] is True
        assert result1['response']['message'] == result2['response']['message']
        
        # Second execution should be faster due to caching
        assert second_time <= first_time
    
    def test_get_pipeline_status(self, agent_pipeline):
        """
        RED: Test should FAIL - AgentPipeline doesn't exist yet
        
        Test: Should provide pipeline status and health information
        """
        status = agent_pipeline.get_pipeline_status()
        
        assert isinstance(status, dict)
        assert 'agents' in status
        assert 'health' in status
        assert 'version' in status
        
        # Should have status for each agent
        agents = status['agents']
        expected_agents = ['query_analyzer', 'model_discovery', 'field_mapper', 
                          'query_builder', 'data_retrieval', 'response_generator']
        
        for agent in expected_agents:
            assert agent in agents
            assert 'status' in agents[agent]
    
    def test_validate_pipeline_configuration(self, agent_pipeline):
        """
        RED: Test should FAIL - AgentPipeline doesn't exist yet
        
        Test: Should validate pipeline configuration
        """
        validation_result = agent_pipeline.validate_configuration()
        
        assert isinstance(validation_result, dict)
        assert 'is_valid' in validation_result
        assert 'errors' in validation_result
        assert 'warnings' in validation_result
        
        # With mock clients, should be valid
        assert validation_result['is_valid'] is True
        assert len(validation_result['errors']) == 0
    
    @pytest.mark.unit
    def test_pipeline_initialization(self):
        """
        RED: Test should FAIL - AgentPipeline doesn't exist yet
        
        Test: Should initialize pipeline with all agents
        """
        pipeline = AgentPipeline()
        
        assert pipeline is not None
        assert hasattr(pipeline, 'query_analyzer')
        assert hasattr(pipeline, 'model_discovery')
        assert hasattr(pipeline, 'field_mapper')
        assert hasattr(pipeline, 'query_builder')
        assert hasattr(pipeline, 'data_retrieval')
        assert hasattr(pipeline, 'response_generator')
    
    @pytest.mark.integration
    def test_end_to_end_pipeline_execution(self, agent_pipeline):
        """
        RED: Test should FAIL - AgentPipeline doesn't exist yet
        
        Test: Complete end-to-end pipeline execution with detailed validation
        """
        user_query = "How many Sony products were launched in Q1 2024?"
        user_context = {
            'role': 'executive',
            'experience_level': 'expert',
            'preferred_detail_level': 'summary'
        }
        
        # Execute full pipeline
        result = agent_pipeline.process_query(
            user_query, 
            user_context=user_context,
            enable_cache=True
        )
        
        # Validate top-level result
        assert isinstance(result, dict)
        assert result['success'] is True
        assert 'response' in result
        assert 'pipeline_metadata' in result
        
        # Validate response structure
        response = result['response']
        assert 'message' in response
        assert 'response_type' in response
        assert 'metadata' in response
        assert response['response_type'] == 'COUNT'
        assert 'Sony' in response['message']
        
        # Validate pipeline metadata
        pipeline_metadata = result['pipeline_metadata']
        assert 'total_execution_time_ms' in pipeline_metadata
        assert pipeline_metadata['total_execution_time_ms'] > 0
        
        # Validate each stage metadata
        stages = ['query_analysis', 'model_discovery', 'field_mapping', 
                 'query_building', 'data_retrieval', 'response_generation']
        
        for stage in stages:
            assert stage in pipeline_metadata
            stage_metadata = pipeline_metadata[stage]
            assert 'execution_time_ms' in stage_metadata
            assert 'success' in stage_metadata
            assert stage_metadata['success'] is True
        
        # Validate query analysis stage
        query_analysis = pipeline_metadata['query_analysis']
        assert 'intent' in query_analysis
        assert 'entities' in query_analysis
        assert query_analysis['intent'] == 'COUNT'
        
        # Validate model discovery stage
        model_discovery = pipeline_metadata['model_discovery']
        assert 'primary_model' in model_discovery
        assert 'relevant_models' in model_discovery
        assert model_discovery['primary_model'] == 'Product'
        
        # Validate field mapping stage
        field_mapping = pipeline_metadata['field_mapping']
        assert 'mapped_entities' in field_mapping
        assert len(field_mapping['mapped_entities']) > 0
        
        # Validate query building stage
        query_building = pipeline_metadata['query_building']
        assert 'query_type' in query_building
        assert 'filters_applied' in query_building
        assert query_building['query_type'] == 'COUNT'
        
        # Validate data retrieval stage
        data_retrieval = pipeline_metadata['data_retrieval']
        assert 'record_count' in data_retrieval
        assert 'query_complexity' in data_retrieval
        
        # Validate response generation stage
        response_generation = pipeline_metadata['response_generation']
        assert 'personalization_applied' in response_generation
        assert response_generation['personalization_applied'] is True