import logging
from typing import Dict, List

from src.domain.interfaces.evaluator import BaseEvaluator

logger = logging.getLogger("evaluation.metrics.registry")


class MetricRegistry:
    """Registry for discovery, registration, and validation of metric evaluators."""

    def __init__(self) -> None:
        self._evaluators: Dict[str, BaseEvaluator] = {}

    def register(self, evaluator: BaseEvaluator) -> None:
        """Registers an evaluator. Raises ValueError if name is a duplicate."""
        name = evaluator.name
        if name in self._evaluators:
            raise ValueError(f"Evaluator with name '{name}' is already registered.")
        self._evaluators[name] = evaluator
        logger.info(f"Registered evaluator: {name}")

    def get(self, name: str) -> BaseEvaluator:
        """Retrieves an evaluator by its unique name."""
        if name not in self._evaluators:
            raise ValueError(f"Evaluator '{name}' is not registered.")
        return self._evaluators[name]

    def list_evaluators(self) -> List[str]:
        """Returns the list of all registered evaluator names."""
        return list(self._evaluators.keys())

    def get_all(self) -> List[BaseEvaluator]:
        """Returns all registered evaluator instances."""
        return list(self._evaluators.values())


def create_default_registry() -> MetricRegistry:
    """Helper to instantiate a registry prepopulated with standard evaluators."""
    from src.use_cases.metrics.evaluators import (
        ContextPrecisionEvaluator,
        ContextRecallEvaluator,
        CostEvaluator,
        LatencyEvaluator,
        TokenUsageEvaluator,
        ToolCallingEvaluator,
    )

    registry = MetricRegistry()
    registry.register(LatencyEvaluator())
    registry.register(TokenUsageEvaluator())
    registry.register(CostEvaluator())
    registry.register(ToolCallingEvaluator())
    registry.register(ContextPrecisionEvaluator())
    registry.register(ContextRecallEvaluator())
    return registry
