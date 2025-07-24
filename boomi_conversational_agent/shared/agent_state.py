"""
Enhanced Agent State Management for Phase 8B
MCP June 2025 Compliance with LangGraph Integration
"""

from typing import Dict, Any, List, Optional, TypedDict
import time
from dataclasses import dataclass, field
from enum import Enum

class AuthStatus(Enum):
    """Authentication status enumeration"""
    PENDING = "pending"
    AUTHENTICATED = "authenticated"
    TOKEN_INVALID = "token_invalid"
    EXPIRED = "expired"

class SecurityClearance(Enum):
    """Security clearance levels"""
    PENDING = "pending"
    LAYER1_PASSED = "layer1_passed"
    LAYER2_PASSED = "layer2_passed"
    LAYER3_PASSED = "layer3_passed"
    APPROVED = "approved"
    BLOCKED = "blocked"

class QueryIntent(Enum):
    """Query intent types"""
    COUNT = "COUNT"
    LIST = "LIST"
    COMPARE = "COMPARE"
    ANALYZE = "ANALYZE"
    META = "META"
    UNKNOWN = "UNKNOWN"

class MCPAgentState(TypedDict):
    """Enhanced state for MCP-compliant agentic orchestration"""
    
    # Core Processing
    request_id: str
    user_query: str
    user_context: Dict[str, Any]
    bearer_token: str
    
    # Authentication & Authorization
    auth_status: str          # AuthStatus enum values
    user_role: str           # "executive", "manager", "analyst", "clerk"
    access_permissions: List[str]
    token_validated: bool
    
    # Multi-Agent Orchestration
    query_intent: Optional[str]
    entities: Dict[str, Any]
    discovered_models: List[Dict[str, Any]]
    field_mappings: Dict[str, List[str]]
    constructed_queries: List[Dict[str, Any]]
    
    # Security & Compliance
    security_clearance: str   # SecurityClearance enum values
    threat_assessment: Dict[str, Any]
    audit_trail: List[Dict[str, Any]]
    
    # Results & Response
    query_results: Optional[Dict[str, Any]]
    formatted_response: Optional[str]
    
    # Proactive Capabilities
    suggested_follow_ups: List[str]
    proactive_insights: List[Dict[str, Any]]
    
    # Error Handling
    error_state: Optional[str]
    retry_count: int
    
    # Performance Tracking
    processing_start_time: float
    security_validation_time: float
    query_execution_time: float

