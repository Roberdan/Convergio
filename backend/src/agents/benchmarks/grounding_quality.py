"""
Grounding Quality Measurement Benchmark
Measures the quality improvement from RAG context injection
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
import structlog
from pathlib import Path

from ..services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
from ..services.redis_state_manager import RedisStateManager
from ..services.unified_cost_tracker import unified_cost_tracker
from ..utils.config import get_settings
from ..utils.feature_flags import FeatureFlagName, get_feature_flags

logger = structlog.get_logger()


@dataclass
class BenchmarkTask:
    """A single benchmark task with ground truth"""
    task_id: str
    category: str  # strategic, analytics, routing
    question: str
    context_needed: List[str]  # Key facts needed for correct answer
    expected_answer_keywords: List[str]  # Keywords that should appear
    expected_reasoning: str  # Expected reasoning pattern
    difficulty: str  # easy, medium, hard
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run"""
    task_id: str
    category: str
    rag_enabled: bool
    response: str
    keywords_found: List[str]
    keywords_missing: List[str]
    relevance_score: float  # 0-1 score
    grounding_score: float  # 0-1 score based on context usage
    latency_ms: int
    tokens_used: int
    cost_usd: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkReport:
    """Aggregate benchmark report"""
    timestamp: str
    total_tasks: int
    rag_enabled_results: List[BenchmarkResult]
    rag_disabled_results: List[BenchmarkResult]
    
    # Aggregate metrics
    avg_relevance_with_rag: float
    avg_relevance_without_rag: float
    avg_grounding_with_rag: float
    avg_grounding_without_rag: float
    
    # Performance metrics
    avg_latency_with_rag_ms: float
    avg_latency_without_rag_ms: float
    avg_cost_with_rag_usd: float
    avg_cost_without_rag_usd: float
    
    # Quality lift
    relevance_lift_percentage: float
    grounding_lift_percentage: float
    
    # Category breakdown
    category_performance: Dict[str, Dict[str, float]]
    
    # Pass/fail based on threshold
    passed: bool
    threshold: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_tasks": self.total_tasks,
            "aggregate_metrics": {
                "avg_relevance_with_rag": self.avg_relevance_with_rag,
                "avg_relevance_without_rag": self.avg_relevance_without_rag,
                "avg_grounding_with_rag": self.avg_grounding_with_rag,
                "avg_grounding_without_rag": self.avg_grounding_without_rag,
                "relevance_lift_percentage": self.relevance_lift_percentage,
                "grounding_lift_percentage": self.grounding_lift_percentage
            },
            "performance_metrics": {
                "avg_latency_with_rag_ms": self.avg_latency_with_rag_ms,
                "avg_latency_without_rag_ms": self.avg_latency_without_rag_ms,
                "avg_cost_with_rag_usd": self.avg_cost_with_rag_usd,
                "avg_cost_without_rag_usd": self.avg_cost_without_rag_usd
            },
            "category_performance": self.category_performance,
            "passed": self.passed,
            "threshold": self.threshold
        }


