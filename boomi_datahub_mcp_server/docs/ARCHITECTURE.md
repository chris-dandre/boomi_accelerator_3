# SYSTEM ARCHITECTURE

**Project**: Boomi DataHub Conversational AI Agent  
**Last Updated**: 2025-01-07  
**Version**: 1.0

## 🏗️ ARCHITECTURE OVERVIEW

The system implements a **multi-tier, multi-agent architecture** that transforms natural language business queries into intelligent Boomi DataHub data retrieval with enterprise-grade security.

```
┌─────────────────────────────────────────────────────────────┐
│                    🌐 Web UI Layer                         │
│              (Streamlit + Authentication)                  │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTPS/WebSocket
┌─────────────────▼───────────────────────────────────────────┐
│              🤖 Agent Orchestration Layer                  │
│       (FastAPI + LangGraph + Security Middleware)         │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │   Query     │   Model     │   Field     │   Query     │  │
│  │  Analyzer   │ Discovery   │  Analyzer   │Constructor  │  │
│  │   Agent     │   Agent     │   Agent     │   Agent     │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
│  ┌─────────────┬─────────────┬─────────────────────────────┐  │
│  │    Data     │  Response   │      Security &             │  │
│  │ Retrieval   │ Synthesizer │   Audit Agent              │  │
│  │   Agent     │   Agent     │                             │  │
│  └─────────────┴─────────────┴─────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────────┘
                  │ MCP Protocol
┌─────────────────▼───────────────────────────────────────────┐
│                🔌 MCP Integration Layer                     │
│          (Enhanced MCP Client v2 Wrapper)                  │
└─────────────────┬───────────────────────────────────────────┘
                  │ MCP Protocol
┌─────────────────▼───────────────────────────────────────────┐
│               📊 Data Access Layer                         │
│          (Existing MCP Server v2 + Boomi Client)           │
└─────────────────┬───────────────────────────────────────────┘
                  │ REST API
┌─────────────────▼───────────────────────────────────────────┐
│                🏢 Boomi DataHub                            │
│           (Golden Records + Data Models)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏛️ TIER BREAKDOWN

### **Tier 1: Web UI Layer**
**Technology**: Streamlit + Custom Components  
**Responsibility**: User interface and basic session management

```python
web_ui/
├── streamlit_app.py           # Main application entry point
├── components/
│   ├── chat_interface.py      # Conversational UI components
│   ├── auth_components.py     # Login and session management
│   └── response_display.py    # Rich response formatting
├── static/
│   ├── styles.css            # Custom styling
│   └── scripts.js            # Client-side enhancements
└── config/
    └── ui_config.py          # Interface configuration
```

**Key Features**:
- Real-time chat interface with typing indicators
- Secure session management with JWT tokens
- Responsive design for desktop and mobile
- Rich response display with charts and tables

### **Tier 2: Agent Orchestration Layer**
**Technology**: FastAPI + LangGraph + Claude 4.0  
**Responsibility**: Multi-agent workflow coordination and business logic

```python
conversational_agent/
├── agent_server.py                    # FastAPI application server
├── workflow/
│   ├── discovery_workflow.py         # LangGraph state machine
│   ├── workflow_state.py             # Shared state management
│   ├── decision_logic.py             # Agent routing logic
│   └── error_recovery.py             # Failure handling
├── agents/
│   ├── base_agent.py                 # Common agent functionality
│   ├── query_analyzer.py             # NL query understanding
│   ├── model_discovery.py            # Boomi model discovery
│   ├── field_analyzer.py             # Field mapping and analysis
│   ├── query_constructor.py          # DataHub query building
│   ├── data_retrieval.py             # MCP execution
│   ├── response_synthesizer.py       # Executive response generation
│   └── security_agent.py             # Guardrails and audit
├── security/
│   ├── auth_middleware.py            # Authentication and RBAC
│   ├── guardrails.py                 # Query validation and blocking
│   ├── jailbreak_detector.py         # Prompt injection prevention
│   └── audit_logger.py               # Security event logging
└── llm/
    ├── claude_client.py              # Anthropic API integration
    ├── prompt_templates.py           # Reusable prompts
    └── response_parsers.py           # LLM output processing
