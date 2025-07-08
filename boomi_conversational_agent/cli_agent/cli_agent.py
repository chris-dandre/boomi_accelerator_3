"""
CLI Agent - Phase 5 TDD Implementation
Command-line interface for conversational Boomi DataHub queries
"""
from typing import Dict, Any, List, Optional
import json
import time
from datetime import datetime

from cli_agent.pipeline.agent_pipeline import AgentPipeline

class CLIAgent:
    """
    Command-line interface for conversational Boomi DataHub queries
    Provides interactive and batch query processing capabilities
    """
    
    def __init__(self, mcp_client=None, claude_client=None):
        """
        Initialize CLI Agent
        
        Args:
            mcp_client: Optional MCP client for Boomi DataHub connection
            claude_client: Optional Claude client for LLM processing
        """
        # Create default clients if none provided
        if mcp_client is None:
            mcp_client = self._create_default_mcp_client()
        if claude_client is None:
            # Create default Claude client (real or mock based on availability)
            claude_client = self._create_default_claude_client()
            
        # Initialize the agent pipeline
        self.pipeline = AgentPipeline(
            mcp_client=mcp_client,
            claude_client=claude_client
        )
        
        # Session management
        self.session_history = []
        
        # Default configuration
        self.configuration = {
            'output_format': 'detailed',  # detailed, json, compact
            'verbose_mode': False,
            'cache_enabled': True,
            'max_history': 100,
            'display_timing': True
        }
        
        # CLI metadata
        self.version = "1.0.0"
        self.session_start_time = datetime.now()
    
    def _create_default_mcp_client(self):
        """Create default mock MCP client for testing/fallback"""
        try:
            from tests.mocks.mock_mcp_client import MockMCPClient
            return MockMCPClient()
        except ImportError:
            # Fallback if mock client not available
            return None
    
    def _create_default_claude_client(self):
        """Create default mock Claude client for testing/fallback"""
        try:
            from tests.mocks.mock_claude_client import MockClaudeClient
            return MockClaudeClient()
        except ImportError:
            # Fallback if mock client not available
            return None
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a single user query
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Formatted result with success status and response
        """
        start_time = time.time()
        
        # Validate input
        if not user_query or not user_query.strip():
            result = {
                'success': False,
                'error': 'Empty query provided. Please enter a valid question.',
                'execution_time': 0,
                'timestamp': datetime.now().isoformat()
            }
            self._add_to_history(user_query, result)
            return result
        
        try:
            # Process through pipeline
            pipeline_result = self.pipeline.process_query(
                user_query.strip(),
                enable_cache=self.configuration['cache_enabled']
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Format result for CLI
            if pipeline_result['success']:
                cli_result = {
                    'success': True,
                    'response': pipeline_result['response']['message'],
                    'response_type': pipeline_result['response']['response_type'],
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Add metadata if verbose mode
                if self.configuration['verbose_mode']:
                    cli_result['pipeline_metadata'] = pipeline_result['pipeline_metadata']
                    cli_result['detailed_timing'] = {
                        'total_time_ms': execution_time,
                        'pipeline_time_ms': pipeline_result['pipeline_metadata'].get('total_execution_time_ms', 0)
                    }
            else:
                cli_result = {
                    'success': False,
                    'error': pipeline_result.get('error', 'Unknown error occurred'),
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add to session history
            self._add_to_history(user_query, cli_result)
            
            return cli_result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_result = {
                'success': False,
                'error': f'CLI processing error: {str(e)}',
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
            self._add_to_history(user_query, error_result)
            return error_result
    
    def start_interactive_session(self):
        """
        Start interactive CLI session
        """
        print("🤖 Boomi DataHub Conversational Agent")
        print("=" * 50)
        print("Ask questions about your Boomi DataHub data in natural language.")
        print("Type 'help' for commands, 'exit' to quit.\n")
        
        while True:
            try:
                user_input = input("❓ Your question: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\n👋 Goodbye! Thank you for using Boomi DataHub Conversational Agent.")
                    break
                elif user_input.lower() == 'help':
                    print(self.get_help())
                    continue
                elif user_input.lower() == 'status':
                    status = self.get_status()
                    print(self.format_output({'success': True, 'data': status}))
                    continue
                elif user_input.lower() == 'history':
                    history = self.get_session_history()
                    print(f"\n📝 Session History ({len(history)} queries):")
                    for i, entry in enumerate(history[-5:], 1):  # Show last 5
                        status_icon = "✅" if entry['success'] else "❌"
                        print(f"{i}. {status_icon} {entry['query']}")
                    continue
                elif user_input.lower().startswith('config'):
                    self._handle_config_command(user_input)
                    continue
                
                # Process regular query
                result = self.process_query(user_input)
                formatted_output = self.format_output(result)
                print(formatted_output)
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
    
    def process_batch_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple queries in batch
        
        Args:
            queries: List of user queries
            
        Returns:
            List of results for each query
        """
        results = []
        
        for query in queries:
            result = self.process_query(query)
            batch_result = {
                'query': query,
                'success': result['success'],
                'response': result.get('response', result.get('error', '')),
                'execution_time': result['execution_time'],
                'timestamp': result['timestamp']
            }
            
            if self.configuration['verbose_mode'] and 'pipeline_metadata' in result:
                batch_result['metadata'] = result['pipeline_metadata']
            
            results.append(batch_result)
        
        return results
    
    def get_help(self) -> str:
        """
        Get help information for CLI usage
        
        Returns:
            Help text with available commands and examples
        """
        help_text = """
🤖 Boomi DataHub Conversational Agent - Help

NATURAL LANGUAGE QUERIES:
You can ask questions in plain English about your Boomi DataHub data:

Examples:
• "How many Sony products are there?"
• "Show me Samsung products launched in Q1"
• "Compare Sony and Samsung product counts"
• "List all marketing campaigns"

SPECIAL COMMANDS:
• help       - Show this help message
• status     - Show system and pipeline status
• history    - Show recent query history
• config     - Show current configuration
• config set <key> <value> - Update configuration
• exit/quit  - Exit the agent

CONFIGURATION OPTIONS:
• output_format: detailed, json, compact
• verbose_mode: true, false
• cache_enabled: true, false

QUERY TYPES SUPPORTED:
• COUNT - "How many products..."
• LIST - "Show me products..."
• COMPARE - "Compare brands..."
• ANALYZE - "Analyze performance..."

For more information, visit the documentation or contact support.
        """
        return help_text.strip()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current system status
        
        Returns:
            Status information including pipeline health
        """
        pipeline_status = self.pipeline.get_pipeline_status()
        validation_result = self.pipeline.validate_configuration()
        
        return {
            'pipeline_status': 'healthy' if validation_result['is_valid'] else 'degraded',
            'connection_status': 'connected' if pipeline_status['agents']['model_discovery']['mcp_client'] else 'mock',
            'agent_health': 'all_operational',
            'session_info': {
                'queries_processed': len(self.session_history),
                'session_duration': str(datetime.now() - self.session_start_time).split('.')[0],
                'cache_size': pipeline_status['pipeline']['cache_size']
            },
            'configuration': self.configuration.copy(),
            'version': self.version,
            'pipeline_version': pipeline_status['version']
        }
    
    def get_session_history(self) -> List[Dict[str, Any]]:
        """
        Get session query history
        
        Returns:
            List of historical query entries
        """
        return self.session_history.copy()
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get current CLI configuration
        
        Returns:
            Current configuration settings
        """
        return self.configuration.copy()
    
    def update_configuration(self, new_config: Dict[str, Any]) -> bool:
        """
        Update CLI configuration
        
        Args:
            new_config: Dictionary with configuration updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate configuration keys
            valid_keys = set(self.configuration.keys())
            for key in new_config:
                if key not in valid_keys:
                    return False
            
            # Update configuration
            self.configuration.update(new_config)
            return True
            
        except Exception:
            return False
    
    def format_output(self, result: Dict[str, Any]) -> str:
        """
        Format output according to current configuration
        
        Args:
            result: Query result to format
            
        Returns:
            Formatted output string
        """
        output_format = self.configuration['output_format']
        
        if output_format == 'json':
            return json.dumps(result, indent=2, default=str)
        
        elif output_format == 'compact':
            if result['success']:
                return f"✅ {result['response']}"
            else:
                return f"❌ {result.get('error', 'Unknown error')}"
        
        else:  # detailed format (default)
            if result['success']:
                output = f"\n✅ **Response:**\n{result['response']}\n"
                
                if self.configuration['display_timing']:
                    exec_time = result.get('execution_time', 0)
                    output += f"⏱️  Execution time: {exec_time:.1f}ms\n"
                
                if self.configuration['verbose_mode'] and 'pipeline_metadata' in result:
                    metadata = result['pipeline_metadata']
                    output += f"\n📊 **Pipeline Details:**\n"
                    output += f"• Query type: {metadata.get('query_analysis', {}).get('intent', 'N/A')}\n"
                    output += f"• Primary model: {metadata.get('model_discovery', {}).get('primary_model', 'N/A')}\n"
                    output += f"• Entities mapped: {len(metadata.get('field_mapping', {}).get('mapped_entities', []))}\n"
                    output += f"• Total pipeline time: {metadata.get('total_execution_time_ms', 0):.1f}ms\n"
                
                return output
            else:
                output = f"\n❌ **Error:**\n{result.get('error', 'Unknown error')}\n"
                
                if self.configuration['display_timing']:
                    exec_time = result.get('execution_time', 0)
                    output += f"⏱️  Execution time: {exec_time:.1f}ms\n"
                
                return output
    
    def _add_to_history(self, query: str, result: Dict[str, Any]):
        """Add query and result to session history"""
        history_entry = {
            'query': query,
            'success': result['success'],
            'timestamp': result['timestamp'],
            'execution_time': result['execution_time']
        }
        
        if result['success']:
            history_entry['response_type'] = result.get('response_type', 'UNKNOWN')
        else:
            history_entry['error'] = result.get('error', 'Unknown error')
        
        self.session_history.append(history_entry)
        
        # Limit history size
        max_history = self.configuration['max_history']
        if len(self.session_history) > max_history:
            self.session_history = self.session_history[-max_history:]
    
    def _handle_config_command(self, command: str):
        """Handle configuration commands"""
        parts = command.split()
        
        if len(parts) == 1:  # Just 'config'
            config = self.get_configuration()
            print("\n⚙️  **Current Configuration:**")
            for key, value in config.items():
                print(f"• {key}: {value}")
        
        elif len(parts) == 4 and parts[1] == 'set':  # 'config set key value'
            key = parts[2]
            value = parts[3]
            
            # Convert string values to appropriate types
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            
            new_config = {key: value}
            if self.update_configuration(new_config):
                print(f"✅ Configuration updated: {key} = {value}")
            else:
                print(f"❌ Invalid configuration key: {key}")
        
        else:
            print("❌ Invalid config command. Use 'config' or 'config set <key> <value>'")

# Main entry point for CLI usage
def main():
    """Main entry point for CLI application"""
    cli_agent = CLIAgent()
    cli_agent.start_interactive_session()

if __name__ == "__main__":
    main()