# USER PERSONAS

**Project**: SWX MCP Server for Boomi DataHub  
**Version**: 2.0 (Enhanced for Phase 8B)  
**Last Updated**: 2025-07-21

## 🎭 OVERVIEW

The SWX MCP Server supports three distinct user personas with differentiated access levels and capabilities. Each persona represents a different organizational role with specific data access requirements and security considerations.

**Phase 8B+ Completed Features:**
- ✅ **MCP Server Unification**: Fixed server startup and authentication issues
- ✅ **Claude LLM Field Mapping**: Revolutionary semantic field mapping (95-98% confidence)  
- ✅ **ReAct Intelligence**: Reasoning + Acting query building with transparent traces
- ✅ **Synapsewerx Branding**: 3x larger logo (360px) and professional UI
- ✅ **Authentication Fixes**: Proper OAuth integration and credential handling

## 👤 EXECUTIVE USER: "Sarah Chen" 

### **Profile**
- **Full Name**: Sarah Chen
- **Username**: `sarah.chen`
- **Password**: `executive.access.2024`
- **Role**: Executive
- **Title**: Chief Data Officer
- **Department**: Executive Leadership
- **Security Clearance**: Highest
- **Data Access**: Full privileges - can access all models and data fields

### **Background & Motivation**
Sarah Chen represents the modern Chief Data Officer who demands comprehensive data insights to drive strategic business decisions. She's known for:
- Leading data-driven transformation initiatives
- Demanding comprehensive analytics and cross-model insights
- Focusing on data governance and strategic data utilization
- Making executive decisions based on thorough data analysis

### **Access Permissions**
```python
"permissions": [
    "READ_ALL",           # Read all data models
    "METADATA_ALL",       # Access all metadata
    "ANALYTICS_ALL",      # Perform all analytics
    "EXPORT_ALL",         # Export data in all formats
    "ADMIN_REPORTS",      # Generate executive reports
    "CROSS_MODEL_QUERY"   # Query across multiple models
]
```

### **Typical Queries (✅ Phase 8B Enhanced)**
```
Executive Queries Sarah Chen Would Perform:
• "How many advertisements are running this quarter?"
• "Compare user engagement against last quarter"
• "What's the performance of our latest opportunities?"
• "Show me engagement metrics for our products"
• "Export quarterly performance report"
• "List all models and their respective fields"
• "Generate executive dashboard summary"

Phase 8B Proactive Features:
• Automatic insights: "Data completeness looks good"
• Follow-up suggestions: "Would you like a board presentation?"
• Cross-model recommendations: "Consider analyzing related models"
```

### **Security Behavior**
- **4-Layer Security**: Highest trust level, adjusted thresholds
- **Threat Analysis**: Relaxed confidence thresholds (0.8)
- **Business Context**: All business queries approved
- **Final Approval**: Executive context considered in LLM decisions

### **Proactive Features**
- **Insights**: Executive-level strategic insights
- **Follow-ups**: Board presentation suggestions, trend analysis
- **Recommendations**: Cross-model analysis opportunities

---

## 👤 MANAGER USER: "David Williams"

### **Profile**
- **Full Name**: David Williams
- **Username**: `david.williams`
- **Password**: `manager.access.2024`
- **Role**: Manager
- **Title**: Business Intelligence Manager
- **Department**: Business Intelligence
- **Security Clearance**: Medium

### **Access Permissions**
```python
"permissions": [
    "READ_ASSIGNED",      # Read assigned models only
    "METADATA_ASSIGNED",  # Access metadata for assigned models
    "ANALYTICS_STANDARD", # Standard analytics capabilities
    "EXPORT_STANDARD",    # Standard export capabilities
    "TEAM_REPORTS"        # Generate team reports
]
```

### **Data Access Scope**
- **Models**: Advertisements, Engagements, Opportunities (department-relevant)
- **Fields**: Business-relevant fields (no sensitive data)
- **Operations**: Read, Analyze, Standard Export
- **Rate Limits**: 50 queries per hour

### **Typical Queries**
```
Manager Queries David Williams Would Perform:
• "Show me advertisement performance this month"
• "Count engagement activities for our campaigns"
• "List opportunity statuses and their counts"
• "What fields are available in the Advertisements model?"
• "Generate BI team performance report"
• "Show trends in engagement data"
• "Compare campaign effectiveness"
```

### **Security Behavior**
- **4-Layer Security**: Medium trust level, standard thresholds
- **Threat Analysis**: Standard confidence thresholds (0.6)
- **Business Context**: Department-relevant queries approved
- **Final Approval**: Manager context considered, scope-limited

---