```

### **Tier 3: MCP Integration Layer**
**Technology**: Enhanced MCP Client v2 Wrapper  
**Responsibility**: Abstraction over existing MCP infrastructure

```python
mcp_integration/
├── enhanced_mcp_client.py            # Wrapper around existing v2 client
├── model_cache.py                    # Metadata caching
├── query_optimizer.py               # Query performance optimization
└── error_translator.py              # MCP error handling
```

### **Tier 4: Data Access Layer**
**Technology**: Existing MCP Server v2 + Boomi DataHub Client  
**Responsibility**: Data retrieval from Boomi DataHub (Preserve existing)

---

## 🤖 MULTI-AGENT WORKFLOW

### **Agent State Machine (LangGraph)**

```python
# Workflow States
class WorkflowState(TypedDict):
    user_query: str
    user_context: Dict[str, Any]
    intent: Optional[str]
    entities: List[Dict[str, Any]]
    candidate_models: List[Dict[str, Any]]
    selected_models: List[str]
    field_mappings: Dict[str, List[str]]
    constructed_query: Optional[Dict[str, Any]]
    query_results: Optional[Dict[str, Any]]
    final_response: Optional[str]
    security_status: str
    error_state: Optional[str]

# Agent Flow
START → SECURITY_CHECK → QUERY_ANALYSIS → MODEL_DISCOVERY → 
FIELD_ANALYSIS → QUERY_CONSTRUCTION → DATA_RETRIEVAL → 
RESPONSE_SYNTHESIS → AUDIT_LOG → END
```

### **Agent Specialization**

#### **1. Query Analyzer Agent**
**Purpose**: Parse natural language into structured intent and entities

```python
Input:  "How many Sony products are we launching this quarter?"
Output: {
    "intent": "COUNT_AGGREGATION",
    "entities": [
        {"text": "Sony", "type": "BRAND", "confidence": 0.95},
        {"text": "products", "type": "OBJECT", "confidence": 0.98},
        {"text": "this quarter", "type": "TIME_PERIOD", "confidence": 0.92}
    ],
    "query_type": "BUSINESS_INTELLIGENCE",
    "complexity": "MEDIUM"
}
```

#### **2. Model Discovery Agent**
**Purpose**: Find relevant Boomi DataHub models using LLM reasoning

```python
Input:  Query intent + entities
Process: 
  1. Retrieve all available models via MCP
  2. Use Claude 4.0 to rank models by relevance
  3. Select optimal model combination
Output: [
    {"model_id": "Product", "relevance": 0.98, "role": "primary"},
    {"model_id": "Launch", "relevance": 0.85, "role": "secondary"},
    {"model_id": "Brand", "relevance": 0.72, "role": "filter"}
]
```

#### **3. Field Analyzer Agent**
**Purpose**: Map entities to specific model fields using semantic analysis

```python
Input:  Entities + Selected models + Model field definitions
Process:
  1. Get detailed field info for each model
  2. Use Claude 4.0 for semantic field mapping
  3. Identify necessary joins and relationships
Output: {
    "Product": {
        "Sony": ["brand_name", "manufacturer"],
        "products": ["product_id", "product_name", "sku"]
    },
    "Launch": {
        "this quarter": ["launch_date", "quarter_year"]
    },
    "joins": [{"Product.brand_id": "Brand.brand_id"}]
}
```

#### **4. Query Constructor Agent**
**Purpose**: Build optimal Boomi DataHub queries from mappings

```python
Input:  Field mappings + Query intent
Process:
  1. Construct filters based on entity mappings
  2. Determine necessary aggregations
  3. Optimize for performance
Output: {
    "universe_id": "universe_123",
    "repository_id": "repo_456", 
    "fields": ["product_id", "product_name", "launch_date"],
    "filters": [
        {"field": "brand_name", "operator": "=", "value": "Sony"},
        {"field": "launch_date", "operator": ">=", "value": "2024-10-01"}
    ],
    "aggregation": {"type": "COUNT", "field": "product_id"}
}
```

#### **5. Data Retrieval Agent**
**Purpose**: Execute queries via MCP Client v2 and handle results

```python
Input:  Constructed query
Process:
  1. Execute via enhanced MCP client
  2. Handle pagination if needed
  3. Aggregate results from multiple queries
  4. Apply post-processing
