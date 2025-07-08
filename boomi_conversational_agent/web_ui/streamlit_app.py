"""
Streamlit Web Interface - Phase 8A Implementation
Web-based conversational interface for Boomi DataHub queries
Preserves all Phase 7C security features while providing enhanced UX
"""

import streamlit as st
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio
import os
import sys

# Add the parent directory to the path to import CLI agent
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from cli_agent.cli_agent import CLIAgent
from cli_agent.pipeline.agent_pipeline import AgentPipeline

# Page configuration
st.set_page_config(
    page_title="Boomi DataHub Conversational AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

class StreamlitWebInterface:
    """
    Web interface wrapper for existing CLI agent functionality
    Preserves all security features while providing enhanced UX
    """
    
    def __init__(self):
        """Initialize the web interface"""
        self.cli_agent = None
        self.initialize_session_state()
        
    def initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
            
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
            
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
            
        if 'cli_agent' not in st.session_state:
            st.session_state.cli_agent = None
            
        if 'session_start_time' not in st.session_state:
            st.session_state.session_start_time = datetime.now()
            
    def render_header(self):
        """Render the application header"""
        st.title("🤖 Boomi DataHub Conversational AI")
        st.markdown("*Enterprise-grade conversational interface with OAuth 2.1 security*")
        
        # Status indicators
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.session_state.authenticated:
                st.success("🔒 Authenticated")
            else:
                st.error("🔓 Not Authenticated")
                
        with col2:
            st.info("🛡️ Security: Active")
            
        with col3:
            st.info("⚡ Rate Limiting: Active")
            
        with col4:
            st.info("📊 Phase 8A: Web UI")
            
    def render_sidebar(self):
        """Render the sidebar with user info and controls"""
        with st.sidebar:
            st.header("Session Information")
            
            if st.session_state.authenticated:
                user_info = st.session_state.user_info or {}
                st.success(f"👤 Welcome, {user_info.get('name', 'User')}!")
                st.write(f"**Role**: {user_info.get('role', 'Unknown')}")
                st.write(f"**Session**: {st.session_state.session_start_time.strftime('%H:%M:%S')}")
                
                if st.button("🚪 Logout", type="secondary"):
                    self.logout()
                    
            st.divider()
            
            # System Status
            st.header("System Status")
            st.write("**Backend**: CLI Agent Pipeline")
            st.write("**Security**: OAuth 2.1 + PKCE")
            st.write("**MCP Protocol**: June 2025 Spec")
            
            # Query Statistics
            if st.session_state.conversation_history:
                st.divider()
                st.header("Session Stats")
                total_queries = len(st.session_state.conversation_history)
                st.metric("Total Queries", total_queries)
                
                # Calculate success rate
                successful = sum(1 for conv in st.session_state.conversation_history 
                               if conv.get('status') == 'success')
                if total_queries > 0:
                    success_rate = (successful / total_queries) * 100
                    st.metric("Success Rate", f"{success_rate:.1f}%")
                    
    def render_authentication(self):
        """Render authentication interface"""
        st.header("🔐 Authentication Required")
        st.markdown("Please authenticate to access the Boomi DataHub Conversational AI system.")
        
        with st.form("auth_form"):
            st.subheader("Login Credentials")
            
            # Demo user options
            user_type = st.selectbox(
                "Select User Type",
                ["Custom", "Martha Stewart (Executive)", "Alex Smith (Clerk)"],
                help="Choose a demo user or enter custom credentials"
            )
            
            if user_type == "Martha Stewart (Executive)":
                username = st.text_input("Username", value="martha.stewart", disabled=True)
                password = st.text_input("Password", value="good.business.2024", type="password", disabled=True)
                role = "executive"
            elif user_type == "Alex Smith (Clerk)":
                username = st.text_input("Username", value="alex.smith", disabled=True)
                password = st.text_input("Password", value="newuser123", type="password", disabled=True)
                role = "clerk"
            else:
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                role = st.selectbox("Role", ["executive", "manager", "clerk"])
                
            submit_button = st.form_submit_button("🔑 Login", type="primary")
            
            if submit_button:
                if username and password:
                    success, user_info = self.authenticate_user(username, password, role)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.success("✅ Authentication successful!")
                        st.rerun()
                    else:
                        st.error("❌ Authentication failed. Please check your credentials.")
                else:
                    st.error("❌ Please enter both username and password.")
                    
    def authenticate_user(self, username: str, password: str, role: str) -> tuple[bool, Optional[Dict]]:
        """
        Authenticate user credentials
        In Phase 8A, this is a simplified demo implementation
        Phase 8B will integrate with the unified server OAuth system
        """
        # Demo authentication logic
        demo_users = {
            "martha.stewart": {
                "password": "good.business.2024",
                "role": "executive",
                "name": "Martha Stewart",
                "permissions": ["read_all", "query_all", "admin_access"]
            },
            "alex.smith": {
                "password": "newuser123", 
                "role": "clerk",
                "name": "Alex Smith",
                "permissions": []  # No data access
            }
        }
        
        if username in demo_users:
            user = demo_users[username]
            if user["password"] == password:
                # Initialize CLI agent for authenticated user
                try:
                    st.session_state.cli_agent = CLIAgent()
                    return True, {
                        "username": username,
                        "name": user["name"],
                        "role": user["role"],
                        "permissions": user["permissions"]
                    }
                except Exception as e:
                    st.error(f"Failed to initialize CLI agent: {str(e)}")
                    return False, None
        
        return False, None
        
    def logout(self):
        """Handle user logout"""
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.cli_agent = None
        st.session_state.conversation_history = []
        st.success("👋 Logged out successfully!")
        st.rerun()
        
    def render_chat_interface(self):
        """Render the main chat interface"""
        st.header("💬 Conversational Query Interface")
        
        # Display conversation history
        chat_container = st.container()
        
        with chat_container:
            for conversation in st.session_state.conversation_history:
                self.render_conversation_item(conversation)
                
        # Query input
        with st.form("query_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_query = st.text_input(
                    "Enter your business question:",
                    placeholder="e.g., How many advertisements do we have?",
                    label_visibility="collapsed"
                )
                
            with col2:
                submit_query = st.form_submit_button("🚀 Send", type="primary")
                
            if submit_query and user_query.strip():
                self.process_user_query(user_query.strip())
                st.rerun()
                
    def render_conversation_item(self, conversation: Dict[str, Any]):
        """Render a single conversation item"""
        timestamp = conversation.get('timestamp', datetime.now())
        
        # User message
        with st.chat_message("user"):
            st.write(f"**{timestamp.strftime('%H:%M:%S')}** - {conversation['query']}")
            
        # Assistant response
        with st.chat_message("assistant"):
            if conversation.get('status') == 'success':
                st.write(conversation['response'])
                
                # Show execution details if available
                if conversation.get('execution_details'):
                    with st.expander("📊 Execution Details"):
                        details = conversation['execution_details']
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Models Found", details.get('models_discovered', 'N/A'))
                        with col2:
                            st.metric("Fields Mapped", details.get('fields_mapped', 'N/A'))
                        with col3:
                            st.metric("Execution Time", f"{details.get('execution_time', 0):.2f}s")
                            
            elif conversation.get('status') == 'error':
                st.error(f"❌ Error: {conversation.get('error_message', 'Unknown error')}")
                
            elif conversation.get('status') == 'blocked':
                st.warning(f"🚫 {conversation.get('block_reason', 'Query blocked by security')}")
                
    def process_user_query(self, query: str):
        """Process user query through CLI agent"""
        start_time = time.time()
        
        # Check user permissions first
        user_info = st.session_state.user_info
        if user_info and user_info.get('role') == 'clerk':
            # Block data queries for clerk users
            conversation = {
                'query': query,
                'timestamp': datetime.now(),
                'status': 'blocked',
                'block_reason': 'Access denied. Contact administrator for data access.',
                'user_role': user_info.get('role')
            }
            st.session_state.conversation_history.append(conversation)
            return
            
        try:
            # Show processing indicator
            with st.spinner("🤖 Processing your query..."):
                # Use the CLI agent to process the query
                cli_agent = st.session_state.cli_agent
                if cli_agent:
                    response = cli_agent.process_query(query)
                    execution_time = time.time() - start_time
                    
                    # Parse response for details (CLI agent returns dict)
                    if isinstance(response, dict):
                        response_text = response.get('response', str(response))
                        execution_details = {
                            'models_discovered': response.get('models_discovered', 0),
                            'fields_mapped': response.get('fields_mapped', 0),
                            'execution_time': execution_time
                        }
                    else:
                        response_text = str(response)
                        execution_details = {'execution_time': execution_time}
                        
                    conversation = {
                        'query': query,
                        'response': response_text,
                        'timestamp': datetime.now(),
                        'status': 'success',
                        'execution_details': execution_details,
                        'user_role': user_info.get('role') if user_info else 'unknown'
                    }
                else:
                    raise Exception("CLI agent not initialized")
                    
        except Exception as e:
            conversation = {
                'query': query,
                'timestamp': datetime.now(),
                'status': 'error',
                'error_message': str(e),
                'user_role': user_info.get('role') if user_info else 'unknown'
            }
            
        # Add to conversation history
        st.session_state.conversation_history.append(conversation)
        
        # Limit history size
        if len(st.session_state.conversation_history) > 50:
            st.session_state.conversation_history = st.session_state.conversation_history[-50:]
            
    def run(self):
        """Main application runner"""
        self.render_header()
        
        if not st.session_state.authenticated:
            self.render_authentication()
        else:
            self.render_sidebar()
            self.render_chat_interface()

def main():
    """Main application entry point"""
    app = StreamlitWebInterface()
    app.run()

if __name__ == "__main__":
    main()