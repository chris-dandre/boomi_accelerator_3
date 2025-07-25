"""
DataRetrieval Agent - Enhanced with MCPAgentState and field_mappings support
Executes queries against Boomi DataHub and retrieves data
"""
from typing import Dict, Any, List, Optional
import time
import hashlib
import json
import copy
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import shared agent state
try:
    from shared.agent_state import MCPAgentState
except ImportError:
    # Fallback if shared state not available
    MCPAgentState = None

class DataRetrieval:
    """
    Execute queries against Boomi DataHub and retrieve data
    Handles query execution, caching, and result formatting
    """
    
    def __init__(self, mcp_client=None, claude_client=None):
        """
        Initialize DataRetrieval agent
        
        Args:
            mcp_client: Optional MCP client (will create default if None)
            claude_client: Optional Claude client (will create default if None)
        """
        self.mcp_client = mcp_client or self._create_default_mcp_client()
        self.claude_client = claude_client or self._create_default_claude_client()
        
        # Query cache for performance
        self.query_cache = {}
        
        # Default timeout for queries (in seconds)
        self.default_timeout = 30
        
        # Valid query types for validation
        self.valid_query_types = ['COUNT', 'LIST', 'COMPARE', 'ANALYZE']
    
    def _create_default_mcp_client(self):
        """Create default MCP client - placeholder for real implementation"""
        # This would import and create the real MCP client
        # For now, return None and expect it to be injected in tests
        return None
    
    def _create_default_claude_client(self):
        """Create default Claude client - placeholder for real implementation"""
        # This would create the real Claude API client
        # For now, return None and expect it to be injected in tests
        return None
    
    def execute_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute query against Boomi DataHub
        
        Args:
            query: Structured query from QueryBuilder
            
        Returns:
            Query result with data and metadata
        """
        start_time = time.time()
        
        # Validate query before execution
        validation_result = self._validate_query_for_execution(query)
        if not validation_result['is_valid']:
            return {
                'error': f"Query validation failed: {', '.join(validation_result['errors'])}",
                'query_type': query.get('query_type', 'UNKNOWN')
            }
        
        # Check cache if enabled
        if query.get('cache_enabled', False):
            cache_key = self._generate_cache_key(query)
            if cache_key in self.query_cache:
                cached_result = copy.deepcopy(self.query_cache[cache_key])
                cached_result['metadata']['cache_hit'] = True
                cached_result['metadata']['execution_time_ms'] = 0  # Cached results are instant
                return cached_result
        
        try:
            # Execute query via MCP client
            raw_result = self._execute_via_mcp(query)
            
            # Handle errors from MCP
            if 'error' in raw_result:
                return {
                    'error': raw_result['error'],
                    'query_type': query.get('query_type', 'UNKNOWN'),
                    'metadata': {
                        'execution_time_ms': (time.time() - start_time) * 1000,
                        'success': False
                    }
                }
            
            # Handle status errors from MCP
            if isinstance(raw_result, dict) and raw_result.get('status') == 'error':
                return {
                    'error': raw_result.get('error', 'MCP returned error status'),
                    'query_type': query.get('query_type', 'UNKNOWN'),
                    'metadata': {
                        'execution_time_ms': (time.time() - start_time) * 1000,
                        'success': False
                    }
                }
            
            # Transform and format result
            formatted_result = self._format_query_result(query, raw_result, start_time)
            
            # Cache result if enabled
            if query.get('cache_enabled', False):
                cache_key = self._generate_cache_key(query)
                self.query_cache[cache_key] = copy.deepcopy(formatted_result)
                formatted_result['metadata']['cache_hit'] = False
            
            return formatted_result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return {
                'error': f"Query execution failed: {str(e)}",
                'query_type': query.get('query_type', 'UNKNOWN'),
                'metadata': {
                    'execution_time_ms': execution_time,
                    'success': False
                }
            }
    
    def transform_raw_data(self, raw_data: List[Dict[str, Any]], 
                          field_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Transform raw MCP data using field mappings
        
        Args:
            raw_data: Raw data from MCP client
            field_mapping: Mapping from raw field names to standard names
            
        Returns:
            Transformed data with standardized field names
        """
        transformed_data = []
        
        for record in raw_data:
            transformed_record = {}
            
            # Apply field mappings
            for raw_field, standard_field in field_mapping.items():
                if raw_field in record:
                    transformed_record[standard_field] = record[raw_field]
            
            # Keep unmapped fields as-is
            for field, value in record.items():
                if field not in field_mapping and field not in transformed_record:
                    transformed_record[field] = value
            
            transformed_data.append(transformed_record)
        
        return transformed_data
    
    def _validate_query_for_execution(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Validate query before execution"""
        validation_result = {
            'is_valid': True,
            'errors': []
        }
        
        # Check required fields
        required_fields = ['query_type', 'model_id']
        for field in required_fields:
            if field not in query:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['is_valid'] = False
        
        # Validate query type
        if 'query_type' in query:
            if query['query_type'] not in self.valid_query_types:
                validation_result['errors'].append(f"Invalid query type: {query['query_type']}")
                validation_result['is_valid'] = False
        
        # Validate model_id
        if 'model_id' in query:
            if not query['model_id'] or not isinstance(query['model_id'], str):
                validation_result['errors'].append("model_id must be a non-empty string")
                validation_result['is_valid'] = False
        
        return validation_result
    
    def _execute_via_mcp(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query via MCP client"""
        if not self.mcp_client:
            raise ValueError("MCP client not configured")
        
        # Set timeout
        query_with_timeout = copy.deepcopy(query)
        if 'timeout' not in query_with_timeout:
            query_with_timeout['timeout'] = self.default_timeout
        
        return self.mcp_client.execute_query(query_with_timeout)
    
    def _format_query_result(self, query: Dict[str, Any], raw_result: Dict[str, Any], 
                           start_time: float) -> Dict[str, Any]:
        """Format raw query result into standardized structure"""
        execution_time = (time.time() - start_time) * 1000
        query_type = query['query_type']
        
        # Base result structure
        result = {
            'query_type': query_type,
            'metadata': {
                'execution_time_ms': round(execution_time, 2),
                'query_complexity': self._assess_query_complexity(query),
                'model_id': query['model_id'],
                'success': True
            }
        }
        
        # Format data based on query type
        if query_type == 'COUNT':
            # For COUNT queries, count the records returned by the LIST operation
            # Handle nested MCP response structure
            data_section = self._extract_data_section(raw_result)
            records = data_section.get('records', [])
            total_count = data_section.get('total_count', len(records))
            result['data'] = {
                'count': total_count
            }
            result['metadata']['record_count'] = total_count
            
        elif query_type == 'LIST':
            # Handle structured MCP response
            data_section = self._extract_data_section(raw_result)
            records = data_section.get('records', [])
            if not records and isinstance(raw_result, list):
                records = raw_result
            result['data'] = records
            result['metadata']['record_count'] = len(records)
            
        elif query_type == 'COMPARE':
            # Handle structured MCP response
            if isinstance(raw_result, dict) and 'data' in raw_result and 'records' in raw_result['data']:
                result['data'] = raw_result['data']['records']
            elif isinstance(raw_result, list):
                result['data'] = raw_result
            else:
                result['data'] = []
            result['metadata']['record_count'] = len(result['data'])
            result['metadata']['comparison_groups'] = len(result['data'])
            
        else:  # ANALYZE or other types
            # Handle structured MCP response
            if isinstance(raw_result, dict) and 'data' in raw_result and 'records' in raw_result['data']:
                result['data'] = raw_result['data']['records']
                result['metadata']['record_count'] = len(result['data'])
            elif isinstance(raw_result, list):
                result['data'] = raw_result
                result['metadata']['record_count'] = len(raw_result)
            elif isinstance(raw_result, dict):
                result['data'] = raw_result
                result['metadata']['record_count'] = 1
            else:
                result['data'] = {}
                result['metadata']['record_count'] = 0
        
        # Add filter information
        if 'filters' in query:
            result['metadata']['filters_applied'] = len(query['filters'])
        
        return result
    
    def _extract_data_section(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the data section from nested MCP response structure"""
        print(f"🔍 Data Extraction Debug - Raw result type: {type(raw_result)}")
        print(f"🔍 Data Extraction Debug - Raw result keys: {raw_result.keys() if isinstance(raw_result, dict) else 'Not a dict'}")
        
        # Handle MCP server response: {"result": {"data": {...}}}
        if isinstance(raw_result, dict):
            # First check if this is already the data section
            if 'records' in raw_result:
                print(f"🔍 Data Extraction Debug - Found records directly, count: {len(raw_result.get('records', []))}")
                return raw_result
            
            # Check for direct data key (from Boomi client)
            if 'data' in raw_result:
                data_section = raw_result['data']
                print(f"🔍 Data Extraction Debug - Found data section, type: {type(data_section)}")
                if isinstance(data_section, dict):
                    print(f"🔍 Data Extraction Debug - Data section keys: {data_section.keys()}")
                    if 'records' in data_section:
                        print(f"🔍 Data Extraction Debug - Found records in data section, count: {len(data_section.get('records', []))}")
                return data_section
                
            # Check for nested structure (from MCP server)
            if 'result' in raw_result and isinstance(raw_result['result'], dict):
                nested_result = raw_result['result']
                print(f"🔍 Data Extraction Debug - Found nested result, keys: {nested_result.keys()}")
                
                # Check for data in response_body (likely contains the actual records)
                if 'response_body' in nested_result:
                    response_body = nested_result['response_body']
                    print(f"🔍 Data Extraction Debug - Found response_body, type: {type(response_body)}")
                    
                    # If response_body is a string, try to parse it as JSON
                    if isinstance(response_body, str):
                        print(f"🔍 Data Extraction Debug - Response body content (first 200 chars): {response_body[:200]}")
                        try:
                            import json
                            parsed_body = json.loads(response_body)
                            print(f"🔍 Data Extraction Debug - Parsed response_body as JSON, keys: {parsed_body.keys() if isinstance(parsed_body, dict) else 'Not a dict'}")
                            if isinstance(parsed_body, dict) and 'records' in parsed_body:
                                print(f"🔍 Data Extraction Debug - Found records in parsed response_body, count: {len(parsed_body.get('records', []))}")
                                return parsed_body
                        except json.JSONDecodeError as e:
                            print(f"🔍 Data Extraction Debug - Failed to parse response_body as JSON: {e}")
                            # Try to check if it's XML and extract error message
                            if response_body.strip().startswith('<'):
                                print(f"🔍 Data Extraction Debug - Response appears to be XML, likely an error response")
                                # Return empty dict for now - the XML parsing should happen in Boomi client
                                return {'records': []}
                    
                    # If response_body is already a dict
                    elif isinstance(response_body, dict):
                        print(f"🔍 Data Extraction Debug - Response_body is dict, keys: {response_body.keys()}")
                        if 'records' in response_body:
                            print(f"🔍 Data Extraction Debug - Found records in response_body dict, count: {len(response_body.get('records', []))}")
                            return response_body
                
                if 'data' in nested_result:
                    data_section = nested_result['data']
                    print(f"🔍 Data Extraction Debug - Found nested data section, type: {type(data_section)}")
                    if isinstance(data_section, dict) and 'records' in data_section:
                        print(f"🔍 Data Extraction Debug - Found records in nested data, count: {len(data_section.get('records', []))}")
                    return data_section
                return nested_result
        
        print(f"🔍 Data Extraction Debug - No valid data structure found, returning empty dict")
        # Fallback to empty dict
        return {}
    
    def _assess_query_complexity(self, query: Dict[str, Any]) -> str:
        """Assess query complexity for metadata"""
        complexity_score = 0
        
        # Base complexity
        if query.get('query_type') == 'COUNT':
            complexity_score += 1
        elif query.get('query_type') == 'LIST':
            complexity_score += 2
        elif query.get('query_type') == 'COMPARE':
            complexity_score += 3
        elif query.get('query_type') == 'ANALYZE':
            complexity_score += 4
        
        # Add complexity for filters
        filter_count = len(query.get('filters', []))
        complexity_score += filter_count
        
        # Add complexity for grouping
        if 'grouping' in query:
            complexity_score += 2
        
        # Add complexity for multiple operations
        operation_count = len(query.get('operations', []))
        if operation_count > 1:
            complexity_score += operation_count - 1
        
        # Classify complexity
        if complexity_score <= 2:
            return 'simple'
        elif complexity_score <= 5:
            return 'moderate'
        else:
            return 'complex'
    
    def _generate_cache_key(self, query: Dict[str, Any]) -> str:
        """Generate cache key for query"""
        # Create a normalized version of the query for consistent caching
        normalized_query = {
            'query_type': query.get('query_type'),
            'model_id': query.get('model_id'),
            'filters': sorted(query.get('filters', []), key=lambda x: x.get('field', '')),
            'fields': sorted(query.get('fields', [])),
            'operations': sorted(query.get('operations', []))
        }
        
        # Add grouping if present
        if 'grouping' in query:
            normalized_query['grouping'] = query['grouping']
        
        # Generate hash
        query_string = json.dumps(normalized_query, sort_keys=True)
        return hashlib.md5(query_string.encode()).hexdigest()