@dataclass
class StateTransition:
    """Represents a state transition for audit purposes"""
    timestamp: float
    from_state: str
    to_state: str
    event: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class StateManager:
    """Enhanced state management for LangGraph orchestration"""
    
    def __init__(self):
        self.state_history: List[StateTransition] = []
        self.performance_metrics: Dict[str, List[float]] = {
            "state_transitions": [],
            "security_validations": [],
            "query_executions": []
        }
    
    def create_initial_state(
        self,
        user_query: str,
        user_context: Dict[str, Any],
        bearer_token: str
    ) -> MCPAgentState:
        """Create initial state for LangGraph processing"""
        
        current_time = time.time()
        
        import uuid
        
        initial_state = MCPAgentState(
            # Core Processing
            request_id=str(uuid.uuid4()),
            user_query=user_query,
            user_context=user_context,
            bearer_token=bearer_token,
            
            # Authentication & Authorization
            auth_status=AuthStatus.PENDING.value,
            user_role=user_context.get("role", "unknown"),
            access_permissions=user_context.get("permissions", []),
            token_validated=False,
            
            # Multi-Agent Orchestration
            query_intent=None,
            entities={},
            discovered_models=[],
            field_mappings={},
            constructed_queries=[],
            
            # Security & Compliance
            security_clearance=SecurityClearance.PENDING.value,
            threat_assessment={},
            audit_trail=[],
            
            # Results & Response
            query_results=None,
            formatted_response=None,
            
            # Proactive Capabilities
            suggested_follow_ups=[],
            proactive_insights=[],
            
            # Error Handling
            error_state=None,
            retry_count=0,
            
            # Performance Tracking
            processing_start_time=current_time,
            security_validation_time=0.0,
            query_execution_time=0.0
        )
        
        # Log initial state creation
        self._log_state_transition(
            from_state="NONE",
            to_state="INITIALIZED",
            event="STATE_CREATED",
            metadata={
                "user_role": user_context.get("role", "unknown"),
                "has_bearer_token": bool(bearer_token),
                "query_length": len(user_query)
            }
        )
        
        return initial_state
    
    def update_auth_status(
        self,
        state: MCPAgentState,
        new_status: AuthStatus,
        token_info: Dict[str, Any] = None
    ) -> MCPAgentState:
        """Update authentication status with audit trail"""
        
        old_status = state["auth_status"]
        state["auth_status"] = new_status.value
        
        if new_status == AuthStatus.AUTHENTICATED and token_info:
            state["token_validated"] = True
            state["user_context"].update(token_info)
        
        # Add to audit trail
        state["audit_trail"].append({
            "timestamp": time.time(),
            "event": "AUTH_STATUS_UPDATE",
            "from_status": old_status,
            "to_status": new_status.value,
            "token_info": token_info or {}
        })
        
        self._log_state_transition(
            from_state=old_status,
            to_state=new_status.value,
            event="AUTH_UPDATE",
            metadata={"token_validated": state["token_validated"]}
        )
        
        return state
    
    def update_security_clearance(
        self,
        state: MCPAgentState,
        new_clearance: SecurityClearance,
        assessment_data: Dict[str, Any] = None
    ) -> MCPAgentState:
        """Update security clearance with assessment data"""
        
        old_clearance = state["security_clearance"]
        state["security_clearance"] = new_clearance.value
        
        if assessment_data:
            state["threat_assessment"].update(assessment_data)
        
        # Add to audit trail
        state["audit_trail"].append({
            "timestamp": time.time(),
            "event": "SECURITY_CLEARANCE_UPDATE",
            "from_clearance": old_clearance,
            "to_clearance": new_clearance.value,
            "assessment_data": assessment_data or {}
        })
        
        self._log_state_transition(
            from_state=old_clearance,
            to_state=new_clearance.value,
            event="SECURITY_UPDATE",
            metadata={"blocked": new_clearance == SecurityClearance.BLOCKED}
        )
        
        return state
    
    def add_discovered_model(
        self,
        state: MCPAgentState,
        model_info: Dict[str, Any]
    ) -> MCPAgentState:
        """Add discovered model to state"""
        
        state["discovered_models"].append(model_info)
        
        # Add to audit trail
        state["audit_trail"].append({
            "timestamp": time.time(),
            "event": "MODEL_DISCOVERED",
            "model_name": model_info.get("name", "unknown"),
            "model_info": model_info
        })
        
        return state
    
    def add_proactive_insight(
        self,
        state: MCPAgentState,
        insight_type: str,
        message: str,
        confidence: float,
        action: str = None
    ) -> MCPAgentState:
        """Add proactive insight to state"""
        
        insight = {
            "type": insight_type,
            "message": message,
            "confidence": confidence,
            "timestamp": time.time()
        }
        
        if action:
            insight["action"] = action
        
        state["proactive_insights"].append(insight)
        
        return state
    
    def set_error_state(
        self,
        state: MCPAgentState,
        error_type: str,
        error_message: str,
        retry_allowed: bool = True
    ) -> MCPAgentState:
        """Set error state with retry handling"""
        
        state["error_state"] = error_type
        
        if retry_allowed and state["retry_count"] < 3:
            state["retry_count"] += 1
        
        # Add to audit trail
        state["audit_trail"].append({
            "timestamp": time.time(),
            "event": "ERROR_STATE_SET",
            "error_type": error_type,
            "error_message": error_message,
            "retry_count": state["retry_count"]
        })
        
        self._log_state_transition(
            from_state=state["security_clearance"],
            to_state=f"ERROR_{error_type}",
            event="ERROR_OCCURRED",
            metadata={
                "error_type": error_type,
                "retry_count": state["retry_count"]
            }
        )
        
        return state
    
    def update_performance_metrics(
        self,
        state: MCPAgentState,
        metric_type: str,
        duration: float
    ) -> MCPAgentState:
        """Update performance metrics"""
        
        if metric_type == "security_validation":
            state["security_validation_time"] = duration
        elif metric_type == "query_execution":
            state["query_execution_time"] = duration
        
        # Track in metrics
        if metric_type in self.performance_metrics:
            self.performance_metrics[metric_type].append(duration)
        
        return state
    
    def get_state_summary(self, state: MCPAgentState) -> Dict[str, Any]:
        """Get comprehensive state summary for debugging"""
        
        total_processing_time = time.time() - state["processing_start_time"]
        
        return {
            "state_summary": {
                "user_role": state["user_role"],
                "auth_status": state["auth_status"],
                "security_clearance": state["security_clearance"],
                "query_intent": state["query_intent"],
                "models_discovered": len(state["discovered_models"]),
                "has_results": state["query_results"] is not None,
                "proactive_insights": len(state["proactive_insights"]),
                "error_state": state["error_state"],
                "retry_count": state["retry_count"]
            },
            "performance_metrics": {
                "total_processing_time": total_processing_time,
                "security_validation_time": state["security_validation_time"],
                "query_execution_time": state["query_execution_time"]
            },
            "audit_trail_size": len(state["audit_trail"]),
            "state_transitions": len(self.state_history)
        }
    
    def _log_state_transition(
        self,
        from_state: str,
        to_state: str,
        event: str,
        metadata: Dict[str, Any] = None
    ):
        """Log state transition for audit purposes"""
        
        transition = StateTransition(
            timestamp=time.time(),
            from_state=from_state,
            to_state=to_state,
            event=event,
            metadata=metadata or {}
        )
        
        self.state_history.append(transition)
        
        # Track performance
        self.performance_metrics["state_transitions"].append(
            transition.timestamp
        )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        
        return {
            "total_transitions": len(self.state_history),
            "average_security_validation": (
                sum(self.performance_metrics["security_validations"]) / 
                len(self.performance_metrics["security_validations"])
                if self.performance_metrics["security_validations"] else 0
            ),
            "average_query_execution": (
                sum(self.performance_metrics["query_executions"]) / 
                len(self.performance_metrics["query_executions"])
                if self.performance_metrics["query_executions"] else 0
            ),
            "recent_transitions": [
                {
                    "timestamp": t.timestamp,
                    "event": t.event,
                    "from_state": t.from_state,
                    "to_state": t.to_state
                }
                for t in self.state_history[-10:]  # Last 10 transitions
            ]
        }