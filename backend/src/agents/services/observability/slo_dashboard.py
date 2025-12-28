"""
SLO Dashboard System for Service Level Objectives
Provides real-time monitoring and alerting for key metrics
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from ...utils.config import get_settings

class SLOStatus(Enum):
    """SLO status enumeration"""
    EXCELLENT = "excellent"  # 95-100%
    GOOD = "good"           # 90-94%
    WARNING = "warning"     # 80-89%
    CRITICAL = "critical"   # <80%

@dataclass
class SLOTarget:
    """SLO target configuration"""
    name: str
    target_percentage: float
    measurement_window: int  # seconds
    error_budget: float = 0.05  # 5% default error budget
    
@dataclass
class SLOMeasurement:
    """SLO measurement data"""
    timestamp: datetime
    value: float
    status: SLOStatus
    metadata: Dict[str, Any] = field(default_factory=dict)

class SLODashboard:
    """SLO Dashboard for monitoring service level objectives"""
    
    def __init__(self):
        self.settings = get_settings()
        self.slo_targets: Dict[str, SLOTarget] = {}
        self.measurements: Dict[str, List[SLOMeasurement]] = {}
        self.alerts: List[Dict[str, Any]] = []
        
        # Initialize default SLOs
        self._initialize_default_slos()
    
    def _initialize_default_slos(self):
        """Initialize default SLO targets"""
        default_slos = {
            "api_availability": SLOTarget(
                name="API Availability",
                target_percentage=99.9,
                measurement_window=300,  # 5 minutes
                error_budget=0.001
            ),
            "response_time_p95": SLOTarget(
                name="Response Time P95",
                target_percentage=95.0,
                measurement_window=300,
                error_budget=0.05
            ),
            "error_rate": SLOTarget(
                name="Error Rate",
                target_percentage=99.5,
                measurement_window=300,
                error_budget=0.005
            ),
            "decision_accuracy": SLOTarget(
                name="Decision Engine Accuracy",
                target_percentage=95.0,
                measurement_window=600,  # 10 minutes
                error_budget=0.05
            ),
            "rag_context_hit_rate": SLOTarget(
                name="RAG Context Hit Rate",
                target_percentage=70.0,
                measurement_window=300,
                error_budget=0.30
            ),
            "cost_prediction_error": SLOTarget(
                name="Cost Prediction Error",
                target_percentage=90.0,
                measurement_window=600,
                error_budget=0.10
            )
        }
        
        for key, slo in default_slos.items():
            self.add_slo_target(key, slo)
    
    def add_slo_target(self, key: str, slo: SLOTarget):
        """Add a new SLO target"""
        self.slo_targets[key] = slo
        self.measurements[key] = []
    
    def record_measurement(self, slo_key: str, value: float, metadata: Optional[Dict[str, Any]] = None):
        """Record a new SLO measurement"""
        if slo_key not in self.slo_targets:
            raise ValueError(f"SLO target '{slo_key}' not found")
        
        target = self.slo_targets[slo_key]
        status = self._calculate_status(value, target)
        
        measurement = SLOMeasurement(
            timestamp=datetime.now(),
            value=value,
            status=status,
            metadata=metadata or {}
        )
        
        self.measurements[slo_key].append(measurement)
        
        # Clean old measurements
        self._cleanup_old_measurements(slo_key)
        
        # Check for alerts
        if status in [SLOStatus.WARNING, SLOStatus.CRITICAL]:
            self._create_alert(slo_key, measurement, target)
    
    def _calculate_status(self, value: float, target: SLOTarget) -> SLOStatus:
        """Calculate SLO status based on value and target"""
        if value >= 95.0:
            return SLOStatus.EXCELLENT
        elif value >= 90.0:
            return SLOStatus.GOOD
        elif value >= 80.0:
            return SLOStatus.WARNING
        else:
            return SLOStatus.CRITICAL
    
    def _cleanup_old_measurements(self, slo_key: str):
        """Remove old measurements outside the measurement window"""
        target = self.slo_targets[slo_key]
        cutoff_time = datetime.now() - timedelta(seconds=target.measurement_window)
        
        self.measurements[slo_key] = [
            m for m in self.measurements[slo_key]
            if m.timestamp > cutoff_time
        ]
    
    def _create_alert(self, slo_key: str, measurement: SLOMeasurement, target: SLOTarget):
        """Create an alert for SLO violation"""
        alert = {
            'id': f"{slo_key}_{int(time.time())}",
            'slo_key': slo_key,
            'slo_name': target.name,
            'timestamp': measurement.timestamp.isoformat(),
            'value': measurement.value,
            'target': target.target_percentage,
            'status': measurement.status.value,
            'severity': 'high' if measurement.status == SLOStatus.CRITICAL else 'medium',
            'message': f"SLO '{target.name}' is {measurement.status.value}: {measurement.value}% (target: {target.target_percentage}%)"
        }
        
        self.alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    def get_slo_status(self, slo_key: str) -> Dict[str, Any]:
        """Get current status for a specific SLO"""
        if slo_key not in self.slo_targets:
            raise ValueError(f"SLO target '{slo_key}' not found")
        
        target = self.slo_targets[slo_key]
        measurements = self.measurements[slo_key]
        
        if not measurements:
            return {
                'slo_key': slo_key,
                'slo_name': target.name,
                'current_value': None,
                'status': SLOStatus.GOOD.value,
                'target': target.target_percentage,
                'measurement_count': 0,
                'last_updated': None
            }
        
        # Calculate current value (average of recent measurements)
        recent_measurements = [
            m for m in measurements
            if m.timestamp > datetime.now() - timedelta(seconds=target.measurement_window)
        ]
        
        if not recent_measurements:
            current_value = None
            status = SLOStatus.GOOD.value
        else:
            current_value = sum(m.value for m in recent_measurements) / len(recent_measurements)
            status = self._calculate_status(current_value, target).value
        
        return {
            'slo_key': slo_key,
            'slo_name': target.name,
            'current_value': current_value,
            'status': status,
            'target': target.target_percentage,
            'measurement_count': len(recent_measurements),
            'last_updated': measurements[-1].timestamp.isoformat() if measurements else None,
            'error_budget_remaining': target.error_budget * 100
        }
    
    def get_all_slo_status(self) -> Dict[str, Any]:
        """Get status for all SLOs"""
        slo_statuses = {}
        for slo_key in self.slo_targets:
            slo_statuses[slo_key] = self.get_slo_status(slo_key)
        
        # Calculate overall health score
        health_scores = []
        for status in slo_statuses.values():
            if status['current_value'] is not None:
                if status['status'] == SLOStatus.EXCELLENT.value:
                    health_scores.append(100)
                elif status['status'] == SLOStatus.GOOD.value:
                    health_scores.append(90)
                elif status['status'] == SLOStatus.WARNING.value:
                    health_scores.append(80)
                else:
                    health_scores.append(60)
        
        overall_health = sum(health_scores) / len(health_scores) if health_scores else 100
        
        return {
            'overall_health': overall_health,
            'overall_status': self._calculate_status(overall_health, SLOTarget("Overall", 95.0, 300)).value,
            'slo_count': len(self.slo_targets),
            'active_alerts': len([a for a in self.alerts if a['severity'] == 'high']),
            'slo_statuses': slo_statuses,
            'last_updated': datetime.now().isoformat()
        }
    
    def get_alerts(self, severity: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get alerts, optionally filtered by severity"""
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return alerts[:limit]
    
    def clear_alerts(self, alert_ids: Optional[List[str]] = None):
        """Clear alerts, optionally by specific IDs"""
        if alert_ids:
            self.alerts = [a for a in self.alerts if a['id'] not in alert_ids]
        else:
            self.alerts = []
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export current SLO metrics for external monitoring"""
        return {
            'slo_dashboard': {
                'overall_health': self.get_all_slo_status()['overall_health'],
                'slo_count': len(self.slo_targets),
                'active_alerts': len(self.alerts),
                'last_updated': datetime.now().isoformat()
            },
            'individual_slos': {
                slo_key: {
                    'current_value': status['current_value'],
                    'status': status['status'],
                    'target': status['target']
                }
                for slo_key, status in self.get_all_slo_status()['slo_statuses'].items()
            }
        }

# Global SLO dashboard instance
_slo_dashboard: Optional[SLODashboard] = None

def get_slo_dashboard() -> SLODashboard:
    """Get global SLO dashboard instance"""
    global _slo_dashboard
    if _slo_dashboard is None:
        _slo_dashboard = SLODashboard()
    return _slo_dashboard

async def record_slo_measurement(slo_key: str, value: float, metadata: Optional[Dict[str, Any]] = None):
    """Record SLO measurement (async wrapper)"""
    dashboard = get_slo_dashboard()
    dashboard.record_measurement(slo_key, value, metadata)
