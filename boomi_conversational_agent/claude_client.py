"""
Claude Client for LLM-powered field mapping and model discovery
"""

import os
import json
import time
import random
from typing import Dict, List, Any, Optional

# Import payload logger for automatic payload saving
try:
    from claude_payload_logger import claude_payload_logger
    PAYLOAD_LOGGING_ENABLED = True
except ImportError:
    PAYLOAD_LOGGING_ENABLED = False
    print("⚠️  Claude payload logger not available")

class ClaudeClient:
    """
    Claude API client for intelligent field mapping and model discovery
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude client
        
        Args:
            api_key: Anthropic API key (will try environment variable if None)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self._client = None
        
        if self.api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
                print("✅ Claude client initialized successfully")
            except ImportError:
                print("⚠️  anthropic package not installed. Install with: pip install anthropic")
                self._client = None
            except Exception as e:
                print(f"⚠️  Failed to initialize Claude client: {e}")
                self._client = None
        else:
            print("⚠️  No ANTHROPIC_API_KEY found. Claude features will use fallback patterns.")
    
    def retry_with_backoff(self, func, max_retries=5):
        """Retry function with exponential backoff for 529 errors"""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if "529" in str(e) or "overloaded" in str(e).lower():
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        print(f"⏳ Claude API overloaded, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                raise e
    
    def is_available(self) -> bool:
        """Check if Claude client is available"""
        return self._client is not None
    
    def generate_response(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate response using Claude (alias for query method)
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            
        Returns:
            Claude's response as a string
        """
        return self.query(prompt, max_tokens)
    
    def query(self, prompt: str, max_tokens: int = 1000, save_payload: bool = True, payload_context: Dict[str, Any] = None) -> str:
        """
        Send a query to Claude
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            save_payload: Whether to save the query payload to logs
            payload_context: Additional context for payload logging
            
        Returns:
            Claude's response as string
        """
        if not self._client:
            raise ValueError("Claude client not available")
        
        def make_request():
            message = self._client.messages.create(
                model="claude-sonnet-4-20250514",  # Claude 4.0 Sonnet
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        
        try:
            response = self.retry_with_backoff(make_request)
            
            # Save payload if logging is enabled and requested
            if save_payload and PAYLOAD_LOGGING_ENABLED:
                try:
                    context = payload_context or {}
                    context.update({
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": max_tokens
                    })
                    claude_payload_logger.save_generic_claude_payload(
                        payload_type="claude_query",
                        prompt=prompt,
                        response=response,
                        context=context
                    )
                except Exception as e:
                    print(f"⚠️  Failed to save Claude query payload: {e}")
            
            return response
        except Exception as e:
            print(f"❌ Claude API error after retries: {e}")
            raise
    
    def map_entities_to_fields(self, entities: List[Dict[str, Any]], 
                             model_fields: List[Dict[str, Any]], 
                             query_context: str = "") -> Dict[str, Any]:
        """
        Use Claude to intelligently map query entities to model fields
        
        Args:
            entities: List of entities from query analysis
            model_fields: List of available model fields
            query_context: Original query for context
            
        Returns:
            Dictionary mapping entity text to field information
        """
        if not self._client:
            raise ValueError("Claude client not available")
        
        prompt = self._build_field_mapping_prompt(entities, model_fields, query_context)
        
        try:
            # Add field mapping context for payload logging
            payload_context = {
                "operation": "field_mapping",
                "entities_count": len(entities),
                "model_fields_count": len(model_fields),
                "query_context": query_context
            }
            
            response = self.query(prompt, max_tokens=1500, payload_context=payload_context)
            
            # Parse JSON response
            try:
                mapping = json.loads(response)
                
                # Save specialized field mapping payload if logging enabled
                if PAYLOAD_LOGGING_ENABLED:
                    try:
                        claude_payload_logger.save_field_mapping_payload(
                            entities=entities,
                            model_fields=model_fields,
                            query_context=query_context,
                            claude_prompt=prompt,
                            claude_response=response,
                            field_mapping=mapping
                        )
                    except Exception as e:
                        print(f"⚠️  Failed to save field mapping payload: {e}")
                
                return mapping
            except json.JSONDecodeError:
                # If response isn't valid JSON, try to extract JSON from it
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    mapping = json.loads(json_match.group())
                    
                    # Save payload even for extracted JSON
                    if PAYLOAD_LOGGING_ENABLED:
                        try:
                            claude_payload_logger.save_field_mapping_payload(
                                entities=entities,
                                model_fields=model_fields,
                                query_context=query_context,
                                claude_prompt=prompt,
                                claude_response=response,
                                field_mapping=mapping,
                                metadata={"json_extraction": True}
                            )
                        except Exception as e:
                            print(f"⚠️  Failed to save field mapping payload: {e}")
                    
                    return mapping
                else:
                    print(f"⚠️  Could not parse Claude response as JSON: {response}")
                    return {}
                    
        except Exception as e:
            print(f"❌ Error in Claude field mapping: {e}")
            return {}
    
    def rank_models_by_relevance(self, query: str, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Use Claude to rank models by relevance to query
        
        Args:
            query: The user's query
            models: List of available models
            
        Returns:
            List of models ranked by relevance with scores
        """
        if not self._client:
            raise ValueError("Claude client not available")
        
        prompt = self._build_model_ranking_prompt(query, models)
        
        try:
            response = self.query(prompt, max_tokens=1000)
            
            # Parse JSON response
            try:
                ranking = json.loads(response)
                return ranking
            except json.JSONDecodeError:
                print(f"⚠️  Could not parse Claude model ranking response: {response}")
                return []
                
        except Exception as e:
            print(f"❌ Error in Claude model ranking: {e}")
            return []
    
    def _build_field_mapping_prompt(self, entities: List[Dict[str, Any]], 
                                  model_fields: List[Dict[str, Any]], 
                                  query_context: str) -> str:
        """Build prompt for Claude field mapping"""
        
        entities_text = json.dumps(entities, indent=2)
        fields_text = json.dumps(model_fields, indent=2)
        
        prompt = f"""You are an expert data analyst helping map user query entities to database fields.

QUERY CONTEXT: "{query_context}"

ENTITIES EXTRACTED:
{entities_text}

AVAILABLE FIELDS:
{fields_text}

TASK: Map each entity to the most appropriate field based on semantic meaning and context.

CRITICAL EXAMPLES:
- If query is "How many products is Sony advertising?", then "Sony" should map to ADVERTISER field (Sony is the advertiser)
- If query is "What Sony products do we have?", then "Sony" should map to PRODUCT field (Sony is the product brand)
- Consider the semantic role of each entity in the query context

INSTRUCTIONS:
1. Understand the semantic meaning of each entity in the query context
2. Map entities based on their ROLE in the query, not just keyword matching
3. Only include mappings with confidence > 0.6
4. Consider business context (advertiser vs product vs campaign etc.)

Return JSON format:
{{
  "entity_text": {{
    "field_name": "FIELD_NAME",
    "confidence": 0.95,
    "reasoning": "Detailed explanation of why this mapping makes sense given the query context"
  }}
}}

Focus on semantic understanding, not just keyword matching."""

        return prompt.strip()
    
    def _build_model_ranking_prompt(self, query: str, models: List[Dict[str, Any]]) -> str:
        """Build prompt for Claude model ranking"""
        
        models_text = json.dumps(models, indent=2)
        
        prompt = f"""You are an expert data analyst helping rank database models by relevance to a user query.

USER QUERY: "{query}"

AVAILABLE MODELS:
{models_text}

TASK: Rank these models by relevance to the user's query.

INSTRUCTIONS:
1. Consider what the user is asking about
2. Rank models from most relevant (highest score) to least relevant
3. Give relevance scores from 0.0 to 1.0
4. Explain why each model is relevant or not

Return JSON format as a list of models with scores:
[
  {{
    "model_id": "model_id_here",
    "name": "model_name", 
    "relevance": 0.95,
    "reasoning": "Why this model is most relevant to the query"
  }}
]

Sort by relevance score (highest first)."""

        return prompt.strip()