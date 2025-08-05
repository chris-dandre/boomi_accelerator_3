"""
Claude Payload Logger - Save JSON payloads from Claude query analysis and reasoning
"""

import os
import json
import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class ClaudePayloadLogger:
    """
    Logger for saving Claude query analysis and reasoning JSON payloads
    """
    
    def __init__(self, base_log_dir: str = "logs/claude_payloads"):
        """
        Initialize the payload logger
        
        Args:
            base_log_dir: Base directory for saving payload logs
        """
        self.base_log_dir = Path(base_log_dir)
        self.base_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different payload types
        self.query_analysis_dir = self.base_log_dir / "query_analysis"
        self.field_mapping_dir = self.base_log_dir / "field_mapping" 
        self.query_building_dir = self.base_log_dir / "query_building"
        self.model_discovery_dir = self.base_log_dir / "model_discovery"
        self.response_generation_dir = self.base_log_dir / "response_generation"
        
        for dir_path in [self.query_analysis_dir, self.field_mapping_dir, 
                        self.query_building_dir, self.model_discovery_dir,
                        self.response_generation_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def save_query_analysis_payload(self, 
                                   user_query: str,
                                   claude_prompt: str, 
                                   claude_response: str,
                                   parsed_analysis: Dict[str, Any],
                                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save query analysis payload from QueryAnalyzer
        
        Args:
            user_query: Original user query
            claude_prompt: Prompt sent to Claude
            claude_response: Raw Claude response
            parsed_analysis: Parsed JSON analysis result
            metadata: Additional metadata
            
        Returns:
            Path to saved payload file
        """
        # Ensure directory exists
        self.query_analysis_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"query_analysis_{timestamp}.json"
        
        payload = {
            "timestamp": datetime.datetime.now().isoformat(),
            "payload_type": "query_analysis",
            "user_query": user_query,
            "claude_prompt": claude_prompt,
            "claude_response": claude_response,
            "parsed_analysis": parsed_analysis,
            "metadata": metadata or {}
        }
        
        file_path = self.query_analysis_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Saved query analysis payload: {file_path}")
        return str(file_path)
    
    def save_field_mapping_payload(self,
                                  entities: list,
                                  model_fields: list,
                                  query_context: str,
                                  claude_prompt: str,
                                  claude_response: str,
                                  field_mapping: Dict[str, Any],
                                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save field mapping payload from FieldMapper
        
        Args:
            entities: Entities from query analysis
            model_fields: Available model fields
            query_context: Original query context
            claude_prompt: Prompt sent to Claude
            claude_response: Raw Claude response
            field_mapping: Final field mapping result
            metadata: Additional metadata
            
        Returns:
            Path to saved payload file
        """
        # Ensure directory exists
        self.field_mapping_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"field_mapping_{timestamp}.json"
        
        payload = {
            "timestamp": datetime.datetime.now().isoformat(),
            "payload_type": "field_mapping",
            "entities": entities,
            "model_fields": model_fields,
            "query_context": query_context,
            "claude_prompt": claude_prompt,
            "claude_response": claude_response,
            "field_mapping": field_mapping,
            "metadata": metadata or {}
        }
        
        file_path = self.field_mapping_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Saved field mapping payload: {file_path}")
        return str(file_path)
    
    def save_query_building_payload(self,
                                   field_mapping: Dict[str, Any],
                                   claude_analysis: Dict[str, Any],
                                   query_context: Dict[str, Any],
                                   reasoning_trace: list,
                                   final_filters: list,
                                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save query building payload with ReAct reasoning trace
        
        Args:
            field_mapping: Entity to field mappings
            claude_analysis: Claude analysis results
            query_context: Query context information
            reasoning_trace: ReAct reasoning steps (THOUGHT-ACTION-OBSERVATION)
            final_filters: Generated filters
            metadata: Additional metadata
            
        Returns:
            Path to saved payload file
        """
        # Ensure directory exists
        self.query_building_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"query_building_{timestamp}.json"
        
        payload = {
            "timestamp": datetime.datetime.now().isoformat(),
            "payload_type": "query_building_react",
            "field_mapping": field_mapping,
            "claude_analysis": claude_analysis,
            "query_context": query_context,
            "reasoning_trace": reasoning_trace,
            "final_filters": final_filters,
            "metadata": metadata or {}
        }
        
        file_path = self.query_building_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Saved query building payload: {file_path}")
        return str(file_path)
    
    def save_model_discovery_payload(self,
                                    user_query: str,
                                    available_models: list,
                                    claude_prompt: str,
                                    claude_response: str,
                                    selected_models: list,
                                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save model discovery payload from ModelDiscovery
        
        Args:
            user_query: Original user query
            available_models: All available models
            claude_prompt: Prompt sent to Claude
            claude_response: Raw Claude response
            selected_models: Claude-selected relevant models
            metadata: Additional metadata
            
        Returns:
            Path to saved payload file
        """
        # Ensure directory exists
        self.model_discovery_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"model_discovery_{timestamp}.json"
        
        payload = {
            "timestamp": datetime.datetime.now().isoformat(),
            "payload_type": "model_discovery",
            "user_query": user_query,
            "available_models": available_models,
            "claude_prompt": claude_prompt,
            "claude_response": claude_response,
            "selected_models": selected_models,
            "metadata": metadata or {}
        }
        
        file_path = self.model_discovery_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Saved model discovery payload: {file_path}")
        return str(file_path)
    
    def save_response_generation_payload(self,
                                        user_query: str,
                                        query_result: Dict[str, Any],
                                        user_context: Dict[str, Any],
                                        claude_prompt: str,
                                        claude_response: str,
                                        final_response: str,
                                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save response generation payload from ResponseGenerator
        
        Args:
            user_query: Original user query
            query_result: Data query results
            user_context: User context information
            claude_prompt: Prompt sent to Claude
            claude_response: Raw Claude response
            final_response: Final formatted response
            metadata: Additional metadata
            
        Returns:
            Path to saved payload file
        """
        # Ensure directory exists
        self.response_generation_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"response_generation_{timestamp}.json"
        
        payload = {
            "timestamp": datetime.datetime.now().isoformat(),
            "payload_type": "response_generation",
            "user_query": user_query,
            "query_result": query_result,
            "user_context": user_context,
            "claude_prompt": claude_prompt,
            "claude_response": claude_response,
            "final_response": final_response,
            "metadata": metadata or {}
        }
        
        file_path = self.response_generation_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Saved response generation payload: {file_path}")
        return str(file_path)
    
    def save_generic_claude_payload(self,
                                   payload_type: str,
                                   prompt: str,
                                   response: str,
                                   context: Dict[str, Any],
                                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save generic Claude payload for any Claude interaction
        
        Args:
            payload_type: Type identifier for the payload
            prompt: Prompt sent to Claude
            response: Claude's response
            context: Context information
            metadata: Additional metadata
            
        Returns:
            Path to saved payload file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{payload_type}_{timestamp}.json"
        
        payload = {
            "timestamp": datetime.datetime.now().isoformat(),
            "payload_type": payload_type,
            "claude_prompt": prompt,
            "claude_response": response,
            "context": context,
            "metadata": metadata or {}
        }
        
        # Save to base directory for generic payloads
        file_path = self.base_log_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Saved {payload_type} payload: {file_path}")
        return str(file_path)
    
    def get_latest_payloads(self, payload_type: str = None, limit: int = 10) -> list:
        """
        Get latest saved payloads
        
        Args:
            payload_type: Optional filter by payload type
            limit: Maximum number of payloads to return
            
        Returns:
            List of payload file paths, sorted by timestamp (newest first)
        """
        if payload_type:
            if payload_type == "query_analysis":
                search_dir = self.query_analysis_dir
            elif payload_type == "field_mapping":
                search_dir = self.field_mapping_dir
            elif payload_type == "query_building":
                search_dir = self.query_building_dir
            elif payload_type == "model_discovery":
                search_dir = self.model_discovery_dir
            elif payload_type == "response_generation":
                search_dir = self.response_generation_dir
            else:
                search_dir = self.base_log_dir
        else:
            search_dir = self.base_log_dir
        
        # Get all JSON files
        json_files = list(search_dir.glob("*.json"))
        if not payload_type:
            # Also search subdirectories if no specific type
            for subdir in [self.query_analysis_dir, self.field_mapping_dir, 
                          self.query_building_dir, self.model_discovery_dir,
                          self.response_generation_dir]:
                json_files.extend(subdir.glob("*.json"))
        
        # Sort by modification time (newest first)
        json_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        return [str(p) for p in json_files[:limit]]

# Global instance for easy access
claude_payload_logger = ClaudePayloadLogger()