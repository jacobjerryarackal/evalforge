import pytest

from src.domain.entities import GoldenTestCase, MetricResult, Trajectory
from src.domain.interfaces.evaluator import BaseEvaluator
from src.use_cases.metrics.registry import MetricRegistry, create_default_registry


class MockEvaluator(BaseEvaluator):

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def evaluate(self, test_case: GoldenTestCase, trajectory: Trajectory) -> MetricResult:
        return MetricResult(metric_name=self.name, score=1.0)


def test_metric_registry_register_and_get():
    registry = MetricRegistry()
    eval1 = MockEvaluator("TestMetric1")
    eval2 = MockEvaluator("TestMetric2")

    registry.register(eval1)
    registry.register(eval2)

    assert registry.get("TestMetric1") is eval1
    assert registry.get("TestMetric2") is eval2
    assert set(registry.list_evaluators()) == {"TestMetric1", "TestMetric2"}
    assert set(registry.get_all()) == {eval1, eval2}


def test_metric_registry_duplicate_validation():
    registry = MetricRegistry()
    eval1 = MockEvaluator("DuplicateMetric")
    eval2 = MockEvaluator("DuplicateMetric")

    registry.register(eval1)
    with pytest.raises(ValueError) as exc_info:
        registry.register(eval2)

    assert "already registered" in str(exc_info.value)


def test_metric_registry_not_found():
    registry = MetricRegistry()
    with pytest.raises(ValueError) as exc_info:
        registry.get("NonExistent")

    assert "not registered" in str(exc_info.value)


def test_create_default_registry():
    registry = create_default_registry()
    evaluators = registry.list_evaluators()

    expected_evaluators = {
        "Latency",
        "TokenUsage",
        "Cost",
        "ToolCalling",
        "ContextPrecision",
        "ContextRecall",
    }
    assert set(evaluators) == expected_evaluators
