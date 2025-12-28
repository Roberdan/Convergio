"""
Backend API Client Tool for Ali and Agent Ecosystem
Provides authenticated access to Convergio backend APIs for data queries
"""

import requests
import json
from typing import Dict, Any, Optional
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ..utils.config import get_settings

class BackendAPIClient:
    """Client for making authenticated API calls to Convergio backend."""
    
    def __init__(self):
        self.settings = get_settings()
        self.backend_url = self.settings.backend_url
        self.session = requests.Session()
        self._jwt_token = None
        
        # Set default headers including service authentication
        service_secret = os.getenv("SERVICE_REGISTRY_SECRET")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Convergio-Ali-Agent/1.0"
        }
        
        # Add service authentication header if available
        if service_secret:
            headers["X-Service-Auth"] = service_secret
            
        self.session.headers.update(headers)
    
    def close(self):
        """Close the session."""
        self.session.close()
    
    def authenticate(self) -> bool:
        """Authenticate with the backend using service authentication."""
        try:
            # Use service authentication instead of admin credentials
            service_secret = os.getenv("SERVICE_REGISTRY_SECRET")
            
            if not service_secret:
                raise ValueError("SERVICE_REGISTRY_SECRET environment variable not set")
            
            # Update headers with service authentication
            self.session.headers.update({
                "X-Service-Auth": service_secret,
                "X-Service-Name": "agents-service"
            })
            
            return True
            
        except Exception as e:
            print(f"Service authentication failed: {e}")
            return False
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to backend API."""
        # Ensure we're authenticated
        if not self.authenticate():
            return {"error": "Failed to authenticate with backend", "status": 401}
            
        # Use service endpoints for inter-service communication
        if endpoint.startswith('/api/v1/health'):
            endpoint = endpoint.replace('/api/v1/health', '/api/v1/service/health')
            
        url = f"{self.backend_url}{endpoint}"
        
        try:
            kwargs = {
                "timeout": 30
            }
            
            if params:
                kwargs["params"] = params
                
            if data:
                kwargs["json"] = data
            
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                return {"error": "Authentication required", "status": 401}
            elif response.status_code == 403:
                return {"error": "Access forbidden", "status": 403}
            else:
                return {
                    "error": f"API request failed: {response.status_code}",
                    "status": response.status_code,
                    "message": response.text
                }
                    
        except requests.exceptions.Timeout:
            return {"error": "Request timeout", "status": 408}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}", "status": 500}
    
    def get_talents_count(self) -> Dict[str, Any]:
        """Get total number of talents in the system."""
        result = self._make_request("GET", "/api/v1/talents")
        
        if "error" in result:
            return result
            
        # Count talents if we got a successful response
        if isinstance(result, list):
            return {
                "total_talents": len(result),
                "status": "success",
                "message": f"Found {len(result)} talents in the database"
            }
        elif isinstance(result, dict) and "data" in result:
            talents = result["data"]
            return {
                "total_talents": len(talents),
                "status": "success", 
                "message": f"Found {len(talents)} talents in the database"
            }
        else:
            return {
                "error": "Unexpected response format",
                "status": 500,
                "response": result
            }
    
    def get_engagements_summary(self) -> Dict[str, Any]:
        """Get engagements summary and statistics."""
        result = self._make_request("GET", "/api/v1/engagements")
        
        if "error" in result:
            return result
            
        # Analyze engagements
        if isinstance(result, list):
            engagements = result
        elif isinstance(result, dict) and "data" in result:
            engagements = result["data"] 
        else:
            return {"error": "Unexpected response format", "response": result}
        
        # Calculate basic statistics
        total_engagements = len(engagements)
        active_engagements = 0
        completed_engagements = 0
        
        for engagement in engagements:
            status = engagement.get("status", "").lower()
            if status in ["active", "in_progress", "ongoing"]:
                active_engagements += 1
            elif status in ["completed", "finished", "done"]:
                completed_engagements += 1
        
        return {
            "total_engagements": total_engagements,
            "active_engagements": active_engagements,
            "completed_engagements": completed_engagements,
            "status": "success",
            "message": f"Found {total_engagements} total engagements ({active_engagements} active, {completed_engagements} completed)"
        }
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        return self._make_request("GET", "/api/v1/dashboard/stats")
    
    def get_skills_overview(self) -> Dict[str, Any]:
        """Get skills overview from the system."""
        result = self._make_request("GET", "/api/v1/skills")
        
        if "error" in result:
            return result
            
        if isinstance(result, list):
            skills = result
        elif isinstance(result, dict) and "data" in result:
            skills = result["data"]
        else:
            return {"error": "Unexpected response format", "response": result}
        
        return {
            "total_skills": len(skills),
            "status": "success",
            "message": f"Found {len(skills)} skills in the database"
        }

# Global instance for reuse
_backend_client: Optional[BackendAPIClient] = None

def get_backend_client() -> BackendAPIClient:
    """Get or create backend API client instance."""
    global _backend_client
    if _backend_client is None:
        _backend_client = BackendAPIClient()
    return _backend_client

def query_talents_count() -> str:
    """Tool function: Get the total number of talents in the database."""
    client = get_backend_client()
    result = client.get_talents_count()
    
    if result.get("status") == "success":
        return f"✅ {result['message']}"
    else:
        return f"❌ Error getting talents count: {result.get('error', 'Unknown error')}"

def query_engagements_summary() -> str:
    """Tool function: Get engagements summary and statistics.""" 
    client = get_backend_client()
    result = client.get_engagements_summary()
    
    if result.get("status") == "success":
        return f"✅ {result['message']}"
    else:
        return f"❌ Error getting engagements summary: {result.get('error', 'Unknown error')}"

def query_dashboard_stats() -> str:
    """Tool function: Get comprehensive dashboard statistics."""
    client = get_backend_client()
    result = client.get_dashboard_stats()
    
    if "error" in result:
        return f"❌ Error getting dashboard stats: {result['error']}"
    else:
        # Format the dashboard stats nicely
        stats = []
        for key, value in result.items():
            if isinstance(value, (int, float)):
                stats.append(f"{key}: {value}")
            elif isinstance(value, str):
                stats.append(f"{key}: {value}")
        
        if stats:
            return "✅ Dashboard Statistics:\n" + "\n".join(stats)
        else:
            return f"✅ Dashboard data retrieved: {json.dumps(result, indent=2)}"

def query_skills_overview() -> str:
    """Tool function: Get skills overview from the system."""
    client = get_backend_client()
    result = client.get_skills_overview()
    
    if result.get("status") == "success":
        return f"✅ {result['message']}"
    else:
        return f"❌ Error getting skills overview: {result.get('error', 'Unknown error')}"