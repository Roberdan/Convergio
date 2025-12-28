"""
Runbook System for On-Call Operations
Provides step-by-step procedures for incident response and troubleshooting
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import yaml
from ...utils.config import get_settings

class IncidentSeverity(Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(Enum):
    """Incident status"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"

@dataclass
class RunbookStep:
    """Individual step in a runbook"""
    step_id: str
    title: str
    description: str
    commands: List[str] = field(default_factory=list)
    expected_output: Optional[str] = None
    timeout_seconds: int = 300
    requires_confirmation: bool = False
    notes: Optional[str] = None

@dataclass
class Runbook:
    """Complete runbook for a specific incident type"""
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    category: str
    steps: List[RunbookStep]
    prerequisites: List[str] = field(default_factory=list)
    estimated_time: int = 30  # minutes
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

@dataclass
class Incident:
    """Incident record with runbook execution"""
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    category: str
    status: IncidentStatus
    runbook_id: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    notes: List[Dict[str, Any]] = field(default_factory=list)
    executed_steps: List[Dict[str, Any]] = field(default_factory=list)

class RunbookManager:
    """Manages runbooks and incident response"""
    
    def __init__(self):
        self.settings = get_settings()
        self.runbooks: Dict[str, Runbook] = {}
        self.incidents: Dict[str, Incident] = {}
        self.runbook_dir = Path("runbooks")
        
        # Initialize default runbooks
        self._initialize_default_runbooks()
    
    def _initialize_default_runbooks(self):
        """Initialize default runbooks for common scenarios"""
        default_runbooks = [
            Runbook(
                id="api_high_latency",
                title="API High Latency Response",
                description="Respond to API latency issues affecting user experience",
                severity=IncidentSeverity.HIGH,
                category="performance",
                estimated_time=45,
                steps=[
                    RunbookStep(
                        step_id="1",
                        title="Verify Incident",
                        description="Check if the latency issue is affecting multiple endpoints or users",
                        commands=[
                            "curl -w '@curl-format.txt' -o /dev/null -s 'https://api.example.com/health'",
                            "grep 'response_time' /var/log/nginx/access.log | tail -100"
                        ],
                        expected_output="Response time > 2 seconds for multiple requests",
                        notes="Use curl-format.txt to measure response times"
                    ),
                    RunbookStep(
                        step_id="2",
                        title="Check System Resources",
                        description="Monitor CPU, memory, and network usage",
                        commands=[
                            "top -bn1 | head -20",
                            "free -h",
                            "netstat -i"
                        ],
                        expected_output="High CPU usage (>80%) or memory pressure",
                        notes="Look for resource exhaustion patterns"
                    ),
                    RunbookStep(
                        step_id="3",
                        title="Check Database Performance",
                        description="Investigate database query performance",
                        commands=[
                            "psql -c 'SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE (now() - pg_stat_activity.query_start) > interval \'5 seconds\';'",
                            "psql -c 'SELECT schemaname, tablename, attname, n_distinct, correlation FROM pg_stats WHERE schemaname = \'public\' ORDER BY n_distinct DESC LIMIT 10;'"
                        ],
                        expected_output="Long-running queries or missing indexes",
                        notes="Focus on queries taking >5 seconds"
                    ),
                    RunbookStep(
                        step_id="4",
                        title="Implement Rate Limiting",
                        description="Apply rate limiting to reduce load",
                        commands=[
                            "redis-cli SET rate_limit:api:enabled 1",
                            "redis-cli SET rate_limit:api:requests_per_minute 30"
                        ],
                        expected_output="Rate limiting enabled successfully",
                        requires_confirmation=True,
                        notes="This will temporarily reduce API throughput"
                    ),
                    RunbookStep(
                        step_id="5",
                        title="Monitor Recovery",
                        description="Observe system recovery after rate limiting",
                        commands=[
                            "watch -n 5 'curl -s https://api.example.com/health | jq .response_time'",
                            "tail -f /var/log/nginx/access.log | grep 'response_time'"
                        ],
                        expected_output="Response times returning to normal (<500ms)",
                        timeout_seconds=600,
                        notes="Continue monitoring for at least 10 minutes"
                    )
                ],
                prerequisites=[
                    "Access to production servers",
                    "Database credentials",
                    "Redis access"
                ],
                tags=["api", "latency", "performance", "rate-limiting"]
            ),
            Runbook(
                id="decision_engine_failure",
                title="Decision Engine Failure",
                description="Respond to Decision Engine service failures",
                severity=IncidentSeverity.CRITICAL,
                category="ai_services",
                estimated_time=60,
                steps=[
                    RunbookStep(
                        step_id="1",
                        title="Verify Service Status",
                        description="Check if Decision Engine service is responding",
                        commands=[
                            "curl -f https://api.example.com/api/v1/decision-engine/health",
                            "systemctl status decision-engine"
                        ],
                        expected_output="Service not responding or failed",
                        notes="Check both HTTP health and systemd status"
                    ),
                    RunbookStep(
                        step_id="2",
                        title="Check Logs",
                        description="Examine Decision Engine logs for errors",
                        commands=[
                            "journalctl -u decision-engine -f --since '10 minutes ago'",
                            "tail -f /var/log/decision-engine/error.log"
                        ],
                        expected_output="Error messages or stack traces",
                        notes="Look for recent errors in the last 10 minutes"
                    ),
                    RunbookStep(
                        step_id="3",
                        title="Check Dependencies",
                        description="Verify Decision Engine dependencies are healthy",
                        commands=[
                            "curl -f https://api.example.com/api/v1/vector-store/health",
                            "curl -f https://api.example.com/api/v1/llm/health",
                            "redis-cli ping"
                        ],
                        expected_output="One or more dependencies failing",
                        notes="Decision Engine depends on vector store, LLM, and Redis"
                    ),
                    RunbookStep(
                        step_id="4",
                        title="Restart Service",
                        description="Restart Decision Engine service",
                        commands=[
                            "systemctl restart decision-engine",
                            "systemctl status decision-engine"
                        ],
                        expected_output="Service started successfully",
                        requires_confirmation=True,
                        notes="This will temporarily interrupt decision processing"
                    ),
                    RunbookStep(
                        step_id="5",
                        title="Verify Recovery",
                        description="Test Decision Engine functionality",
                        commands=[
                            "curl -X POST https://api.example.com/api/v1/decision-engine/decide -H 'Content-Type: application/json' -d '{\"query\": \"test query\"}'",
                            "curl -f https://api.example.com/api/v1/decision-engine/health"
                        ],
                        expected_output="Decision Engine responding and processing requests",
                        timeout_seconds=300,
                        notes="Test with a simple decision request"
                    )
                ],
                prerequisites=[
                    "Access to production servers",
                    "Decision Engine service access",
                    "API credentials"
                ],
                tags=["decision-engine", "ai-services", "critical", "restart"]
            ),
            Runbook(
                id="rag_context_failure",
                title="RAG Context Injection Failure",
                description="Respond to RAG context injection failures",
                severity=IncidentSeverity.MEDIUM,
                category="ai_services",
                estimated_time=30,
                steps=[
                    RunbookStep(
                        step_id="1",
                        title="Check RAG Service Health",
                        description="Verify RAG service is responding",
                        commands=[
                            "curl -f https://api.example.com/api/v1/rag/health",
                            "systemctl status rag-service"
                        ],
                        expected_output="RAG service not responding",
                        notes="Check both HTTP health and systemd status"
                    ),
                    RunbookStep(
                        step_id="2",
                        title="Check Vector Store",
                        description="Verify vector store is accessible",
                        commands=[
                            "curl -f https://api.example.com/api/v1/vector-store/health",
                            "redis-cli LLEN vector_store:embeddings"
                        ],
                        expected_output="Vector store not responding or empty",
                        notes="RAG depends on vector store for context retrieval"
                    ),
                    RunbookStep(
                        step_id="3",
                        title="Check Cache Status",
                        description="Verify RAG cache is functioning",
                        commands=[
                            "redis-cli INFO memory",
                            "redis-cli KEYS 'rag_cache:*' | wc -l"
                        ],
                        expected_output="Low memory or empty cache",
                        notes="RAG uses Redis for caching context"
                    ),
                    RunbookStep(
                        step_id="4",
                        title="Disable RAG Temporarily",
                        description="Disable RAG to restore basic functionality",
                        commands=[
                            "redis-cli SET feature_flag:rag_in_loop_enabled 0",
                            "curl -X POST https://api.example.com/api/v1/feature-flags/refresh"
                        ],
                        expected_output="RAG feature flag disabled",
                        requires_confirmation=True,
                        notes="This will disable context injection but restore basic chat"
                    ),
                    RunbookStep(
                        step_id="5",
                        title="Monitor Basic Functionality",
                        description="Verify basic chat functionality works without RAG",
                        commands=[
                            "curl -X POST https://api.example.com/api/v1/chat -H 'Content-Type: application/json' -d '{\"message\": \"test message\"}'"
                        ],
                        expected_output="Chat responding without context injection",
                        timeout_seconds=120,
                        notes="Basic chat should work without RAG context"
                    )
                ],
                prerequisites=[
                    "Access to production servers",
                    "Redis access",
                    "Feature flag management access"
                ],
                tags=["rag", "context-injection", "ai-services", "feature-flags"]
            )
        ]
        
        for runbook in default_runbooks:
            self.add_runbook(runbook)
    
    def add_runbook(self, runbook: Runbook):
        """Add a new runbook"""
        self.runbooks[runbook.id] = runbook
    
    def get_runbook(self, runbook_id: str) -> Optional[Runbook]:
        """Get a runbook by ID"""
        return self.runbooks.get(runbook_id)
    
    def get_runbooks_by_category(self, category: str) -> List[Runbook]:
        """Get runbooks by category"""
        return [r for r in self.runbooks.values() if r.category == category]
    
    def get_runbooks_by_severity(self, severity: IncidentSeverity) -> List[Runbook]:
        """Get runbooks by severity"""
        return [r for r in self.runbooks.values() if r.severity == severity]
    
    def search_runbooks(self, query: str) -> List[Runbook]:
        """Search runbooks by title, description, or tags"""
        query_lower = query.lower()
        results = []
        
        for runbook in self.runbooks.values():
            if (query_lower in runbook.title.lower() or
                query_lower in runbook.description.lower() or
                any(query_lower in tag.lower() for tag in runbook.tags)):
                results.append(runbook)
        
        return results
    
    def create_incident(self, title: str, description: str, severity: IncidentSeverity, 
                       category: str, runbook_id: Optional[str] = None) -> Incident:
        """Create a new incident"""
        incident_id = f"incident_{int(time.time())}"
        
        incident = Incident(
            id=incident_id,
            title=title,
            description=description,
            severity=severity,
            category=category,
            status=IncidentStatus.OPEN,
            runbook_id=runbook_id
        )
        
        self.incidents[incident_id] = incident
        return incident
    
    def update_incident_status(self, incident_id: str, status: IncidentStatus, 
                             notes: Optional[str] = None) -> Optional[Incident]:
        """Update incident status"""
        if incident_id not in self.incidents:
            return None
        
        incident = self.incidents[incident_id]
        incident.status = status
        incident.updated_at = datetime.now()
        
        if status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.now()
        
        if notes:
            incident.notes.append({
                'timestamp': datetime.now().isoformat(),
                'status': status.value,
                'notes': notes
            })
        
        return incident
    
    def execute_runbook_step(self, incident_id: str, step_id: str, 
                           output: str, success: bool, notes: Optional[str] = None) -> bool:
        """Execute a runbook step for an incident"""
        if incident_id not in self.incidents:
            return False
        
        incident = self.incidents[incident_id]
        
        step_record = {
            'step_id': step_id,
            'timestamp': datetime.now().isoformat(),
            'output': output,
            'success': success,
            'notes': notes
        }
        
        incident.executed_steps.append(step_record)
        incident.updated_at = datetime.now()
        
        return True
    
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get incident by ID"""
        return self.incidents.get(incident_id)
    
    def get_active_incidents(self) -> List[Incident]:
        """Get all active incidents"""
        return [i for i in self.incidents.values() 
                if i.status in [IncidentStatus.OPEN, IncidentStatus.INVESTIGATING]]
    
    def get_incidents_by_severity(self, severity: IncidentSeverity) -> List[Incident]:
        """Get incidents by severity"""
        return [i for i in self.incidents.values() if i.severity == severity]
    
    def export_runbook(self, runbook_id: str, format: str = "json") -> Optional[str]:
        """Export runbook in specified format"""
        runbook = self.get_runbook(runbook_id)
        if not runbook:
            return None
        
        if format == "json":
            return json.dumps(runbook, default=str, indent=2)
        elif format == "yaml":
            return yaml.dump(runbook, default_flow_style=False, default_representer=str)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def import_runbook_from_file(self, file_path: str) -> Optional[Runbook]:
        """Import runbook from file"""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    raise ValueError("Unsupported file format")
                
                # Convert to Runbook object
                runbook = Runbook(**data)
                self.add_runbook(runbook)
                return runbook
                
        except Exception as e:
            print(f"Error importing runbook: {e}")
            return None
    
    def get_runbook_statistics(self) -> Dict[str, Any]:
        """Get statistics about runbooks and incidents"""
        total_incidents = len(self.incidents)
        active_incidents = len(self.get_active_incidents())
        resolved_incidents = len([i for i in self.incidents.values() 
                                if i.status == IncidentStatus.RESOLVED])
        
        severity_counts = {}
        for severity in IncidentSeverity:
            severity_counts[severity.value] = len(self.get_incidents_by_severity(severity))
        
        category_counts = {}
        for incident in self.incidents.values():
            category_counts[incident.category] = category_counts.get(incident.category, 0) + 1
        
        return {
            'total_runbooks': len(self.runbooks),
            'total_incidents': total_incidents,
            'active_incidents': active_incidents,
            'resolved_incidents': resolved_incidents,
            'severity_distribution': severity_counts,
            'category_distribution': category_counts,
            'last_updated': datetime.now().isoformat()
        }

# Global runbook manager instance
_runbook_manager: Optional[RunbookManager] = None

def get_runbook_manager() -> RunbookManager:
    """Get global runbook manager instance"""
    global _runbook_manager
    if _runbook_manager is None:
        _runbook_manager = RunbookManager()
    return _runbook_manager
