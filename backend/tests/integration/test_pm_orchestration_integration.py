"""
Integration Tests for PM Orchestration System
Tests the complete AI-orchestrated project management workflow end-to-end
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, Any
import json

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.core.database import get_async_session
from src.models.project import Project
from src.models.project_orchestration import (
    ProjectOrchestration, ProjectAgentAssignment, ProjectJourneyStage,
    ProjectTouchpoint, OrchestrationStatus, JourneyStage, TouchpointType, AgentRole
)
from src.services.pm_orchestrator_service import PMOrchestratorService
from src.services.project_journey_service import ProjectJourneyService
from src.api.schemas.project_orchestration import EnhancedProjectCreateRequest


class TestPMOrchestrationIntegration:
    """Integration tests for PM orchestration system"""
    
    @pytest.fixture
    async def async_client(self):
        """Create async HTTP client for testing"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    
    @pytest.fixture
    async def db_session(self):
        """Create database session for testing"""
        async with get_async_session() as session:
            yield session
    
    @pytest.fixture
    async def sample_project(self, db_session: AsyncSession):
        """Create sample project for testing"""
        project = Project(
            name="Test AI Platform",
            description="Test project for orchestration",
            status="active"
        )
        
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        
        return project
    
    @pytest.fixture
    def sample_orchestration_request(self):
        """Create sample orchestration request"""
        return {
            "name": "AI Platform Development",
            "description": "Comprehensive AI platform with multi-agent coordination",
            "project_type": "ai_implementation",
            "requirements": [
                "Multi-agent orchestration system",
                "Real-time monitoring dashboard", 
                "Cost tracking and optimization",
                "Scalable architecture"
            ],
            "constraints": [
                "6-month timeline",
                "$500K budget",
                "High security requirements"
            ],
            "success_criteria": [
                "95% system uptime",
                "Cost efficiency under budget",
                "User satisfaction > 90%"
            ],
            "budget": 500000.0,
            "timeline_days": 180,
            "orchestration_config": {
                "coordination_pattern": "hierarchical",
                "auto_agent_assignment": True,
                "real_time_monitoring": True,
                "max_concurrent_agents": 5,
                "optimization_frequency_hours": 24
            },
            "primary_agent": "ali-chief-of-staff",
            "context": {
                "priority": "high",
                "stakeholders": ["CTO", "Product Manager", "Engineering Team"]
            },
            "user_id": "test_user_123"
        }
    
    async def test_create_orchestrated_project_end_to_end(
        self, 
        async_client: AsyncClient,
        sample_orchestration_request: Dict[str, Any]
    ):
        """Test complete orchestrated project creation workflow"""
        
        # Create orchestrated project
        response = await async_client.post(
            "/api/v1/pm/orchestration/projects",
            json=sample_orchestration_request
        )
        
        assert response.status_code == 200
        project_data = response.json()
        
        # Verify orchestration was created
        assert "id" in project_data
        assert project_data["orchestration_enabled"] is True
        assert project_data["primary_agent"] == "ali-chief-of-staff"
        assert project_data["orchestration_status"] == "active"
        assert project_data["current_stage"] == "discovery"
        
        # Verify agent assignments were created
        assert len(project_data["agent_assignments"]) > 0
        assert any(agent["agent_name"] == "ali-chief-of-staff" for agent in project_data["agent_assignments"])
        
        # Verify journey stages were initialized
        assert len(project_data["journey_stages"]) == 6  # All default stages
        discovery_stage = next(
            stage for stage in project_data["journey_stages"] 
            if stage["stage_name"] == "discovery"
        )
        assert discovery_stage["status"] == "active"
        
        # Verify initial touchpoint was created
        assert len(project_data["recent_touchpoints"]) > 0
        
        return project_data["id"]
    
    async def test_journey_stage_progression(
        self,
        async_client: AsyncClient,
        sample_orchestration_request: Dict[str, Any]
    ):
        """Test journey stage progression workflow"""
        
        # Create orchestrated project
        response = await async_client.post(
            "/api/v1/pm/orchestration/projects",
            json=sample_orchestration_request
        )
        orchestration_id = response.json()["id"]
        
        # Update discovery stage to completed
        update_request = {
            "orchestration_id": orchestration_id,
            "stage_name": "discovery",
            "status": "completed",
            "progress_percentage": 100.0,
            "notes": "Requirements gathering completed successfully",
            "deliverables": [
                "Requirements document",
                "Stakeholder analysis",
                "Risk assessment"
            ]
        }
        
        response = await async_client.put(
            f"/api/v1/pm/orchestration/projects/{orchestration_id}/journey/stages",
            json=update_request
        )
        
        assert response.status_code == 200
        
        # Transition to planning stage
        response = await async_client.post(
            f"/api/v1/pm/orchestration/projects/{orchestration_id}/journey/transition",
            params={
                "from_stage": "discovery",
                "to_stage": "planning", 
                "transition_reason": "Discovery phase completed successfully"
            }
        )
        
        assert response.status_code == 200
        transition_data = response.json()
        
        assert transition_data["success"] is True
        assert transition_data["from_stage"] == "discovery"
        assert transition_data["to_stage"] == "planning"
        
        # Verify orchestration current stage updated
        response = await async_client.get(
            f"/api/v1/pm/orchestration/projects/{orchestration_id}"
        )
        
        orchestration_data = response.json()
        assert orchestration_data["current_stage"] == "planning"
        
        # Verify planning stage is now active
        planning_stage = next(
            stage for stage in orchestration_data["journey_stages"]
            if stage["stage_name"] == "planning"
        )
        assert planning_stage["status"] == "active"
    
    async def test_touchpoint_creation_and_tracking(
        self,
        async_client: AsyncClient,
        sample_orchestration_request: Dict[str, Any]
    ):
        """Test touchpoint creation and analytics"""
        
        # Create orchestrated project
        response = await async_client.post(
            "/api/v1/pm/orchestration/projects",
            json=sample_orchestration_request
        )
        orchestration_id = response.json()["id"]
        
        # Create multiple touchpoints
        touchpoint_requests = [
            {
                "orchestration_id": orchestration_id,
                "touchpoint_type": "client_checkin",
                "title": "Weekly Status Review",
                "summary": "Reviewed project progress with client stakeholders",
                "participants": ["ali-chief-of-staff", "client_pm"],
                "duration_minutes": 45,
                "key_decisions": [
                    "Approved architecture approach",
                    "Increased testing phase duration"
                ],
                "action_items": [
                    "Prepare detailed technical specifications",
                    "Schedule security review meeting"
                ],
                "satisfaction_score": 0.85,
                "impact_level": "high"
            },
            {
                "orchestration_id": orchestration_id,
                "touchpoint_type": "milestone_review",
                "title": "Discovery Phase Completion",
                "summary": "Completed discovery phase milestone review",
                "participants": ["ali-chief-of-staff", "antonio-strategy"],
                "duration_minutes": 30,
                "key_decisions": [
                    "Move to planning phase",
                    "Allocate additional resources"
                ],
                "satisfaction_score": 0.92,
                "impact_level": "critical"
            }
        ]
        
        for touchpoint_request in touchpoint_requests:
            response = await async_client.post(
                f"/api/v1/pm/orchestration/projects/{orchestration_id}/touchpoints",
                json=touchpoint_request
            )
            assert response.status_code == 200
        
        # Get touchpoints
        response = await async_client.get(
            f"/api/v1/pm/orchestration/projects/{orchestration_id}/touchpoints",
            params={"limit": 10}
        )
        
        assert response.status_code == 200
        touchpoints_data = response.json()
        
        # Verify touchpoints were created (including initial touchpoint)
        assert touchpoints_data["total"] >= 2
    
    async def test_project_optimization_workflow(
        self,
        async_client: AsyncClient,
        sample_orchestration_request: Dict[str, Any]
    ):
        """Test AI-powered project optimization"""
        
        # Create orchestrated project
        response = await async_client.post(
            "/api/v1/pm/orchestration/projects",
            json=sample_orchestration_request
        )
        orchestration_id = response.json()["id"]
        
        # Request optimization
        optimization_request = {
            "orchestration_id": orchestration_id,
            "optimization_type": "performance",
            "constraints": {
                "budget_limit": 500000,
                "timeline_limit": 180
            },
            "preferences": {
                "prioritize": "quality",
                "risk_tolerance": "medium"
            }
        }
        
        response = await async_client.post(
            f"/api/v1/pm/orchestration/projects/{orchestration_id}/optimize",
            json=optimization_request
        )
        
        assert response.status_code == 200
        optimization_data = response.json()
        
        # Verify optimization response structure
        assert "orchestration_id" in optimization_data
        assert "optimization_type" in optimization_data
        assert "current_performance" in optimization_data
        assert "analysis_date" in optimization_data
        
        # Verify last_optimization timestamp was updated
        response = await async_client.get(
            f"/api/v1/pm/orchestration/projects/{orchestration_id}"
        )
        orchestration_data = response.json()
        assert orchestration_data["last_optimization"] is not None
    
    async def test_journey_analytics_and_insights(
        self,
        async_client: AsyncClient,
        sample_orchestration_request: Dict[str, Any]
    ):
        """Test journey analytics and predictive insights"""
        
        # Create orchestrated project
        response = await async_client.post(
            "/api/v1/pm/orchestration/projects",
            json=sample_orchestration_request
        )
        orchestration_id = response.json()["id"]
        
        # Get journey analytics
        response = await async_client.get(
            f"/api/v1/pm/orchestration/projects/{orchestration_id}/journey"
        )
        
        assert response.status_code == 200
        analytics_data = response.json()
        
        # Verify analytics structure
        assert "orchestration_id" in analytics_data
        assert "current_stage" in analytics_data
        assert "completion_percentage" in analytics_data
        assert "stage_progression" in analytics_data
        assert "touchpoint_summary" in analytics_data
        assert "risk_factors" in analytics_data
        assert "success_probability" in analytics_data
        assert "recommended_interventions" in analytics_data
        
        # Verify stage progression data
        assert len(analytics_data["stage_progression"]) == 6
        
        # Verify predictive analytics
        assert 0 <= analytics_data["success_probability"] <= 1
        assert isinstance(analytics_data["risk_factors"], list)
        assert isinstance(analytics_data["recommended_interventions"], list)
    
    async def test_satisfaction_score_calculation(
        self,
        async_client: AsyncClient,
        sample_orchestration_request: Dict[str, Any]
    ):
        """Test satisfaction score calculation"""
        
        # Create orchestrated project
        response = await async_client.post(
            "/api/v1/pm/orchestration/projects",
            json=sample_orchestration_request
        )
        orchestration_id = response.json()["id"]
        
        # Create touchpoint with satisfaction score
        touchpoint_request = {
            "orchestration_id": orchestration_id,
            "touchpoint_type": "client_checkin",
            "title": "Client Satisfaction Review",
            "summary": "Excellent progress, client very satisfied",
            "satisfaction_score": 0.95,
            "impact_level": "high"
        }
        
        await async_client.post(
            f"/api/v1/pm/orchestration/projects/{orchestration_id}/touchpoints",
            json=touchpoint_request
        )
        
        # Get overall satisfaction score
        response = await async_client.get(
            f"/api/v1/pm/orchestration/projects/{orchestration_id}/satisfaction"
        )
        
        assert response.status_code == 200
        satisfaction_data = response.json()
        
        assert "satisfaction_score" in satisfaction_data
        assert "rating" in satisfaction_data
        assert 0 <= satisfaction_data["satisfaction_score"] <= 1
        assert satisfaction_data["rating"] in [
            "Excellent", "Very Good", "Good", "Fair", "Needs Improvement"
        ]
    
    async def test_metrics_and_performance_tracking(
        self,
        async_client: AsyncClient,
        sample_orchestration_request: Dict[str, Any]
    ):
        """Test comprehensive metrics tracking"""
        
        # Create orchestrated project
        response = await async_client.post(
            "/api/v1/pm/orchestration/projects",
            json=sample_orchestration_request
        )
        orchestration_id = response.json()["id"]
        
        # Get performance metrics
        response = await async_client.get(
            f"/api/v1/pm/orchestration/projects/{orchestration_id}/metrics",
            params={"period_days": 30}
        )
        
        assert response.status_code == 200
        metrics_data = response.json()
        
        # Verify metrics structure
        assert "performance_metrics" in metrics_data
        assert "collaboration_metrics" in metrics_data
        assert "cost_metrics" in metrics_data
        assert "recommendations" in metrics_data
        
        # Verify performance metrics
        perf_metrics = metrics_data["performance_metrics"]
        assert "overall_efficiency" in perf_metrics
        assert "agent_utilization" in perf_metrics
        assert "cost_efficiency" in perf_metrics
        assert "timeline_efficiency" in perf_metrics
        assert "quality_score" in perf_metrics
        
        # Verify all scores are between 0 and 1
        for score in perf_metrics.values():
            assert 0 <= score <= 1
    
    async def test_error_handling_and_validation(
        self,
        async_client: AsyncClient
    ):
        """Test error handling and input validation"""
        
        # Test invalid orchestration request
        invalid_request = {
            "name": "",  # Empty name should fail
            "project_type": "invalid_type",
            "requirements": []  # Empty requirements should fail
        }
        
        response = await async_client.post(
            "/api/v1/pm/orchestration/projects",
            json=invalid_request
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test non-existent orchestration ID
        fake_id = str(uuid4())
        response = await async_client.get(
            f"/api/v1/pm/orchestration/projects/{fake_id}"
        )
        
        assert response.status_code == 404
        
        # Test invalid stage update
        response = await async_client.put(
            f"/api/v1/pm/orchestration/projects/{fake_id}/journey/stages",
            json={
                "orchestration_id": fake_id,
                "stage_name": "discovery",
                "status": "invalid_status",  # Invalid status
                "progress_percentage": 150.0  # Invalid percentage
            }
        )
        
        assert response.status_code in [404, 422]
    
    async def test_concurrent_operations(
        self,
        async_client: AsyncClient,
        sample_orchestration_request: Dict[str, Any]
    ):
        """Test concurrent operations on orchestration"""
        
        # Create orchestrated project
        response = await async_client.post(
            "/api/v1/pm/orchestration/projects",
            json=sample_orchestration_request
        )
        orchestration_id = response.json()["id"]
        
        # Perform concurrent operations
        tasks = []
        
        # Concurrent touchpoint creation
        for i in range(3):
            touchpoint_request = {
                "orchestration_id": orchestration_id,
                "touchpoint_type": "status_update",
                "title": f"Concurrent Update {i}",
                "summary": f"Concurrent operation test {i}"
            }
            
            task = async_client.post(
                f"/api/v1/pm/orchestration/projects/{orchestration_id}/touchpoints",
                json=touchpoint_request
            )
            tasks.append(task)
        
        # Concurrent metrics retrieval
        for i in range(2):
            task = async_client.get(
                f"/api/v1/pm/orchestration/projects/{orchestration_id}/metrics"
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        responses = await asyncio.gather(*tasks)
        
        # Verify all operations succeeded
        for response in responses:
            assert response.status_code == 200
    
    async def test_bulk_operations(self, async_client: AsyncClient):
        """Test bulk operations on multiple projects"""
        
        # Create multiple orchestrated projects
        orchestration_ids = []
        
        for i in range(3):
            request = {
                "name": f"Bulk Test Project {i}",
                "description": f"Bulk operation test project {i}",
                "project_type": "web_development",
                "requirements": [f"Requirement {i}"],
                "budget": 100000.0,
                "timeline_days": 90
            }
            
            response = await async_client.post(
                "/api/v1/pm/orchestration/projects",
                json=request
            )
            
            assert response.status_code == 200
            orchestration_ids.append(response.json()["id"])
        
        # Test bulk optimization
        response = await async_client.post(
            "/api/v1/pm/orchestration/projects/bulk-optimize",
            json=orchestration_ids,
            params={"optimization_type": "cost"}
        )
        
        assert response.status_code == 200
        bulk_data = response.json()
        
        assert bulk_data["project_count"] == 3
        assert bulk_data["optimization_type"] == "cost"
        assert "scheduled_at" in bulk_data
    
    async def test_list_orchestrated_projects(
        self,
        async_client: AsyncClient,
        sample_orchestration_request: Dict[str, Any]
    ):
        """Test listing orchestrated projects with filtering"""
        
        # Create orchestrated project
        response = await async_client.post(
            "/api/v1/pm/orchestration/projects",
            json=sample_orchestration_request
        )
        
        # List all projects
        response = await async_client.get(
            "/api/v1/pm/orchestration/projects",
            params={"limit": 50, "offset": 0}
        )
        
        assert response.status_code == 200
        projects_data = response.json()
        
        assert "projects" in projects_data
        assert "total" in projects_data
        assert "limit" in projects_data
        assert "offset" in projects_data
        
        # Test filtering by status
        response = await async_client.get(
            "/api/v1/pm/orchestration/projects",
            params={"status": "active", "limit": 50}
        )
        
        assert response.status_code == 200


@pytest.mark.asyncio
class TestPMOrchestrationServices:
    """Direct service-level integration tests"""
    
    async def test_pm_orchestrator_service_integration(self):
        """Test PMOrchestratorService directly"""
        
        service = PMOrchestratorService()
        
        # Test service initialization
        assert service.unified_orchestrator is not None
        assert service.cost_tracker is not None
        assert len(service.project_type_agents) > 0
        assert len(service.default_journey_stages) == 6
    
    async def test_journey_service_integration(self):
        """Test ProjectJourneyService directly"""
        
        service = ProjectJourneyService()
        
        # Test service initialization
        assert service.satisfaction_weights is not None
        assert len(service.satisfaction_weights) == 5
        assert sum(service.satisfaction_weights.values()) == 1.0


if __name__ == "__main__":
    # Run specific tests for development
    import subprocess
    subprocess.run([
        "python", "-m", "pytest", 
        "tests/integration/test_pm_orchestration_integration.py",
        "-v", "--tb=short"
    ])