"""
QueryAnalyzer Agent - Enhanced with MCPAgentState and field_mappings support
Phase 8B+ implementation with load_dotenv integration
"""
from typing import Dict, Any, List
import re
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

class QueryAnalyzer:
    """
    Analyze user queries to extract intent and entities
    Minimal implementation for TDD GREEN phase
    """
    
    def __init__(self, claude_client=None):
        """Initialize the QueryAnalyzer"""
        self.claude_client = claude_client
        self.intent_patterns = {
            'COMPARE': [
                r'compare',
                r'vs\b',
                r'versus',
                r'against'
            ],
            'COUNT': [
                r'how many',
                r'count',
                r'number of'
            ],
            'LIST': [
                r'show me',
                r'list',
                r'display'
            ],
            'ANALYZE': [
                r'analyze',
                r'analysis',
                r'performance'
            ]
        }
        
        self.entity_patterns = {
            'BRAND': [
                r'\bSony\b',
                r'\bSamsung\b',
                r'\bApple\b',
                r'\bGoogle\b'
            ],
            'OBJECT': [
                r'\bproducts?\b',
                r'\bportfolios?\b',
                r'\binventory\b',
                r'\bcampaigns?\b'
            ],
            'TIME_PERIOD': [
                r'\bquarter\b',
                r'\bQ[1-4]\b',
                r'\bmonth\b',
                r'\byear\b'
            ]
        }
    
    def analyze(self, user_query: str, available_models: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze user query for intent and entities
        
        Args:
            user_query: Natural language query from user
            available_models: Optional list of available models for semantic matching
            
        Returns:
            Dictionary with intent, entities, query_type, and suggested_models
        """
        if not user_query or not user_query.strip():
            return {
                'intent': 'UNKNOWN',
                'entities': [],
                'query_type': 'INVALID',
                'suggested_models': []
            }
        
        print(f"🧠 Query Analysis: Using AI semantic understanding...")
        print(f"   Query: '{user_query}'")
        
        # Use Claude for intelligent analysis if available
        print(f"   Claude Client Available: {self.claude_client is not None}")
        print(f"   Available Models Count: {len(available_models) if available_models else 0}")
        if available_models:
            try:
                # Safe model name extraction
                model_names = []
                for i, model in enumerate(available_models):
                    if i >= 3:  # Limit to first 3
                        break
                    if isinstance(model, dict):
                        model_names.append(model.get('name', f'Model_{i}'))
                    else:
                        model_names.append(f'Model_{i}')
                print(f"   Model Names: {model_names}")
            except Exception as e:
                print(f"   Model Names: Error extracting names - {e}")
        
        if self.claude_client and available_models:
            return self._claude_semantic_analysis(user_query, available_models)
        
        # Fallback to pattern-based analysis
        print("🔄 Falling back to pattern-based analysis...")
        query_lower = user_query.lower()
        
        # Extract intent
        intent = self._extract_intent(query_lower)
        
        # Extract entities
        entities = self._extract_entities(user_query)
        
        # Classify complexity
        query_type = self._classify_complexity(intent, entities)
        
        return {
            'intent': intent,
            'entities': entities,
            'query_type': query_type,
            'suggested_models': []
        }
    
    def _extract_intent(self, query_lower: str) -> str:
        """Extract intent from query using pattern matching"""
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        
        return 'UNKNOWN'
    
    def _extract_entities(self, query: str) -> List[Dict[str, Any]]:
        """Extract entities from query with confidence scores"""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    entity_text = match.group().strip()
                    # Remove word boundaries for cleaner text
                    entity_text = re.sub(r'\\b', '', entity_text)
                    
                    entities.append({
                        'text': entity_text,
                        'type': entity_type,
                        'confidence': self._calculate_confidence(entity_text, entity_type)
                    })
        
        # Remove duplicates while preserving order
        unique_entities = []
        seen = set()
        for entity in entities:
            key = (entity['text'].lower(), entity['type'])
            if key not in seen:
                unique_entities.append(entity)
                seen.add(key)
        
        return unique_entities
    
    def _calculate_confidence(self, text: str, entity_type: str) -> float:
        """Calculate confidence score for entity recognition"""
        
        # Higher confidence for exact brand matches
        if entity_type == 'BRAND' and text.lower() in ['sony', 'samsung', 'apple']:
            return 0.98
        
        # High confidence for common business objects
        if entity_type == 'OBJECT' and text.lower() in ['products', 'product']:
            return 0.95
        
        # Good confidence for time periods
        if entity_type == 'TIME_PERIOD':
            return 0.90
        
        # Default confidence
        return 0.85
    
    def _classify_complexity(self, intent: str, entities: List[Dict[str, Any]]) -> str:
        """Classify query complexity based on intent and entities"""
        
        if intent == 'UNKNOWN':
            return 'INVALID'
        
        # Compare queries are complex
        if intent == 'COMPARE':
            return 'COMPLEX'
        
        # Multiple brands suggest comparison
        brand_count = sum(1 for e in entities if e['type'] == 'BRAND')
        if brand_count > 1:
            return 'COMPLEX'
        
        # Simple single-intent queries
        return 'SIMPLE'
    
    def _claude_semantic_analysis(self, user_query: str, available_models: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use Claude for intelligent query analysis"""
        print("💭 Claude Processing: Semantic query analysis...")
        # Safe debug print for models structure
        if isinstance(available_models, list):
            print(f"   Debug - Models structure: {available_models[:2]}")  # Show first 2 models
        else:
            print(f"   Debug - Models structure: {type(available_models)} - {available_models}")
        
        # Build model context for Claude
        model_descriptions = []
        for model in available_models:
            if isinstance(model, dict):
                name = model.get('name', 'Unknown')
                description = model.get('description', 'No description')
            elif isinstance(model, str):
                name = model
                description = 'No description'
            else:
                name = str(model)
                description = 'No description'
            model_descriptions.append(f"- {name}: {description}")
        
        models_text = '\n'.join(model_descriptions)
        
        prompt = f"""
Analyze this user query and determine the most relevant information:

User Query: "{user_query}"

Available Data Models:
{models_text}

Please analyze and provide:
1. Intent (COUNT, LIST, COMPARE, ANALYZE, META)
2. Entities mentioned - extract ALL relevant entities including:
   - Specific values (Sony, Apple, Tesla, etc.)
   - Object types (products, users, advertisements, etc.)
   - Field indicators (descriptions, names, titles, prices, dates, etc.)
   - Time periods (this quarter, last month, etc.)
3. Most relevant model(s) for this query
4. Query complexity (SIMPLE, COMPLEX, META)
5. Whether this is a meta-query about the system itself

Respond in this JSON format:
{{
    "intent": "LIST",
    "entities": [
        {{"text": "entity_name", "type": "BRAND|OBJECT|FIELD_INDICATOR|TIME_PERIOD|META", "confidence": 0.95}}
    ],
    "query_type": "SIMPLE",
    "suggested_models": ["model_name"],
    "is_meta_query": false,
    "reasoning": "Explanation of why this model was chosen"
}}

CRITICAL: Extract field indicators as entities:
- If query mentions "descriptions" → extract as FIELD_INDICATOR entity
- If query mentions "names" → extract as FIELD_INDICATOR entity  
- If query mentions "titles", "prices", "dates", "IDs" → extract as FIELD_INDICATOR entities
- These indicate what specific fields the user wants to see in results

Examples:
- "show product descriptions" → entities: [{{"text": "product", "type": "OBJECT"}}, {{"text": "descriptions", "type": "FIELD_INDICATOR"}}]
- "list user names" → entities: [{{"text": "user", "type": "OBJECT"}}, {{"text": "names", "type": "FIELD_INDICATOR"}}]

IMPORTANT - Distinguish between data queries and meta-queries:
- Data queries: "list users", "show Sony products" → Query actual data records, use specific models
- Meta-queries: "list models", "list all data models", "what models are available", "show me the data models" → Show system structure, use "ALL_AVAILABLE_MODELS"

For meta-queries:
- Set "intent": "META" 
- Set "is_meta_query": true
- Set "query_type": "META"
- Set "suggested_models": ["ALL_AVAILABLE_MODELS"]

Focus on semantic understanding - if they ask about "users", suggest the "users" model, not "advertisements".
"""
        
        try:
            response = self.claude_client.query(prompt, max_tokens=500)
            print(f"✅ Claude Analysis Complete")
            print(f"   Raw Response: {response[:200]}...")  # Show first 200 chars for debugging
            
            # Parse Claude's JSON response (handle markdown code blocks)
            import json
            import re
            
            # Try direct JSON parsing first
            try:
                analysis = json.loads(response.strip())
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    try:
                        analysis = json.loads(json_match.group(1).strip())
                    except json.JSONDecodeError:
                        # Try generic code blocks
                        code_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
                        if code_match:
                            analysis = json.loads(code_match.group(1).strip())
                        else:
                            raise ValueError("Could not parse JSON from Claude response")
                else:
                    # Try to find any JSON-like structure
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                    else:
                        raise ValueError("No JSON found in Claude response")
            
            print(f"   Intent: {analysis.get('intent', 'UNKNOWN')}")
            print(f"   Entities: {len(analysis.get('entities', []))} found")
            print(f"   Suggested Models: {analysis.get('suggested_models', [])}")
            print(f"   Is Meta Query: {analysis.get('is_meta_query', False)}")
            print(f"   Reasoning: {analysis.get('reasoning', 'No reasoning provided')}")
            
            # Store original query for reference
            analysis['original_query'] = user_query
            
            return analysis
            
        except Exception as e:
            print(f"❌ Claude analysis failed: {e}, using fallback")
            # Fall back to pattern-based analysis
            query_lower = user_query.lower()
            return {
                'intent': self._extract_intent(query_lower),
                'entities': self._extract_entities(user_query),
                'query_type': self._classify_complexity(self._extract_intent(query_lower), self._extract_entities(user_query)),
                'suggested_models': []
            }