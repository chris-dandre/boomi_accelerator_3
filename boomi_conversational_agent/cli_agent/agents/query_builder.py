"""
QueryBuilder Agent - Phase 5 TDD Implementation
Builds executable queries from analysis and field mappings
"""
from typing import Dict, Any, List, Optional
import copy

class QueryBuilder:
    """
    Build executable queries for Boomi DataHub
    Converts query analysis and field mappings into structured queries
    """
    
    def __init__(self, mcp_client=None, claude_client=None):
        """
        Initialize QueryBuilder agent
        
        Args:
            mcp_client: Optional MCP client (will create default if None)
            claude_client: Optional Claude client (will create default if None)
        """
        self.mcp_client = mcp_client or self._create_default_mcp_client()
        self.claude_client = claude_client or self._create_default_claude_client()
        
        # Valid query types
        self.valid_query_types = ['COUNT', 'LIST', 'COMPARE', 'ANALYZE']
        
        # Valid operators
        self.valid_operators = ['equals', 'contains', 'greater_than', 'less_than', 'in', 'between']
    
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
    
    def build_query(self, query_analysis: Dict[str, Any], 
                   field_mapping: Dict[str, Any], 
                   model_id: str) -> Dict[str, Any]:
        """
        Build executable query from analysis and field mappings
        
        Args:
            query_analysis: Result from QueryAnalyzer
            field_mapping: Result from FieldMapper
            model_id: Target model ID
            
        Returns:
            Structured query ready for execution
        """
        intent = query_analysis.get('intent', 'UNKNOWN')
        entities = query_analysis.get('entities', [])
        query_type = query_analysis.get('query_type', 'SIMPLE')
        
        # Build base query structure
        query = {
            'query_type': intent,
            'model_id': model_id,
            'operations': self._determine_operations(intent),
            'filters': [],
            'fields': [],
            'metadata': {
                'original_intent': intent,
                'complexity': query_type,
                'entity_count': len(entities)
            }
        }
        
        # Add filters based on field mappings
        print(f"🔧 Query Builder: Constructing filters from field mappings...")
        filters = self._build_filters(field_mapping)
        query['filters'] = filters
        print(f"   🎯 Filters created: {len(filters)} filter(s)")
        for i, filter_item in enumerate(filters, 1):
            field = filter_item.get('field', 'Unknown')
            operator = filter_item.get('operator', 'Unknown')
            value = filter_item.get('value', 'Unknown')
            confidence = filter_item.get('confidence', 0)
            print(f"      {i}. {field} {operator} '{value}' (confidence: {confidence:.2f})")
        
        # Add grouping for comparison queries
        if intent == 'COMPARE':
            grouping = self._build_grouping(field_mapping)
            if grouping:
                query['grouping'] = grouping
        
        # Add fields to select
        query['fields'] = self._determine_fields(intent, field_mapping, model_id)
        
        return query
    
    def validate_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate query structure and content
        
        Args:
            query: Query structure to validate
            
        Returns:
            Validation result with is_valid and errors
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        required_fields = ['query_type', 'model_id', 'operations']
        for field in required_fields:
            if field not in query:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['is_valid'] = False
        
        # Validate query_type
        if 'query_type' in query:
            if query['query_type'] not in self.valid_query_types:
                validation_result['errors'].append(f"Invalid query_type: {query['query_type']}")
                validation_result['is_valid'] = False
        
        # Validate model_id
        if 'model_id' in query:
            if not query['model_id'] or not isinstance(query['model_id'], str):
                validation_result['errors'].append("model_id must be a non-empty string")
                validation_result['is_valid'] = False
        
        # Validate operations
        if 'operations' in query:
            if not query['operations'] or not isinstance(query['operations'], list):
                validation_result['errors'].append("operations must be a non-empty list")
                validation_result['is_valid'] = False
        
        # Validate filters structure
        if 'filters' in query:
            for i, filter_item in enumerate(query['filters']):
                if not isinstance(filter_item, dict):
                    validation_result['errors'].append(f"Filter {i} must be a dictionary")
                    validation_result['is_valid'] = False
                    continue
                
                required_filter_fields = ['field', 'operator', 'value']
                for field in required_filter_fields:
                    if field not in filter_item:
                        validation_result['errors'].append(f"Filter {i} missing field: {field}")
                        validation_result['is_valid'] = False
                
                if 'operator' in filter_item and filter_item['operator'] not in self.valid_operators:
                    validation_result['warnings'].append(f"Filter {i} uses non-standard operator: {filter_item['operator']}")
        
        return validation_result
    
    def optimize_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize query for performance
        
        Args:
            query: Query to optimize
            
        Returns:
            Optimized query
        """
        optimized_query = copy.deepcopy(query)
        
        # Remove duplicate filters
        if 'filters' in optimized_query:
            unique_filters = []
            seen_filters = set()
            
            for filter_item in optimized_query['filters']:
                filter_key = (filter_item['field'], filter_item['operator'], str(filter_item['value']))
                if filter_key not in seen_filters:
                    unique_filters.append(filter_item)
                    seen_filters.add(filter_key)
            
            optimized_query['filters'] = unique_filters
        
        # Optimize field selection for COUNT queries
        if optimized_query.get('query_type') == 'COUNT':
            # For count queries, ensure we have at least one valid field (not '*')
            if not optimized_query.get('fields') or optimized_query.get('fields') == ['*']:
                # Get common fields for the model
                model_id = optimized_query.get('model_id', '')
                common_fields = self._get_common_fields_for_model(model_id)
                if common_fields:
                    optimized_query['fields'] = [common_fields[0]]  # Use first valid field
                else:
                    # Keep existing fields if any, don't use '*'
                    if not optimized_query.get('fields'):
                        optimized_query['fields'] = []
        
        # Add query hints for performance
        optimized_query['hints'] = self._generate_query_hints(optimized_query)
        
        return optimized_query
    
    def _determine_operations(self, intent: str) -> List[str]:
        """Determine operations based on intent"""
        # Boomi DataHub only supports LIST operations
        # COUNT operations will be handled by retrieving records and counting them
        operation_mapping = {
            'COUNT': ['select'],  # Use select and count in post-processing
            'LIST': ['select'],
            'COMPARE': ['select'], 
            'ANALYZE': ['select']
        }
        
        return operation_mapping.get(intent, ['select'])
    
    def _build_filters(self, field_mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build filters from field mappings"""
        filters = []
        
        for entity_text, mapping_info in field_mapping.items():
            field_name = mapping_info.get('field_name')
            confidence = mapping_info.get('confidence', 0.0)
            
            # Only include high-confidence mappings as filters
            if confidence >= 0.7 and field_name:
                # Skip generic terms that represent what we're counting, not filtering criteria
                if self._should_skip_as_filter(entity_text, field_name):
                    print(f"   ⏭️  Skipping '{entity_text}' as filter (generic term)")
                    continue
                    
                filter_item = {
                    'field': field_name,
                    'operator': self._determine_operator(entity_text, field_name),
                    'value': entity_text,
                    'confidence': confidence
                }
                filters.append(filter_item)
        
        return filters
    
    def _should_skip_as_filter(self, entity_text: str, field_name: str) -> bool:
        """Determine if an entity should be skipped as a filter"""
        
        # Skip generic object terms that represent what we're counting
        generic_count_terms = ['products', 'product', 'items', 'records', 'entries', 
                              'users', 'user', 'customers', 'campaigns', 'advertisements', 'ads',
                              'user names', 'usernames', 'names', 'opportunities', 'engagements']
        
        if entity_text.lower() in generic_count_terms:
            # These are typically what we're counting, not filter criteria
            return True
            
        # Keep specific values (brands, names, etc.) as filters
        return False
    
    def _determine_operator(self, entity_text: str, field_name: str) -> str:
        """Determine appropriate operator for filter"""
        
        # Time fields might use range operators
        if 'date' in field_name.lower() or 'quarter' in field_name.lower():
            return 'EQUALS'  # Could be 'CONTAINS' for quarter ranges
        
        # Brand names typically use exact match
        if 'brand' in field_name.lower() or 'name' in field_name.lower():
            return 'EQUALS'
        
        # Product names typically use contains for partial matching
        if 'product' in field_name.lower():
            return 'CONTAINS'
        
        # Default to equals
        return 'EQUALS'
    
    def _build_grouping(self, field_mapping: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build grouping for comparison queries"""
        
        # Find the most appropriate field for grouping
        # Typically brands for product comparisons
        for entity_text, mapping_info in field_mapping.items():
            field_name = mapping_info.get('field_name')
            confidence = mapping_info.get('confidence', 0.0)
            
            if confidence >= 0.8 and field_name:
                if 'brand' in field_name.lower():
                    return {
                        'field': field_name,
                        'type': 'group_by'
                    }
        
        # Fallback: use first high-confidence field
        for entity_text, mapping_info in field_mapping.items():
            field_name = mapping_info.get('field_name')
            confidence = mapping_info.get('confidence', 0.0)
            
            if confidence >= 0.8 and field_name:
                return {
                    'field': field_name,
                    'type': 'group_by'
                }
        
        return None
    
    def _determine_fields(self, intent: str, field_mapping: Dict[str, Any], model_id: str) -> List[str]:
        """Determine which fields to select"""
        
        # Start with mapped fields from dynamic field discovery
        fields = []
        for entity_text, mapping_info in field_mapping.items():
            field_name = mapping_info.get('field_name')
            if field_name and field_name not in fields:
                fields.append(field_name)
        
        # If no fields from mapping, get available fields from the model
        if not fields:
            # Try to get model fields dynamically
            available_fields = self._get_available_fields_for_model(model_id)
            if available_fields:
                if intent == 'COUNT':
                    # For COUNT queries, just need one field
                    fields = [available_fields[0]]
                else:
                    # For LIST queries, include a few key fields
                    fields = available_fields[:3]  # First 3 fields
            else:
                # Final fallback to hardcoded fields
                common_fields = self._get_common_fields_for_model(model_id)
                if common_fields:
                    fields = [common_fields[0]] if intent == 'COUNT' else common_fields[:3]
        
        return fields
    
    def _get_available_fields_for_model(self, model_id: str) -> List[str]:
        """Get available fields for a model by querying the MCP client"""
        if not self.mcp_client:
            return []
        
        try:
            # Get model fields from MCP client
            model_fields_result = self.mcp_client.get_model_fields(model_id)
            
            if isinstance(model_fields_result, dict) and 'fields' in model_fields_result:
                field_names = []
                for field in model_fields_result['fields']:
                    field_name = field.get('name', '')
                    if field_name:
                        field_names.append(field_name)
                return field_names
            
        except Exception as e:
            # If dynamic field discovery fails, fall back to common fields
            pass
        
        return []
    
    def _get_common_fields_for_model(self, model_id: str) -> List[str]:
        """Get commonly needed fields for a model"""
        # Map real model IDs to their primary fields
        common_fields_mapping = {
            # Real Boomi DataHub models
            '02367877-e560-4d82-b640-6a9f7ab96afa': ['AD_ID', 'ADVERTISER', 'PRODUCT'],  # Advertisements
            'cb5053d0-c97b-4d20-b208-346e6f0a1e0b': ['opportunity_id'],  # opportunity  
            '4f56db1f-b5bd-49b2-af68-b4d622b71996': ['engagement_id'],  # Engagements
            '674108ee-4018-481a-ae7c-7becd6c6fa37': ['user_id'],  # users
            'ea228582-91a6-4818-9f7d-bff2d9d4ed56': ['platform_user_id']  # platform-users
        }
        
        return common_fields_mapping.get(model_id, [])
    
    def _generate_query_hints(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance hints for the query"""
        hints = {}
        
        # Index hints based on filters
        if 'filters' in query and query['filters']:
            index_fields = [f['field'] for f in query['filters']]
            hints['suggested_indexes'] = index_fields
        
        # Optimization level based on complexity
        filter_count = len(query.get('filters', []))
        if filter_count == 0:
            hints['optimization_level'] = 'simple'
        elif filter_count <= 3:
            hints['optimization_level'] = 'moderate'
        else:
            hints['optimization_level'] = 'complex'
        
        return hints