"""
ModelDiscovery Agent - Phase 5 TDD Implementation
Discovers relevant Boomi DataHub models using LLM reasoning
"""
from typing import Dict, Any, List, Optional
import json
import os

class ModelDiscovery:
    """
    Discover and rank Boomi DataHub models based on query analysis
    Uses Claude LLM for intelligent model relevance ranking
    """
    
    def __init__(self, mcp_client=None, claude_client=None):
        """
        Initialize ModelDiscovery agent
        
        Args:
            mcp_client: Optional MCP client (will create default if None)
            claude_client: Optional Claude client (will create default if None)
        """
        self.mcp_client = mcp_client or self._create_default_mcp_client()
        self.claude_client = claude_client or self._create_default_claude_client()
        
        # Default relevance threshold for filtering models
        self.default_threshold = 0.5
    
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
    
    def get_all_models(self) -> List[Dict[str, Any]]:
        """
        Retrieve all available models from Boomi DataHub
        
        Returns:
            List of model dictionaries with id, name, description
        """
        if not self.mcp_client:
            raise ValueError("MCP client not configured")
        
        return self.mcp_client.get_all_models()
    
    def find_relevant_models(self, query_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find models relevant to the analyzed query
        
        Args:
            query_analysis: Result from QueryAnalyzer with intent, entities, query_type
            
        Returns:
            List of relevant models with relevance scores and roles
        """
        # Get all available models
        all_models = self.get_all_models()
        
        # Create query context for Claude
        query_context = self._build_query_context(query_analysis)
        
        # Use Claude to rank models by relevance
        ranked_models = self.rank_models_by_relevance(all_models, query_context)
        
        # Filter by relevance threshold and assign roles
        relevant_models = self._assign_model_roles(ranked_models)
        
        return relevant_models
    
    def rank_models_by_relevance(self, available_models: List[Dict[str, Any]], 
                                query_context: str) -> List[Dict[str, Any]]:
        """
        Use Claude LLM to rank models by relevance to query
        
        Args:
            available_models: List of available models from MCP
            query_context: Query context for ranking
            
        Returns:
            List of models with relevance scores and reasoning
        """
        if not self.claude_client:
            # Fallback to simple pattern-based ranking when Claude not available
            return self._fallback_pattern_ranking(available_models, query_context)
        
        # Build prompt for Claude
        prompt = self._build_ranking_prompt(available_models, query_context)
        
        # Get Claude's response
        claude_response = self.claude_client.query(prompt)
        
        # Parse Claude's ranking response
        try:
            ranked_models = json.loads(claude_response)
            if isinstance(ranked_models, list):
                return ranked_models
            else:
                # Handle case where Claude returns unexpected format
                return []
        except (json.JSONDecodeError, TypeError):
            # Fallback: return models with default relevance
            return self._fallback_ranking(available_models)
    
    def filter_by_relevance_threshold(self, ranked_models: List[Dict[str, Any]], 
                                    threshold: float = None) -> List[Dict[str, Any]]:
        """
        Filter models below relevance threshold
        
        Args:
            ranked_models: Models with relevance scores
            threshold: Minimum relevance score (default: 0.5)
            
        Returns:
            Filtered list of models above threshold
        """
        if threshold is None:
            threshold = self.default_threshold
        
        return [
            model for model in ranked_models 
            if model.get('relevance_score', 0) >= threshold
        ]
    
    def discover_models_for_query(self, query_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Complete model discovery workflow for a query
        
        Args:
            query_analysis: Result from QueryAnalyzer
            
        Returns:
            Final list of relevant models for the query
        """
        return self.find_relevant_models(query_analysis)
    
    def _build_query_context(self, query_analysis: Dict[str, Any]) -> str:
        """Build context string for Claude ranking"""
        intent = query_analysis.get('intent', 'UNKNOWN')
        entities = query_analysis.get('entities', [])
        query_type = query_analysis.get('query_type', 'SIMPLE')
        
        entity_text = ', '.join([e.get('text', '') for e in entities])
        
        return f"Intent: {intent}, Entities: [{entity_text}], Type: {query_type}"
    
    def _build_ranking_prompt(self, available_models: List[Dict[str, Any]], 
                            query_context: str) -> str:
        """Build prompt for Claude model ranking"""
        
        models_text = json.dumps(available_models, indent=2)
        
        prompt = f"""
Rank these models by relevance for the query context.

Query Context: {query_context}

Available Models:
{models_text}

Rank these models by relevance (0.0 to 1.0) for answering the user's query.
Consider model names, descriptions, and likely data contents.

Return JSON array with format:
[
  {{
    "model_id": "ModelName",
    "relevance_score": 0.95,
    "role": "primary|secondary|tertiary",
    "reasoning": "Why this model is relevant"
  }}
]

Focus on models most likely to contain the data needed to answer the query.
"""
        return prompt.strip()
    
    def _assign_model_roles(self, ranked_models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assign primary/secondary/tertiary roles based on relevance scores"""
        
        # Filter by threshold first
        filtered_models = self.filter_by_relevance_threshold(ranked_models)
        
        # Sort by relevance score (highest first)
        sorted_models = sorted(
            filtered_models, 
            key=lambda x: x.get('relevance_score', 0), 
            reverse=True
        )
        
        # Assign roles based on ranking
        for i, model in enumerate(sorted_models):
            if i == 0:
                model['role'] = 'primary'
            elif i == 1:
                model['role'] = 'secondary'
            else:
                model['role'] = 'tertiary'
        
        return sorted_models
    
    def _fallback_ranking(self, available_models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback ranking when Claude fails"""
        
        # Simple fallback: give Product model highest relevance
        fallback_ranking = []
        
        for model in available_models:
            # Always use the UUID (id field), never the name
            model_uuid = model.get('id', '')
            model_name = model.get('name', '').lower()
            
            # Rank based on model name but use UUID as model_id
            if 'product' in model_name or 'advertisement' in model_name:
                relevance = 0.80
            elif 'campaign' in model_name:
                relevance = 0.70
            elif 'launch' in model_name:
                relevance = 0.60
            else:
                relevance = 0.50
            
            fallback_ranking.append({
                "model_id": model_uuid,  # Use UUID, not name
                "name": model.get('name', ''),  # Keep name for reference
                "relevance_score": relevance,
                "role": "primary" if relevance >= 0.75 else "secondary",
                "reasoning": f"Fallback ranking based on model type for '{model_name}'"
            })
        
        return sorted(fallback_ranking, key=lambda x: x['relevance_score'], reverse=True)
    
    def _fallback_pattern_ranking(self, available_models: Dict[str, Any], query_context: str) -> List[Dict[str, Any]]:
        """Pattern-based ranking when Claude client not available"""
        
        # Extract published models from the API response
        if isinstance(available_models, dict) and 'data' in available_models:
            models_list = available_models['data'].get('published', [])
        else:
            models_list = available_models if isinstance(available_models, list) else []
        
        pattern_ranking = []
        query_lower = query_context.lower()
        
        for model in models_list:
            model_name = model.get('name', '').lower()
            model_id = model.get('id', '')
            
            # Simple pattern matching for relevance
            relevance = 0.30  # Base relevance
            
            # Check for direct name matches in query
            if model_name in query_lower or any(word in model_name for word in query_lower.split()):
                relevance += 0.40
            
            # Boost common business models
            if model_name in ['advertisements', 'ads', 'advertising']:
                relevance += 0.20
            elif model_name in ['users', 'user', 'customer', 'customers']:
                relevance += 0.15
            elif model_name in ['opportunity', 'opportunities', 'leads']:
                relevance += 0.15
            elif model_name in ['engagements', 'engagement', 'interactions']:
                relevance += 0.10
            
            pattern_ranking.append({
                "model_id": model_id,
                "name": model.get('name', ''),
                "relevance_score": min(relevance, 0.95),  # Cap at 95%
                "role": "primary" if relevance >= 0.60 else "secondary",
                "reasoning": f"Pattern match for '{model_name}' with query context",
                "confidence": min(relevance, 0.95)
            })
        
        return sorted(pattern_ranking, key=lambda x: x['relevance_score'], reverse=True)