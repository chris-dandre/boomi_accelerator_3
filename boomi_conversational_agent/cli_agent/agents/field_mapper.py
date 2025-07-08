"""
FieldMapper Agent - Phase 5 TDD Implementation
Maps entities to model fields using LLM reasoning
"""
from typing import Dict, Any, List, Optional
import json

class FieldMapper:
    """
    Map entities from queries to specific model fields
    Uses Claude LLM for intelligent entity-to-field mapping
    """
    
    def __init__(self, mcp_client=None, claude_client=None):
        """
        Initialize FieldMapper agent
        
        Args:
            mcp_client: Optional MCP client (will create default if None)
            claude_client: Optional Claude client (will create default if None)
        """
        self.mcp_client = mcp_client or self._create_default_mcp_client()
        self.claude_client = claude_client or self._create_default_claude_client()
        
        # Default confidence threshold for field mappings
        self.default_confidence_threshold = 0.7
    
    def _create_default_mcp_client(self):
        """Create default MCP client - placeholder for real implementation"""
        # This would import and create the real MCP client
        # For now, return None and expect it to be injected in tests
        return None
    
    def _create_default_claude_client(self):
        """Create default Claude client - real implementation"""
        try:
            import sys
            from pathlib import Path
            
            # Add parent directory to path to import claude_client
            parent_dir = Path(__file__).parent.parent.parent
            sys.path.append(str(parent_dir))
            
            from claude_client import ClaudeClient
            client = ClaudeClient()
            
            if client.is_available():
                return client
            else:
                print("⚠️  Claude client not available, using fallback patterns")
                return None
                
        except Exception as e:
            print(f"⚠️  Could not create Claude client: {e}")
            return None
    
    def get_model_fields(self, model_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve field information for a specific model
        
        Args:
            model_id: ID of the model to get fields for
            
        Returns:
            List of field dictionaries with name, type, description
        """
        if not self.mcp_client:
            raise ValueError("MCP client not configured")
        
        print(f"🔍 Field Discovery - Getting fields for model: {model_id}")
        
        try:
            print(f"🔍 Field Discovery - MCP client type: {type(self.mcp_client)}")
            print(f"🔍 Field Discovery - MCP client methods: {[m for m in dir(self.mcp_client) if not m.startswith('_')]}")
            result = self.mcp_client.get_model_fields(model_id)
            print(f"🔍 Field Discovery - Raw result: {type(result)}")
            print(f"🔍 Field Discovery - Result sample: {str(result)[:200]}...")
            return result
        except Exception as e:
            print(f"❌ Field Discovery - Error getting fields: {e}")
            print(f"❌ Field Discovery - Client type: {type(self.mcp_client)}")
            return []
    
    
    def map_entities_to_fields(self, entities: List[Dict[str, Any]], 
                             model_fields: List[Dict[str, Any]], 
                             query_context: str = "") -> Dict[str, Any]:
        """
        Map entities to model fields using Claude LLM
        
        Args:
            entities: List of entities from query analysis
            model_fields: List of available model fields
            query_context: Original query for context
            
        Returns:
            Dictionary mapping entity text to field information
        """
        if not self.claude_client:
            # Fallback: Use pattern-based field mapping when Claude not available
            return self._fallback_pattern_field_mapping(entities, model_fields)
        
        try:
            # Use Claude's intelligent field mapping with query context
            print(f"🧠 Claude Field Mapping: Analyzing semantic relationships...")
            print(f"   Entities to map: {[e.get('text', '') for e in entities]}")
            print(f"   Available fields: {[f.get('name', '') for f in model_fields]}")
            print(f"   Query context: '{query_context}'")
            
            field_mapping = self.claude_client.map_entities_to_fields(
                entities, model_fields, query_context
            )
            
            if field_mapping and isinstance(field_mapping, dict):
                print(f"✅ Claude mapped {len(field_mapping)} entities to fields")
                for entity, mapping in field_mapping.items():
                    field_name = mapping.get('field_name', 'Unknown')
                    confidence = mapping.get('confidence', 0)
                    reasoning = mapping.get('reasoning', 'No reasoning provided')
                    print(f"   🎯 '{entity}' → {field_name} (confidence: {confidence:.2f})")
                    print(f"      💭 Reasoning: {reasoning}")
                return field_mapping
            else:
                print("⚠️  Claude returned empty mapping, using fallback")
                return self._fallback_field_mapping(entities, model_fields)
                
        except Exception as e:
            print(f"⚠️  Claude field mapping failed: {e}, using fallback")
            return self._fallback_field_mapping(entities, model_fields)
    
    def create_field_mapping_for_models(self, entities: List[Dict[str, Any]], 
                                      relevant_models: List[Dict[str, Any]], 
                                      query_context: str = "") -> Dict[str, Any]:
        """
        Create field mappings for all relevant models
        
        Args:
            entities: List of entities from query analysis
            relevant_models: List of relevant models from ModelDiscovery
            query_context: Original user query for context
            
        Returns:
            Dictionary with model_id -> field_mapping structure
        """
        complete_mapping = {}
        
        for model in relevant_models:
            model_id = model['model_id']
            
            # Get fields for this model
            model_fields = self.get_model_fields(model_id)
            
            # Extract fields list from model_fields response
            print(f"🔍 Debug - Raw model_fields structure: {type(model_fields)}")
            print(f"🔍 Debug - Model_fields keys: {model_fields.keys() if isinstance(model_fields, dict) else 'Not a dict'}")
            
            if isinstance(model_fields, dict):
                # Check if it's a nested MCP response
                if 'fields' in model_fields and isinstance(model_fields['fields'], dict):
                    # Extract the actual fields list from nested structure
                    nested_fields = model_fields['fields']
                    if 'fields' in nested_fields:
                        fields_list = nested_fields['fields']
                    else:
                        fields_list = []
                elif 'fields' in model_fields and isinstance(model_fields['fields'], list):
                    # Direct fields list
                    fields_list = model_fields['fields']
                else:
                    fields_list = []
            else:
                fields_list = model_fields if isinstance(model_fields, list) else []
            
            print(f"🔍 Debug - Extracted fields_list: {len(fields_list) if isinstance(fields_list, list) else 'Not a list'} items")
            
            # Map entities to fields for this model with query context
            field_mapping = self.map_entities_to_fields(entities, fields_list, query_context)
            
            complete_mapping[model_id] = field_mapping
        
        return complete_mapping
    
    def validate_field_mapping(self, field_mapping: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate field mapping for completeness and confidence
        
        Args:
            field_mapping: Entity to field mapping dictionary
            
        Returns:
            Validation result with is_valid, missing_entities, low_confidence_mappings
        """
        validation_result = {
            'is_valid': True,
            'missing_entities': [],
            'low_confidence_mappings': [],
            'warnings': []
        }
        
        # Check for low confidence mappings
        for entity_text, mapping_info in field_mapping.items():
            confidence = mapping_info.get('confidence', 0.0)
            
            if confidence < self.default_confidence_threshold:
                validation_result['low_confidence_mappings'].append(entity_text)
                validation_result['is_valid'] = False
        
        # Add warnings for low confidence
        if validation_result['low_confidence_mappings']:
            validation_result['warnings'].append(
                f"Low confidence mappings: {', '.join(validation_result['low_confidence_mappings'])}"
            )
        
        return validation_result
    
    def _build_field_mapping_prompt(self, entities: List[Dict[str, Any]], 
                                  model_fields: List[Dict[str, Any]]) -> str:
        """Build prompt for Claude field mapping"""
        
        entities_text = json.dumps(entities, indent=2)
        fields_text = json.dumps(model_fields, indent=2)
        
        prompt = f"""
Map these entities to the most appropriate model fields.

Entities:
{entities_text}

Available Fields:
{fields_text}

Map each entity to the best matching field based on:
1. Entity type and field description
2. Semantic similarity
3. Business context

Return JSON with format:
{{
  "entity_text": {{
    "field_name": "field_name",
    "confidence": 0.95,
    "reasoning": "Why this mapping makes sense"
  }}
}}

Only include mappings with confidence > 0.6. Focus on the most relevant mappings.
"""
        return prompt.strip()
    
    def _fallback_field_mapping(self, entities: List[Dict[str, Any]], 
                              model_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback field mapping when Claude fails"""
        
        field_mapping = {}
        
        # Simple pattern matching for common mappings
        field_names = [field['name'] for field in model_fields]
        
        for entity in entities:
            # Handle both string and dictionary entity formats
            if isinstance(entity, str):
                entity_text = entity
                entity_type = 'unknown'
            elif isinstance(entity, dict):
                entity_text = entity.get('text', '')
                entity_type = entity.get('type', '')
            else:
                continue  # Skip invalid entity formats
            
            mapped_field = None
            confidence = 0.0
            
            # Brand entities -> brand_name field
            if entity_type == 'BRAND' and 'brand_name' in field_names:
                mapped_field = 'brand_name'
                confidence = 0.9
            
            # Product entities -> product_name field
            elif entity_type == 'OBJECT' and entity_text.lower() in ['products', 'product']:
                if 'product_name' in field_names:
                    mapped_field = 'product_name'
                    confidence = 0.8
            
            # Time entities -> date fields
            elif entity_type == 'TIME_PERIOD':
                if 'quarter_year' in field_names:
                    mapped_field = 'quarter_year'
                    confidence = 0.85
                elif 'launch_date' in field_names:
                    mapped_field = 'launch_date'
                    confidence = 0.75
            
            if mapped_field:
                field_mapping[entity_text] = {
                    'field_name': mapped_field,
                    'confidence': confidence,
                    'reasoning': f'Fallback mapping based on entity type {entity_type}'
                }
        
        return field_mapping
    
    def _fallback_pattern_field_mapping(self, entities: List[Dict[str, Any]], 
                                      model_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Pattern-based field mapping when Claude client not available
        
        Args:
            entities: List of entity dictionaries with text and type
            model_fields: List of available field dictionaries from model
            
        Returns:
            Dictionary mapping entity text to field information
        """
        mapping = {}
        
        if not model_fields:
            return mapping
            
        # Create field name patterns for matching
        field_patterns = {}
        for field in model_fields:
            field_name = field.get('name', '').lower()
            field_patterns[field_name] = field
            
        # Map entities to fields using pattern matching
        for entity in entities:
            # Handle both string and dictionary entity formats
            if isinstance(entity, str):
                entity_text = entity.lower()
                entity_type = 'unknown'
            elif isinstance(entity, dict):
                entity_text = entity.get('text', '').lower()
                entity_type = entity.get('type', 'unknown')
            else:
                continue  # Skip invalid entity formats
            
            best_field = None
            best_confidence = 0.0
            
            # Pattern matching logic
            for field_name, field_info in field_patterns.items():
                confidence = self._calculate_field_pattern_match(entity_text, entity_type, field_name, field_info)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_field = field_info
            
            # Only include mappings with reasonable confidence
            if best_field and best_confidence >= 0.3:
                mapping[entity_text] = {
                    'field_name': best_field.get('name', ''),
                    'confidence': best_confidence,
                    'reasoning': f"Pattern match between '{entity_text}' and '{best_field.get('name', '')}'"
                }
        
        return mapping
    
    def _calculate_field_pattern_match(self, entity_text: str, entity_type: str, 
                                     field_name: str, field_info: Dict[str, Any]) -> float:
        """Calculate confidence score for entity-field pattern matching"""
        confidence = 0.0
        
        # Direct name match
        if entity_text in field_name or field_name in entity_text:
            confidence += 0.8
        
        # Common business entity patterns
        business_patterns = {
            'id': ['id', 'identifier', 'key'],
            'name': ['name', 'title', 'label'],
            'date': ['date', 'time', 'created', 'modified'],
            'status': ['status', 'state', 'active'],
            'type': ['type', 'category', 'class'],
            'user': ['user', 'person', 'customer', 'client'],
            'product': ['product', 'item', 'goods'],
            'campaign': ['campaign', 'marketing', 'promo'],
            'advertisement': ['ad', 'advertisement', 'banner', 'creative'],
            'engagement': ['engagement', 'interaction', 'activity'],
            'opportunity': ['opportunity', 'lead', 'prospect']
        }
        
        # Check entity type patterns
        for pattern, keywords in business_patterns.items():
            if pattern in entity_text or pattern in entity_type.lower():
                for keyword in keywords:
                    if keyword in field_name:
                        confidence += 0.6
                        break
        
        # Field type considerations
        field_type = field_info.get('type', '').lower()
        if entity_type.lower() == 'date' and 'date' in field_type:
            confidence += 0.4
        elif entity_type.lower() == 'number' and ('int' in field_type or 'num' in field_type):
            confidence += 0.4
        elif entity_type.lower() == 'string' and 'string' in field_type:
            confidence += 0.2
            
        return min(confidence, 1.0)  # Cap at 1.0