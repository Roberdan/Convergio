"""
AutoGen Bench Scenarios for Convergio
Comprehensive benchmark scenarios for CI/CD validation and performance testing
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
import structlog

from ..services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
from ..services.redis_state_manager import RedisStateManager
from services.unified_cost_tracker import unified_cost_tracker
from ..observability.otel_integration import initialize_otel
from ..services.observability.metrics_collector import get_metrics_collector
from ..utils.config import get_settings

logger = structlog.get_logger()


@dataclass
class ScenarioConfig:
    """Configuration for a benchmark scenario"""
    scenario_id: str
    name: str
    description: str
    category: str  # strategic, analytics, routing, workflow
    complexity: str  # low, medium, high
    expected_agents: List[str]
    max_turns: int
    timeout_seconds: int
    success_criteria: Dict[str, Any]
    test_messages: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScenarioResult:
    """Result of a benchmark scenario execution"""
    scenario_id: str
    scenario_name: str
    execution_id: str
    
    # Performance metrics
    start_time: datetime
    end_time: datetime
    duration_ms: int
    turns_taken: int
    agents_involved: List[str]
    
    # Token and cost metrics
    total_tokens: int
    total_cost_usd: float
    avg_tokens_per_turn: float
    
    # Quality metrics
    response_quality_score: float  # 0-1
    agent_selection_accuracy: float  # 0-1
    task_completion_rate: float  # 0-1
    
    # Success evaluation
    passed: bool
    failure_reason: Optional[str] = None
    
    # Detailed data
    conversation_transcript: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat()
        }


@dataclass
class BenchmarkReport:
    """Aggregate benchmark report for all scenarios"""
    report_id: str
    timestamp: datetime
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    
    # Aggregate metrics
    avg_duration_ms: float
    avg_turns: float
    avg_tokens: float
    avg_cost_usd: float
    total_cost_usd: float
    
    # Performance breakdown
    p50_duration_ms: int
    p95_duration_ms: int
    
    # Category performance
    category_results: Dict[str, Dict[str, Any]]
    
    # Individual results
    scenario_results: List[ScenarioResult]
    
    # CI/CD metadata
    commit_sha: Optional[str] = None
    branch_name: Optional[str] = None
    build_number: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp.isoformat(),
            "summary": {
                "total_scenarios": self.total_scenarios,
                "passed": self.passed_scenarios,
                "failed": self.failed_scenarios,
                "pass_rate": self.passed_scenarios / self.total_scenarios if self.total_scenarios > 0 else 0
            },
            "metrics": {
                "avg_duration_ms": self.avg_duration_ms,
                "p50_duration_ms": self.p50_duration_ms,
                "p95_duration_ms": self.p95_duration_ms,
                "avg_turns": self.avg_turns,
                "avg_tokens": self.avg_tokens,
                "avg_cost_usd": self.avg_cost_usd,
                "total_cost_usd": self.total_cost_usd
            },
            "category_results": self.category_results,
            "ci_metadata": {
                "commit_sha": self.commit_sha,
                "branch": self.branch_name,
                "build": self.build_number
            }
        }


class AutoGenBenchRunner:
    """Runner for AutoGen benchmark scenarios"""
    
    def __init__(self, orchestrator: Optional[ModernGroupChatOrchestrator] = None):
        self.orchestrator = orchestrator
        self.scenarios = self._load_scenarios()
        self.settings = get_settings()
        
    def _load_scenarios(self) -> List[ScenarioConfig]:
        """Load predefined benchmark scenarios"""
        scenarios = []
        
        # Scenario 1: Strategic Q&A
        scenarios.append(ScenarioConfig(
            scenario_id="strategic_qa_001",
            name="Strategic Planning Q&A",
            description="Test strategic planning conversation with multiple agents",
            category="strategic",
            complexity="medium",
            expected_agents=["ali_chief_of_staff", "domik_mckinsey_strategic_decision_maker"],
            max_turns=10,
            timeout_seconds=60,
            success_criteria={
                "min_agents": 2,
                "max_turns": 10,
                "required_keywords": ["strategy", "plan", "approach", "recommendation"]
            },
            test_messages=[
                "What should be our go-to-market strategy for the new AI product line?",
                "How do we differentiate from competitors?",
                "What are the key risks we should consider?"
            ]
        ))
        
        # Scenario 2: Analytics Synthesis
        scenarios.append(ScenarioConfig(
            scenario_id="analytics_synthesis_001",
            name="Performance Analytics Review",
            description="Test analytics and data synthesis capabilities",
            category="analytics",
            complexity="high",
            expected_agents=["diana_performance_dashboard", "amy_cfo"],
            max_turns=12,
            timeout_seconds=90,
            success_criteria={
                "min_agents": 2,
                "max_turns": 12,
                "required_keywords": ["metrics", "performance", "analysis", "trend", "insight"]
            },
            test_messages=[
                "Analyze our Q1 performance metrics and identify key trends",
                "What are the financial implications of these trends?",
                "Provide actionable recommendations based on the data"
            ]
        ))
        
        # Scenario 3: Routing Complexity
        scenarios.append(ScenarioConfig(
            scenario_id="routing_complex_001",
            name="Complex Multi-Agent Routing",
            description="Test complex routing requiring multiple specialist agents",
            category="routing",
            complexity="high",
            expected_agents=["ali_chief_of_staff", "luca_security_expert", "amy_cfo", "wanda_workflow_orchestrator"],
            max_turns=15,
            timeout_seconds=120,
            success_criteria={
                "min_agents": 4,
                "max_turns": 15,
                "agent_diversity": 0.6  # At least 60% of available agents
            },
            test_messages=[
                "We have a security breach that's affecting our financial systems and needs immediate workflow adjustments",
                "What's the impact assessment?",
                "How do we coordinate the response across teams?",
                "What's the recovery timeline and cost?"
            ]
        ))
        
        # Scenario 4: Workflow Execution
        scenarios.append(ScenarioConfig(
            scenario_id="workflow_exec_001",
            name="Product Launch Workflow",
            description="Test end-to-end workflow execution for product launch",
            category="workflow",
            complexity="high",
            expected_agents=["wanda_workflow_orchestrator", "ali_chief_of_staff", "amy_cfo"],
            max_turns=20,
            timeout_seconds=150,
            success_criteria={
                "min_agents": 3,
                "workflow_steps_completed": ["planning", "budgeting", "execution", "monitoring"],
                "max_cost_usd": 0.50
            },
            test_messages=[
                "Initialize product launch workflow for Q2",
                "Define launch milestones and dependencies",
                "Allocate budget and resources",
                "Set up monitoring and success metrics",
                "Execute launch sequence"
            ]
        ))
        
        # Scenario 5: Simple Query (Baseline)
        scenarios.append(ScenarioConfig(
            scenario_id="simple_query_001",
            name="Simple Information Query",
            description="Baseline test with simple query",
            category="baseline",
            complexity="low",
            expected_agents=["ali_chief_of_staff"],
            max_turns=3,
            timeout_seconds=30,
            success_criteria={
                "max_turns": 3,
                "max_duration_ms": 5000
            },
            test_messages=[
                "What's our current headcount?"
            ]
        ))
        
        # Scenario 6: Cost Optimization
        scenarios.append(ScenarioConfig(
            scenario_id="cost_optimization_001",
            name="Cost Optimization Analysis",
            description="Test cost-aware decision making",
            category="financial",
            complexity="medium",
            expected_agents=["amy_cfo", "diana_performance_dashboard"],
            max_turns=8,
            timeout_seconds=60,
            success_criteria={
                "min_agents": 2,
                "max_turns": 8,
                "max_cost_usd": 0.10,
                "required_keywords": ["cost", "savings", "optimization", "efficiency"]
            },
            test_messages=[
                "Identify our top 3 cost centers",
                "What optimization opportunities exist?",
                "Calculate potential savings"
            ]
        ))
        
        return scenarios
    
    async def run_scenario(
        self,
        scenario: ScenarioConfig,
        verbose: bool = False
    ) -> ScenarioResult:
        """Run a single benchmark scenario"""
        
        execution_id = f"{scenario.scenario_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()
        start_ms = time.time() * 1000
        
        logger.info(f"🎯 Running scenario: {scenario.name}", scenario_id=scenario.scenario_id)
        
        try:
            # Initialize result
            result = ScenarioResult(
                scenario_id=scenario.scenario_id,
                scenario_name=scenario.name,
                execution_id=execution_id,
                start_time=start_time,
                end_time=start_time,
                duration_ms=0,
                turns_taken=0,
                agents_involved=[],
                total_tokens=0,
                total_cost_usd=0.0,
                avg_tokens_per_turn=0.0,
                response_quality_score=0.0,
                agent_selection_accuracy=0.0,
                task_completion_rate=0.0,
                passed=False
            )
            
            if not self.orchestrator:
                result.failure_reason = "No orchestrator available"
                return result
            
            # Run conversation for each test message
            all_agents = set()
            total_turns = 0
            total_tokens = 0
            total_cost = 0.0
            conversation_transcript = []
            
            for i, message in enumerate(scenario.test_messages):
                if verbose:
                    logger.info(f"  Message {i+1}: {message[:50]}...")
                
                # Run with timeout
                try:
                    response = await asyncio.wait_for(
                        self.orchestrator.orchestrate_conversation(
                            message=message,
                            user_id=f"bench_user_{scenario.scenario_id}",
                            conversation_id=execution_id,
                            context={"benchmark": True, "scenario": scenario.scenario_id}
                        ),
                        timeout=scenario.timeout_seconds / len(scenario.test_messages)
                    )
                    
                    # Collect metrics
                    all_agents.update(response.agents_used)
                    total_turns += response.turn_count
                    total_tokens += response.cost_breakdown.get("estimated_tokens", 0)
                    total_cost += response.cost_breakdown.get("total_cost_usd", 0)
                    
                    # Record transcript
                    conversation_transcript.append({
                        "message": message,
                        "response": response.response[:500],  # Truncate for storage
                        "agents": response.agents_used,
                        "turns": response.turn_count
                    })
                    
                except asyncio.TimeoutError:
                    result.failure_reason = f"Timeout at message {i+1}"
                    break
            
            # Calculate final metrics
            end_time = datetime.utcnow()
            duration_ms = int((time.time() * 1000) - start_ms)
            
            result.end_time = end_time
            result.duration_ms = duration_ms
            result.turns_taken = total_turns
            result.agents_involved = list(all_agents)
            result.total_tokens = total_tokens
            result.total_cost_usd = total_cost
            result.avg_tokens_per_turn = total_tokens / total_turns if total_turns > 0 else 0
            result.conversation_transcript = conversation_transcript
            
            # Evaluate success criteria
            passed, scores = self._evaluate_success(scenario, result)
            result.passed = passed
            result.response_quality_score = scores.get("quality", 0.0)
            result.agent_selection_accuracy = scores.get("selection", 0.0)
            result.task_completion_rate = scores.get("completion", 0.0)
            
            if not passed and not result.failure_reason:
                result.failure_reason = "Failed success criteria evaluation"
            
            # Record OTEL metrics
            metrics_collector = get_metrics_collector()
            if metrics_collector:
                metrics_collector.record_conversation_metrics(
                    conversation_id=execution_id,
                    user_id=f"bench_{scenario.scenario_id}",
                    agent_count=len(all_agents),
                    duration_ms=duration_ms,
                    tokens_used=total_tokens,
                    cost_usd=total_cost,
                    success=passed
                )
            
            logger.info(
                "✅ Scenario completed",
                scenario_id=scenario.scenario_id,
                passed=passed,
                duration_ms=duration_ms,
                turns=total_turns,
                agents=len(all_agents)
            )
            
        except Exception as e:
            logger.error(f"Scenario failed with error: {e}", scenario_id=scenario.scenario_id)
            result.failure_reason = str(e)
            result.passed = False
        
        return result
    
    def _evaluate_success(
        self,
        scenario: ScenarioConfig,
        result: ScenarioResult
    ) -> Tuple[bool, Dict[str, float]]:
        """Evaluate if scenario met success criteria"""
        
        criteria = scenario.success_criteria
        scores = {"quality": 0.0, "selection": 0.0, "completion": 0.0}
        checks = []
        
        # Check turn limits
        if "max_turns" in criteria:
            checks.append(result.turns_taken <= criteria["max_turns"])
            scores["completion"] += 0.5 if result.turns_taken <= criteria["max_turns"] else 0
        
        # Check agent involvement
        if "min_agents" in criteria:
            checks.append(len(result.agents_involved) >= criteria["min_agents"])
            scores["selection"] += 0.5 if len(result.agents_involved) >= criteria["min_agents"] else 0
        
        # Check expected agents
        expected_agents = set(scenario.expected_agents)
        actual_agents = set(result.agents_involved)
        agent_overlap = len(expected_agents.intersection(actual_agents)) / len(expected_agents) if expected_agents else 1
        scores["selection"] += agent_overlap * 0.5
        
        # Check keywords in responses
        if "required_keywords" in criteria:
            all_text = " ".join([t["response"] for t in result.conversation_transcript])
            keywords_found = sum(1 for kw in criteria["required_keywords"] if kw.lower() in all_text.lower())
            keyword_ratio = keywords_found / len(criteria["required_keywords"])
            checks.append(keyword_ratio >= 0.5)
            scores["quality"] = keyword_ratio
        
        # Check cost limit
        if "max_cost_usd" in criteria:
            checks.append(result.total_cost_usd <= criteria["max_cost_usd"])
        
        # Check duration
        if "max_duration_ms" in criteria:
            checks.append(result.duration_ms <= criteria["max_duration_ms"])
        
        # Overall pass/fail
        passed = all(checks) if checks else True
        
        # Calculate task completion rate
        scores["completion"] = sum(checks) / len(checks) if checks else 1.0
        
        return passed, scores
    
    async def run_all_scenarios(
        self,
        categories: Optional[List[str]] = None,
        verbose: bool = False
    ) -> BenchmarkReport:
        """Run all benchmark scenarios"""
        
        report_id = f"bench_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Filter scenarios by category if specified
        scenarios_to_run = self.scenarios
        if categories:
            scenarios_to_run = [s for s in self.scenarios if s.category in categories]
        
        logger.info(f"🚀 Starting AutoGen Bench with {len(scenarios_to_run)} scenarios")
        
        results = []
        for scenario in scenarios_to_run:
            result = await self.run_scenario(scenario, verbose=verbose)
            results.append(result)
            
            # Small delay between scenarios
            await asyncio.sleep(2)
        
        # Generate report
        report = self._generate_report(report_id, results)
        
        logger.info(
            "📊 Benchmark complete",
            total=report.total_scenarios,
            passed=report.passed_scenarios,
            failed=report.failed_scenarios
        )
        
        return report
    
    def _generate_report(
        self,
        report_id: str,
        results: List[ScenarioResult]
    ) -> BenchmarkReport:
        """Generate benchmark report from results"""
        
        # Calculate aggregates
        total_scenarios = len(results)
        passed_scenarios = sum(1 for r in results if r.passed)
        failed_scenarios = total_scenarios - passed_scenarios
        
        # Performance metrics
        durations = [r.duration_ms for r in results]
        durations.sort()
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        p50_duration = durations[len(durations) // 2] if durations else 0
        p95_duration = durations[int(len(durations) * 0.95)] if durations else 0
        
        avg_turns = sum(r.turns_taken for r in results) / len(results) if results else 0
        avg_tokens = sum(r.total_tokens for r in results) / len(results) if results else 0
        avg_cost = sum(r.total_cost_usd for r in results) / len(results) if results else 0
        total_cost = sum(r.total_cost_usd for r in results)
        
        # Category breakdown
        category_results = {}
        for category in set(s.category for s in self.scenarios):
            cat_results = [r for r in results if any(
                s.scenario_id == r.scenario_id and s.category == category 
                for s in self.scenarios
            )]
            
            if cat_results:
                category_results[category] = {
                    "total": len(cat_results),
                    "passed": sum(1 for r in cat_results if r.passed),
                    "avg_duration_ms": sum(r.duration_ms for r in cat_results) / len(cat_results),
                    "avg_turns": sum(r.turns_taken for r in cat_results) / len(cat_results),
                    "avg_quality_score": sum(r.response_quality_score for r in cat_results) / len(cat_results)
                }
        
        # Get CI/CD metadata from environment
        commit_sha = os.getenv("GITHUB_SHA", os.getenv("CI_COMMIT_SHA"))
        branch_name = os.getenv("GITHUB_REF_NAME", os.getenv("CI_COMMIT_BRANCH"))
        build_number = os.getenv("GITHUB_RUN_NUMBER", os.getenv("CI_PIPELINE_ID"))
        
        return BenchmarkReport(
            report_id=report_id,
            timestamp=datetime.utcnow(),
            total_scenarios=total_scenarios,
            passed_scenarios=passed_scenarios,
            failed_scenarios=failed_scenarios,
            avg_duration_ms=avg_duration,
            avg_turns=avg_turns,
            avg_tokens=avg_tokens,
            avg_cost_usd=avg_cost,
            total_cost_usd=total_cost,
            p50_duration_ms=p50_duration,
            p95_duration_ms=p95_duration,
            category_results=category_results,
            scenario_results=results,
            commit_sha=commit_sha,
            branch_name=branch_name,
            build_number=build_number
        )
    
    async def save_report(
        self,
        report: BenchmarkReport,
        output_dir: str = "benchmark_artifacts"
    ) -> str:
        """Save benchmark report as CI artifact"""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        
        # Save detailed report
        report_file = output_path / f"{report.report_id}.json"
        with open(report_file, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        
        # Save summary for CI
        summary_file = output_path / "benchmark_summary.json"
        summary = {
            "report_id": report.report_id,
            "timestamp": report.timestamp.isoformat(),
            "pass_rate": report.passed_scenarios / report.total_scenarios if report.total_scenarios > 0 else 0,
            "avg_duration_ms": report.avg_duration_ms,
            "total_cost_usd": report.total_cost_usd,
            "passed": report.passed_scenarios,
            "failed": report.failed_scenarios,
            "commit": report.commit_sha,
            "branch": report.branch_name
        }
        
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        # Save as latest for easy access
        latest_file = output_path / "benchmark_latest.json"
        with open(latest_file, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        
        logger.info(f"💾 Benchmark report saved to {report_file}")
        
        return str(report_file)


async def main():
    """Run AutoGen benchmark suite"""
    
    import os
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = os.getenv("OTEL_ENDPOINT", "localhost:4317")
    
    # Initialize OTEL
    initialize_otel(
        service_name="convergio-bench",
        enable_console=False,
        enable_prometheus=True
    )
    
    # Initialize orchestrator
    settings = get_settings()
    state_manager = RedisStateManager(settings.REDIS_URL)
    cost_tracker = unified_cost_tracker
    
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker
    )
    
    await orchestrator.initialize()
    
    # Create benchmark runner
    runner = AutoGenBenchRunner(orchestrator)
    
    # Run all scenarios
    report = await runner.run_all_scenarios(verbose=True)
    
    # Save report
    await runner.save_report(report)
    
    # Print summary
    print("\n" + "="*60)
    print("AUTOGEN BENCH RESULTS")
    print("="*60)
    print(f"Report ID: {report.report_id}")
    print(f"Total Scenarios: {report.total_scenarios}")
    print(f"Passed: {report.passed_scenarios}")
    print(f"Failed: {report.failed_scenarios}")
    print(f"Pass Rate: {report.passed_scenarios/report.total_scenarios*100:.1f}%")
    print("\nPerformance Metrics:")
    print(f"  Avg Duration: {report.avg_duration_ms:.0f}ms")
    print(f"  P50 Duration: {report.p50_duration_ms}ms")
    print(f"  P95 Duration: {report.p95_duration_ms}ms")
    print(f"  Avg Turns: {report.avg_turns:.1f}")
    print(f"  Avg Tokens: {report.avg_tokens:.0f}")
    print(f"  Total Cost: ${report.total_cost_usd:.4f}")
    print("\nCategory Performance:")
    for category, metrics in report.category_results.items():
        print(f"  {category}: {metrics['passed']}/{metrics['total']} passed")
    print("="*60)
    
    # Return exit code for CI
    return 0 if report.failed_scenarios == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))