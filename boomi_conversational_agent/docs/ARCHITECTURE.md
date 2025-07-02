# SYSTEM ARCHITECTURE

**Project**: Boomi DataHub Conversational AI Agent  
**Last Updated**: 2025-07-02  
**Version**: 2.0 (Phase 5 Complete, Phase 6 Ready)

## 🏗️ ARCHITECTURE OVERVIEW

The system implements a **multi-tier, multi-agent architecture** that transforms natural language business queries into intelligent Boomi DataHub data retrieval. **Phase 5 (CLI Agent Foundation) is complete** with 100% success rate on real queries using dynamic field discovery.

### Current Implementation Status
- ✅ **Phase 5 Complete**: CLI-based conversational agent with 6-agent pipeline
- ✅ **Dynamic Discovery**: Real-time model and field discovery from Boomi DataHub
- ✅ **TDD Implementation**: 76/76 tests passing with comprehensive coverage
- ✅ **Real Data Integration**: Working end-to-end with live Boomi DataHub
- 🎯 **Phase 6 Ready**: Security & Guardrails implementation planned

### Phase 5 Implementation (✅ COMPLETE)
```
┌─────────────────────────────────────────────────────────────┐
│                    🖥️ CLI Interface                        │
│              (Python CLI + Session Management)             │
└─────────────────┬───────────────────────────────────────────┘
                  │ Direct Function Calls
┌─────────────────▼───────────────────────────────────────────┐
│              🤖 6-Agent Sequential Pipeline                │
│                (TDD-Tested, 76/76 passing)                │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │   Query     │   Model     │   Field     │   Query     │  │
│  │  Analyzer   │ Discovery   │  Mapper     │ Builder     │  │
│  │  (Pattern)  │(Dynamic+LLM)│(Dynamic+LLM)│(Dynamic)    │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
│  ┌─────────────┬─────────────┬─────────────────────────────┐  │
│  │    Data     │  Response   │      Agent Pipeline         │  │
│  │ Retrieval   │ Generator   │    Orchestration            │  │
│  │ (MCP Client)│  (Pattern)  │                             │  │
│  └─────────────┴─────────────┴─────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────────┘
                  │ Sync Wrapper → MCP Protocol
┌─────────────────▼───────────────────────────────────────────┐
│            🔌 Enhanced MCP Client v2 (EXISTING)            │
│          (boomi_datahub_mcp_client_v2.py)                  │
└─────────────────┬───────────────────────────────────────────┘
                  │ MCP Protocol
┌─────────────────▼───────────────────────────────────────────┐
│           📊 MCP Server v2 + DataHub Client (EXISTING)     │
│    (boomi_datahub_mcp_server_v2.py + boomi_datahub_client) │
└─────────────────┬───────────────────────────────────────────┘
                  │ REST API
┌─────────────────▼───────────────────────────────────────────┐
│                🏢 Boomi DataHub (PRODUCTION)               │
│  (Advertisements, users, opportunity, Engagements, etc.)   │
└─────────────────────────────────────────────────────────────┘
```

### Phase 6 Target Architecture (🎯 PLANNED)
```
┌─────────────────────────────────────────────────────────────┐
│          🌐 Web UI Layer (Future)                          │
│              (Streamlit + Authentication)                  │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTPS/WebSocket
┌─────────────────▼───────────────────────────────────────────┐
│              🔒 Security & Guardrails Layer               │
│          (Authentication + RBAC + Audit Logging)           │
└─────────────────┬───────────────────────────────────────────┘
                  │ Secured API Calls
┌─────────────────▼───────────────────────────────────────────┐
│              🤖 Enhanced Agent Pipeline                    │
│         (Phase 5 + Security Integration)                   │
└─────────────────┬───────────────────────────────────────────┘
                  │ (Rest of architecture unchanged)
                 ...existing infrastructure...
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

### **Tier 2: Agent Pipeline Layer (✅ IMPLEMENTED)**
**Technology**: Python Sequential Pipeline + Pattern Matching + Optional Claude  
**Responsibility**: Multi-agent query processing with dynamic discovery

```python
boomi_conversational_agent/
├── cli_agent/
│   ├── cli_agent.py                   # Main CLI interface (COMPLETE)
│   ├── pipeline/
│   │   └── agent_pipeline.py          # Sequential orchestration (COMPLETE)
│   ├── agents/                        # All 6 agents (COMPLETE)
│   │   ├── query_analyzer.py          # Pattern-based NL understanding
│   │   ├── model_discovery.py         # Dynamic model discovery + LLM
│   │   ├── field_mapper.py            # Dynamic field mapping + LLM
│   │   ├── query_builder.py           # Boomi query construction
│   │   ├── data_retrieval.py          # MCP client execution
│   │   └── response_generator.py      # Business response generation
│   └── tests/                         # TDD test suite (76/76 passing)
├── integration_test.py                # Real Boomi integration testing
├── test_dynamic_field_discovery.py   # Dynamic discovery validation
└── requirements.txt                   # Python dependencies

