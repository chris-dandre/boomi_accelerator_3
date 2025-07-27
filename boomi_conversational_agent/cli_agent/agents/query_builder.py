"""
QueryBuilder Agent - Enhanced with MCPAgentState and field_mappings support
Builds executable queries from analysis and field mappings
"""
from typing import Dict, Any, List, Optional
import copy
import json
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
            'fields': self._determine_fields(intent, field_mapping, model_id),
            'metadata': {
                'original_intent': intent,
                'complexity': query_type,
                'entity_count': len(entities)
            }
        }
        
        # Use Claude to understand query intent and build appropriate filters
        print(f"🧠 Query Builder: Using LLM to analyze query intent...")
        query_context = {
            'original_query': query_analysis.get('original_query', ''),
            'intent': intent,
            'entities': entities,
            'field_mapping': field_mapping,
            'model_id': model_id
        }
        
        # Get Claude's reasoning about the query structure
        claude_query_analysis = self._analyze_query_with_claude(query_context)
        
        # Build filters based on Claude's analysis using ReAct reasoning
        print(f"🔧 Query Builder: Constructing filters based on ReAct analysis...")
        filters = self._build_intelligent_filters(field_mapping, claude_query_analysis, query_context)
        query['filters'] = filters
        print(f"   🎯 Filters created: {len(filters)} filter(s)")
        for i, filter_item in enumerate(filters, 1):
            field = filter_item.get('fieldId', 'Unknown')
            operator = filter_item.get('operator', 'Unknown')
            value = filter_item.get('value', 'Unknown')
            confidence = filter_item.get('confidence', 0)
            reasoning = filter_item.get('reasoning', 'Pattern-based')
            print(f"      {i}. {field} {operator} '{value}' (confidence: {confidence:.2f})")
            print(f"         💭 {reasoning}")
        
        # Apply Claude's query structure recommendations
        if claude_query_analysis.get('distinct_values_requested'):
            query['operations'].append('distinct')
            query['distinct_field'] = claude_query_analysis.get('distinct_field')
            print(f"   🎯 LLM Analysis: Requesting distinct values from {claude_query_analysis.get('distinct_field')}")
        
        # Store Claude's reasoning in metadata
        query['metadata']['llm_analysis'] = claude_query_analysis
        
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
                filter_key = (filter_item['fieldId'], filter_item['operator'], str(filter_item['value']))
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
        
        print(f"   🔍 Filter Debug - Processing {len(field_mapping)} field mappings:")
        for entity_text, mapping_info in field_mapping.items():
            field_name = mapping_info.get('field_name')
            confidence = mapping_info.get('confidence', 0.0)
            
            print(f"      📌 '{entity_text}' → {field_name} (confidence: {confidence:.2f})")
            
            # Only include high-confidence mappings as filters
            if confidence >= 0.7 and field_name:
                # Skip generic terms that represent what we're counting, not filtering criteria
                if self._should_skip_as_filter(entity_text, field_name):
                    print(f"         ⏭️  Skipping '{entity_text}' as filter (generic term)")
                    continue
                    
                filter_item = {
                    'fieldId': field_name,
                    'operator': self._determine_operator(entity_text, field_name),
                    'value': entity_text,
                    'confidence': confidence,
                    'reasoning': f"Field mapping: {entity_text} → {field_name}"
                }
                filters.append(filter_item)
                print(f"         ✅ Created filter: {field_name} = '{entity_text}'")
            else:
                print(f"         ❌ Skipped: confidence {confidence:.2f} < 0.7 or no field_name")
        
        print(f"   🎯 Filter Debug - Created {len(filters)} filters total")
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
        
        # For COUNT queries, prioritize ID fields for counting
        if intent == 'COUNT':
            for entity_text, mapping_info in field_mapping.items():
                field_name = mapping_info.get('field_name')
                if field_name and 'ID' in field_name.upper():
                    print(f"🔧 Query Builder: Using {field_name} for COUNT operation")
                    return [field_name]
        
        # For other queries, collect all mapped fields
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
                    # For COUNT queries, prefer ID fields
                    id_field = next((f for f in available_fields if 'ID' in f.upper()), available_fields[0])
                    print(f"🔧 Query Builder: Using {id_field} for COUNT operation")
                    fields = [id_field]
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
            index_fields = [f['fieldId'] for f in query['filters']]
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
    
    def _analyze_query_with_claude(self, query_context: Dict[str, Any]) -> Dict[str, Any]:
        """Use Claude to analyze query intent and determine proper query structure"""
        
        if not self.claude_client:
            # Fallback to pattern-based analysis
            return self._fallback_query_analysis(query_context)
        
        # Build prompt for Claude
        prompt = self._build_query_analysis_prompt(query_context)
        
        try:
            print(f"🧠 Claude Query Analysis: Analyzing query structure...")
            response = self.claude_client.query(prompt)
            
            # Parse Claude's response
            analysis = self._parse_claude_query_response(response)
            print(f"   ✅ Claude analysis complete")
            print(f"   🎯 Query Type: {analysis.get('query_type', 'Unknown')}")
            print(f"   🎯 Distinct Values: {analysis.get('distinct_values_requested', False)}")
            print(f"   🎯 Filters Needed: {len(analysis.get('filters', []))}")
            
            return analysis
            
        except Exception as e:
            print(f"   ❌ Claude analysis failed: {e}")
            print(f"   🔄 Falling back to pattern-based analysis...")
            return self._fallback_query_analysis(query_context)
    
    def _build_query_analysis_prompt(self, query_context: Dict[str, Any]) -> str:
        """Build prompt for Claude to analyze query structure"""
        
        original_query = query_context.get('original_query', '')
        intent = query_context.get('intent', '')
        entities = query_context.get('entities', [])
        field_mapping = query_context.get('field_mapping', {})
        
        # Extract field information
        field_info = []
        for entity, mapping in field_mapping.items():
            field_name = mapping.get('field_name', '')
            confidence = mapping.get('confidence', 0)
            field_info.append(f"'{entity}' → {field_name} (confidence: {confidence:.2f})")
        
        prompt = f"""
Analyze this database query intent and determine the proper query structure:

**Original Query**: "{original_query}"
**Detected Intent**: {intent}
**Entities Found**: {[e.get('text', e) if isinstance(e, dict) else e for e in entities]}
**Field Mappings**: {', '.join(field_info) if field_info else 'None'}

Please analyze whether this query is requesting:

1. **DISTINCT VALUES** - User wants to see all unique values from a field
   Example: "list all advertisers" → SELECT DISTINCT ADVERTISER
   
2. **FILTERED RECORDS** - User wants records matching specific criteria  
   Example: "Sony products" → SELECT * WHERE ADVERTISER = 'Sony'

3. **ALL RECORDS** - User wants all records with no filters
   Example: "show all advertisements" → SELECT * (no WHERE clause)

For each entity→field mapping, determine:
- Should this be used as a FILTER (WHERE field = value)?
- Should this field return DISTINCT values?
- Is the entity a literal search term or a generic category?

Respond in JSON format:
{{
    "query_type": "DISTINCT_VALUES|FILTERED_RECORDS|ALL_RECORDS",
    "distinct_values_requested": true/false,
    "distinct_field": "field_name" (if distinct values requested),
    "filters": [
        {{
            "field": "field_name",
            "operator": "EQUALS|CONTAINS|IN",
            "value": "search_value",
            "reasoning": "why this should be a filter",
            "confidence": 0.0-1.0
        }}
    ],
    "reasoning": "explanation of the analysis"
}}
"""
        
        return prompt
    
    def _parse_claude_query_response(self, response: str) -> Dict[str, Any]:
        """Parse Claude's query analysis response"""
        
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # Look for JSON block in response
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Look for any JSON-like structure
            json_match = re.search(r'(\{.*?\})', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
                
        except json.JSONDecodeError:
            pass
        
        # If JSON parsing fails, extract key information using patterns
        analysis = {
            "query_type": "FILTERED_RECORDS",  # default
            "distinct_values_requested": False,
            "filters": [],
            "reasoning": "Pattern-based fallback due to JSON parsing error"
        }
        
        # Check for distinct values indicators
        if any(phrase in response.lower() for phrase in ['distinct', 'unique values', 'all different']):
            analysis["distinct_values_requested"] = True
            analysis["query_type"] = "DISTINCT_VALUES"
        
        return analysis
    
    def _fallback_query_analysis(self, query_context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback pattern-based query analysis when Claude is not available"""
        
        original_query = query_context.get('original_query', '').lower()
        
        # Detect "list all X" patterns
        if any(phrase in original_query for phrase in ['list all', 'show all', 'get all']):
            # Check if it's asking for categories vs specific items
            if any(term in original_query for term in ['advertisers', 'users', 'companies', 'brands', 'products']):
                return {
                    "query_type": "DISTINCT_VALUES",
                    "distinct_values_requested": True,
                    "distinct_field": self._guess_distinct_field(query_context),
                    "filters": [],
                    "reasoning": "Pattern detected: 'list all X' typically requests distinct values"
                }
        
        # Default to filtered records
        return {
            "query_type": "FILTERED_RECORDS", 
            "distinct_values_requested": False,
            "filters": [],
            "reasoning": "Pattern-based fallback analysis"
        }
    
    def _guess_distinct_field(self, query_context: Dict[str, Any]) -> str:
        """Guess which field should return distinct values"""
        
        field_mapping = query_context.get('field_mapping', {})
        
        # Return the first mapped field
        for entity, mapping in field_mapping.items():
            field_name = mapping.get('field_name')
            if field_name:
                return field_name
        
        return None
    
    def _build_intelligent_filters(self, field_mapping: Dict[str, Any], claude_analysis: Dict[str, Any], query_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build filters using ReAct (Reasoning + Acting) approach"""
        
        print(f"   🤔 ReAct Query Builder: Starting multi-step reasoning...")
        
        # Get query context for reasoning from metadata or analysis
        original_query = query_context.get('original_query', 'unknown query')
        
        filters = []
        
        # THOUGHT 1: Analyze the user's intent and query structure
        print(f"   💭 THOUGHT: Analyzing query structure...")
        print(f"      Query: '{original_query}'")
        print(f"      Claude Analysis: {claude_analysis.get('query_type', 'unknown')} query")
        print(f"      Distinct values requested: {claude_analysis.get('distinct_values_requested', False)}")
        print(f"      Field mappings: {[(entity, info.get('field_name')) for entity, info in field_mapping.items()]}")
        
        # THOUGHT 2: Determine if entities are filter values or field identifiers
        print(f"   💭 THOUGHT: Are entities filter values or field identifiers?")
        entity_analysis = {}
        
        for entity_text, mapping_info in field_mapping.items():
            field_name = mapping_info.get('field_name')
            confidence = mapping_info.get('confidence', 0.0)
            
            # Reasoning about entity role
            is_generic_term = self._is_generic_field_identifier(entity_text, original_query)
            is_specific_value = self._is_specific_filter_value(entity_text, original_query)
            
            entity_analysis[entity_text] = {
                'field_name': field_name,
                'confidence': confidence,
                'is_generic_term': is_generic_term,
                'is_specific_value': is_specific_value,
                'reasoning': self._explain_entity_role(entity_text, original_query, is_generic_term, is_specific_value)
            }
            
            print(f"      '{entity_text}' → {field_name}")
            print(f"         Generic term: {is_generic_term}, Specific value: {is_specific_value}")
            print(f"         Reasoning: {entity_analysis[entity_text]['reasoning']}")
        
        # ACTION 1: Decide whether to apply filters or get distinct values
        print(f"   🎯 ACTION: Determining filter strategy...")
        
        if claude_analysis.get('distinct_values_requested'):
            # For distinct values queries, only use specific filter values, skip generic terms
            print(f"      Decision: Distinct values query - filtering out generic field identifiers")
            
            for entity_text, analysis in entity_analysis.items():
                if analysis['is_specific_value'] and not analysis['is_generic_term']:
                    filter_item = {
                        'fieldId': analysis['field_name'],
                        'operator': 'EQUALS',
                        'value': entity_text,
                        'confidence': analysis['confidence'],
                        'reasoning': f"ReAct: {analysis['reasoning']}"
                    }
                    filters.append(filter_item)
                    print(f"         ✅ Creating filter: {analysis['field_name']} = '{entity_text}'")
                else:
                    print(f"         ⏭️  Skipping '{entity_text}': {analysis['reasoning']}")
        else:
            # For regular queries, trust Claude's analysis of what filters are needed
            print(f"      Decision: Regular query - trusting Claude LLM analysis")
            
            # Check if Claude determined filters are needed
            claude_filters = claude_analysis.get('filters', [])
            if claude_filters:
                print(f"         Claude identified {len(claude_filters)} filters needed")
                # Convert Claude's filter format to our format
                for claude_filter in claude_filters:
                    # Handle IS_NOT_NULL operator which doesn't need a value parameter
                    operator = claude_filter.get('operator', 'EQUALS')
                    filter_item = {
                        'fieldId': claude_filter.get('field', 'unknown'),
                        'operator': operator,
                        'confidence': 0.95,
                        'reasoning': f"Claude LLM: {claude_filter.get('reasoning', 'Filter recommended by Claude')}"
                    }
                    
                    # Only add value parameter for operators that need it
                    if operator not in ['IS_NOT_NULL', 'IS_NULL']:
                        filter_item['value'] = claude_filter.get('value', '')
                    filters.append(filter_item)
                    if 'value' in filter_item:
                        print(f"         ✅ Added Claude filter: {filter_item['fieldId']} {filter_item['operator']} '{filter_item['value']}'")
                    else:
                        print(f"         ✅ Added Claude filter: {filter_item['fieldId']} {filter_item['operator']}")
            else:
                print(f"         Claude determined NO FILTERS needed - query should return all records")
                print(f"         Reason: {claude_analysis.get('reasoning', 'No specific reasoning provided')}")
                # No filters - trust Claude's analysis that this should select all records
        
        # OBSERVATION: Report the final decision
        print(f"   👁️  OBSERVATION: Created {len(filters)} filters using ReAct reasoning")
        
        if claude_analysis.get('distinct_values_requested'):
            distinct_field = claude_analysis.get('distinct_field', 'unknown')
            print(f"      Final action: Get distinct values from '{distinct_field}' field with {len(filters)} filters")
        else:
            print(f"      Final action: Execute regular query with {len(filters)} filters")
            
        return filters
    
    def _is_generic_field_identifier(self, entity_text: str, original_query: str) -> bool:
        """Determine if entity is a generic term identifying a field type, not a filter value"""
        
        generic_terms = [
            'companies', 'company', 'organizations', 'organization', 
            'products', 'product', 'items', 'things',
            'users', 'user', 'customers', 'customer', 'people',
            'campaigns', 'campaign', 'advertisements', 'ads', 'ad',
            'opportunities', 'opportunity', 'deals', 'deal',
            'records', 'record', 'entries', 'entry', 'data',
            'advertising', 'marketing', 'promoting'
        ]
        
        # Check if entity is a generic term
        if entity_text.lower() in generic_terms:
            return True
            
        # Check query patterns that suggest generic usage
        question_patterns = ['which', 'what', 'list', 'show all', 'get all', 'find all']
        query_lower = original_query.lower()
        
        # If query starts with question words and entity is plural, likely generic
        if any(pattern in query_lower for pattern in question_patterns) and entity_text.endswith('s'):
            return True
            
        return False
    
    def _is_specific_filter_value(self, entity_text: str, original_query: str) -> bool:
        """Determine if entity is a specific value to filter by"""
        
        # Proper nouns (capitalized) are often specific values
        if entity_text and entity_text[0].isupper() and len(entity_text) > 1:
            return True
            
        # Specific brand names, numbers, dates, etc.
        if entity_text.lower() in ['sony', 'apple', 'microsoft', 'google', 'amazon', 'meta', 'tesla']:
            return True
            
        # If entity appears in quotes or specific context, likely a filter value
        if f"'{entity_text}'" in original_query or f'"{entity_text}"' in original_query:
            return True
            
        return False
    
    def _explain_entity_role(self, entity_text: str, original_query: str, is_generic: bool, is_specific: bool) -> str:
        """Explain the reasoning for entity role classification"""
        
        if is_generic and not is_specific:
            return f"Generic field identifier - '{entity_text}' describes what type of data to return"
        elif is_specific and not is_generic:
            return f"Specific filter value - '{entity_text}' is a concrete value to filter by"
        elif is_generic and is_specific:
            return f"Ambiguous - '{entity_text}' could be generic or specific, treating as generic in question context"
        else:
            return f"Uncertain classification - '{entity_text}' doesn't match clear patterns, defaulting to filter value"
    
    def _build_filters_original(self, field_mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Original pattern-based filter building (renamed from _build_filters)"""
        
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
                    'fieldId': field_name,
                    'operator': self._determine_operator(entity_text, field_name),
                    'value': entity_text,
                    'confidence': confidence,
                    'reasoning': 'Pattern-based analysis'
                }
                filters.append(filter_item)
        
        return filters