## 👤 CLERK USER: "Alex Smith"

### **Profile**  
- **Full Name**: Alex Smith
- **Username**: `alex.smith`
- **Password**: `newuser123`
- **Role**: Clerk
- **Title**: Operations Clerk
- **Department**: Operations
- **Security Clearance**: None (No Data Access)
- **Data Access**: No privileges - blocked from all data queries

### **Access Permissions**
```python
"permissions": []  # No data access permissions
```

### **Background & Motivation**
Alex Smith represents entry-level employees who may have system access for other purposes but should not be able to access sensitive business intelligence data. This persona tests our access control and demonstrates proper security boundaries.

### **Attempted Queries (All Blocked)**
```
Clerk Queries Alex Smith Would Attempt (All Blocked):
• "List models in the system"        → BLOCKED: No data access
• "Show me user information"         → BLOCKED: No data access
• "Count advertisements"             → BLOCKED: No data access
• "What data is available?"          → BLOCKED: No data access

Phase 8B Enhanced Security:
• All queries blocked at Layer 3 (Business Context)
• Clear error messages explaining access denial
• Guidance provided for requesting access
```

### **Security Behavior**
- **4-Layer Security**: No data access, all queries blocked at Layer 3
- **Threat Analysis**: Not applicable (blocked before analysis)
- **Business Context**: No data access privilege
- **Final Approval**: Not reached (blocked earlier)

### **System Behavior**
- **Authentication**: Can log in successfully
- **Query Processing**: All data queries blocked with clear messaging
- **Error Messages**: "Your clerk role does not have data access privileges. Contact your administrator."

---

## 🔐 ROLE-BASED ACCESS CONTROL (RBAC)

### **Permission Matrix**

| Permission | Executive | Manager | Clerk |
|------------|-----------|---------|-------|
| Read All Models | ✅ | ❌ | ❌ |
| Read Assigned Models | ✅ | ✅ | ❌ |
| Metadata Access | ✅ | ✅ (Limited) | ❌ |
| Analytics | ✅ | ✅ (Standard) | ❌ |
| Export Data | ✅ | ✅ (Standard) | ❌ |
| Cross-Model Queries | ✅ | ❌ | ❌ |
| Admin Reports | ✅ | ❌ | ❌ |
| System Information | ❌ | ❌ | ❌ |

### **Model Access Matrix**

| Model | Executive | Manager | Clerk |
|-------|-----------|---------|-------|
| Advertisements | ✅ | ✅ | ❌ |
| Users | ✅ | ❌ | ❌ |
| Opportunities | ✅ | ✅ | ❌ |
| Engagements | ✅ | ✅ | ❌ |
| Platform-Users | ✅ | ❌ | ❌ |

### **Security Threshold Matrix**

| Security Layer | Executive | Manager | Clerk |
|----------------|-----------|---------|-------|
| Input Sanitization | Moderate | Standard | Strict |
| Semantic Analysis | 0.8 threshold | 0.6 threshold | 0.4 threshold |
| Business Context | All approved | Scope-limited | All blocked |
| Final Approval | Executive context | Manager context | Not reached |

This comprehensive user persona documentation provides the foundation for implementing role-based access control and ensuring appropriate user experiences across all organizational levels.
```python
# Example permission structure
ROLES = {
    'executive': {
        'permissions': ['read_all_models', 'read_all_fields', 'complex_queries'],
        'query_limit': 1000,
        'rate_limit': '100/hour'
    },
    'clerk': {
        'permissions': [],
        'query_limit': 0,
        'rate_limit': '10/hour'  # For login attempts only
    }
}
```

### **Security Patterns to Detect**
```python
JAILBREAK_PATTERNS = [
    r"ignore.*(previous|all|initial).*(instruction|prompt|rule)",
    r"you are now",
    r"pretend.*you are",
    r"override.*security",
    r"show.*\.env",
    r"access.*file",
    # Add more patterns as needed
]
```

### **Audit Logging Schema (🎯 Phase 6)**
```json
{
    "timestamp": "2025-07-02T14:23:15Z",
    "user": "martha.stewart",
    "query": "How many advertisements do we have?",
    "action": "ALLOWED|BLOCKED|SECURITY_VIOLATION",
    "models_accessed": ["Advertisements"],
    "fields_accessed": ["AD_ID"],
    "response_summary": "Returned 6 advertisements from Boomi DataHub",
    "session_id": "sess_abc123",
    "phase5_success": true,
    "execution_time_ms": 2100
}
```

---

*These personas drive both development and testing to ensure the system works correctly for authorized users while maintaining security against unauthorized access and malicious attempts.*