Output: {
    "total_count": 47,
    "results": [...],
    "metadata": {"execution_time": "1.2s", "source": "Boomi DataHub"}
}
```

#### **6. Response Synthesizer Agent**
**Purpose**: Generate executive-friendly responses with insights

```python
Input:  Raw query results + Original query context
Process:
  1. Analyze results for trends and insights
  2. Generate business-appropriate language
  3. Add context and recommendations
Output: "Sony is launching 47 products this quarter, representing a 28% 
         increase from last quarter's 18 products. This indicates strong 
         Sony partnership growth and suggests increased market confidence 
         in their product portfolio."
```

#### **7. Security & Audit Agent**
**Purpose**: Continuous security monitoring and compliance logging

```python
# Runs in parallel with all other agents
Responsibilities:
  - Pre-query security validation
  - Jailbreak attempt detection
  - Access control enforcement
  - Comprehensive audit logging
  - Real-time threat monitoring
```

---

## 🔒 SECURITY ARCHITECTURE

### **Multi-Layer Security Model**

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Authentication & Session Management              │
│  ├── JWT Token Validation                                  │
│  ├── Session Timeout Enforcement                           │
│  └── Multi-Factor Authentication (Future)                  │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Role-Based Access Control (RBAC)                 │
│  ├── User Role Assignment (Executive, Manager, Clerk)      │
│  ├── Permission Matrix Enforcement                         │
│  └── Feature-Level Access Control                          │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Query Guardrails & Context Validation            │
│  ├── Business Context Enforcement                          │
│  ├── Query Scope Limitation                                │
│  └── Out-of-Scope Query Blocking                           │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Jailbreak Detection & Prevention                 │
│  ├── Prompt Injection Pattern Matching                     │
│  ├── Behavioral Anomaly Detection                          │
│  └── Real-time Threat Analysis                             │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: Audit & Compliance Logging                       │
│  ├── All Interactions Logged                               │
│  ├── Security Event Tracking                               │
│  └── Compliance Report Generation                          │
└─────────────────────────────────────────────────────────────┘
```

### **Security Components**

#### **Authentication Middleware**
```python
@app.middleware("http")
async def authentication_middleware(request: Request, call_next):
    # Validate JWT tokens
    # Check session timeout
    # Enforce rate limiting
    # Log authentication events
```

#### **RBAC Permission Matrix**
```python
PERMISSIONS = {
    "executive": {
        "models": ["ALL"],
        "fields": ["ALL"], 
        "query_types": ["ALL"],
        "rate_limit": "100/hour"
    },
    "manager": {
        "models": ["Product", "Campaign"],
        "fields": ["SUBSET"],
        "query_types": ["READ_ONLY"],
        "rate_limit": "50/hour"
    },
    "clerk": {
        "models": [],
        "fields": [],
        "query_types": [],
        "rate_limit": "10/hour"  # Login attempts only
    }
}
```

#### **Jailbreak Detection Patterns**
```python
SECURITY_PATTERNS = [
    # Prompt injection attempts
    r"ignore.*(previous|all|initial).*(instruction|prompt|rule)",
    r"you are now",
    r"pretend.*you are",
    r"override.*security",
    
    # System access attempts  
    r"show.*\.env",
    r"access.*file",
    r"list.*directory",
    r"run.*command",
    
    # Role escalation attempts
    r"make me.*admin",
    r"grant.*permission",
    r"bypass.*security"
]
```

---

## 📊 DATA FLOW ARCHITECTURE

### **End-to-End Query Processing**

