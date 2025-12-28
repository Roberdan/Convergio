"""
Decision Engine
Generates a deterministic DecisionPlan for each user message to guide AutoGen orchestration.

Keeps logic simple, explainable, and safe-by-default. Honors feature flag in settings.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import time
import structlog

from agents.utils.config import get_settings
from agents.tools.smart_tool_selector import SmartToolSelector


logger = structlog.get_logger()


@dataclass
class DecisionPlan:
    sources: List[str]          # e.g., ["backend", "vector", "web", "llm"]
    tools: List[str]            # e.g., ["web_search", "vector_search", "database_query"]
    model: str                  # model id
    max_turns: int              # groupchat turns
    budget_usd: float           # hard budget for this run
    rationale: str              # short human-readable reason
    metadata: Dict[str, Any]    # extra scores/classifications


class DecisionEngine:
    """Compute a DecisionPlan based on message and context."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def plan(self, message: str, context: Optional[Dict[str, Any]] = None) -> DecisionPlan:
        start = time.time()

        # Analyze message using existing SmartToolSelector (regex + heuristics)
        analysis = SmartToolSelector.analyze_query(message)

        sources: List[str] = []
        tools: List[str] = []

        # Source selection in priority order
        if "database_query" in analysis.get("suggested_tools", []):
            sources.append("backend")
            tools.append("database_query")

        if "vector_search" in analysis.get("suggested_tools", []):
            sources.append("vector")
            tools.append("vector_search")

        if analysis.get("needs_web_search"):
            sources.append("web")
            tools.append("web_search")

        # Always allow LLM reasoning as last step
        sources.append("llm")

        # Model and turns from settings
        model = self.settings.default_ai_model
        max_turns = max(1, int(self.settings.autogen_max_turns))

        # Budget: use a fraction per conversation of total limit
        total_limit = float(self.settings.autogen_cost_limit_usd)
        budget = max(0.5, round(min(total_limit * 0.1, total_limit), 2))

        # Rationale
        rationale = analysis.get("reason", "Default policy")

        metadata = {
            "analysis": analysis,
            "environment": self.settings.environment,
        }

        plan = DecisionPlan(
            sources=sources,
            tools=list(dict.fromkeys(tools)),  # de-dup while preserving order
            model=model,
            max_turns=max_turns,
            budget_usd=budget,
            rationale=rationale,
            metadata=metadata,
        )

        # Telemetry event
        logger.info(
            "decision_made",
            sources=plan.sources,
            tools=plan.tools,
            model=plan.model,
            max_turns=plan.max_turns,
            budget_usd=plan.budget_usd,
            rationale=plan.rationale,
            took_ms=int((time.time() - start) * 1000),
        )

        return plan


