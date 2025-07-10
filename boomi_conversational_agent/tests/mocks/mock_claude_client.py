"""
Mock Claude API client for testing without API calls
"""
from typing import Dict, Any, List
import json
import re

class MockClaudeClient:
    """Mock Claude API for testing without making real API calls"""
    
    def __init__(self):
        self.call_count = 0
        self.last_prompt = None
        self.api_calls = []  # Track all API calls for testing
    
    def query(self, prompt: str, max_tokens: int = None) -> str:
        """Return mock Claude responses based on prompt content"""
        self.call_count += 1
        self.last_prompt = prompt
        self.api_calls.append(prompt)
        
        prompt_lower = prompt.lower()
        
        # Model ranking responses - broader pattern matching
        if ("rank" in prompt_lower and "models" in prompt_lower) or "relevance" in prompt_lower:
            return self._mock_model_ranking(prompt)
        
        # Field mapping responses  
        elif (("map" in prompt_lower and "fields" in prompt_lower) or 
              "field.*mapping" in prompt_lower or
              ("entities" in prompt_lower and "available fields" in prompt_lower)):
            return self._mock_field_mapping(prompt)
        
        # Response generation requests
        elif ("generate" in prompt_lower and "response" in prompt_lower) or \
             ("natural language" in prompt_lower) or \
             ("user-friendly" in prompt_lower):
            return self._mock_response_generation(prompt)
        
        # Query analysis responses
        elif "analyze" in prompt_lower and "query" in prompt_lower:
            return self._mock_query_analysis(prompt)
        
        # Default response
        else:
            return json.dumps({"response": "Mock Claude response", "confidence": 0.8})
    
    def _mock_model_ranking(self, prompt: str) -> str:
        """Mock model relevance ranking based on query intent"""
        
        prompt_lower = prompt.lower()
        
        # Check entities section for more specific matching
        if "entities: [campaign]" in prompt_lower:
            return json.dumps([
                {"model_id": "Campaign", "relevance_score": 0.95, "role": "primary", "reasoning": "Direct campaign query"},
                {"model_id": "Product", "relevance_score": 0.70, "role": "secondary", "reasoning": "Products in campaigns"}
            ])
        
        # Check entities section for product queries (including multi-entity contexts)
        elif ("entities: [products]" in prompt_lower or 
              "entities: [product]" in prompt_lower or
              ("entities:" in prompt_lower and "products" in prompt_lower)):
            return json.dumps([
                {"model_id": "Product", "relevance_score": 0.95, "role": "primary", "reasoning": "Direct product query"},
                {"model_id": "Launch", "relevance_score": 0.75, "role": "secondary", "reasoning": "Product launches related"},
                {"model_id": "Campaign", "relevance_score": 0.60, "role": "tertiary", "reasoning": "Marketing context"}
            ])
        
        # Campaign-focused queries (fallback)
        elif "campaign" in prompt_lower or "marketing" in prompt_lower:
            return json.dumps([
                {"model_id": "Campaign", "relevance_score": 0.95, "role": "primary", "reasoning": "Direct campaign query"},
                {"model_id": "Product", "relevance_score": 0.70, "role": "secondary", "reasoning": "Products in campaigns"}
            ])
        
        # Product-focused queries (fallback)
        elif "product" in prompt_lower:
            return json.dumps([
                {"model_id": "Product", "relevance_score": 0.95, "role": "primary", "reasoning": "Direct product query"},
                {"model_id": "Launch", "relevance_score": 0.75, "role": "secondary", "reasoning": "Product launches related"},
                {"model_id": "Campaign", "relevance_score": 0.60, "role": "tertiary", "reasoning": "Marketing context"}
            ])
        
        # Launch/quarter queries
        elif "launch" in prompt_lower or "quarter" in prompt_lower:
            return json.dumps([
                {"model_id": "Launch", "relevance_score": 0.95, "role": "primary", "reasoning": "Launch timing query"},
                {"model_id": "Product", "relevance_score": 0.85, "role": "secondary", "reasoning": "Products being launched"}
            ])
        
        # Sales/revenue queries
        elif "sales" in prompt_lower or "revenue" in prompt_lower:
            return json.dumps([
                {"model_id": "Sales", "relevance_score": 0.95, "role": "primary", "reasoning": "Sales data query"},
                {"model_id": "Customer", "relevance_score": 0.70, "role": "secondary", "reasoning": "Customer purchase behavior"}
            ])
        
        # Comparison queries (multiple models)
        elif "compare" in prompt_lower or "vs" in prompt_lower:
            return json.dumps([
                {"model_id": "Product", "relevance_score": 0.90, "role": "primary", "reasoning": "Product comparison"},
                {"model_id": "Sales", "relevance_score": 0.80, "role": "secondary", "reasoning": "Performance metrics"},
                {"model_id": "Campaign", "relevance_score": 0.70, "role": "tertiary", "reasoning": "Marketing performance"}
            ])
        
        # Default: Product model most relevant
        return json.dumps([
            {"model_id": "Product", "relevance_score": 0.80, "role": "primary", "reasoning": "Default product relevance"}
        ])
    
    def _mock_field_mapping(self, prompt: str) -> str:
        """Mock entity to field mapping"""
        mapping = {}
        
        # Check for specific entities in the prompt and map them to fields
        if "Sony" in prompt or "Samsung" in prompt:
            mapping["Sony"] = {
                "field_name": "brand_name",
                "confidence": 0.95,
                "reasoning": "Brand entity maps to brand_name field"
            }
            
        if "Samsung" in prompt:
            mapping["Samsung"] = {
                "field_name": "brand_name", 
                "confidence": 0.95,
                "reasoning": "Brand entity maps to brand_name field"
            }
        
        if "products" in prompt.lower():
            mapping["products"] = {
                "field_name": "product_name",
                "confidence": 0.85,
                "reasoning": "Product entity maps to product_name field"
            }
        
        if "quarter" in prompt.lower():
            mapping["quarter"] = {
                "field_name": "quarter_year",
                "confidence": 0.90,
                "reasoning": "Time period entity maps to quarter_year field"
            }
            
        if "Q1" in prompt:
            mapping["Q1"] = {
                "field_name": "quarter_year",
                "confidence": 0.90,
                "reasoning": "Quarter entity maps to quarter_year field"
            }
        
        if "campaign" in prompt.lower():
            mapping["campaign"] = {
                "field_name": "campaign_name",
                "confidence": 0.90,
                "reasoning": "Campaign entity maps to campaign_name field"
            }
        
        return json.dumps(mapping)
    
    def _mock_response_generation(self, prompt: str) -> str:
        """Mock natural language response generation"""
        prompt_lower = prompt.lower()
        
        # Extract key information from the prompt to generate appropriate responses
        # Check for comparison first (more specific)
        if "compare" in prompt_lower or "comparison" in prompt_lower:
            if "sony" in prompt_lower and "samsung" in prompt_lower:
                return "Comparing Sony and Samsung products:\n\n• Sony: 45 products with an average price of $299.99\n• Samsung: 38 products with an average price of $349.99\n\nSony has 18% more products than Samsung, but Samsung's products are priced 17% higher on average."
        
        if "count" in prompt_lower and "45" in prompt:
            if "sony" in prompt_lower:
                return "I found 45 Sony products in the database. This represents a substantial portion of our product catalog."
        
        if "count" in prompt_lower and "12" in prompt:
            if "sony" in prompt_lower:
                return "There are 12 Sony products that launched in Q1. This shows strong product development activity for the quarter."
        
        if "list" in prompt_lower or "show" in prompt_lower:
            if "sony tv" in prompt_lower and "sony speaker" in prompt_lower:
                return "Here are the Sony products I found:\n\n1. Sony TV 55\" - A high-quality television\n2. Sony Speaker - Premium audio device\n\nI found 2 Sony products matching your criteria."
        
        
        if "error" in prompt_lower or "validation" in prompt_lower:
            return "I apologize, but I encountered an error while processing your request. The query validation failed due to an invalid model identifier. Please check your request and try again."
        
        # Default response for unmatched patterns
        return "I've processed your request and found the relevant information from the Boomi DataHub."
    
    def _mock_query_analysis(self, prompt: str) -> str:
        """Mock query analysis (fallback from QueryAnalyzer)"""
        if "how many" in prompt.lower():
            return json.dumps({
                "intent": "COUNT",
                "entities": ["products", "quarter"],
                "query_type": "SIMPLE"
            })
        
        return json.dumps({
            "intent": "ANALYZE",
            "entities": [],
            "query_type": "SIMPLE"
        })
    
    def reset_stats(self):
        """Reset call statistics for testing"""
        self.call_count = 0
        self.last_prompt = None
        self.api_calls = []