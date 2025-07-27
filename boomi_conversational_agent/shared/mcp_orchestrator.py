"""
Unified MCP Orchestrator for Phase 8B
LangGraph-based proactive orchestration with enhanced features
"""

import os
import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from redis.asyncio import Redis
from pybreaker import CircuitBreaker
from prometheus_client import Counter, Histogram
import requests
from cli_agent.pipeline.agent_pipeline import AgentPipeline
from security.hybrid_semantic_analyzer import HybridSemanticAnalyzer
from security.audit_logger import audit_logger, AuditEvent, AuditEventType, AuditSeverity
from claude_client import ClaudeClient
from shared.agent_state import MCPAgentState, StateManager, AuthStatus, SecurityClearance
from shared.workflow_nodes import WorkflowNodes

load_dotenv()

query_counter = Counter('mcp_queries_total', 'Total queries processed', ['interface_type'])
query_latency = Histogram('mcp_query_latency_seconds', 'Query processing latency', ['interface_type'])

breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

class UnifiedMCPOrchestrator:
    """Unified orchestrator supporting both CLI and Web interfaces"""
    
    def __init__(self, interface_type: Literal["cli", "web", "mcp"] = "cli"):
        self.interface_type = interface_type
        self.state_manager = StateManager()
        self.workflow_nodes = None
        self.agent_graph = None
        self._initialize_dependencies()
        self._build_langgraph_workflow()
    
    def _initialize_dependencies(self):
        """Initialize required dependencies"""
        try:
            class MCPAuthenticatedClient:
                """MCP client with OAuth 2.1 Bearer token authentication"""
                
                def __init__(self, access_token: str = None, server_url: str = os.getenv("OAUTH_SERVER_URL", "http://127.0.0.1:8001")):
                    self.access_token = access_token
                    self.server_url = server_url
                    self.session = requests.Session()
                    self.headers = {
                        "Content-Type": "application/json",
                        "MCP-Protocol-Version": "2025-06-18",
                        "resource": "https://localhost:8001"
                    }
                    if access_token:
                        self.headers["Authorization"] = f"Bearer {access_token}"
                
                def set_bearer_token(self, token: str):
                    """Set bearer token for authentication"""
                    self.access_token = token
                    self.headers["Authorization"] = f"Bearer {token}"
                
                @breaker
                def get_all_models(self):
                    """Get all models via MCP JSON-RPC 2.0"""
                    try:
                        print("📡 MCP Client→Server: Calling get_all_models()")
                        payload = {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "resources/read",
                            "params": {
                                "uri": "boomi://datahub/models/all"
                            }
                        }
                        print("🔄 MCP Server: Processing model discovery request")
                        response = self.session.post(
                            f"{self.server_url}/mcp",
                            headers=self.headers,
                            json=payload
                        )
                        if response.status_code == 200:
                            result = response.json()
                            if "result" in result:
                                models_data = json.loads(result["result"])
                                model_count = len(models_data.get("models", [])) if isinstance(models_data.get("models"), list) else "unknown"
                                print(f"✅ MCP Server→Client: Response received - {model_count} models found")
                                return models_data
                            elif "error" in result:
                                print(f"❌ MCP Server→Client: Error response - {result['error']['message']}")
                                return {"status": "error", "error": result["error"]["message"]}
                            else:
                                print("❌ MCP Server→Client: Invalid response format")
                                return {"status": "error", "error": "Invalid MCP response"}
                        elif response.status_code == 401:
                            print("❌ MCP Server→Client: Authentication failed")
                            return {"status": "error", "error": "Authentication required"}
                        elif response.status_code == 403:
                            print("❌ MCP Server→Client: Access denied")
                            return {"status": "error", "error": "Access denied"}
                        else:
                            print(f"❌ MCP Server→Client: HTTP error {response.status_code}")
                            return {"status": "error", "error": f"HTTP {response.status_code}: {response.text}"}
                    except Exception as e:
                        return {"status": "error", "error": str(e)}
                
                @breaker
                def get_model_fields(self, model_id: str):
                    """Get model fields via MCP JSON-RPC 2.0"""
                    try:
                        payload = {
                            "jsonrpc": "2.0",
                            "id": 5,
                            "method": "tools/call",
                            "params": {
                                "name": "get_model_fields",
                                "arguments": {"model_id": model_id}
                            }
                        }
                        response = self.session.post(
                            f"{self.server_url}/mcp",
                            headers=self.headers,
                            json=payload
                        )
                        if response.status_code == 200:
                            result = response.json()
                            if "result" in result:
                                return result["result"]
                            elif "error" in result:
                                return {"status": "error", "error": result["error"]["message"]}
                            else:
                                return {"status": "error", "error": "Invalid MCP response"}
                        else:
                            return {"status": "error", "error": f"HTTP {response.status_code}: {response.text}"}
                    except Exception as e:
                        return {"status": "error", "error": str(e)}
                
                @breaker
                def query_records(self, model_id: str, fields: list = None, filters: list = None, limit: int = 100):
                    """Query records via MCP JSON-RPC 2.0"""
                    try:
                        payload = {
                            "jsonrpc": "2.0",
                            "id": 7,
                            "method": "tools/call",
                            "params": {
                                "name": "query_records",
                                "arguments": {
                                    "model_id": model_id,
                                    "fields": fields or [],
                                    "filters": filters or [],
                                    "limit": limit
                                }
                            }
                        }
                        response = self.session.post(
                            f"{self.server_url}/mcp",
                            headers=self.headers,
                            json=payload
                        )
                        if response.status_code == 200:
                            result = response.json()
                            if "result" in result:
                                return result["result"]
                            elif "error" in result:
                                return {"status": "error", "error": result["error"]["message"]}
                            else:
                                return {"status": "error", "error": "Invalid MCP response"}
                        else:
                            return {"status": "error", "error": f"HTTP {response.status_code}: {response.text}"}
                    except Exception as e:
                        return {"status": "error", "error": str(e)}
                
                def close(self):
                    """Close HTTP session"""
                    if self.session:
                        self.session.close()
                        print("✅ MCPAuthenticatedClient session closed")
            
            class MCPClientAdapter:
                """Adapter to make MCPAuthenticatedClient compatible with CLI Agent Pipeline"""
                def __init__(self, mcp_client):
                    self.mcp_client = mcp_client
                
                def set_bearer_token(self, token: str):
                    self.mcp_client.set_bearer_token(token)
                
                def get_all_models(self):
                    try:
                        result = self.mcp_client.get_all_models()
                        if isinstance(result, dict):
                            if "status" in result and result["status"] == "error":
                                return {"status": "error", "error": result["error"], "models": []}
                            elif "data" in result:
                                data = result["data"]
                                if isinstance(data, dict):
                                    published = data.get("published", [])
                                    draft = data.get("draft", [])
                                    models = published + draft
                                    return {"status": "success", "models": models}
                                else:
                                    return {"status": "success", "models": data}
                            else:
                                return {"status": "success", "models": result}
                        else:
                            return {"status": "success", "models": result}
                    except Exception as e:
                        return {"status": "error", "error": str(e), "models": []}
                
                def get_model_fields(self, model_id: str):
                    try:
                        result = self.mcp_client.get_model_fields(model_id)
                        if result.get('status') == 'success':
                            return result
                        else:
                            return {"status": "error", "error": result.get('error', 'Unknown error')}
                    except Exception as e:
                        return {"status": "error", "error": str(e)}
                
                def execute_query(self, query: Dict[str, Any]):
                    try:
                        model_id = query.get('model_id')
                        fields = query.get('fields', [])
                        filters = query.get('filters', [])
                        limit = query.get('limit', 100)
                        
                        # Debug the exact query being sent
                        print(f"🔍 MCP Execute Query Debug:")
                        print(f"   Model ID: {model_id}")
                        print(f"   Fields: {fields}")
                        print(f"   Filters: {filters}")
                        print(f"   Limit: {limit}")
                        print(f"   Full query: {query}")
                        payload = {
                            "jsonrpc": "2.0",
                            "id": 8,
                            "method": "tools/call",
                            "params": {
                                "name": "query_records",
                                "arguments": {
                                    "model_id": model_id,
                                    "fields": fields or [],
                                    "filters": filters or [],
                                    "limit": limit
                                }
                            }
                        }
                        response = self.mcp_client.session.post(
                            f"{self.mcp_client.server_url}/mcp",
                            headers=self.mcp_client.headers,
                            json=payload
                        )
                        if response.status_code == 200:
                            result = response.json()
                            if "result" in result:
                                return result["result"]
                            elif "error" in result:
                                return {"status": "error", "error": result["error"]["message"]}
                            else:
                                return {"status": "error", "error": "Invalid MCP response"}
                        else:
                            return {"status": "error", "error": f"HTTP {response.status_code}: {response.text}"}
                    except Exception as e:
                        return {"status": "error", "error": str(e)}
            
            mcp_auth_client = MCPAuthenticatedClient()
            mcp_client = MCPClientAdapter(mcp_auth_client)
            print(f"✅ MCP client adapter initialized: {type(mcp_client)}")
            
            security_engine = HybridSemanticAnalyzer()
            claude_client = ClaudeClient()
            
            self.workflow_nodes = WorkflowNodes(
                mcp_client=mcp_client,
                security_engine=security_engine,
                claude_client=claude_client
            )
            
            print("✅ Dependencies initialized successfully")
            
        except Exception as e:
            print(f"⚠️  Dependency initialization error: {e}")
            self.workflow_nodes = WorkflowNodes()
    
    def _build_langgraph_workflow(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(MCPAgentState)
        
        workflow.add_node("validate_bearer_token", self.workflow_nodes.validate_bearer_token)
        workflow.add_node("check_user_authorization", self.workflow_nodes.check_user_authorization)
        workflow.add_node("comprehensive_security_analysis", self.workflow_nodes.comprehensive_security_analysis)
        workflow.add_node("execute_query", self._execute_query)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("generate_insights", self.workflow_nodes.generate_insights)
        workflow.add_node("suggest_follow_ups", self.workflow_nodes.suggest_follow_ups)
        
        workflow.add_edge(START, "validate_bearer_token")
        workflow.add_conditional_edges(
            "validate_bearer_token",
            self._route_after_token_validation,
            {"authorized": "check_user_authorization", "unauthorized": END}
        )
        workflow.add_conditional_edges(
            "check_user_authorization",
            self._route_after_authorization,
            {"approved": "comprehensive_security_analysis", "blocked": END}
        )
        workflow.add_conditional_edges(
            "comprehensive_security_analysis",
            self._route_after_security,
            {"approved": "execute_query", "blocked": END}
        )
        workflow.add_edge("execute_query", "generate_response")
        workflow.add_edge("generate_response", "generate_insights")
        workflow.add_edge("generate_insights", "suggest_follow_ups")
        workflow.add_edge("suggest_follow_ups", END)
        
        self.agent_graph = workflow.compile()
        print("✅ LangGraph workflow compiled successfully")
    
    def _route_after_token_validation(self, state: MCPAgentState) -> str:
        if state["token_validated"]:
            return "authorized"
        else:
            return "unauthorized"
    
    def _route_after_authorization(self, state: MCPAgentState) -> str:
        if state["security_clearance"] == SecurityClearance.BLOCKED.value:
            return "blocked"
        else:
            return "approved"
    
    def _route_after_security(self, state: MCPAgentState) -> str:
        if state["security_clearance"] == SecurityClearance.APPROVED.value:
            return "approved"
        else:
            return "blocked"
    
    async def _execute_query(self, state: MCPAgentState) -> MCPAgentState:
        print("🤖 AGENTIC AI PROCESSING LAYER: Query Execution")
        start_time = time.time()
        
        try:
            # Set bearer token on MCP client for authentication (like the working backup)
            if hasattr(self.workflow_nodes.mcp_client, 'set_bearer_token') and state.get("bearer_token"):
                self.workflow_nodes.mcp_client.set_bearer_token(state["bearer_token"])
                print(f"🔐 Query Execution: Set bearer token for MCP client")
            
            # Import and use AgentPipeline (the working approach!)
            from cli_agent.pipeline.agent_pipeline import AgentPipeline
            
            pipeline = AgentPipeline(
                mcp_client=self.workflow_nodes.mcp_client,
                claude_client=self.workflow_nodes.claude_client
            )
            
            # Prepare user context with field_mappings (matching backup format)
            user_context = {
                "query_intent": state.get("query_intent", "UNKNOWN"),
                "field_mappings": state.get("field_mappings", {}),
                "role": state.get("user_role", "unknown"),
                "username": state.get("user_context", {}).get("username", "anonymous"),
                "permissions": state.get("access_permissions", []),
                "has_data_access": state.get("user_context", {}).get("has_data_access", False)
            }
            
            results = pipeline.process_query(
                user_query=state["user_query"],
                user_context=user_context,
                enable_cache=False
            )
            
            state["query_results"] = results
            
            execution_time = time.time() - start_time
            state = self.state_manager.update_performance_metrics(
                state, "query_execution", execution_time
            )
            
            if results.get("success"):
                print(f"✅ Query executed successfully in {execution_time:.2f}s")
            else:
                print(f"❌ Query execution failed: {results.get('error', 'Unknown error')}")
            
        except Exception as e:
            print(f"❌ Query execution error: {e}")
            state = self.state_manager.set_error_state(
                state, "QUERY_EXECUTION_ERROR", str(e)
            )
        
        return state
    
    async def _generate_response(self, state: MCPAgentState) -> MCPAgentState:
        print("🤖 AGENTIC AI PROCESSING LAYER: LLM-Based Response Generation")
        
        try:
            query_results = state["query_results"]
            print(f"🔍 Query Results Type: {type(query_results)}")
            
            if isinstance(query_results, dict) and "response" in query_results:
                print("✅ Using response from CLI pipeline")
                state["formatted_response"] = query_results["response"]
                
            elif isinstance(query_results, dict) and "success" in query_results:
                if not query_results["success"]:
                    print("❌ Query failed, using error response from CLI pipeline")
                    state["formatted_response"] = {
                        "response_type": "ERROR",
                        "message": query_results.get("error", "Unknown error occurred")
                    }
                else:
                    from cli_agent.agents.response_generator import ResponseGenerator
                    generator = ResponseGenerator(claude_client=self.workflow_nodes.claude_client)
                    
                    response = generator.generate_response(
                        query_result=query_results,
                        user_query=state["user_query"],
                        user_context=state["user_context"]
                    )
                    state["formatted_response"] = response
            else:
                from cli_agent.agents.response_generator import ResponseGenerator
                generator = ResponseGenerator(claude_client=self.workflow_nodes.claude_client)
                
                response = generator.generate_response(
                    query_result=query_results,
                    user_query=state["user_query"],
                    user_context=state["user_context"]
                )
                state["formatted_response"] = response
            
            print("✅ Response generated successfully")
            
        except Exception as e:
            print(f"❌ Response generation error: {e}")
            state["formatted_response"] = {
                "response_type": "ERROR",
                "message": f"Error generating response: {e}"
            }
        
        return state
    
    async def process_query(self, query: str, user_context: dict, bearer_token: str) -> dict:
        query_counter.labels(interface_type=self.interface_type).inc()
        start_time = time.time()
        
        # Log query start
        username = user_context.get('username', 'anonymous')
        user_role = user_context.get('role', 'unknown')
        
        await audit_logger.log_event(AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            severity=AuditSeverity.INFO,
            user_id=username,
            endpoint=f"/{self.interface_type}/query",
            method="POST",
            success=True,
            details={
                "query": query[:100] + "..." if len(query) > 100 else query,  # Truncate long queries
                "user_role": user_role,
                "interface_type": self.interface_type,
                "query_length": len(query)
            }
        ))
        
        with query_latency.labels(interface_type=self.interface_type).time():
            print(f"🚀 Starting unified orchestration for {self.interface_type} interface")
            print(f"   Query: {query}")
            print(f"   User: {username}")
            print(f"   Role: {user_role}")
            
            initial_state = self.state_manager.create_initial_state(
                user_query=query,
                user_context=user_context,
                bearer_token=bearer_token
            )
            
            try:
                final_state = await self.agent_graph.ainvoke(initial_state)
                await self.store_state(final_state)
                
                # Log successful completion
                processing_time = (time.time() - start_time) * 1000
                success = final_state.get("error_state") is None
                
                await audit_logger.log_event(AuditEvent(
                    event_type=AuditEventType.API_SUCCESS,
                    severity=AuditSeverity.INFO,
                    user_id=username,
                    endpoint=f"/{self.interface_type}/query",
                    method="POST",
                    success=success,
                    processing_time_ms=processing_time,
                    details={
                        "security_clearance": final_state.get("security_clearance", "unknown"),
                        "query_intent": final_state.get("query_intent", "unknown"),
                        "models_discovered": len(final_state.get("discovered_models", [])),
                        "error_state": final_state.get("error_state"),
                        "interface_type": self.interface_type
                    }
                ))
                
                if self.interface_type == "web":
                    return self._format_web_response(final_state)
                elif self.interface_type == "mcp":
                    return self._format_mcp_response(final_state)
                else:
                    return self._format_cli_response(final_state)
                    
            except Exception as e:
                print(f"❌ Orchestration error: {e}")
                
                # Log error
                processing_time = (time.time() - start_time) * 1000
                await audit_logger.log_event(AuditEvent(
                    event_type=AuditEventType.API_FAILURE,
                    severity=AuditSeverity.ERROR,
                    user_id=username,
                    endpoint=f"/{self.interface_type}/query",
                    method="POST",
                    success=False,
                    processing_time_ms=processing_time,
                    details={
                        "error": str(e),
                        "interface_type": self.interface_type,
                        "error_type": type(e).__name__
                    }
                ))
                
                return self._format_error_response(str(e))
    
    async def store_state(self, state: MCPAgentState):
        try:
            redis = Redis(host='localhost', port=6379)
            state_id = f"request:{state['request_id']}"
            await redis.set(state_id, json.dumps(state, default=str))
            await redis.expire(state_id, 3600)
            print(f"✅ State stored in Redis for request: {state['request_id']}")
        except Exception as e:
            # print(f"⚠️ Redis not available, skipping state storage: {e}")
            # Continue without Redis - not critical for basic operation
            print(f"⚠️ Redis not available, skipping state storage")
    
    def _format_web_response(self, state: MCPAgentState) -> dict:
        success = state.get("error_state") is None
        return {
            "success": success,
            "response": state.get("formatted_response", ""),
            "proactive_insights": state.get("proactive_insights", []),
            "suggested_follow_ups": state.get("suggested_follow_ups", []),
            "security_status": state.get("security_clearance", "unknown"),
            "execution_metadata": {
                "user_role": state.get("user_role", "unknown"),
                "models_discovered": len(state.get("discovered_models", [])),
                "query_intent": state.get("query_intent", "unknown"),
                "security_layers_passed": self._count_security_layers(state),
                "processing_time": time.time() - state.get("processing_start_time", 0),
                "error_state": state.get("error_state")
            }
        }
    
    def _format_cli_response(self, state: MCPAgentState) -> dict:
        success = state.get("error_state") is None
        return {
            "success": success,
            "response": state.get("formatted_response", ""),
            "response_type": "LANGGRAPH_ORCHESTRATED",
            "pipeline_metadata": {
                "security_clearance": state.get("security_clearance", "unknown"),
                "query_intent": state.get("query_intent", "unknown"),
                "models_discovered": len(state.get("discovered_models", [])),
                "proactive_insights": state.get("proactive_insights", []),
                "suggested_follow_ups": state.get("suggested_follow_ups", []),
                "processing_time": time.time() - state.get("processing_start_time", 0),
                "error_state": state.get("error_state")
            }
        }
    
    def _format_mcp_response(self, state: MCPAgentState) -> dict:
        success = state.get("error_state") is None
        return {
            "jsonrpc": "2.0",
            "result": {
                "success": success,
                "content": state.get("formatted_response", ""),
                "metadata": {
                    "security_clearance": state.get("security_clearance", "unknown"),
                    "query_intent": state.get("query_intent", "unknown"),
                    "models_discovered": len(state.get("discovered_models", [])),
                    "processing_time": time.time() - state.get("processing_start_time", 0),
                    "mcp_compliance": "2025-06-18"
                }
            }
        }
    
    def _format_error_response(self, error_message: str) -> dict:
        if self.interface_type == "web":
            return {
                "success": False,
                "error": error_message,
                "proactive_insights": [],
                "suggested_follow_ups": [],
                "security_status": "error"
            }
        elif self.interface_type == "mcp":
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": error_message
                }
            }
        else:
            return {
                "success": False,
                "error": error_message,
                "response_type": "ERROR"
            }
    
    def _count_security_layers(self, state: MCPAgentState) -> int:
        clearance = state.get("security_clearance", "pending")
        if clearance == SecurityClearance.APPROVED.value:
            return 4
        elif clearance == SecurityClearance.LAYER3_PASSED.value:
            return 3
        elif clearance == SecurityClearance.LAYER2_PASSED.value:
            return 2
        elif clearance == "layer1_passed":
            return 1
        else:
            return 0
    
    def get_state_summary(self) -> dict:
        return {
            "orchestrator_type": self.interface_type,
            "workflow_nodes_initialized": self.workflow_nodes is not None,
            "graph_compiled": self.agent_graph is not None,
            "performance_metrics": self.state_manager.get_performance_report()
        }
    
    async def process_mcp_request(self, mcp_request: dict, user_context: dict, bearer_token: str) -> dict:
        method = mcp_request.get("method", "")
        params = mcp_request.get("params", {})
        if method == "resources/list":
            query = "list models in datahub"
        elif method == "resources/read":
            resource_uri = params.get("uri", "")
            query = f"show data from {resource_uri}"
        else:
            query = params.get("query", "")
        return await self.process_query(query, user_context, bearer_token)

def create_orchestrator(interface_type: Literal["cli", "web", "mcp"] = "cli") -> UnifiedMCPOrchestrator:
    return UnifiedMCPOrchestrator(interface_type=interface_type)