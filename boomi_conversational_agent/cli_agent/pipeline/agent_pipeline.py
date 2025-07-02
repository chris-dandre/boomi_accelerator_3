"""
AgentPipeline - Phase 5 TDD Implementation
Orchestrates all agents in sequential pipeline for query processing
"""
from typing import Dict, Any, List, Optional
import time
import hashlib
import json
import copy

# Import all agents
from cli_agent.agents.query_analyzer import QueryAnalyzer
from cli_agent.agents.model_discovery import ModelDiscovery
from cli_agent.agents.field_mapper import FieldMapper
from cli_agent.agents.query_builder import QueryBuilder
from cli_agent.agents.data_retrieval import DataRetrieval
from cli_agent.agents.response_generator import ResponseGenerator

class AgentPipeline:
    """
    Sequential pipeline orchestrating all conversational agents
    Processes user queries from natural language to final response
    """
    
    def __init__(self, mcp_client=None, claude_client=None):
        """
        Initialize AgentPipeline with all agents
        
        Args:
            mcp_client: Optional MCP client (shared across agents)
            claude_client: Optional Claude client (shared across agents)
        """
        self.mcp_client = mcp_client
        self.claude_client = claude_client
        
        # Initialize all agents with shared clients
        self.query_analyzer = QueryAnalyzer(claude_client=claude_client)
        
        self.model_discovery = ModelDiscovery(
            mcp_client=mcp_client,
            claude_client=claude_client
        )
        
        self.field_mapper = FieldMapper(
            mcp_client=mcp_client,
            claude_client=claude_client
        )
        
        self.query_builder = QueryBuilder(
            mcp_client=mcp_client,
            claude_client=claude_client
        )
        
        self.data_retrieval = DataRetrieval(
            mcp_client=mcp_client,
            claude_client=claude_client
        )
        
        self.response_generator = ResponseGenerator(
            mcp_client=mcp_client,
            claude_client=claude_client
        )
        
        # Pipeline cache for performance
        self.pipeline_cache = {}
        
        # Pipeline version and metadata
        self.version = "1.0.0"
        self.pipeline_stages = [
            'query_analysis',
            'model_discovery', 
            'field_mapping',
            'query_building',
            'data_retrieval',
            'response_generation'
        ]
    
    def process_query(self, user_query: str, user_context: Optional[Dict[str, Any]] = None,
                     enable_cache: bool = False) -> Dict[str, Any]:
        """
        Process user query through complete agent pipeline
        
        Args:
            user_query: Natural language query from user
            user_context: Optional user context for personalization
            enable_cache: Whether to enable pipeline caching
            
        Returns:
            Complete pipeline result with response and metadata
        """
        pipeline_start_time = time.time()
        
        # Check cache if enabled
        if enable_cache:
            cache_key = self._generate_pipeline_cache_key(user_query, user_context)
            if cache_key in self.pipeline_cache:
                cached_result = copy.deepcopy(self.pipeline_cache[cache_key])
                cached_result['pipeline_metadata']['cache_hit'] = True
                cached_result['pipeline_metadata']['total_execution_time_ms'] = 0
                return cached_result
        
        # Initialize pipeline result
        pipeline_result = {
            'success': False,
            'response': {},
            'pipeline_metadata': {
                'user_context': user_context,
                'cache_enabled': enable_cache,
                'cache_hit': False
            }
        }
        
        try:
            # Stage 0: Get Available Models (for semantic analysis)
            available_models = []
            try:
                raw_models = self.model_discovery.get_all_models()
                print(f"🔍 Debug - Raw models from MCP: {type(raw_models)}")
                print(f"🔍 Debug - Raw models sample: {raw_models[:2] if isinstance(raw_models, list) else raw_models}")
                
                if isinstance(raw_models, dict):
                    if 'models' in raw_models:
                        available_models = raw_models['models']
                    elif 'data' in raw_models and isinstance(raw_models['data'], dict):
                        # Handle MCP response structure: data.published + data.draft
                        available_models = []
                        if 'published' in raw_models['data']:
                            available_models.extend(raw_models['data']['published'])
                        if 'draft' in raw_models['data']:
                            available_models.extend(raw_models['data']['draft'])
                    else:
                        available_models = []
                elif isinstance(raw_models, list):
                    available_models = raw_models
                else:
                    available_models = []
                    
                print(f"🔍 Debug - Processed models: {available_models[:2] if available_models else 'None'}")
            except Exception as e:
                print(f"⚠️  Model discovery failed: {e}")
                available_models = []  # Continue with empty list if model discovery fails
            
            # Stage 1: Query Analysis
            stage_start = time.time()
            try:
                query_analysis = self.query_analyzer.analyze(user_query, available_models)
                stage_metadata = {
                    'success': True,
                    'execution_time_ms': (time.time() - stage_start) * 1000,
                    'intent': query_analysis.get('intent'),
                    'entities': query_analysis.get('entities', []),
                    'query_type': query_analysis.get('query_type'),
                    'suggested_models': query_analysis.get('suggested_models', [])
                }
                pipeline_result['pipeline_metadata']['query_analysis'] = stage_metadata
                
                # Early exit for invalid queries
                if query_analysis.get('intent') == 'UNKNOWN':
                    return self._handle_pipeline_error("Unable to understand the query", pipeline_result, pipeline_start_time)
                    
            except Exception as e:
                return self._handle_stage_error('query_analysis', str(e), pipeline_result, pipeline_start_time)
            
            # Stage 2: Model Discovery
            stage_start = time.time()
            try:
                # Check if this is a meta-query about system structure
                is_meta_query = query_analysis.get('is_meta_query', False)
                suggested_models = query_analysis.get('suggested_models', [])
                
                if is_meta_query or 'ALL_AVAILABLE_MODELS' in suggested_models:
                    print(f"🧠 Meta-Query Detected: Providing system structure information")
                    return self._handle_meta_query(query_analysis, available_models, pipeline_result, pipeline_start_time)
                
                elif suggested_models:
                    print(f"🎯 Using Claude-suggested models: {suggested_models}")
                    # Filter available models to match suggestions
                    relevant_models = []
                    for model in available_models:
                        if isinstance(model, dict) and model.get('name') in suggested_models:
                            # Create a copy and add metadata
                            model_copy = model.copy()
                            model_copy['relevance_score'] = 0.95
                            model_copy['role'] = 'primary'
                            model_copy['model_id'] = model.get('id', '')  # Ensure model_id field exists
                            relevant_models.append(model_copy)
                    
                    if not relevant_models:
                        print("⚠️  Suggested models not found, falling back to discovery")
                        relevant_models = self.model_discovery.find_relevant_models(query_analysis)
                else:
                    relevant_models = self.model_discovery.find_relevant_models(query_analysis)
                if not relevant_models:
                    return self._handle_pipeline_error("No relevant data models found", pipeline_result, pipeline_start_time)
                
                primary_model = relevant_models[0]['model_id']
                stage_metadata = {
                    'success': True,
                    'execution_time_ms': (time.time() - stage_start) * 1000,
                    'primary_model': primary_model,
                    'relevant_models': [m['model_id'] for m in relevant_models],
                    'model_count': len(relevant_models)
                }
                pipeline_result['pipeline_metadata']['model_discovery'] = stage_metadata
                
            except Exception as e:
                return self._handle_stage_error('model_discovery', str(e), pipeline_result, pipeline_start_time)
            
            # Stage 3: Field Mapping
            stage_start = time.time()
            try:
                field_mapping = self.field_mapper.create_field_mapping_for_models(
                    query_analysis.get('entities', []),
                    relevant_models,
                    user_query  # Pass the original query for context
                )
                
                # Get field mapping for primary model
                primary_field_mapping = field_mapping.get(primary_model, {})
                
                stage_metadata = {
                    'success': True,
                    'execution_time_ms': (time.time() - stage_start) * 1000,
                    'mapped_entities': list(primary_field_mapping.keys()),
                    'mapping_confidence': self._calculate_mapping_confidence(primary_field_mapping),
                    'models_mapped': list(field_mapping.keys())
                }
                pipeline_result['pipeline_metadata']['field_mapping'] = stage_metadata
                
            except Exception as e:
                return self._handle_stage_error('field_mapping', str(e), pipeline_result, pipeline_start_time)
            
            # Stage 4: Query Building
            stage_start = time.time()
            try:
                executable_query = self.query_builder.build_query(
                    query_analysis,
                    primary_field_mapping,
                    primary_model
                )
                
                # Optimize query
                optimized_query = self.query_builder.optimize_query(executable_query)
                
                # Enable caching if requested
                if enable_cache:
                    optimized_query['cache_enabled'] = True
                
                stage_metadata = {
                    'success': True,
                    'execution_time_ms': (time.time() - stage_start) * 1000,
                    'query_type': optimized_query.get('query_type'),
                    'filters_applied': len(optimized_query.get('filters', [])),
                    'optimization_applied': True
                }
                pipeline_result['pipeline_metadata']['query_building'] = stage_metadata
                
            except Exception as e:
                return self._handle_stage_error('query_building', str(e), pipeline_result, pipeline_start_time)
            
            # Stage 5: Data Retrieval
            stage_start = time.time()
            try:
                query_result = self.data_retrieval.execute_query(optimized_query)
                
                # Handle query execution errors
                if 'error' in query_result:
                    return self._handle_pipeline_error(f"Data retrieval failed: {query_result['error']}", pipeline_result, pipeline_start_time)
                
                stage_metadata = {
                    'success': True,
                    'execution_time_ms': (time.time() - stage_start) * 1000,
                    'record_count': query_result.get('metadata', {}).get('record_count', 0),
                    'query_complexity': query_result.get('metadata', {}).get('query_complexity', 'unknown'),
                    'data_source': primary_model
                }
                pipeline_result['pipeline_metadata']['data_retrieval'] = stage_metadata
                
            except Exception as e:
                return self._handle_stage_error('data_retrieval', str(e), pipeline_result, pipeline_start_time)
            
            # Stage 6: Response Generation
            stage_start = time.time()
            try:
                final_response = self.response_generator.generate_response(
                    user_query,
                    query_result,
                    user_context=user_context
                )
                
                stage_metadata = {
                    'success': True,
                    'execution_time_ms': (time.time() - stage_start) * 1000,
                    'response_type': final_response.get('response_type'),
                    'personalization_applied': user_context is not None,
                    'message_length': len(final_response.get('message', ''))
                }
                pipeline_result['pipeline_metadata']['response_generation'] = stage_metadata
                
            except Exception as e:
                return self._handle_stage_error('response_generation', str(e), pipeline_result, pipeline_start_time)
            
            # Finalize successful pipeline result
            total_execution_time = (time.time() - pipeline_start_time) * 1000
            pipeline_result.update({
                'success': True,
                'response': final_response,
            })
            pipeline_result['pipeline_metadata']['total_execution_time_ms'] = total_execution_time
            
            # Cache result if enabled
            if enable_cache:
                cache_key = self._generate_pipeline_cache_key(user_query, user_context)
                self.pipeline_cache[cache_key] = copy.deepcopy(pipeline_result)
            
            return pipeline_result
        
        except Exception as e:
            return self._handle_pipeline_error(f"Pipeline execution failed: {str(e)}", pipeline_result, pipeline_start_time)
    
    def _handle_meta_query(self, query_analysis: Dict[str, Any], available_models: List[Dict[str, Any]], 
                          pipeline_result: Dict[str, Any], pipeline_start_time: float) -> Dict[str, Any]:
        """Handle meta-queries about system structure"""
        print("🔧 Processing Meta-Query: System structure request")
        
        user_query = query_analysis.get('original_query', 'list models')
        
        # Check if this is a field listing request for a specific model
        if 'field' in user_query.lower() and any(model['name'].lower() in user_query.lower() for model in available_models):
            print("🔍 Field listing request detected")
            return self._handle_field_listing_query(user_query, available_models, pipeline_result, pipeline_start_time)
        
        # Regular model listing
        model_list = []
        for model in available_models:
            if isinstance(model, dict):
                name = model.get('name', 'Unknown')
                status = model.get('publicationStatus', 'unknown')
                version = model.get('latestVersion', 'unknown')
                description = self._get_model_description(name)
                model_list.append({
                    'name': name,
                    'status': status,
                    'version': version,
                    'description': description
                })
        
        # Generate response using Claude or fallback
        response_message = self._generate_meta_response(user_query, model_list)
        
        execution_time = (time.time() - pipeline_start_time) * 1000
        
        pipeline_result.update({
            'success': True,
            'response': {
                'response_type': 'META',
                'message': response_message
            },
            'pipeline_metadata': {
                'total_execution_time_ms': execution_time,
                'query_analysis': {
                    'intent': query_analysis.get('intent'),
                    'is_meta_query': True,
                    'models_found': len(model_list)
                }
            }
        })
        
        return pipeline_result
    
    def _get_model_description(self, model_name: str) -> str:
        """Get user-friendly description for model"""
        descriptions = {
            'Advertisements': 'Marketing campaigns and advertising data',
            'users': 'System user accounts and profiles', 
            'opportunity': 'Sales opportunities and prospects',
            'Engagements': 'Customer interaction and engagement data',
            'platform-users': 'Platform user subscription and activity data',
            'Hub-Opportunity': 'Hub-specific opportunity data (draft)'
        }
        return descriptions.get(model_name, 'Business data model')
    
    def _generate_meta_response(self, user_query: str, model_list: List[Dict[str, Any]]) -> str:
        """Generate response for meta-queries"""
        if self.claude_client:
            try:
                prompt = f"""
Generate a helpful response for this meta-query about system structure.

User Query: "{user_query}"
Available Models: {model_list}

Generate a natural response that:
1. Lists the available data models
2. Provides brief descriptions of what each contains  
3. Is helpful for users to understand what data they can query

Format as a clear, organized response.
"""
                return self.claude_client.query(prompt, max_tokens=400)
            except:
                pass
        
        # Fallback response
        response = f"Here are the available data models in the system ({len(model_list)} total):\n\n"
        for i, model in enumerate(model_list, 1):
            status_emoji = "✅" if model['status'] == 'publish' else "🚧"
            response += f"{i}. {status_emoji} **{model['name']}** - {model['description']}\n"
        
        response += f"\nYou can query any of these models by asking questions like:\n"
        response += f"• 'List users' or 'How many users are there?'\n"
        response += f"• 'Show me advertisements' or 'Count the advertisements'\n"
        response += f"• 'List opportunities' or 'Show me engagements'"
        
        return response
    
    def _handle_field_listing_query(self, user_query: str, available_models: List[Dict[str, Any]], 
                                   pipeline_result: Dict[str, Any], pipeline_start_time: float) -> Dict[str, Any]:
        """Handle field listing queries for specific models"""
        print("🔧 Processing Field Listing Query")
        
        # Find the target model
        target_model = None
        for model in available_models:
            model_name = model.get('name', '').lower()
            if model_name in user_query.lower():
                target_model = model
                break
        
        if not target_model:
            return self._handle_pipeline_error("Could not identify the target model for field listing", pipeline_result, pipeline_start_time)
        
        model_id = target_model.get('id')
        model_name = target_model.get('name', 'Unknown')
        print(f"🎯 Target Model: {model_name} ({model_id})")
        
        # Get model fields using MCP client
        try:
            print("🔍 Retrieving model fields from MCP server...")
            if not self.mcp_client:
                raise ValueError("MCP client not available")
            
            fields_result = self.mcp_client.get_model_fields(model_id)
            print(f"✅ Retrieved fields for {model_name}")
            
            # Format field information
            if isinstance(fields_result, dict) and 'fields' in fields_result:
                fields_list = fields_result['fields']
                response_message = self._format_fields_response(model_name, fields_list, user_query)
            else:
                response_message = f"Could not retrieve fields for {model_name} model. The model may not have accessible field information."
            
        except Exception as e:
            print(f"❌ Field retrieval failed: {e}")
            response_message = f"I apologize, but I couldn't retrieve the field information for the {model_name} model. Error: {str(e)}"
        
        execution_time = (time.time() - pipeline_start_time) * 1000
        
        pipeline_result.update({
            'success': True,
            'response': {
                'response_type': 'META_FIELDS',
                'message': response_message
            },
            'pipeline_metadata': {
                'total_execution_time_ms': execution_time,
                'query_analysis': {
                    'intent': 'META',
                    'is_meta_query': True,
                    'target_model': model_name,
                    'query_type': 'field_listing'
                }
            }
        })
        
        return pipeline_result
    
    def _format_fields_response(self, model_name: str, fields_list: List[Dict[str, Any]], user_query: str) -> str:
        """Format the fields information into a user-friendly response"""
        if self.claude_client:
            try:
                prompt = f"""
Format this field information into a helpful response for the user.

User Query: "{user_query}"
Model Name: {model_name}
Fields Data: {fields_list}

Generate a well-organized response that:
1. Shows the model name clearly
2. Lists all fields with their types and descriptions
3. Groups similar fields if applicable
4. Is easy to read and understand
5. Mentions the total number of fields

Format it as a clear, structured response with appropriate headers and formatting.
"""
                return self.claude_client.query(prompt, max_tokens=800)
            except:
                pass
        
        # Fallback formatting
        response = f"# Fields in {model_name} Model\n\n"
        response += f"Here are the {len(fields_list)} fields available in the **{model_name}** model:\n\n"
        
        for i, field in enumerate(fields_list, 1):
            field_name = field.get('name', 'Unknown')
            field_type = field.get('type', 'Unknown')
            field_desc = field.get('description', 'No description available')
            
            response += f"**{i}. {field_name}** ({field_type})\n"
            if field_desc and field_desc != 'No description available':
                response += f"   - {field_desc}\n"
            response += "\n"
        
        response += f"You can use any of these fields when querying the {model_name} model."
        return response
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get current pipeline status and health information
        
        Returns:
            Pipeline status with agent health and version info
        """
        return {
            'version': self.version,
            'health': 'healthy',
            'agents': {
                'query_analyzer': {
                    'status': 'ready',
                    'type': 'pattern_based'
                },
                'model_discovery': {
                    'status': 'ready',
                    'mcp_client': self.mcp_client is not None,
                    'claude_client': self.claude_client is not None
                },
                'field_mapper': {
                    'status': 'ready',
                    'mcp_client': self.mcp_client is not None,
                    'claude_client': self.claude_client is not None
                },
                'query_builder': {
                    'status': 'ready',
                    'query_types_supported': ['COUNT', 'LIST', 'COMPARE', 'ANALYZE']
                },
                'data_retrieval': {
                    'status': 'ready',
                    'mcp_client': self.mcp_client is not None,
                    'cache_enabled': hasattr(self.data_retrieval, 'query_cache')
                },
                'response_generator': {
                    'status': 'ready',
                    'claude_client': self.claude_client is not None,
                    'personalization_supported': True
                }
            },
            'pipeline': {
                'stages': self.pipeline_stages,
                'cache_size': len(self.pipeline_cache),
                'total_stages': len(self.pipeline_stages)
            }
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate pipeline configuration and dependencies
        
        Returns:
            Validation result with errors and warnings
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check agent initialization
        required_agents = [
            ('query_analyzer', self.query_analyzer),
            ('model_discovery', self.model_discovery),
            ('field_mapper', self.field_mapper),
            ('query_builder', self.query_builder),
            ('data_retrieval', self.data_retrieval),
            ('response_generator', self.response_generator)
        ]
        
        for agent_name, agent_instance in required_agents:
            if agent_instance is None:
                validation_result['errors'].append(f"Agent {agent_name} is not initialized")
                validation_result['is_valid'] = False
        
        # Check client dependencies
        if self.mcp_client is None:
            validation_result['warnings'].append("MCP client not configured - using mock data")
        
        if self.claude_client is None:
            validation_result['warnings'].append("Claude client not configured - using fallback responses")
        
        return validation_result
    
    def _handle_stage_error(self, stage_name: str, error_message: str, 
                           pipeline_result: Dict[str, Any], pipeline_start_time: float) -> Dict[str, Any]:
        """Handle error in a specific pipeline stage"""
        total_execution_time = (time.time() - pipeline_start_time) * 1000
        
        pipeline_result.update({
            'success': False,
            'error': f"Error in {stage_name}: {error_message}",
            'failed_stage': stage_name
        })
        pipeline_result['pipeline_metadata']['total_execution_time_ms'] = total_execution_time
        
        # Add stage error metadata
        pipeline_result['pipeline_metadata'][stage_name] = {
            'success': False,
            'error': error_message,
            'execution_time_ms': 0
        }
        
        return pipeline_result
    
    def _handle_pipeline_error(self, error_message: str, pipeline_result: Dict[str, Any], 
                              pipeline_start_time: float) -> Dict[str, Any]:
        """Handle general pipeline error"""
        total_execution_time = (time.time() - pipeline_start_time) * 1000
        
        pipeline_result.update({
            'success': False,
            'error': error_message
        })
        pipeline_result['pipeline_metadata']['total_execution_time_ms'] = total_execution_time
        
        return pipeline_result
    
    def _calculate_mapping_confidence(self, field_mapping: Dict[str, Any]) -> float:
        """Calculate average confidence of field mappings"""
        if not field_mapping:
            return 0.0
        
        confidences = []
        for entity_mapping in field_mapping.values():
            if isinstance(entity_mapping, dict) and 'confidence' in entity_mapping:
                confidences.append(entity_mapping['confidence'])
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _generate_pipeline_cache_key(self, user_query: str, user_context: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for pipeline result"""
        cache_data = {
            'query': user_query.strip().lower(),
            'context': user_context or {}
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()