import pytest

from src.adapters.repositories import InMemoryEvaluationRepository
from src.domain.entities import (
    BenchmarkConfig,
    GoldenDataset,
    GoldenTestCase,
    MetricResult,
    RetryPolicy,
    Step,
    Trajectory,
)
from src.domain.interfaces import AgentSUT, BaseEvaluator
from src.domain.value_objects import Cost, Latency, TokenUsage
from src.use_cases.metrics.registry import MetricRegistry
from src.use_cases.runners.benchmark_runner import BenchmarkRunner


class FlakyTravelAgentSUT(AgentSUT):
    """Mock agent SUT that fails a specified number of times before succeeding."""

    def __init__(self, failures_before_success: int, version: str = "v-flaky") -> None:
        self.failures_before_success = failures_before_success
        self.version_str = version
        self.call_count = 0

    @property
    def version(self) -> str:
        return self.version_str

    async def run(self, input_query: str) -> Trajectory:
        self.call_count += 1
        if self.call_count <= self.failures_before_success:
            raise RuntimeError(f"Simulated failure {self.call_count}")

        trajectory = Trajectory()
        trajectory.add_step(
            Step(
                step_number=1,
                thought="Recovered",
                response="Success after retry",
                token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                cost=Cost(amount=0.001),
                latency=Latency(seconds=0.0),
            )
        )
        return trajectory


class MockMetricEvaluator(BaseEvaluator):
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def evaluate(self, test_case: GoldenTestCase, trajectory: Trajectory) -> MetricResult:
        return MetricResult(metric_name=self.name, score=1.0, reasoning="Good")


def test_benchmark_config_instantiation():
    case = GoldenTestCase(case_id="tc-1", input_query="test query")
    dataset = GoldenDataset(dataset_id="ds-1", name="Test Dataset", test_cases=[case])

    # Default policy
    config = BenchmarkConfig(dataset=dataset, provider="gemini")
    assert config.concurrency == 3
    assert config.retry_policy.max_retries == 3
    assert config.retry_policy.initial_delay == 1.0

    # Custom policy
    policy = RetryPolicy(max_retries=5, initial_delay=0.1, backoff_factor=1.5)
    config_custom = BenchmarkConfig(
        dataset=dataset,
        provider="ollama",
        evaluators=["Latency", "Cost"],
        concurrency=5,
        retry_policy=policy,
        execution_parameters={"temperature": 0.0},
    )
    assert config_custom.concurrency == 5
    assert config_custom.retry_policy.max_retries == 5
    assert config_custom.retry_policy.initial_delay == 0.1
    assert config_custom.retry_policy.backoff_factor == 1.5
    assert config_custom.evaluators == ["Latency", "Cost"]
    assert config_custom.execution_parameters["temperature"] == 0.0


@pytest.mark.asyncio
async def test_benchmark_runner_retry_success():
    case = GoldenTestCase(case_id="tc-1", input_query="test query")
    dataset = GoldenDataset(dataset_id="ds-1", name="Test Dataset", test_cases=[case])

    # SUT fails twice, then succeeds. RetryPolicy allows 3 retries (4 total attempts)
    sut = FlakyTravelAgentSUT(failures_before_success=2)
    policy = RetryPolicy(max_retries=3, initial_delay=0.01, backoff_factor=1.1)
    config = BenchmarkConfig(dataset=dataset, provider="mock", retry_policy=policy)

    repo = InMemoryEvaluationRepository()
    registry = MetricRegistry()
    registry.register(MockMetricEvaluator("Faithfulness"))

    runner = BenchmarkRunner(repository=repo, registry=registry)
    run = await runner.run_benchmark("run-retry-succ", config, sut)

    assert run.summary["successful_cases"] == 1
    assert run.cases[0].success is True
    # The SUT was called 3 times (1 initial + 2 retries)
    assert sut.call_count == 3


@pytest.mark.asyncio
async def test_benchmark_runner_retry_failure():
    case = GoldenTestCase(case_id="tc-1", input_query="test query")
    dataset = GoldenDataset(dataset_id="ds-1", name="Test Dataset", test_cases=[case])

    # SUT fails 4 times. RetryPolicy only allows 2 retries (3 total attempts)
    sut = FlakyTravelAgentSUT(failures_before_success=4)
    policy = RetryPolicy(max_retries=2, initial_delay=0.01, backoff_factor=1.1)
    config = BenchmarkConfig(dataset=dataset, provider="mock", retry_policy=policy)

    repo = InMemoryEvaluationRepository()
    registry = MetricRegistry()
    registry.register(MockMetricEvaluator("Faithfulness"))

    runner = BenchmarkRunner(repository=repo, registry=registry)
    run = await runner.run_benchmark("run-retry-fail", config, sut)

    # Case should fail because retries were exhausted
    assert run.summary["successful_cases"] == 0
    assert run.cases[0].success is False
    assert sut.call_count == 3  # 1 initial + 2 retries


@pytest.mark.asyncio
async def test_benchmark_runner_evaluator_filtering():
    case = GoldenTestCase(case_id="tc-1", input_query="test query")
    dataset = GoldenDataset(dataset_id="ds-1", name="Test Dataset", test_cases=[case])

    sut = FlakyTravelAgentSUT(failures_before_success=0)
    config = BenchmarkConfig(
        dataset=dataset,
        provider="mock",
        evaluators=["Faithfulness"],  # Only run Faithfulness, ignore Groundedness
    )

    repo = InMemoryEvaluationRepository()
    registry = MetricRegistry()
    registry.register(MockMetricEvaluator("Faithfulness"))
    registry.register(MockMetricEvaluator("Groundedness"))

    runner = BenchmarkRunner(repository=repo, registry=registry)
    run = await runner.run_benchmark("run-eval-filter", config, sut)

    assert "Faithfulness" in run.cases[0].metrics
    assert "Groundedness" not in run.cases[0].metrics
