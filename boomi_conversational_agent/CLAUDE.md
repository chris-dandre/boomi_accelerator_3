# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Server and Client Startup
```bash
# Start the unified MCP server (required first)
python boomi_datahub_mcp_server_unified_compliant.py

# Run CLI client
python cli/enhanced_interactive_cli.py

# Run web UI client
streamlit run web_ui/enhanced_streamlit_app.py

# Optional: Run OAuth server for testing
python run_oauth_server.py
```

### Testing
```bash
# Run all tests with coverage (80% minimum requirement)
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m security      # Security tests only
pytest -m e2e           # End-to-end tests only

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_phase5/test_agent_pipeline.py

# Generate HTML coverage report
pytest --cov=cli_agent --cov-report=html:htmlcov
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install additional dependencies for full functionality
pip install langgraph langsmith jsonrpc-base jsonrpc-async authlib
```

## Architecture Overview

This is a **Boomi DataHub Conversational Agent** with OAuth 2.1 authentication, LangGraph orchestration, and **ReAct (Reasoning + Acting) intelligence**. The system uses a **12-node workflow pipeline** for secure, intelligent query processing.

### Current System Status (Phase 8B+)
- ✅ **FULLY FUNCTIONAL**: Authentication, data retrieval, and query processing working
- ✅ **MCP COMPLIANT**: Uses unified MCP server with proper OAuth integration  
- ✅ **ReAct INTELLIGENCE**: Revolutionary query understanding and field mapping

### Core Components

**MCP Server**: `boomi_datahub_mcp_server_unified_compliant.py`
- Unified MCP server with OAuth 2.1 authentication
- Boomi DataHub integration with proper credential handling
- **CRITICAL**: This is the working server - other MCP servers in the repo are legacy/broken

**CLI Agent System**: `cli_agent/`
- **Agents**: Specialized components for query analysis, model discovery, field mapping, response generation
- **Pipeline**: LangGraph orchestration with 12-node workflow including security layers
- **Auth**: OAuth 2.1 authentication manager with role-based access control

**Web Interface**: `web_ui/enhanced_streamlit_app.py`
- Streamlit-based UI with enhanced Synapsewerx branding (360px logo)
- Unified server integration with proper authentication flow

**Security Architecture**: `security/`
- Multi-layered security: input sanitization, semantic analysis, audit logging
- Rate limiting, token revocation, jailbreak detection
- Audit trail with JSON logging for compliance

### ReAct Intelligence (Revolutionary Implementation)

**Field Mapping Intelligence** (`cli_agent/agents/field_mapper.py`):
- **Problem Solved**: Eliminated 150+ lines of failing data-driven field discovery
- **Solution**: Claude LLM semantic analysis with 95-98% confidence scores
- **Impact**: Transformed from 0% success rate to near-perfect field mapping

**Query Builder Intelligence** (`cli_agent/agents/query_builder.py:608-684`):
- **Problem Solved**: Queries like "which companies are advertising?" returned 0 results
- **Solution**: THOUGHT→ACTION→OBSERVATION cycle that classifies entity roles
- **Impact**: Fixed critical system failure - queries now return actual data

**ReAct Pattern**: All intelligence uses transparent reasoning traces:
1. **THOUGHT**: Analyze current situation and plan next steps
2. **ACTION**: Execute specific operations based on reasoning  
3. **OBSERVATION**: Analyze results and gather new information
4. **THOUGHT**: Reflect and determine next actions

### Authentication & User Roles

**OAuth 2.1 Flow** with role-based access:
- **Sarah Chen** (Data Analyst): Full data access with analytical context
- **David Williams** (Executive): Executive summaries and business insights
- **Alex** (IT Administrator): System administration capabilities

**Token Management**: Bearer tokens with 2-hour expiry, introspection support (RFC 7662)

## Key Implementation Details

### Startup Sequence
1. **Always start the unified MCP server first**: `python boomi_datahub_mcp_server_unified_compliant.py`
2. **Then start client**: CLI or Web UI
3. **Authentication**: System handles OAuth flow automatically

### Critical Fixes Applied (Phase 8B+)
- **Server Unification**: CLI now starts correct MCP server (was using broken legacy server)
- **Authentication**: Fixed OAuth import errors and connection timeouts
- **Field Mapping**: Replaced complex failing code with simple Claude LLM semantic analysis
- **Query Logic**: Fixed entity classification to prevent 0-result queries
- **UI Enhancement**: 3x larger Synapsewerx logo (360px) with proper branding

### Testing Strategy
- **TDD Approach**: 80% minimum coverage requirement configured in `pytest.ini`
- **Categorized Tests**: Unit, integration, security, and e2e test markers
- **Mocking**: Comprehensive mocks for Claude client and MCP client in `tests/mocks/`

### Development Notes
- **ReAct Debugging**: Query reasoning traces available for troubleshooting complex queries
- **Error Handling**: System provides transparent error messages with reasoning
- **Security First**: All inputs go through 4-layer security validation before processing
- **Audit Trail**: All operations logged to `logs/audit/` for compliance

## Planned Enhancements (Next Phase)
- **Error Recovery ReAct**: Transform generic errors into actionable guidance
- **Response Personalization**: Role-specific responses with appropriate detail levels
- **Model Discovery Transparency**: Explain why specific models were selected

## File Organization
- **Main Server**: `boomi_datahub_mcp_server_unified_compliant.py` (the working one)
- **CLI Entry**: `cli/enhanced_interactive_cli.py`
- **Web Entry**: `web_ui/enhanced_streamlit_app.py` 
- **Core Logic**: `cli_agent/` directory structure
- **Tests**: `tests/` with organized subdirectories
- **Documentation**: `docs/` with comprehensive architecture and implementation details

This system has evolved from a complex, partially-working prototype to a streamlined, intelligent agent with transparent reasoning and reliable performance.