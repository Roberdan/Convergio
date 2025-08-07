#!/usr/bin/env python3
"""
🚀 Test Backend for Convergio Frontend Testing
Quick backend to test both SvelteKit and Reflex frontends
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn

# ================================
# 🔧 SIMPLE MODELS
# ================================

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class DashboardData(BaseModel):
    overview: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    cost_summary: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

# ================================
# 🚀 FASTAPI APP
# ================================

app = FastAPI(
    title="Convergio Test Backend",
    description="Simple backend for frontend testing",
    version="2.0.0-test"
)

# CORS middleware for both frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Reflex
        "http://localhost:4000",  # SvelteKit
        "http://127.0.0.1:3000",
        "http://127.0.0.1:4000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# 🔐 AUTH ENDPOINTS
# ================================

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Simple login endpoint with multiple test accounts"""
    
    # Test accounts
    if request.username == "admin" and request.password == "admin":
        return LoginResponse(
            access_token="test-token-12345",
            user={
                "id": 1,
                "username": "admin",
                "email": "admin@convergio.io",
                "full_name": "Admin User",
                "is_admin": True
            }
        )
    
    elif request.username == "roberdan@convergio.local" and request.password == "admin123":
        return LoginResponse(
            access_token="test-token-roberdan",
            user={
                "id": 2,
                "username": "roberdan@convergio.local",
                "email": "roberdan@convergio.local",
                "full_name": "Roberto Daniele",
                "is_admin": True
            }
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

@app.get("/api/v1/auth/user")
async def get_user():
    """Get current user"""
    return {
        "id": 1,
        "username": "admin",
        "email": "admin@convergio.io",
        "full_name": "Admin User",
        "is_admin": True
    }

@app.post("/api/v1/auth/logout")
async def logout():
    """Logout endpoint"""
    return {"message": "Logout successful"}

# ================================
# 📊 DASHBOARD ENDPOINTS
# ================================

@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_analytics(time_range: str = "7d"):
    """Get dashboard analytics"""
    return DashboardData(
        overview={
            "total_users": 142,
            "active_users": 89,
            "system_health": "Healthy"
        },
        performance_metrics={
            "agent_interactions": 1256,
            "avg_response_time": "0.8s",
            "success_rate": "99.2%"
        },
        cost_summary={
            "total_cost": 234.56,
            "top_models": ["gpt-4", "gpt-3.5-turbo"],
            "monthly_budget": 500.0
        }
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="2.0.0-test"
    )

# ================================
# 🤖 AGENTS ENDPOINTS (SIMPLIFIED)
# ================================

@app.get("/api/v1/agents")
async def get_agents():
    """Get available agents"""
    return [
        {
            "key": "ali-chief-of-staff",
            "name": "Ali - Chief of Staff",
            "description": "Master orchestrator for strategic solutions",
            "tier": "Elite"
        },
        {
            "key": "socrates-first-principles",
            "name": "Socrates - First Principles",
            "description": "Elite reasoning specialist using Socratic methodology",
            "tier": "Elite"
        },
        {
            "key": "baccio-tech-architect",
            "name": "Baccio - Tech Architect",
            "description": "Elite technology architect for system design",
            "tier": "Elite"
        }
    ]

@app.post("/api/v1/agents/{agent_type}/execute")
async def execute_agent(agent_type: str, request: Dict[str, Any]):
    """Execute an agent"""
    return {
        "execution_id": "exec-123",
        "agent": agent_type,
        "response": f"Hello! I'm {agent_type}. You said: '{request.get('message', '')}'. This is a test response from the test backend.",
        "status": "completed"
    }

# ================================
# 🚀 STARTUP
# ================================

if __name__ == "__main__":
    print("🚀 CONVERGIO TEST BACKEND")
    print("=" * 50)
    print("🔗 Backend URL: http://localhost:9002")
    print("🔐 Login Accounts:")
    print("   👤 admin / admin")
    print("   👤 roberdan@convergio.local / admin123")
    print("🎨 Frontend URLs:")
    print("   📱 Reflex:    http://localhost:3000")
    print("   ⚡ SvelteKit: http://localhost:4000")
    print("=" * 50)
    
    uvicorn.run(
        "test_backend:app",
        host="0.0.0.0",
        port=9002,
        reload=True,
        log_level="info"
    )