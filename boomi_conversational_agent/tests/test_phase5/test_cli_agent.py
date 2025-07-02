"""
Test suite for CLI Agent - TDD Phase 5
Following Red-Green-Refactor cycle
"""
import pytest
from unittest.mock import patch, Mock
from cli_agent.cli_agent import CLIAgent
from tests.mocks.mock_mcp_client import MockMCPClient
from tests.mocks.mock_claude_client import MockClaudeClient

class TestCLIAgent:
    """Test cases for CLI Agent interface"""
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client"""
        return MockMCPClient()
    
    @pytest.fixture
    def mock_claude_client(self):
        """Create mock Claude client"""
        return MockClaudeClient()
    
    @pytest.fixture
    def cli_agent(self, mock_mcp_client, mock_claude_client):
        """Create CLI Agent with mocked dependencies"""
        agent = CLIAgent(
            mcp_client=mock_mcp_client,
            claude_client=mock_claude_client
        )
        return agent
    
    def test_process_single_query(self, cli_agent):
        """
        RED: Test should FAIL - CLIAgent doesn't exist yet
        
        Test: Should process single user query and return response
        """
        user_query = "How many Sony products are there?"
        
        result = cli_agent.process_query(user_query)
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'response' in result
        assert 'execution_time' in result
        
        assert result['success'] is True
        assert 'Sony' in result['response']
        assert isinstance(result['execution_time'], (int, float))
    
    def test_interactive_session(self, cli_agent):
        """
        RED: Test should FAIL - CLIAgent doesn't exist yet
        
        Test: Should handle interactive session with multiple queries
        """
        # Mock user input for interactive session
        queries = [
            "How many Sony products are there?",
            "Show me Samsung products",
            "exit"
        ]
        
        with patch('builtins.input', side_effect=queries):
            with patch('builtins.print') as mock_print:
                cli_agent.start_interactive_session()
        
        # Should have processed queries and printed responses
        assert mock_print.call_count >= 3  # Welcome, responses, goodbye
    
    def test_batch_query_processing(self, cli_agent):
        """
        RED: Test should FAIL - CLIAgent doesn't exist yet
        
        Test: Should process multiple queries in batch
        """
        queries = [
            "How many Sony products are there?",
            "Compare Sony and Samsung product counts",
            "Show me product launches in Q1"
        ]
        
        results = cli_agent.process_batch_queries(queries)
        
        assert isinstance(results, list)
        assert len(results) == 3
        
        for i, result in enumerate(results):
            assert isinstance(result, dict)
            assert 'query' in result
            assert 'success' in result
            assert 'response' in result
            assert result['query'] == queries[i]
            assert result['success'] is True
    
    def test_error_handling_in_cli(self, cli_agent):
        """
        RED: Test should FAIL - CLIAgent doesn't exist yet
        
        Test: Should handle errors gracefully in CLI interface
        """
        # Empty query should be handled gracefully
        result = cli_agent.process_query("")
        
        assert isinstance(result, dict)
        assert result['success'] is False
        assert 'error' in result
        assert 'empty query' in result['error'].lower() or 'invalid query' in result['error'].lower()
    
    def test_help_command(self, cli_agent):
        """
        RED: Test should FAIL - CLIAgent doesn't exist yet
        
        Test: Should provide help information
        """
        help_info = cli_agent.get_help()
        
        assert isinstance(help_info, str)
        assert len(help_info) > 0
        assert 'help' in help_info.lower()
        assert 'command' in help_info.lower() or 'query' in help_info.lower()
    
    def test_status_command(self, cli_agent):
        """
        RED: Test should FAIL - CLIAgent doesn't exist yet
        
        Test: Should provide system status information
        """
        status = cli_agent.get_status()
        
        assert isinstance(status, dict)
        assert 'pipeline_status' in status
        assert 'connection_status' in status
        assert 'agent_health' in status
        
        # Pipeline should be healthy with mock clients
        assert status['pipeline_status'] == 'healthy'
        assert status['connection_status'] == 'connected'
    
    def test_session_history_tracking(self, cli_agent):
        """
        RED: Test should FAIL - CLIAgent doesn't exist yet
        
        Test: Should track session history
        """
        queries = [
            "How many products are there?",
            "Show me Sony products"
        ]
        
        # Process queries
        for query in queries:
            cli_agent.process_query(query)
        
        # Get history
        history = cli_agent.get_session_history()
        
        assert isinstance(history, list)
        assert len(history) == 2
        
        for i, entry in enumerate(history):
            assert 'query' in entry
            assert 'timestamp' in entry
            assert 'success' in entry
            assert entry['query'] == queries[i]
    
    def test_configuration_management(self, cli_agent):
        """
        RED: Test should FAIL - CLIAgent doesn't exist yet
        
        Test: Should manage CLI configuration
        """
        # Test getting current config
        config = cli_agent.get_configuration()
        
        assert isinstance(config, dict)
        assert 'output_format' in config
        assert 'verbose_mode' in config
        assert 'cache_enabled' in config
        
        # Test updating config
        new_config = {
            'output_format': 'json',
            'verbose_mode': True,
            'cache_enabled': False
        }
        
        success = cli_agent.update_configuration(new_config)
        assert success is True
        
        # Verify config was updated
        updated_config = cli_agent.get_configuration()
        assert updated_config['output_format'] == 'json'
        assert updated_config['verbose_mode'] is True
        assert updated_config['cache_enabled'] is False
    
    def test_output_formatting(self, cli_agent):
        """
        RED: Test should FAIL - CLIAgent doesn't exist yet
        
        Test: Should format output according to configuration
        """
        query = "How many Sony products are there?"
        
        # Test default formatting
        result = cli_agent.process_query(query)
        formatted_output = cli_agent.format_output(result)
        
        assert isinstance(formatted_output, str)
        assert len(formatted_output) > 0
        
        # Test JSON formatting
        cli_agent.update_configuration({'output_format': 'json'})
        json_output = cli_agent.format_output(result)
        
        assert isinstance(json_output, str)
        assert '{' in json_output and '}' in json_output  # Should look like JSON
    
    def test_verbose_mode(self, cli_agent):
        """
        RED: Test should FAIL - CLIAgent doesn't exist yet
        
        Test: Should provide detailed output in verbose mode
        """
        query = "How many Sony products are there?"
        
        # Enable verbose mode
        cli_agent.update_configuration({'verbose_mode': True})
        
        result = cli_agent.process_query(query)
        verbose_output = cli_agent.format_output(result)
        
        # Verbose output should include more details
        assert 'execution time' in verbose_output.lower() or 'pipeline details' in verbose_output.lower()
        assert len(verbose_output) > 100  # Should be reasonably detailed
    
    @pytest.mark.unit
    def test_cli_agent_initialization(self):
        """
        RED: Test should FAIL - CLIAgent doesn't exist yet
        
        Test: Should initialize CLI agent with default configuration
        """
        agent = CLIAgent()
        
        assert agent is not None
        assert hasattr(agent, 'pipeline')
        assert hasattr(agent, 'session_history')
        assert hasattr(agent, 'configuration')
    
    @pytest.mark.integration
    def test_end_to_end_cli_interaction(self, cli_agent):
        """
        RED: Test should FAIL - CLIAgent doesn't exist yet
        
        Test: Complete CLI interaction workflow
        """
        # Test status check
        status = cli_agent.get_status()
        assert status['pipeline_status'] == 'healthy'
        
        # Test help
        help_info = cli_agent.get_help()
        assert len(help_info) > 0
        
        # Test configuration
        cli_agent.update_configuration({
            'output_format': 'detailed',
            'verbose_mode': True,
            'cache_enabled': True
        })
        
        # Process various query types
        test_queries = [
            "How many Sony products are there?",
            "Show me Samsung products", 
            "Compare Sony and Samsung product counts",
            "List product launches in Q1"
        ]
        
        all_successful = True
        for query in test_queries:
            result = cli_agent.process_query(query)
            if not result.get('success', False):
                all_successful = False
                break
        
        assert all_successful is True
        
        # Verify session history
        history = cli_agent.get_session_history()
        assert len(history) == len(test_queries)
        
        # Test batch processing
        batch_results = cli_agent.process_batch_queries(test_queries[:2])
        assert len(batch_results) == 2
        assert all(r['success'] for r in batch_results)
        
        # Verify final configuration
        final_config = cli_agent.get_configuration()
        assert final_config['verbose_mode'] is True
        assert final_config['cache_enabled'] is True