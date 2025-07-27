"""
Celery tasks for asynchronous query processing in the Boomi DataHub Conversational Agent
Phase 8B: Supports field_mappings and OAuth 2.1 integration
"""

import os
from dotenv import load_dotenv
from celery import Celery
from typing import Dict, Any, Optional
from shared.mcp_orchestrator import UnifiedMCPOrchestrator
from shared.oauth_client import oauth_client

load_dotenv()

# Configure Celery
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app = Celery(
    "boomi_tasks",
    broker=redis_url,
    backend=redis_url,
    broker_connection_retry_on_startup=True
)

# Celery configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour timeout
    task_soft_time_limit=3000,  # 50 minutes soft timeout
)

@app.task(bind=True, max_retries=3, retry_backoff=True)
def process_query_task(self, query: str, user_context: Dict[str, Any], bearer_token: str, interface_type: str = "mcp") -> Dict[str, Any]:
    """
    Asynchronous task to process a query using UnifiedMCPOrchestrator
    
    Args:
        query: User query string
        user_context: Dictionary containing query_intent, field_mappings, username, role
        bearer_token: OAuth 2.1 bearer token
        interface_type: Interface type ("cli", "web", "mcp")
    
    Returns:
        Dictionary with query results and metadata
    """
    try:
        print(f"🚀 Starting async query processing for {interface_type} interface: {query}")
        
        # Initialize orchestrator
        orchestrator = UnifiedMCPOrchestrator(interface_type=interface_type)
        
        # Process query
        result = orchestrator.process_query(
            query=query,
            user_context=user_context,
            bearer_token=bearer_token
        ).get()
        
        print(f"✅ Query processing completed: {result.get('success', False)}")
        return result
    
    except Exception as e:
        print(f"❌ Query processing error: {e}")
        self.retry(exc=e, countdown=60)
        return {
            "success": False,
            "error": str(e),
            "response_type": "ERROR"
        }
    
    finally:
        # Clean up orchestrator resources
        if 'orchestrator' in locals():
            orchestrator.close()

@app.task
def refresh_oauth_token(client_id: str, client_secret: str, refresh_token: str) -> Dict[str, Any]:
    """
    Asynchronous task to refresh OAuth token
    
    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        refresh_token: Current refresh token
    
    Returns:
        Dictionary with new access token and metadata
    """
    try:
        token_response = oauth_client.refresh_token(refresh_token)
        print(f"✅ OAuth token refreshed for client_id: {client_id}")
        return {
            "success": True,
            "access_token": token_response.get("access_token"),
            "refresh_token": token_response.get("refresh_token"),
            "expires_in": token_response.get("expires_in"),
            "scope": token_response.get("scope")
        }
    except Exception as e:
        print(f"❌ OAuth token refresh error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def setup_celery():
    """Initialize Celery configuration"""
    print("✅ Celery configuration initialized")
    return app