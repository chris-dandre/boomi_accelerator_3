"""
Enhanced Streamlit Web Interface with LangGraph Orchestration
Phase 8B implementation with Synapsewerx branding
"""

import streamlit as st
import asyncio
import time
import os
import sys
from typing import Dict, Any, Optional
import json
import base64
from PIL import Image
import requests
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set default configuration to disable proactive features for Web UI
os.environ.setdefault("ENABLE_PROACTIVE_INSIGHTS", "false")
os.environ.setdefault("ENABLE_FOLLOW_UP_SUGGESTIONS", "false")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.mcp_orchestrator import create_orchestrator
from shared.oauth_client import oauth_client

class EnhancedSWXWebInterface:
    """Enhanced web interface with Synapsewerx branding"""
    
    def __init__(self):
        self.orchestrator = create_orchestrator(interface_type="web")
        self.logos = self._load_synapsewerx_logos()
        self._initialize_session_state()
        self._load_custom_css()
        self.oauth_server_url = os.getenv('OAUTH_SERVER_URL', "http://localhost:8001")
        self._initialize_oauth_server()
        self.field_mappings = {}
        
        # Demo users for testing
        self.demo_users = {
            "sarah.chen": {
                "username": "sarah.chen",
                "password": "executive.access.2024",
                "role": "executive",
                "full_name": "Sarah Chen",
                "department": "Executive Leadership",
                "title": "Chief Data Officer",
                "has_data_access": True,
                "permissions": ["READ_ALL", "METADATA_ALL", "ANALYTICS_ALL", "EXPORT_ALL"],
                "description": "Chief Data Officer with full system access"
            },
            "david.williams": {
                "username": "david.williams",
                "password": "manager.access.2024",
                "role": "manager",
                "full_name": "David Williams",
                "department": "Business Intelligence",
                "title": "BI Manager",
                "has_data_access": True,
                "permissions": ["READ_ASSIGNED", "METADATA_ASSIGNED", "ANALYTICS_STANDARD"],
                "description": "BI Manager with departmental data access"
            },
            "alex.smith": {
                "username": "alex.smith",
                "password": "newuser123",
                "role": "clerk",
                "full_name": "Alex Smith",
                "department": "Operations",
                "title": "Operations Clerk",
                "has_data_access": False,
                "permissions": [],
                "description": "Operations clerk with no data access"
            }
        }
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_info' not in st.session_state:
            st.session_state.user_info = {}
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'access_token' not in st.session_state:
            st.session_state.access_token = None
        if 'followup_query' not in st.session_state:
            st.session_state.followup_query = None
    
    def _load_synapsewerx_logos(self) -> Dict[str, Any]:
        """Load Synapsewerx logos from docs/logos directory"""
        logos = {}
        logo_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "logos")
        
        try:
            for file in os.listdir(logo_dir):
                if file.endswith('.png'):
                    logo_path = os.path.join(logo_dir, file)
                    logo_name = file.replace('.png', '')
                    try:
                        logos[logo_name] = Image.open(logo_path)
                    except Exception as e:
                        print(f"Error loading logo {file}: {e}")
        except FileNotFoundError:
            print(f"Logo directory not found: {logo_dir}")
        
        return logos
    
    def _initialize_oauth_server(self):
        """Initialize OAuth server for authentication"""
        if 'oauth_server_initialized' not in st.session_state:
            st.session_state.oauth_server_initialized = False
            
        if not st.session_state.oauth_server_initialized:
            # Check if OAuth server is already running
            if self._check_oauth_server_health():
                st.session_state.oauth_server_initialized = True
                st.success("✅ OAuth server is running")
            else:
                st.warning("⚠️ OAuth server not detected. Please start the compliant MCP server.")
                with st.expander("OAuth Server Setup Instructions"):
                    st.markdown("""
                    **To enable OAuth authentication:**
                    1. Open a terminal in the project directory
                    2. Run: `python boomi_datahub_mcp_server_unified_compliant.py`
                    3. Wait for the server to start
                    4. Refresh this page
                    
                    **Note:** The unified server includes Claude LLM field mapping and full OAuth support.
                    """)
    
    def _check_oauth_server_health(self) -> bool:
        """Check if OAuth server is running and healthy"""
        try:
            response = requests.get(f"{self.oauth_server_url}/health", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def _load_custom_css(self):
        """Load custom CSS for Synapsewerx branding"""
        st.markdown("""
        <style>
        /* Synapsewerx Color Palette */
        :root {
            --swx-primary: #1E3A8A;
            --swx-secondary: #3B82F6;
            --swx-accent: #10B981;
            --swx-dark: #1F2937;
            --swx-light: #F8FAFC;
            --swx-warning: #F59E0B;
            --swx-error: #EF4444;
        }
        
        /* Enhanced header styling */
        .main-header {
            background: linear-gradient(135deg, var(--swx-primary), var(--swx-secondary));
            color: white;
            padding: 1rem 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .main-header h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
            color: white;
        }
        
        .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }
        
        /* Status badges */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            text-align: center;
            margin: 0.25rem;
        }
        
        .status-badge.success {
            background-color: var(--swx-accent);
            color: white;
        }
        
        .status-badge.warning {
            background-color: var(--swx-warning);
            color: white;
        }
        
        .status-badge.error {
            background-color: var(--swx-error);
            color: white;
        }
        
        /* Enhanced chat styling */
        .chat-message {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 10px;
            border-left: 4px solid var(--swx-secondary);
        }
        
        .user-message {
            background-color: #f0f9ff;
            border-left-color: var(--swx-primary);
        }
        
        .assistant-message {
            background-color: #f0fdf4;
            border-left-color: var(--swx-accent);
        }
        
        /* Proactive insights styling */
        .insight-card {
            background: linear-gradient(135deg, #fef3c7, #fde68a);
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border-left: 4px solid var(--swx-warning);
        }
        
        .followup-card {
            background: linear-gradient(135deg, #e0f2fe, #b3e5fc);
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border-left: 4px solid var(--swx-secondary);
        }
        
        /* Performance metrics */
        .metrics-container {
            background: var(--swx-light);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        /* Hide Streamlit default elements */
        .stDeployButton {
            display: none;
        }
        
        header[data-testid="stHeader"] {
            display: none;
        }
        
        /* Enhanced button styling */
        .stButton > button {
            background: linear-gradient(135deg, var(--swx-primary), var(--swx-secondary));
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_branded_header(self):
        """Render header with Synapsewerx branding"""
        
        # Logo and title (adjusted for larger logo)
        col1, col2 = st.columns([2, 3])
        
        with col1:
            if '20241013_Synapsewerx_Logo_Positive-01' in self.logos:
                st.image(self.logos['20241013_Synapsewerx_Logo_Positive-01'], width=360)
            else:
                st.markdown("### SWX")
        
        with col2:
            st.markdown("""
            <div class="main-header">
                <h1>SWX MCP Server for Boomi DataHub</h1>
                <div class="subtitle">Enterprise-grade conversational AI with MCP June 2025 compliance</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Enhanced status indicators
        self._render_status_indicators()
    
    def _render_status_indicators(self):
        """Render enhanced status indicators"""
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.session_state.authenticated:
                st.markdown('<div class="status-badge success">🔐 Authenticated</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-badge warning">🔓 Not Authenticated</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="status-badge success">🛡️ 4-Layer Security</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="status-badge success">⚡ LangGraph AI</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="status-badge success">🤖 Proactive Intel</div>', unsafe_allow_html=True)
        
        with col5:
            st.markdown('<div class="status-badge success">📊 MCP June 2025</div>', unsafe_allow_html=True)
    
    def render_login_form(self):
        """Render enhanced login form with Synapsewerx branding"""
        
        # Add spacing
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Use same column layout as post-login header for consistency
        col1, col2 = st.columns([2, 3])
        
        with col1:
            if '20241013_Synapsewerx_Logo_Positive-01' in self.logos:
                st.image(self.logos['20241013_Synapsewerx_Logo_Positive-01'], width=360)
            else:
                st.markdown("### SWX")
        
        with col2:
            # Add title and branding in the same style as post-login
            st.markdown("""
            <div style="margin-top: 2rem;">
                <h1>SWX MCP Server for Boomi DataHub</h1>
                <div style="color: #666; font-size: 18px; margin-bottom: 2rem;">
                    Enterprise-grade conversational AI with MCP June 2025 compliance
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Login form section
        st.markdown("### 🔐 Authentication Required")
        st.markdown("Please authenticate to access the SWX MCP Server")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns(2)
            with col1:
                login_button = st.form_submit_button("🔐 Login", use_container_width=True)
            with col2:
                demo_button = st.form_submit_button("👥 Show Demo Users", use_container_width=True)
            
            if demo_button:
                st.markdown("### 👥 Demo Users")
                st.markdown("""
                **Sarah Chen (Executive)**
                - Username: `sarah.chen`
                - Password: `executive.access.2024`
                - Role: Chief Data Officer with full access
                
                **David Williams (Manager)**
                - Username: `david.williams`
                - Password: `manager.access.2024`
                - Role: BI Manager with departmental access
                
                **Alex Smith (Clerk)**
                - Username: `alex.smith`
                - Password: `newuser123`
                - Role: Operations Clerk with no data access
                """)
            
            if login_button:
                if username and password:
                    success = self._authenticate_user(username, password)
                    if success:
                        st.rerun()
                else:
                    st.error("Please enter both username and password")
    
    def _authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user with real OAuth 2.1 token exchange"""
        
        # Check if OAuth server is available
        if not self._check_oauth_server_health():
            st.error("❌ OAuth server is not available. Please start the unified MCP server: `python boomi_datahub_mcp_server_unified_compliant.py`")
            return False
        
        if username in self.demo_users:
            user = self.demo_users[username]
            if user["password"] == password:
                # Get real OAuth token from server
                bearer_token = self._get_oauth_token(username)
                
                if bearer_token:
                    st.session_state.authenticated = True
                    st.session_state.user_info = user
                    st.session_state.access_token = bearer_token
                    st.session_state.login_success = True  # Flag for welcome message
                    
                    # Don't show welcome message or token on login page - show on main page
                    st.success("✅ Authentication successful!")
                    return True
                else:
                    st.error("❌ Failed to obtain OAuth token")
                    return False
            else:
                st.error("❌ Invalid password")
                return False
        else:
            st.error("❌ User not found")
            return False
    
    def _get_oauth_token(self, username: str) -> Optional[str]:
        """Get OAuth token using shared OAuth client"""
        try:
            user_info = self.demo_users[username]
            result = oauth_client.authenticate(username, user_info["password"])
            
            if result["success"]:
                return result["access_token"]
            else:
                st.error(f"❌ OAuth token generation failed: {result['error']}")
                return None
                
        except Exception as e:
            st.error(f"❌ OAuth token generation failed: {e}")
            return None
    
    def _get_oauth_scope(self, username: str) -> str:
        """Get OAuth scope for user"""
        user_info = self.demo_users[username]
        role = user_info["role"]
        
        # Map roles to OAuth scopes
        scope_mapping = {
            "executive": "read:all write:all mcp:admin",
            "manager": "read:advertisements mcp:read", 
            "clerk": "none"
        }
        
        return scope_mapping.get(role, "none")
    
    def render_user_info(self):
        """Render user information panel"""
        
        if st.session_state.authenticated:
            user = st.session_state.user_info
            
            with st.sidebar:
                st.markdown("### 👤 User Information")
                st.markdown(f"**Name:** {user['full_name']}")
                st.markdown(f"**Role:** {user['role']}")
                st.markdown(f"**Department:** {user['department']}")
                st.markdown(f"**Title:** {user['title']}")
                st.markdown(f"**Data Access:** {'✅ Granted' if user['has_data_access'] else '❌ Denied'}")
                
                if user['permissions']:
                    st.markdown("**Permissions:**")
                    for perm in user['permissions']:
                        st.markdown(f"• {perm}")
                
                if st.button("🚪 Logout"):
                    self._logout()
                    st.rerun()
    
    def _logout(self):
        """Logout user and clear session"""
        st.session_state.authenticated = False
        st.session_state.user_info = {}
        st.session_state.access_token = None
        st.session_state.chat_history = []
        st.session_state.followup_query = None
    
    async def process_user_query(self, query: str):
        """Process user query through enhanced orchestration (legacy method)"""
        
        user_info = st.session_state.user_info
        bearer_token = st.session_state.get('access_token')
        
        # Prepare user context with field_mappings
        user_context = {
            "role": user_info.get("role", "unknown"),
            "username": user_info.get("username", "anonymous"),
            "permissions": user_info.get("permissions", []),
            "has_data_access": user_info.get("has_data_access", False),
            "full_name": user_info.get("full_name", "Unknown"),
            "department": user_info.get("department", "Unknown"),
            "field_mappings": self.field_mappings
        }
        
        with st.spinner("🚀 Processing query through LangGraph orchestration..."):
            try:
                # Process through unified orchestrator
                result = await self.orchestrator.process_query(
                    query=query,
                    user_context=user_context,
                    bearer_token=bearer_token
                )
                
                # Add to chat history (legacy method - no processing steps captured)
                st.session_state.chat_history.append({
                    "query": query,
                    "result": result,
                    "timestamp": time.time(),
                    "processing_steps": []  # Empty for legacy method
                })
                
                # Note: Result display is now handled in render_chat_interface()
                # to maintain proper layout order
                
            except Exception as e:
                st.error(f"❌ Error processing query: {e}")
    
    async def process_user_query_with_progress(self, query: str, progress_container):
        """Process user query with real-time progress display using logging interception"""
        
        user_info = st.session_state.user_info
        bearer_token = st.session_state.get('access_token')
        
        # Prepare user context with field_mappings
        user_context = {
            "role": user_info.get("role", "unknown"),
            "username": user_info.get("username", "anonymous"),
            "permissions": user_info.get("permissions", []),
            "has_data_access": user_info.get("has_data_access", False),
            "full_name": user_info.get("full_name", "Unknown"),
            "department": user_info.get("department", "Unknown"),
            "field_mappings": self.field_mappings
        }
        
        with progress_container:
            st.markdown("**🤖 Agentic AI Workflow Progress**")
            progress_bar = st.progress(0)
            status_output = st.empty()
            
            # Create a custom print interceptor that preserves terminal output while capturing for UI
            import sys
            import builtins
            
            workflow_log = []
            original_print = builtins.print
            step_count = 0
            
            def intercepted_print(*args, **kwargs):
                nonlocal step_count, workflow_log
                
                # Always print to terminal first (preserve original behavior)
                original_print(*args, **kwargs)
                
                # Capture relevant workflow steps for UI display
                message = ' '.join(str(arg) for arg in args)
                
                # Capture ALL processing steps for real-time VP demo display
                # Only exclude very verbose debug messages
                if not any(skip in message for skip in [
                    "DEBUG:",
                    "INFO:httpx:",
                    "🔍 Debug - Raw models from MCP:",
                    "🔍 Debug - Raw models sample:",
                    "🔍 Debug - Processed models:",
                    "🔍 Field Discovery - Raw result sample:",
                    "🔍 ModelDiscovery: Full response:",
                    "🔍 ModelDiscovery: Retrieved non-list",
                    "🔍 ModelDiscovery: Models type:",
                    "🔍 Field Discovery - MCP client type:",
                    "🔍 Field Discovery - MCP client methods:"
                ]):
                    step_count += 1
                    # Clean up the message for display
                    clean_message = message.strip()
                    
                    # Add to workflow log for real-time display
                    workflow_log.append(clean_message)
                    
                    # Update progress based on step count (more granular for VP demo)
                    progress = min(step_count * 0.05, 0.95)
                    progress_bar.progress(progress)
                    
                    # Update UI display in real-time (show more lines for VP demo)
                    status_output.text("\n".join(workflow_log[-25:]))  # Show last 25 lines
                    
                    # Add small delay for visual effect in demo
                    time.sleep(0.1)
            
            try:
                # Replace print function temporarily
                builtins.print = intercepted_print
                
                # Add initial status
                workflow_log.append("🚀 Initializing LangGraph orchestration...")
                status_output.text("\n".join(workflow_log))
                progress_bar.progress(0.05)
                
                # Process the query through orchestrator (prints will be intercepted)
                result = await self.orchestrator.process_query(
                    query=query,
                    user_context=user_context,
                    bearer_token=bearer_token
                )
                
                # Final status based on actual result
                if result.get("success"):
                    workflow_log.append("Status: ✅ Complete! - LangGraph orchestration successful")
                    progress_bar.progress(1.0)
                else:
                    workflow_log.append(f"Status: ❌ Failed - {result.get('error', 'Unknown error')}")
                    progress_bar.progress(0.0)
                
                status_output.text("\n".join(workflow_log[-15:]))  # Show last 15 lines
                
                # Add to chat history with processing steps
                st.session_state.chat_history.append({
                    "query": query,
                    "result": result,
                    "timestamp": time.time(),
                    "processing_steps": workflow_log.copy()  # Store the captured steps
                })
                
            except Exception as e:
                progress_bar.progress(0.0)
                workflow_log.append(f"Status: ❌ Failed - Error: {str(e)}")
                status_output.text("\n".join(workflow_log[-15:]))
                
                # Add error to chat history with processing steps
                st.session_state.chat_history.append({
                    "query": query,
                    "result": {"success": False, "error": str(e)},
                    "timestamp": time.time(),
                    "processing_steps": workflow_log.copy()  # Store the captured steps even on error
                })
                
            finally:
                # Always restore original print function
                builtins.print = original_print
    
    def _display_enhanced_result(self, result: Dict[str, Any]):
        """Display result with proactive features (aligned with orchestrator output)"""
        
        if result["success"]:
            st.success("✅ Query processed successfully!")
            
            # Main response - handle both string and dict formats
            if result.get("response"):
                response = result["response"]
                st.markdown("### 📊 Response")
                
                if isinstance(response, dict):
                    # Handle structured response
                    if response.get("message"):
                        st.markdown(response["message"])
                    elif response.get("response_type"):
                        st.write(f"**Type:** {response['response_type']}")
                        if response.get("data"):
                            st.json(response["data"])
                else:
                    # Handle string response
                    st.write(response)
            
            # Pipeline metadata - aligned with orchestrator structure
            metadata = result.get("pipeline_metadata", {})
            if metadata:
                with st.expander("🔍 Processing Details", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Security Clearance", metadata.get("security_clearance", "unknown"))
                        st.metric("Query Intent", metadata.get("query_intent", "unknown"))
                    
                    with col2:
                        st.metric("Models Discovered", metadata.get("models_discovered", 0))
                        st.metric("Processing Time", f"{metadata.get('processing_time', 0):.2f}s")
            
            # Proactive insights - aligned with orchestrator structure (conditional display)
            if os.getenv("ENABLE_PROACTIVE_INSIGHTS", "true").lower() == "true":
                insights = result.get("pipeline_metadata", {}).get("proactive_insights", [])
                if insights:
                    st.markdown("### 💡 Proactive Insights")
                    for insight in insights:
                        confidence = insight.get("confidence", 0)
                        st.markdown(f"""
                        <div class="insight-card">
                            <strong>{insight['message']}</strong><br>
                            <small>Confidence: {confidence:.1f} | Type: {insight.get('type', 'general')}</small>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Follow-up suggestions - aligned with orchestrator structure (conditional display)
            if os.getenv("ENABLE_FOLLOW_UP_SUGGESTIONS", "true").lower() == "true":
                suggestions = result.get("pipeline_metadata", {}).get("suggested_follow_ups", [])
                if suggestions:
                    st.markdown("### 🔄 Suggested Follow-ups")
                    for i, suggestion in enumerate(suggestions, 1):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"""
                            <div class="followup-card">
                                {i}. {suggestion}
                            </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            if st.button("Ask", key=f"followup_{i}"):
                                st.session_state.followup_query = suggestion
                                st.rerun()
        
        else:
            st.error("❌ Query failed")
            if result.get("error"):
                st.error(f"Error: {result['error']}")
                
            # Show error details if available
            metadata = result.get("pipeline_metadata", {})
            if metadata.get("error_state"):
                st.error(f"Error State: {metadata['error_state']}")
    
    def render_chat_interface(self):
        """Render enhanced chat interface with improved layout"""
        
        # Show welcome message once after successful login
        if st.session_state.get("login_success", False):
            user_info = st.session_state.get("user_info", {})
            st.success(f"✅ Welcome, {user_info.get('full_name', 'User')}! You are successfully authenticated.")
            st.session_state.login_success = False  # Clear the flag
        
        st.markdown("### 💬 Conversational Interface")
        
        # Handle follow-up query
        if st.session_state.followup_query:
            query = st.session_state.followup_query
            st.session_state.followup_query = None
            asyncio.run(self.process_user_query(query))
        
        # Query input - positioned right after heading using text_input instead of chat_input
        # Use a default value from session state if available (for example queries)
        # Clear input after submission by using a counter-based key
        if "input_counter" not in st.session_state:
            st.session_state.input_counter = 0
            
        default_query = st.session_state.get("pending_query", "")
        user_input = st.text_input(
            "Enter your query:", 
            value=default_query,
            placeholder="Ask me anything about your Boomi DataHub...",
            key=f"query_input_{st.session_state.input_counter}"
        )
        
        # Submit button for the query
        submit_clicked = st.button("Submit Query", type="primary")
        
        if submit_clicked and user_input:
            # Clear the pending query if it was set by example button
            if "pending_query" in st.session_state:
                del st.session_state.pending_query
            
            # Show Query Status section immediately with progress
            st.markdown("### 📊 Query Status")
            progress_container = st.container()
            
            # Process the query with real-time progress
            asyncio.run(self.process_user_query_with_progress(user_input, progress_container))
            
            # Increment counter to create new input widget (effectively clearing it)
            st.session_state.input_counter += 1
            st.rerun()
        
        # Display current query and response (most recent) 
        if st.session_state.chat_history:
            latest_chat = st.session_state.chat_history[-1]  # Get most recent
            
            st.markdown("### 🔍 Current Query")
            st.markdown(f"**Query:** {latest_chat['query']}")
            
            # Show processing steps if available
            if 'processing_steps' in latest_chat and latest_chat['processing_steps']:
                with st.expander("🔧 Processing Steps", expanded=False):
                    st.text("\n".join(latest_chat['processing_steps']))
            
            st.markdown("### 📊 Query Status")
            # Show the response
            if latest_chat['result']['success']:
                # Display the full enhanced result for the current response
                self._display_enhanced_result(latest_chat['result'])
            else:
                st.error(f"❌ Error: {latest_chat['result'].get('error', 'Unknown error')}")
        
        # Display chat history at the bottom (always show after first query)
        if st.session_state.chat_history:
            st.markdown("### 📝 Chat History")
            
            if len(st.session_state.chat_history) == 1:
                # First query - show helpful message
                st.info("💡 Previous conversations will appear here as you continue chatting.")
            else:
                # Multiple queries - show all but the latest (since latest is shown above)
                history_to_show = st.session_state.chat_history[:-1]  # Exclude current
                
                for i, chat in enumerate(history_to_show):
                    query_number = i + 1  # Simple 1-based numbering
                    with st.expander(f"Query {query_number}: {chat['query'][:50]}..."):
                        st.markdown(f"**Query:** {chat['query']}")
                        st.markdown(f"**Time:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(chat['timestamp']))}")
                        
                        # Show processing steps if available
                        if 'processing_steps' in chat and chat['processing_steps']:
                            with st.expander("🔧 Processing Steps", expanded=False):
                                st.text("\n".join(chat['processing_steps']))
                        
                        if chat['result']['success']:
                            # For history, show simplified response
                            response = chat['result']['response']
                            if isinstance(response, dict) and response.get('message'):
                                st.markdown(f"**Response:** {response['message']}")
                            else:
                                st.markdown(f"**Response:** {response}")
                        else:
                            st.error(f"**Error:** {chat['result'].get('error', 'Unknown error')}")
    
    def render_example_queries(self):
        """Render example queries based on user role"""
        
        user_role = st.session_state.user_info.get("role", "unknown")
        
        with st.sidebar:
            st.markdown("### 💡 Example Queries")
            
            if user_role == "executive":
                examples = [
                    "How many advertisements are running this quarter?",
                    "Show me user engagement metrics",
                    "List all available data models",
                    "Export quarterly performance report"
                ]
            elif user_role == "manager":
                examples = [
                    "Count engagements this month",
                    "Show advertisement performance",
                    "List opportunity statuses",
                    "What fields are available in Advertisements?"
                ]
            else:
                examples = [
                    "List models in the system",
                    "Show user information",
                    "Count advertisements"
                ]
            
            for example in examples:
                if st.button(example, key=f"example_{example[:20]}"):
                    # Set the pending query to be used as default value in input field
                    st.session_state.pending_query = example
                    st.rerun()
    
    def run(self):
        """Run the enhanced web interface"""
        
        # Configure page
        st.set_page_config(
            page_title="SWX MCP Server",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Check authentication
        if not st.session_state.authenticated:
            self.render_login_form()
        else:
            # Render header only when authenticated
            self.render_branded_header()
            
            # Render user info
            self.render_user_info()
            
            # Render example queries
            self.render_example_queries()
            
            # Render main chat interface
            self.render_chat_interface()
    
    def close(self):
        """Close method for cleanup"""
        if hasattr(self.orchestrator, 'close'):
            try:
                asyncio.run(self.orchestrator.close())
                st.success("✅ Orchestrator closed successfully")
            except Exception as e:
                st.error(f"⚠️ Error closing orchestrator: {e}")

def main():
    """Main entry point"""
    interface = EnhancedSWXWebInterface()
    interface.run()

if __name__ == "__main__":
    main()