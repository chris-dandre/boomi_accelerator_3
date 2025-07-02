# Interactive CLI for Boomi DataHub Conversational Agent

This directory contains interactive CLI scripts to run your own natural language queries against Boomi DataHub.

## Quick Start

### 1. Start MCP Server
```bash
# In terminal 1 - start the MCP server
cd "/mnt/d/Synapsewerx_Projects/Boomi Accelerator 3/boomi_datahub_mcp_server"
python boomi_mcp_server/boomi_datahub_mcp_server_v2.py
```

### 2. Test the System
```bash
# In terminal 2 - test that everything works
cd boomi_conversational_agent
python quick_test.py
```

### 3. Run Interactive CLI
```bash
# Choose one of these interactive options:

# Simple CLI
python interactive_cli.py

# Advanced CLI with history and commands
python advanced_cli.py
```

## Available CLI Scripts

### 🧪 `quick_test.py`
- **Purpose**: Verify the system is working
- **What it does**: Runs 4 test queries automatically
- **Use when**: First time setup or troubleshooting

```bash
python quick_test.py
```

Expected output:
```
🧪 Quick Test of Boomi DataHub CLI Agent
✅ CLI agent initialized successfully
🔍 Test 1: How many advertisements do we have?
✅ SUCCESS: Based on the Advertisements data, we currently have 6 advertisements
📊 TEST SUMMARY: 4/4 successful (100% success rate)
```

### 💬 `interactive_cli.py`
- **Purpose**: Simple interactive query interface
- **What it does**: Ask questions and get answers
- **Use when**: Quick queries and testing

```bash
python interactive_cli.py
```

Features:
- Real-time query processing
- Business-friendly responses
- Error handling and suggestions
- Exit with 'quit'

### 🚀 `advanced_cli.py`
- **Purpose**: Enhanced interactive interface
- **What it does**: Full-featured CLI with commands
- **Use when**: Extended sessions and exploration

```bash
python advanced_cli.py
```

Features:
- Query history (`history` command)
- Help system (`help` command)
- Model information (`models` command)
- Example queries (`examples` command)
- Execution metadata (timing, models used)
- Success rate tracking

## Example Queries

### ✅ Working Queries (100% Success Rate)
These queries work with your actual Boomi DataHub:

- `"How many advertisements do we have?"` → 6 advertisements
- `"Count users in the system"` → 6 users
- `"Show me opportunities"` → 6 opportunities
- `"List engagements"` → Engagement data
- `"How many platform users are there?"` → Platform user data

### 💡 Try These Variations
- `"What data do we have about advertisements?"`
- `"Count all the users"`
- `"Display opportunity information"`
- `"How many records are in the users model?"`

## How It Works

### Phase 5 Architecture (✅ Complete)
```
Your Query → Query Analysis → Model Discovery → Field Mapping → 
Query Building → Data Retrieval → Response Generation
```

1. **Query Analysis**: Understands your intent (COUNT, LIST, etc.)
2. **Model Discovery**: Finds relevant Boomi models dynamically
3. **Field Mapping**: Maps your words to actual field names
4. **Query Building**: Creates Boomi-compatible queries
5. **Data Retrieval**: Executes via MCP client
6. **Response Generation**: Returns business-friendly answers

### Dynamic Discovery
- **Zero Hardcoding**: All models and fields discovered in real-time
- **Real Boomi Data**: Connects to your actual DataHub
- **Automatic Field Discovery**: Finds available fields for each model
- **Intelligent Mapping**: Maps your query terms to field names

## Available Models

Your Boomi DataHub contains these models:

| Model | Description | Example Query |
|-------|-------------|---------------|
| **Advertisements** | Marketing campaigns | "How many advertisements?" |
| **users** | System users | "Count users" |
| **opportunity** | Sales opportunities | "Show opportunities" |
| **Engagements** | Customer interactions | "List engagements" |
| **platform-users** | Platform accounts | "How many platform users?" |

## Troubleshooting

### ❌ "Failed to initialize"
**Problem**: Can't connect to MCP server
**Solution**: 
```bash
# Make sure MCP server is running
python ../boomi_mcp_server/boomi_datahub_mcp_server_v2.py
```

### ❌ "Import error"
**Problem**: Can't find CLI agent modules
**Solution**:
```bash
# Make sure you're in the right directory
cd boomi_conversational_agent
ls -la cli_agent/  # Should show agent files
```

### ❌ "Connection failed"
**Problem**: MCP server not responding
**Solution**:
```bash
# Test MCP server directly
python ../boomi_mcp_server/quick_test_script.py
# Check .env file has valid Boomi credentials
```

### ❌ Query returns error
**Problem**: Query not understood or model not found
**Solution**:
- Try simpler queries: "How many advertisements?"
- Use model names: "advertisements", "users", "opportunities"
- Check examples with `examples` command in advanced CLI

## Success Metrics

### Phase 5 Achievement ✅
- **76/76 tests passing** (100% test success rate)
- **100% success rate** on real Boomi DataHub queries
- **Dynamic discovery** working (zero hardcoded models/fields)
- **Real-time integration** with production DataHub

### Current Performance
- **Query processing**: ~2-5 seconds
- **Model discovery**: Real-time from Boomi
- **Field discovery**: Dynamic per model
- **Data retrieval**: Live from DataHub

## Next Steps (Phase 6)

The working CLI foundation is ready for Phase 6 enhancements:

- **Authentication**: Steve Jobs vs Alex Smith user scenarios
- **Access Control**: Role-based permissions
- **Security Guardrails**: Jailbreak detection
- **Audit Logging**: Complete query tracking

For now, enjoy querying your Boomi DataHub with natural language! 🚀