# Boomi DataHub Conversational Agent

A complete conversational AI system for querying Boomi DataHub using natural language, built with Test-Driven Development (TDD) methodology.

## Project Overview

This project implements a multi-agent conversational AI system that enables non-technical users (particularly marketing executives) to query Boomi DataHub using natural language queries like "How many advertisements do we have?" or "Show me users by region."

## Architecture

### Phase 5: CLI Agent Foundation (✅ COMPLETED)
- **Multi-Agent Pipeline**: 6 specialized agents working in sequence
- **Dynamic Discovery**: Real-time model and field discovery from Boomi DataHub
- **TDD Implementation**: 76/76 tests passing with comprehensive coverage
- **Real Data Integration**: Working end-to-end with live Boomi DataHub

### Components

#### 1. Core Agents (`boomi_conversational_agent/cli_agent/agents/`)
- **QueryAnalyzer**: Analyzes natural language and extracts intent (COUNT, LIST, COMPARE, ANALYZE)
- **ModelDiscovery**: Discovers and ranks relevant Boomi models using pattern matching
- **FieldMapper**: Maps query entities to actual Boomi field names using dynamic discovery
- **QueryBuilder**: Constructs Boomi-compatible queries using discovered fields
- **DataRetrieval**: Executes queries against Boomi DataHub via MCP client
- **ResponseGenerator**: Generates natural language responses from query results

#### 2. Agent Pipeline (`boomi_conversational_agent/cli_agent/pipeline/`)
- **AgentPipeline**: Orchestrates sequential execution of all agents
- **Error Handling**: Comprehensive error handling with fallback mechanisms
- **Performance Tracking**: Execution time and complexity analysis

#### 3. CLI Interface (`boomi_conversational_agent/cli_agent/`)
- **CLIAgent**: Command-line interface for query processing
- **Session Management**: Query history and context management
- **Configuration**: Flexible output formats and settings

#### 4. MCP Infrastructure (`boomi_mcp_server/`)
- **MCP Server v2**: Enhanced server with field mapping and dual credentials
- **MCP Client v2**: Enhanced client with advanced query capabilities
- **Sync Wrapper**: Synchronous wrapper for async MCP operations

## Key Features

### ✅ Dynamic Field Discovery
- **Real-time Model Discovery**: Automatically discovers available Boomi models
- **Field Introspection**: Dynamically discovers field names and types for each model
- **Intelligent Mapping**: Pattern-based mapping of query intent to specific fields
- **No Hardcoding**: Zero hardcoded model or field names - everything discovered dynamically

### ✅ Boomi DataHub Integration
- **Native Query Language**: Queries use LIST operations (Boomi's native format)
- **COUNT Simulation**: Local counting of retrieved records for COUNT operations
- **Field Validation**: Uses real field names discovered from Boomi schema
- **Error Handling**: Graceful handling of missing models or fields

### ✅ Test-Driven Development
- **Comprehensive Tests**: 76 tests covering all components
- **Mock Infrastructure**: Complete mock clients for isolated testing
- **Integration Tests**: Real-world testing against live Boomi DataHub
- **Red-Green-Refactor**: Full TDD methodology throughout development

## Current Results (Phase 5)

### Real-World Performance
**100% Success Rate** on test queries with actual Boomi DataHub:

| Query | Model Discovered | Fields Used | Records Found | Status |
|-------|------------------|-------------|---------------|---------|
| "How many advertisements do we have?" | Advertisements | AD_ID, ADVERTISER, PRODUCT | 6 | ✅ Success |
| "How many users do we have?" | users | USERID, FIRSTNAME, LASTNAME | 6 | ✅ Success |
| "Count opportunities" | opportunity | ACCOUNTID, DESCRIPTION, TYPE | 6 | ✅ Success |
| "List engagements" | Engagements | PRODUCT_ID, PRODUCT_NAME, VENDOR_ID | Found | ✅ Success |

### Models Discovered
- **Advertisements**: 10 fields (AD_ID, ADVERTISER, PRODUCT, CAMPAIGN, CATEGORY...)
- **opportunity**: 35 fields (ACCOUNTID, DESCRIPTION, TYPE, ORDERNUMBER__C...)  
- **Engagements**: 5 fields (PRODUCT_ID, PRODUCT_NAME, VENDOR_ID, VENDOR_NAME...)
- **users**: 5 fields (USERID, FIRSTNAME, LASTNAME, LOYALTYCARDNO...)
- **platform-users**: 16 fields (USERID, EMAIL, FIRSTNAME, LASTNAME...)

## Installation & Setup

### Prerequisites
- Python 3.8+
- Boomi DataHub access credentials
- Virtual environment

### Quick Start
```bash
# Setup environment
cd boomi_conversational_agent
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure credentials in .env file
cp .env.example .env
# Edit .env with your Boomi credentials

# Start MCP server
cd ../boomi_mcp_server
python boomi_datahub_mcp_server_v2.py

# Run conversational agent
cd ../boomi_conversational_agent
python -c "
from cli_agent.cli_agent import CLIAgent
from integration_test import SyncBoomiMCPClient
cli = CLIAgent(mcp_client=SyncBoomiMCPClient())
result = cli.process_query('How many advertisements do we have?')
print(result)
"
```

### Testing
```bash
# Run all tests
cd boomi_conversational_agent
python -m pytest tests/ -v

# Run integration tests
python test_specific_query.py
python test_dynamic_field_discovery.py
```

## Technical Implementation

### Dynamic Discovery Process
1. **Query Analysis**: Extract intent and entities from natural language
2. **Model Discovery**: Query MCP server for available models and rank by relevance  
3. **Field Discovery**: For each relevant model, discover available fields
4. **Pattern Matching**: Map query entities to discovered fields using confidence scoring
5. **Query Construction**: Build Boomi-compatible queries using discovered field names
6. **Execution**: Execute queries and process results
7. **Response Generation**: Create natural language responses

### Error Handling & Fallbacks
- **Missing Claude Client**: Pattern-based fallbacks for all LLM operations
- **Model Discovery Failure**: Fallback ranking based on model name patterns
- **Field Mapping Failure**: Graceful degradation to available fields
- **Query Execution Failure**: Detailed error reporting and retry mechanisms

## Next Phase: Security & Guardrails (Phase 6)

### Planned Features
- **Authentication**: User login and session management
- **Role-Based Access Control**: Executive vs clerk access levels
- **Guardrails**: Query validation and security filtering  
- **Audit Logging**: Complete query audit trail
- **Jailbreak Detection**: Security against prompt injection attacks

## Development Team

- **Architecture**: Multi-agent conversational AI system
- **Technology Stack**: Python, FastMCP, Pytest, Boomi DataHub
- **Methodology**: Test-Driven Development (TDD)
- **Integration**: Real-time Boomi DataHub connectivity

## Repository Structure

```
boomi_datahub_mcp_server/
├── boomi_mcp_server/           # MCP server implementation
│   ├── boomi_datahub_mcp_server_v2.py
│   ├── boomi_datahub_mcp_client_v2.py
│   └── boomi_datahub_client.py
├── boomi_conversational_agent/ # Conversational AI implementation
│   ├── cli_agent/
│   │   ├── agents/            # Core AI agents
│   │   ├── pipeline/          # Agent orchestration
│   │   └── cli_agent.py       # CLI interface
│   ├── tests/                 # TDD test suite
│   ├── integration_test.py    # Real-world integration
│   └── requirements.txt       # Dependencies
└── README.md                  # This file
```

## License

Proprietary - Synapsewerx Pty Ltd
