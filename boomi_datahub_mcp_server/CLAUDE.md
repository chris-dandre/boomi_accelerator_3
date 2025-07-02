# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Boomi DataHub MCP (Model Context Protocol) Server that provides AI agents with access to Boomi DataHub APIs through standardized MCP resources. The project consists of two main components:

1. **MCP Server** (`boomi_mcp_server/`) - Exposes Boomi DataHub functionality through MCP resources
2. **DataHub APIs** (`boomi_datahub_apis/`) - Core client library for Boomi DataHub REST API interactions

## Development Environment Setup

The project uses Conda for environment management:

```bash
# Create environment
./bootstrap.sh

# Run the MCP server
./run.sh

# Run API tests  
cd boomi_datahub_apis && ./run.sh
```

### Environment Configuration

The project requires a `.env` file with Boomi credentials:
```
BOOMI_USERNAME=your_username
BOOMI_PASSWORD=your_password
BOOMI_ACCOUNT_ID=your_account_id
BOOMI_BASE_URL=https://api.boomi.com
```

### Conda Environment

- Environment name: `env_MCPServer_DataHub`
- Python version: 3.11
- Key dependencies: fastmcp, requests, python-dotenv, pandas, transformers, langchain

## Core Architecture

### MCP Server Layer (`boomi_mcp_server/`)
- **`boomi_datahub_mcp_server.py`** - Main MCP server using FastMCP framework
- **`boomi_datahub_mcp_client.py`** - Reference client implementation
- **`boomi_datahub_mcp_server_v2.py`** and **`boomi_datahub_mcp_client_v2.py`** - Version 2 implementations

### DataHub Client Layer (`boomi_datahub_apis/`)
- **`boomi_datahub_client.py`** - Core REST API client with BoomiDataHubClient class
- **`test_boomi_datahub_client.py`** - Test suite for the API client
- JSON test data files for different model states (draft, published, all)

### MCP Resources Exposed
The server exposes resources under the `boomi://datahub/` URI scheme:
- Connection testing
- Model discovery across repositories
- Model detail retrieval with fields, sources, and match rules
- Publication status filtering (published/draft)

## Running Components

### Start MCP Server
```bash
python boomi_mcp_server/boomi_datahub_mcp_server.py
```

### Start MCP Client (separate terminal)
```bash
python boomi_mcp_server/boomi_datahub_mcp_client.py
```

### Run API Tests
```bash
python boomi_datahub_apis/test_boomi_datahub_client.py
```

## Key Classes and Integration Points

- **BoomiDataHubClient** - Main API client class in `boomi_datahub_apis/boomi_datahub_client.py`
- **BoomiCredentials** - Credential management dataclass
- **FastMCP** - MCP server framework for exposing resources
- Server runs on `http://127.0.0.1:8001/mcp` by default

## Development Workflow

1. Modify core client functionality in `boomi_datahub_apis/`
2. Update MCP server resources in `boomi_mcp_server/`
3. Test API changes with `test_boomi_datahub_client.py`
4. Test MCP integration by running server and client together
5. Use debug scripts (`auth_debug.py`, `query_predicate_debugger.py`) for troubleshooting

## File Versioning

The project maintains both v1 and v2 versions of MCP components, indicating active development and iteration on the MCP interface design.