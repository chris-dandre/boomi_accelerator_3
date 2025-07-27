# Phase 8B Startup Guide

## 🚀 Complete System Startup Instructions

### **Prerequisites**
```bash
# Install LangGraph dependencies
pip install langgraph langsmith

# Ensure all other dependencies are installed
pip install -r requirements.txt
```

### **Step 1: Start the MCP Server (Backend)**

The system demonstrates **separation of duties** - the backend server handles data processing while the frontend provides the user interface.

```bash
# Terminal 1: Start the unified MCP server (Backend)
python boomi_datahub_mcp_server_unified_compliant.py
```

**Expected Output:**
```
🚀 Starting MCP-Compliant Unified Boomi DataHub Server
📊 Server Configuration:
   • MCP Server: http://localhost:8000
   • OAuth Server: http://localhost:8001
   • Web UI: http://localhost:8501
✅ Server started successfully!
```

**Keep this terminal open** - you'll see backend processing logs here.

### **Step 2: Start Your Client Interface (Frontend)**

In a **separate terminal**, choose your preferred interface. This demonstrates the **distributed architecture** where the LangGraph orchestrator communicates with the MCP server.

#### **Option A: Enhanced CLI Interface**
```bash
# Terminal 2: Launch enhanced CLI (Frontend)
python run_enhanced_system.py cli
```

#### **Option B: Enhanced Web Interface**
```bash
# Terminal 2: Launch enhanced web UI (Frontend)
python run_enhanced_system.py web
```

#### **Option C: Test the Orchestrator**
```bash
# Terminal 2: Run orchestrator tests
python run_enhanced_system.py test
```

### **Why Two Terminals?**

This setup demonstrates:
- **🔄 Separation of Concerns**: Backend (data/security) vs Frontend (user interface)
- **📡 Distributed Architecture**: Client-server communication via HTTP/MCP
- **🔍 Real-time Monitoring**: See backend processing logs while using frontend
- **🏗️ Scalability**: Multiple clients can connect to the same server
- **🛡️ Security Layers**: Authentication and authorization happen server-side

### **Step 3: Authentication**

Use these demo credentials:

| User | Username | Password | Role | Access Level |
|------|----------|----------|------|-------------|
| **Sarah Chen** | `sarah.chen` | `executive.access.2024` | Executive | Full Access |
| **David Williams** | `david.williams` | `manager.access.2024` | Manager | Limited Access |
| **Alex Smith** | `alex.smith` | `newuser123` | Clerk | No Data Access |

### **Step 4: Test Queries**

Try these example queries based on your user role:

#### **Executive Queries (Sarah Chen):**
- `"list models in datahub"`
- `"how many advertisements do we have?"`
- `"show me user engagement metrics"`
- `"export quarterly performance report"`

#### **Manager Queries (David Williams):**
- `"count engagements this month"`
- `"show advertisement performance"`
- `"what fields are available in Advertisements?"`

#### **Clerk Queries (Alex Smith):**
- `"list models"` (should be blocked)
- `"show user data"` (should be blocked)

### **System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 8B Architecture                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │  Enhanced CLI   │    │  Enhanced Web   │                   │
│  │  Interface      │    │  Interface      │                   │
│  └─────────────────┘    └─────────────────┘                   │
│           │                       │                           │
│           └───────────────────────┼──────────────────────────┐│
│                                   │                          ││
│  ┌─────────────────────────────────▼──────────────────────────▼┤
│  │          LangGraph Unified Orchestrator                    │
│  │  ┌─────────────────────────────────────────────────────┐   │
│  │  │  1. Bearer Token Validation                         │   │
│  │  │  2. User Authorization Check                        │   │
│  │  │  3. Layer 1: Input Sanitization                    │   │
│  │  │  4. Layer 2: Semantic Analysis                     │   │
│  │  │  5. Layer 3: Business Context                      │   │
│  │  │  6. Layer 4: Final Approval                        │   │
│  │  │  7. Query Intent Analysis                           │   │
│  │  │  8. Model Discovery                                 │   │
│  │  │  9. Query Execution                                 │   │
│  │  │ 10. Response Generation                             │   │
│  │  │ 11. Proactive Insights                              │   │
│  │  │ 12. Follow-up Suggestions                           │   │
│  │  └─────────────────────────────────────────────────────┘   │
│  └─────────────────────────────────────────────────────────────┤
│                                   │                           │
│  ┌─────────────────────────────────▼──────────────────────────┐│
│  │       MCP Server (Port 8000/8001)                        ││
│  │  • OAuth 2.1 + PKCE Authentication                       ││
│  │  • 4-Layer Security Pipeline                             ││
│  │  • Rate Limiting & Threat Detection                      ││
│  │  • Boomi DataHub Integration                             ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### **Key Features**

#### **🔐 Enhanced Security**
- MCP June 2025 compliant bearer token validation
- 4-layer security with authentication context
- Role-based access control
- Comprehensive audit logging

#### **🤖 Proactive Intelligence**
- Automatic insights generation
- Context-aware follow-up suggestions
- Performance monitoring
- Cross-model analysis recommendations

#### **🎨 Synapsewerx Branding**
- Professional UI with corporate colors
- Logo integration from docs/logos
- Enhanced status indicators
- Responsive design

### **Troubleshooting**

#### **Common Issues:**

1. **Server not starting:**
   ```bash
   # Check if ports are available
   lsof -i :8000
   lsof -i :8001
   lsof -i :8501
   ```

2. **Import errors:**
   ```bash
   # Ensure all dependencies are installed
   pip install -r requirements.txt
   pip install langgraph langsmith
   ```

3. **Authentication issues:**
   - Use exact credentials from the table above
   - Ensure the MCP server is running first

4. **Query failures:**
   - Check server logs for detailed error messages
   - Verify your user role has appropriate permissions

### **Development Mode**

For development and debugging:

```bash
# Run with debug logging
PYTHONPATH=. python -m pytest test_orchestrator.py -v

# Check orchestrator state
python -c "
from shared.mcp_orchestrator import create_orchestrator
orchestrator = create_orchestrator()
print(orchestrator.get_state_summary())
"
```

### **Next Steps**

1. **Install dependencies** (if not already done)
2. **Start the MCP server** (Terminal 1)
3. **Launch your preferred interface** (Terminal 2)
4. **Authenticate with demo users**
5. **Test the enhanced orchestration**

The Phase 8B system is now ready for full testing and demonstration!