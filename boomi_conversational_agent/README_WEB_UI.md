# Boomi DataHub Web Interface - Phase 8A

## Overview

Phase 8A provides a modern web-based interface for the Boomi DataHub Conversational Agent, built with Streamlit. This interface preserves all Phase 7C security features while providing an enhanced user experience.

## Features

### 🔐 Authentication & Security
- **OAuth 2.1 + PKCE Integration**: Full integration with Phase 7C authentication
- **Role-based Access Control**: Executive vs Clerk user permissions  
- **Input Sanitization**: Automatic query sanitization before processing
- **Threat Detection**: Jailbreak and prompt injection protection
- **Session Management**: Secure web session handling

### 💬 Conversational Interface
- **Chat-style UI**: Modern chat interface with message history
- **Real-time Processing**: Live query processing with status indicators
- **Rich Response Display**: Enhanced formatting for query results
- **Error Handling**: Detailed error messages and troubleshooting tips
- **Execution Details**: Metrics on model discovery, field mapping, and timing

### 📊 Enhanced UX
- **Status Dashboard**: Real-time system status and security indicators
- **Query Statistics**: Session-based analytics (success rate, blocked queries)
- **User Information**: Detailed user profile and permissions display
- **Query Examples**: Built-in examples for common query patterns

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Unified Server
```bash
python boomi_datahub_mcp_server_unified_compliant.py
```

### 3. Launch Web Interface
```bash
python run_web_ui.py
```

The web interface will open at: http://localhost:8501

## Demo Accounts

### Martha Stewart (Executive)
- **Username**: `martha.stewart`
- **Password**: `good.business.2024`
- **Access**: Full data access granted

### Alex Smith (Clerk)  
- **Username**: `alex.smith`
- **Password**: `newuser123`
- **Access**: Data access denied (demonstrates access control)

## Architecture Integration

### Phase 7C Components Used
- **Unified MCP Server**: `boomi_datahub_mcp_server_unified_compliant.py`
- **OAuth 2.1 Authentication**: `cli_agent/auth/auth_manager.py`
- **Security Stack**: Complete `security/` directory
- **CLI Agent Pipeline**: Full agent pipeline integration

### Web Interface Components
- **Main App**: `web_ui/streamlit_app.py`
- **Launch Script**: `run_web_ui.py`
- **Dependencies**: Added to main `requirements.txt`

## Query Examples

### Data Queries
```
Show me Sony products
Find advertisements for Samsung
List campaigns in Q1
How many advertisements do we have?
```

### Meta Queries
```
List all available models
What data models exist?
Show me the data structure
```

## Security Features

### Input Validation
- SQL injection prevention
- XSS protection
- Command injection blocking
- Malicious pattern detection

### Access Control
- Role-based data access
- Session-based authentication
- Token-based authorization
- Permission validation

### Threat Detection
- Jailbreak attempt detection
- Prompt injection analysis
- Semantic threat analysis
- Behavioral anomaly detection

## Technical Details

### Technology Stack
- **Frontend**: Streamlit 1.28+
- **Backend**: Phase 7C Unified Server
- **Authentication**: OAuth 2.1 + PKCE
- **Security**: Multi-layered protection
- **Protocol**: MCP June 2025 Specification

### Performance
- Real-time query processing
- Efficient session management
- Optimized security checks
- Fast response rendering

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify demo account credentials
   - Check OAuth server is running
   - Ensure `.env` file is configured

2. **Connection Error**
   - Start unified server first: `python boomi_datahub_mcp_server_unified_compliant.py`
   - Check server is running on port 8001
   - Verify network connectivity

3. **Security Blocked**
   - Rephrase query if blocked by threat detection
   - Check user permissions
   - Review query for policy violations

4. **Query Errors**
   - Verify Boomi credentials in `.env`
   - Check DataHub connectivity
   - Try simpler queries first

### Logs and Debugging
- Application logs in console output
- Security events logged to `logs/audit/`
- Streamlit debug info in browser console

## Development

### File Structure
```
web_ui/
├── streamlit_app.py         # Main Streamlit application
├── requirements.txt         # Dependencies (merged with main)
└── README.md               # This documentation

run_web_ui.py               # Launch script
requirements.txt            # Updated with Streamlit deps
```

### Extending the Interface
- Add new pages in `streamlit_app.py`
- Extend security checks in `process_user_query()`
- Customize UI themes in Streamlit config
- Add new query examples in sidebar

## Future Enhancements (Phase 8B)

- Real-time query streaming
- Advanced data visualization
- Multi-user concurrent sessions
- Enhanced dashboard analytics
- Custom query templates
- Export functionality

## Support

For issues and questions:
1. Check troubleshooting section above
2. Review Phase 7C documentation
3. Check system logs and audit trails
4. Verify all dependencies are installed

---

**Phase 8A Complete**: Web interface with full Phase 7C integration and security preservation.