```
1. User Query Input
   ↓
2. Authentication & Session Validation
   ↓  
3. RBAC Permission Check
   ↓
4. Security Guardrails & Jailbreak Detection
   ↓
5. Query Analysis (Intent + Entity Extraction)
   ↓
6. Model Discovery (LLM-powered relevance ranking)
   ↓
7. Field Analysis (Semantic entity-to-field mapping)
   ↓
8. Query Construction (DataHub query building)
   ↓
9. Data Retrieval (MCP Client v2 execution)
   ↓
10. Response Synthesis (Executive-friendly formatting)
    ↓
11. Audit Logging (Security + compliance)
    ↓
12. Response Delivery (Streaming to UI)
```

### **State Management**

```python
# Workflow state persistence
class StateManager:
    def __init__(self):
        self.redis_client = Redis()  # For session state
        self.db_client = SQLite()    # For audit logs
        
    async def save_workflow_state(self, session_id: str, state: WorkflowState):
        # Persist state for error recovery
        
    async def get_conversation_history(self, user_id: str):
        # Retrieve context for follow-up queries
```

---

## 🔧 INTEGRATION ARCHITECTURE

### **MCP Integration Strategy**

```python
# Wrapper pattern to preserve existing functionality
class EnhancedMCPClient:
    def __init__(self):
        # Use existing MCP Client v2 as foundation
        self.base_client = BoomiDataHubMCPClient()
        self.cache = ModelCache()
        self.optimizer = QueryOptimizer()
    
    async def get_models_with_intelligence(self, query_context: Dict):
        # Add LLM-powered model ranking on top of base client
        
    async def execute_optimized_query(self, query: Dict):
        # Add caching and optimization layer
```

### **Claude 4.0 Integration**

```python
class ClaudeClient:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.rate_limiter = RateLimiter(max_calls=1000, period=3600)
    
    async def rank_models_by_relevance(self, query: str, models: List[Dict]):
        # Use Claude 4.0 for intelligent model selection
        
    async def map_entities_to_fields(self, entities: List, fields: Dict):
        # Use Claude 4.0 for semantic field mapping
```

### **Performance Architecture**

#### **Caching Strategy**
```python
# Multi-level caching
class CacheManager:
    def __init__(self):
        self.memory_cache = {}        # Fast access for frequent data
        self.redis_cache = Redis()    # Session and temporary data
        self.disk_cache = SQLite()    # Model metadata persistence
        
    async def get_model_metadata(self, model_id: str):
        # Check memory → Redis → Disk → MCP Server
```

#### **Performance Targets**
- **Simple Queries**: <5 seconds (cached model metadata)
- **Complex Queries**: <15 seconds (with LLM processing)
- **Concurrent Users**: 10+ simultaneous sessions
- **Cache Hit Rate**: >80% for model/field metadata

---

## 🚀 DEPLOYMENT ARCHITECTURE

### **Development Environment**
```bash
# Local development setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start all services
python conversational_agent/agent_server.py &    # FastAPI backend
streamlit run web_ui/streamlit_app.py &          # Web interface
python boomi_mcp_server/boomi_datahub_mcp_server_v2.py &  # MCP server
```

### **Production Considerations**
```yaml
# Docker composition for production
services:
  agent-server:
    build: ./conversational_agent
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
      - mcp-server
      
  web-ui:
    build: ./web_ui
    ports:
      - "8501:8501"
    depends_on:
      - agent-server
      
  mcp-server:
    build: ./boomi_mcp_server
    environment:
      - BOOMI_USERNAME=${BOOMI_USERNAME}
      - BOOMI_PASSWORD=${BOOMI_PASSWORD}
      
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

---

## 📈 SCALABILITY DESIGN

### **Horizontal Scaling Points**
1. **Agent Processing**: Each agent can be scaled independently
2. **MCP Client Pool**: Multiple MCP client instances for load distribution  
3. **Cache Layer**: Redis cluster for distributed caching
4. **LLM API**: Rate limiting and request queuing

### **Future Extension Points**
1. **New Data Sources**: Plugin architecture for additional data connectors
2. **Additional Agents**: Framework supports adding specialized agents
3. **Advanced UI**: React/Next.js replacement for Streamlit
4. **Enterprise SSO**: Integration with corporate authentication systems

---

*This architecture provides a robust, secure, and scalable foundation for the conversational AI agent while preserving and building upon the existing MCP infrastructure.*