import asyncio
from datetime import datetime, timezone

import pytest

from src.adapters.repositories import InMemoryEvaluationRepository
from src.domain.entities import (
    GoldenDataset,
    GoldenTestCase,
    MetricResult,
    Step,
    Trajectory,
)
from src.domain.interfaces import AgentSUT, BaseEvaluator
from src.domain.value_objects import Cost, Latency, TokenUsage
from src.use_cases.runners.benchmark_runner import BenchmarkRunner

# --- Mock Implementations for Testing ---


class MockTravelAgentSUT(AgentSUT):
    """Mock travel agent SUT that returns a predefined trajectory."""

    def __init__(self, version: str = "v1.0.0-mock", delay: float = 0.0) -> None:
        self._version = version
        self.delay = delay
        self.call_count = 0

    @property
    def version(self) -> str:
        return self._version

    async def run(self, input_query: str) -> Trajectory:
        self.call_count += 1
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        trajectory = Trajectory()
        trajectory.add_step(
            Step(
                step_number=1,
                thought="Processing query...",
                response=f"Itinerary matching query: {input_query}",
                token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                cost=Cost(amount=0.001),
                latency=Latency(seconds=self.delay),
            )
        )
        return trajectory


class CrashingTravelAgentSUT(AgentSUT):
    """Mock agent SUT that intentionally throws exceptions."""

    @property
    def version(self) -> str:
        return "v-crash-mock"

    async def run(self, input_query: str) -> Trajectory:
        raise RuntimeError("GDS API Connection Timeout")


class MockMetricEvaluator(BaseEvaluator):
    """Mock evaluator that returns a predefined metric score."""

    def __init__(self, name: str, score: float | bool, reasoning: str = "Good") -> None:
        self._name = name
        self.score = score
        self.reasoning = reasoning
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._name

    async def evaluate(self, test_case: GoldenTestCase, trajectory: Trajectory) -> MetricResult:
        self.call_count += 1
        return MetricResult(
            metric_name=self.name,
            score=self.score,
            reasoning=self.reasoning,
            metadata={"run_timestamp": str(datetime.now(timezone.utc))},
        )


class CrashingMetricEvaluator(BaseEvaluator):
    """Mock evaluator that intentionally throws exceptions."""

    @property
    def name(self) -> str:
        return "CrashingMetric"

    async def evaluate(self, test_case: GoldenTestCase, trajectory: Trajectory) -> MetricResult:
        raise ValueError("Model rate limit exceeded")


# --- Test Cases ---


@pytest.mark.asyncio
async def test_benchmark_runner_success_flow():
    # 1. Setup Golden Dataset
    case1 = GoldenTestCase(case_id="tc-1", input_query="Fly to Paris")
    case2 = GoldenTestCase(case_id="tc-2", input_query="Hotel in Tokyo")
    dataset = GoldenDataset(
        dataset_id="ds-test", name="Test Dataset", version="1.0.0", test_cases=[case1, case2]
    )

    # 2. Setup SUT and Evaluators
    sut = MockTravelAgentSUT(version="v1.2.3")
    eval1 = MockMetricEvaluator(name="Faithfulness", score=1.0, reasoning="Faithful response")
    eval2 = MockMetricEvaluator(name="Groundedness", score=0.8, reasoning="Substantially grounded")

    repo = InMemoryEvaluationRepository()
    runner = BenchmarkRunner(repository=repo, evaluators=[eval1, eval2])

    # 3. Run Benchmark
    run = await runner.run_evaluation(
        run_id="run-succ", dataset=dataset, sut=sut, max_concurrency=2
    )

    # 4. Assertions on Run results
    assert run.run_id == "run-succ"
    assert run.dataset_id == "ds-test"
    assert run.sut_version == "v1.2.3"
    assert len(run.cases) == 2

    # Check that individual cases succeeded
    for case_eval in run.cases:
        assert case_eval.success is True
        assert "Faithfulness" in case_eval.metrics
        assert case_eval.metrics["Faithfulness"].score == 1.0
        assert "Groundedness" in case_eval.metrics
        assert case_eval.metrics["Groundedness"].score == 0.8

    # Check aggregations
    assert run.summary["total_cases"] == 2
    assert run.summary["successful_cases"] == 2
    assert run.summary["success_rate"] == 1.0
    assert run.summary["avg_metrics"]["Faithfulness"] == 1.0
    assert run.summary["avg_metrics"]["Groundedness"] == 0.8
    assert run.summary["total_tokens"] == 30  # 15 * 2
    assert run.summary["total_cost"] == pytest.approx(0.002)

    # Check persistence
    saved_run = await repo.get_run("run-succ")
    assert saved_run is not None
    assert saved_run.run_id == "run-succ"
    assert len(saved_run.cases) == 2


