from abc import ABC, abstractmethod

from src.domain.entities import GoldenTestCase, MetricResult, Trajectory


class BaseEvaluator(ABC):
    """Abstract interface that all trajectory and outcome evaluators must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the evaluator metric (e.g. 'Faithfulness')."""
        pass

    @abstractmethod
    async def evaluate(self, test_case: GoldenTestCase, trajectory: Trajectory) -> MetricResult:
        """Evaluates the SUT trajectory against the GoldenTestCase criteria."""
        pass
