"""
GraphFlow Runner - Complete Workflow Execution Engine
Handles step-by-step execution with state management, error handling, and observability
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import structlog

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from .definitions import (
    BusinessWorkflow, WorkflowStep, WorkflowStatus,
    StepType
)
from agents.utils.config import get_settings

try:
    from ..observability.integration import get_observability
except ImportError:
    get_observability = None

logger = structlog.get_logger()


class StepStatus(Enum):
    """Status of individual workflow steps"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class StepExecutionResult:
    """Result of a single step execution"""
    step_id: str
    status: StepStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    duration_ms: Optional[int] = None
    cost_usd: float = 0.0
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """Complete workflow execution state"""
    execution_id: str
    workflow_id: str
    user_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    current_step: Optional[str] = None
    step_results: Dict[str, StepExecutionResult] = field(default_factory=dict)
    total_cost_usd: float = 0.0
    total_duration_ms: Optional[int] = None
    context: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    checkpoint_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


class GraphFlowRunner:
    """Advanced workflow execution engine with state management and observability"""
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        db_session: Optional[AsyncSession] = None
    ):
        self.redis = redis_client
        self.db_session = db_session
        # Lazy-load settings to avoid configuration issues in tests
        self.settings = None
        self.otel_manager = None
        self.active_executions: Dict[str, WorkflowExecution] = {}
        
    async def initialize(self):
        """Initialize connections and resources"""
        # Lazy-load settings if needed
        if not self.settings:
            try:
                self.settings = get_settings()
            except Exception:
                # Use defaults if settings not available
                pass
        
        if not self.redis and self.settings:
            self.redis = await redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        
        logger.info("🚀 GraphFlow Runner initialized")
    
    async def execute_workflow(
        self,
        workflow: BusinessWorkflow,
        user_id: str,
        context: Dict[str, Any] = None,
        resume_from: Optional[str] = None
    ) -> WorkflowExecution:
        """Execute a complete workflow with state tracking"""
        
        execution_id = str(uuid.uuid4())
        
        # Create execution record
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow.workflow_id,
            user_id=user_id,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow(),
            context=context or {}
        )
        
        self.active_executions[execution_id] = execution
        
        # Lazy-load OTEL manager if needed
        if not self.otel_manager:
            try:
                # Use ObservabilityIntegration as a provider for spans if available
                obs = get_observability()
                self.otel_manager = obs.telemetry if obs else None
            except Exception:
                self.otel_manager = None
        
        # Start OTEL span for workflow
        if self.otel_manager and hasattr(self.otel_manager, "span"):
            with self.otel_manager.span(
                f"workflow.{workflow.workflow_id}",
                {
                    "execution_id": execution_id,
                    "user_id": user_id,
                    "priority": workflow.priority.value
                }
            ) as span:
                try:
                    # Execute workflow steps
                    await self._execute_steps(workflow, execution, resume_from)
                    
                    # Mark as completed
                    execution.status = WorkflowStatus.COMPLETED
                    execution.completed_at = datetime.utcnow()
                    execution.total_duration_ms = int(
                        (execution.completed_at - execution.started_at).total_seconds() * 1000
                    )
                    
                    logger.info(
                        "✅ Workflow completed",
                        execution_id=execution_id,
                        duration_ms=execution.total_duration_ms,
                        total_cost=execution.total_cost_usd
                    )
                    
                except Exception as e:
                    execution.status = WorkflowStatus.FAILED
                    execution.error_message = str(e)
                    execution.completed_at = datetime.utcnow()
                    
                    logger.error(
                        "❌ Workflow failed",
                        execution_id=execution_id,
                        error=str(e)
                    )
                    
                    if span:
                        span.record_exception(e)
                    
                    raise
                
                finally:
                    # Persist final state
                    await self._persist_execution_state(execution)
        
        return execution
    
    async def _execute_steps(
        self,
        workflow: BusinessWorkflow,
        execution: WorkflowExecution,
        resume_from: Optional[str] = None
    ):
        """Execute workflow steps in sequence with dependency management"""
        
        # Build execution order respecting dependencies
        execution_order = self._build_execution_order(workflow.steps)
        
        # Resume from checkpoint if specified
        start_index = 0
        if resume_from:
            for i, step_id in enumerate(execution_order):
                if step_id == resume_from:
                    start_index = i
                    break
        
        # Execute steps
        for step_id in execution_order[start_index:]:
            step = next(s for s in workflow.steps if s.step_id == step_id)
            
            # Check if dependencies are met
            if not await self._check_dependencies(step, execution):
                logger.warning(f"Skipping step {step_id} - dependencies not met")
                execution.step_results[step_id] = StepExecutionResult(
                    step_id=step_id,
                    status=StepStatus.SKIPPED,
                    started_at=datetime.utcnow()
                )
                continue
            
            # Execute step
            execution.current_step = step_id
            result = await self._execute_single_step(step, execution)
            execution.step_results[step_id] = result
            
            # Update cost
            execution.total_cost_usd += result.cost_usd
            
            # Check for failures
            if result.status == StepStatus.FAILED:
                if step.retry_count > 0 and result.retry_count < step.retry_count:
                    # Retry step
                    logger.info(f"Retrying step {step_id}, attempt {result.retry_count + 1}")
                    result.retry_count += 1
                    await asyncio.sleep(5)  # Wait before retry
                    result = await self._execute_single_step(step, execution)
                    execution.step_results[step_id] = result
                
                if result.status == StepStatus.FAILED:
                    # Step failed after retries
                    await self._handle_step_failure(step, execution, result)
                    if not self._can_continue_after_failure(step, workflow):
                        raise Exception(f"Critical step {step_id} failed")
            
            # Save checkpoint after each step
            await self._save_checkpoint(execution)
            
            # Check for pause conditions
            if await self._should_pause(step, execution):
                execution.status = WorkflowStatus.PAUSED
                await self._persist_execution_state(execution)
                logger.info(f"Workflow paused at step {step_id}")
                return
    
    async def _execute_single_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> StepExecutionResult:
        """Execute a single workflow step"""
        
        result = StepExecutionResult(
            step_id=step.step_id,
            status=StepStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        try:
            # Start OTEL span for step
            if self.otel_manager:
                with self.otel_manager.span(
                    f"step.{step.step_type.value}",
                    {
                        "step_id": step.step_id,
                        "agent": step.agent_name,
                        "execution_id": execution.execution_id
                    }
                ):
                    # Prepare step inputs from previous outputs
                    step_inputs = await self._prepare_step_inputs(step, execution)
                    
                    # Execute step logic based on type
                    if step.approval_required:
                        outputs = await self._execute_approval_step(step, step_inputs)
                    else:
                        outputs = await self._execute_agent_step(step, step_inputs)
                    
                    result.outputs = outputs
                    result.status = StepStatus.COMPLETED
            
            # Calculate duration and cost
            result.completed_at = datetime.utcnow()
            result.duration_ms = int(
                (result.completed_at - result.started_at).total_seconds() * 1000
            )
            result.cost_usd = self._calculate_step_cost(step, result.duration_ms)
            
            logger.info(
                f"✅ Step completed: {step.step_id}",
                duration_ms=result.duration_ms,
                cost=result.cost_usd
            )
            
        except Exception as e:
            result.status = StepStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.utcnow()
            
            logger.error(
                f"❌ Step failed: {step.step_id}",
                error=str(e)
            )
        
        return result
    
    async def _execute_agent_step(
        self,
        step: WorkflowStep,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a step using an agent"""
        
        # This would integrate with the actual agent system
        # For now, return mock outputs
        logger.info(
            f"Executing agent step: {step.step_id}",
            agent=step.agent_name,
            inputs=list(inputs.keys())
        )
        
        # Simulate agent execution
        await asyncio.sleep(1)
        
        # Generate outputs based on step definition
        outputs = {}
        for output_name in step.outputs:
            outputs[output_name] = f"Generated {output_name} for {step.step_id}"
        
        return outputs
    
    async def _execute_approval_step(
        self,
        step: WorkflowStep,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an approval step requiring human intervention"""
        
        logger.info(
            f"⏸️ Approval required for step: {step.step_id}",
            description=step.description
        )
        
        # This would integrate with HITL system
        # For now, auto-approve after delay
        await asyncio.sleep(2)
        
        return {
            "approval_status": "approved",
            "approver": "system",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _build_execution_order(self, steps: List[WorkflowStep]) -> List[str]:
        """Build execution order respecting dependencies"""
        
        # Simple topological sort
        visited = set()
        order = []
        
        def visit(step_id: str):
            if step_id in visited:
                return
            
            step = next((s for s in steps if s.step_id == step_id), None)
            if not step:
                return
            
            # Visit dependencies first
            for dep in step.dependencies:
                visit(dep)
            
            visited.add(step_id)
            order.append(step_id)
        
        # Visit all steps
        for step in steps:
            visit(step.step_id)
        
        return order
    
    async def _check_dependencies(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> bool:
        """Check if step dependencies are satisfied"""
        
        for dep_id in step.dependencies:
            if dep_id not in execution.step_results:
                return False
            
            dep_result = execution.step_results[dep_id]
            if dep_result.status not in [StepStatus.COMPLETED, StepStatus.SKIPPED]:
                return False
        
        return True
    
    async def _prepare_step_inputs(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Prepare inputs for a step from previous outputs and context"""
        
        inputs = {}
        
        # Collect outputs from dependencies
        for dep_id in step.dependencies:
            if dep_id in execution.step_results:
                dep_outputs = execution.step_results[dep_id].outputs
                inputs.update(dep_outputs)
        
        # Add context data
        for input_name in step.inputs:
            if input_name in execution.context:
                inputs[input_name] = execution.context[input_name]
        
        return inputs
    
    def _calculate_step_cost(self, step: WorkflowStep, duration_ms: int) -> float:
        """Calculate cost for step execution"""
        
        # Base cost per step type
        base_costs = {
            StepType.ANALYSIS: 0.05,
            StepType.RESEARCH: 0.10,
            StepType.PLANNING: 0.08,
            StepType.EXECUTION: 0.03,
            StepType.APPROVAL: 0.01
        }
        
        base_cost = base_costs.get(step.step_type, 0.05)
        
        # Add time-based cost (per minute)
        time_cost = (duration_ms / 60000) * 0.02
        
        return base_cost + time_cost
    
    async def _handle_step_failure(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
        result: StepExecutionResult
    ):
        """Handle step failure with escalation if needed"""
        
        logger.error(
            f"Step {step.step_id} failed",
            errors=result.errors,
            retry_count=result.retry_count
        )
        
        # Check escalation triggers
        if step.escalation_triggers:
            # This would trigger escalation logic
            pass
    
    def _can_continue_after_failure(
        self,
        step: WorkflowStep,
        workflow: BusinessWorkflow
    ) -> bool:
        """Check if workflow can continue after step failure"""
        
        # Check if step is critical
        critical_steps = workflow.metadata.get("critical_steps", [])
        return step.step_id not in critical_steps
    
    async def _should_pause(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> bool:
        """Check if workflow should pause after step"""
        
        # Check for pause conditions
        pause_after = execution.context.get("pause_after_steps", [])
        return step.step_id in pause_after
    
    async def _save_checkpoint(self, execution: WorkflowExecution):
        """Save execution checkpoint for recovery"""
        
        if self.redis:
            checkpoint_key = f"workflow:checkpoint:{execution.execution_id}"
            checkpoint_data = {
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "current_step": execution.current_step,
                "status": execution.status.value,
                "step_results": {
                    k: asdict(v) for k, v in execution.step_results.items()
                },
                "context": execution.context,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.redis.setex(
                checkpoint_key,
                3600,  # 1 hour TTL
                json.dumps(checkpoint_data)
            )
    
    async def _persist_execution_state(self, execution: WorkflowExecution):
        """Persist execution state to database"""
        
        # This would save to PostgreSQL
        # For now, just log
        logger.info(
            "Persisting execution state",
            execution_id=execution.execution_id,
            status=execution.status.value
        )
    
    async def resume_workflow(
        self,
        execution_id: str,
        from_step: Optional[str] = None
    ) -> WorkflowExecution:
        """Resume a paused or failed workflow"""
        
        # Load checkpoint from Redis
        if self.redis:
            checkpoint_key = f"workflow:checkpoint:{execution_id}"
            checkpoint_data = await self.redis.get(checkpoint_key)
            
            if checkpoint_data:
                json.loads(checkpoint_data)
                
                # Reconstruct execution
                execution = self.active_executions.get(execution_id)
                if not execution:
                    # Recreate from checkpoint
                    logger.info(f"Resuming workflow {execution_id} from checkpoint")
                
                execution.status = WorkflowStatus.RUNNING
                
                # Continue execution
                # This would reload the workflow and continue from checkpoint
                
                return execution
        
        raise ValueError(f"Cannot resume workflow {execution_id} - no checkpoint found")
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow"""
        
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            
            await self._persist_execution_state(execution)
            
            logger.info(f"Workflow {execution_id} cancelled")
            return True
        
        return False
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current execution status"""
        
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            
            completed_steps = sum(
                1 for r in execution.step_results.values()
                if r.status == StepStatus.COMPLETED
            )
            
            total_steps = len(execution.step_results)
            
            return {
                "execution_id": execution_id,
                "workflow_id": execution.workflow_id,
                "status": execution.status.value,
                "current_step": execution.current_step,
                "progress_percentage": (completed_steps / total_steps * 100) if total_steps > 0 else 0,
                "total_cost": execution.total_cost_usd,
                "started_at": execution.started_at.isoformat(),
                "error": execution.error_message
            }
        
        return None


# Workflow execution helpers
async def create_execution_graph(workflow: BusinessWorkflow) -> Dict[str, Any]:
    """Create execution graph from workflow definition"""
    
    graph = {
        "nodes": [],
        "edges": []
    }
    
    # Add nodes for each step
    for step in workflow.steps:
        graph["nodes"].append({
            "id": step.step_id,
            "type": step.step_type.value,
            "agent": step.agent_name,
            "description": step.description
        })
    
    # Add edges based on dependencies
    for step in workflow.steps:
        for dep in step.dependencies:
            graph["edges"].append({
                "from": dep,
                "to": step.step_id
            })
    
    return graph


async def save_execution_state(
    execution: WorkflowExecution,
    storage_path: str = "/tmp/workflow_executions"
) -> str:
    """Save execution state to file"""
    
    import os
    os.makedirs(storage_path, exist_ok=True)
    
    file_path = os.path.join(storage_path, f"{execution.execution_id}.json")
    
    with open(file_path, 'w') as f:
        json.dump(execution.to_dict(), f, indent=2)
    
    logger.info(f"Execution state saved to {file_path}")
    return file_path


__all__ = [
    "GraphFlowRunner",
    "WorkflowExecution",
    "StepExecutionResult",
    "StepStatus",
    "create_execution_graph",
    "save_execution_state"
]