@pytest.mark.asyncio
async def test_benchmark_runner_sut_crash_isolation():
    # 1. Setup Golden Dataset
    case1 = GoldenTestCase(case_id="tc-1", input_query="Fly to Paris")
    dataset = GoldenDataset(
        dataset_id="ds-test", name="Test Dataset", version="1.0.0", test_cases=[case1]
    )

    # 2. Setup Crashing SUT and Evaluators
    sut = CrashingTravelAgentSUT()
    evaluator = MockMetricEvaluator(name="Safety", score=1.0)
    repo = InMemoryEvaluationRepository()
    runner = BenchmarkRunner(repository=repo, evaluators=[evaluator])

    # 3. Run Benchmark (Ensure SUT crash doesn't bubble up and fail the execution)
    run = await runner.run_evaluation(run_id="run-crash-sut", dataset=dataset, sut=sut)

    # 4. Assertions on Failure capture
    assert len(run.cases) == 1
    case_eval = run.cases[0]

    # The case should have failed due to the crash
    assert case_eval.success is False
    assert len(case_eval.trajectory.steps) == 1
    assert "failed" in case_eval.trajectory.steps[0].thought
    assert case_eval.trajectory.steps[0].metadata["exception_type"] == "RuntimeError"

    # Evaluators should still have run on the failed trajectory (or returned defaults)
    assert "Safety" in case_eval.metrics
    assert case_eval.metrics["Safety"].score == 1.0

    # Overall run summary check
    assert run.summary["successful_cases"] == 0
    assert run.summary["success_rate"] == 0.0


@pytest.mark.asyncio
async def test_benchmark_runner_evaluator_crash_isolation():
    # 1. Setup Golden Dataset
    case1 = GoldenTestCase(case_id="tc-1", input_query="Fly to Paris")
    dataset = GoldenDataset(
        dataset_id="ds-test", name="Test Dataset", version="1.0.0", test_cases=[case1]
    )

    # 2. Setup SUT and Crashing Evaluator
    sut = MockTravelAgentSUT()
    eval1 = MockMetricEvaluator(name="Safety", score=1.0)
    eval2 = CrashingMetricEvaluator()

    repo = InMemoryEvaluationRepository()
    runner = BenchmarkRunner(repository=repo, evaluators=[eval1, eval2])

    # 3. Run Benchmark (Ensure evaluator crash is caught safely)
    run = await runner.run_evaluation(run_id="run-crash-eval", dataset=dataset, sut=sut)

    # 4. Assertions
    assert len(run.cases) == 1
    case_eval = run.cases[0]

    # Case should fail because one of the evaluators failed (score 0.0 is < 0.5 threshold)
    assert case_eval.success is False
    assert "Safety" in case_eval.metrics
    assert case_eval.metrics["Safety"].score == 1.0

    assert "CrashingMetric" in case_eval.metrics
    crashed_metric = case_eval.metrics["CrashingMetric"]
    assert crashed_metric.score == 0.0
    assert "ValueError" in crashed_metric.metadata["exception_type"]
    assert "rate limit exceeded" in crashed_metric.reasoning


@pytest.mark.asyncio
async def test_benchmark_runner_concurrency_bounding():
    # 1. Setup Golden Dataset with 4 cases
    cases = [GoldenTestCase(case_id=f"tc-{i}", input_query=f"Query {i}") for i in range(4)]
    dataset = GoldenDataset(
        dataset_id="ds-concurrency", name="Test Concurrency", version="1.0.0", test_cases=cases
    )

    # 2. Setup SUT with delay
    sut = MockTravelAgentSUT(delay=0.05)  # 50ms delay per run
    repo = InMemoryEvaluationRepository()
    runner = BenchmarkRunner(repository=repo, evaluators=[])

    # 3. Test running with max_concurrency = 2
    # Total time should be roughly: 4 cases * 50ms / 2 threads = 100ms + overhead
    start = datetime.now()
    _ = await runner.run_evaluation(
        run_id="run-concurrency", dataset=dataset, sut=sut, max_concurrency=2
    )
    duration = (datetime.now() - start).total_seconds()

    # If it was sequential, it would take >= 0.20 seconds.
    # If it ran concurrently with limit 2, it should take < 0.18 seconds (excluding setup).
    # We verify that concurrency actually parallelized the execution.
    assert duration < 0.18
    assert sut.call_count == 4