class GroundingQualityBenchmark:
    """Benchmark harness for measuring RAG grounding quality"""
    
    def __init__(
        self,
        orchestrator: Optional[ModernGroupChatOrchestrator] = None,
        threshold: float = 0.15  # 15% minimum lift required
    ):
        self.orchestrator = orchestrator
        self.threshold = threshold
        self.benchmark_tasks = self._load_benchmark_tasks()
        self.settings = get_settings()
        self.flag_manager = get_feature_flags()
        
    def _load_benchmark_tasks(self) -> List[BenchmarkTask]:
        """Load predefined benchmark tasks"""
        tasks = []
        
        # Strategic Q&A tasks
        tasks.append(BenchmarkTask(
            task_id="strategic_001",
            category="strategic",
            question="What should be our market entry strategy for the European market considering our current resources?",
            context_needed=[
                "Current market presence in 3 US regions",
                "Budget allocation of $5M for expansion",
                "Team of 50 sales professionals",
                "Product localization completed for Germany and France"
            ],
            expected_answer_keywords=["phased", "Germany", "France", "localization", "budget", "team"],
            expected_reasoning="Should suggest phased approach starting with Germany/France where localization exists",
            difficulty="medium"
        ))
        
        tasks.append(BenchmarkTask(
            task_id="strategic_002",
            category="strategic",
            question="How should we prioritize our product roadmap given customer feedback and competitive pressures?",
            context_needed=[
                "Top customer request: API improvements (40% of feedback)",
                "Competitor launched AI features last quarter",
                "Current tech debt: 30% of codebase needs refactoring",
                "Engineering capacity: 20 developers"
            ],
            expected_answer_keywords=["API", "AI", "tech debt", "prioritization", "customer", "competitive"],
            expected_reasoning="Balance customer needs (API) with competitive catch-up (AI) while managing tech debt",
            difficulty="hard"
        ))
        
        # Analytics synthesis tasks
        tasks.append(BenchmarkTask(
            task_id="analytics_001",
            category="analytics",
            question="What are the key insights from our Q1 performance metrics?",
            context_needed=[
                "Revenue grew 15% QoQ to $12M",
                "Customer churn increased from 5% to 8%",
                "NPS score dropped from 45 to 38",
                "New customer acquisition cost increased 20%"
            ],
            expected_answer_keywords=["revenue", "growth", "churn", "NPS", "acquisition", "concern"],
            expected_reasoning="Highlight revenue growth but flag concerning trends in churn and satisfaction",
            difficulty="easy"
        ))
        
        tasks.append(BenchmarkTask(
            task_id="analytics_002",
            category="analytics",
            question="Analyze the correlation between our marketing spend and customer acquisition metrics.",
            context_needed=[
                "Marketing spend increased 50% to $2M in Q1",
                "Customer acquisition grew 30% to 1000 new customers",
                "CAC increased from $1500 to $2000",
                "Channel breakdown: 60% digital, 40% traditional"
            ],
            expected_answer_keywords=["correlation", "efficiency", "CAC", "channels", "ROI", "optimization"],
            expected_reasoning="Identify declining efficiency (CAC increase) despite higher spend, suggest channel optimization",
            difficulty="medium"
        ))
        
        # Routing complexity tasks
        tasks.append(BenchmarkTask(
            task_id="routing_001",
            category="routing",
            question="Which team should handle the customer complaint about billing and technical issues?",
            context_needed=[
                "Customer tier: Enterprise",
                "Issue: Billing discrepancy of $10K",
                "Secondary issue: API performance degradation",
                "Customer health score: At risk"
            ],
            expected_answer_keywords=["escalation", "account manager", "finance", "engineering", "priority"],
            expected_reasoning="Route to account manager for coordination, involve finance and engineering teams",
            difficulty="easy"
        ))
        
        tasks.append(BenchmarkTask(
            task_id="routing_002",
            category="routing",
            question="How should we coordinate the response to a security incident affecting multiple customers?",
            context_needed=[
                "Severity: High - data exposure risk",
                "Affected customers: 50 enterprise accounts",
                "Time since detection: 2 hours",
                "Compliance requirements: GDPR, SOC2"
            ],
            expected_answer_keywords=["incident", "security", "legal", "communications", "coordination", "GDPR"],
            expected_reasoning="Immediate security team lead, legal for compliance, communications for customer notice",
            difficulty="hard"
        ))
        
        return tasks
    
    async def run_single_task(
        self,
        task: BenchmarkTask,
        rag_enabled: bool
    ) -> BenchmarkResult:
        """Run a single benchmark task"""
        start_time = datetime.utcnow()
        
        try:
            # Configure RAG setting
            self.flag_manager.update_flag(
                FeatureFlagName.RAG_IN_LOOP,
                enabled=rag_enabled
            )
            
            # If RAG is enabled, inject context into memory system
            if rag_enabled and self.orchestrator and self.orchestrator.memory_system:
                for fact in task.context_needed:
                    await self.orchestrator.memory_system.store_conversation(
                        user_id="benchmark_user",
                        agent_id="benchmark",
                        content=fact,
                        metadata={"type": "benchmark_context", "task_id": task.task_id}
                    )
            
            # Run the task through orchestrator
            if self.orchestrator:
                result = await self.orchestrator.orchestrate_conversation(
                    message=task.question,
                    user_id="benchmark_user",
                    conversation_id=f"benchmark_{task.task_id}_{rag_enabled}",
                    context={"benchmark": True, "task_id": task.task_id}
                )
                response = result.response
                cost = result.cost_breakdown.get("total_cost_usd", 0.0)
                tokens = result.cost_breakdown.get("estimated_tokens", 0)
            else:
                # Simulate response for testing
                response = f"Simulated response for {task.task_id}"
                cost = 0.01
                tokens = 100
            
            # Calculate scores
            keywords_found = [kw for kw in task.expected_answer_keywords if kw.lower() in response.lower()]
            keywords_missing = [kw for kw in task.expected_answer_keywords if kw.lower() not in response.lower()]
            
            relevance_score = len(keywords_found) / len(task.expected_answer_keywords) if task.expected_answer_keywords else 0
            
            # Grounding score: how well the response uses the provided context
            context_references = sum(1 for fact in task.context_needed if any(
                word in response.lower() for word in fact.lower().split()[:3]
            ))
            grounding_score = context_references / len(task.context_needed) if task.context_needed else 0
            
            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return BenchmarkResult(
                task_id=task.task_id,
                category=task.category,
                rag_enabled=rag_enabled,
                response=response,
                keywords_found=keywords_found,
                keywords_missing=keywords_missing,
                relevance_score=relevance_score,
                grounding_score=grounding_score,
                latency_ms=latency_ms,
                tokens_used=tokens,
                cost_usd=cost,
                metadata={"difficulty": task.difficulty}
            )
            
        except Exception as e:
            logger.error(f"Failed to run benchmark task {task.task_id}", error=str(e))
            return BenchmarkResult(
                task_id=task.task_id,
                category=task.category,
                rag_enabled=rag_enabled,
                response=f"Error: {str(e)}",
                keywords_found=[],
                keywords_missing=task.expected_answer_keywords,
                relevance_score=0.0,
                grounding_score=0.0,
                latency_ms=0,
                tokens_used=0,
                cost_usd=0.0,
                metadata={"error": str(e)}
            )
        finally:
            # Clean up benchmark context
            if rag_enabled and self.orchestrator and self.orchestrator.memory_system:
                # In production, would implement cleanup method
                pass
    
    async def run_benchmark(
        self,
        tasks: Optional[List[BenchmarkTask]] = None,
        categories: Optional[List[str]] = None
    ) -> BenchmarkReport:
        """Run full benchmark suite"""
        
        if tasks is None:
            tasks = self.benchmark_tasks
        
        if categories:
            tasks = [t for t in tasks if t.category in categories]
        
        logger.info(f"🎯 Starting grounding quality benchmark with {len(tasks)} tasks")
        
        rag_enabled_results = []
        rag_disabled_results = []
        
        # Run each task with RAG enabled and disabled
        for task in tasks:
            logger.info(f"Running task {task.task_id} with RAG enabled")
            rag_enabled_result = await self.run_single_task(task, rag_enabled=True)
            rag_enabled_results.append(rag_enabled_result)
            
            logger.info(f"Running task {task.task_id} with RAG disabled")
            rag_disabled_result = await self.run_single_task(task, rag_enabled=False)
            rag_disabled_results.append(rag_disabled_result)
            
            # Small delay between tasks
            await asyncio.sleep(1)
        
        # Calculate aggregate metrics
        report = self._generate_report(
            rag_enabled_results,
            rag_disabled_results,
            len(tasks)
        )
        
        logger.info(
            f"✅ Benchmark complete. Grounding lift: {report.grounding_lift_percentage:.1f}%, "
            f"Relevance lift: {report.relevance_lift_percentage:.1f}%"
        )
        
        return report
    
    def _generate_report(
        self,
        rag_enabled_results: List[BenchmarkResult],
        rag_disabled_results: List[BenchmarkResult],
        total_tasks: int
    ) -> BenchmarkReport:
        """Generate benchmark report from results"""
        
        # Calculate averages
        avg_relevance_with_rag = sum(r.relevance_score for r in rag_enabled_results) / len(rag_enabled_results) if rag_enabled_results else 0
        avg_relevance_without_rag = sum(r.relevance_score for r in rag_disabled_results) / len(rag_disabled_results) if rag_disabled_results else 0
        
        avg_grounding_with_rag = sum(r.grounding_score for r in rag_enabled_results) / len(rag_enabled_results) if rag_enabled_results else 0
        avg_grounding_without_rag = sum(r.grounding_score for r in rag_disabled_results) / len(rag_disabled_results) if rag_disabled_results else 0
        
        avg_latency_with_rag_ms = sum(r.latency_ms for r in rag_enabled_results) / len(rag_enabled_results) if rag_enabled_results else 0
        avg_latency_without_rag_ms = sum(r.latency_ms for r in rag_disabled_results) / len(rag_disabled_results) if rag_disabled_results else 0
        
        avg_cost_with_rag_usd = sum(r.cost_usd for r in rag_enabled_results) / len(rag_enabled_results) if rag_enabled_results else 0
        avg_cost_without_rag_usd = sum(r.cost_usd for r in rag_disabled_results) / len(rag_disabled_results) if rag_disabled_results else 0
        
        # Calculate lift percentages
        relevance_lift_percentage = ((avg_relevance_with_rag - avg_relevance_without_rag) / avg_relevance_without_rag * 100) if avg_relevance_without_rag > 0 else 0
        grounding_lift_percentage = ((avg_grounding_with_rag - avg_grounding_without_rag) / avg_grounding_without_rag * 100) if avg_grounding_without_rag > 0 else 0
        
        # Category breakdown
        category_performance = {}
        for category in set(r.category for r in rag_enabled_results):
            cat_rag_enabled = [r for r in rag_enabled_results if r.category == category]
            cat_rag_disabled = [r for r in rag_disabled_results if r.category == category]
            
            category_performance[category] = {
                "avg_grounding_with_rag": sum(r.grounding_score for r in cat_rag_enabled) / len(cat_rag_enabled) if cat_rag_enabled else 0,
                "avg_grounding_without_rag": sum(r.grounding_score for r in cat_rag_disabled) / len(cat_rag_disabled) if cat_rag_disabled else 0,
                "grounding_lift_percentage": 0
            }
            
            if category_performance[category]["avg_grounding_without_rag"] > 0:
                category_performance[category]["grounding_lift_percentage"] = (
                    (category_performance[category]["avg_grounding_with_rag"] - 
                     category_performance[category]["avg_grounding_without_rag"]) / 
                    category_performance[category]["avg_grounding_without_rag"] * 100
                )
        
        # Check if benchmark passed
        passed = grounding_lift_percentage >= (self.threshold * 100)
        
        return BenchmarkReport(
            timestamp=datetime.utcnow().isoformat(),
            total_tasks=total_tasks,
            rag_enabled_results=rag_enabled_results,
            rag_disabled_results=rag_disabled_results,
            avg_relevance_with_rag=avg_relevance_with_rag,
            avg_relevance_without_rag=avg_relevance_without_rag,
            avg_grounding_with_rag=avg_grounding_with_rag,
            avg_grounding_without_rag=avg_grounding_without_rag,
            avg_latency_with_rag_ms=avg_latency_with_rag_ms,
            avg_latency_without_rag_ms=avg_latency_without_rag_ms,
            avg_cost_with_rag_usd=avg_cost_with_rag_usd,
            avg_cost_without_rag_usd=avg_cost_without_rag_usd,
            relevance_lift_percentage=relevance_lift_percentage,
            grounding_lift_percentage=grounding_lift_percentage,
            category_performance=category_performance,
            passed=passed,
            threshold=self.threshold
        )
    
    async def save_report(self, report: BenchmarkReport, output_dir: str = "benchmark_reports"):
        """Save benchmark report to file"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = output_path / f"grounding_benchmark_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        
        logger.info(f"💾 Benchmark report saved to {filename}")
        
        # Also save as latest for CI
        latest_filename = output_path / "grounding_benchmark_latest.json"
        with open(latest_filename, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        
        return filename


async def main():
    """Run grounding quality benchmark"""
    
    # Initialize components
    settings = get_settings()
    state_manager = RedisStateManager(settings.REDIS_URL)

    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=unified_cost_tracker
    )
    
    await orchestrator.initialize()
    
    # Create benchmark
    benchmark = GroundingQualityBenchmark(
        orchestrator=orchestrator,
        threshold=0.15  # Require 15% improvement
    )
    
    # Run benchmark
    report = await benchmark.run_benchmark()
    
    # Save report
    await benchmark.save_report(report)
    
    # Print summary
    print("\n" + "="*60)
    print("GROUNDING QUALITY BENCHMARK RESULTS")
    print("="*60)
    print(f"Total Tasks: {report.total_tasks}")
    print("\nGrounding Scores:")
    print(f"  With RAG:    {report.avg_grounding_with_rag:.2%}")
    print(f"  Without RAG: {report.avg_grounding_without_rag:.2%}")
    print(f"  Lift:        {report.grounding_lift_percentage:+.1f}%")
    print("\nRelevance Scores:")
    print(f"  With RAG:    {report.avg_relevance_with_rag:.2%}")
    print(f"  Without RAG: {report.avg_relevance_without_rag:.2%}")
    print(f"  Lift:        {report.relevance_lift_percentage:+.1f}%")
    print("\nPerformance Impact:")
    print(f"  Latency increase: {report.avg_latency_with_rag_ms - report.avg_latency_without_rag_ms:.0f}ms")
    print(f"  Cost increase:    ${report.avg_cost_with_rag_usd - report.avg_cost_without_rag_usd:.4f}")
    print("\nCategory Performance:")
    for category, perf in report.category_performance.items():
        print(f"  {category}: {perf['grounding_lift_percentage']:+.1f}% lift")
    print(f"\nBenchmark {'PASSED ✅' if report.passed else 'FAILED ❌'}")
    print(f"Required threshold: {report.threshold*100:.0f}% lift")
    print("="*60)
    
    return report


if __name__ == "__main__":
    asyncio.run(main())