# Phase 6 Planned Extensions
security/ (PLANNED)
├── auth_middleware.py                 # Authentication and RBAC
├── guardrails.py                      # Query validation and blocking
├── jailbreak_detector.py              # Prompt injection prevention
└── audit_logger.py                    # Security event logging
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

#### **1. Query Analyzer Agent (✅ IMPLEMENTED)**
**Purpose**: Parse natural language into structured intent and entities using pattern matching

```python
# Real Phase 5 Implementation
Input:  "How many advertisements do we have?"
Output: {
    "intent": "COUNT",
    "entities": [
        {"text": "advertisements", "type": "OBJECT", "confidence": 0.9}
    ],
    "query_type": "COUNT",
    "complexity": "LOW"
}

# Actual working patterns:
- COUNT queries: "How many", "Count", "Number of"
- LIST queries: "Show me", "List", "Display"
- Entity extraction: advertisements, users, opportunities, engagements
```

#### **2. Model Discovery Agent (✅ IMPLEMENTED)**
**Purpose**: Find relevant Boomi DataHub models using dynamic discovery + optional LLM

```python
# Real Phase 5 Implementation
Input:  Query analysis with "advertisements" entity
Process: 
  1. Retrieve all available models via MCP server
  2. Use pattern matching + optional Claude for ranking
  3. Fallback to pattern-based ranking when Claude unavailable
Output: [
    {"model_id": "02367877-e560-4d82-b640-6a9f7ab96afa", 
     "name": "Advertisements", "relevance": 0.95, "role": "primary"},
    {"model_id": "674108ee-4018-481a-ae7c-7becd6c6fa37", 
     "name": "users", "relevance": 0.3, "role": "secondary"}
]

# Real discovered models: Advertisements, users, opportunity, Engagements, platform-users
```

#### **3. Field Mapper Agent (✅ IMPLEMENTED)**
**Purpose**: Map entities to specific model fields using dynamic field discovery

```python
# Real Phase 5 Implementation
Input:  Entities + Selected models + Dynamically discovered fields
Process:
  1. Get real field info for each model via MCP
  2. Use pattern matching + optional Claude for mapping
  3. Support both string and dictionary entity formats
Output: {
    "02367877-e560-4d82-b640-6a9f7ab96afa": {
        "advertisements": {
            "field_name": "AD_ID",
            "confidence": 0.8,
            "reasoning": "Pattern match for count queries"
        }
    }
}

# Real discovered fields: AD_ID, ADVERTISER, PRODUCT, CAMPAIGN, etc.
```

#### **4. Query Builder Agent (✅ IMPLEMENTED)**
**Purpose**: Build Boomi DataHub queries using discovered fields (no hardcoding)

```python
# Real Phase 5 Implementation
Input:  Field mappings + Query intent
Process:
  1. Use real field names from field discovery
  2. Convert COUNT to LIST operations (Boomi native)
  3. Apply discovered fields instead of '*' wildcards
Output: {
    "model_id": "02367877-e560-4d82-b640-6a9f7ab96afa",
    "repository_id": "43212d46-1832-4ab1-820d-c0334d619f6f",
    "fields": ["AD_ID"],  # Real discovered field, not '*'
    "filters": [],
    "query_type": "LIST",  # Boomi native operation
    "operation": "COUNT"   # Local counting after retrieval
}

# 100% success rate with real Boomi DataHub queries
```

#### **5. Data Retrieval Agent (✅ IMPLEMENTED)**
**Purpose**: Execute queries via MCP Client v2 with sync wrapper

```python
# Real Phase 5 Implementation
Input:  Constructed query with real field names
Process:
  1. Execute via SyncBoomiMCPClient wrapper
  2. Handle async/sync conversion automatically
  3. Process real Boomi DataHub responses
  4. Count results locally for COUNT operations
Output: {
    "total_count": 6,  # Real count from Advertisements model
    "results": [
        {"AD_ID": "a02dL000004QpHuQAK_a01dL00000QjQ75QAF", ...},
        # 5 more real advertisement records
    ],
    "metadata": {"execution_time": "2.1s", "source": "Boomi DataHub"}
}
```

#### **6. Response Generator Agent (✅ IMPLEMENTED)**
**Purpose**: Generate business-friendly responses from real data

```python
# Real Phase 5 Implementation
Input:  Real query results + Original query context
Process:
  1. Extract count from real result data
  2. Generate appropriate business language
  3. Include data source and context
Output: "Based on the Advertisements data, we currently have 6 advertisements 
         in our system. This information was retrieved from the Boomi DataHub 
         and reflects the current state of our advertising campaigns."

# Real working examples:
- "6 advertisements found"
- "6 users found in the system"
- "6 opportunities identified"
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